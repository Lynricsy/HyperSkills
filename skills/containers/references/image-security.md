# Image security and supply chain

Verified against: Docker Engine 29 with BuildKit, Buildx 0.2x, `docker/dockerfile:1`.

## Contents

- [Build secrets: where a credential actually leaks](#build-secrets-where-a-credential-actually-leaks)
- [Doing it correctly](#doing-it-correctly)
- [Secrets that are already in an image](#secrets-that-are-already-in-an-image)
- [What the runtime user buys you](#what-the-runtime-user-buys-you)
- [Registry references and mutability](#registry-references-and-mutability)
- [Scanning](#scanning)
- [SBOM, provenance and signing](#sbom-provenance-and-signing)
- [What a container does not isolate](#what-a-container-does-not-isolate)

## Build secrets: where a credential actually leaks

The claim "use a multi-stage build so the secret does not reach the final image" is
wrong, and it is wrong in a way that survives every check people run.

Take the most favourable case: the credential is an `ARG` consumed only inside a
builder stage, the file it wrote is deleted in the same `RUN`, and the builder stage is
not the shipped stage.

```bash
docker history --no-trunc <ref> | grep -c glpat        # 0
docker inspect <ref> --format '{{json .Config.Env}}' | grep -c glpat   # 0
```

Both clean. And yet BuildKit attaches a provenance attestation to the build and records
the build arguments **verbatim** in it: [verified]

```
{"frontend":"dockerfile.v0","args":{"build-arg:NPM_TOKEN":"glpat-…"}, …
 "request":{"args":{"build-arg:NPM_TOKEN":"glpat-…"}}}
```

The check that can actually fail:

```bash
docker buildx imagetools inspect <ref> --format '{{json .Provenance}}' \
  | grep -oE 'glpat-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}' \
  | sort -u | wc -l
```

Grep for the **credential pattern**, never for the argument name. The attestation also
embeds commit messages and `RUN` command lines, so searching for `NPM_TOKEN` matches
your own commit text and reports a leak that is not there. A pre-fix tag returning a
non-zero count and a post-fix tag returning zero is the proof; a single post-fix zero
proves nothing on its own.

Layer deletion does not help either, for a separate reason: layers are additive, so
`RUN rm -f .npmrc` in a later layer only records a whiteout entry. The earlier layer
still contains the file and is still distributed.

## Doing it correctly

```dockerfile
RUN --mount=type=secret,id=npm_token \
    NPM_CONFIG_USERCONFIG=/tmp/npmrc \
    sh -c 'printf "//registry.npmjs.org/:_authToken=%s\n" "$(cat /run/secrets/npm_token)" > /tmp/npmrc \
      && npm ci --omit=dev'
```

```bash
docker build --secret id=npm_token,env=NPM_TOKEN .
docker build --secret id=npm_token,src=./token.txt .
```

The mount exists for the duration of that one instruction, is not part of the layer,
and is not recorded in the attestation — the same provenance grep returns zero on an
otherwise identical build. [verified]

Two details that get missed:

- Write any derived file (an `.npmrc`, a `.netrc`, a `pip.conf`) to a path outside the
  build context that the tool is told about by environment variable, not into the
  working directory. A file written into `/app` and deleted later is still in a layer.
- `RUN --mount=type=ssh` is the equivalent for private Git dependencies; it forwards an
  agent socket rather than a key file.

BuildKit's own linter flags the mistake before any of this matters:

```
docker build --check .
# SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ARG "NPM_TOKEN")
```

Make that a CI gate. It costs nothing and produces no image. [verified]

## Secrets that are already in an image

Treat as compromised and rotate. Rewriting the Dockerfile does not retract a pushed
image, a cache export, or the attestation of any tag already published — a single
leaked token in a builder `ARG` has been found replicated across every published
version of a package, because every build wrote it again.

The order is: rotate the credential, then fix the Dockerfile, then delete the affected
tags if the registry allows it. Doing only the last two leaves a live credential.

Runtime secrets are a different question and never belong in the image: no `ENV` with a
password, no baked config file. They arrive at run time from the platform (a Kubernetes
Secret, a Compose secret, an injected file).

## What the runtime user buys you

A non-root `USER` is the difference between "a remote code execution gives the attacker
the application" and "a remote code execution gives the attacker the container, package
manager included". It is not a sandbox — see the last section — but it removes the
cheapest escalations.

```dockerfile
RUN useradd --uid 10001 --create-home app
USER 10001
```

Numeric, because Kubernetes' `runAsNonRoot: true` check happens before the container
starts and can only verify a numeric uid without reading the image's `/etc/passwd`.

Pair it with the workload side, which is where it is actually enforced:
`runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`,
`capabilities.drop: [ALL]`. A `USER` line by itself is overridden by any manifest that
sets `runAsUser: 0`.

A read-only root filesystem is the one that most often needs image changes: find every
path the process writes (temp files, caches, compiled assets, pid files) and either
configure it elsewhere or mount a volume there.

## Registry references and mutability

A tag is a mutable pointer. `example.com/app:1.2.3` can be re-pushed, and with
`imagePullPolicy: IfNotPresent` the nodes that already cached it keep the old content
while new nodes get the new one — one Deployment, two versions, no way to tell from
`kubectl get`.

Deploy by digest: `example.com/app@sha256:…`. Keep the human-readable tag as an
additional reference for people, and let the deployment pipeline resolve tag → digest
once and write the digest into the manifest.

```bash
docker buildx imagetools inspect example.com/app:1.2.3 --format '{{json .Manifest.Digest}}'
```

Registry hygiene worth checking during a review: is the registry authenticated for
pulls (and does the cluster have the pull secret), is there a retention policy, and is
the base image pulled from a mirror you control rather than rate-limited Docker Hub.
`ImagePullBackOff` on a fresh node hours after a successful deploy is usually one of
those three.

## Scanning

```bash
docker scout cves <ref>              # or: trivy image <ref>, grype <ref>
```

Scan the image you ship, not the builder stage, and scan it in CI on a schedule as well
as on change — the image does not change but the vulnerability database does, so
yesterday's clean scan means nothing today.

Two failure modes to avoid:

- **Fail the build on any CVE.** Every image has unfixed low-severity findings in the
  base distribution; a gate that blocks on those gets disabled within a week. Gate on
  fixable high/critical findings, and track the rest.
- **Scanning instead of updating.** Most findings in a well-built image come from the
  base image, and the fix is rebuilding on a current base, not suppressing entries.
  Pinning by digest and *not* bumping it is how images rot; the pin is there to make
  the bump a reviewable commit, not to avoid it.

## SBOM, provenance and signing

```bash
docker buildx build --sbom=true --provenance=mode=max -t example.com/app:1.2.3 --push .
docker buildx imagetools inspect example.com/app:1.2.3 --format '{{json .SBOM}}'
```

An SBOM answers "is this image affected" for a new CVE without rebuilding or rescanning
everything. Provenance answers "what produced this image" — source, builder, build
arguments. Note the consequence of the second one: `mode=max` records more, including
the build arguments discussed above, so the attestation is only as safe as the build is
secret-free.

Signing (`cosign sign`, keyless via an OIDC identity) plus an admission policy that
verifies signatures is the only thing that stops a registry compromise from becoming a
cluster compromise. Without the verification side, signing is a ritual.

## What a container does not isolate

A container is a process with namespaces and cgroups, not a VM. Things that survive the
boundary by default:

- The **kernel** is shared. A kernel vulnerability is a host vulnerability.
- **Container root is host root** unless user namespaces are on. That is what
  `spec.hostUsers: false` (stable 1.36) changes, and what `runAsNonRoot` approximates
  in its absence.
- Mounting the **Docker socket** into a container is equivalent to giving it root on the
  host — it can start a privileged container mounting `/`. This includes CI containers
  that "just need to build images"; use a rootless builder or a BuildKit daemon instead.
- `hostNetwork`, `hostPID`, `hostPath` and `privileged: true` each remove a different
  part of the boundary. `privileged: true` removes essentially all of it.

Anything genuinely untrusted needs a sandboxed runtime (gVisor, Kata) or a separate
node pool, not a tighter `securityContext`.

<!-- sources: netresearch-docker, docker-docs, kubernetes-docs, google-skills, impertio-docker -->
