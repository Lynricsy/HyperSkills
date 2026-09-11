# Resources, scheduling and disruption

Verified against: Kubernetes 1.37. Gates such as `(1.35+)` mark the minimum server version.

## Contents

- [Requests and limits are different things](#requests-and-limits-are-different-things)
- [QoS classes and eviction order](#qos-classes-and-eviction-order)
- [Memory: OOMKill](#memory-oomkill)
- [CPU: throttling](#cpu-throttling)
- [Where the numbers come from](#where-the-numbers-come-from)
- [Changing resources without recreating the pod](#changing-resources-without-recreating-the-pod)
- [Namespace guardrails](#namespace-guardrails)
- [Horizontal autoscaling](#horizontal-autoscaling)
- [PodDisruptionBudget](#poddisruptionbudget)
- [Placement: affinity, taints, topology spread](#placement-affinity-taints-topology-spread)
- [Priority and preemption](#priority-and-preemption)

## Requests and limits are different things

- **Request** is what the scheduler reserves. It decides which node the pod lands on and
  nothing else at run time (except that CPU requests become CFS shares under
  contention).
- **Limit** is the ceiling the kernel enforces. Memory over the limit is an OOMKill;
  CPU over the limit is throttling.

A pod with no requests is scheduled as if it were free, so the node accepts more work
than it can run. A pod with no memory limit can take the node down.

## QoS classes and eviction order

Assigned by the kubelet, not set by you:

| Class | Condition | Evicted under node pressure |
|---|---|---|
| `Guaranteed` | Every container has `requests == limits` for both CPU and memory | Last |
| `Burstable` | At least one request is set and it is not Guaranteed | Middle |
| `BestEffort` | No requests or limits anywhere in the pod | First |

`BestEffort` is not a choice, it is an omission. Nothing in production should be in it.

## Memory: OOMKill

Memory is incompressible: the kernel cannot give a process less memory, so exceeding
the limit means the cgroup's OOM killer terminates the process. The pod's container
status shows `lastState.terminated.reason: OOMKilled` and exit code 137.

```bash
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState.terminated}'
```

Exit 137 *with* reason `OOMKilled` is the limit. Exit 137 *without* it is a `SIGKILL`
from somewhere else (grace period expiry, node shutdown).

Set a memory limit on every container, and set it equal to the request unless you have
a specific reason not to: memory that is "burstable" is memory the scheduler did not
reserve, so the burst competes with whatever else landed on the node.

Runtime-specific trap: a JVM, .NET or Node heap that is not told about the cgroup limit
sizes itself from the *node's* memory and is OOMKilled at a fraction of what it thinks
it has. Modern runtimes read the cgroup, but only when the container is not given a
larger visible machine — check `-XX:MaxRAMPercentage`, `DOTNET_GCHeapHardLimit`,
`--max-old-space-size` before concluding the limit is too small.

## CPU: throttling

CPU is compressible. A CPU limit is implemented as a CFS quota: the cgroup gets
`limit × period` of CPU time per 100 ms period, and when it is spent the tasks are
descheduled until the next period — **even if the node is idle**. For a latency
sensitive service this shows up as p99 spikes with no visible load, and
`container_cpu_cfs_throttled_seconds_total` climbing.

The practical default: [community]

```yaml
resources:
  requests:
    cpu: 250m           # steady-state usage; drives scheduling
    memory: 512Mi
  limits:
    memory: 512Mi       # always
    # no CPU limit
```

Set a CPU limit when the cluster is multi-tenant and fairness must be enforced, when
the workload is batch and must not starve interactive pods, or when you deliberately
want Guaranteed QoS. Be explicit about the trade-off: without `requests == limits` for
both resources the pod is Burstable and is evicted before Guaranteed pods under node
pressure.

## Where the numbers come from

Not from round numbers. From measurement:

```bash
kubectl top pod -n <ns> --containers            # instantaneous, needs metrics-server
kubectl describe node <node> | sed -n '/Allocated resources/,/^Events/p'
```

Set the memory request at the observed steady-state working set plus headroom, and the
CPU request at roughly the observed p50–p90. Then check the node's *allocated* totals:
requests that sum well below capacity mean the cluster is paying for idle, and requests
that sum near capacity mean the next pod is Pending.

`kubectl describe node` also prints the difference between capacity and allocatable —
the kubelet and system reservations. Scheduling arithmetic uses allocatable.

## Changing resources without recreating the pod

In-place pod resize is stable from **1.35** (beta and on by default from 1.33): CPU and
memory in `spec.containers[].resources` are mutable through the `pods/resize`
subresource, and `status.containerStatuses[].resources` reports what is actually
configured.

```yaml
resizePolicy:
  - { resourceName: cpu,    restartPolicy: NotRequired }
  - { resourceName: memory, restartPolicy: RestartContainer }
```

Memory usually needs `RestartContainer` because shrinking a limit below current usage
cannot be honoured otherwise. Do not build workflows on this for clusters older than
1.33.

Pod-level `spec.resources` (requests and limits for the pod as a whole) is beta from
1.34 — useful where sidecars make per-container accounting wasteful, but not something
to depend on yet.

## Namespace guardrails

- `LimitRange` gives defaults and per-container maxima in a namespace, which is how a
  pod with no resources stops being BestEffort by accident. It applies at admission, so
  it does not retrofit existing pods.
- `ResourceQuota` caps the namespace's total requests and limits. Note the interaction:
  once a quota names `requests.cpu`, **every** pod in the namespace must set that
  request or it is rejected. Deploy `LimitRange` and `ResourceQuota` together or the
  quota breaks every manifest that omitted a field.

## Horizontal autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: checkout }
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies: [{ type: Percent, value: 50, periodSeconds: 60 }]
```

- Utilization is a percentage **of the request**, so an HPA on a container with no CPU
  request does nothing. This is the most common "the HPA never scales" cause.
- Do not set `replicas:` in a Deployment that an HPA manages, or a re-apply of the
  manifest fights the autoscaler. (Helm: template it out; Kustomize: leave the field
  absent.)
- Scale-down needs a stabilisation window or the autoscaler thrashes on a spiky signal.
- CPU utilisation is a proxy. For a queue consumer or a latency SLO, an external or
  custom metric describes the real load; CPU will scale the wrong way for an I/O-bound
  service.

## PodDisruptionBudget

A PDB constrains **voluntary** disruptions — `kubectl drain`, node pool upgrades,
descheduler moves. It does nothing about a node dying.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
spec:
  maxUnavailable: 1
  unhealthyPodEvictionPolicy: AlwaysAllow     # 1.27+
  selector:
    matchLabels:
      app.kubernetes.io/name: checkout
```

Two failure modes, both of which present as "the drain hung for an hour":

1. **Zero budget.** `minAvailable: 3` against `replicas: 3` allows no eviction at all,
   so the eviction API returns 429 forever and `kubectl drain` retries until its
   timeout. Express the budget as `maxUnavailable` so it tracks a replica-count change
   instead of silently becoming zero when someone scales down.
2. **Unhealthy pods wedging it.** With the default `IfHealthyBudget`, pods that are not
   Ready cannot be evicted while the budget is already at its edge — so an outage that
   makes pods unready also blocks the drain that would fix it.
   `unhealthyPodEvictionPolicy: AlwaysAllow` removes that deadlock.

A PDB with a selector matching no pods is silently useless. A PDB matching pods from
two different controllers constrains them jointly, which is almost never intended.

## Placement: affinity, taints, topology spread

Spread replicas before worrying about anything more exotic:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels: { app.kubernetes.io/name: checkout }
```

`whenUnsatisfiable: DoNotSchedule` makes the constraint hard — correct for spreading
across zones in a cluster that definitely has them, and a way to leave pods Pending
forever in one that does not. `ScheduleAnyway` is the safe default for
`kubernetes.io/hostname` spreading in a small cluster.

- **nodeSelector** is the simple form; **nodeAffinity** adds `preferred` and set-based
  operators.
- **podAntiAffinity** with `requiredDuringScheduling` over `kubernetes.io/hostname` is
  the older way to spread. It is O(pods²) to evaluate and caps replicas at the node
  count; prefer topology spread constraints.
- **Taints and tolerations** are the node's side of the conversation: a taint repels
  pods that do not tolerate it. A toleration does not attract a pod to a node — that
  still needs affinity. "Tolerated but not selected" is why a GPU workload ends up on a
  CPU node.

## Priority and preemption

`priorityClassName` decides who gets evicted when the scheduler needs room. Two
practical notes: system-critical add-ons already have high-priority classes, so a
workload given a higher number than those can starve the cluster's own components; and
`preemptionPolicy: Never` gives a pod a scheduling preference without letting it evict
anything, which is usually what "this is important" actually means.

<!-- sources: kubernetes-docs, lukasniessen-k8s, awesome-copilot, azure-aks-skills -->
