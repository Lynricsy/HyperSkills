# Kubernetes API versions and offline validation

Verified against: Kubernetes 1.37 (current stable), kubectl 1.34, kubeconform, Helm 4.2, Kustomize 5.7.

## Contents

- [Why this file is read first](#why-this-file-is-read-first)
- [Removed API versions, by the release that stopped serving them](#removed-api-versions-by-the-release-that-stopped-serving-them)
- [Structural changes that bite when you migrate](#structural-changes-that-bite-when-you-migrate)
- [Deprecated but still served](#deprecated-but-still-served)
- [Version gates for the fields this skill recommends](#version-gates-for-the-fields-this-skill-recommends)
- [Validating without a cluster](#validating-without-a-cluster)
- [Validating against a cluster](#validating-against-a-cluster)
- [Finding what a live cluster still uses](#finding-what-a-live-cluster-still-uses)

## Why this file is read first

Removal is not a warning. Once a release stops serving an API version, the server
answers `error: unable to recognize ...: no matches for kind "Ingress" in version
"extensions/v1beta1"` and nothing about the object is created. Deprecation is the
warning stage and is harmless for one or two releases.

Two failure shapes come from the same root:

- A manifest reproduced from memory or from a tutorial carries an `apiVersion` that was
  correct in 2021.
- A chart renders fine, `helm lint` passes, and `kubectl apply` fails, because the
  template produced syntactically valid YAML with a dead `apiVersion`.

Both are cheap to catch and expensive to discover during a deploy. Check the
`apiVersion` of every object first, then review the rest.

## Removed API versions, by the release that stopped serving them

The most recent removal was in **1.32**. Releases 1.33 through 1.37 removed no API
versions, so a manifest that is valid on 1.32 is valid on 1.37 as far as `apiVersion`
goes. [official]

| Removed in | Kind | Dead version | Use instead |
|---|---|---|---|
| 1.32 | FlowSchema, PriorityLevelConfiguration | `flowcontrol.apiserver.k8s.io/v1beta3` | `flowcontrol.apiserver.k8s.io/v1` (since 1.29) |
| 1.29 | FlowSchema, PriorityLevelConfiguration | `flowcontrol.apiserver.k8s.io/v1beta2` | `flowcontrol.apiserver.k8s.io/v1` |
| 1.27 | CSIStorageCapacity | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` (since 1.24) |
| 1.26 | HorizontalPodAutoscaler | `autoscaling/v2beta2` | `autoscaling/v2` (since 1.23) |
| 1.26 | FlowSchema, PriorityLevelConfiguration | `flowcontrol.apiserver.k8s.io/v1beta1` | `flowcontrol.apiserver.k8s.io/v1` |
| 1.25 | CronJob | `batch/v1beta1` | `batch/v1` (since 1.21) |
| 1.25 | EndpointSlice | `discovery.k8s.io/v1beta1` | `discovery.k8s.io/v1` (since 1.21) |
| 1.25 | Event | `events.k8s.io/v1beta1` | `events.k8s.io/v1` (since 1.19) |
| 1.25 | HorizontalPodAutoscaler | `autoscaling/v2beta1` | `autoscaling/v2` |
| 1.25 | PodDisruptionBudget | `policy/v1beta1` | `policy/v1` (since 1.21) |
| 1.25 | PodSecurityPolicy | `policy/v1beta1` | Pod Security Admission, or an admission webhook — there is no replacement object |
| 1.25 | RuntimeClass | `node.k8s.io/v1beta1` | `node.k8s.io/v1` (since 1.20) |
| 1.22 | Ingress, IngressClass | `extensions/v1beta1`, `networking.k8s.io/v1beta1` | `networking.k8s.io/v1` (since 1.19) |
| 1.22 | CustomResourceDefinition | `apiextensions.k8s.io/v1beta1` | `apiextensions.k8s.io/v1` (since 1.16) |
| 1.22 | MutatingWebhookConfiguration, ValidatingWebhookConfiguration | `admissionregistration.k8s.io/v1beta1` | `admissionregistration.k8s.io/v1` |
| 1.22 | ClusterRole, ClusterRoleBinding, Role, RoleBinding | `rbac.authorization.k8s.io/v1beta1` | `rbac.authorization.k8s.io/v1` |
| 1.22 | CertificateSigningRequest | `certificates.k8s.io/v1beta1` | `certificates.k8s.io/v1` |
| 1.22 | PriorityClass | `scheduling.k8s.io/v1beta1` | `scheduling.k8s.io/v1` |
| 1.22 | Lease | `coordination.k8s.io/v1beta1` | `coordination.k8s.io/v1` |
| 1.22 | CSIDriver, CSINode, StorageClass, VolumeAttachment | `storage.k8s.io/v1beta1` | `storage.k8s.io/v1` |
| 1.22 | APIService | `apiregistration.k8s.io/v1beta1` | `apiregistration.k8s.io/v1` |
| 1.16 | Deployment, DaemonSet, ReplicaSet, StatefulSet | `extensions/v1beta1`, `apps/v1beta1`, `apps/v1beta2` | `apps/v1` |
| 1.16 | NetworkPolicy | `extensions/v1beta1` | `networking.k8s.io/v1` |

## Structural changes that bite when you migrate

Changing the `apiVersion` string is rarely the whole migration.

**Ingress → `networking.k8s.io/v1`.** `spec.backend` becomes `spec.defaultBackend`;
`serviceName` / numeric `servicePort` become `service.name` / `service.port.number`
(named ports become `service.port.name`); `pathType` is **required** on every path
(`Prefix`, `Exact`, or `ImplementationSpecific` to keep the old undefined behaviour);
the `kubernetes.io/ingress.class` annotation is replaced by `spec.ingressClassName`.

**PodDisruptionBudget → `policy/v1`.** An *empty* `spec.selector` (`{}`) now selects
every pod in the namespace, where in `v1beta1` it selected none. A copied-in `{}` turns
a no-op budget into a namespace-wide one.

**HorizontalPodAutoscaler → `autoscaling/v2`.** `targetAverageUtilization` moves to
`target.averageUtilization` with `target.type: Utilization`; `behavior` (scale-up and
scale-down policies and stabilisation windows) is only available here.

**CustomResourceDefinition → `apiextensions.k8s.io/v1`.** `spec.version`,
`spec.validation`, `spec.subresources` and `spec.additionalPrinterColumns` move under
`spec.versions[*]`; `spec.scope` is no longer defaulted; an
`openAPIV3Schema` structural schema is required; `spec.preserveUnknownFields: true` is
rejected and must become `x-kubernetes-preserve-unknown-fields` inside the schema.

**Admission webhooks → `admissionregistration.k8s.io/v1`.** Defaults changed in ways
that alter behaviour silently: `failurePolicy` from `Ignore` to `Fail`, `matchPolicy`
from `Exact` to `Equivalent`, `timeoutSeconds` from 30 to 10; `sideEffects` and
`admissionReviewVersions` became required.

## Deprecated but still served

- **`v1` Endpoints** is deprecated as of 1.33 in favour of EndpointSlice. It still
  works; do not hand-write Endpoints objects for new work, and do not read Endpoints to
  reason about a Service's backends when EndpointSlice is available.
- Beta APIs of any kind are disabled by default on new clusters unless the specific
  group/version is enabled. "It works on my cluster" for a beta version is a statement
  about flags, not about the version.

## Version gates for the fields this skill recommends

Taken from each feature gate's own stage table, not from memory. [official]

| Field / behaviour | Stable since | Notes |
|---|---|---|
| `initContainers[].restartPolicy: Always` (sidecar containers) | **1.33** | Beta and on by default from 1.29. This is how a sidecar gets started before, and terminated after, the app container. |
| `spec.hostUsers: false` (user namespaces) | **1.36** | Beta and on by default from 1.33. Maps container root to an unprivileged host uid. |
| In-place resize (`resizePolicy`, the `pods/resize` subresource) | **1.35** | Beta and on by default from 1.33; alpha 1.27–1.32. Lets CPU and memory change without recreating the pod. |
| Pod-level `spec.resources` | beta since **1.34** | Requests and limits for the pod as a whole rather than per container. Treat as not-yet-stable. |
| `unhealthyPodEvictionPolicy` on PodDisruptionBudget | **1.27** | `AlwaysAllow` lets unready pods be evicted so a drain is not wedged by them. |
| Pod Security Admission (`pod-security.kubernetes.io/*` labels) | **1.25** | Replaces PodSecurityPolicy, which was removed in the same release. |
| `seccompProfile.type: RuntimeDefault` required by restricted PSS | **1.19** field, **1.25** enforcement | The restricted profile tightened in 1.25; a manifest written for the 1.24 profile is rejected. |

When a rule needs a gate, state it and check the cluster: `kubectl version` for the
server minor, `kubectl api-resources` for what is actually served.

## Validating without a cluster

`kubectl apply --dry-run=client` is **not** offline validation. It downloads the
OpenAPI schema, and with `--validate=false` it still performs RESTMapper discovery, so
with no reachable cluster both forms fail: [verified]

```
error validating data: failed to download openapi: the server could not find the requested resource
couldn't get current server API group list: the server could not find the requested resource
```

What does work with no cluster:

```bash
# Schema validation against a specific server version (the real gate)
kubeconform -kubernetes-version 1.34.0 -strict -summary manifests/

# Render an overlay or a chart, then validate the rendered output
kubectl kustomize overlays/prod | kubeconform -kubernetes-version 1.34.0 -strict -
helm template rel ./chart      | kubeconform -kubernetes-version 1.34.0 -strict -
helm lint ./chart

# Generate a starting manifest locally
kubectl create deployment demo --image=nginx:1.29 --dry-run=client -o yaml
```

`kubeconform` reports a removed API version as `could not find schema for <Kind>`,
because no schema exists for that group/version at the requested release — which is
exactly the signal wanted. Validating the fixture in this skill's evals against 1.34.0
produces `Valid: 1, Errors: 2`, naming the `policy/v1beta1` PDB and the
`extensions/v1beta1` Ingress. [verified]

`-strict` rejects unknown fields. Without it a typo such as `resource:` instead of
`resources:` validates cleanly and is silently ignored by the server.

For CRDs, point `kubeconform` at extra schema locations with `-schema-location`;
otherwise pass `-ignore-missing-schemas` and accept that custom resources are unchecked.

## Validating against a cluster

When a cluster is reachable, two extra checks become available and are worth running
before an apply:

```bash
kubectl apply --dry-run=server -f manifests/   # runs admission, including webhooks and PSA
kubectl diff -f manifests/                     # what would actually change
```

`--dry-run=server` is the only form that exercises admission control, so it is the one
that tells you whether an `enforce: restricted` namespace will accept the pod spec.
`--dry-run=client` never does.

## Finding what a live cluster still uses

Before a cluster upgrade, the question is which *objects* use a version about to go
away, not which files do:

```bash
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis
kubectl api-resources --verbs=list -o name \
  | xargs -n1 kubectl get --show-kind --ignore-not-found -A -o name 2>/dev/null
```

The first line is the authoritative one: the API server emits
`apiserver_requested_deprecated_apis` with the group, version, resource and the release
in which it will be removed, for every deprecated API that is still being requested.

<!-- sources: kubernetes-docs, lukasniessen-k8s, helm-docs, kustomize -->
