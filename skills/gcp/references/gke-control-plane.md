# GKE control plane

Scope: creating and operating the cluster itself. Kubernetes manifests, Helm, Kustomize,
probes, resource limits and Pod security belong to the `containers` skill and are not repeated
here.

Verified against: Google Cloud SDK 584.0.0 (`gcloud container` help text); pricing and version
policy cross-read against cloud.google.com/kubernetes-engine.

## Contents

- [Autopilot or Standard](#autopilot-or-standard)
- [Autopilot's constraints](#autopilots-constraints)
- [Regional or zonal](#regional-or-zonal)
- [Release channels and version lifetime](#release-channels-and-version-lifetime)
- [What a cluster actually costs](#what-a-cluster-actually-costs)
- [Networking: VPC-native and IP planning](#networking-vpc-native-and-ip-planning)
- [Private clusters and control-plane access](#private-clusters-and-control-plane-access)
- [Workload Identity Federation for GKE](#workload-identity-federation-for-gke)
- [A production Autopilot cluster](#a-production-autopilot-cluster)
- [Standard node pools](#standard-node-pools)
- [Upgrades](#upgrades)
- [Connecting kubectl](#connecting-kubectl)

## Autopilot or Standard

| | Autopilot | Standard |
|---|---|---|
| Nodes | Google provisions, sizes, patches, repairs | you define node pools |
| Billing | per Pod CPU/memory/storage **request** | per underlying Compute Engine VM, idle or not |
| Node access | none — no SSH, no privileged DaemonSets, no host filesystem | full |
| Customisation | compute classes | machine type, image, kernel args, taints, local SSD |
| Right-sizing pressure | over-requesting costs money immediately | over-provisioned nodes cost money quietly |

Default to Autopilot. Choose Standard only for a requirement Autopilot cannot express:
privileged workloads, custom node images or kernel tuning, host networking, node-local
storage, or a licensing model tied to VM cores. "We might need it later" is not one of those —
migrating a workload from Autopilot to Standard is a cluster rebuild, but so is the reverse,
and Autopilot is the cheaper mistake.

## Autopilot's constraints

The ones that turn into deployment failures rather than design discussions:

- Minimum per Pod on the general-purpose (Balanced) class: **0.25 vCPU and 0.5 GiB**. A Pod
  requesting 50m CPU is billed and scheduled at the minimum.
- CPU:memory ratio must land between **1:1 and 1:8**. A Pod asking for 1 vCPU and 16 GiB is
  rejected or silently adjusted upward on one axis.
- Resource *requests* are what you pay for, and Autopilot sets limits equal to requests for
  CPU and memory. Tuning requests is the cost lever.
- No privileged containers, no `hostNetwork`/`hostPID`, restricted DaemonSets, no node SSH.
  Agents that expect to run as a privileged DaemonSet (some security and APM vendors) need
  their Autopilot-specific build.
- GPUs and TPUs work, via compute classes rather than node pools.

## Regional or zonal

A **regional** cluster replicates the control plane across three zones in the region; a
**zonal** cluster has one control-plane replica. During a zonal outage or a control-plane
upgrade, a zonal cluster's API server is unavailable — existing Pods keep running, but nothing
can be deployed, scaled or rescheduled, and the HPA stops acting.

Use regional for anything with an SLO. Note that this is the *control plane*'s topology;
worker placement is separate, and a Standard regional cluster spreads nodes across three zones
by default, multiplying `--num-nodes` by three.

## Release channels and version lifetime

| Channel | Position |
|---|---|
| `rapid` | earliest, no SLA on the versions themselves |
| `regular` | the default balance, a few months behind rapid |
| `stable` | most soak time |
| `extended` | same versions as regular, but a minor version stays supported up to **24 months** |
| no channel | **deprecated** — do not create new clusters this way |

Defaults, from the CLI's own help: if neither a channel nor a version is given, the cluster
enrols in **REGULAR**. If a version is given but no channel, it enrols in the most mature
channel where that version exists — STABLE first, then REGULAR, then RAPID. Channel clusters
have node auto-upgrade on by default; you control *when* it happens with maintenance windows
and exclusions, not *whether*.

Pinning a version does not stop upgrades. It stops them only until that version leaves the
channel, at which point GKE upgrades the cluster anyway. Plan for a minor version bump at
least yearly; the Extended channel buys time, not permanence, and costs extra once standard
support ends.

## What a cluster actually costs

- **$0.10 per cluster per hour**, flat, for every cluster regardless of mode, size or topology
  — Autopilot, zonal, multi-zonal and regional all pay the same fee.
- The GKE free tier gives **$74.40 of credit per billing account per month**, roughly one free
  Autopilot or zonal Standard cluster. It does **not** apply to the regional cluster fee.
- Clusters that have passed end of standard support and are running on the Extended channel's
  extended period pay an additional **$0.50 per cluster per hour** — $0.60 total.
- Standard node pools are billed as Compute Engine VMs whether or not Pods are scheduled on
  them. An idle three-node `e2-standard-4` pool costs the same as a busy one.

Ten small Standard clusters for ten teams cost $720/month in management fees before a single
Pod runs. Namespaces plus a shared Autopilot cluster is usually the cheaper multi-tenancy
answer; per-team clusters are worth it when the isolation is a compliance requirement.

## Networking: VPC-native and IP planning

Create VPC-native (alias IP) clusters — `--enable-ip-alias`, the default for new clusters.
Routes-based clusters are legacy: they consume VPC routes, cap cluster size, and cannot use
several newer features.

Three ranges matter and two of them cannot be resized after creation:

| Range | Sizing |
|---|---|
| node subnet primary range | one address per node, plus internal load balancer addresses |
| Pod secondary range | `max-pods-per-node` rounded up to a power of two, per node |
| Service secondary range | one per ClusterIP Service, cluster lifetime |

The default maximum is **110 Pods per node** on Standard (configurable up to 256), and GKE
allocates a **/24 (256 addresses) per node** for it — so a /21 Pod range supports eight nodes,
not 2048 Pods spread freely. Lowering `--default-max-pods-per-node` to 32 shrinks the per-node
block to /26 and quadruples the node count the same range supports. Getting this wrong caps
the cluster at a node count you discover during an incident; the fix is a new cluster.

## Private clusters and control-plane access

`--enable-private-nodes` gives nodes no external IPs — they reach the internet, if at all,
through Cloud NAT. This is the right default; budget for Cloud NAT before assuming image pulls
from public registries still work.

For control-plane reachability, prefer the **DNS-based endpoint** (`--enable-dns-access`):
access is authorized by IAM (`roles/container.developer` and friends) and resolved over DNS,
so there is no bastion host, no VPN path to a private endpoint, and no
`--master-ipv4-cidr` peering block to plan. Where the IP-based endpoint is still in use,
`--enable-master-authorized-networks` with an explicit CIDR list is mandatory — an unrestricted
public control-plane endpoint is the single most common GKE finding in an audit.

## Workload Identity Federation for GKE

`--workload-pool=PROJECT_ID.svc.id.goog` is the supported way for Pods to authenticate to
Google Cloud APIs. It is enabled by default on Autopilot and must be enabled explicitly on
Standard, on both the cluster and each node pool (`--workload-metadata=GKE_METADATA`).

Without it, Pods reach the node's metadata server and inherit the **node's** service account —
which means every Pod on the node has the same permissions, and in older projects that is the
Compute Engine default service account with `roles/editor`.

Bind a Kubernetes service account to a Google service account:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  checkout@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]" --quiet
```

and annotate the Kubernetes service account with
`iam.gke.io/gcp-service-account: checkout@PROJECT_ID.iam.gserviceaccount.com`. Newer
deployments can skip the Google service account entirely by granting a
`principal://...workloadIdentityPools/PROJECT_ID.svc.id.goog/subject/ns/NS/sa/KSA` member
directly on the target resource.

## A production Autopilot cluster

```bash
gcloud container clusters create-auto CLUSTER_NAME \
  --project=PROJECT_ID --region=us-central1 \
  --release-channel=regular \
  --enable-private-nodes \
  --enable-master-authorized-networks \
  --enable-dns-access \
  --enable-secret-manager \
  --quiet
```

Every flag earns its place: `regular` is the supported default channel, private nodes remove
public IPs from the data plane, authorized networks plus the DNS endpoint close the control
plane, and Secret Manager integration lets Pods mount secrets without a Kubernetes Secret
holding plaintext in etcd. Workload Identity Federation and Shielded nodes are already on for
Autopilot.

## Standard node pools

Create the cluster with a minimal default pool and add purpose-built pools rather than
growing one:

```bash
gcloud container node-pools create batch \
  --cluster=CLUSTER_NAME --project=PROJECT_ID --region=us-central1 \
  --machine-type=n2-standard-8 --spot \
  --enable-autoscaling --min-nodes=0 --max-nodes=20 \
  --node-taints=workload=batch:NoSchedule \
  --workload-metadata=GKE_METADATA --quiet
```

- `--spot` nodes cost far less and are reclaimed with 30 seconds' notice. Fine for batch and
  fault-tolerant inference; not for a stateful primary.
- Taint special-purpose pools so ordinary workloads do not land on them. The matching
  toleration lives in the workload manifest — that side is the `containers` skill's subject.
- `--min-nodes=0` lets a pool scale to nothing. The cluster autoscaler only scales down a node
  when every Pod on it can be evicted, so a single unevictable Pod (no PodDisruptionBudget,
  local storage, `kube-system` without a PDB) pins the node forever.
- Node auto-repair and auto-upgrade are on for release-channel clusters; leave them on.

## Upgrades

Control plane first, then nodes — GKE enforces version skew, and nodes may not be newer than
the control plane.

Two node upgrade strategies on Standard:

- **Surge** (default): adds up to `--max-surge` extra nodes and drains
  `--max-unavailable` at a time, rolling through the pool. Fast, and the pool needs spare
  quota for the surge nodes.
- **Blue-green**: creates a whole new node set, moves workloads, keeps the old set around for
  a soak window so a rollback is immediate. Costs double capacity during the window; correct
  for pools where a bad node image is expensive to discover late.

Control when, with maintenance windows and exclusions:

```bash
gcloud container clusters update CLUSTER_NAME --project=PROJECT_ID --region=us-central1 \
  --maintenance-window-start=2026-01-05T03:00:00Z \
  --maintenance-window-end=2026-01-05T07:00:00Z \
  --maintenance-window-recurrence="FREQ=WEEKLY;BYDAY=SA,SU" --quiet
```

Maintenance **exclusions** additionally block upgrades during a freeze, with scopes for
no-upgrades, no-minor-upgrades or no-minor-or-node-upgrades. An exclusion has a maximum length
and does not stop an upgrade forced by end of support.

## Connecting kubectl

```bash
gcloud container clusters get-credentials CLUSTER_NAME \
  --project=PROJECT_ID --region=us-central1
```

This writes a kubeconfig entry that shells out to **`gke-gcloud-auth-plugin`**. The plugin is
a separate gcloud component; if `kubectl` reports
`no Auth Provider found for name "gcp"` or an exec plugin failure, install it with
`gcloud components install gke-gcloud-auth-plugin` and confirm it is on `PATH`. A kubeconfig
copied from another machine carries the exec stanza but not the binary.

<!-- sources: gcp-docs, google-skills, bagelhole-devops -->
