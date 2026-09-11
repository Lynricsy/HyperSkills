---
name: containers
description: "Guides container artefacts: Dockerfiles and multi-stage builds, base-image choice, BuildKit cache mounts and build secrets, .dockerignore, multi-architecture images, image hardening and SBOMs, Compose development environments with profiles, healthchecks and watch, Kubernetes manifests (Deployment, Service, Ingress, ConfigMap, Secret, PodDisruptionBudget, HPA), probe semantics, requests and limits, QoS and OOMKill, rolling updates, securityContext and Pod Security Standards, RBAC, Helm charts, Kustomize overlays, devcontainer.json, and CrashLoopBackOff / ImagePullBackOff / Pending diagnosis. Use when writing or reviewing a Dockerfile, compose file, Kubernetes manifest, chart or overlay, when an image is too large or rebuilds too slowly, when a rollout or node drain misbehaves, or when a pod will not start. Do not use for Terraform, OpenTofu or other infrastructure-as-code syntax, for managed control planes such as EKS, AKS or GKE, for service-mesh products, or for the application code inside the container."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# containers

## Scope

Covers the container artefacts a repository owns and the runtime behaviour they
declare: Dockerfiles and the build that produces an image, image hardening and
supply-chain metadata, Compose files for local development, Kubernetes workload
manifests, Helm charts and Kustomize overlays, `devcontainer.json`, and the diagnosis
of a workload that will not start or will not drain.

Written against Docker Engine 29 with BuildKit, the Compose Specification as shipped in
Compose v5, **Kubernetes 1.37** (current stable), Helm 4 and Kustomize 5. Rules needing
a server newer than 1.29 carry a gate such as `(1.33+)`.

Not covered:

- Terraform, OpenTofu and HCL — module structure, `count` versus `for_each`, state
  moves, provider configuration. Use the `terraform` skill.
- Build, scan and publish pipelines on GitHub Actions — workflow syntax, `permissions`,
  OIDC to a registry, SHA pinning of actions. Use the `github` skill. This skill covers
  what the build *does*, not the workflow that runs it.
- The application code inside the container. Use the `go`, `python`, `nodejs-backend`,
  `java-spring` or `csharp-dotnet` skill; this skill only covers what the language
  runtime imposes on the image (entrypoint and signals, where dependencies live, what
  the runtime stage actually needs).
- Managed cluster control planes — EKS, AKS and GKE node pools, cloud IAM and workload
  identity, provider load balancers and CSI drivers, cluster upgrades through the
  provider API. Use the `aws`, `azure` or `gcp` skill for those. Everything here still
  holds for a workload running on a managed cluster.
- Service meshes (Istio, Linkerd, Cilium Service Mesh) and their CRDs; GitOps
  controllers (Argo CD, Flux). Not covered by any skill in this library.
- Observability pipelines and dashboards — Prometheus Operator, OpenTelemetry
  Collector, log shipping, alert rules. Use the `observability` skill. This skill stops
  at what a manifest declares (probes, `terminationGracePeriodSeconds`,
  resource fields).

Paths below are relative to this skill's directory.

## Read first

`references/kubernetes-api-versions.md`, before writing or reviewing any Kubernetes
manifest, chart template or overlay. It carries the removed-API table, the version gate
for every field this skill recommends, and the validation commands that work without a
cluster. Generated manifests reproduce API versions the server stopped serving years
ago, and a removed version is a hard rejection, not a warning.

## Core rules

1. Establish versions before applying a gated rule: `docker version`, `kubectl version`,
   `helm version`, and the cluster's minor version. Half the container guidance in
   circulation predates BuildKit-by-default, Compose v2 and Kubernetes 1.25.
2. A credential passed as `ARG` / `--build-arg` is leaked, whether or not the stage that
   used it is shipped and whether or not the file it wrote was deleted. BuildKit records
   build arguments verbatim in the image's provenance attestation. Use
   `RUN --mount=type=secret,id=<name>` and read `/run/secrets/<name>`; the mount exists
   only for that instruction and lands in no layer. [verified]
3. `docker history` is the wrong check for a leak. On an image built with a bare `ARG`,
   `docker history` and `docker inspect .Config.Env` both return nothing while the token
   sits in cleartext in the attestation. The check that can fail is
   `docker buildx imagetools inspect <ref> --format '{{json .Provenance}}'`, grepped for
   the *credential pattern* rather than the argument name. [verified]
4. Order a Dockerfile by rate of change: copy the dependency manifest, install, then copy
   the source. `COPY . .` before the install re-runs the install on every source edit,
   because `COPY` invalidates on the copied files' metadata. [verified]
5. Every image needs a `.dockerignore` (or a `<dockerfile>.dockerignore`) that excludes
   at least `.git`, the host dependency directory and local env files. Without one the
   whole working tree is uploaded as build context and `COPY . .` bakes it in — measured
   here as 73.5 MB of `.git` and host `node_modules` inside the image. [verified]
6. The runtime stage starts from a different, smaller image than the build stage.
   Default to distroless, `scratch` for a statically linked binary, or the `-slim`
   variant when a libc and a package manager are genuinely needed. Fall back to Alpine
   only when you must `exec` into the container to debug, and accept its cost: musl
   changes DNS resolution behaviour and breaks glibc-compiled wheels and native modules.
7. `COPY --from=build /app /app` ships the entire builder working tree — sources, dev
   dependencies, caches. Copy named artefacts, not directories you did not curate.
8. Reference base images and deployed images by digest, or at minimum a full patch
   version. A tag is mutable: `node:20` moves weekly, and with
   `imagePullPolicy: IfNotPresent` two nodes can run different code under one tag, which
   also makes `kubectl rollout undo` meaningless.
9. Use exec-form `CMD`/`ENTRYPOINT` (`CMD ["node", "dist/index.js"]`). Shell form runs
   the process under `/bin/sh -c`, which does not forward `SIGTERM`, so the container is
   `SIGKILL`ed at the end of the grace period instead of shutting down. BuildKit warns
   about this as `JSONArgsRecommended`. [verified]
10. Set a non-root `USER` in the runtime stage and make the Kubernetes side enforce it
    with `runAsNonRoot: true`. A `USER` line alone is advisory — a manifest can override
    it with `runAsUser: 0`.
11. Compose files carry no top-level `version:`. It is obsolete: Compose always validates
    against the current schema and warns when the key is present. [official]
12. `depends_on: [db]` waits for the container to be *created*, not for the process to
    accept connections. Use the long form with `condition: service_healthy` plus a real
    `healthcheck` on the dependency, and `condition: service_completed_successfully` for
    a migration or seed container that must finish first.
13. A one-shot service (migrate, seed, fixtures) belongs behind `profiles:` so a plain
    `docker compose up` does not run it, *and* behind a
    `service_completed_successfully` dependency so that when it does run, everything
    else waits for it. Profiles alone change "always runs" into "never runs".
14. Shadow a bind-mounted dependency directory with a container-owned volume
    (`- /app/node_modules` on top of `- .:/app`), otherwise the host's platform-specific
    build replaces the image's. Better still, replace the whole-tree bind mount with
    `develop.watch` (`action: sync` for sources, `action: rebuild` for the dependency
    manifest) and run `docker compose watch`; sync pushes changed files instead of
    paying bind-mount I/O on every read.
15. Liveness answers "is this process wedged?", readiness answers "can it serve right
    now?", startup answers "has it finished booting?". A liveness probe that touches a
    database or another service converts that dependency's outage into a simultaneous
    restart of every replica, and the restarts prevent recovery. Dependency checks go in
    readiness.
16. While a startup probe is running, liveness and readiness are suspended. Any workload
    with a slow boot needs one; size it as `failureThreshold × periodSeconds >` worst
    observed startup. Keep `timeoutSeconds < periodSeconds`, and never set
    `failureThreshold: 1` on liveness — one slow response then kills the container.
17. Always set a memory limit; it is the only defence against one container taking the
    node down, and exceeding it is an OOMKill, not throttling. Prefer leaving CPU
    *unlimited* unless the workload is batch, multi-tenant or deliberately Guaranteed:
    a CPU limit is enforced by CFS quota, so the container is throttled at the ceiling
    inside every scheduling window even when the node is idle. Note the trade-off —
    without equal requests and limits the pod is Burstable and is evicted before
    Guaranteed pods under node pressure. [community]
18. A PodDisruptionBudget whose budget is zero (`minAvailable` equal to `replicas`)
    makes the eviction API refuse forever, so a node drain hangs rather than fails.
    Express the budget as `maxUnavailable: 1` so it tracks replica-count changes, and
    set `unhealthyPodEvictionPolicy: AlwaysAllow` (1.27+) so unready pods cannot wedge
    the drain either.
19. Default a web workload's rollout to `maxSurge: 1, maxUnavailable: 0` — capacity is
    added before it is removed. `maxUnavailable: 50%` with `maxSurge: 0` removes half
    the fleet for the entire rollout, which is exactly when load arrives at the rest.
20. The restricted Pod Security Standard needs all of `runAsNonRoot: true`,
    `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` and
    `seccompProfile.type: RuntimeDefault`; the first three alone are rejected by an
    `enforce: restricted` namespace. Add `readOnlyRootFilesystem: true` and
    `automountServiceAccountToken: false` as well: neither is required by the standard,
    and both remove a real escalation path.
21. A literal secret in `env.value` is readable by anyone who can `get deployment` or
    `get pod` in the namespace, and it is in version control. Use
    `valueFrom.secretKeyRef`, and treat a secret that reached a manifest as compromised —
    rotate it rather than only removing it.
22. Kubernetes pod-to-pod networking is flat by default: every pod can reach every other
    pod until a NetworkPolicy selects it. A namespace with no policy is not "using the
    default policy", it is unsegmented.
23. Helm distributes configuration to *other people* — versioning, dependencies, a
    published chart. Kustomize expresses the differences between *your own* environments
    with no templating. Choose one per artefact; the only sane combination is Kustomize
    post-processing someone else's rendered chart.
24. `kubectl apply --dry-run=client` is not offline validation: it fetches the OpenAPI
    schema and performs RESTMapper discovery, so it fails outright with no reachable
    cluster (even with `--validate=false`). The gates that work locally are
    `kubeconform -kubernetes-version <x.y.z> -strict`, `kubectl kustomize`,
    `helm template` and `helm lint`. [verified]
25. Diagnose from the object, not from the symptom name. `kubectl describe pod` plus
    `kubectl get events --sort-by=.lastTimestamp` distinguishes the four causes that all
    surface as "Pending" and the five that all surface as "CrashLoopBackOff". Quote the
    evidence before naming a root cause.

## Workflows

### write-or-slim-a-container-image

- [ ] Measure before changing: `docker image ls`, then `docker history <ref>` to see
      which instruction owns the bytes. Fix the largest layer first, not the tidiest one.
- [ ] Split build from runtime and pick the runtime base by what the process actually
      needs at run time (`references/dockerfile.md`).
- [ ] Reorder for cache: dependency manifest → install → source → build. Add
      `--mount=type=cache` for the package manager's own cache directory.
- [ ] Write or fix `.dockerignore`; prefer a deny-everything-then-allow form so a new
      secret file added later is excluded by default.
- [ ] Move every build-time credential to `--mount=type=secret`, and remove the `ARG`
      and any `ENV` that carried it (`references/image-security.md`).
- [ ] Add `USER`, exec-form `CMD`, and a digest or full-version base image pin.
- [ ] **Gate — the numbers and the attestation:** re-run the build, quote both sizes and
      the cached-versus-rebuilt step list for a source-only change, and show
      `docker buildx imagetools inspect <ref> --format '{{json .Provenance}}'` grepped for
      the credential pattern returning zero.

### review-a-kubernetes-manifest

- [ ] Check every `apiVersion` against the target cluster's minor version first
      (`references/kubernetes-api-versions.md`). A removed version makes the rest of the
      review moot because the object cannot be created.
- [ ] Read the probes as a set: which one checks dependencies, is there a startup budget,
      does `timeoutSeconds` fit inside `periodSeconds`
      (`references/kubernetes-workloads.md`).
- [ ] Check resources and the resulting QoS class, then the disruption story — PDB
      budget, rollout parameters, spread across nodes and zones
      (`references/kubernetes-resources.md`).
- [ ] Check the security posture against restricted PSS, plus service account,
      RBAC and secret handling (`references/kubernetes-security.md`).
- [ ] Check the set is complete and internally consistent: a Service exists for every
      Ingress backend, selectors match template labels, ports line up, and the
      `app.kubernetes.io/*` labels are present.
- [ ] Check image references are immutable and `imagePullPolicy` agrees with them.
- [ ] **Gate — it validates offline:**
      `kubeconform -kubernetes-version <cluster version> -strict -summary` over the
      rendered output returns zero invalid resources, and every finding names a
      `file:line`.

### set-up-a-compose-development-environment

- [ ] Drop `version:`, pin every image to a version tag, and name the project.
- [ ] Give each dependency a real `healthcheck`, then convert `depends_on` to the long
      form with `service_healthy` / `service_completed_successfully`
      (`references/compose.md`).
- [ ] Put one-shot jobs behind `profiles:` and wire the services that need them to wait
      for completion.
- [ ] Replace the whole-tree bind mount with `develop.watch`, or keep the bind mount and
      shadow the dependency directory with a volume.
- [ ] Persist state in named volumes; publish a port to the host only when a host tool
      needs it, bound to `127.0.0.1`.
- [ ] **Gate — a cold start works:** `docker compose config --quiet` is silent, then
      `docker compose down -v && docker compose up --wait` reaches a healthy state with
      no manual step in between.

### debug-a-pod-that-will-not-run

- [ ] Get the state before theorising: `kubectl get pod -o wide`,
      `kubectl describe pod`, `kubectl get events --sort-by=.lastTimestamp -n <ns>`.
- [ ] Read the *previous* container's logs, not the current one's, when it is restarting:
      `kubectl logs <pod> --previous` (`references/troubleshooting.md`).
- [ ] Map the phase to its real causes — Pending is scheduling (resources, taints,
      affinity, unbound PVC), CrashLoopBackOff is the process (exit code, OOMKill, config,
      failing liveness), ImagePullBackOff is the reference or the credentials.
- [ ] For an OOMKill read `kubectl get pod -o jsonpath` for
      `lastState.terminated.reason` and `exitCode`; exit 137 with reason `OOMKilled` is
      the limit, exit 137 without it is a `SIGKILL` from elsewhere.
- [ ] Reproduce the container's own view before changing the manifest: `kubectl debug`
      with an ephemeral container, or run the image locally with the same command.
- [ ] **Gate — the fix is tied to evidence:** quote the event, the exit code or the log
      line that names the cause, then show the same command clean after the change.

### choose-and-structure-helm-or-kustomize

- [ ] Decide by consumer, not by taste (Core rule 23), and record the decision in the
      repository so the next change does not re-open it.
- [ ] For Helm: keep templates free of logic that belongs in `values.yaml`, give every
      value a default and a `values.schema.json`, and never template an `apiVersion`
      without a `.Capabilities` guard (`references/helm-and-kustomize.md`).
- [ ] For Kustomize: a base that is deployable on its own, overlays that only express
      differences, strategic-merge patches for structure and JSON-6902 patches for list
      surgery.
- [ ] Keep generated ConfigMaps and Secrets hash-suffixed so a config change actually
      rolls the pods.
- [ ] **Gate — render then validate:** `helm template` or `kubectl kustomize` piped into
      `kubeconform -strict`, plus `helm lint` for a chart. Compare the rendered diff, not
      the template diff, when reviewing a change.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Removed and deprecated API versions by release, the version gate for every field this skill recommends, and the validation commands that work without a cluster | Before writing or reviewing any manifest, chart template or overlay | `references/kubernetes-api-versions.md` |
| Stage structure, base-image selection, cache ordering and cache mounts, `.dockerignore` semantics, entrypoints and signals, multi-architecture builds, build lint | Writing or slimming a Dockerfile, or a build is slow | `references/dockerfile.md` |
| Build secrets and the provenance leak, non-root and read-only runtime, registry references and digests, scanning, SBOM and signing, what a container runtime does and does not isolate | Hardening an image or auditing how one was built | `references/image-security.md` |
| Compose file shape without `version:`, healthchecks and dependency conditions, profiles, `develop.watch`, volumes and bind-mount shadowing, networks and ports, `include`/`extends` | Building or fixing a local development environment | `references/compose.md` |
| Deployment, StatefulSet, Job and CronJob shape, Service types and Ingress, ConfigMap and Secret wiring, probes, lifecycle and graceful shutdown, rollout strategy and rollback, sidecars | Writing or reviewing a workload manifest | `references/kubernetes-workloads.md` |
| Requests, limits and QoS, OOMKill and CFS throttling, LimitRange and ResourceQuota, HPA, PodDisruptionBudget, node affinity, taints and topology spread, in-place resize | Sizing a workload, or scheduling and disruption behave oddly | `references/kubernetes-resources.md` |
| securityContext field by field, Pod Security Standards and Pod Security Admission labels, ServiceAccount and RBAC, secret handling, NetworkPolicy, user namespaces | Hardening a workload or reviewing its blast radius | `references/kubernetes-security.md` |
| When each tool fits, chart layout and values design, capability guards and hooks, overlay and patch strategy, generators and hash suffixes, the combinations that go wrong | Packaging manifests for more than one environment | `references/helm-and-kustomize.md` |
| Pending, CrashLoopBackOff, ImagePullBackOff, OOMKilled, Terminating, 502 from an Ingress, DNS failures — the evidence that separates their causes | A workload is broken and you need the cause, not a guess | `references/troubleshooting.md` |
| `devcontainer.json` review rules, the image-metadata merge that makes absence unprovable, lifecycle command ordering and prebuilds, Features, `remoteUser` and UID handling | Writing or reviewing a dev container or Codespaces configuration | `references/devcontainers.md` |

## Output format

When reviewing a Dockerfile, compose file or manifest set, group findings by file and
lead each with the location and the consequence:

```
k8s/checkout/deployment.yaml:34 - blocking - livenessProbe hits /health, which queries
  Postgres. A database blip fails the probe on all 3 replicas at once and the kubelet
  restarts them together. Move the dependency check to readinessProbe; point liveness at
  a handler that only reports process health.
```

Order findings by blast radius: first anything that makes the object impossible to
create (a removed `apiVersion`, a schema error), then anything that causes an outage
(probe semantics, a zero-budget PDB, a leaked credential), then correctness, then size
and style. For a size or build-time finding quote the measurement (`docker history`
line, image size, which steps were `CACHED`) rather than asserting an improvement, and
give the before/after snippet.

## Environment

- Docker Engine 24+ with BuildKit for `--mount=type=secret` and `--mount=type=cache`;
  `docker buildx imagetools inspect` needs an image in a registry or an OCI export, and
  provenance attestations require the `docker-container` builder driver, not the default
  `docker` driver.
- `kubeconform` is the offline schema validator used by the gates above; it is a single
  binary or `ghcr.io/yannh/kubeconform`. It needs network access the first time to fetch
  the schema set for the requested Kubernetes version.
- `kubectl` needs a reachable cluster for anything that touches discovery, including
  `apply --dry-run=client`. `kubectl create --dry-run=client -o yaml` and
  `kubectl kustomize` are the two subcommands that work with no cluster at all.
- Helm 4 is current; Helm 3 left bug-fix support in 2026 and receives security fixes
  only. `helm template` and `helm lint` are offline; `--dry-run=server` is not.
- Say which tools are actually present rather than assuming. A review performed by
  reading files is still a review — state that nothing was executed.
