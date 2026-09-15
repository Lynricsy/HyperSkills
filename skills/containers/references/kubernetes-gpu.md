# GPUs in containers and on Kubernetes

Verified against: Kubernetes 1.37, NVIDIA k8s-device-plugin, NVIDIA GPU Operator,
NVIDIA Container Toolkit, CUDA Compatibility guide, ROCm k8s-device-plugin.

Getting a GPU into a container — device plugin resource names, MIG and
time-slicing, driver and CUDA compatibility, topology-aware scheduling — belongs
to this skill; what a serving process does with the GPU once it has one — KV cache
sizing, batching, parallelism, benchmarking and scaling signals — belongs to the
`model-serving` skill.

## Contents

- [The resource contract](#the-resource-contract)
- [Is the device plugin actually there](#is-the-device-plugin-actually-there)
- [Sharing a GPU: time-slicing, MPS, MIG](#sharing-a-gpu-time-slicing-mps-mig)
- [MIG strategies and resource names](#mig-strategies-and-resource-names)
- [Runtime wiring](#runtime-wiring)
- [The variables that decide what the container sees](#the-variables-that-decide-what-the-container-sees)
- [Driver and CUDA version coupling](#driver-and-cuda-version-coupling)
- [What belongs in the image](#what-belongs-in-the-image)
- [Picking the right node](#picking-the-right-node)
- [Startup budget](#startup-budget)
- [Dynamic Resource Allocation](#dynamic-resource-allocation)
- [Draining and upgrading a GPU node](#draining-and-upgrading-a-gpu-node)
- [Diagnosing a GPU workload](#diagnosing-a-gpu-workload)
- [AMD and other vendors](#amd-and-other-vendors)

## The resource contract

A GPU is an extended resource, and extended resources are not CPU:

- **Declare it in `limits`.** You may write only `limits` (Kubernetes copies the
  value to `requests`), or both with **equal** values. Writing only `requests` is
  invalid. [official]
- **Integers only, and no overcommit.** [official] There is no `0.5` GPU.
- **Devices are not shared between containers** on the device-plugin path. Two
  containers in one Pod each asking for `nvidia.com/gpu: 1` get two *different*
  cards, not two handles on one. [official]
- The resource name follows `vendor-domain/resourcetype` and is whatever the
  plugin registered — `nvidia.com/gpu`, `amd.com/gpu`. A typo in the domain does
  not error; the Pod simply stays `Pending` forever. [official]

The QoS consequence is easy to miss: `nvidia.com/gpu` being equal on both sides
does nothing for the QoS class, which is still decided by CPU and memory. A Pod
that declares only a GPU limit is Burstable or BestEffort and is evicted before
Guaranteed Pods under node pressure (see `references/kubernetes-resources.md`).

## Is the device plugin actually there

The discriminator is whether the resource key **exists at all** in
`allocatable` — not whether its value is zero:

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

Empty output means no plugin or operator is running. A value that is merely too
small is an ordinary capacity problem. [community]

`Capacity: 8` with `Allocatable: 5` means **three devices were marked unhealthy**,
not a quota: the kubelet lowers `allocatable` and leaves `capacity` alone.
[official] Pods already placed on a failed device are **not rescheduled** — they
stay bound to it, entering `Failed` when `restartPolicy` is not `Always` and a
crash loop otherwise. [official] Per-device health, including messages such as
thermal events, is in the container status field `allocatedResourcesStatus`
(1.36+, beta, on by default). [official]

Plugin-side facts worth knowing when the plugin itself misbehaves: its socket
directory `/var/lib/kubelet/device-plugins` is hardcoded and unaffected by the
kubelet's `--root-dir`; a kubelet restart deletes every socket there and the
plugin must re-register itself. [official] `FAIL_ON_INIT_ERROR` now defaults to
`true`; setting it `false` makes a broken plugin **block silently forever**
instead of reporting. [official]

## Sharing a GPU: time-slicing, MPS, MIG

**Time-slicing provides no isolation of any kind.** The upstream wording is
explicit: nothing isolates workloads granted replicas of the same GPU, each has
access to the whole GPU memory, and they run **in one fault domain — if one
workload crashes, they all do**. [official] That is the fact most often missed
when a platform team "turns on GPU sharing".

Mechanically, `replicas: 10` **multiplies the advertised count**: an 8-GPU node
reports `Capacity: nvidia.com/gpu: 80`. [official] The 80 is allocatable units;
the memory is still that of 8 cards. Requesting several shared units does **not**
give proportional compute either — CUDA simply time-slices across all clients'
processes. [official]

Two configuration details decide whether a workload can even tell: [official]

- `renameByDefault: true` renames the resource to `<name>.shared`, e.g.
  `nvidia.com/gpu.shared`; default `false` leaves the Pod unable to tell whether
  its card was sliced.
- `failRequestsGreaterThanOne` **defaults differently per strategy**: the field is a
  `*bool`, and time-slicing leaves it unset, so the effective value is `false` for
  backward compatibility, while MPS forces it to `true` when unset ("preserve the
  historical MPS behavior"). The vendor recommends `true`. [verified] With `true`,
  a request above 1 is rejected at
  admission with `Warning UnexpectedAdmissionError ... request for 'nvidia.com/gpu: 2'
  too large: maximum request size for shared resources is 1`, and **the Pod does
  not self-heal — it must be deleted by hand**. Leaving it `false` is worse than
  it looks: the Pod starts happily with two references to one card, converting a
  clear admission error into an obscure out-of-memory failure later.

| Mechanism | Partitioning | Isolation | Notes |
|---|---|---|---|
| Time-slicing | temporal | **none** | shared memory and fault domain |
| MPS | spatial | per-client memory and compute limits, evenly 1/N | still **experimental** as of plugin v0.15.0; **unsupported on MIG-enabled devices** |
| MIG | hardware | hardware-enforced | **Ampere and newer only** |

Sharing is configured **per node, not per GPU** — the same method applies to
every GPU on the node, and time-slicing and MPS are mutually exclusive. Mixed
requirements need separate node groups selected by the
`nvidia.com/device-plugin.config` label. [official] Time-slicing can be applied
to `nvidia.com/gpu` and to the `nvidia.com/mig-*` resources produced by the mixed
MIG strategy; MPS only to whole `nvidia.com/gpu`. [official]

## MIG strategies and resource names

`MIG_STRATEGY`: `none` (plugin default, whole-card `nvidia.com/gpu`), `single` (GPU Operator chart's `mig.strategy: single` default), or `mixed`. [official] [verified]

| Strategy | Resource name | Requirement |
|---|---|---|
| `single` | still `nvidia.com/gpu`, one unit = one MIG instance | every GPU on the node must have the same MIG configuration |
| `mixed` | `nvidia.com/mig-<slices>g.<memory>gb`, e.g. `nvidia.com/mig-1g.10gb` | required when MIG is not enabled on all GPUs of a node |

GFD: `mixed` publishes per-profile counts (`nvidia.com/mig-1g.10gb.count: 2`); `single`
publishes instance count in `nvidia.com/gpu.count` and **rewrites `nvidia.com/gpu.product`**,
e.g. `NVIDIA-H100-80GB-HBM3-MIG-1g.10gb`, breaking plain-product affinity. [official]
**MIG changes are not hot:** MIG Manager labels the node and **terminates every GPU Pod** before changing mode/geometry; the vendor requires no user workloads, and some environments need reboot.
Cordon first, as for driver upgrades. Node-label configuration does not self-heal. [official]

```bash
kubectl label nodes <node> nvidia.com/mig.config=all-1g.10gb --overwrite
# success criterion: nvidia.com/mig.config.state == success  (pending / rebooting are transient)
```

The default `nvidia.com/mig.config: all-disabled` means installing MIG Manager
alone partitions nothing. [official] Drivers 570.124.06, 570.133.20, 570.148.08 and
570.158.01 leave GPU Pods indefinitely `Pending` on nodes with **both** MIG slices
and whole GPUs; the vendor advises moving to 570.86.15. [official]

## Runtime wiring

If the Container Toolkit was installed without making nvidia the default runtime,
Pods need a RuntimeClass: [official]

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: nvidia
handler: nvidia
```

Set `runtimeClassName: nvidia` in the Pod spec. Distinct failure modes:

| Configuration | Result |
|---|---|
| **Missing `runtimeClassName`**, nvidia not default | Container starts under the default runtime: Running Pod, no GPU wiring, no `/dev/nvidia*` or `nvidia-smi` |
| **Nonexistent RuntimeClass** or CRI unable to run its handler | Pod goes **straight to `Failed`**, not Pending or CrashLoopBackOff; read the event [official] |

RuntimeClass assumes homogeneous nodes: otherwise set `scheduling.nodeSelector`.
Admission **intersects** it with the Pod's selector, rejecting conflicts, and
**unions** `scheduling.tolerations` (1.16+). [official] `overhead` (1.24+ stable)
budgets the runtime's own node cost. [official]

CRI-O requires `/etc/crio/crio.conf.d/99-nvidia.conf` to override `10-crun.conf`;
add `crun` to `runtimes` in `/etc/nvidia-container-runtime/config.toml` or
nvidia-container-runtime cannot find the underlying runtime. [official]

## The variables that decide what the container sees

`docker run --gpus` and `--runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=…` are two
paths to the same thing. Using the variable **requires** `--runtime=nvidia` unless
nvidia is the default, otherwise it is just an ignored environment variable and
the container has no card. The device syntax needs doubled quoting:
`--gpus '"device=1,2"'`. [official]

`NVIDIA_VISIBLE_DEVICES` values, where the last two are the ones people confuse:
[official]

| Value | Effect |
|---|---|
| `all` | every GPU (**the default baked into CUDA base images**) |
| UUID or index list | those devices |
| `none` | no GPU, **but driver capabilities still injected** |
| `void`, empty, or unset | runtime behaves like plain `runc` — no GPU and no capabilities |

`NVIDIA_DRIVER_CAPABILITIES` selects which driver libraries are mounted:
`compute` (CUDA/OpenCL), `utility` (nvidia-smi and NVML), `graphics`, `video`,
`compat32`, `display`, `ngx`, plus `all` and `none`. **Unset or empty means only
`utility,compute`.** [verified]
The diagnostic that follows: **`nvidia-smi` works while the framework sees no
device means `compute` is missing and only `utility` was granted.**

`NVIDIA_REQUIRE_CUDA` (baked into official CUDA images as e.g.
`cuda>=11.0 driver>=450`) **refuses to start the container** when the driver is
too old — so the symptom is a container that never runs rather than a CUDA error
at runtime. Spaces are OR, commas are AND, and multiple `NVIDIA_REQUIRE_*` are
ANDed. The escape hatch `NVIDIA_DISABLE_REQUIRE=true` is intended only for base
images older than CUDA 11.7. [official]

The device plugin decides how it hands devices over via `DEVICE_LIST_STRATEGY`,
default `envvar` — it injects `NVIDIA_VISIBLE_DEVICES` and lets the NVIDIA
runtime pick. Alternatives are `volume-mounts`, `cdi-annotations` and `cdi-cri`;
the CDI ones do not need the NVIDIA runtime but do need a CDI-enabled engine.
[official] With `envvar`, one upstream behaviour matters for isolation: **a Pod
that does not request `nvidia.com/gpu` at all sees every GPU on the machine.**
[official] That is a failure of isolation, not an absence of GPUs.

## Driver and CUDA version coupling

Minor-version compatibility runs CUDA minors on older drivers within their major family, above a floor: [official]

| CUDA family | Minimum driver | Notes |
|---|---|---|
| 13.x | >= 580 | |
| 12.x | >= 525 | minor compatibility up to < 580 |
| 11.x | >= 450 | up to < 525 |
| 10.x | — | **no minor compatibility**; every minor needs a driver bump |

Minor compatibility boundaries: [official]

| Boundary | Requirement / failure |
|---|---|
| New feature requiring toolkit and driver support | Upgrade the driver; otherwise `cudaErrorCallRequiresNewerDriver` |
| **Device code compiled to PTX**, including framework JIT | Does not work on an older driver; upgrade required |
| Target architecture | Pass `-arch=sm_xx` to `nvcc` |

Below the floor: `cudaGetDeviceCount returned 3 -> initialization error`, not an obvious version complaint. [official]
`cuda-compat-<major>-<minor>` provides newer CUDA on older drivers (forward compatibility), with these limits: [official]

| Limit | Consequence |
|---|---|
| **Supported hardware only**: data-centre GPUs, some NGC-certified RTX cards, Jetson | Consumer cards return `CUDA_ERROR_COMPAT_NOT_SUPPORTED_ON_DEVICE (804)` |
| **Libraries only; loader not configured** | Set `LD_LIBRARY_PATH=/usr/local/cuda-X.Y/compat` (or `ld.so.conf`), otherwise installation is ineffective |
| **Upper bound**: old compat package incompatible with new driver | **Remove leftover compat packages** on full driver-plus-toolkit upgrades; old `libcuda` shadows the new driver, causing `CUDA_ERROR_SYSTEM_DRIVER_MISMATCH (803)` |
| CUDA only | OpenGL/Vulkan interop unsupported under every compat package; other driver components stay at the old version |

Minor compatibility links CUDA runtime to CUDA driver; forward compatibility links kernel driver to CUDA driver.
**PTX-JIT restrictions do not apply** to compat packages: use this path for PTX JIT without a driver upgrade. [official]

## What belongs in the image

Driver user-space libraries are **injected at container creation** from host or driver-container root;
a driver in the image guarantees version conflict: ship only CUDA runtime/toolkit. [official]
GPU Operator does not manage pre-installed host drivers: set `driver.enabled=false` or its container fights the host for kernel modules. [official]

CUDA bases set `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility`: [official]

| Image choice | Consequence |
|---|---|
| Distroless, `scratch`, or any non-NVIDIA runtime stage | **Drops both variables**, hence no CUDA libraries: works locally with `docker run --gpus`, breaks after changing base. Hand-built runtime images must set them explicitly |
| Keep `NVIDIA_VISIBLE_DEVICES=all`, no device-plugin constraint | Container sees every GPU on the machine |
| Layer in `cuda-compat-*` | Set the loader path in the image; the layer becomes wrong on a newer-driver node [official] |

## Picking the right node

The GPU extended resource is itself a scheduling constraint, so a Pod requesting
`nvidia.com/gpu` cannot land on a CPU node. What it does **not** constrain is
*which* GPU — that is what node selection is for, and it is the part usually
missing in a heterogeneous pool.

Labels to select on: [official]

- Node Feature Discovery publishes `feature.node.kubernetes.io/*` and can also
  taint nodes so only Pods asking for a feature land there.
- GPU Feature Discovery publishes `nvidia.com/gpu.present`,
  `nvidia.com/gpu.product`, `nvidia.com/gpu.count`, `nvidia.com/gpu.replicas`,
  `nvidia.com/gpu.memory`, plus `nvidia.com/gpu.sharing-strategy`
  (`none|mps|time-slicing`), `nvidia.com/mig.capable`, `nvidia.com/mps.capable`.
- Select memory numerically with the **`Gt`** operator against
  `nvidia.com/gpu.memory` rather than enumerating product names.

NVIDIA's own Pod examples carry
`tolerations: [{key: nvidia.com/gpu, operator: Exists, effect: NoSchedule}]`;
tainting GPU nodes is conventional, so omitting it yields
`node(s) had untolerated taint`. [official] Tolerating is not selecting — see
`references/kubernetes-resources.md`.

Multi-node NVLink has a real abstraction rather than an affinity rule: the DRA
driver's **`ComputeDomain`** guarantees MNNVL reachability between Pods inside the
domain and isolation from outside, with a lifecycle bound to the consuming
workload (1.32+ for that driver). [official] On the device-plugin side, IMEX
injection via `imex.channelIDs` / `imex.required` is a **global switch affecting
all workloads**; `channelIDs` currently accepts only `[]` or `[0]`, and
`required: false` silently injects nothing when no channel is found. [official]

## Startup budget

A GPU container's startup is dominated by work a CPU container never does:
driver initialisation, device memory allocation, and kernel compilation or PTX
JIT. Accelerator node and container startup latency is severe enough to change
placement decisions. [community] The practical consequence for a manifest is only
this: size `failureThreshold × periodSeconds` of a **startup probe** from a
measured GPU cold start rather than reusing the CPU service's budget. Probe
semantics themselves are in `references/kubernetes-workloads.md`.

## Dynamic Resource Allocation

| Contract | Consequence |
|---|---|
| DRA **stable since 1.35** | Locked `DynamicResourceAllocation` gate ignores explicit settings without error [official] |
| API **`resource.k8s.io/v1`** | `DeviceClass`, `ResourceClaim`, `ResourceClaimTemplate`, `ResourceSlice`, `DeviceTaintRule`; CEL selection via `selectors[].cel.expression` [official] |
| **No scheduler preemption for DRA resources** | High-priority Pods cannot take lower-priority Pods' devices: they stay Pending until the other Pod terminates or is deleted; PriorityClass offers no protection here [official] |
| `ResourceClaim` | **Shares one device across Pods**, self-managed lifecycle; `ResourceClaim.status.reservedFor` caps sharing at **256** entries/Pods [official] |
| `ResourceClaimTemplate` | Generates per-Pod claims that die with the Pod; referencing auto-generated claims is an anti-pattern [official] |
| Claim absent from namespace | Pod remains unscheduled, like a missing PVC [official] |

Feature maturity as of 1.37, because the sub-features are not all on: [official]

| Feature | State in 1.37 |
|---|---|
| Prioritized list (`requests[].firstAvailable[]`) | Stable since 1.36, on. **Selection is per-Pod**, so replicas of one ReplicaSet may land on different subrequests — the workload must tolerate heterogeneity |
| Partitionable devices (`sharedCounters` / `consumesCounters`) | 1.36 beta, on by default. The CounterSet must live in a *different* ResourceSlice from the device but the same pool |
| Consumable capacity (`allowMultipleAllocations`) | 1.36 beta, on by default |
| Device taints and `DeviceTaintRule` | **Stable since 1.37**, gates locked |
| Device compatibility groups | 1.37 **alpha, off**; also requires `DRAPartitionableDevices` |
| Workload ResourceClaims (PodGroup-level) | 1.37 **beta, off**. With the gate off, a matching template creates **no** claims rather than falling back to per-Pod ones |

| Device taint effect | Behaviour |
|---|---|
| `NoSchedule` | Prevents scheduling |
| `NoExecute` | Implies NoSchedule; kube-controller-manager evicts **by deleting Pods** |
| `None` | Scheduler and eviction controller ignore it; driver reports degraded health or dry-runs [official] |
| `DeviceTaintRule` without `deviceSelector` | **Taints nothing**, protecting against accidental cluster-wide eviction [official] |
| Safe tainting procedure | Publish `effect: None`, read status condition message, switch to `NoExecute`; scheduler/controller observation can race [official] |
| Claim covering all node devices | **Every** device must be untainted or tolerated; `adminAccess` is not exempt [official] |

NVIDIA moved to `kubernetes-sigs/dra-driver-nvidia-gpu`; its two kubelet plugins are **officially supported** ComputeDomain
and **GPU allocation, disabled by default in Helm and not yet supported** — caveat any GPU-allocation advice. [official]

## Draining and upgrading a GPU node

Driver upgrades **necessarily interrupt workloads**: every client stops for kernel-module unload/reload. [official]
GPU Operator's `nvidia.com/gpu-driver-upgrade-state` node label follows `upgrade-required` → `cordon-required` → `wait-for-jobs-required` → `pod-deletion-required` → `drain-required` (only if Pod deletion failed and drain is enabled) → `pod-restart-required` → `validation-required` → `uncordon-required` → `upgrade-done` / `upgrade-failed`. [official]

Defaults: [official]

| Setting | Default | Consequence |
|---|---|---|
| `autoUpgrade` | `true` | upgrades proceed unattended |
| `maxParallelUpgrades` | `1` | |
| `maxUnavailable` | `25%` | **counts already-cordoned nodes**, so an upgrade stalls silently when enough nodes are already cordoned |
| `drain.enable` | **`false`** | the default is "delete GPU Pods, do not drain" |
| `gpuPodDeletion.timeoutSeconds` | `300` | GPU Pods are **force-deleted** after this, finished or not |
| `force` | `false` | bare Pods survive unless set |

Fit `terminationGracePeriodSeconds` **inside** the deletion timeout or long requests die mid-flight.
Escape hatches: `autoUpgrade=false` pauses the state machine; `nvidia.com/gpu-driver-upgrade.skip=true`
skips a node; relabel failed nodes `upgrade-required` to retry; `daemonsets.updateStrategy: OnDelete`
gives you rollout pacing. [official] New functionality lands only in the upgrade controller:
do not build on the older `k8s-driver-manager` init-container path. [official]

Schedule MIG reconfiguration as the same planned interruption. [official] DRA's `NoExecute` device taint deletes Pods:
only claim-toleration `tolerationSeconds` gives long requests drain time; a PodDisruptionBudget does not help. [official]

## Diagnosing a GPU workload

Symptoms that the generic tables in `references/troubleshooting.md` cannot
explain, because they are not "insufficient resource" at all:

| Evidence | Cause |
|---|---|
| `allocatable` has no `nvidia.com/gpu` key at all | device plugin never registered [community] |
| `Capacity: 8`, `Allocatable: 5` | 3 devices unhealthy; bound Pods are not rescheduled [official] |
| `0/3 nodes available: 3 Insufficient nvidia.com/gpu` | ordinary capacity, compared against allocatable [community] |
| `Warning UnexpectedAdmissionError ... maximum request size for shared resources is 1` | requested more than one shared unit; **Pod will not self-heal** [official] |
| Running Pod, no `/dev/nvidia*`, no `nvidia-smi` | no nvidia runtime in effect (missing `runtimeClassName`) or the image dropped `NVIDIA_VISIBLE_DEVICES` [official] |
| `nvidia-smi` works, framework reports no CUDA device | `NVIDIA_DRIVER_CAPABILITIES` lacks `compute` [official] |
| `cudaGetDeviceCount returned 3 -> initialization error` | driver below the CUDA family's floor [official] |
| `CUDA_ERROR_SYSTEM_DRIVER_MISMATCH (803)` | leftover forward-compat package shadowing a new driver [official] |
| `CUDA_ERROR_COMPAT_NOT_SUPPORTED_ON_DEVICE (804)` | forward compat configured on unsupported hardware [official] |
| Pod `Failed` immediately, GPU-related event | `runtimeClassName` handler missing or unusable [official] |
| GPU Pods Pending on a node holding both MIG slices and whole GPUs | known driver defect on 570.124.06 / 570.133.20 / 570.148.08 / 570.158.01 [official] |

Ask the driver rather than the labels for the real MIG geometry: [official]

```bash
kubectl exec -n gpu-operator ds/nvidia-driver-daemonset -- nvidia-smi -L
```

The GPU Operator components worth naming when deciding which Pod to read:
`nvidia-driver-daemonset`, `nvidia-container-toolkit-daemonset`,
`nvidia-device-plugin-daemonset`, `gpu-feature-discovery`,
`nvidia-dcgm-exporter`, `nvidia-mig-manager`, `nvidia-operator-validator`,
`nvidia-cuda-validator`, plus a separate `node-feature-discovery`. [official]

## AMD and other vendors

The resource name is `amd.com/gpu` and the plugin targets Kubernetes 1.18+.
Two differences from the NVIDIA plugin matter operationally: enabling device
health checks requires a **privileged** Pod (it needs `/dev/kfd`), which
conflicts with the restricted Pod Security Standard; and node attribute labels
come from a separate `k8s-node-labeller` DaemonSet rather than the plugin itself.
[official]

<!-- sources: kubernetes-docs, nvidia-device-plugin, nvidia-gpu-operator, nvidia-container-toolkit, nvidia-cuda-docs, nvidia-dra-driver, rocm-device-plugin, google-skills -->
