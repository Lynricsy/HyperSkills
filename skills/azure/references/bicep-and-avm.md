# Bicep and Azure Verified Modules

Verified against: Bicep CLI 0.47.16 (linter behaviour reproduced locally). Azure Verified Modules
Bicep resource index as published in `Azure/Azure-Verified-Modules`.

## Contents

- [What the compiler does and does not check](#what-the-compiler-does-and-does-not-check)
- [Linter severities and the bicepconfig.json gate](#linter-severities-and-the-bicepconfigjson-gate)
- [Symbolic references and the dependency graph](#symbolic-references-and-the-dependency-graph)
- [Secrets](#secrets)
- [Parameters, types and .bicepparam](#parameters-types-and-bicepparam)
- [Scopes and modules](#scopes-and-modules)
- [Azure Verified Modules](#azure-verified-modules)
- [Migrating hand-written resources to AVM](#migrating-hand-written-resources-to-avm)
- [Old patterns](#old-patterns)

## What the compiler does and does not check

`bicep build` is a transpiler with a linter attached. It resolves types from the resource provider
schemas bundled with the CLI, so it catches misspelled properties, wrong types and unknown API
versions. It knows nothing about your subscription.

It does **not** catch, and you must therefore check by other means:

| Failure | Where it actually surfaces |
|---|---|
| Resource name violates the type's name rules (length, charset, global uniqueness) | ARM, at deployment |
| Role assignment `name` is not a GUID | ARM, at deployment |
| Region does not offer the SKU, or quota is exhausted | ARM preflight / deployment |
| RBAC insufficient for the principal running the deployment | ARM preflight |
| A referenced existing resource does not exist | ARM, at deployment |
| Policy assignment denies the resource | ARM, at deployment |

The gap between "compiles" and "deploys" is what `what-if` and preflight validation close.

Name rules are the most common of these. Storage accounts and container registries are 3-24 and
5-50 characters of **lowercase letters and digits only** - no hyphens - while nearly every other
resource type does allow hyphens. A template that builds `'st-${workload}-${uniqueString(...)}'`
compiles cleanly and fails at deployment for two independent reasons. Use
`'st${replace(workload, '-', '')}${uniqueString(resourceGroup().id)}'` and truncate with `take()`.

## Linter severities and the bicepconfig.json gate

Measured on Bicep 0.47.16 with a template containing a secure parameter default, a `listKeys()`
output and a hardcoded `management.azure.com` URL: the linter emits four warnings and
**`bicep build` exits 0**. A pipeline step that runs `bicep build` and checks the exit code
therefore passes a template that leaks a storage key in its outputs.

Escalate the rules you actually care about in `bicepconfig.json` at the repository root:

```json
{
  "analyzers": {
    "core": {
      "enabled": true,
      "rules": {
        "outputs-should-not-contain-secrets": { "level": "error" },
        "secure-parameter-default": { "level": "error" },
        "no-hardcoded-env-urls": { "level": "error" },
        "use-recent-api-versions": { "level": "warning", "maxAgeInDays": 730 }
      }
    }
  }
}
```

With that file present the same template exits 1. Rules worth knowing:

| Rule | Default | Why it matters |
|---|---|---|
| `outputs-should-not-contain-secrets` | warning | Outputs land in the deployment history, readable by anyone with read access on the scope |
| `secure-parameter-default` | warning | A default on a `@secure()` parameter is a credential in source control |
| `no-hardcoded-env-urls` | warning | Breaks in sovereign clouds; use `environment()` |
| `use-resource-symbol-reference` | warning | `resourceId()`/`reference()`/`listKeys(resourceId(...))` hide edges from the dependency graph |
| `use-recent-api-versions` | **off** | Nothing warns about a 2021 API version until you switch this on and set `maxAgeInDays` |
| `no-unused-params`, `no-unused-vars` | warning | Dead parameters in a module's interface mislead callers |
| `prefer-unquoted-property-names`, `simplify-interpolation` | warning | Style only; do not report these as review findings |

`bicep lint <file>` runs the analyzers without emitting ARM JSON. Its exit code follows the highest
diagnostic level: 1 when any rule is at `error`, 0 when everything is a warning. Both commands read
the nearest `bicepconfig.json` walking up from the file, so a per-environment override is a file in
that directory, not a flag.

## Symbolic references and the dependency graph

Bicep infers `dependsOn` from symbolic references. The moment you reach for
`resourceId('Microsoft.Web/serverfarms', planName)` instead of `plan.id`, the edge disappears and
you have to hand-write `dependsOn` to put it back. The explicit `dependsOn` block in a template is
almost always a symptom, not a decision.

```bicep
// Loses the edge, needs dependsOn, breaks if the name expression drifts
serverFarmId: resourceId('Microsoft.Web/serverfarms', planName)

// Keeps the edge, no dependsOn needed
serverFarmId: plan.id
```

The same applies to `listKeys(resourceId(...), '2021-04-01')` versus `storage.listKeys()`, and to
`reference(resourceId(...), apiVersion, 'Full').identity.principalId` versus
`site.identity.principalId`. The symbolic forms also carry the API version from the resource
declaration, so there is one place to bump rather than several string literals to keep in sync.

For a resource this template does not create, declare it `existing`:

```bicep
resource kv 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: vaultName
  scope: resourceGroup(sharedRgName)
}
```

`existing` costs nothing at deploy time - it compiles to a reference, not a resource - and gives you
type checking on the properties you read.

## Secrets

Three separate rules, often conflated:

1. **Nothing sensitive in outputs.** Deployment outputs are persisted in the resource group's
   deployment history. `@secure()` on an output does not remove it from there; it only masks it in
   CLI output. Return the resource ID and let the consumer read the secret with its own identity.
2. **Nothing sensitive in parameter files.** A `.bicepparam` file is source. Use
   `getSecret()` against an existing Key Vault, which is resolved by ARM at deployment and never
   materialises in the template:

   ```bicep
   // main.bicep
   @secure()
   param sqlAdminPassword string
   ```

   ```bicep
   // main.bicepparam
   using './main.bicep'
   param sqlAdminPassword = az.getSecret(subId, rgName, vaultName, 'sql-admin-password')
   ```
3. **Prefer no secret at all.** A managed identity plus a data-plane role assignment removes the
   secret from the system rather than hiding it.

## Parameters, types and .bicepparam

- Every parameter gets `@description()`. A module's parameters are its API; an undescribed
  parameter forces the caller to read the implementation.
- Use `@minLength`/`@maxLength` on name parameters so the ARM-time name-rule failure becomes a
  compile-time failure.
- Use `@allowed()` sparingly. It is a hard gate evaluated before deployment, so an allowed-list of
  SKUs blocks a legitimate deployment the day a new SKU appears. Reserve it for genuinely closed
  sets (`'dev' | 'test' | 'prod'`).
- Use user-defined types for structured parameters instead of `object`:

  ```bicep
  type subnetConfig = {
    name: string
    prefix: string
    delegation: string?
  }
  param subnets subnetConfig[]
  ```

  `object` defers the type error into the resource body, where the message names a provider field
  the caller has never heard of.
- Default values should be safe for a throwaway environment (cheap SKU, no zone redundancy, short
  retention). A default that costs money in a test subscription is a bug.
- `.bicepparam` files (`using './main.bicep'`) are type-checked against the template; JSON parameter
  files are not. Prefer `.bicepparam`, and update it in the same change as the parameter.
  `bicep build-params main.bicepparam` renders the JSON if a tool needs it.

## Scopes and modules

`targetScope` is declared at the top of the file and determines which deployment command applies:

| `targetScope` | Deploy with |
|---|---|
| `resourceGroup` (default) | `az deployment group create` |
| `subscription` | `az deployment sub create --location <region>` |
| `managementGroup` | `az deployment mg create --location <region> --management-group-id <id>` |
| `tenant` | `az deployment tenant create --location <region>` |

The `--location` on the non-resource-group scopes is where the *deployment metadata* lives, not
where the resources go. It cannot be changed later for a given deployment name.

A module can target a different scope than its parent via `scope:`:

```bicep
module rbac 'modules/rbac.bicep' = {
  name: 'rbac'
  scope: resourceGroup(sharedRgName)   // cross-resource-group from a resourceGroup-scoped parent
  params: { principalId: site.identity.principalId }
}
```

Subscription-scoped templates create resource groups and then deploy into them with a module
scoped to `resourceGroup(rgName)`. This is the normal shape for a landing-zone entry point.

Module `name` is the nested deployment name and must be unique within the parent deployment. In a
loop, derive it from the loop key (`name: 'net-${subnet.name}'`); a fixed name inside a loop makes
every iteration overwrite the previous deployment record.

## Azure Verified Modules

AVM is Microsoft's first-party module library. Reference a resource module as
`br/public:avm/res/{service}/{resource}:{version}` and a pattern module as
`br/public:avm/ptn/{pattern}:{version}`:

```bicep
module storage 'br/public:avm/res/storage/storage-account:0.30.0' = {
  name: 'storage'
  params: {
    name: storageName
    location: location
    skuName: 'Standard_ZRS'
    allowBlobPublicAccess: false
    tags: tags
  }
}
```

Rules that matter:

- **Pin an exact version.** There is no range syntax; `:0.30.0` is a literal tag in the public
  registry. An unpinned reference is not possible, which is the point.
- **Check the module's status before adopting it.** The index at
  `docs/static/module-indexes/BicepResourceModules.csv` in `Azure/Azure-Verified-Modules` has a
  `ModuleStatus` column whose values include `Available` and `Orphaned`. An orphaned module still
  resolves and still deploys; it just has no owner to fix it. Adopting one is a decision, not an
  accident to discover later.
- **AVM modules are pre-1.0.** A minor bump can be a breaking change to the parameter surface. Read
  the module's `CHANGELOG.md` before bumping and re-run what-if.
- **Restore needs network access.** `br/public:` modules are pulled from the Microsoft Container
  Registry on first build and cached under `~/.bicep`. An air-gapped build needs the cache
  pre-populated or a private registry (`br/<alias>:`) configured in `bicepconfig.json`.
- **AVM is not always the answer.** For a single resource with three properties, an AVM module adds
  a version to track and dozens of parameters to ignore. Reach for it where the module encapsulates
  something real: diagnostic settings, private endpoints, managed identity wiring, RBAC.

Outputs follow a convention - `resourceId`, `name`, `location`, `systemAssignedMIPrincipalId` -
so `storage.outputs.resourceId` works across modules without reading each one.

## Migrating hand-written resources to AVM

Do it one resource type at a time, and prove each step with what-if rather than by reading the
diff:

- [ ] Find the module and its current version in the AVM index; confirm `ModuleStatus` is
      `Available`.
- [ ] Map every property you set today onto the module's parameters. Anything with no equivalent is
      the decision point: either the module covers it under a different name, or you keep the
      hand-written resource.
- [ ] Replace the `resource` block with the `module` block and update every symbolic reference to
      go through `.outputs`.
- [ ] Run `what-if`. The expected result is `NoChange` on the resource and `Create` on nothing. A
      `Delete`+`Create` pair means the module produces a different resource name - fix the name
      parameter, do not accept the replacement.
- [ ] Deploy to a non-production environment before production, because what-if does not simulate
      property-level API behaviour for every provider.

## Old patterns

<details>
<summary>ARM JSON templates, nested/linked templates, and deployment scripts</summary>

ARM JSON is still the deployment format - Bicep compiles to it - but hand-editing it is no longer
the way to author. `bicep decompile template.json` gives a starting point; expect to rename the
generated symbols and re-type the parameters, because the decompiler cannot recover intent.

Linked templates (`templateLink` to a URI) were the pre-Bicep module system. They require the
template to be reachable over HTTPS at deployment time, which means a storage account with a SAS
token in the deployment. Bicep modules compile into nested templates with no external fetch;
there is no reason to author a linked template today.

`Microsoft.Resources/deploymentScripts` runs an arbitrary CLI or PowerShell script inside a
container as part of a deployment. It creates a storage account and a container instance behind
the scenes, both of which you pay for and must clean up, and it makes the deployment
non-idempotent. Use it only for something ARM genuinely cannot express, and prefer a `postprovision`
hook in azd or a pipeline step.
</details>

<!-- sources: bicep, avm, awesome-copilot, bicep-registry-modules, azure-docs -->
