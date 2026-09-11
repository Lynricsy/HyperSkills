# Resource hierarchy, org policy and projects

Verified against: Google Cloud SDK 584.0.0; product behaviour cross-read against
cloud.google.com documentation.

## Contents

- [The hierarchy and what flows down it](#the-hierarchy-and-what-flows-down-it)
- [Projects](#projects)
- [Organization policy](#organization-policy)
- [Constraints worth enforcing on day one](#constraints-worth-enforcing-on-day-one)
- [Labels versus tags](#labels-versus-tags)
- [Service agents](#service-agents)
- [Billing accounts](#billing-accounts)
- [Shared VPC and project topology](#shared-vpc-and-project-topology)
- [Choosing the shape](#choosing-the-shape)

## The hierarchy and what flows down it

```
Organization
  └── Folder (optional, nestable up to 10 levels)
        └── Project
              └── Resource (bucket, instance, service, ...)
```

Three different mechanisms inherit down this tree and they do not behave the same way:

| Mechanism | Inheritance | Conflict resolution |
|---|---|---|
| IAM allow policy | additive union of every level | a grant anywhere above is effective here; you cannot subtract with an allow policy |
| IAM deny policy | additive union | evaluated **before** allow; a matching deny wins outright |
| Organization policy | child may inherit, merge, or reset | for list constraints, a denied value anywhere in the merged chain wins over an allow |

The consequence people get wrong: **you cannot revoke an inherited role at a lower level.**
Granting `roles/editor` at the folder makes every project below it editable, and setting a
narrower policy on one project changes nothing. Use a deny policy, or move the project.

Folders require an organization. Without one (a project created under a plain Gmail account)
there is no folder layer, no org policy, and no organization-level IAM — that is a real
constraint on any design that assumes guardrails exist above the project.

## Projects

- **Project ID** — lowercase, 6–30 characters, globally unique across all of Google Cloud,
  **immutable after creation**, and unavailable for reuse after the project is deleted. This
  is the string you put in `--project` and in IAM member bindings.
- **Project number** — auto-assigned integer. Appears in service agent emails, Cloud Run
  `namespace` fields and many resource names. Not interchangeable with the ID when building
  strings by hand.
- **Project name** — display only, mutable, not unique.

Deleting a project soft-deletes it: it stays recoverable with `gcloud projects undelete` for
**30 days**, still counts against the organization's project quota during that window, and
then is destroyed irreversibly. Resources inside stop serving immediately, so "delete and
undelete" is not a safe rollback for anything live.

Place a **lien** on projects that must not be deleted by accident:

```bash
gcloud resource-manager liens create --project=PROJECT_ID \
  --restrictions=resourcemanager.projects.delete \
  --reason="prod, deletion requires platform team sign-off" --quiet
```

A lien makes `projects.delete` fail for everyone, including owners, until it is removed. It is
the only project-level protection that survives a user having `roles/owner`.

## Organization policy

Organization policy constrains *what configurations are allowed*, independent of who has
permission. IAM answers "may this principal act"; org policy answers "may this resource exist
in this shape". They are separate systems and a project owner cannot override an inherited
enforced constraint.

Two constraint kinds:

- **Boolean** — `enforce: true|false`. Example: `iam.disableServiceAccountKeyCreation`.
- **List** — allowed or denied values. Example: `gcp.resourceLocations`,
  `compute.vmExternalIpAccess`.

A child policy either inherits the parent's rules (`inheritFromParent: true`, merged) or
replaces them (`inheritFromParent: false`), and `reset: true` restores the Google default.
In a merged list policy, **a denied value anywhere in the chain wins** over an allow at any
level — so an exception at project level must be granted by editing the ancestor's policy or
by a conditional rule, not by adding an allow lower down.

Test before enforcing. Setting a policy in **dry-run** mode records violations to audit logs
without blocking anything:

```bash
gcloud org-policies set-policy policy.yaml --update-mask=dryRunSpec --quiet
```

Enforcing `compute.vmExternalIpAccess` or `gcp.resourceLocations` blind on a live
organization breaks running deployments; the dry-run audit entries tell you which ones first.

Custom constraints (`gcloud org-policies set-custom-constraint`) let you write CEL against a
resource's own fields when no built-in constraint exists — for example, requiring every Cloud
SQL instance to have `settings.availabilityType == "REGIONAL"`.

## Constraints worth enforcing on day one

| Constraint | Why |
|---|---|
| `iam.disableServiceAccountKeyCreation` | downloaded JSON keys are the most common long-lived credential leak; blocks the creation path rather than auditing it afterwards |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | stops default Compute/App Engine service accounts being handed `roles/editor` at creation. **Enforced by default only for organizations created after 3 May 2024** — older organizations must set it explicitly, and every existing default service account still holds Editor until you strip it |
| `iam.allowedPolicyMemberDomains` | blocks granting access to identities outside your Cloud Identity domains, which is how "we added a personal Gmail as owner" happens |
| `storage.publicAccessPrevention` | prevents `allUsers`/`allAuthenticatedUsers` on buckets organization-wide |
| `compute.vmExternalIpAccess` | most workloads do not need a public IP; deny by default and allow-list the exceptions |
| `gcp.resourceLocations` | data residency, enforced at create time instead of discovered in an audit |
| `sql.restrictPublicIp` | Cloud SQL instances default to a public IP path; this closes it |

## Labels versus tags

They look similar and solve different problems. Choosing wrong means rebuilding your cost
reporting or your guardrails later.

| | Labels | Tags (resource-manager tags) |
|---|---|---|
| Shape | free-form `key: value` on a resource | `key`/`value` objects defined at org or project, then bound to resources |
| Governed by IAM | no — anyone who can edit the resource can set any label | yes — `roles/resourcemanager.tagUser` to bind, separate permission to define |
| Inherited | no | yes, down the hierarchy, with override at a lower level |
| Usable in policy | no | yes — IAM conditions, org policy conditions, firewall policy rules |
| Shows up in billing export | yes | yes |

Use labels for cost attribution and ad-hoc grouping (`team`, `env`, `cost-center`). Use tags
when an access or policy decision depends on the value (`environment: production` gating a
deny policy). A label named `env: prod` is a comment; a tag named `environment/production` can
be enforced.

## Service agents

Google-managed service accounts, created automatically when an API is enabled, with emails
like `service-482910337712@gcp-sa-cloudbuild.iam.gserviceaccount.com` or
`482910337712@cloudbuild.gserviceaccount.com`. They carry the roles a Google service needs to
act on your resources.

Two facts that cause outages:

- Removing what looks like an unused binding for a service agent breaks the service, often
  with a delayed and unrelated-looking error. Before deleting any binding whose member matches
  `*gcp-sa-*` or `*@*.gserviceaccount.com` and which you did not create, identify the agent.
- The **Compute Engine default service account**
  (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`) is not a service agent — it is a
  user-managed account that Google creates for you, and it is the default identity for Compute
  Engine VMs, and for Cloud Run and Cloud Functions when no service account is specified. A
  workload running as it inherits whatever that account holds, which in older organizations is
  `roles/editor`, i.e. write access to almost the whole project. Give every workload its own
  dedicated service account with only the roles it needs.

## Billing accounts

A project has at most one billing account. Detaching it stops billable services in that
project — this is a hard stop, not a warning, and it is why `gcloud billing *` belongs on the
human-approval list. Billing account IAM is separate from project IAM: `roles/billing.admin`
on the billing account does not grant anything inside the projects it pays for, and
`roles/owner` on a project does not let you change what pays for it.

## Shared VPC and project topology

Shared VPC puts the network in a **host project** and lets **service projects** attach
workloads to its subnets. The network team owns firewall rules, subnets and Cloud NAT in one
place; application teams get project-level isolation without each inventing a VPC. Grant
`roles/compute.networkUser` on the specific subnet, not the whole host project, or service
project owners can attach to any subnet including production.

VPC Service Controls is a different mechanism: a perimeter around a set of projects that
blocks data egress to Google APIs outside it, even for a principal holding valid IAM. It
defends against exfiltration by an authorized identity, which IAM by definition cannot. It
also breaks legitimate cross-perimeter access in ways that are hard to diagnose — stand it up
in dry-run mode first.

## Choosing the shape

A workable default for a small organization:

```
Organization
├── folder: bootstrap      (Terraform state, CI identity, org-policy admin)
├── folder: platform       (shared VPC host project, Artifact Registry, logging sinks)
└── folder: workloads
    ├── folder: prod       (one project per application)
    └── folder: nonprod    (one project per application per environment)
```

The environment boundary is a folder (so org policy and IAM differ between prod and nonprod),
and the application boundary is a project (so a quota exhaustion, a billing anomaly or a
compromised service account is contained). Separating environments by label inside one project
gives you neither.

<!-- sources: gcp-docs, google-skills -->
