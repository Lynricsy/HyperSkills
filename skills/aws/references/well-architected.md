# Well-Architected, as trade-offs rather than a checklist

Verified against: the AWS Well-Architected Framework and its pillar documents on
docs.aws.amazon.com. The point of this file is not to reproduce the questionnaire — that is
freely available and reading it aloud helps nobody. It is to name the decisions each pillar
actually forces, and the answers that show up as incidents when they are skipped.

## Contents

- [How to run a review that produces decisions](#how-to-run-a-review-that-produces-decisions)
- [Operational excellence](#operational-excellence)
- [Security](#security)
- [Reliability](#reliability)
- [Performance efficiency](#performance-efficiency)
- [Cost optimisation](#cost-optimisation)
- [Sustainability](#sustainability)
- [The trade-offs that cut across pillars](#the-trade-offs-that-cut-across-pillars)
- [Recording a decision](#recording-a-decision)

## How to run a review that produces decisions

1. **Establish what the workload is for.** Its availability target, its data classification,
   its cost ceiling and its team size. Every pillar answer depends on these, and a review
   without them produces generic advice.
2. **Read the infrastructure as code, not the console.** The template is what will exist
   after the next deployment; the console is what exists now. Where they differ, that gap is
   itself a finding.
3. **Score by consequence, not by count.** Six style findings and one missing backup is one
   finding. Rank by what happens when it fails: data loss, then availability, then cost, then
   operability.
4. **Turn each finding into a decision with an owner.** "Enable PITR" is a task; "we accept a
   24-hour RPO on the staging table and 5 minutes on production" is a decision. The second
   survives the review; the first does not.
5. **Name the observation that would change the answer.** A trade-off without a trigger is a
   guess that will never be revisited.

## Operational excellence

The questions that matter:

- Can the whole environment be recreated from source? If any resource was made by hand, the
  disaster-recovery plan is fiction.
- Is there one deployment path, and does it include a rollback that has been executed at
  least once?
- Are changes small and frequent, or large and rare? Large-and-rare correlates with long
  outages, because nobody can tell which change broke it.
- Does every alarm have a documented response, and does every response have an owner? An
  alarm nobody acts on trains the team to ignore alarms.
- Is the tagging consistent enough to answer "who owns this and what environment is it"?
  Without it, incident response starts with an archaeology exercise.

Concrete failures to look for: infrastructure in the console, manual deployment steps, no
CloudTrail (or CloudTrail without an organisation trail), no runbooks, alarms on CPU but not
on the business signal, and log groups with no retention.

## Security

The questions that matter:

- Is every human identity federated with MFA, and are there any long-lived access keys? An
  IAM user with a static key in a CI system is the most common root cause of a real breach.
- Does anything run with `*FullAccess` or a wildcard resource? And separately: does anything
  hold `iam:PassRole` on `*` next to a compute create action? That pair is administrator
  access in disguise, whatever the policy's name says.
- Where do secrets live, and who can read them? Environment variables and plain
  CloudFormation parameters both fail this.
- Is data encrypted at rest and in transit, and is TLS *enforced* rather than merely
  available? A bucket with default encryption and no `aws:SecureTransport` deny still accepts
  plaintext requests.
- Is anything reachable from the internet that does not need to be? Security groups with
  `0.0.0.0/0`, public buckets, public RDS endpoints, and public API Gateway stages that were
  meant to be private.
- Is there a detective layer — GuardDuty, Security Hub, Config, Access Analyzer external
  findings — or only preventative controls?

The pillar's own framing is useful here: preventative controls (SCPs, IAM, policy-as-code in
the pipeline) stop the mistake, detective controls (Config, GuardDuty, Access Analyzer) find
what got through, and responsive controls (automation, runbooks) shorten the exposure. Most
reviews find preventative controls and nothing else.

## Reliability

The questions that matter:

- What is the stated RTO and RPO, and what evidence exists that they are met? A backup that
  has never been restored is a hypothesis.
- Is every tier multi-AZ, including the ones people forget — NAT gateways, single-AZ RDS,
  self-managed brokers, a Redis node with no replica?
- What happens when a dependency is slow rather than down? Timeouts, retries with jitter,
  circuit breakers and bulkheads are the difference between one degraded service and a
  cascade.
- Where are the queues and dead-letter queues, and does anyone look at the DLQs?
- Which quotas will be hit first at 10x traffic — account concurrency, API throttle, ENIs per
  VPC, table throughput — and is there an alarm on approaching them?
- Is there a single-writer or single-region component that the availability target does not
  actually allow?

Multi-AZ is the default and is cheap. Multi-region is expensive, changes the data model
(conflict resolution, replication lag), and should be a deliberate answer to a stated RTO
that multi-AZ cannot meet — not an aspiration.

## Performance efficiency

The questions that matter:

- Is the instance or memory size a measurement or a guess? Lambda memory in particular is a
  CPU dial: 1,769 MB is one vCPU, so halving memory below it more than halves throughput.
- Is the architecture right for the load *shape*? Steady load rewards provisioned capacity
  and commitments; spiky load rewards serverless and on-demand; unpredictable load rewards
  scale-to-zero.
- Is caching where the latency actually is — CloudFront for static and cacheable responses,
  DAX or ElastiCache for repeated reads, API Gateway cache for expensive idempotent GETs?
- Is Graviton (arm64) in use? For most managed services it is the same or better performance
  at lower cost, which makes not using it a decision that needs a reason.
- Are reads separated from writes where the ratio justifies it (Aurora readers, DynamoDB
  eventually-consistent reads at half the cost)?

Measure before and after. A performance change without a before number is a story.

## Cost optimisation

The pillar-level questions, with the mechanics covered separately:

- Does anyone see the bill weekly, and is there a budget with a forecast alert?
- Can spend be attributed to a team or a product? If cost allocation tags were never
  activated, the answer is no and cannot be made retroactive.
- Are non-production environments running 168 hours a week to serve 40?
- Are commitments sized to the floor of usage after right-sizing, or to whatever was running
  when someone bought them?
- Is there an owner for the architectural line items — NAT, cross-AZ, CloudWatch cardinality
  — or only for instance sizes?

## Sustainability

In practice this pillar overlaps heavily with cost, and the overlap is the useful part:
deleting idle resources, right-sizing, moving to Graviton, choosing managed services with
higher utilisation, and lifecycle-ing cold data all reduce both the bill and the footprint.
The distinct questions are about placement (a region with a lower carbon intensity), about
data retention policy rather than storage class, and about whether batch work can be moved to
a time or place with cleaner supply.

Do not let it become a separate workstream. Where a sustainability finding does not also
reduce cost or risk, it will not get prioritised, and pretending otherwise wastes the review.

## The trade-offs that cut across pillars

| Trade-off | What you gain | What you pay | Choose the expensive side when |
|---|---|---|---|
| Multi-region active-active | survives a regional failure | conflict resolution, replication lag, roughly double the infrastructure, much harder testing | the RTO is minutes and the business genuinely stops without it |
| Provisioned concurrency / provisioned capacity | predictable latency | pay while idle | the latency is on a user-facing synchronous path with a tight SLO |
| Managed service over self-hosted | operational load disappears | less control, a proprietary API, higher unit price | the team is small or the component is not a differentiator |
| Strong consistency | simpler application code | throughput and latency cost | correctness depends on read-after-write and the code cannot compensate |
| Microservices | independent deploy and scale | network failure modes, distributed tracing, more infrastructure | teams genuinely need to deploy independently |
| Tight IAM scoping | small blast radius | more policies to maintain, more friction | the credential can reach production data |
| Long log and metric retention | better forensics | storage cost that compounds | a compliance requirement names the period |

A review that reports only the cheap side of each row has not reviewed anything.

## Recording a decision

Write it where the next engineer will find it — an ADR in the repository, not a slide:

```
Decision: single-region, multi-AZ, Aurora PostgreSQL with a 5-minute RPO.
Rejected: multi-region active-active with DSQL.
Constraint that decided it: the stated RTO is 4 hours; multi-AZ failover meets it,
  and the team of four cannot operate conflict resolution.
Cost of being wrong: a regional outage exceeds the RTO. Accepted.
Revisit when: the RTO tightens below 30 minutes, or the team exceeds ten engineers.
```

Four lines and a trigger beat a forty-page assessment nobody reads.

<!-- sources: aws-wa-samples, awesome-copilot-aws, aws-docs -->
