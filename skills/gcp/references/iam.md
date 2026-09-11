# IAM: roles, deny policies, service accounts, federation

Verified against: Google Cloud SDK 584.0.0; semantics cross-read against cloud.google.com/iam.

## Contents

- [Evaluation order](#evaluation-order)
- [The three kinds of role](#the-three-kinds-of-role)
- [Custom roles](#custom-roles)
- [Principal identifiers](#principal-identifiers)
- [Conditions](#conditions)
- [Deny policies](#deny-policies)
- [Editing a policy without losing someone else's change](#editing-a-policy-without-losing-someone-elses-change)
- [Propagation](#propagation)
- [Service accounts](#service-accounts)
- [Workload Identity Federation](#workload-identity-federation)
- [Right-sizing an existing policy](#right-sizing-an-existing-policy)
- [Diagnosing "permission denied"](#diagnosing-permission-denied)

## Evaluation order

For every API call, IAM resolves in this order:

1. Collect deny policies on the resource and all its ancestors. **If any matching deny applies
   to this principal and permission, the call fails — allow policies are never consulted.**
2. Collect allow policies on the resource and all its ancestors, take the union.
3. Evaluate conditions on any matching bindings.

The practical consequence: a deny policy is the only way to guarantee that a permission stays
unavailable regardless of what someone grants later, anywhere in the hierarchy. Removing a
binding is not a guarantee; it is a state that any project owner can undo.

## The three kinds of role

| Kind | Example | Use |
|---|---|---|
| Basic (legacy) | `roles/owner`, `roles/editor`, `roles/viewer` | Do not use in production. `roles/editor` covers thousands of permissions across every enabled API, including creating service accounts and granting them roles — a de facto path to owner |
| Predefined | `roles/run.invoker`, `roles/cloudsql.client`, `roles/storage.objectViewer` | The default choice. Google maintains them as APIs change |
| Custom | `projects/p/roles/deployPipeline` | When no predefined role is narrow enough and the gap matters |

Permissions are named `service.resource.verb` (`compute.instances.create`). A role is a
bundle of them; there is no "deny" inside a role.

Grant on the **narrowest resource that supports it**. Many services accept IAM policies on the
individual resource — `gcloud run services add-iam-policy-binding`,
`gcloud storage buckets add-iam-policy-binding`, `gcloud secrets add-iam-policy-binding`.
A project-level `roles/secretmanager.secretAccessor` reads every secret in the project; the
same role on one secret reads one secret.

## Custom roles

- Can be created at **project or organization level only**. There is no folder-level custom
  role; if a role must be usable across a folder, define it at the organization.
- Carry a launch stage (`ALPHA`, `BETA`, `GA`, `DEPRECATED`, `DISABLED`). The stage is
  metadata for you, not an enforcement mechanism, but `DISABLED` does stop the role granting
  anything.
- Do not auto-update. When a service adds a permission that a predefined role picks up
  automatically, your custom role does not, and the failure surfaces later as a confusing
  partial outage.
- Editing custom roles is itself an escalation path: anyone who can edit a custom role can add
  any permission to it. Treat `roles/iam.roleAdmin` as a privileged grant.

Build one from observed usage rather than guessing:

```bash
gcloud iam roles create deployPipeline --project=PROJECT_ID \
  --title="Deploy pipeline" --stage=GA \
  --permissions=run.services.get,run.services.update,run.revisions.list \
  --quiet
```

## Principal identifiers

| Prefix | Meaning |
|---|---|
| `user:alice@example.com` | a Google identity |
| `group:eng@example.com` | a Google group — membership changes take effect without touching IAM |
| `serviceAccount:sa@p.iam.gserviceaccount.com` | a service account |
| `domain:example.com` | every identity in a Cloud Identity domain |
| `principal://iam.googleapis.com/projects/N/locations/global/workloadIdentityPools/POOL/subject/SUBJECT` | one federated identity |
| `principalSet://.../attribute.ATTR/VALUE` | every federated identity matching an attribute |
| `allAuthenticatedUsers` | any Google account **or service account anywhere in the world**, not "anyone in my org" |
| `allUsers` | unauthenticated public |

`allAuthenticatedUsers` is the one people misread. It does not mean "authenticated to my
organization"; it means any of the billions of Google accounts, and it excludes nothing. On a
bucket or a Cloud Run service it is effectively public with a login wall.

## Conditions

A condition attaches a CEL expression to a binding: the role applies only when it evaluates
true.

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='user:contractor@partner.example' \
  --role='roles/storage.objectViewer' \
  --condition='title=expires_2026_12_31,expression=request.time < timestamp("2027-01-01T00:00:00Z")' \
  --quiet
```

Limits that are not obvious:

- **Conditions cannot be attached to basic roles** (`roles/owner`, `roles/editor`,
  `roles/viewer`) or to `allUsers`/`allAuthenticatedUsers`. Attempting it fails at
  `setIamPolicy`.
- Only some attributes are available for some services. `resource.name` and `resource.type`
  work where the service supports conditional bindings; `request.time` works everywhere.
- A condition narrows one binding. It cannot narrow an inherited binding from a parent.

The common good use is a time-bounded grant for contractors and incident access, so the
cleanup is automatic instead of a ticket nobody closes.

## Deny policies

IAM v2. Attached to an organization, folder or project — not to an individual resource — and
expressed as a policy file rather than flags:

```yaml
# deny-setiampolicy.yaml
displayName: "Contractors cannot change IAM"
rules:
  - denyRule:
      deniedPrincipals:
        - principalSet://goog/public:all
      exceptionPrincipals:
        - principalSet://goog/group/platform-admins@example.com
      deniedPermissions:
        - cloudresourcemanager.googleapis.com/projects.setIamPolicy
        - iam.googleapis.com/roles.update
```

```bash
gcloud iam policies create deny-setiampolicy \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/PROJECT_ID \
  --kind=denypolicies --policy-file=deny-setiampolicy.yaml --quiet

gcloud iam policies list \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/PROJECT_ID \
  --kind=denypolicies
```

Notes:

- Permissions in a deny rule use the **full service-qualified form**
  (`cloudresourcemanager.googleapis.com/projects.setIamPolicy`), not the short IAM form
  (`resourcemanager.projects.setIamPolicy`). Not every permission is deniable; the deny
  permission reference lists which are.
- `exceptionPrincipals` is how you carve out the break-glass group. Without one, a deny on
  `projects.setIamPolicy` can lock the organization out of its own IAM.
- Deny policies apply to the resource *and its descendants*, so an org-level deny reaches
  every project.

## Editing a policy without losing someone else's change

`get-iam-policy` → edit → `set-iam-policy` is a read-modify-write with an `etag`. If someone
else changed the policy in between, `set-iam-policy` fails on the etag rather than silently
overwriting — which is the desired behaviour, so do not strip the etag to force it through.

`add-iam-policy-binding` / `remove-iam-policy-binding` do the read-modify-write for you and
retry on etag conflict. Prefer them for single-binding changes. Reserve `set-iam-policy` for
bulk rewrites where you have reviewed the whole document.

## Propagation

IAM changes are **typically effective in about 2 minutes but can take 7 minutes or longer**.
Changes made by adding or removing someone from a Google group take longer still, because
group membership propagates separately.

This matters twice: a verification run immediately after a grant can report a false failure,
and — worse — a revocation is not instantaneous, so removing access during an incident is not
containment. For containment, also revoke the session: disable or delete the service account,
rotate the key, or `gcloud auth revoke`.

## Service accounts

A service account is both an identity (it has roles) and a resource (others have roles *on*
it). The two role families are distinct and both are needed:

| Role | Grants |
|---|---|
| `roles/iam.serviceAccountUser` on the SA | attach this SA to a resource ("act as") — required to deploy a Cloud Run service or a VM that runs as it |
| `roles/iam.serviceAccountTokenCreator` on the SA | mint tokens for it, i.e. impersonate it |
| `roles/iam.serviceAccountAdmin` on the project | create and delete service accounts |

**Do not create downloaded JSON keys.** They never expire, they end up in repositories and CI
variables, and nothing in Google Cloud tells you a copy leaked. The alternatives, in order of
preference:

1. **Attached identity** — the workload runs on Google Cloud; give the Cloud Run service, GKE
   pod or VM its own service account and use ADC. No credential exists to leak.
2. **Workload Identity Federation** — the workload runs elsewhere (GitHub Actions, AWS,
   on-prem) and exchanges its existing OIDC/SAML token for a short-lived Google token.
3. **Impersonation** — a human or another service account borrows this one for a single
   operation via `--impersonate-service-account`.

Block the path rather than auditing it: enforce the
`iam.disableServiceAccountKeyCreation` organization policy constraint. Deleting a service
account does **not** invalidate tokens
already issued for it; they remain valid until expiry, and re-creating an account with the
same email produces a different unique ID, which silently breaks bindings that referenced the
old one (`deleted:serviceAccount:...?uid=...` entries in the policy are the visible symptom).

## Workload Identity Federation

The chain is: external IdP → **workload identity pool** → **pool provider** (OIDC or SAML, with
an attribute mapping and an attribute condition) → either direct resource access via a
`principalSet://` binding, or impersonation of a service account.

```bash
gcloud iam workload-identity-pools create-cred-config \
  "//iam.googleapis.com/projects/N/locations/global/workloadIdentityPools/POOL/providers/PROVIDER" \
  --service-account=deployer@PROJECT_ID.iam.gserviceaccount.com \
  --output-file=adc.json --credential-source-file=/path/to/oidc/token
```

Two rules that decide whether the setup is secure:

- **Always set an attribute condition on the provider.** Without one, any token the IdP issues
  — including one for a repository you do not own, on a public CI platform — satisfies the
  provider. The condition is the tenancy boundary.
- **Map numeric IDs, not names.** For GitHub, condition on `repository_id` and
  `repository_owner_id`, not `repository` and `repository_owner`. A deleted repository or
  organization name can be re-registered by someone else, who then inherits your federation
  trust.

Direct resource access (`principalSet://` in the resource's own IAM policy) avoids the service
account entirely and is preferable when the service supports it; impersonation is the fallback
for services that do not yet accept federated principals.

## Right-sizing an existing policy

The IAM recommender analyses 90 days of actual usage and proposes narrower roles:

```bash
gcloud recommender recommendations list --project=PROJECT_ID \
  --location=global --recommender=google.iam.policy.Recommender \
  --format="table(content.overview.member, content.overview.removedRole)" --limit=50
```

Treat its output as a candidate list, not a patch: a role used once a quarter (disaster
recovery, annual key rotation) looks unused in a 90-day window.

## Diagnosing "permission denied"

Order matters — checking the allow policy first is the slow path.

1. Which identity is actually calling? `gcloud auth list`, or for a workload, the service
   account attached to it — not the one you intended to attach.
2. Is a deny policy matching?
   `gcloud iam policies list --attachment-point=... --kind=denypolicies` at project, folder and
   organization.
3. Is an org policy blocking the *configuration* rather than the caller? These surface as
   constraint violation errors naming the constraint, not as 403 on a permission.
4. Is it IAM at all? VPC Service Controls denials, a disabled API (`SERVICE_DISABLED`) and
   billing being detached all present as access failures with different error bodies. Read the
   error's `reason` field.
5. Only then: Policy Troubleshooter (`gcloud policy-troubleshoot iam`), which evaluates the
   full chain for one principal, one resource and one permission and tells you which binding
   granted or failed to grant it.

<!-- sources: gcp-docs, google-skills -->
