# AKS control plane

Verified against: AKS pricing tiers and CNI networking documentation as published in
`MicrosoftDocs/azure-docs`. Commands were not executed locally; claims are `[official]`.

Scope: creating and operating the cluster as an Azure resource. Kubernetes objects that run *on*
the cluster - Deployments, Services, Ingress resources, probes, resource limits, Helm charts,
Kustomize overlays, pod security - are the `containers` skill's job.

## Contents

- [Day-0 versus Day-1](#day-0-versus-day-1)
- [Cluster SKU and tier](#cluster-sku-and-tier)
- [Pod IP model](#pod-ip-model)
- [Reserved CIDR ranges](#reserved-cidr-ranges)
- [API server access](#api-server-access)
- [Identity](#identity)
- [Node pools](#node-pools)
- [Version support and upgrades](#version-support-and-upgrades)
- [Registry access](#registry-access)
- [Creating a production cluster](#creating-a-production-cluster)
- [Cost levers](#cost-levers)

## Day-0 versus Day-1

The organising question for any AKS design review is which decisions survive the cluster.

**Day-0 - fixed at creation, requires rebuilding the cluster to change:**

- Pod IP model / network plugin (a kubenet-to-Overlay migration exists, but it is one-way,
  reimages every node pool and requires a user-assigned managed identity)
- Service CIDR and DNS service IP
- Which VNet and subnet the nodes live in
- Availability zones for a node pool (zones are set per node pool at creation)
- Private-cluster mode via Private Link

**Day-1 - can be enabled or changed later:**

- Pricing tier (`az aks update --tier standard`)
- Managed identity migration from a service principal
- Entra integration and Azure RBAC for Kubernetes authorization
- Auto-upgrade channel, maintenance windows
- Additional node pools, autoscaling, KEDA, monitoring add-ons
- Network policy engine

Say which bucket a finding is in. "Switch to Standard tier" is a one-line update; "switch to Azure
CNI Overlay" is a migration project.

## Cluster SKU and tier

Two independent dials. The SKU is `Base` or `Automatic`; the tier is `Free`, `Standard` or
`Premium`.

| Tier | Uptime SLA | Node ceiling | Use for |
|---|---|---|---|
| Free | none (best effort) | 1,000, recommended under 10 | dev, test, learning |
| Standard | 99.95% with availability zones, 99.9% without | 5,000 | production |
| Premium | same as Standard, plus 24-month Long Term Support | 5,000 | regulated or slow-moving estates |

- Free tier has every feature; what it lacks is a financially backed SLA on the API server. This
  is the cheapest production mistake to fix (`--tier standard`) and the most common to leave in
  place.
- Premium requires `--k8s-support-plan AKSLongTermSupport` set **together with** `--tier premium`;
  enabling and disabling LTS and Premium are a single operation.
- **AKS Automatic** is the recommended production default. It is preconfigured with the Standard
  tier, Node Auto Provisioning, up to 5,000 nodes, and a pod readiness SLA (99.9% of qualifying
  pod readiness operations complete within five minutes). Choose Base + Standard only when you
  need configuration that Node Auto Provisioning does not support.
- When the region has availability zones, the control plane is spread across them automatically on
  Standard and Premium, whether or not your node pools use zones. Your node pools still need
  `--zones 1 2 3` - the control-plane SLA says nothing about where your pods run.

## Pod IP model

| Option | Model | Choose it when |
|---|---|---|
| **Azure CNI Overlay** | overlay | Default for nearly everything. Pod IPs come from a separate CIDR, so VNet address space is not consumed. Supports the maximum node count the API server allows, at 250 pods per node |
| Azure CNI Pod Subnet | flat | Pods must be reachable by their own IP from the VNet, peered VNets or on-premises |
| Azure CNI Node Subnet | flat, legacy | Only for an existing cluster; limited scale and wasteful of VNet IPs |
| kubenet | overlay, legacy | Nothing new. **Retires March 31, 2028**; migrate to Azure CNI Overlay before then |

With Overlay, outbound pod traffic is SNAT'd to the node IP, so an on-premises firewall sees node
addresses. If a partner needs to allow-list individual pods, that is the case for Pod Subnet.

The data plane is a separate choice from IPAM: **Azure CNI powered by Cilium** (eBPF) works with
Overlay or Pod Subnet and provides network policy and better throughput than the iptables-based
data plane. Choose it at creation; switching the policy engine later has a window in which policy
is not enforced.

## Reserved CIDR ranges

AKS rejects a pod, service or cluster VNet range that overlaps any of these:

```
169.254.0.0/16
192.0.2.0/24
172.30.0.0/16
172.31.0.0/16
```

The trap: `172.16.0.0/12` contains both `172.30.0.0/16` and `172.31.0.0/16`, so it is an invalid
pod CIDR even though it is a perfectly ordinary private range. This fails at cluster creation with
a message about a reserved range, after the resource group and VNet already exist.

The other CIDR trap is the default service CIDR `10.0.0.0/16`, which collides with a large fraction
of hub-and-spoke address plans. It cannot be replaced after creation. Pick it deliberately and set
`--dns-service-ip` inside it.

## API server access

- **Public with authorized IP ranges** (`--api-server-authorized-ip-ranges`) - simplest, and
  enough for most teams that already have a bastion or a VPN with fixed egress.
- **Private cluster** (`--enable-private-cluster`) - the API server gets a private endpoint and a
  private DNS zone. Anything that talks to the API server (CI, developer laptops) now needs VNet
  connectivity or a self-hosted runner. A classic Private Link private cluster cannot simply be
  turned back into a public one.
- **API Server VNet Integration** - the API server is projected into your subnet. Once enabled it
  cannot be disabled.

Decide this before creation and write down who needs `kubectl` access and from where; retrofitting
private access is where teams discover their pipeline cannot reach the cluster.

## Identity

Three different identities, frequently confused:

| Identity | What it is for |
|---|---|
| Cluster identity (control plane) | Managing Azure resources for the cluster: load balancers, disks, route tables |
| Kubelet identity | Pulling images (this is what `--attach-acr` grants `AcrPull` to) |
| Workload identity | Pods authenticating to Azure services via Entra |

Rules:

- `--enable-managed-identity`, never `--service-principal` with a secret. A service principal
  secret expiring on a running cluster presents as "cannot create a load balancer / attach a disk /
  scale", not as an authentication error, which makes it expensive to diagnose.
- Prefer a user-assigned cluster identity (`--assign-identity`) - it survives cluster recreation,
  can be granted network permissions before the cluster exists, and is a prerequisite for the
  kubenet-to-Overlay migration.
- `--enable-aad --enable-azure-rbac` makes Kubernetes authorization go through Entra and Azure
  role assignments (`Azure Kubernetes Service RBAC Cluster Admin`,
  `... RBAC Reader`, `... RBAC Writer`), so access is auditable per user and revocable centrally.
- `az aks get-credentials --admin` returns a static cluster-admin client certificate. It bypasses
  Entra entirely, cannot be attributed to a person, does not expire and cannot be revoked short of
  rotating cluster certificates. Add `--disable-local-accounts` at creation so it does not exist.
- `--enable-oidc-issuer --enable-workload-identity` is what lets a pod get an Entra token with no
  secret. Each workload then needs a federated identity credential whose subject is
  `system:serviceaccount:<namespace>:<serviceaccount>`, and the federated-credential constraints
  apply: 20 per identity, no wildcards, and silent failure on a wrong subject.

## Node pools

- A **dedicated system node pool** with at least two nodes, tainted `CriticalAddonsOnly=true:NoSchedule`,
  keeps CoreDNS and metrics-server off the same nodes as your workloads. A single-pool cluster
  means an application memory leak can evict cluster DNS.
- System node pools need at least 4 vCPU and cannot use burstable (B-series) VMs. B-series throttle
  when their CPU credits run out, which shows up as intermittent latency rather than as a resource
  limit.
- Node pool names are 1-12 lowercase alphanumeric characters on Linux (1-6 on Windows) and cannot
  start with a digit. `npsystem` and `npuser01` fit; `system-pool` does not.
- Zones are set per node pool at creation and cannot be added later. Spreading one pool across
  `1 2 3` is not the same as three pools; both are valid, the first is simpler.
- Ephemeral OS disks (`--node-osdisk-type Ephemeral`) boot faster and cost less, at the price of
  losing the OS disk on deallocation - correct for stateless nodes, which is all of them.
- Node Auto Provisioning picks VM sizes from pending pod requirements instead of scaling a fixed
  pool. It is the default in AKS Automatic and usually beats hand-tuned cluster autoscaler
  min/max counts.

## Version support and upgrades

AKS supports the three most recent minor versions (N-2); each stays in community support for about
a year, after which the cluster is unsupported and eventually cannot be scaled or modified.
Premium tier plus `AKSLongTermSupport` extends a designated version to 24 months.

A version literal pinned in a provisioning script is a slow-motion outage. Instead:

- `--auto-upgrade-channel patch` for the control plane (or `stable` if you accept minor bumps)
- `--node-os-upgrade-channel NodeImage` for node OS patching
- `az aks maintenanceconfiguration add` for `aksManagedAutoUpgradeSchedule` and
  `aksManagedNodeOSUpgradeSchedule`, so the upgrade lands in a window you chose
- PodDisruptionBudgets on every production workload, because an upgrade drains nodes - this part
  is a `containers` concern but the upgrade will expose its absence

`az aks get-upgrades -g <rg> -n <cluster>` lists what the cluster can move to right now.

## Registry access

`--attach-acr <registry>` creates an `AcrPull` role assignment for the kubelet identity on the
registry. That is the whole mechanism: no secret, no `imagePullSecrets`, nothing in a namespace.

Enabling the ACR admin user and distributing a `docker-registry` secret replaces that with a
shared credential that has push as well as pull, cannot be attributed to a person in the registry
audit log, and must be created in every namespace that needs it. If image pulls fail after
`--attach-acr`, check the role assignment on the *kubelet* identity (not the cluster identity) and
the propagation window, rather than falling back to the admin user.

## Creating a production cluster

```bash
az aks create \
  --resource-group "$RG" --name "$CLUSTER" --location "$LOCATION" \
  --tier standard \
  --zones 1 2 3 \
  --vnet-subnet-id "$NODE_SUBNET_ID" \
  --network-plugin azure --network-plugin-mode overlay \
  --network-dataplane cilium --network-policy cilium \
  --pod-cidr 10.244.0.0/16 --service-cidr 10.245.0.0/16 --dns-service-ip 10.245.0.10 \
  --enable-managed-identity --assign-identity "$UAMI_ID" \
  --enable-aad --enable-azure-rbac --disable-local-accounts \
  --enable-oidc-issuer --enable-workload-identity \
  --node-count 3 --node-vm-size Standard_D4s_v5 --node-osdisk-type Ephemeral \
  --nodepool-name npsystem --nodepool-taints CriticalAddonsOnly=true:NoSchedule \
  --auto-upgrade-channel patch --node-os-upgrade-channel NodeImage \
  --attach-acr "$ACR_NAME"
```

Do not treat the CIDRs as copy-paste values - they must come from the address plan of the VNet the
cluster joins. Add the user node pool separately with `az aks nodepool add`.

Prefer expressing all of this in Bicep (`Microsoft.ContainerService/managedClusters`) or the AVM
module, so the Day-0 decisions are reviewable in a diff instead of buried in a script's defaults.

## Cost levers

- Spot node pools (`--priority Spot --eviction-policy Delete`) for interruptible batch work; they
  can be evicted with 30 seconds' notice, so nothing with state belongs there.
- `az aks stop` / `az aks start` deallocates the whole cluster for dev and test. Stopping is not
  the same as scaling to zero - the control plane stops billing too.
- Reservations and savings plans apply to the node VMs, not to the cluster management fee.
- The cluster management fee is per cluster, so many small clusters cost more in fixed fees than
  one cluster with namespace isolation. Weigh that against the blast radius you want.

<!-- sources: aks-skills, microsoft-azure-skills, azure-docs -->
