---
name: azure
description: "Guides Azure control-plane and architecture work: Bicep and Azure Verified Modules, what-if preflight, deployment stacks, azd projects, CAF naming and subscription structure, Microsoft Entra ID, managed identity, federated credentials and Azure RBAC, choosing between App Service, Container Apps, Functions and AKS, the AKS control plane, Resource Health and Activity Log diagnosis, quotas, cost and Well-Architected reviews. Use when reading or writing .bicep, .bicepparam or azure.yaml, when an az deployment fails, when a role assignment does not grant what was expected, or when picking an Azure service or region. Do not use for Terraform, HCL or .tf files, including the azurerm provider (use the `terraform` skill), Kubernetes manifests, Helm charts or container images (use the `containers` skill), .NET code (use the `csharp-dotnet` skill), OpenTelemetry instrumentation or alert pipelines (use the `observability` skill), AWS, GCP, or LLM applications on Azure AI Foundry."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# azure

## Scope

Covers Azure as a control plane and as a set of architectural choices: resource orchestration
with Bicep, Azure Verified Modules and the Azure Developer CLI; naming and the management
group / subscription / resource group hierarchy; Microsoft Entra ID identities and Azure RBAC;
selecting and configuring App Service, Container Apps, Functions and virtual machines; the AKS
control plane; diagnosing a resource through Resource Health, the Activity Log and diagnostic
settings; quotas, capacity and cost; and Well-Architected reviews.

Written against the current generally available services. Rules that depend on a specific
version carry a gate such as `(Bicep 0.47+)`, and facts reproduced on this machine are marked
`[verified]`; everything else is `[official]`, taken from Microsoft's documentation rather than
from a running subscription.

Not covered:

- Kubernetes objects and container images: Dockerfiles, Compose, manifests, Helm, Kustomize,
  probes, resource limits, pod security. Use the `containers` skill. This skill owns the AKS
  cluster as an Azure resource - tier, networking model, node pools, identity, upgrades.
- Terraform and HCL: module design, state, `terraform test`, the `azurerm` provider's syntax.
  Use the `terraform` skill. Bicep, ARM templates, deployment stacks and azd belong here.
- Application code in any language. Use `csharp-dotnet`, `python`, `typescript`,
  `nodejs-backend` and their peers. This skill covers the Azure resource the code runs on and
  the identity it authenticates with.
- Instrumentation and alerting practice: OpenTelemetry, span design, semantic conventions, RED
  and USE metrics, SLOs, alert routing, on-call. Use the `observability` skill. Azure Monitor,
  Application Insights and Log Analytics as *Azure resources* - diagnostic settings, retention,
  ingestion cost, workspace placement - belong here.
- AWS and GCP. Cross-cloud comparison only where a decision genuinely turns on it.
- Building LLM applications on Azure AI Foundry or Azure OpenAI. No skill in this library covers
  it yet; say so rather than improvising. Provisioning the accounts and quota for those services
  is ordinary Azure work and does belong here.

Paths below are relative to this skill's directory.

## Core rules

1. `bicep build` succeeding proves the template compiles, not that it deploys. Resource name
   rules, quota, RBAC, policy and the existence of referenced resources are all enforced by ARM
   at deployment time. Close that gap with `what-if`, not with a second reading
   (`references/bicep-and-avm.md`).
2. The linter's security rules are warnings by default, so `bicep build` exits 0 on a template
   that returns a storage key from an output. Measured on **Bicep 0.47.16**: four warnings, exit
   0; after raising `outputs-should-not-contain-secrets` to `error` in `bicepconfig.json`, exit 1
   `[verified]`. `use-recent-api-versions` is off entirely until enabled with a `maxAgeInDays`
   setting `[verified]`. A CI step that runs `bicep build` without that file is not a gate.
3. Storage accounts and container registries take lowercase letters and digits only, 3-24 and
   5-50 characters. The general `<type>-<workload>-<env>` pattern produces an illegal name for
   both, and the compiler accepts it (`references/naming-and-structure.md`).
4. A `Microsoft.Authorization/roleAssignments` name must be a GUID, and it must be derived with
   `guid(scopeId, principalId, roleDefinitionId)` so redeployment is idempotent. `newGuid()` is
   legal only in a parameter default and would create a new assignment every deployment.
5. Reach for a symbolic reference (`plan.id`, `storage.listKeys()`, `site.identity.principalId`)
   rather than `resourceId()` / `reference()` / `listKeys(resourceId(...))`. The string forms
   erase the dependency edge, which is why templates that use them need a hand-written
   `dependsOn` - the explicit `dependsOn` is the symptom.
6. Nothing sensitive goes in a deployment output. Outputs are persisted in the resource group's
   deployment history in plaintext and are readable by anyone with read access on the scope;
   `@secure()` masks CLI output and changes nothing about that.
7. Pin Azure Verified Modules to an exact version (`br/public:avm/res/storage/storage-account:0.30.0`)
   and check the module's `ModuleStatus` in the AVM index before adopting it - `Orphaned` modules
   still resolve and deploy but have no owner.
8. Never run `--mode Complete` without reading the what-if first: it deletes every resource in
   the resource group that is not in the template. Deployment stacks give the same authority with
   an explicit `--action-on-unmanage` policy and deny settings that stop portal edits
   (`references/deployment-and-azd.md`).
9. Treat a `-` (Delete) line in what-if as a stop condition and a `*` (Ignore) line as missing
   information - `*` means the resource was not analysed, not that it is unchanged.
10. A management-plane role does not grant data-plane access. `Storage Account Contributor` does
    not read blobs and `Key Vault Contributor` does not read secrets; they only let the caller
    fetch the account keys, which is the failure, not the workaround
    (`references/entra-and-rbac.md`).
11. A subscription supports **4000 role assignments** and the limit cannot be raised. Assignments
    at management-group scope and PIM-eligible assignments do not count, so group-based and
    management-group-scope assignments are the way out of a full subscription.
12. Prefer workload identity federation over any long-lived secret for CI. A federated credential
    with a wrong `subject` is created **without error** and fails only at token exchange; there
    is a maximum of 20 per identity and wildcards are not supported.
13. `Key Vault Secrets User` does nothing on a vault still using access policies. The vault needs
    `enableRbacAuthorization: true` before any role assignment on it has an effect, and no error
    is raised in the meantime.
14. The Consumption (`Y1`) Functions plan cannot do virtual network integration at all. Reaching
    a private endpoint from a Function App is a plan migration to Flex Consumption or Premium,
    not a setting (`references/functions.md`).
15. Flex Consumption is the recommended serverless Functions plan: Linux only, 512 / 2048 /
    4096 MB instances, up to 1000 instances against Consumption's 200, and a shared regional
    quota of 250 cores per subscription that can cap scale below the configured maximum.
    `alwaysOn` does nothing on Consumption; cold starts there are fixed with always-ready
    instances (Flex) or pre-warmed instances (Premium), never with a keep-alive timer.
16. An extension bundle range is a version contract: `[4.*, 5.0.0)` loads Service Bus extension
    5.x with flat `maxConcurrentCalls`, while bundle v2 and v3 load extension 4.x where the same
    setting lives under `messageHandlerOptions`. The host silently ignores settings it does not
    recognise, so a mismatched `host.json` runs entirely on defaults.
17. AKS Day-0 decisions - pod IP model, service CIDR, node subnet, availability zones,
    private-cluster mode - cannot be changed on an existing cluster. Say which bucket a finding
    is in before proposing it (`references/aks-control-plane.md`).
18. kubenet is legacy and **retires March 31, 2028**; Azure CNI Overlay is the default choice.
    AKS also rejects pod, service or VNet ranges overlapping `169.254.0.0/16`, `192.0.2.0/24`,
    `172.30.0.0/16` or `172.31.0.0/16` - which makes the ordinary-looking `172.16.0.0/12` an
    invalid pod CIDR.
19. The AKS Free tier has no financially backed SLA and is recommended below about 10 nodes.
    Standard and Premium give 99.95% API-server availability with availability zones and 99.9%
    without; AKS Automatic is the recommended production default and is preconfigured to
    Standard.
20. `az aks get-credentials --admin` hands out a static cluster-admin certificate that bypasses
    Entra, cannot be attributed to a person and cannot be revoked. Create clusters with
    `--enable-aad --enable-azure-rbac --disable-local-accounts`.
21. Resource logs are **off by default** and are not retained anywhere until a diagnostic setting
    routes them. This cannot be fixed retroactively during an incident
    (`references/diagnostics.md`).
22. Check Resource Health and the Activity Log before reading logs. Most incidents are a change,
    and the Activity Log names the caller and the correlation ID; it retains 90 days and records
    control-plane operations only.
23. Never quote an Azure price from memory. Get the current figure from the Retail Prices API or
    Cost Management, state the region, SKU and volume assumptions, and show the arithmetic
    (`references/cost-and-quotas.md`).
24. Discover a quota name with `az quota list` and match on `localizedValue`. There is no 1:1
    mapping from an ARM resource type to a quota name, and a REST or portal reading of
    "No Limit" means the quota API does not model that type, not that capacity is unlimited.
25. Where a local failure can be reproduced, use the `debugging` skill; where only production
    signals exist (logs, metrics, traces, alerts), this is the `observability` skill's job.

## Workflows

### author-or-review-a-bicep-template

- [ ] Read `bicepconfig.json` first. Without it the linter's security rules are warnings and the
      build exits 0 regardless (`references/bicep-and-avm.md`).
- [ ] Check every generated name against its type's rules - length, charset, global uniqueness -
      paying attention to storage accounts and container registries, which forbid hyphens
      (`references/naming-and-structure.md`).
- [ ] Replace `resourceId()` / `reference()` / `listKeys(resourceId(...))` with symbolic
      references and delete the `dependsOn` they required.
- [ ] Remove every secret from outputs and from `appSettings`, and replace it with a managed
      identity plus a data-plane role assignment (`references/entra-and-rbac.md`).
- [ ] Check role assignments: GUID name derived from `guid(scope, principal, role)`, correct
      `scope:`, `principalType` set, and a data-plane role rather than a management-plane one.
- [ ] Prefer a pinned AVM module where the module encapsulates something real - diagnostics,
      private endpoints, RBAC - and confirm its `ModuleStatus` is `Available`.
- [ ] Type the parameters: `@description()` everywhere, `@minLength`/`@maxLength` on names,
      `@allowed()` only on genuinely closed sets, user-defined types instead of `object`.
- [ ] **Gate - the build fails on the things that matter:** with the rules you care about set to
      `error` in `bicepconfig.json`, `bicep build main.bicep --stdout` exits 0, and a
      deliberately reintroduced secret in an output makes it exit 1.

### ship-a-deployment-safely

- [ ] Establish the target: subscription, resource group, region, and the template's
      `targetScope` - which decides whether this is `az deployment group|sub|mg|tenant`
      (`references/deployment-and-azd.md`).
- [ ] Run `what-if` at that scope with `--validation-level Provider`. On an RBAC failure fall
      back to `ProviderNoRbac` and record in the review that permissions were not validated.
- [ ] Read the what-if output line by line. Stop on any `-`; treat `*` as a resource that was not
      analysed; open every `~` and check whether the changed property is immutable.
- [ ] For an azd project, use `azd provision --preview` instead, because it resolves the
      environment's parameters the way `azd provision` will.
- [ ] Confirm no secret is on a command line or in a hook, and that the CI identity is federated
      rather than holding a client secret.
- [ ] Deploy, then verify from the resource's own state - not from the deployment's exit code.
- [ ] **Gate - the change is what you claimed:** a second `what-if` immediately after the deploy
      returns no changes, and `az deployment operation group list` shows no failed operations.

### grant-an-identity-access-to-a-resource

- [ ] Name the identity precisely: system-assigned on which resource, or which user-assigned
      identity. Prefer user-assigned when the role assignments should outlive a redeploy
      (`references/entra-and-rbac.md`).
- [ ] Decide whether the operation is management plane or data plane, and pick the role
      accordingly. If the design still needs `listKeys`, it is not finished.
- [ ] Look up the role definition GUID rather than using the display name, and scope the
      assignment to the narrowest resource that works - the container, not the storage account.
- [ ] Write the assignment in IaC with a `guid()`-derived name, and check the deploying identity
      can create role assignments at all: Contributor cannot, and
      `Role Based Access Control Administrator` is the least-privilege role that can.
- [ ] For Key Vault, confirm the vault is in RBAC mode; otherwise the assignment is accepted and
      does nothing.
- [ ] Set `AZURE_CLIENT_ID` when more than one identity is attached, so `DefaultAzureCredential`
      picks the right one, and grant the developer's own identity the same role or local runs
      fail with a 403 that looks like an application bug.
- [ ] **Gate - the access works from the workload, not from your laptop:** the application's own
      identity performs the operation successfully after the propagation window, and no
      connection string or account key remains in its configuration.

### choose-a-hosting-service

- [ ] Collect the four constraints before naming any service: traffic shape, network position,
      operational appetite, and what the code already is
      (`references/hosting-selection.md`).
- [ ] Eliminate on networking first - reaching a private endpoint rules out Consumption
      Functions; inbound-private-only rules out several defaults.
- [ ] Choose AKS only for a stated reason: the Kubernetes API itself, an existing Helm estate,
      node-level control, or scale that justifies cluster overhead. "We might need it later" is
      not one (`references/aks-control-plane.md`).
- [ ] Check the SKU exists in the target region and has availability zones, and check the quota
      there before committing (`references/cost-and-quotas.md`).
- [ ] Decide zone redundancy now - it is create-time for Container Apps environments, AKS node
      pools and App Service plan tiers.
- [ ] Plan the identity and its role assignments as part of the move, not after it; that is the
      part of a migration that is routinely missed.
- [ ] **Gate - the choice survives its own constraints:** each of the four constraints maps to a
      capability of the chosen service, and the composite SLA of the resulting chain is computed
      rather than assumed (`references/well-architected.md`).

### diagnose-a-production-azure-resource

- [ ] Check Resource Health for the resource and Service Health for the region before anything
      else, and note whether the cause is classified platform-initiated or customer-initiated
      (`references/diagnostics.md`).
- [ ] Read the Activity Log for the last 24 hours at resource group scope. Resolve any managed
      identity caller from its object ID before concluding that nothing changed.
- [ ] Run the service's own detectors (Diagnose and solve problems) - they are portal-only, so
      say so rather than inventing a CLI equivalent.
- [ ] Only now read logs and metrics, and only against a hypothesis. If there are no resource
      logs, the finding is the missing diagnostic setting.
- [ ] For a failed deployment, get the nested error:
      `az deployment operation group list -g <rg> -n <name>`.
- [ ] Report setting names, never setting values, and get explicit approval before restarting,
      rewriting app settings or redeploying.
- [ ] **Gate - the cause is evidenced:** each conclusion names a command output, an Activity Log
      entry or a health status, and anything still inferred is labelled as inferred.

### review-a-workload-against-well-architected

- [ ] Fix the scope to a subscription and a workload, and collect inventory evidence first -
      Resource Graph, the IaC, Advisor and Defender recommendations
      (`references/well-architected.md`).
- [ ] Work the five pillars as questions, writing each finding with the evidence line that
      produced it and the consequence of leaving it.
- [ ] Compute the composite SLA of the synchronous chain rather than quoting the best component's
      number.
- [ ] Check zone redundancy at every tier, and flag the ones that would require recreating a
      resource to change.
- [ ] Find waste by query, not by opinion - unattached disks, unassociated public IPs, stopped
      but not deallocated VMs, empty plans (`references/cost-and-quotas.md`).
- [ ] Rank by consequence across pillars, and include a "Not findings" section for the things
      that look wrong and are fine.
- [ ] **Gate - every finding is actionable and every gap is declared:** each finding names a
      resource, the evidence and the smallest fix, and anything not checked is listed under gaps
      rather than left implied.

## Topic router

| Topic | Read when | File |
|---|---|---|
| What the compiler checks versus what ARM checks, linter rule severities and `bicepconfig.json`, symbolic references, secrets, parameters and `.bicepparam`, scopes and modules, AVM discovery and pinning, migrating hand-written resources to AVM | Writing or reviewing `.bicep` / `.bicepparam`, or deciding whether to adopt a module | `references/bicep-and-avm.md` |
| The release gate, `what-if` per scope and validation levels, change symbols, Complete mode versus deployment stacks, deployment history limits, `azure.yaml` shape, azd environments, hooks, CI authentication, reading a failed deployment | Deploying, reviewing a deployment, or debugging one that failed | `references/deployment-and-azd.md` |
| CAF naming pattern and per-resource name rules, resources that forbid hyphens, generating names in IaC, the management group / subscription / resource group hierarchy, hard limits, tags, locks, resource moves, Azure Policy, joining an existing landing zone | Naming anything, structuring subscriptions, or working inside an enterprise landing zone | `references/naming-and-structure.md` |
| Entra roles versus Azure RBAC, control plane versus data plane, built-in role GUIDs, scope and the 4000 ceiling, role assignments in Bicep, managed identity types, workload identity federation constraints, app registrations, custom roles, ABAC, PIM, diagnosing `AuthorizationFailed` | Granting access, reviewing an access export, or debugging a permission failure | `references/entra-and-rbac.md` |
| The four constraints that decide hosting, App Service versus Container Apps versus Functions versus AKS versus Container Instances, plan tiers, revisions and slots, networking per service, zone redundancy, what a migration actually costs | Choosing where a workload runs, or planning a move between services | `references/hosting-selection.md` |
| Functions hosting plans, Flex Consumption specifics and its regional core quota, runtime and extension bundle versions, identity-based connections, `host.json` settings and the Service Bus schema shift, cold starts, deployment, migrating off Consumption | Working on a Function App | `references/functions.md` |
| AKS Day-0 versus Day-1 decisions, tiers and SLAs, pod IP models and reserved CIDRs, API server access, the three cluster identities, node pools, version support and upgrades, registry access, a production `az aks create`, cost levers | Creating, reviewing or upgrading an AKS cluster | `references/aks-control-plane.md` |
| Diagnosis ordering, Resource Health, Activity Log, diagnostic settings, Application Insights and Log Analytics as resources, Resource Graph, Service Health, per-service first commands, opening a support ticket | Something in production is failing or behaving unexpectedly | `references/diagnostics.md` |
| Quotas as capacity, finding the right quota name, increase requests, comparing regions, the Retail Prices API, where the money goes, waste shapes and their queries, reservations and savings plans, attributing cost | Planning capacity, estimating cost, or reducing spend | `references/cost-and-quotas.md` |
| The five pillars as questions, reliability and zone redundancy, composite SLA arithmetic, security findings, cost, operational excellence, performance efficiency, running and reporting a review | Doing a readiness or architecture review | `references/well-architected.md` |

## Output format

Group findings by file or resource, lead with the location and the consequence, and name the
evidence rather than asserting the conclusion:

```
infra/main.bicep:21 - deploy-blocking - storageName renders as
  st-orders-api-dev-<13 char hash>: hyphens and ~30 characters against a 3-24 lowercase
  alphanumeric limit. bicep build exits 0 because name rules are enforced by ARM, so this
  fails mid-deployment. Use take('st${token}${uniqueString(resourceGroup().id)}', 24).
```

Order by consequence, not by category: anything that blocks a deployment, deletes a resource or
exposes a credential first, then correctness, then cost, then style. State which bucket each
finding is in when it matters - "cannot be changed after creation" and "one CLI flag" deserve
different urgency.

Say plainly when something is fine. Two acceptable spellings of the same thing are not findings,
and reporting them buries the ones that are. Separate what you verified from what you inferred,
and list what you could not check rather than leaving it implied.

## Environment

- `az` is the control-plane CLI; `az bicep install` bundles the Bicep compiler, and the
  standalone `bicep` binary works identically for `build` and `lint`. `az account show` is the
  first command of any session - the active subscription is a per-machine setting and is not
  what a script should rely on.
- `az extension add --name quota` is required before any `az quota` command; without it those
  commands do not exist.
- `azd` is separate from `az` and authenticates separately (`azd auth login`). A project with an
  `azure.yaml` is an azd project and should be driven through `azd`, not around it.
- `bicep build` and `bicep lint` are offline and need no credentials, so a Bicep question can be
  settled in seconds rather than argued about. Restoring a `br/public:` AVM module does need
  network access on first use.
- Nothing in this skill requires a subscription to *read*: the Retail Prices API is
  unauthenticated, the AVM module index is a CSV in a public repository, and the linter runs
  locally.

<!-- sources: microsoft-azure-skills, awesome-copilot, aks-skills, azure-functions-skills, bicep, avm, azure-docs, sre-agent-skills -->
