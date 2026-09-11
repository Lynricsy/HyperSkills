# Diagnosing a workload that will not run

Verified against: Kubernetes 1.37, kubectl 1.34.

## Contents

- [The contract](#the-contract)
- [First three commands](#first-three-commands)
- [Pending](#pending)
- [ImagePullBackOff and ErrImagePull](#imagepullbackoff-and-errimagepull)
- [CrashLoopBackOff](#crashloopbackoff)
- [OOMKilled](#oomkilled)
- [CreateContainerConfigError and CreateContainerError](#createcontainerconfigerror-and-createcontainererror)
- [Running but not Ready](#running-but-not-ready)
- [Terminating forever](#terminating-forever)
- [502 or 503 through an Ingress](#502-or-503-through-an-ingress)
- [DNS failures](#dns-failures)
- [Getting inside](#getting-inside)

## The contract

Two rules, borrowed from incident practice, that change the outcome more than any
command does:

**Read-only until asked.** Do not restart, delete, scale, cordon or drain anything
while investigating. A restart destroys the evidence — in particular the previous
container's logs and its termination state — and often "fixes" the symptom for long
enough to lose the cause.

**Evidence before conclusion.** "The pod is Pending" and "the node is NotReady" are
symptoms. Name the specific event, exit code, or unsatisfied predicate, and quote it.
If the evidence is not there, say what is missing rather than picking the most likely
story.

## First three commands

```bash
kubectl get pod -n <ns> -o wide
kubectl describe pod <pod> -n <ns>
kubectl get events -n <ns> --sort-by=.lastTimestamp | tail -30
```

`describe` carries the three things that resolve most cases: the container's
`State`/`Last State` (with `Reason` and `Exit Code`), the `Events` for that pod, and
the resolved spec as admission left it. Events are namespaced and expire (one hour by
default), so collect them before doing anything else.

When a container is restarting, the interesting logs are the *previous* instance's:

```bash
kubectl logs <pod> -n <ns> --previous
kubectl logs <pod> -n <ns> -c <container> --previous --timestamps
```

## Pending

Pending means unscheduled (or scheduled but not yet started). `describe` prints the
scheduler's reason; read it literally.

| Message | Cause |
|---|---|
| `Insufficient cpu` / `Insufficient memory` | No node has enough *allocatable* left for the pod's **requests**. Compare `kubectl describe node` "Allocated resources" against the request; actual usage is irrelevant here. |
| `node(s) had untolerated taint {…}` | The only candidate nodes are tainted and the pod has no toleration. Common on control-plane, GPU and spot pools. |
| `node(s) didn't match Pod's node affinity/selector` | `nodeSelector`/`nodeAffinity` names labels no node has. Check with `kubectl get nodes --show-labels`. |
| `node(s) didn't match pod topology spread constraints` | A `DoNotSchedule` constraint cannot be satisfied — frequently spreading across zones in a single-zone cluster. |
| `pod has unbound immediate PersistentVolumeClaims` | No PV matches, or the StorageClass has no provisioner, or it is `WaitForFirstConsumer` and something else blocks scheduling. |
| `0/N nodes are available: N Too many pods` | The node's pod limit (110 by default), not CPU or memory. |
| Nothing at all, no events | No scheduler is running, or the pod names a `schedulerName` that does not exist. |

A Pending pod with a cluster autoscaler present should trigger a scale-up; if it does
not, the reason is in the autoscaler's own events, and the usual cause is a request
larger than any node shape can ever satisfy.

## ImagePullBackOff and ErrImagePull

The event text names which of four it is:

- `manifest unknown` / `not found` — the tag or digest does not exist. Typos, and tags
  deleted by a retention policy.
- `unauthorized` / `authentication required` — no pull secret, the wrong one, or one in
  another namespace. `imagePullSecrets` is namespaced; a Deployment copied between
  namespaces loses it.
- `toomanyrequests` — registry rate limiting. Anonymous Docker Hub pulls hit this on a
  node that scales up frequently.
- `no match for platform` — an amd64-only image on an arm64 node, or the reverse.

Verify the reference from outside the cluster before touching manifests:

```bash
docker buildx imagetools inspect <ref>
```

A pod that ran yesterday and fails to pull today on a *new* node is the giveaway for
retention, rate limiting or a mutated tag: the old nodes still have the layers cached.

## CrashLoopBackOff

Not a cause — a statement that the container keeps exiting and the kubelet is backing
off (10s, 20s, 40s … capped at 5 minutes). Find the exit:

```bash
kubectl get pod <pod> -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.lastState.terminated.reason}{"\t"}{.lastState.terminated.exitCode}{"\n"}{end}'
kubectl logs <pod> --previous
```

| Signal | Meaning |
|---|---|
| Exit 0, restarting | The process finished. A Deployment expects a long-running process; this is usually a command that is really a Job, or a server that failed to bind and exited quietly. |
| Exit 1 or 2, with logs | Application error. The logs are the answer. |
| Exit 137 with `Reason: OOMKilled` | Memory limit. See below. |
| Exit 137 without `OOMKilled` | SIGKILL from elsewhere — grace period expired (the process ignores SIGTERM), or node shutdown. |
| Exit 143 | SIGTERM, handled. Something asked it to stop. |
| Exit 126 / 127 | The entrypoint is not executable / not found. Wrong path, missing shell in a distroless image, CRLF line endings in a script. |
| `Reason: Error` with no logs at all | The process never started writing. Check the command and args as *resolved* (`kubectl get pod -o yaml`), not as written in the chart. |
| Restarts but liveness is the trigger | `describe` shows `Liveness probe failed: …`. This is a probe problem, not an application crash. |

The liveness case is worth separating because the fix is the opposite of the instinct:
a liveness probe that checks a dependency turns that dependency's outage into a restart
loop across every replica, and increasing the timeout does not help. Move the check to
readiness.

## OOMKilled

```bash
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState.terminated}'
```

Then, before raising the limit:

- Is the limit lower than the process's genuine working set, or is the process leaking?
  Two OOMKills an hour apart with rising usage in between is a leak; an OOMKill under
  every burst is a limit.
- Does the runtime know about the limit? A JVM, .NET or Node process that sized its
  heap from the node's memory is OOMKilled well under what it believes is available.
- Is it the *sidecar* that died? `containerStatuses` names the container.
- Raising a memory limit also raises what the node must have. Check the node's
  allocatable before assuming the pod will schedule with the new number.

## CreateContainerConfigError and CreateContainerError

Almost always a missing reference, and `describe` names it: a ConfigMap or Secret that
does not exist in this namespace, a key that is not in it, or a volume referring to a
PVC that is not bound. The pod is scheduled, so this is not a resource problem.

`CreateContainerError` additionally covers a mount path colliding with a file, and an
image whose entrypoint cannot be resolved.

## Running but not Ready

`kubectl describe` shows `Readiness probe failed: …`. Distinguish three:

- The probe's path or port is wrong. `kubectl port-forward` to the pod and request it.
- The application is genuinely not ready — a dependency is down, which is the probe
  working correctly.
- The probe is too aggressive for the machine: `timeoutSeconds` shorter than the
  endpoint's real latency under load, so it flaps.

A pod that is Ready but receives no traffic is an endpoint problem, not a probe one:

```bash
kubectl get endpointslices -n <ns> -l kubernetes.io/service-name=<svc>
```

An empty list means the Service's selector does not match the pod's labels, or the
named `targetPort` does not exist on the container.

## Terminating forever

A pod stuck in `Terminating` is waiting for something:

- A **finalizer** on the object (`kubectl get pod <pod> -o jsonpath='{.metadata.finalizers}'`).
  Removing it by hand leaks whatever the finalizer was supposed to clean up — find the
  controller that owns it first.
- A **volume that will not unmount**, usually a network filesystem whose server is
  unreachable.
- The **node is gone**. The pod object survives until the node controller or a manual
  deletion removes it.

`--grace-period=0 --force` only deletes the API object. If the kubelet is alive, the
container may keep running; for a StatefulSet that is how you get two pods with the
same identity writing to the same volume.

## 502 or 503 through an Ingress

Work inward, one layer at a time:

1. **Does the Service have endpoints?** `kubectl get endpointslices -l
   kubernetes.io/service-name=<svc>`. Empty is the most common answer, and it means
   selector, labels or readiness.
2. **Does the pod answer directly?** `kubectl port-forward pod/<pod> 8080:8080` and
   request it. If it does, the problem is between the Service and the pod (port
   mismatch, `targetPort` naming).
3. **Does the Service answer?** Run a throwaway client in the cluster:
   `kubectl run tmp --rm -it --image=curlimages/curl --restart=Never -- curl -s
   http://<svc>.<ns>.svc:8080/healthz`.
4. **Only then the Ingress.** Its controller's logs name the upstream and the reason.
   A 503 from the controller usually means no endpoints; a 502 usually means the
   upstream refused or reset; a 504 means it did not answer in time.

A rollout that produces 502s only during the deploy is the graceful-shutdown story, not
a routing bug: endpoint removal is concurrent with SIGTERM, so a `preStop` delay is the
fix.

## DNS failures

```bash
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- nslookup <svc>.<ns>.svc.cluster.local
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=100
```

Three causes worth knowing:

- **An egress NetworkPolicy that does not allow DNS.** Denying egress without allowing
  port 53 to the DNS pods breaks every name lookup, and the application-level error
  says nothing about DNS.
- **`ndots: 5`.** The default search path means `example.com` is tried as
  `example.com.<ns>.svc.cluster.local` first, and so on — five failed lookups before
  the real one. Visible as latency, not failure. A trailing dot or a `dnsConfig` with a
  lower `ndots` fixes it for external-heavy workloads.
- **musl in Alpine** resolves differently from glibc: it queries A and AAAA in
  parallel and handles search domains and truncated UDP responses differently, which
  shows up as intermittent resolution failures that do not reproduce on a Debian-based
  image.

## Getting inside

```bash
kubectl debug -it <pod> --image=busybox:1.36 --target=<container>   # ephemeral container
kubectl debug node/<node> -it --image=busybox:1.36                  # a pod on the node's namespaces
kubectl exec -it <pod> -- sh                                        # only if the image has a shell
```

An ephemeral container joins the running pod's namespaces, which is how you inspect a
distroless container that has no shell, and it does not restart the pod. It cannot be
removed once added — the pod carries it until it is recreated.

`kubectl debug <pod> --copy-to=<name> --set-image=...` makes a copy of the pod with a
different image or command, which is the way to inspect a container that crashes
before you can attach.

<!-- sources: azure-aks-skills, lukasniessen-k8s, kubernetes-docs, google-skills -->
