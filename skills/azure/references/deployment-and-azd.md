# Deployment, what-if and the Azure Developer CLI

Verified against: `az` 2.76+ command surface and `azd` as documented in `Azure/azure-dev`. Commands
in this file were not executed locally (no Azure CLI on the authoring machine); every claim is
`[official]` unless marked otherwise.

## Contents

- [The release gate](#the-release-gate)
- [what-if and validation levels](#what-if-and-validation-levels)
- [Deployment modes and deployment stacks](#deployment-modes-and-deployment-stacks)
- [Deployment history](#deployment-history)
- [azd project shape](#azd-project-shape)
- [azd environments and secrets](#azd-environments-and-secrets)
- [azd hooks](#azd-hooks)
- [CI authentication](#ci-authentication)
- [Reading a failed deployment](#reading-a-failed-deployment)

## The release gate

Four steps, in order, each of which can fail independently:

1. `bicep build main.bicep --stdout > /dev/null` - syntax, types, linter. Exit code only reflects
   `error`-level diagnostics, which is a `bicepconfig.json` decision rather than a default.
2. `az deployment group validate` - ARM parses the template, resolves parameters and checks basic
   provider schema. It does not check RBAC or quota.
3. `az deployment group what-if` - ARM runs the change calculation against the real current state.
   This is the step that shows deletions.
4. Deploy.

Skipping step 3 is how a template that "only adds a tag" removes a subnet. Run it, read it, and
attach the output to the change.

## what-if and validation levels

Match the command to the template's `targetScope`:

| `targetScope` | Command |
|---|---|
| `resourceGroup` | `az deployment group what-if -g <rg> -f main.bicep -p main.bicepparam` |
| `subscription` | `az deployment sub what-if -l <region> -f main.bicep -p main.bicepparam` |
| `managementGroup` | `az deployment mg what-if -l <region> -m <mg-id> -f main.bicep` |
| `tenant` | `az deployment tenant what-if -l <region> -f main.bicep` |

Change symbols in the output:

| Symbol | Meaning | How to read it |
|---|---|---|
| `+` | Create | Expected for new resources |
| `-` | Delete | Only legitimate in Complete mode or a stack with delete semantics. Otherwise stop |
| `~` | Modify | Read the property list; a change to an immutable property is a replacement |
| `=` | NoChange | |
| `*` | Ignore | The resource was **not analysed**. Absence of a diff here is not evidence |
| **!** | Deploy | ARM will send the resource but cannot predict the result - typically a nested deployment or a provider without what-if support |

`--validation-level` controls how much ARM checks before reporting:

- `Provider` (default) - full provider preflight including RBAC. Most accurate, needs the most
  permissions.
- `ProviderNoRbac` - skips the RBAC check. Use when the pull-request identity is deliberately
  read-only; note in the review that permissions were not validated.
- `Template` - template validation only. Fast, and blind to everything interesting.

Two persistent sources of what-if noise are worth recognising rather than chasing: properties the
provider normalises after write (casing, default sub-objects) and resources whose provider does not
implement what-if and so come back as a bare Deploy marker. Suppress the first class with
`az deployment group what-if --no-pretty-print` plus a diff filter in CI if it is drowning the
signal; never suppress `-` lines.

## Deployment modes and deployment stacks

`az deployment group create --mode Complete` **deletes every resource in the resource group that is
not in the template**. It is the only way to make a template authoritative over a resource group,
and it is also the fastest way to delete production. If you use it, the resource group must contain
nothing that is not managed by that template, and the what-if must be read before every apply.
Incremental (the default) never deletes.

Deployment stacks are the managed alternative. A stack is a resource that owns a set of resources
and tracks membership across deployments:

```bash
az stack group create \
  --name orders \
  --resource-group rg-orders-prod \
  --template-file main.bicep \
  --parameters main.bicepparam \
  --action-on-unmanage deleteResources \
  --deny-settings-mode denyWriteAndDelete
```

- `--action-on-unmanage` decides what happens to a resource that leaves the template:
  `detachAll` (leave it), `deleteResources`, or `deleteAll` (resources and resource groups).
- `--deny-settings-mode` writes a deny assignment onto the managed resources, so a portal user
  cannot edit or delete them out from under the template. `denyDelete` and `denyWriteAndDelete`
  are the useful values; `--deny-settings-excluded-principals` exempts a break-glass identity.

Stacks give you Complete-mode authority with an explicit, reviewable unmanage policy instead of an
implicit delete. Both are required parameters for a reason: there is no safe default.

## Deployment history

Every deployment is recorded at its scope, and the record contains the resolved parameter values
and the outputs in plaintext. Two consequences:

- Anyone with read access on the resource group can read a secret that was passed as a parameter
  or returned as an output, even if it was marked `@secure()` in the template.
- The history holds **800 deployments per resource group** and per subscription. ARM deletes the
  oldest automatically as you approach the limit, so a CI job that deploys on every commit
  silently erases its own audit trail. If you need retention, export it; do not rely on the history.

`az deployment group list -g <rg> --query "[?properties.provisioningState=='Failed']"` is the first
command when someone says "the deployment broke last night".

## azd project shape

`azure.yaml` at the repository root is the manifest. Read it before assuming anything - the infra
path, the IaC provider and the service list are all configurable.

```yaml
name: orders-platform
infra:
  provider: bicep      # or terraform
  path: infra
  module: main
services:
  api:
    project: ./src/api
    language: csharp
    host: appservice   # containerapp | function | staticwebapp | aks | springapp
```

Defaults worth keeping:

| Concern | Default |
|---|---|
| Application code | `src/<service-name>`, one entry per independently deployable unit |
| Infrastructure | `infra/` with a thin `main.bicep` entry point and modules beneath |
| Local state | `.azure/<environment-name>`, git-ignored |
| Shared state | azd remote environments backed by Azure Blob Storage |
| Scripts | short, idempotent, under `scripts/` and invoked from hooks |

Service keys participate in resource discovery: azd matches a service to its deployed resource by
the `azd-service-name` tag on the resource. Renaming a service key without renaming the tag makes
`azd deploy` fail to find its target.

`azd provision --preview` is the azd-shaped what-if. Use it in place of `az deployment ... what-if`
when a project has an `azure.yaml`, because it resolves the environment's parameters the same way
`azd provision` will.

## azd environments and secrets

- `azd env new <name>`, `azd env select`, `azd env list`. Pass `-e <name>` explicitly in any script
  or pipeline; the "current" environment is a local file and is not what you want in CI.
- `azd env set KEY value` for configuration, `azd env set-secret KEY` for anything sensitive (it
  stores a Key Vault reference, not the value).
- `azd env refresh` re-reads deployment outputs after someone else provisioned. Without it,
  `azd deploy` can wire an application to a resource that no longer exists.
- Never edit `.azure/<env>/.env` by hand and never commit `.azure/`.
- `azd down` destroys the environment's resources. `--purge` additionally purges soft-deleted Key
  Vaults and Cognitive Services accounts - without it, re-provisioning into the same names fails
  with a conflict against the soft-deleted resource.

## azd hooks

Hooks exist for lifecycle gaps that IaC cannot express - seeding a database, running a migration.
They are not a place to configure infrastructure; a `postprovision` hook that sets app settings is
a role assignment and a Key Vault reference that should have been in the Bicep.

```yaml
hooks:
  postprovision:
    posix:
      shell: sh
      run: ./scripts/seed.sh
      continueOnError: false
    windows:
      shell: pwsh
      run: ./scripts/seed.ps1
```

Set `shell` explicitly, provide both variants if the team is mixed, make the script idempotent, and
test it in isolation with `azd hooks run postprovision`. A hook that echoes a secret into
`az ... --settings` puts that secret in the command line, where it lands in shell history and CI
logs.

## CI authentication

Use workload identity federation (OIDC). `azd pipeline config --auth-type federated` creates the
app registration, the federated credential and the pipeline definition; review what it generated
rather than trusting it, especially the scope of the role assignment it makes.

The failure mode to know: a federated identity credential whose `subject` does not exactly match
the token the pipeline presents is created **without error** and fails only at token exchange, with
no diagnostic on the Azure side. For GitHub Actions the subject is
`repo:<org>/<repo>:environment:<env>` or `repo:<org>/<repo>:ref:refs/heads/<branch>` - the two are
different credentials.

Pipeline mechanics themselves - workflow syntax, runners, environment approvals - belong to the
`github` skill. This skill covers what the pipeline must run and with which identity.

## Reading a failed deployment

The message in the CLI is usually the outermost wrapper. The useful error is nested:

```bash
az deployment group show -g <rg> -n <deployment-name> \
  --query "properties.error" -o json
```

```bash
# Per-resource operations, including the provider's own message
az deployment operation group list -g <rg> -n <deployment-name> \
  --query "[?properties.provisioningState=='Failed'].properties.statusMessage"
```

Frequent codes and what they actually mean:

| Code | Meaning |
|---|---|
| `InvalidTemplateDeployment` | The provider rejected the resource; the real reason is in the nested `details` |
| `RequestDisallowedByPolicy` | Azure Policy denied it. The response names the policy assignment |
| `QuotaExceeded` / `OperationNotAllowed` | Regional quota in that subscription and region |
| `AuthorizationFailed` | The deploying principal lacks a permission; the message names the action and the scope |
| `ResourceNotFound` on a resource the template creates | A missing dependency edge - usually a `resourceId()` string where a symbolic reference belonged |
| `Conflict` with `already exists in soft deleted state` | Key Vault or Cognitive Services soft delete; purge or reuse the name |
| `DeploymentActive` | A deployment with the same name is already running at that scope |

<!-- sources: awesome-copilot, microsoft-azure-skills, azure-docs, azure-dev -->
