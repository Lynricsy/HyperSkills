---
name: aws
description: "Guides AWS architecture and control-plane work: IAM policy evaluation, permissions boundaries, trust policies and PassRole escalation; Lambda, API Gateway, Step Functions, SQS and EventBridge selection and quotas; choosing between CloudFormation, SAM and CDK and recovering a stack that is stuck or about to replace a stateful resource; managed data service selection; VPC endpoints, NAT and cross-AZ traffic; EKS and ECS control planes; CloudWatch quotas and billing; Well-Architected trade-offs; and cost work with Cost Explorer, Compute Optimizer, Savings Plans and Budgets. Use when reviewing an IAM policy, a SAM or CloudFormation template or a CDK app, diagnosing a 504, a throttle, a failed deployment or a cost spike, or picking an AWS service. Do not use for Terraform HCL (use the `terraform` skill), Dockerfiles or Kubernetes manifests (`containers`), OpenTelemetry instrumentation or alerting pipelines (`observability`), Azure, Google Cloud, or building LLM applications on Bedrock."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# aws

## Scope

Covers the AWS control plane and the architecture decisions that sit on top of it: identity
(IAM policy evaluation, permissions boundaries, trust policies, SCPs, Organizations, STS),
serverless compute and integration (Lambda, API Gateway, Step Functions, SQS, EventBridge),
deployment through AWS's own tooling (CloudFormation, SAM, CDK) including stack recovery and
safe refactoring, managed data service selection and its quotas, networking as it affects
cost and reachability (VPC endpoints, NAT, cross-AZ), the EKS and ECS control planes,
the CloudWatch product surface, Well-Architected trade-offs, and cost analysis.

Not covered:

- Terraform and OpenTofu — HCL, modules, state, `moved`/`import`, `terraform test`. Use the
  `terraform` skill, even when every resource in the file is an AWS resource. Where this skill
  shows infrastructure as code it uses AWS's own tools; if the user is on Terraform, the
  service selection and quota reasoning here still applies and the syntax does not.
- Dockerfiles, Compose, Kubernetes manifests, Helm and Kustomize, probes, resource limits and
  Pod security. Use the `containers` skill. The split at EKS is: cluster creation, node
  groups, IAM integration, the networking plugin and managed upgrades are here; anything
  inside `kubectl apply` is there.
- OpenTelemetry instrumentation, Collector configuration, semantic conventions, structured
  logging, RED/USE metrics, tracing, alerting and SLOs. Use the `observability` skill. The
  CloudWatch product surface itself — quotas, billing dimensions, Logs Insights syntax,
  console flows — is here.
- Index and mapping design for OpenSearch-style search workloads. Use the `elasticsearch`
  skill for query DSL and mappings; service selection and quotas stay here.
- Microsoft Azure and Google Cloud. Use the `azure` and `gcp` skills. Cross-cloud comparison
  is out of scope beyond a sentence where a decision genuinely depends on it.
- Building LLM applications on Bedrock, AgentCore or SageMaker inference — prompting, RAG,
  agent orchestration, evaluation. Use the `ai-engineering` skill; training or fine-tuning the
  weights is the `ml-training` skill. Bedrock's IAM, quota and cost surface is in scope like
  any other service.

Paths below are relative to this skill's directory.

## Core rules

1. Establish the account, the region and the calling identity before quoting anything
   account-specific: `aws sts get-caller-identity` and `aws configure list`. Almost every
   confusing AWS error is the right command against the wrong account or region.
2. Quotas are per account and per region, and most of the interesting ones are adjustable
   defaults rather than physical limits. Read the current value with
   `aws service-quotas get-service-quota` instead of quoting a remembered number when the
   number drives an architecture decision.
3. Policy evaluation is deny-biased and has a fixed order: an explicit `Deny` anywhere wins;
   then an SCP, a resource control policy, a permissions boundary and a session policy can
   each only *remove* permission; only identity-based and resource-based policies grant. A
   boundary attached to a role does not make an over-broad policy safe
   (`references/iam.md`).
4. `iam:PassRole` with `Resource: "*"` next to any create-or-update action on a compute
   service — `lambda:CreateFunction`, `ec2:RunInstances`, `ecs:RegisterTaskDefinition`,
   `cloudformation:*`, Glue, SageMaker — is administrator access in disguise. Scope
   `Resource` to specific role ARNs or an IAM path and constrain with `iam:PassedToService`.
5. `ForAllValues:*` is vacuously true when the context key is absent from the request, so a
   caller who sends no tags at all passes a `ForAllValues:StringEquals` on `aws:TagKeys`.
   Pair it with `"Null": {"<same key>": "false"}` in the same `Condition` block.
6. A resource-based policy naming an IAM **user** ARN or an **assumed-role session** ARN of
   the same account as `Principal` is not limited by that principal's permissions boundary; a
   policy naming a **role** ARN still is. Auditing identity policies alone understates
   effective permissions (`references/iam.md`).
7. A trust policy with a service principal and no `aws:SourceAccount` / `aws:SourceArn`, or
   with `arn:aws:iam::<account>:root` and no `sts:ExternalId`, is a confused-deputy hole: the
   whole external account, not one role, can assume it.
8. Prove a permission change instead of reasoning about it: `aws iam simulate-principal-policy`
   or `simulate-custom-policy` answers "can this principal do this" offline, and IAM Access
   Analyzer generates a least-privilege policy from CloudTrail rather than from imagination.
9. An `AWS::Serverless::HttpApi` is API Gateway v2, whose maximum integration timeout is
   **30 seconds and is not increasable**. A REST API defaults to 29 seconds and can be raised
   only on Regional and private endpoints — not edge-optimized — and the increase may cost
   Region-level throttle quota. Anything slower belongs off the request path
   (`references/serverless.md`).
10. Lambda's function timeout is 900 seconds; only Lambda Managed Instances functions invoked
    asynchronously or through an event source mapping (except Amazon MQ and DocumentDB) reach
    5,400 seconds. Design against 900 unless you have deliberately chosen Managed Instances.
11. Every Lambda invocation can be delivered more than once, and every retrying client
    produces the same effect. Idempotency keyed on a business identifier is part of the
    handler's contract, not a hardening pass.
12. An SQS queue's visibility timeout must be at least the consumer's function timeout —
    AWS's guidance is about six times it. A queue whose visibility timeout is below the
    function timeout redelivers work that is still running, and the symptom surfaces as
    duplicated side effects, not as an error.
13. Pick the API type before anything else. REST API buys usage plans, request validation,
    caching, WAF, resource policies, private endpoints and canary deployments; HTTP API buys
    roughly 70% lower cost and lower latency and has none of them. Changing your mind later
    is a rewrite, not a setting.
14. Choose the IaC tool by workload shape: SAM for an application that is mostly Lambda, API
    and tables; CDK when you need real abstraction, multi-environment synthesis and unit tests
    over the infrastructure; plain CloudFormation when the team already owns YAML or when the
    template must be readable by people who do not write TypeScript. For Terraform, use the
    `terraform` skill (`references/deployment.md`).
15. A CDK construct id is what produces the CloudFormation logical id. Renaming a construct or
    moving it between stacks changes the logical id, and CloudFormation answers a changed
    logical id with delete-and-create. Treat `destroy` on a stateful resource in `cdk diff` as
    a stop condition, and preserve identity with `cdk refactor` or `overrideLogicalId`.
16. Read failures with `aws cloudformation describe-events --stack-name <name>
    --filters FailedEvents=true`. `describe-stack-events` accepts no filter and never returns
    early-validation or Hook failures. Then read *every* failed event: a
    `ResourceStatusReason` of `Resource creation cancelled` is rollback noise, and the events
    carrying real messages are the ones to fix — all of them, because fixing one surfaces the
    next on the following attempt.
17. Classify each deployment failure as template-level or environment-level before proposing a
    change. An SCP denial, an exhausted quota, deletion protection or a stuck resource is not
    fixed by editing the template.
18. `cdk deploy --hotswap` and Express-mode deployments are development-only and are not the
    same thing. Hotswap bypasses CloudFormation, creates drift on purpose, and silently
    ignores changes to non-hotswappable resources while still reporting success. Express runs
    the real CloudFormation path with no drift but disables rollback, and a failed Express
    deployment can only be rolled *forward*.
19. A CloudFormation `Export` cannot be removed while another stack imports it. Check
    `list-imports` first and break the dependency in the consumer before the producer, or the
    two stacks deadlock with neither able to deploy.
20. Gateway VPC endpoints for S3 and DynamoDB carry no hourly and no per-GB charge, so routing
    that traffic off the NAT path is free. Interface (PrivateLink) endpoints bill per AZ-hour
    plus per GB and only pay for themselves above a traffic threshold
    (`references/networking.md`).
21. EKS supports a Kubernetes minor version under standard support for 14 months, then 12
    months of extended support billed extra per cluster-hour. Extended support is **on by
    default**, and a cluster still running at the end of it is auto-upgraded. An unattended
    cluster therefore has both a surprise bill and a surprise upgrade in its future
    (`references/eks-control-plane.md`).
22. CloudWatch bills custom metrics per distinct metric per month, where a distinct metric is
    a unique name-and-dimension combination. High-cardinality dimensions — request id, user
    id, pod name — turn into a five-figure line item. CloudWatch Logs groups default to never
    expire, so log storage grows forever unless retention is set (`references/cloudwatch.md`).
23. Never hand a cost number to a human without computing it in a script. Also check the
    window: Cost Explorer's `--time-period` end date is exclusive, so
    `Start=2026-08-01,End=2026-08-31` silently omits 31 August (`references/cost.md`).
24. Sequence cost work by reversibility: delete idle and unattached resources first, right-size
    on Compute Optimizer evidence second, and buy Savings Plans last. A one- or three-year
    commitment bought before right-sizing locks in the waste.
25. Secrets never live in a Lambda environment variable, a CloudFormation `Parameter` of type
    `String`, or a resource `Metadata` block — all three are readable by anyone with describe
    permission on the resource. Use Secrets Manager or SSM `SecureString`, referenced
    dynamically (`{{resolve:secretsmanager:...}}`).
26. Finish with the gate that runs without an account: `cfn-lint` (or `sam validate --lint`)
    on every template, `cdk synth --strict` and `cdk diff` on every CDK change, and a policy
    scan such as `cfn-guard`. These catch schema and rule violations — they do not catch the
    architecture, so a clean run is a precondition, not a verdict.

## Workflows

### review-an-iam-policy-or-role

- [ ] Collect all four inputs before judging anything: the identity policy, the role's trust
      policy, any permissions boundary, and the resource-based policies of the resources it
      touches. A verdict from the identity policy alone is wrong in both directions
      (`references/iam.md`).
- [ ] Walk the escalation paths first, not the wildcards: `iam:PassRole` plus a compute
      create/update action, `iam:CreatePolicyVersion` or `Attach*Policy` on the principal's
      own policies, and `sts:AssumeRole` into something broader.
- [ ] Check every `Condition` for the operator's empty-set behaviour, for a missing `Null`
      guard, and for conditions on keys the calling service never sends.
- [ ] Check the trust policy for a root principal, a wildcard principal, a service principal
      without `aws:SourceAccount`/`aws:SourceArn`, and a missing `sts:ExternalId` on
      third-party access.
- [ ] Rewrite to least privilege from evidence — Access Analyzer policy generation over
      CloudTrail, or the service authorization reference for the exact actions an API call
      needs — rather than by narrowing wildcards by intuition.
- [ ] **Gate — the new policy is simulated, not asserted:** `aws iam simulate-custom-policy`
      allows every action the workload genuinely makes and denies each escalation path you
      identified, and IAM Access Analyzer policy validation returns no errors or security
      findings.

### design-or-review-a-serverless-application

- [ ] Fix the synchronous budget first: what is the slowest acceptable response, and does any
      integration exceed the API type's ceiling (30s hard on HTTP API, 29s default on REST)?
      If it does, the answer is an async pattern, not a larger timeout
      (`references/serverless.md`).
- [ ] Choose the API type against the governance requirements — usage plans, request
      validation, WAF, private endpoints — and record why, because switching later is a
      rewrite.
- [ ] Make every consumer idempotent, then make the queue agree with it: visibility timeout
      above the function timeout, a redrive policy with a DLQ, and partial batch failure
      reporting so one bad record does not replay its batch.
- [ ] Right-size memory against measured duration, remembering that 1,769 MB is exactly one
      vCPU and that arm64 is cheaper per GB-second for the same work.
- [ ] Replace broad managed policies (`*FullAccess`) with scoped ones, and keep secrets out of
      environment variables.
- [ ] **Gate — the template lints and the limits are written down:** `sam validate --lint` or
      `cfn-lint` exits 0, and the design names the quota that will break first under 10x
      traffic (account concurrency, API throttle, table capacity) with the observation that
      would show it.

### recover-a-stuck-or-failed-stack

- [ ] Get the real failures: `aws cloudformation describe-events --stack-name <name>
      --filters FailedEvents=true`. Do not use `describe-stack-events`; it cannot filter and
      omits validation and Hook failures (`references/deployment.md`).
- [ ] Discard the cascade (`Resource creation cancelled`) and enumerate *all* events with a
      specific `ResourceStatusReason`; parallel failures usually share one root cause.
- [ ] Ask what changed in the template's identity, not just its values: a renamed CDK
      construct, a moved resource, a changed `Condition`, a modified `Export`. Replacement of a
      stateful resource is the failure, even when the error message is about something else.
- [ ] Split the findings into template-level and environment-level, and route the
      environment-level ones (SCP, quota, deletion protection, drift) to the owner of that
      control rather than into a template edit.
- [ ] Recover the stack state deliberately: `cdk rollback` or `continue-update-rollback`,
      skipping only the resource that genuinely cannot roll back, and never by deleting a
      stack that owns production data.
- [ ] **Gate — the next deployment is provably safe:** `cdk diff` (or a change set) shows no
      `Replace` or `Remove` on any stateful resource, the stack is back in a `*_COMPLETE`
      state, and `list-imports` confirms no consumer still depends on an export you are
      dropping.

### reduce-the-bill-without-causing-an-incident

- [ ] Establish the baseline with a script, not by reading the console: `ce get-cost-and-usage`
      grouped by service over a correct window (end date is exclusive), and keep the script as
      the artefact (`references/cost.md`).
- [ ] Separate waste from spend: unattached volumes, idle load balancers, empty clusters,
      orphaned snapshots and stopped-but-provisioned resources cost money and carry no
      availability risk when deleted.
- [ ] Attack the architectural line items before the unit prices — NAT data processing,
      cross-AZ traffic, CloudWatch metric cardinality and log retention are usually larger and
      more permanent than instance sizing.
- [ ] Right-size only on evidence: enable Compute Optimizer
      (`compute-optimizer update-enrollment-status --status Active`), let it accumulate
      history, and take the recommendation with its performance risk rating.
- [ ] Commit last: Compute Savings Plans over instance-family RIs for flexibility, sized to the
      *post-right-sizing* floor of usage, never to current usage.
- [ ] **Gate — the plan is auditable and guarded:** each item names its monthly saving from the
      script's output, its blast radius, and how to undo it; and AWS Budgets plus Cost Anomaly
      Detection are in place so the next regression is caught by an alert rather than a board
      meeting.

### choose-a-managed-service

- [ ] State the constraints that eliminate options before comparing features: data model and
      access pattern, consistency requirement, peak and idle load shape, latency budget,
      compliance boundary, and who operates it at 3am (`references/data-services.md`).
- [ ] Check the quotas that bite at the target scale, not the headline capability — item and
      payload sizes, partition throughput, connection counts, per-region resource counts.
- [ ] Price the idle case as well as the peak: provisioned capacity, per-cluster-hour control
      planes and per-AZ endpoints charge whether or not traffic arrives.
- [ ] Check the exit: what a migration away looks like, and whether the choice locks in a
      proprietary API or keeps a portable one.
- [ ] **Gate — the decision is written down as a trade-off:** the record names the option
      chosen, the option rejected, the constraint that decided it, and the observation that
      would make the decision wrong (`references/well-architected.md`).

## Topic router

| Topic | Read when | File |
|---|---|---|
| Policy evaluation order, permissions boundaries and SCP/RCP, trust policies and confused deputy, `PassRole` and the other escalation paths, condition operators and their empty-set behaviour, STS session limits, Organizations, Access Analyzer and policy simulation | Writing or reviewing any policy, debugging an `AccessDenied`, or designing cross-account access | `references/iam.md` |
| Lambda quotas, concurrency and scaling, event source mappings, idempotency and partial batch failure; API Gateway REST vs HTTP vs WebSocket, timeouts, authorizers, throttling and the recurring 4xx/5xx causes; Step Functions Standard vs Express and JSONata; SQS and EventBridge wiring | Designing, reviewing or debugging anything serverless | `references/serverless.md` |
| CloudFormation, SAM and CDK selection; logical ids and replacement; change sets and validation layers; `describe-events` and the rollback states; drift, hotswap and Express mode; cross-stack exports; importing existing resources | Writing or reviewing a template or CDK app, or recovering a failed deployment | `references/deployment.md` |
| DynamoDB, Aurora and RDS, Aurora DSQL, ElastiCache, S3 storage classes, OpenSearch, Kinesis and MSK — what each is for, the quotas that decide, and the misuse that shows up later | Picking a data service, or explaining why the current one is struggling | `references/data-services.md` |
| VPC layout and subnets, NAT versus gateway and interface endpoints, cross-AZ charges, security groups versus NACLs, ALB/NLB selection, PrivateLink, Route 53 and certificate placement | Designing connectivity, or tracing a bill or a timeout back to the network | `references/networking.md` |
| Cost Explorer and CUR, the Price List API, Budgets and Cost Anomaly Detection, Compute Optimizer, Savings Plans versus Reserved Instances, and the per-service cost traps | Investigating a cost spike or building a reduction plan | `references/cost.md` |
| The six pillars turned into concrete trade-offs, the questions worth asking per pillar, multi-AZ versus multi-region, RTO/RPO choices, and how to record a decision | Running a design review, or justifying an architecture to someone who will inherit it | `references/well-architected.md` |
| EKS cluster creation and versions, standard versus extended support, node groups versus Karpenter versus Auto Mode, EKS Pod Identity versus IRSA, the VPC CNI and IP exhaustion, add-ons and upgrades; ECS and Fargate control-plane equivalents | Creating, upgrading or diagnosing a managed cluster — not the workloads on it | `references/eks-control-plane.md` |
| CloudWatch metrics, alarms and composite alarms, Logs groups and retention, Logs Insights query syntax, the quotas and the billing dimensions, and what belongs in the `observability` skill instead | Working with CloudWatch itself, or explaining a CloudWatch bill | `references/cloudwatch.md` |

## Output format

When reviewing a policy, a template or an architecture, group findings by file and lead each
with the location and the consequence, not the rule name:

```
infra/deployer-policy.json:18 - escalation - Sid PassAnyRole allows iam:PassRole on
  Resource "*" while Sid DeployCompute allows lambda:CreateFunction. Anyone holding this role
  can create a function with the account's admin role attached and read its credentials.
  Scope Resource to arn:aws:iam::111122223333:role/service/* and add
  Condition iam:PassedToService.
```

Order findings by blast radius: privilege escalation and data loss first, then availability,
then cost, then style. Quote the evidence — the policy `Sid`, the `ResourceStatusReason`, the
`cdk diff` line, the Cost Explorer figure produced by the script — rather than asserting it,
and give the corrected JSON or YAML for each fix.

Say explicitly when something is fine as written, and separate "this is wrong" from "this is
not how I would have done it". A `RestApi` where an `HttpApi` would also work is not a finding.

## Environment

- The AWS CLI v2 is the baseline tool. `aws sts get-caller-identity`, `aws configure list` and
  `aws configure list-profiles` are the first three commands of any diagnosis; the region can
  come from `AWS_REGION`, the profile, or a config file, and the one it actually used is worth
  confirming rather than assuming.
- Most read-only investigation runs fine with an IAM Identity Center session
  (`aws sso login --profile <p>`) and needs no long-lived keys. If a workflow appears to need
  an access key, that is usually a missing role, not a missing key.
- `cfn-lint` runs entirely offline and validates templates against the resource provider
  schemas, including the SAM transform. Verified against **cfn-lint 1.56.3**: it catches a
  misspelled property on a native resource (`E3002`) and an out-of-range
  `AWS::Lambda::Function` `Timeout` (`E3717`), but it does **not** flag the same out-of-range
  timeout on an `AWS::Serverless::Function`, nor a `MemorySize` above the 10,240 MB ceiling on
  either. Treat a clean run as "the schema is satisfied", not "the values are legal".
- `sam validate --lint` wraps cfn-lint and adds SAM-specific checks; `sam local invoke` and
  `sam local start-api` need a container runtime. `cdk synth` and `cdk diff` need no
  credentials once `cdk.context.json` is committed — that file is what keeps a synth
  deterministic, so it belongs in version control.
- `cfn-guard` evaluates policy-as-code rules against a template offline and is the right place
  for organisational rules (no public S3, encryption required) that cfn-lint does not know
  about.
- `aws iam simulate-custom-policy` and IAM Access Analyzer policy validation are read-only API
  calls: they need credentials but change nothing, which makes them safe to run inside a
  review.
