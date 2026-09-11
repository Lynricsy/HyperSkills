# Naming, subscriptions and resource structure

Verified against: Cloud Adoption Framework abbreviations and the ARM resource name rules as
published in `MicrosoftDocs/azure-docs`. Subscription and resource group limits are from the
Azure subscription and service limits article.

## Contents

- [The naming pattern](#the-naming-pattern)
- [Per-resource name rules](#per-resource-name-rules)
- [Resources that forbid hyphens](#resources-that-forbid-hyphens)
- [Generating names in IaC](#generating-names-in-iac)
- [Management groups, subscriptions, resource groups](#management-groups-subscriptions-resource-groups)
- [Hard limits that shape the design](#hard-limits-that-shape-the-design)
- [Tags](#tags)
- [Locks and moving resources](#locks-and-moving-resources)
- [Azure Policy](#azure-policy)
- [Joining an existing landing zone](#joining-an-existing-landing-zone)

## The naming pattern

```
<resource-type-abbreviation>-<workload>-<environment>-<region>-<instance>
```

`rg-orders-prod`, `vnet-shared-westeurope-001`, `app-orders-prod-001`. Lowercase, hyphen-separated,
zero-padded instance numbers, environment segment present even in production. Do not spell out the
resource type (`storageaccount-orders`), do not use uppercase (names are compared
case-insensitively, so casing is decoration that will not survive), and never encode a subscription
or tenant ID in a name.

The value of a convention is that a name can be parsed. Deviating for one resource type because it
reads better costs more than it saves.

## Per-resource name rules

| Resource | Abbr | Uniqueness | Length | Characters |
|---|---|---|---|---|
| Management group | `mg` | tenant | 1-90 | alphanumeric, `-`, `_`, `.`, `()` |
| Resource group | `rg` | subscription | 1-90 | alphanumeric, `-`, `_`, `.`, `()`; cannot end with `.` |
| Virtual network | `vnet` | resource group | 2-64 | alphanumeric, `_`, `.`, `-` |
| Subnet | `snet` | virtual network | 1-80 | alphanumeric, `_`, `.`, `-` |
| Network security group | `nsg` | resource group | 1-80 | alphanumeric, `_`, `.`, `-` |
| Public IP | `pip` | resource group | 1-80 | alphanumeric, `_`, `.`, `-` |
| Private endpoint | `pep` | resource group | 2-64 | alphanumeric, `_`, `.`, `-` |
| Front Door profile | `afd` | resource group | 5-64 | alphanumeric and `-` |
| Virtual machine | `vm` | resource group | 1-15 Windows / 1-64 Linux | no spaces or `~!@#$%^&*()=+_[]{}\|;:.'",<>/?` |
| App Service plan | `asp` | resource group | 1-60 | alphanumeric, `-` |
| Web app | `app` | **global** | 2-60 | alphanumeric, `-`; cannot start or end with `-` |
| Function app | `func` | **global** | 2-60 | alphanumeric, `-`; cannot start or end with `-` |
| AKS cluster | `aks` | resource group | 1-63 | alphanumeric, `_`, `-` |
| AKS node pool | `np` / `npsystem` | cluster | 1-12 Linux / 1-6 Windows | lowercase alphanumeric, cannot start with a digit |
| Container app | `ca` | resource group | 2-32 | lowercase alphanumeric and `-`; start with a letter, end alphanumeric |
| Container apps environment | `cae` | resource group | 2-60 | lowercase alphanumeric and `-` |
| Container registry | `cr` | **global** | 5-50 | **alphanumeric only** |
| Storage account | `st` | **global** | 3-24 | **lowercase letters and digits only** |
| Key vault | `kv` | **global** | 3-24 | alphanumeric and `-`; start with a letter, no consecutive hyphens |
| Managed identity | `id` | resource group | 3-128 | alphanumeric, `-`, `_` |
| Azure SQL server | `sql` | **global** | 1-63 | lowercase alphanumeric and `-` |
| PostgreSQL flexible server | `psql` | **global** | 3-63 | lowercase alphanumeric and `-` |
| Cosmos DB account | `cosmos` | **global** | 3-44 | lowercase alphanumeric and `-` |
| Service Bus namespace | `sbns` | **global** | 6-50 | alphanumeric and `-`; start with a letter |
| Event Hubs namespace | `evhns` | **global** | 6-50 | alphanumeric and `-`; start with a letter |
| API Management | `apim` | **global** | 1-50 | alphanumeric and `-`; start with a letter |
| App Configuration | `appcs` | **global** | 5-50 | alphanumeric and `-`; at most two consecutive hyphens |
| Log Analytics workspace | `log` | resource group | 4-63 | alphanumeric and `-` |
| Application Insights | `appi` | resource group | 1-260 | cannot use `%&\?/` |
| Data Explorer cluster | `dec` | **global** | 4-22 | **lowercase letters and digits only**, start with a letter |

Globally unique names live in public DNS (`<name>.blob.core.windows.net`,
`<name>.azurewebsites.net`), so a collision is with the whole world, not just your tenant. Put a
short deterministic suffix on every globally-unique name.

## Resources that forbid hyphens

Storage accounts, container registries and Data Explorer clusters take lowercase alphanumerics
only. This is the single most common template bug, because the general pattern produces
`st-orders-prod-001` and the compiler accepts it - the failure arrives from ARM at deployment, and
only after the rest of the deployment has partially run.

```
st{workload}{env}{instance}   -> stordersprod001
cr{workload}{env}{instance}   -> crordersprod001
dec{workload}{env}            -> decordersprod
```

## Generating names in IaC

```bicep
@minLength(3)
@maxLength(11)
@description('Short workload token, lowercase alphanumerics only')
param workloadToken string

var storageName = take('st${workloadToken}${uniqueString(resourceGroup().id)}', 24)
```

- `uniqueString()` returns 13 characters derived from its arguments. It is deterministic for the
  same inputs, which is what makes redeployment stable - and it changes if you change the seed, so
  seed it from something that does not move (`resourceGroup().id`, `subscription().subscriptionId`),
  never from `utcNow()`.
- `take()` truncates to the type's maximum. Truncating the *suffix* defeats the uniqueness, so put
  the hash last and truncate the whole string only when the prefix is already short.
- Some resource types reject names beginning with a digit; a literal prefix avoids that.
- Enforce the constraint at the parameter with `@minLength`/`@maxLength` so the failure is at
  compile time rather than mid-deployment.

## Management groups, subscriptions, resource groups

- **Management group** - the policy and RBAC boundary above subscriptions. Assign broad,
  long-lived roles and policies here; assignments at this scope do not count against a
  subscription's role assignment limit.
- **Subscription** - the billing, quota and scale boundary. Quotas are per subscription **per
  region**, so "we are out of vCPU" is solved by another subscription or another region, not by a
  bigger resource group. Split subscriptions along the axis you need to isolate: billing owner,
  environment, or regulatory boundary.
- **Resource group** - the lifecycle and deployment boundary. Everything in a resource group should
  be created and destroyed together. The resource group's own `location` stores only its metadata;
  resources inside it can live anywhere. Deleting the resource group deletes everything in it, in
  an order you do not control.

Environment separation belongs at the subscription level when the environments must not share
quota, policy or blast radius; resource-group separation within one subscription is acceptable for
dev and test only.

## Hard limits that shape the design

| Limit | Value |
|---|---|
| Management groups per tenant | 10,000 |
| Management group hierarchy depth | root plus 6 levels |
| Resource groups per subscription | 980 |
| Resources per resource group **per resource type** | 800 (some types exempt) |
| Deployments in a resource group's history | 800, oldest auto-deleted near the limit |
| Subscription-level and management-group-level deployments | 800 each |
| Tags per resource, resource group or subscription | 50 |
| Tag key / value length | 512 / 256 characters |
| Management locks per scope | 20 |
| Template parameters / variables / resources / outputs | 256 / 256 / 800 / 64 |
| Template size / parameter file size | 4 MB each |

The 800-outputs-per-history and 64-outputs-per-template limits are what force a large landing zone
into several deployments rather than one giant template.

## Tags

Tags do **not** inherit. A tag on a resource group is not on the resources inside it, and cost
reports group by resource tags. The two ways to make inheritance real:

- Azure Policy with the `modify` effect and the
  `Inherit a tag from the resource group` built-in definition, plus a remediation task for
  existing resources.
- Passing a `tags` object down through every module and spreading it onto every resource. This is
  what AVM modules expect (`tags: tags`).

A minimum useful tag set: `env`, `workload`, `owner`, `cost-center`, `managed-by` (the IaC repo or
stack that owns the resource). `managed-by` is the one that answers "can I delete this?".

## Locks and moving resources

`CanNotDelete` and `ReadOnly` locks are inherited downward and apply to everyone including Owners -
they are a guard against accident, not against privilege. `ReadOnly` breaks more than it protects:
it blocks control-plane writes that many services perform normally (listing keys is a POST), so
prefer `CanNotDelete`. A lock also blocks the delete half of a Complete-mode deployment, which
turns into a confusing deployment failure rather than a clear "this is locked".

Moving resources between resource groups or subscriptions (`az resource move`) is supported for
some types and not others, and the unsupported list is long (among them: VM scale sets with some
configurations, Managed Identities, and anything with a dependency that cannot move with it). The
move locks both source and target for the duration. Check the per-provider support list before
planning a move; the common alternative is redeploy-and-cut-over, which is also usually faster.

## Azure Policy

Policy is the mechanism that makes conventions binding. The effects, in order of how much they can
break:

| Effect | Behaviour |
|---|---|
| `audit` | Records non-compliance; changes nothing. Start here |
| `deny` | Rejects the deployment. The ARM error is `RequestDisallowedByPolicy` and names the assignment |
| `modify` | Adds or changes a property (tags, TLS version) on create/update; needs a managed identity on the assignment and a remediation task for existing resources |
| `deployIfNotExists` | Deploys a companion resource (diagnostic settings, an agent); needs a managed identity with the right role, and only evaluates on create/update plus periodic scans |
| `denyAction` | Blocks a specific action such as delete |

Two operational facts: policy evaluation for existing resources runs roughly every 24 hours, so a
compliance dashboard is never current after a change; and `deployIfNotExists` / `modify`
assignments whose identity lacks the required role fail silently at remediation time, showing as
non-compliant resources with no obvious cause.

When a deployment fails with `RequestDisallowedByPolicy`, read the policy definition before
requesting an exemption - the usual cause is a real convention violation, such as a resource in a
disallowed region or a storage account without the required TLS minimum.

## Joining an existing landing zone

Before writing any IaC into an enterprise landing zone, establish these, because they determine
what your template is even allowed to do:

- [ ] Which management group the subscription sits under, and which policy assignments are
      inherited from it (`az policy assignment list --disable-scope-strict-match`).
- [ ] Which regions are permitted, and whether a naming policy is enforced with `deny`.
- [ ] Whether networking is delegated: most landing zones own the VNet and hand out a subnet, so
      your template must take a subnet resource ID as a parameter rather than create one.
- [ ] Whether private endpoints and private DNS zones are centrally managed - if so, your template
      creates the private endpoint but not the DNS zone group.
- [ ] Which identity creates resources in your subscription and what role it holds; if it is
      Contributor, it cannot create role assignments and that has to be solved before the first
      deployment, not during it.

<!-- sources: awesome-copilot, azure-docs, microsoft-azure-skills, azure-landing-zone -->
