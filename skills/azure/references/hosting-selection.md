# Choosing a hosting service

Verified against: the Azure Container Apps comparison article and related product documentation as
published in `MicrosoftDocs/azure-docs`. Claims are `[official]`.

## Contents

- [Start from the constraints, not the service](#start-from-the-constraints-not-the-service)
- [The five realistic options](#the-five-realistic-options)
- [App Service](#app-service)
- [Container Apps](#container-apps)
- [When AKS is the right answer](#when-aks-is-the-right-answer)
- [Networking is usually the deciding constraint](#networking-is-usually-the-deciding-constraint)
- [Regions and availability zones](#regions-and-availability-zones)
- [Migrating between them](#migrating-between-them)

## Start from the constraints, not the service

Most hosting arguments are settled by four facts about the workload, and asking for them first
turns a preference debate into a lookup:

1. **Traffic shape.** Steady, bursty, or mostly idle? Anything that idles for hours wants a plan
   that scales to zero; anything with a hard latency floor does not.
2. **Network position.** Does it need to reach a private endpoint, or be reachable only
   privately? This eliminates more options than anything else.
3. **Operational appetite.** Who patches, upgrades and debugs it at 3am, and do they know
   Kubernetes?
4. **What the code already is.** A container, a web framework, or a set of event handlers.

"We might need Kubernetes later" is not a constraint. Moving a container from Container Apps to
AKS is a manifest and a pipeline change; moving a team onto Kubernetes it does not need is a
permanent cost.

## The five realistic options

| Service | Scales to zero | Kubernetes API | Best for |
|---|---|---|---|
| **App Service** | no | no | Web apps and HTTP APIs, code or container, with slots and easy custom domains |
| **Container Apps** | yes | no | Containerised microservices, event-driven workers, and jobs; Dapr and KEDA built in |
| **Functions** | yes (Flex/Consumption) | no | Event handlers with the trigger/binding programming model |
| **AKS** | no | yes | You need the Kubernetes API itself: operators, CRDs, service mesh, GPU scheduling, an existing Helm estate |
| **Container Instances** | n/a | no | A single isolated container on demand; a building block, not a platform - no scale, no load balancing, no certificates |

Azure Red Hat OpenShift exists and is the answer only when the organisation already runs OpenShift.

## App Service

- Plan tiers: Basic for dev, **Premium v3** for production (zone redundancy, larger instances,
  VNet integration), Isolated v2 for a dedicated App Service Environment. Free and Shared tiers
  have no SLA and no custom-domain TLS; do not put anything real on them.
- `alwaysOn` must be on for any non-Consumption plan, otherwise the app unloads after 20 minutes
  idle and the next request pays a full start.
- **Deployment slots** are the main reason to choose App Service over Container Apps for a
  classic web app: a swap warms the target first and is reversible. Slots are per plan tier -
  Basic has none.
- App settings are environment variables; they restart the app when changed. Key Vault references
  (`@Microsoft.KeyVault(SecretUri=...)`) resolve at start using the app's managed identity, so a
  rotated secret needs a restart to be picked up, and a missing role assignment presents as the
  literal reference string in the environment variable.
- One plan hosts many apps and they share its CPU and memory. A noisy neighbour in the same plan
  is indistinguishable from an application performance problem; check what else is on the plan
  before profiling.

## Container Apps

- Built on Kubernetes, KEDA, Dapr and Envoy, but the Kubernetes API is not exposed. If you need
  `kubectl`, CRDs or an operator, this is the wrong service and no workaround changes that.
- **Environment** (`Microsoft.App/managedEnvironments`) is the boundary: apps in one environment
  share a VNet, a Log Analytics workspace and internal DNS, and can call each other by app name.
  It is the unit of network isolation, so split environments by network boundary, not by team.
- **Workload profiles**: the Consumption profile is serverless and scales to zero; Dedicated
  profiles (D- and E-series) give reserved compute for workloads that need it, in the same
  environment. An environment can have both.
- **Scale rules** are KEDA scalers: HTTP concurrency, CPU/memory, or a queue length. `minReplicas: 0`
  is what gives scale to zero - and it also means the first request after idle pays a cold start,
  so a latency-sensitive app sets `minReplicas: 1` and stops being serverless.
- **Revisions**: single revision mode replaces on every deployment; multiple revision mode keeps
  old revisions and splits traffic between them, which is how you do blue/green or canary.
  Choosing single mode and then wanting canary is a mode change plus a revision-suffix convention.
- Ingress is `external` (public) or `internal` (only within the environment's VNet). There is one
  ingress per app with one target port; multi-port containers need separate apps or a sidecar.
- Jobs (`Microsoft.App/jobs`) cover scheduled and event-triggered batch work in the same
  environment, which removes the usual reason to add a separate Container Instances deployment.

The Dockerfile, image size, base image and multi-stage build are the `containers` skill's domain;
this skill covers the Azure resource around them.

## When AKS is the right answer

Pick AKS when at least one of these is true, and say which one:

- The workload needs the Kubernetes API: custom resources, operators, admission webhooks, a
  service mesh you configure yourself.
- You have an existing Helm/Kustomize estate and a team that operates it.
- You need node-level control: GPU scheduling, specific VM SKUs, host-level tuning, Windows
  containers alongside Linux.
- You are running enough distinct services that per-app platform overhead exceeds cluster
  overhead.

Six HTTP services and two queue workers is a Container Apps environment. The same eight services
with a service mesh, GPU inference and a platform team is AKS.

## Networking is usually the deciding constraint

| Requirement | App Service | Container Apps | Functions | AKS |
|---|---|---|---|---|
| Outbound to a private endpoint | VNet integration (Basic and above) | yes, environment is VNet-injected | Flex Consumption or Premium only - **not** Consumption | yes, nodes are in the VNet |
| Inbound private only | Private endpoint + `publicNetworkAccess: Disabled` | internal ingress | private endpoint on Premium/Flex | internal load balancer |
| Fixed outbound IP | NAT gateway on the integration subnet | NAT gateway on the environment subnet | NAT gateway | NAT gateway or Static Egress Gateway |

Two details that bite:

- VNet integration gives **outbound** access. Restricting **inbound** access is a separate
  control (private endpoint, access restrictions, internal ingress). Teams routinely add the
  first and believe they got the second.
- The delegated subnet for App Service integration or a Container Apps environment is dedicated -
  nothing else may use it - and the Container Apps minimum subnet size is `/27` for a workload
  profiles environment and `/23` for the legacy Consumption-only environment. The subnet, the
  choice between an Azure-managed network and your own VNet, and the external-versus-internal
  virtual IP are all fixed at environment creation; changing any of them means a new environment.

## Regions and availability zones

- Zone redundancy is a create-time property for a Container Apps environment and an AKS node pool;
  it is a plan-tier property for App Service (Premium v3 with `zoneRedundant: true`). None of
  them can be switched on later without recreating something.
- Zone redundancy protects against a datacentre failure inside one region. It does not protect
  against a regional outage, and it does not make a single-region database highly available - the
  composite SLA of a chain is the product of its parts, so one non-redundant dependency sets the
  ceiling.
- Not every region has zones, and not every service is in every region. Check both for the
  specific SKU before committing to a region:
  `az vm list-skus --location <region> --query "[?name=='Standard_D4s_v5'].locationInfo[].zones"`.

## Migrating between them

Common moves and what actually has to change:

| From | To | The real work |
|---|---|---|
| VM | Container Apps | Containerising the app and externalising state; the Azure resource is the easy part |
| App Service (code) | Container Apps | A Dockerfile, and replacing slot-swap deployment with revisions and traffic splitting |
| Container Apps | AKS | Manifests, ingress controller, an upgrade and patching process, and an on-call rota |
| Consumption Functions | Flex Consumption | A new app resource, a runtime upgrade, identity-based connections |
| Anything | Anything | Re-doing the identity: every managed identity and role assignment is attached to the old resource |

The last row is the one that gets missed in estimates. Plan the identity and its role assignments
first, because they are what makes the new resource able to reach the data it needs.

<!-- sources: azure-docs, microsoft-azure-skills, microsoftdocs-agent-skills, awesome-copilot -->
