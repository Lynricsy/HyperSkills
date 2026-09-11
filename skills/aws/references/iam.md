# IAM, identity and organisation controls

Verified against: AWS IAM User Guide, AWS Organizations User Guide and the IAM API reference
as published on docs.aws.amazon.com. Rules marked `[verified]` were reproduced locally;
everything else is `[official]`.

## Contents

- [How a request is actually authorised](#how-a-request-is-actually-authorised)
- [Permissions boundaries and what they do not bound](#permissions-boundaries-and-what-they-do-not-bound)
- [SCPs and resource control policies](#scps-and-resource-control-policies)
- [Escalation paths worth auditing for](#escalation-paths-worth-auditing-for)
- [Condition operators and their empty-set behaviour](#condition-operators-and-their-empty-set-behaviour)
- [Trust policies and the confused deputy](#trust-policies-and-the-confused-deputy)
- [STS: sessions, chaining and regional endpoints](#sts-sessions-chaining-and-regional-endpoints)
- [Getting to least privilege from evidence](#getting-to-least-privilege-from-evidence)
- [Debugging an AccessDenied](#debugging-an-accessdenied)
- [Quotas and other sharp edges](#quotas-and-other-sharp-edges)

## How a request is actually authorised

Every API call is evaluated against the union of the policy types that apply, in a fixed
order. Only two of them can grant anything:

| Policy type | Can grant | Can deny | Attached to |
|---|---|---|---|
| Identity-based (managed or inline) | yes | yes | user, group, role |
| Resource-based (bucket policy, queue policy, KMS key policy, Lambda permission) | yes | yes | the resource |
| Permissions boundary | no | yes (by omission) | user or role |
| Service control policy (SCP) | no | yes (by omission) | OU or account |
| Resource control policy (RCP) | no | yes (by omission) | OU or account |
| Session policy (passed to `AssumeRole`) | no | yes (by omission) | the session |

The decision: an explicit `Deny` in *any* of them ends the evaluation. Otherwise the request
must be allowed by at least one granting policy **and** not excluded by every restricting
policy that applies. This is why "add a boundary" is never the fix for an over-broad identity
policy — the boundary narrows what the principal could ever do, but the over-broad statement
is still the thing being intersected. `[official]`

The one asymmetry worth memorising: for a **resource-based** policy, being named as
`Principal` is itself a grant, so a caller in the same account needs no identity-policy
statement at all. Cross-account is the opposite — both sides must allow.

## Permissions boundaries and what they do not bound

A boundary is an intersection: effective permissions are `identity policy ∩ boundary`. Three
consequences that catch people:

- A boundary cannot grant. Attaching a boundary that allows `s3:*` to a role with no identity
  policy gives that role nothing.
- Whether a resource-based policy escapes the boundary depends on **which kind of ARN** it
  names as `Principal`, and conflating the three is how audits go wrong. Within the same
  account: an **IAM user ARN** is not limited by an implicit deny in that user's identity
  policy or permissions boundary — a bucket policy granting `s3:*` to
  `arn:aws:iam::111122223333:user/ci-bot` works even if `ci-bot`'s boundary excludes S3. An
  **IAM role session ARN** (`arn:aws:sts::111122223333:assumed-role/<role>/<session>`) is
  likewise not limited, because the grant lands on the session. But an **IAM role ARN** is
  still limited by an implicit deny in a permissions boundary or session policy, so naming
  `arn:aws:iam::111122223333:role/ci-role` does *not* bypass that role's boundary. An
  explicit `Deny` anywhere always wins, in all three cases. `[official]`
- Boundaries are commonly used as a *delegation* control: give a team `iam:CreateRole` only
  with `iam:PermissionsBoundary` conditioned to your boundary policy, so they can create roles
  but not roles more powerful than the boundary. Without that condition the delegation is an
  escalation path.

## SCPs and resource control policies

An SCP filters what principals **in your accounts** may do. An RCP filters what may be done
**to your resources**, including by principals outside your organisation — that is the gap
SCPs never covered. Both are deny-by-omission filters and never grant.

Operational consequences:

- An SCP denial arrives as a normal `AccessDenied`, often naming the CloudFormation execution
  role rather than the human. It is an environment-level failure: no template edit fixes it.
- SCPs do not apply to the management account, and they do not apply to service-linked roles.
- The suspended-account trap: a suspended or closed member account cannot be removed from the
  organisation until it is permanently closed, which takes roughly 90 days. Remove the account
  from the organisation *first*, then close it. `[official]`

## Escalation paths worth auditing for

Audit for these combinations before auditing for wildcards; a narrow policy containing one of
them is more dangerous than a broad policy containing none.

1. **`iam:PassRole` plus a compute create/update action.** `lambda:CreateFunction`,
   `lambda:UpdateFunctionConfiguration`, `ec2:RunInstances`, `ecs:RegisterTaskDefinition`,
   Glue, SageMaker and `cloudformation:*` all take a role ARN. With `PassRole` on
   `Resource: "*"`, the holder attaches the account's most powerful role to compute it
   controls and reads that role's credentials. Scope `Resource` to specific role ARNs or an
   IAM path, and add `Condition: {"StringEquals": {"iam:PassedToService": "lambda.amazonaws.com"}}`.
2. **Self-modification of policy.** `iam:PutUserPolicy`, `PutRolePolicy`, `PutGroupPolicy`,
   `CreatePolicy`, `CreatePolicyVersion`, `AttachUserPolicy`, `AttachRolePolicy`,
   `AttachGroupPolicy` — any of these on the principal's own identity is administrator access
   one call away.
3. **`sts:AssumeRole` into something broader**, especially where the target role's trust
   policy is permissive.
4. **`iam:UpdateAssumeRolePolicy`** — rewriting a role's trust policy to trust yourself.
5. **`kms:*` on a key** whose policy is the only thing protecting encrypted data.
6. **`cloudformation:*` with a service role** — CloudFormation acts with the service role's
   permissions, so stack creation becomes a proxy for that role.

## Condition operators and their empty-set behaviour

Multi-value context keys need `ForAnyValue:` or `ForAllValues:` prefixes, and the two behave
very differently when the key is missing:

- `ForAnyValue:` is false when the key is absent — fail-closed, usually what you want.
- `ForAllValues:` is **true** when the key is absent or empty. Universal quantification over
  an empty set is vacuously true, so a request that carries no tags at all satisfies a
  `ForAllValues:StringEquals` on `aws:TagKeys`. `[official]`

The repair is a `Null` check on the same context key, in the same `Condition` block:

```json
"Condition": {
  "ForAllValues:StringEquals": { "aws:TagKeys": ["Owner", "CostCentre"] },
  "Null": { "aws:TagKeys": "false" }
}
```

Two more condition traps:

- A condition on a context key the calling service never populates silently allows
  everything, because a condition on an absent key with a non-`Null` operator is not
  evaluated as false in the way people expect. Check the service authorization reference for
  which keys a given action supports.
- `StringLike` with `*` inside an ARN is fine; `StringEquals` with a `*` in the value is a
  literal asterisk and will never match.

## Trust policies and the confused deputy

A role's trust policy is a resource-based policy whose only action is `sts:AssumeRole`. Two
recurring holes:

- **Service principal without source conditions.** `"Principal": {"Service":
  "codebuild.amazonaws.com"}` means *any* CodeBuild project, in any account, that the service
  chooses to act for. Add `aws:SourceAccount` (your account id) and, where the service
  supports it, `aws:SourceArn` (the specific project or resource ARN).
- **Account root principal.** `"Principal": {"AWS": "arn:aws:iam::444455556666:root"}` trusts
  every principal in that account which is *itself* permitted `sts:AssumeRole` on this role.
  That is a delegation to the other account's administrators, not to one role. Name the
  specific role ARN, and for third-party (vendor) access require `sts:ExternalId`.

For OIDC federation (GitHub Actions, EKS service accounts), the trust policy conditions on
`sub` and `aud` are the whole security boundary. A `sub` condition using `StringLike` with a
trailing `*` — `repo:acme/*` — trusts every repository in the organisation, including a new
one an attacker can create. Thumbprints are no longer required for most OIDC providers
because AWS verifies them against trusted CAs. `[official]`

## STS: sessions, chaining and regional endpoints

- **Role chaining** (assuming a role from credentials that are themselves a role session) caps
  the session at **1 hour**, regardless of `DurationSeconds` or the role's maximum session
  duration. A pipeline that chains twice and expects 12 hours will fail mid-run. `[official]`
- `GetSessionToken` credentials cannot call IAM APIs unless MFA was included, and cannot call
  STS except `AssumeRole` and `GetCallerIdentity`.
- Assuming a role into an **opt-in region** requires the *target* account to have enabled that
  region; enabling it in the calling account changes nothing.
- Prefer regional STS endpoints (`sts.<region>.amazonaws.com`). The global endpoint is a
  single point of failure and its sessions are not valid in opt-in regions by default.

## Getting to least privilege from evidence

Narrowing wildcards by intuition produces policies that are both too broad and broken. Use
evidence:

- **IAM Access Analyzer policy generation** builds a policy from the principal's CloudTrail
  history over a time window. It is the right starting point for an existing workload.
- **Access Analyzer policy validation** checks a draft policy for errors, security warnings
  (such as `PassRole` with a wildcard) and suggestions, offline against the policy grammar.
- **The service authorization reference** lists, per service, every action with its resource
  types and condition keys. Use it to map "the app calls `GetObject` and `ListBucket`" to the
  exact actions, rather than reaching for `s3:*`.
- **External access findings** in Access Analyzer tell you which of your resources are
  reachable from outside the account or organisation — the question a bucket policy review is
  actually trying to answer.

## Debugging an AccessDenied

Read the message before theorising. AWS denials name the principal, the action and the
resource, and increasingly say *why*:

| Message fragment | Meaning |
|---|---|
| `with an explicit deny in a service control policy` | Organisation-level; fix the SCP or move the account |
| `with an explicit deny in a resource-based policy` | The resource's own policy denies it |
| `with an explicit deny in a permissions boundary` | Boundary excludes the action |
| `because no identity-based policy allows` | Nothing granted it; add the statement |
| `is not authorized to perform: iam:PassRole on resource` | The role ARN is outside the `PassRole` scope |
| `The security token included in the request is expired` | Session lifetime, not permissions |

Then confirm with `aws iam simulate-principal-policy --policy-source-arn <role-arn>
--action-names <action> --resource-arns <arn>`, which evaluates identity policies, boundaries
and SCPs without making the real call. For resource-based policies, pass them explicitly with
`--resource-policy`, because the simulator does not fetch them.

## Quotas and other sharp edges

- A managed policy keeps at most **5 versions**; `CreatePolicyVersion` fails once full, so
  automation must delete the oldest version.
- Inline policy size limits are per-identity (2,048 characters for a user, 10,240 for a role);
  managed policies are 6,144 characters. Long resource lists hit these before you expect.
- An instance profile is eventually consistent after creation — a `RunInstances` immediately
  after `AddRoleToInstanceProfile` can fail with an invalid-profile error. Wait, then retry.
- Unassigned virtual MFA devices are deleted automatically when a new one is created for the
  same user, which quietly breaks a half-finished enrolment.
- Deleting a role does not delete the sessions already issued from it; they remain valid until
  they expire unless you also revoke them (attach a deny policy conditioned on
  `aws:TokenIssueTime`).

<!-- sources: aws-agent-toolkit, aws-docs, aws-builder-samples -->
