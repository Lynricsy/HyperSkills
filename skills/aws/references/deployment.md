# Deployment: CloudFormation, SAM and CDK

Verified against: CloudFormation User Guide and API reference, AWS SAM developer guide, and
CDK CLI documentation. Local checks were run with **cfn-lint 1.56.3** and are marked
`[verified]`.

## Contents

- [Choosing the tool](#choosing-the-tool)
- [Resource identity is the whole game](#resource-identity-is-the-whole-game)
- [Validation layers, and what each one misses](#validation-layers-and-what-each-one-misses)
- [Reading a failed deployment](#reading-a-failed-deployment)
- [Stack states and how to leave them](#stack-states-and-how-to-leave-them)
- [Cross-stack references and the deadly embrace](#cross-stack-references-and-the-deadly-embrace)
- [Protecting stateful resources](#protecting-stateful-resources)
- [Fast deployment modes are development-only](#fast-deployment-modes-are-development-only)
- [Adopting existing resources](#adopting-existing-resources)
- [Drift](#drift)
- [CDK specifics worth knowing](#cdk-specifics-worth-knowing)
- [Secrets and parameters](#secrets-and-parameters)

## Choosing the tool

All three produce CloudFormation stacks; the question is who writes the template.

| Situation | Tool | Why |
|---|---|---|
| Mostly Lambda, API Gateway, DynamoDB, queues | SAM | The transform collapses a dozen resources into one, `sam local` gives an offline loop, and the YAML stays readable |
| Needs abstraction, shared constructs, multi-environment synthesis, unit tests over infrastructure | CDK | Real types and real tests; `aws-cdk-lib/assertions` can assert a logical id has not moved |
| Team already owns YAML, or the template is read by people who do not write TypeScript | CloudFormation | No synthesis step, no bootstrap, no toolchain drift |
| Multi-cloud, or the organisation standardised on HCL | Terraform | Use the `terraform` skill; the service and quota reasoning in this skill still applies |

SAM and CDK coexist: `sam build` and `sam local invoke` work against a synthesised CDK
template, so a CDK project can still use the SAM local loop.

Avoid mixing console edits with any of them. A resource changed by hand is drift, and the next
deployment either reverts it or fails on a state it did not expect.

## Resource identity is the whole game

CloudFormation tracks resources by **logical id**. A changed logical id is a different
resource: CloudFormation creates the new one and deletes the old one. Most production
accidents in this area are a rename nobody thought was a rename.

- In plain CloudFormation the logical id is the YAML key. Renaming `EventsTable` to
  `OrdersTable` destroys the table.
- In CDK the logical id is derived from the construct **path** — the construct id plus every
  parent id, hashed. Renaming a construct, moving it into a different parent, or moving it to
  another stack all change it.
- `cdk refactor` (behind `--unstable=refactor`) moves resources between stacks and paths while
  preserving identity. Do the refactor and the property change in separate deployments.
- `CfnResource.overrideLogicalId` pins the old id when a rename must happen anyway.
- `aws-cdk-lib/assertions` can assert that a stateful resource still has its expected logical
  id, which turns "we renamed a construct" into a failing unit test instead of a 2am page.

Treat `destroy` or `Replace` on a stateful resource in `cdk diff` or a change set as a stop
condition, not a warning. Some property changes also force replacement — a DynamoDB partition
key, an RDS `DBInstanceIdentifier`, an S3 `BucketName` — and the change set is the only place
that shows it before it happens.

## Validation layers, and what each one misses

Run three layers; they catch different classes of error.

1. **Schema and rules — `cfn-lint`** (or `sam validate --lint`, which wraps it). Offline,
   validates against the resource provider schemas including the SAM transform.
2. **Policy — `cfn-guard`.** Offline, evaluates organisational rules the schema does not know
   about: encryption required, no public buckets, tagging.
3. **Pre-deployment — a change set.** Shows what CloudFormation will actually do, including
   replacements. This is the only layer that sees the current stack.

What layer 1 does not catch, measured with **cfn-lint 1.56.3** `[verified]`:

| Template | Result |
|---|---|
| `AWS::S3::Bucket` with `BucketNam` (typo) | `E3002 Additional properties are not allowed … Did you mean 'BucketName'?` |
| `AWS::Lambda::Function` with `Timeout: 901` | `E3717 901 is greater than the maximum of 900 for functions without 'CapacityProviderConfig'` |
| `AWS::Serverless::Function` with `Timeout: 901` | **no finding** |
| `AWS::Lambda::Function` with `MemorySize: 12000` (ceiling is 10,240) | **no finding** |
| A SAM template whose HTTP API timeout is unreachable and whose SQS visibility timeout is below the consumer's function timeout | **no finding** |

So a clean `cfn-lint` run means "the schema is satisfied". It is a precondition for review,
never a substitute for one.

## Reading a failed deployment

Use `aws cloudformation describe-events --stack-name <name> --filters FailedEvents=true`.
The `DescribeEvents` API groups events by operation id and returns progress events, early
validation errors, provisioning errors and Hook invocation errors; its `Filters` parameter
takes an `EventFilter` whose `FailedEvents` boolean narrows the result to failures.
`DescribeStackEvents` has no filter parameter at all and never returns validation or Hook
failures — `--query` on its output is not an equivalent, because the events are not there.
`[official]`

Then read the events, not just the first one:

- A `ResourceStatusReason` of `Resource creation cancelled` carries no information. It means
  CloudFormation stopped that resource because something else failed. Never diagnose from it.
- Several resources failing with *specific* messages at the same timestamp are parallel
  failures from one root cause — typically a missing permission that several resources needed.
  Enumerate all of them; fixing one at a time turns a single fix into a week of deployments.
- Resources that were cancelled may have their own problems that only appear once the visible
  failures are fixed. Say so rather than promising the next attempt will work.

Finally classify each finding:

- **Template-level**: a wrong property, a missing dependency, an unreachable timeout. Edit the
  template.
- **Environment-level**: an SCP denial, an exhausted quota, deletion protection, an AMI that
  does not exist in the region, a resource already created by hand. No template edit fixes
  these, and proposing one wastes a deployment cycle.

An SCP or IAM denial during a CDK deployment names the **CloudFormation execution role**
(`cdk-<qualifier>-cfn-exec-role-<account>-<region>`), not the engineer. The permission has to
be granted to that role.

## Stack states and how to leave them

| State | Meaning | Way out |
|---|---|---|
| `ROLLBACK_COMPLETE` | Initial create failed and rolled back; the stack has no resources | Delete the stack and create again — it cannot be updated |
| `UPDATE_ROLLBACK_FAILED` | Rollback itself failed; the stack is stuck | `cdk rollback`, or `continue-update-rollback --resources-to-skip <LogicalId>` after fixing or manually reconciling the resource |
| `UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS` | Rollback succeeded, old resources being removed | Wait; it is terminal-adjacent, not stuck |
| `DELETE_FAILED` | A resource refused deletion (deletion protection, non-empty bucket, in-use ENI) | Remove the blocker, or delete with `--retain-resources` |
| `REVIEW_IN_PROGRESS` | A change set was created but never executed | Execute or delete the change set |

Deleting a production stack to escape a bad state destroys everything it owns that is not
`Retain`. It is almost never the right move.

## Cross-stack references and the deadly embrace

`Fn::ImportValue` creates a hard dependency: while any stack imports an export, the producing
stack cannot change or remove it. The error is
`Export <name> cannot be deleted as it is in use by <stack>`, and it can leave both stacks
unable to deploy.

The ordered escape:

1. `aws cloudformation list-imports --export-name <name>` to find every consumer.
2. Change each consumer to stop using the import — inline the value, read it from SSM
   Parameter Store, or accept it as a parameter — and deploy the consumers.
3. Only then remove the export from the producer.

In CDK the same problem appears when a cross-stack reference is deleted. Weaken the reference
first (`CrossStackReferences.of(resource).produce(ReferenceStrength.BOTH)`, then `WEAK`, then
remove — three deployments), or use the older two-deployment `this.exportValue()` recipe.

Prefer SSM Parameter Store over exports for anything crossing an ownership boundary: it is a
late binding, so the producer can change without coordinating a three-step dance.

## Protecting stateful resources

- `DeletionPolicy: Retain` and `UpdateReplacePolicy: Retain` on every database, table and
  bucket. Without the second one, a replacement destroys the data even though deletion is
  protected.
- `Retain` cuts both ways: a retained resource removed from the template becomes an orphan
  nobody owns, and it still costs money. Removing it is a decision about ownership transfer,
  not a cleanup.
- Put stateful resources in their own stack with `terminationProtection: true`. The blast
  radius of a stateless deployment should not include the database.
- A non-empty S3 bucket will not delete. In CDK that needs both `removalPolicy: DESTROY` and
  `autoDeleteObjects: true`; on a versioned bucket, delete markers survive what looks like a
  successful emptying.
- DynamoDB deletion protection blocks the delete half of a replacement, which is how a rename
  turns into `UPDATE_ROLLBACK_FAILED` rather than silent data loss. That is the good outcome.

## Fast deployment modes are development-only

They are not the same mechanism and they fail differently.

| | `cdk deploy --hotswap` | Express mode |
|---|---|---|
| Path | direct service APIs, bypassing CloudFormation | real CloudFormation, faster completion |
| Drift | creates it deliberately | none |
| Non-hotswappable changes | silently skipped, still reports success | n/a |
| Rollback | n/a | disabled by default; a failed deployment cannot be rolled back |
| Recovery | `cdk deploy --revert-drift` | fix and roll *forward* with another Express deployment |

Express mode completes as soon as resource configuration is applied, while resources continue
stabilising in the background — so it is wrong for anything that must serve traffic the moment
the stack reports complete. `aws cloudformation deploy` does not support it; use
`create-stack`/`update-stack` with `--deployment-config '{"mode": "EXPRESS"}'`.

Both belong behind an IAM or pipeline control that makes them impossible in production, not
behind a convention.

## Adopting existing resources

Prefer declarative adoption that leaves a reviewable artefact:

- CloudFormation: `IMPORT` change sets, or `create-stack` with `--resources-to-import`.
- CDK: `cdk import` (interactive, or `--resource-mapping` for CI), or
  `cdk deploy --import-existing-resources` when the template already describes them.
- The IaC generator can produce a first-draft template from existing resources; treat its
  output as a draft — it emits every computed attribute, and those must be removed before the
  template is maintainable.

Imported resources must match the template exactly or the import fails, which is a feature:
the failure is telling you the template does not describe reality.

## Drift

`aws cloudformation detect-stack-drift` and `cdk drift` (with `--fail` in CI) compare live
resources against the template. Two things they do not do: they do not cover every resource
type, and they do not tell you *who* drifted it — pair a scheduled drift check with CloudTrail
for that. Drift on a stack that also uses hotswap is expected and meaningless, which is one
more reason to keep hotswap out of shared environments.

## CDK specifics worth knowing

- Commit `cdk.context.json`. It caches VPC, AZ and AMI lookups; without it, synthesis contacts
  AWS and can produce a different template on a different day.
- Set an explicit `env: { account, region }` on stacks that do environment-specific lookups;
  otherwise the stack is environment-agnostic and the lookups fail at synth.
- Prefer L2 constructs and `grant*()` methods over hand-written IAM statements — `grant*`
  produces a narrower policy than most people write, and it updates when the resource does.
- Escape hatch order: L2 property → `node.defaultChild` with `addPropertyOverride` → L1
  construct. Reaching for L1 because one property is missing loses every default the L2 set.
- `cdk-nag` (`Aspects.of(app).add(new AwsSolutionsChecks())`) applies AWS Solutions rules at
  synth time; suppress findings with `NagSuppressions` and a written reason, never by removing
  the aspect.
- `cdk bootstrap` creates the roles the CLI assumes. A `BootstrapVersionValidation` error means
  the bootstrap stack is older than the CLI expects; mismatched `--qualifier` values between
  bootstrap and app are the other common cause.

## Secrets and parameters

- Never a plain `String` parameter and never a Lambda environment variable. Both are readable
  by anyone with describe permission.
- Use dynamic references: `{{resolve:secretsmanager:<secret>:SecretString:<key>}}` or
  `{{resolve:ssm-secure:<name>:<version>}}`. They are resolved at deployment and not stored in
  the template.
- Never write secrets or personal data into a resource's `Metadata`: it is unencrypted and
  returned by the CloudFormation APIs.
- Template bodies are limited to 1,048,576 bytes (51,200 inline). Approaching the limit is a
  signal to split the stack by ownership, not to minify the YAML.

<!-- sources: aws-agent-toolkit, awslabs-agent-plugins, aws-docs -->
