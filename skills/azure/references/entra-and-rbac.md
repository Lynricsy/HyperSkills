# Microsoft Entra ID and Azure RBAC

Verified against: Azure RBAC and Microsoft Entra Workload ID documentation as published in
`MicrosoftDocs/azure-docs` and the Entra docs. CLI commands were not executed locally; claims are
`[official]` unless marked otherwise.

## Contents

- [Two different permission systems](#two-different-permission-systems)
- [Control plane versus data plane](#control-plane-versus-data-plane)
- [Built-in role IDs worth memorising](#built-in-role-ids-worth-memorising)
- [Scope and the 4000 ceiling](#scope-and-the-4000-ceiling)
- [Role assignments in Bicep](#role-assignments-in-bicep)
- [Managed identity](#managed-identity)
- [Workload identity federation](#workload-identity-federation)
- [App registrations and service principals](#app-registrations-and-service-principals)
- [Custom roles, ABAC and PIM](#custom-roles-abac-and-pim)
- [Diagnosing an authorization failure](#diagnosing-an-authorization-failure)

## Two different permission systems

Azure RBAC governs Azure resources (subscriptions, resource groups, storage accounts) and is scoped
by resource hierarchy. Microsoft Entra roles govern the directory (users, groups, app
registrations, Conditional Access) and are scoped by the tenant or an administrative unit. They are
separate systems with separate role catalogues and separate assignment APIs.

Consequences people trip over:

- Owner on a subscription does not let you create an app registration.
- Global Administrator does not, by default, see any Azure subscription. The "elevate access"
  toggle grants User Access Administrator at the root scope and should be turned off again.
- `az role assignment create` writes Azure RBAC; `az ad` commands write directory objects. A
  question about "permissions" has to be resolved into one of the two before it can be answered.

## Control plane versus data plane

The single most common Azure permission mistake. A management-plane role lets you manage the
resource; it does not let you read the data inside it.

| The app needs to | Wrong (management plane) | Right (data plane) |
|---|---|---|
| Read/write blobs | Storage Account Contributor | Storage Blob Data Contributor |
| Read secrets from Key Vault (RBAC mode) | Key Vault Contributor | Key Vault Secrets User |
| Send to a Service Bus queue | Contributor on the namespace | Azure Service Bus Data Sender |
| Read Cosmos DB documents | DocumentDB Account Contributor | A Cosmos DB data-plane role assignment (separate API) |
| Pull an image from ACR | Contributor | AcrPull |

The management-plane roles usually *appear* to work, because they let the caller list the account
keys and authenticate with those instead. That is the failure: the deployment "works", and the
application is now using a shared key that nobody rotates. If an application still needs
`listKeys`, the identity design is not finished.

Key Vault has two authorization models. A vault with `enableRbacAuthorization: true` ignores access
policies entirely; a vault without it ignores role assignments. Granting `Key Vault Secrets User`
on a vault still in access-policy mode produces an assignment that does nothing and no error.

## Built-in role IDs worth memorising

Role definition IDs are stable GUIDs, identical in every tenant. Use them in IaC rather than role
names, which are localised and occasionally renamed.

| Role | ID |
|---|---|
| Owner | `8e3af657-a8ff-443c-a75c-2fe8c4bcb635` |
| Contributor | `b24988ac-6180-42a0-ab88-20f7382dd24c` |
| Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` |
| User Access Administrator | `18d7d88d-d35e-4fb5-a5c3-7773c20a72d9` |
| Role Based Access Control Administrator | `f58310d9-a9f6-439a-9e8d-f62e7b41a168` |
| Storage Blob Data Contributor | `ba92f5b4-2d11-453d-a403-e96b0029c9fe` |
| Storage Blob Data Reader | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` |
| Storage Queue Data Contributor | `974c5e8b-45b9-4653-ba55-5f855dd0fb88` |
| Key Vault Secrets User | `4633458b-17de-408a-b874-0445c86b69e6` |
| Key Vault Crypto User | `12338af0-0e69-4776-bea7-57ae8d297424` |
| AcrPull | `7f951dda-4ed3-4680-a7ca-43fe172d538d` |
| AcrPush | `8311e382-0749-4cb8-b61a-304f252e45ec` |
| Azure Service Bus Data Sender | `69a216fc-b8fb-44d8-bc22-1f3c2cd27a39` |
| Azure Service Bus Data Receiver | `4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0` |
| Azure Kubernetes Service RBAC Cluster Admin | `b1ff04bb-8a4e-4dc4-8eb5-8693973ce19b` |
| Monitoring Metrics Publisher | `3913510d-42f4-4e42-8a64-420c390055eb` |

When you need one that is not here, `az role definition list --name "<role>" --query "[].name"`
returns the GUID; do not guess it.

## Scope and the 4000 ceiling

Assignments inherit downward: management group → subscription → resource group → resource. An
assignment at a lower scope can only add, never subtract - there is no deny by omission. (Deny
assignments exist but are created only by Azure Blueprints and deployment stacks, not by users.)

**A subscription supports 4000 role assignments. The limit is fixed and cannot be raised by a
support request.** Assignments at subscription, resource group and resource scope all count;
management-group-scope assignments and PIM-eligible (not-yet-activated) assignments do not. When a
subscription approaches it, the three ways out, in order of leverage:

1. Assign to Entra groups instead of individual principals. Twenty engineers become one assignment.
2. Move the assignment up to a management group, where it stops counting against the subscription.
3. Delete redundant assignments - a Contributor at resource group scope underneath an Owner at
   subscription scope grants nothing extra and costs a slot.

Other limits: 5000 custom roles per tenant (2000 in some sovereign clouds), 500 role assignments
per management group, 20 management locks per scope.

Assignment changes propagate in roughly a minute but can take up to ten. A pipeline that creates a
role assignment and immediately uses it needs a retry, not a `sleep`.

## Role assignments in Bicep

```bicep
resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' existing = {
  name: storageName
}

var blobDataContributor = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource assignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, principalId, blobDataContributor)
  properties: {
    roleDefinitionId: blobDataContributor
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
```

Four rules, each of which breaks a deployment when ignored:

- **The name must be a GUID.** ARM rejects anything else, and `bicep build` does not catch it.
- **Derive the GUID from `(scope, principal, role)` with `guid()`.** That makes redeployment
  idempotent. `newGuid()` produces a new assignment on every deployment and is only legal in a
  parameter default anyway.
- **`scope:` sets the assignment scope**, and the resource is an extension resource - it attaches
  to whatever you point it at. Omitting `scope:` in a resource-group-scoped template silently
  grants at the whole resource group.
- **Set `principalType`.** Without it, ARM sometimes fails with
  `PrincipalNotFound` on a freshly created managed identity because directory replication has not
  caught up; naming the type skips the lookup.

Creating role assignments requires `Microsoft.Authorization/roleAssignments/write`, which
Contributor does not have. The deploying identity needs Owner, User Access Administrator, or
preferably **Role Based Access Control Administrator** - which grants exactly role assignment
management and nothing else, and supports a condition restricting which roles it may assign.

## Managed identity

| | System-assigned | User-assigned |
|---|---|---|
| Lifecycle | Tied to the resource; deleted with it | Independent resource |
| Shared | No, exactly one resource | Yes, many resources |
| Role assignments survive a redeploy | Only if the resource survives | Yes |
| Available before the resource exists | No - chicken and egg in IaC | Yes |

Use a **user-assigned** identity whenever the identity's role assignments are part of the platform
rather than part of the application: it can be created first, granted roles, and then attached, so
`what-if` on the application deployment shows no RBAC churn. Use system-assigned for a single
resource with a short blast radius and no cross-template references.

An application authenticates with `DefaultAzureCredential` (or the language equivalent). With more
than one user-assigned identity attached, or a mix of system and user-assigned, the credential
cannot guess which to use: set `AZURE_CLIENT_ID` to the identity's client ID. The symptom of
forgetting is an `ManagedIdentityCredential authentication failed` or a 403 from a resource the
"right" identity can reach.

Managed identities cannot be used from outside Azure. Local development uses the developer's own
Entra identity via `az login` / `azd auth login`, which `DefaultAzureCredential` picks up - so the
role assignments the application needs must also exist for the developer, or local runs fail with
a 403 that looks like an application bug.

## Workload identity federation

Federation replaces a client secret with a trust relationship: an external OIDC issuer (GitHub
Actions, an AKS cluster, another cloud) presents a token, Entra validates issuer and subject, and
returns an Azure access token. Nothing to rotate, nothing to leak.

Constraints that cause silent failures:

- **Maximum 20 federated identity credentials per application or user-assigned managed identity.**
- `issuer` + `subject` must be unique on the identity, and **wildcards are not supported in any
  property**. A repository with branch-based and environment-based workflows needs one credential
  per subject.
- **A wrong `subject` is created successfully and fails only at token exchange, with no error on
  the Azure side.** Match it character for character against what the issuer actually sends -
  `repo:<org>/<repo>:ref:refs/heads/main` is not `repo:<org>/<repo>:environment:main`.
- `audiences` takes exactly one value; use `api://AzureADTokenExchange`.
- Propagation takes time. A token request minutes after creating the credential can fail with
  `AADSTS70021: No matching federated identity record found for presented assertion`. Retry rather
  than recreating the credential.
- Creating several credentials **concurrently under the same user-assigned identity returns
  409 Conflict**. Create them serially - in ARM/Bicep, chain them with `dependsOn` or set the copy
  loop to `mode: serial`.
- Only RS256-signed issuers are supported.

## App registrations and service principals

An app registration is the global application object; a service principal is its instance in a
tenant. `az ad app create` makes the first, `az ad sp create --id <appId>` the second, and a role
assignment targets the service principal's object ID - not the application ID. Using the wrong one
produces `PrincipalNotFound`.

- Prefer certificates or federation over client secrets. When a secret is unavoidable, the portal
  caps its lifetime at 24 months, and an expiring secret is an outage with no warning unless you
  monitor it. `az ad app credential list --id <appId> --query "[].endDateTime"` is the audit.
- Delegated permissions act as a signed-in user; application permissions act as the app itself and
  almost always require admin consent. Granting `Directory.Read.All` as an application permission
  to a deployment identity is a tenant-wide read, not a project-scoped one.
- A deleted app registration is soft-deleted for 30 days and still holds its name and identifier
  URIs. `az ad app list --show-deleted` finds it when a re-create fails with a conflict.

## Custom roles, ABAC and PIM

A custom role with `actions: ["*"]` is Owner with a different name; `notActions` removes
permissions but cannot make it least-privilege. Write custom roles from the actions you need
upward, never from `*` downward. `assignableScopes` must list the scopes where the role may be
used - a role assignable at the subscription root is a tenant-wide surface.

ABAC conditions narrow an existing assignment by resource or request attributes, which is how you
grant blob access to one container without a per-container assignment:

```text
(
 (!(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read'}))
 OR
 (@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'invoices')
)
```

Conditions are supported on storage and a growing set of providers; unsupported providers accept no
condition. They also count as one assignment, which helps against the 4000 ceiling.

Privileged Identity Management makes an assignment *eligible* rather than active: the human
activates it for a bounded window, with approval and justification. Any standing human assignment
to Owner or User Access Administrator at subscription scope should be eligible instead. Eligible
assignments do not count toward the 4000 limit.

## Diagnosing an authorization failure

`AuthorizationFailed` names the principal, the action and the scope. Work outward from there:

```bash
# What does this principal actually have, including inherited assignments?
az role assignment list --assignee <objectId> --all --include-inherited -o table

# Does any assigned role contain the action the error named?
az role definition list --name "<role>" --query "[].permissions[].actions" -o json
```

Then check, in this order: is the action a data action (needs a data-plane role), is the vault in
access-policy mode, is the assignment within its propagation window, is a deny assignment from a
deployment stack in play, and is the caller actually the principal you think it is
(`az account show` vs the identity the application uses).

<!-- sources: azure-docs, microsoft-azure-skills, awesome-copilot, microsoftdocs-agent-skills -->
