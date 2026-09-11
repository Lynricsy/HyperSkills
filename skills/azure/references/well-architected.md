# Well-Architected review

Verified against: the Azure Well-Architected Framework pillars and the reliability and SLA
documentation as published by Microsoft. Claims are `[official]`.

A Well-Architected review is only useful if it produces findings someone can act on. A review
that returns "consider enabling monitoring" for every workload is a template, not a review. Each
finding needs the evidence that produced it, the consequence if it is left alone, and the
smallest change that removes it.

## Contents

- [The five pillars as questions](#the-five-pillars-as-questions)
- [Reliability](#reliability)
- [Composite SLA arithmetic](#composite-sla-arithmetic)
- [Security](#security)
- [Cost optimisation](#cost-optimisation)
- [Operational excellence](#operational-excellence)
- [Performance efficiency](#performance-efficiency)
- [Running the review](#running-the-review)
- [Reporting](#reporting)

## The five pillars as questions

| Pillar | The question that produces findings |
|---|---|
| Reliability | What single failure takes this down, and how long until it is back? |
| Security | What credential exists that should not, and what could this identity reach if it were stolen? |
| Cost optimisation | What is running that nobody would provision today? |
| Operational excellence | What is done by hand that would have to be done again under pressure? |
| Performance efficiency | What scales, what does not, and which one hits its ceiling first? |

## Reliability

- **Availability zones.** Zone redundancy is create-time for most services (Container Apps
  environment, AKS node pool, Premium v3 App Service plan, zone-redundant storage, zone-redundant
  databases). Retrofitting means recreating the resource. Check each tier of the stack
  separately: a zone-redundant front end over a single-zone database is a single-zone system.
- **Redundancy is not failover.** Geo-replicated storage (GRS) does not fail over automatically
  and the secondary is not readable unless you chose RA-GRS. An Azure SQL failover group does
  fail over, but only if the application resolves the listener endpoint rather than the primary's
  name.
- **Tested recovery.** A backup that has never been restored is an assumption. Ask for the date
  of the last restore test and the measured RTO, not the configured retention.
- **Health probes and graceful shutdown** decide whether a deployment is visible to users;
  those live in the workload configuration and belong to the `containers` skill for
  Kubernetes-hosted services.
- **Regional outage.** Most workloads correctly choose not to be multi-region. That is a decision
  to write down with its RTO, not a gap to flag - the finding is the absence of the decision.

## Composite SLA arithmetic

A synchronous chain's availability is the product of its parts, so adding a component always
lowers it:

```
App Service (99.95%) x Azure SQL (99.99%) x Key Vault (99.99%)
  = 0.9995 x 0.9999 x 0.9999 = 99.93%   -> about 6 hours of allowed downtime per year
```

Two consequences worth stating in a review:

- Adding a hard dependency - a synchronous Key Vault lookup on the hot path, an extra service in
  the chain - costs availability even though each piece is highly available. Cache it, or make
  the dependency non-fatal.
- Parallel redundancy multiplies the *failure* probabilities instead:
  two independent 99.9% instances give `1 - 0.001^2 = 99.9999%`, but only if they genuinely fail
  independently. Two instances in one zone do not.

Composite SLA is also the honest answer to "can we promise four nines?" - compute it before
promising.

## Security

- **Every credential is a finding.** Connection strings, account keys, client secrets, ACR admin
  users, SAS tokens with long expiry. The replacement is a managed identity plus a data-plane
  role assignment.
- **Every standing privileged assignment is a finding.** Owner or User Access Administrator
  active (not PIM-eligible) at subscription scope, for a human or a CI principal.
- **Public data plane.** `publicNetworkAccess: Enabled` on a resource that only serves internal
  traffic, `allowBlobPublicAccess: true`, a database firewall rule of `0.0.0.0`, an NSG rule with
  source `Internet` on a management port.
- **Transport.** `minTlsVersion` below 1.2, `ftpsState: AllAllowed`, `supportsHttpsTrafficOnly`
  false.
- **Key management.** Key Vault without soft delete and purge protection; secrets with no
  expiry; no rotation and no alert on expiry. An expiring client secret is an unscheduled outage.
- **Defender for Cloud** secure score is a cheap external opinion on the same subscription. Read
  it before writing the security section - it sees configuration you would have to enumerate by
  hand.

## Cost optimisation

Findings, not observations. "Costs are high" is not a finding; "these three disks have
`managedBy == ''` and have been unattached since March" is. Every waste shape worth reporting is
reachable as a Resource Graph query, so run the query rather than eyeballing the portal.

The structural questions:

- Is non-production running outside working hours?
- Is the baseline covered by a reservation or savings plan, and is the coverage percentage known?
- Are the per-hour platform resources (Application Gateway, Firewall, API Management, private
  endpoints) attributable to a workload, or are they shared overhead nobody owns?
- Is Log Analytics ingestion proportionate to what is actually queried?

## Operational excellence

- Is everything in IaC, and does a `what-if` against production return an empty diff? A drifted
  template is a template nobody trusts, so nobody uses it in an incident.
- Is the deployment reversible? Slots, revisions with traffic splitting, or a documented rollback.
- Are diagnostic settings enabled, and enforced by policy rather than by memory? Resource logs
  are off by default.
- Is there an alert on the things that would page someone, and does it reach a human? This is the
  boundary: whether the alert exists and is wired to an action group is an Azure configuration
  question; how to define the SLO behind it and route it to on-call is the `observability`
  skill's.
- Are secrets rotated on a schedule, and does anything alert before expiry?

## Performance efficiency

- Which resource hits a ceiling first - a quota, a plan's instance limit, a database DTU/vCore
  cap, a connection limit? Name it with the number, taken from the quota or the tier's documented
  limit rather than estimated.
- Is scaling reactive (autoscale rules, KEDA) or manual? Manual scaling is a reliability finding
  as much as a performance one.
- Is data close to compute? Cross-region calls on the hot path are latency and egress cost at the
  same time.
- Is the tier appropriate, or was it chosen once and never revisited? Standard-tier storage
  behind a latency-sensitive workload, or a Premium plan for a service that idles, are the same
  mistake in opposite directions.

## Running the review

- [ ] Establish scope: which subscription, which resource groups, which workload. A review of
      "everything" produces nothing.
- [ ] Collect evidence before forming opinions - `az resource list`, Resource Graph inventory,
      the IaC that produced it, the Advisor and Defender recommendations.
- [ ] Work pillar by pillar, writing each finding with the evidence line that supports it.
- [ ] Rank by consequence, not by pillar. A public storage account outranks a missing tag, and a
      single-zone database outranks an oversized SKU.
- [ ] Separate what you verified from what you inferred. An export is a snapshot of what was
      exported; say so when the sample is partial.
- [ ] Present findings and ask which to act on before changing anything.

## Reporting

```
Scope: <subscription> / <resource groups> / <workload>
Evidence: <what was collected, and what was not available>

Critical
  - <resource id> - <what is true> - <what happens if unchanged> - <smallest fix>
High
  - ...
Medium
  - ...

Not findings
  - <thing that looks wrong and is fine, with the reason>

Gaps
  - <what could not be checked, and what access would be needed>
```

The "Not findings" section earns its place: it is what stops the same three false positives being
raised at every review. The "Gaps" section is what stops a partial review being read as a clean
bill of health.

<!-- sources: awesome-copilot, sre-agent-skills, microsoft-azure-skills, azure-docs -->
