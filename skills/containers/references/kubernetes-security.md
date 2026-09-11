# Workload security in Kubernetes

Verified against: Kubernetes 1.37. Gates such as `(1.36+)` mark the minimum server version.

## Contents

- [securityContext, field by field](#securitycontext-field-by-field)
- [Pod Security Standards and Pod Security Admission](#pod-security-standards-and-pod-security-admission)
- [ServiceAccounts and the projected token](#serviceaccounts-and-the-projected-token)
- [RBAC](#rbac)
- [Secrets](#secrets)
- [NetworkPolicy](#networkpolicy)
- [User namespaces](#user-namespaces)
- [The host escapes](#the-host-escapes)
- [Reviewing a manifest set](#reviewing-a-manifest-set)

## securityContext, field by field

Pod level applies to every container; container level overrides it and is where the
per-container fields live.

```yaml
spec:
  securityContext:                 # pod level
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001                 # group ownership applied to mounted volumes
    seccompProfile: { type: RuntimeDefault }
  automountServiceAccountToken: false
  containers:
    - name: app
      securityContext:             # container level
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        privileged: false
        capabilities:
          drop: ["ALL"]
```

| Field | What it actually does |
|---|---|
| `runAsNonRoot: true` | The kubelet refuses to start the container if the image's user resolves to uid 0. It cannot resolve a *username* on a distroless image, so pair it with a numeric `runAsUser` or a numeric `USER` in the image. |
| `allowPrivilegeEscalation: false` | Sets `no_new_privs`. Blocks setuid binaries from gaining privileges — the cheapest escalation path, and the one `sudo`-style tooling inside an image relies on. |
| `readOnlyRootFilesystem: true` | Mounts `/` read-only. Needs an `emptyDir` at every path the process writes (`/tmp` almost always). Stops an attacker from persisting a payload in the image's filesystem. |
| `capabilities.drop: ["ALL"]` | Removes the ~14 capabilities the runtime grants by default. Add back only what is needed; `NET_BIND_SERVICE` for a port below 1024 is the common one — or just listen above 1024. |
| `seccompProfile.type: RuntimeDefault` | Applies the container runtime's syscall filter. Without it the container has the full syscall surface, and the restricted Pod Security Standard rejects the pod. |
| `privileged: true` | Disables essentially every isolation mechanism. There is no partial version of this. |
| `fsGroup` | Recursively chowns volume contents on mount. On a large volume this makes pod start-up slow; `fsGroupChangePolicy: OnRootMismatch` avoids re-doing it every start. |

`runAsUser` at pod level is overridden by a container-level value, and a container
that sets `runAsUser: 0` defeats a pod-level `runAsNonRoot`. Check both levels when
reviewing.

## Pod Security Standards and Pod Security Admission

Three profiles, enforced by the built-in admission controller through namespace labels.
PodSecurityPolicy was removed in 1.25 and has no successor object.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shop
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.34
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

- **privileged** — no restrictions.
- **baseline** — blocks the known escapes: `privileged`, host namespaces, `hostPath`,
  most capability additions, unconfined seccomp/AppArmor.
- **restricted** — baseline plus: `runAsNonRoot: true`,
  `allowPrivilegeEscalation: false`, `capabilities.drop: ["ALL"]` and
  `seccompProfile.type` explicitly set to `RuntimeDefault` or `Localhost`.

The field people forget is `seccompProfile`. A pod with the other three is still
rejected by `enforce: restricted`, and the rejection happens at apply time in the
target cluster rather than in any local validation — which is why it usually surfaces
as a failed deploy rather than a failed review. `readOnlyRootFilesystem` and
`automountServiceAccountToken: false` are *not* required by the standard and are worth
adding anyway.

Pin `enforce-version` to a specific release. Without it the namespace follows the
latest policy definition and a cluster upgrade can start rejecting pods it used to
accept — the restricted profile tightened in 1.25, and nothing says it will not again.

Roll it out as `warn` and `audit` first, read the warnings, then flip `enforce`.
`kubectl label --dry-run=server` against a namespace reports what would be rejected.

## ServiceAccounts and the projected token

Every pod gets the namespace's `default` ServiceAccount unless told otherwise, and by
default its token is mounted at
`/var/run/secrets/kubernetes.io/serviceaccount/token`. A process that never calls the
Kubernetes API has no use for it, and an attacker inside the container does.

```yaml
spec:
  serviceAccountName: checkout      # a dedicated one, not default
  automountServiceAccountToken: false
```

Set it at pod level (the ServiceAccount object also has the field, but the pod's value
wins and is visible where it matters). Tokens are projected, audience-bound and
time-limited since 1.22, so a stolen token expires — but "expires in an hour" is not
"cannot be used".

Never grant permissions to `default`: every pod in the namespace that forgot to name a
ServiceAccount inherits them.

## RBAC

Rules to check in a review:

- **No wildcards in production Roles.** `verbs: ["*"]`, `resources: ["*"]` and
  `apiGroups: ["*"]` each turn a scoped Role into an unscoped one.
- **Role before ClusterRole.** A ClusterRoleBinding to a namespaced workload's
  ServiceAccount grants the permission in every namespace.
- **`create pods` is `become anything`.** A ServiceAccount that can create pods,
  Deployments, Jobs or CronJobs in a namespace can mount any other ServiceAccount's
  token in that namespace, and can request a privileged pod if admission allows.
  Similarly, `get secrets` in a namespace is every credential in it, and
  `escalate`/`bind` on RBAC objects is self-promotion.
- **`exec` and `portforward`** on pods bypass whatever the Service exposes.

```bash
kubectl auth can-i --list --as=system:serviceaccount:shop:checkout -n shop
```

That is the review command: it answers what the workload can actually do, rather than
what the Role appears to say.

## Secrets

- Base64, not encryption. `get secret` in the namespace returns the value. Encryption
  at rest is a cluster-level API server configuration, and is off unless someone turned
  it on.
- A literal in `env.value` is worse still: it is in the manifest, in version control,
  in `kubectl describe deployment`, and in every CI log that echoed the manifest.
- Prefer mounting a Secret as a volume over `envFrom`: environment variables leak into
  crash dumps, child processes and error reporters, and a volume-mounted Secret updates
  in place while an environment variable never does.
- Anything that reached a manifest, a log or an image is compromised: rotate it, do not
  merely remove it.
- For real key management use an external secrets operator or a CSI secret store; both
  end with a Kubernetes Secret unless the workload reads the provider directly, so
  understand which one you are getting.
- `imagePullSecrets` is per-namespace. A Deployment that works in one namespace and
  gives `ImagePullBackOff` in another is usually this.

## NetworkPolicy

Pod networking is flat: every pod can reach every other pod, in every namespace, until
a NetworkPolicy selects it. A namespace with no policy is unsegmented, not
"default-deny".

Policies are additive and allow-only — there is no deny rule. The way to get
default-deny is an empty-selector policy, then explicit allows:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: shop }
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
```

Points that cost time:

- Policies are **namespaced**; `podSelector` only ever selects pods in the policy's own
  namespace. Cross-namespace traffic needs `namespaceSelector`.
- Denying egress breaks DNS. Allow UDP/TCP 53 to the DNS pods or nothing resolves, and
  the symptom looks like an application bug.
- The CNI must implement NetworkPolicy. On a cluster whose CNI does not, the objects
  are accepted and ignored — a policy that appears to exist and enforces nothing.
- Policies select by label. A pod that is missing the label is simply not covered.

## User namespaces

`spec.hostUsers: false` (stable **1.36**, beta and on by default from 1.33) puts the
pod in its own user namespace, so uid 0 inside the container maps to an unprivileged
uid on the host. It is the strongest available mitigation for a container-breakout
class of bug, and it is the one thing `runAsNonRoot` only approximates.

Requires runtime support and, on older clusters, a kubelet feature gate. Volumes
mounted into the pod need id-mapping support in the CSI driver; without it, file
ownership looks wrong inside the container.

## The host escapes

Each of these removes a specific part of the boundary; all of them should be flagged
in a review unless there is a documented reason:

| Field | Consequence |
|---|---|
| `privileged: true` | Full device access, all capabilities, no seccomp. Equivalent to root on the node. |
| `hostNetwork: true` | The pod uses the node's network namespace: it can bind node ports, see all node traffic, and reach anything the node reaches. |
| `hostPID: true` | Sees and can signal every process on the node. |
| `hostPath` volume | Reads and writes the node's filesystem. Mounting `/var/run/docker.sock` or the containerd socket is root on the node; mounting `/` needs no further explanation. |
| `capabilities.add: ["SYS_ADMIN"]` | Effectively privileged. |
| A service account that can create privileged pods | The same escalation, one API call away. |

## Reviewing a manifest set

In order, because each answer changes what the next one means:

1. What does the pod run as — `runAsNonRoot`, numeric uid, `readOnlyRootFilesystem`,
   dropped capabilities, seccomp.
2. What does it mount — host paths, the service account token, Secrets as environment
   variables.
3. What can its identity do — `kubectl auth can-i --list --as=system:serviceaccount:…`.
4. What can reach it, and what can it reach — Service type, Ingress exposure,
   NetworkPolicy coverage.
5. Would the namespace's enforced Pod Security profile accept it — and if the namespace
   has no `pod-security.kubernetes.io/enforce` label, that is itself the finding.

<!-- sources: kubernetes-docs, lukasniessen-k8s, google-skills, awesome-copilot -->
