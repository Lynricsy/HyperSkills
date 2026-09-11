# Cost analysis and reduction

Verified against: the AWS Cost Management, Compute Optimizer and Savings Plans user guides on
docs.aws.amazon.com. Prices change and vary by region; this file gives the *dimensions* and
the traps, not a price list — look up current prices with the Price List API or the pricing
calculator.

## Contents

- [Before any number is quoted](#before-any-number-is-quoted)
- [Cost Explorer](#cost-explorer)
- [CUR and Athena](#cur-and-athena)
- [Budgets and anomaly detection](#budgets-and-anomaly-detection)
- [Compute Optimizer](#compute-optimizer)
- [Savings Plans versus Reserved Instances](#savings-plans-versus-reserved-instances)
- [The per-service traps](#the-per-service-traps)
- [The order of operations](#the-order-of-operations)
- [Attribution: tags and allocation](#attribution-tags-and-allocation)

## Before any number is quoted

Two failures make cost analysis worse than useless, because the output looks authoritative:

- **Doing the arithmetic in prose.** Sums, percentages and month-over-month deltas computed
  by reasoning are unreliable. Write a script, run it, and quote its output. Keep the script
  as the artefact so someone can re-run it next month.
- **Analysing the wrong window.** Establish today's date from the system rather than
  assuming, and remember that Cost Explorer's `--time-period` **end date is exclusive**.
  `Start=2026-08-01,End=2026-08-31` returns 30 days and silently omits 31 August. For a full
  month, the end is the first of the next month. `[official]`

## Cost Explorer

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-08-01,End=2026-09-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

- `UnblendedCost` is the default to reason with. `AmortizedCost` spreads upfront commitment
  payments and is the right metric when comparing months where a Savings Plan was purchased.
- Exclude credits and refunds when measuring real consumption:
  `--filter '{"Not":{"Dimensions":{"Key":"RECORD_TYPE","Values":["Credit","Refund"]}}}'`.
  The dimension key is `RECORD_TYPE`, not `CHARGE_TYPE` — the wrong key returns
  `ValidationException`.
- When `--group-by` is used, the `Total` field comes back empty by design. Sum the groups in
  the script, or make a second ungrouped call.
- An empty result from a filter almost always means the filter value does not match exactly.
  Call `ce get-dimension-values` first to get the valid strings; service names in Cost
  Explorer differ from the service codes in the Price List API.
- Hourly granularity and resource-level data must be enabled in Cost Explorer preferences
  first; until then those calls return `AccessDeniedException`, which reads like a permission
  problem and is not.
- `ce get-cost-comparison-drivers` answers "what changed between these two months" directly
  and is usually faster than diffing two grouped queries by hand.

## CUR and Athena

The Cost and Usage Report (CUR 2.0) is the line-item truth: one row per resource per hour
with every tag and every discount applied. Use it when Cost Explorer's dimensions are too
coarse — per-resource attribution, per-tenant chargeback, or "which exact NAT gateway".

Set it up before you need it: CUR starts accumulating from the day it is configured and
cannot be backfilled. Query it through Athena, and partition by billing period or the scans
get expensive enough to appear in next month's bill.

## Budgets and anomaly detection

- AWS Budgets is a **global** service whose API answers in `us-east-1`. Calls from another
  region fail; set `--region us-east-1`. `[official]`
- A budget alert at 100% of the expected spend is a post-mortem. Set thresholds on *forecast*
  as well as actual, so the alert arrives while there is still a month to act in.
- Cost Anomaly Detection is the complement: it learns the pattern per service or per account
  and alerts on deviation, which catches the class of spike no static threshold anticipates.
- Both are free to run. An account with neither has no cost feedback loop at all, and that is
  a finding in its own right.

## Compute Optimizer

Right-sizing without measurement is guessing. Compute Optimizer analyses CloudWatch history
for EC2, EBS, Lambda, ECS on Fargate and RDS, and returns recommendations with a performance
risk rating.

- It must be opted in: `aws compute-optimizer update-enrollment-status --status Active`.
  Until then every call returns "account not registered". `[official]`
- It needs history. A freshly enrolled account has no recommendations, and a recently changed
  workload has misleading ones.
- Enhanced infrastructure metrics (memory utilisation) require the CloudWatch agent on EC2.
  Without it, recommendations are CPU- and network-based only, which under-sizes
  memory-bound workloads.
- Take the performance risk rating seriously: a "very low risk" downsize is safe to batch, a
  "medium" one needs a load test.

## Savings Plans versus Reserved Instances

| | Compute Savings Plan | EC2 Instance Savings Plan | Reserved Instance |
|---|---|---|---|
| Flexibility | any region, family, size, OS, tenancy; covers EC2, Fargate and Lambda | one family in one region | one family, often one region/AZ |
| Discount | lowest of the three | higher | highest for Standard RIs |
| Resale | no | no | Standard RIs can be sold on the marketplace |

Default to Compute Savings Plans. The extra few percent from an instance-family commitment is
rarely worth losing the freedom to move a workload to Graviton, to Fargate, or to a different
family.

Three rules that prevent expensive mistakes:

1. Commit to the **floor** of usage after right-sizing, not to current usage. A commitment
   bought over an over-provisioned fleet locks the waste in for one or three years.
2. Buy in layers — several smaller commitments with staggered end dates — rather than one
   large one, so the renewal decision is never all-or-nothing.
3. Check existing coverage and utilisation first (`ce get-savings-plans-coverage`,
   `get-savings-plans-utilisation`). Unused commitment is a pure loss and is common after a
   migration.

Note that `--billing-view-arn` is accepted by `get-cost-and-usage`, `get-cost-forecast`,
`get-dimension-values` and budget creation, but **not** by the Savings Plans and reservation
coverage/utilisation calls; passing it there returns `ValidationException`. `[official]`

## The per-service traps

| Line item | What is actually being billed | Usual fix |
|---|---|---|
| NAT gateway | hourly per gateway (one per AZ) plus per-GB processing | gateway endpoints for S3/DynamoDB (free), interface endpoints for the rest |
| Data transfer | cross-AZ in both directions; egress to internet | zone affinity; CloudFront in front of public origins |
| CloudWatch | per distinct custom metric per month; log ingestion per GB; log storage forever by default | cut dimension cardinality, use the embedded metric format, set retention |
| EBS | provisioned size, not used size; unattached volumes; snapshots after the volume is gone | delete unattached volumes, gp2 → gp3, lifecycle the snapshots |
| Lambda | GB-seconds; arm64 is materially cheaper than x86_64 for the same work | switch architecture, right-size memory against measured duration |
| S3 | storage class minimum durations; requests; versioned noncurrent objects | lifecycle rules, Intelligent-Tiering, expire noncurrent versions |
| EKS | per cluster-hour for the control plane regardless of workload, plus extended-support surcharge | consolidate clusters; stay inside standard support |
| RDS/Aurora | provisioned instances bill while idle; snapshots persist after deletion | schedule non-production shutdown, Serverless v2 for spiky workloads |
| Elastic IPs and idle load balancers | hourly while unattached or unused | delete them |

Two of these are pure arithmetic with no capacity risk and are the easiest wins in any
account: moving Lambda functions to `arm64`, and migrating gp2 volumes to gp3.

## The order of operations

Sequence by reversibility, not by size of the line item:

1. **Delete waste.** Unattached volumes, unassociated Elastic IPs, idle load balancers, empty
   clusters, orphaned snapshots, stopped-but-provisioned resources. Zero availability risk.
2. **Fix the architectural line items.** NAT and endpoints, cross-AZ topology, CloudWatch
   cardinality and retention, S3 lifecycle. These are permanent and usually larger than
   instance sizing.
3. **Schedule non-production.** Development and staging that run 168 hours a week to serve
   40 is a 76% saving on those resources with one scheduler.
4. **Right-size on evidence.** Compute Optimizer, with its risk rating, after it has history.
5. **Commit.** Savings Plans sized to the post-right-sizing floor.
6. **Install the feedback loop.** Budgets with forecast alerts plus Cost Anomaly Detection,
   so the next regression is caught by an alarm rather than by finance.

Each recommendation in the final plan should name its monthly saving (from the script), its
blast radius, and how to reverse it. A plan without the last two columns will not be approved
by anyone accountable for availability.

## Attribution: tags and allocation

- A tag only appears in Cost Explorer and CUR after it is activated as a **cost allocation
  tag** in the billing console, and activation is not retroactive. An account that starts
  tagging today can attribute costs from today.
- Tags do not propagate to every child resource. An EBS volume created by an Auto Scaling
  group, a snapshot of a tagged volume, and objects in a tagged bucket may all be untagged.
- Untaggable spend — data transfer, some support charges — never attributes to a team. Decide
  the split rule before the chargeback conversation rather than during it.
- Enforce tags at creation with an SCP or a CloudFormation Hook; a tagging policy without
  enforcement decays within a quarter.

<!-- sources: aws-agent-toolkit, awesome-copilot-aws, aws-docs, zxkane-aws -->
