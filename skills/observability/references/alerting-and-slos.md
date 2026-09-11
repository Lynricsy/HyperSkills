# Alerting and SLOs

The burn-rate multipliers and window pairs below follow the canonical multi-window multi-burn-rate
formulation; they are marked `[official]` and were checked against it rather than measured here.

## Contents

- [RED and USE](#red-and-use)
- [Symptom, not cause](#symptom-not-cause)
- [Ratios, not counts](#ratios-not-counts)
- [Anatomy of an SLO](#anatomy-of-an-slo)
- [Choosing the number of nines](#choosing-the-number-of-nines)
- [Writing an SLI that is not a lie](#writing-an-sli-that-is-not-a-lie)
- [Error budgets](#error-budgets)
- [Burn-rate alerting](#burn-rate-alerting)
- [Two severities](#two-severities)
- [Runbooks](#runbooks)
- [Recording rules for alert expressions](#recording-rules-for-alert-expressions)
- [Auditing an alert set](#auditing-an-alert-set)

## RED and USE

Two checklists that between them cover most of what a service needs:

- **RED**, for anything request-driven — every endpoint and every outbound dependency:
  **R**ate (requests per second), **E**rrors (failure ratio), **D**uration (a latency histogram,
  never an average).
- **USE**, for anything resource-like — pools, queues, hosts, disks:
  **U**tilisation, **S**aturation, **E**rrors.

RED is what alerts fire on, because it is expressed in what a user experiences. USE is what the
dashboard beside the alert explains it with. Reversing that — alerting on USE and dashboarding RED
— is the single most common cause of a useless pager.

RED on outbound dependencies is the part most often skipped, and it is what distinguishes "our
service is failing" from "the payment provider is failing and we are reporting it faithfully".

## Symptom, not cause

| Symptom — page-worthy | Cause — dashboard, not a page |
|---|---|
| Error ratio above the burn-rate threshold | CPU at 85% |
| p99 latency past the objective | A pod restarted |
| Queue age beyond its deadline | Disk 70% full |
| A critical user journey failing a synthetic check | Memory above a fixed number of bytes |

Cause alerts fail in both directions. They fire when nothing is wrong — a pod restart during a
rollout, CPU high because the service is doing work — and they stay silent for every failure mode
nobody anticipated. A symptom alert fires exactly when users are hurt, whatever the cause, and
that includes the causes not yet imagined.

The practical test for an existing alert: if the response is "acknowledge, it self-heals", it is
not an alert. Delete it or move it to a dashboard.

## Ratios, not counts

`increase(errors[5m]) > 100` is wrong in both directions. It fires on a busy afternoon when the
error *ratio* is unchanged, and it stays quiet during a traffic collapse when almost every
remaining request is failing. Express the condition as a ratio of bad events to total events, and
let the threshold come from the SLO rather than from a guess.

The same applies to latency: an absolute millisecond threshold with no baseline is a number
someone picked, and it will be wrong after the next traffic pattern change. Derive it from the
objective.

## Anatomy of an SLO

Four parts, all required:

| Part | Example |
|---|---|
| The thing measured | Checkout POST requests |
| The success criterion | Returns a non-5xx status within 800 ms |
| The target | 99.9% of them |
| The compliance window | Rolling 30 days |

An SLO missing the window is a slogan. An SLO whose criterion is "not 5xx" credits timeouts,
connection failures and 4xx storms as successes — which is why the criterion has to be written
positively (what counts as *good*) rather than as the absence of one failure mode.

Pick three to five SLOs per service, tied to user-visible behaviour, measured automatically, and
reviewed at least quarterly. Internal metrics — cache hit ratio, queue depth — are not SLOs; they
are the things you look at when an SLO is at risk.

## Choosing the number of nines

Each nine costs roughly an order of magnitude more than the last:

| Target | Allowed failure per 30-day month |
|---|---|
| 99% | ~7 h 18 m |
| 99.9% | ~43 m 12 s |
| 99.95% | ~21 m 36 s |
| 99.99% | ~4 m 19 s |
| 99.999% | ~26 s |

Read that table against your actual operations before choosing. At 99.99% a single rolling deploy
that drops requests for three minutes consumes most of the month's budget; at 99.999% a DNS TTL
is a meaningful fraction of it. A target the organisation cannot meet is worse than a lower one it
can, because a permanently exhausted budget carries no information and its alerts get ignored.

Do not aim for 100%. A 100% target means no error budget, which means no basis for shipping
anything.

## Writing an SLI that is not a lie

Two recurring defects:

**"Not 5xx" as the success criterion.** It counts as good: a request that timed out with no status
at all, a 400 returned because the service corrupted its own request to a dependency, and every
4xx storm caused by a broken client release. Define good explicitly — the status codes and the
latency bound that constitute a successful request.

**A quantile of an average as the latency SLI.** `avg(rate(x_sum[5m]) / rate(x_count[5m]))` is an
average, whatever it is labelled. Averaging it further, or calling it p95, does not make it one.
An average hides precisely the tail the objective exists to protect.

The sound latency SLI is a good-event ratio: the fraction of requests that completed under the
threshold, computed from histogram buckets. The threshold then appears in the SLI definition,
where it can be reviewed, rather than inside an alert expression where it cannot.

```promql
# Good-event ratio for a 800ms threshold, from histogram buckets.
sum(rate(http_server_request_duration_seconds_bucket{le="0.8",job="checkout"}[5m]))
/
sum(rate(http_server_request_duration_seconds_count{job="checkout"}[5m]))
```

Note the unit: the stable convention metric is in **seconds**, so a threshold carried over from a
millisecond-based predecessor is wrong by a factor of 1000. Any SLI migration that touches a
duration metric must re-derive its thresholds rather than port them.

## Error budgets

The budget is the inverse of the objective: at 99.9% over 30 days, 0.1% of requests may fail. Its
value is the feedback loop it creates between reliability and velocity, and that loop only exists
if the policy has a consequence:

| Budget state | Policy |
|---|---|
| Healthy | Ship aggressively |
| Roughly half spent | Slow down; prioritise reliability work |
| Exhausted | Freeze risky changes until reliability recovers |

"Discuss it in the weekly meeting" is not a policy. Write down what stops, who can override it,
and what has to be true to resume — otherwise the budget is a chart nobody acts on.

## Burn-rate alerting

Burn rate is how fast the budget is being consumed relative to the rate that would exactly exhaust
it over the compliance window. A burn rate of 1 spends the budget precisely by the end of the
window; a burn rate of 14.4 spends it in about two days.

The reason to alert on burn rate rather than on the SLO itself: **an alert whose window equals the
compliance window cannot page in time.** A condition evaluated over 30 days only becomes true once
the budget is already gone, and then stays true for weeks — late and then latched.

The canonical multi-window multi-burn-rate configuration:

| Burn rate | Long window | Short window | Budget consumed before firing | Severity |
|---|---|---|---|---|
| 14.4× | 1 hour | 5 minutes | ~2% | Page |
| 6× | 6 hours | 30 minutes | ~5% | Page |
| 3× | 1 day | 2 hours | ~10% | Ticket |
| 1× | 3 days | 6 hours | ~10% | Ticket |

Two windows per rule, not one, and both must be firing:

- The **long** window is the detection window. It sets how much budget is consumed before the
  alert fires, and it filters out brief spikes.
- The **short** window is the confirmation window, conventionally one twelfth of the long one. It
  exists so the alert **resolves promptly** once the burn stops. Without it, a rule with a 6-hour
  window stays firing for six hours after the incident ends, which is how a rotation learns to
  ignore it.

```promql
# 14.4x fast burn against a 99.9% objective: both windows must exceed the threshold.
(
  checkout:error_ratio:rate1h  > (14.4 * 0.001)
  and
  checkout:error_ratio:rate5m  > (14.4 * 0.001)
)
```

Every rule also needs `for:` — a duration the condition must hold before the alert fires — so a
single scrape-interval blip does not page. Keep it short on the fast-burn rules (a minute or two);
the long window is already doing the smoothing. [official]

## Two severities

Exactly two, and they are defined by the response, not by an impact adjective:

- **Page** — a user-facing failure that needs action now.
- **Ticket** — a degradation that needs action this week.

Anything else is a dashboard. A third and fourth tier turn every alert into a sorting exercise,
and the sorting is always done wrong under pressure.

A paging alert must be actionable, important and **rare**. More than one or two pages a week per
rotation is alert fatigue, and fatigue is not a discipline problem — it is the predictable outcome
of a pager that is usually wrong. Fix the alerts or fix the underlying reliability; do not ask
people to be more attentive.

## Runbooks

Every paging alert links to a runbook. The minimum useful runbook is three lines, and three good
lines beat twenty skimmed ones:

```markdown
# Runbook: checkout fast burn
**Means:** checkout is failing fast enough to spend 2% of the monthly budget in an hour.
  Usually a bad deploy or the payment provider degrading.
**First check:** error ratio by route and by provider for the last hour; then the deploy log.
**Escalate to:** payments on-call, then the provider's status page.
```

Expand beyond three lines only when the first check alone cannot decide what to do next. Update
the runbook as part of closing every incident it was used in — a stale runbook is worse than none,
because it is trusted.

## Recording rules for alert expressions

Precompute the SLI so the alert expression stays readable and cheap:

```yaml
groups:
  - name: checkout-sli
    interval: 30s
    rules:
      - record: checkout:error_ratio:rate5m
        expr: |
          sum(rate(http_requests_total{job="checkout",status_code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="checkout"}[5m]))
```

The trap: aggregate **after** the rate, never before. `sum without (pod) (rate(x[5m]))` is
correct; summing a counter across pods and then taking `rate()` of the sum merges independent
counter resets and produces nonsense — the same corruption as dropping a distinguishing label,
expressed in PromQL instead of in a relabel rule. The inverted form usually arrives as a
subquery, `rate(sum without (pod) (x)[5m:30s])`, which is valid syntax and reads plausibly, so it
survives review; every pod restart in the summed series then looks like a counter reset. Check
the nesting order of any rule that both aggregates and rates, and prefer `sum without (...)` over
`sum by (...)` so a new label cannot silently change the grouping.

## Auditing an alert set

Quarterly, and after any incident that revealed a gap:

- Which alerts fired, and how many were acted on? An alert with a zero action rate is noise.
- Which incidents were not caught by any alert? Those are the missing symptom alerts.
- Does every paging alert have a `for:` duration, a runbook link and one of the two severities?
- Is any alert on a cause rather than a symptom?
- Is any threshold an unexplained absolute number rather than something derived from an SLO or a
  measured baseline?
- Have the SLOs been met? A consistently breached target is either wrong or under-resourced —
  decide which, rather than leaving it breached.
- Did any alert stay firing long after its incident ended? That is a missing short window.
- Is the paging path itself monitored? If the notification provider is down, nothing tells you
  except its own status feed.

<!-- sources: rampstack-monitoring, addyosmani-agent-skills, grafana-skills, google-sre-workbook, prometheus, otel-semconv -->
