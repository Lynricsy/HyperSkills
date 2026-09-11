# Cost and quotas

Verified against: Google Cloud SDK 584.0.0 (`gcloud quotas`, `gcloud billing` help text);
pricing mechanics from cloud.google.com/billing and the per-product pricing pages.

## Contents

- [Quotas are three different things](#quotas-are-three-different-things)
- [Finding and raising a quota](#finding-and-raising-a-quota)
- [Quota as a blast-radius control](#quota-as-a-blast-radius-control)
- [Budgets do not cap spend](#budgets-do-not-cap-spend)
- [Where the numbers actually come from](#where-the-numbers-actually-come-from)
- [Attribution: labels, projects, tags](#attribution-labels-projects-tags)
- [Discounts](#discounts)
- [The five costs teams forget](#the-five-costs-teams-forget)
- [Working a cost investigation](#working-a-cost-investigation)

## Quotas are three different things

| Kind | Restricts | Example |
|---|---|---|
| **Allocation** | how much of a resource may exist at once | vCPUs per region, IP addresses, Cloud Run services per region |
| **Rate** | consumption over a time window | API requests per minute per project |
| **Concurrent** | operations running simultaneously | concurrent builds, concurrent job executions |

They fail differently. An allocation quota fails at create time with a clear message. A rate
quota fails at runtime with `429 RESOURCE_EXHAUSTED` under load only — which is why the first
encounter is usually in production during a spike, and why retry-with-backoff belongs in the
client regardless.

Most quotas are **per project per region**. Scaling out by adding regions multiplies the
headroom; scaling out inside one region does not.

Quotas are not limits. A **limit** (a system-level maximum, such as the size of a single
Pub/Sub message) cannot be raised at all; a quota can.

## Finding and raising a quota

```bash
gcloud quotas info list --service=compute.googleapis.com --project=PROJECT_ID \
  --format="table(quotaId, quotaDisplayName, dimensions, details.value)" --limit=50

gcloud quotas preferences create \
  --service=compute.googleapis.com --project=PROJECT_ID \
  --quota-id=CPUS-per-project-region --preferred-value=500 \
  --dimensions=region=us-central1 \
  --justification="Q4 launch capacity" --email=platform@example.com --quiet
```

An increase is a **request**, not a setting: small increases are often granted
automatically, large ones go to review and can take days. Request capacity before the launch,
not during it. A new project starts with low quotas across the board, so "it works in staging"
where the project is older is not evidence.

## Quota as a blast-radius control

`gcloud quotas preferences create` also *lowers* quotas, and that is an underused safety
mechanism. A runaway loop creating VMs, a misconfigured autoscaler, or a compromised service
account is bounded by the quota, not by the budget — because the budget does not stop
anything. Deliberately low quotas in development projects convert an unbounded bill into a
failed API call.

`--allow-quota-decrease-below-usage` exists precisely because lowering below current usage is
dangerous; requiring the flag is the guard.

## Budgets do not cap spend

A Cloud Billing budget with alert thresholds **does not automatically cap usage or
spending**. It sends notifications. Google Cloud keeps serving and keeps charging past 100%.

```bash
gcloud billing budgets create --billing-account=BILLING_ACCOUNT_ID \
  --display-name="prod monthly" --budget-amount=5000USD \
  --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0 --threshold-rule=percent=1.2,basis=forecasted-spend \
  --filter-projects=projects/PROJECT_NUMBER --quiet
```

Set thresholds on **forecasted** spend as well as actual — a forecast crossing 120% on day 8
is actionable; an actual crossing 100% on day 29 is a postmortem.

A budget can publish to Pub/Sub, and it is technically possible to wire that to a function
that detaches the billing account. That stops every billable service in the project
immediately, including the database. It is a legitimate control for a sandbox and a
self-inflicted outage anywhere else; the safer automated response is to lower quotas or scale
a specific service to zero.

## Where the numbers actually come from

The console's billing reports are for browsing. Anything analytical needs the **BigQuery
billing export**, which has three flavours:

| Export | Grain | Use |
|---|---|---|
| Standard usage cost | service, SKU, project, label, day | most reporting |
| Detailed usage cost | adds resource-level rows (individual VM, bucket) | "which instance is this" |
| Pricing | the price list itself | modelling a change before making it |

Two properties decide how you plan: the export is **not retroactive** — it starts producing
rows when you enable it, and there is no way to backfill — and it lands with a delay measured
in hours, so it is a reporting tool, not a real-time alarm. Enable both standard and detailed
export on day one of any project that will ever have a cost question.

Credits (free tier, committed-use, promotional) appear as separate negative rows; summing
`cost` without `credits.amount` overstates the bill and produces reports nobody can reconcile
against the invoice.

## Attribution: labels, projects, tags

Cost attribution is only as good as the dimension you can group by:

1. **Project** — the strongest boundary, always present, and it is why one project per
   application per environment pays for itself the first time someone asks what a service
   costs.
2. **Labels** — propagate to the billing export, but only on resources that support them and
   only if they were set. A label added today does not relabel yesterday's rows. Enforce them
   at creation (org policy on some resources, CI checks otherwise) rather than auditing later.
3. **Tags** — inherited down the hierarchy and governed by IAM, so they are the reliable
   choice for the one or two dimensions that must never be wrong (`environment`,
   `cost-center`).

Unlabelled resources show up as a single large "unattributed" bucket, and reconciling it after
the fact is manual work proportional to the number of resources.

## Discounts

| Mechanism | Applies to | Commitment |
|---|---|---|
| **Sustained use discounts (SUD)** | Compute Engine, automatic | none — up to **30%** off for instances running the whole month, on self-serve billing accounts only |
| **Resource-based CUD** | Compute vCPU and memory, per region | 1 or 3 years, billed whether or not used |
| **Spend-based CUD** | Cloud Run, Cloud SQL, GKE Autopilot, and others — a dollar-per-hour commitment | 1 or 3 years |
| **Spot VMs** | preemptible capacity | none; reclaimed with ~30 seconds' notice |

Right-size **before** committing. A three-year CUD on an over-provisioned fleet locks in the
over-provisioning for three years, and the commitment is charged whether the capacity is used
or not. The order is: delete idle → right-size → commit → then negotiate.

`gcloud recommender recommendations list --recommender=google.compute.instance.MachineTypeRecommender`
and the idle-resource recommenders (unattached persistent disks, idle VMs, idle Cloud SQL
instances, unused IP addresses) are where the first pass of waste lives.

## The five costs teams forget

1. **Network egress.** Internet egress, cross-region traffic, and cross-zone traffic inside a
   region all cost money; ingress does not. A multi-region bucket read from a single-region
   workload pays on every read. Co-location is usually the biggest single saving available.
2. **Idle provisioned capacity.** Cloud SQL and Compute Engine bill for existence, not use. A
   stopped Compute Engine instance still bills for its persistent disk and any static IP.
3. **Observability.** Log ingestion at $0.50/GiB beyond 50 GiB per project per month, and
   custom metrics per sample. Debug logging left on in production is a line item.
4. **Storage tails.** Soft-deleted objects, noncurrent versions, orphaned multipart upload
   parts, old snapshots and unattached disks — none appear in an object listing.
5. **Per-cluster and per-endpoint fees.** GKE charges $0.10 per cluster per hour regardless of
   size; ten small clusters cost $720/month before any workload runs. The same shape applies
   to load balancer forwarding rules, Cloud NAT gateways and VPN tunnels.

## Working a cost investigation

Inform, then optimise, then operate — in that order, because acting before you can attribute
means you cannot prove the saving.

1. **Inform.** Query the BigQuery export grouped by `service.description` and `sku.description`
   for the period, then diff against the previous period. Rank by *delta*, not by absolute
   size: the biggest line is usually expected, the biggest change is not.
2. **Attribute.** Take the top delta and group by project, then by label, then by resource
   using the detailed export. Stop when one team owns the answer.
3. **Optimise.** Delete idle resources, right-size, fix the storage class or region, and only
   then consider commitments. Recommender output is a candidate list, not a patch — a resource
   used once per quarter looks idle in a 90-day window.
4. **Operate.** Put a budget with forecast thresholds on the project, a quota ceiling on the
   resource that ran away, and the label requirement into the deployment path so the next
   investigation starts from attribution rather than archaeology.

<!-- sources: gcp-docs, google-skills, optimnow-finops -->
