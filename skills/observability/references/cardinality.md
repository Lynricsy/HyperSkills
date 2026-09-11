# Metric cardinality

Verified against: Prometheus 2.x/3.x behaviour as documented upstream; the TSDB status endpoint
fields and PromQL feature gates below are marked `[official]` because no local Prometheus instance
was available to exercise them.

## Contents

- [The arithmetic](#the-arithmetic)
- [The one rule](#the-one-rule)
- [What the safe actions are](#what-the-safe-actions-are)
- [Diagnosing: the TSDB status endpoint](#diagnosing-the-tsdb-status-endpoint)
- [Churn](#churn)
- [Histograms](#histograms)
- [Scoring a label](#scoring-a-label)
- [Static target labels versus dynamic sample labels](#static-target-labels-versus-dynamic-sample-labels)
- [Info metrics](#info-metrics)
- [Exemplars](#exemplars)
- [The five levers, in order](#the-five-levers-in-order)
- [Emergency procedure](#emergency-procedure)

## The arithmetic

A time series is one metric name plus one distinct combination of label values. Series count for a
metric is therefore the **product** of its labels' cardinalities, not the sum.

A single metric with `route` (100 values), `status_code` (10), `method` (5) and `instance` (50) is
250,000 series. Adding one label with ten values makes it 2.5 million. This is why "just one more
label" is never just one more label.

The cost lands on both paths:

- **Ingest:** a larger head block and write-ahead log, more memory, bigger remote-write payloads,
  a higher bill.
- **Query:** every aggregation has to materialise the matching series in memory first, so query
  latency and query memory scale with cardinality even when the result is a single line on a
  graph.

The question to ask about any proposed label: *will queries on this metric reliably filter or
aggregate on it?* If no, it should not be a label.

## The one rule

**Never remove, at scrape or relabel time, a label that makes a series unique.** Not `pod`, not
`instance`, not an identifier — nothing that distinguishes one real series from another. This
covers `metric_relabel_configs` with `action: labeldrop` and every equivalent in a collection
agent.

It looks like a cardinality win. It is data corruption:

- **Counter resets interleave.** Two pods' counters collapsed into one series means their
  independent restarts appear as resets on the merged series. `rate()` and `increase()` then
  return garbage — characteristically *absurdly high* values, because every restart reads as a
  reset.
- **Sample volume goes up, not down.** Multiple samples now land on the same series in the same
  scrape: duplicate-sample and out-of-order errors, and more samples per minute rather than
  fewer.
- **Aggregations become wrong, not merely coarse.** A `sum` over the dropped dimension
  double-counts or under-counts depending on how the collapse happened.

The trap is that none of this errors at configuration time. The pipeline keeps running, the numbers
are quietly wrong, and there is **no evidence left in the data** of where it broke. Weeks later
someone asks why `rate()` is absurd and nothing points at the cause.

The same reasoning applies to *normalising* a label value at scrape — collapsing `/users/123` and
`/users/456` into `/users/:id`, or `503` into `5xx`. That is a merge of distinct series wearing a
different name, with the same consequences. Do it at the source or post-ingest, never at scrape.

## What the safe actions are

Three, and only three:

1. **Do not emit the label.** Fix the application. This is the only place a label can be removed
   with no consequence, because the series was never unique on it to begin with.
2. **Drop an entire metric** by `__name__`. You are discarding a whole metric, not merging
   distinct series. It is a real and visible loss, which is what makes it honest.
3. **Aggregate post-ingest** with a mechanism that is counter-reset-aware, recorded (so the
   aggregation is auditable) and reversible. This is the correct tool for structural cardinality
   you cannot fix at the source — `pod`-level series in a large cluster, for instance. Managed
   metrics platforms provide this; the property to demand is reset-awareness, not a product name.

One narrow fourth case: removing a label that **exactly duplicates** a target label. If an
application emits its own `instance` or `cluster` and the scrape target already provides it, the
target label still supplies uniqueness, so removing the duplicate breaks nothing. Prometheus
renames the colliding one to `exported_*`, so scope the rule to those names precisely and never
include a label that is a genuine source of uniqueness. Fixing the application is still better.

## Diagnosing: the TSDB status endpoint

Prometheus exposes a cardinality breakdown directly, and it is almost always the fastest path from
"something is wrong" to "this metric, this label":

```bash
curl -s http://prometheus:9090/api/v1/status/tsdb | jq
```

| Field | Answers |
|---|---|
| `seriesCountByMetricName` | Which metric has the most series |
| `labelValueCountByLabelName` | Which label has the most distinct values |
| `memoryInBytesByLabelName` | Which label costs the most memory |
| `seriesCountByLabelValuePair` | Which specific label value dominates |

Reading it:

- A `_bucket` metric at the top is almost always the answer — see [Histograms](#histograms).
- A metric in the top five that nobody recognises is usually a debug metric that shipped to
  production. Grep the source for the name.
- Any label above roughly 10,000 distinct values is a bug, with the only real exception being an
  intentional per-target label in a very large fleet.
- `trace_id`, `request_id`, `session_id`, `user_id`, `order_id`, `email`, `query`, `path`, `url`:
  these should never be labels. They belong in exemplars, logs or traces.

For the "when did this start?" question, compare the current metric list against the same query
with an `offset` of a week and diff externally. A new metric near the top that was absent a week
ago, with a step change aligned to a deploy, is conclusive. [official]

## Churn

Churn is series being created faster than they retire. The signature is a series count that climbs
steadily and drops sharply whenever the store restarts.

```promql
rate(prometheus_tsdb_head_series_created_total[5m])
rate(prometheus_tsdb_head_series_removed_total[5m])
```

A creation rate that materially and persistently exceeds the removal rate means cardinality is on
a one-way trip.

| Cause | Tell |
|---|---|
| `pod` label with frequent rollouts | Churn spikes align with deploy times |
| `version` / `git_sha` / `image_tag` on every metric | Churn spikes on every deploy, across many metrics at once |
| Ephemeral hostnames in `instance` | Aligns with autoscaling events |
| Dynamically constructed label *names* | Climbs forever, never plateaus |
| An application bug emitting fresh identifiers | Linear unbounded growth with no deploy correlation |

Restarting the store clears churned series and fixes nothing. `pod` is a special case: it is
genuinely high-churn *and* genuinely necessary for per-pod attribution, so it must not be dropped.
Add a stable `workload` target label (controller kind plus name) so dashboards and alerts can
aggregate on something that does not roll, and reduce `pod`-level cost post-ingest if it is too
expensive. [official]

## Histograms

A classic histogram multiplies its base cardinality by roughly **the bucket count plus three** —
one series per `le` bucket, plus `_sum`, `_count` and `_created` (Prometheus 2.39+). With the
default eleven buckets that is a 14× multiplier.

The consequences:

- A histogram whose labels already produce 1,000 series becomes ~14,000 series.
- Every label removed from a histogram saves 14× what removing it from a counter would.
- **Trim the histogram's labels before touching its buckets.** Labels are the larger lever, and
  reducing bucket count degrades the resolution the histogram exists to provide.
- Never `labeldrop` a histogram's labels at scrape. That merges distinct bucket families and
  corrupts the distribution itself, not just the totals.
- Native histograms (Prometheus 2.40+) replace the whole bucket family with one sparse series, and
  are the right answer for high-resolution latency at scale. [official]

## Scoring a label

| Label | Typical cardinality | Verdict |
|---|---|---|
| `env` | 2–5 | Good |
| `job`, `cluster`, `region` | tens | Good |
| `namespace`, `service`, `workload`, `container` | tens to hundreds | Acceptable |
| `instance` | hundreds to low thousands | Evaluate — fine on per-instance metrics, risky on aggregates |
| `pod` | thousands, high churn | Keep (it is the source of uniqueness); reduce cost post-ingest, never drop |
| `route` | bounded if templated, unbounded if raw | Only with templated values |
| `version`, `git_sha` | grows per deploy | Info metric instead |
| `status_code` | ~10 as a class, more as raw codes | Prefer a class on histograms |
| `user_id`, `request_id`, `trace_id` | unbounded | Never — use exemplars |
| `tenant_id` | often unbounded | Only for a small fixed tenant set |
| `error_message`, `query`, `sql` | unbounded text | Never — use a bounded `error_type` enum |

Consistency is a second axis that is easy to miss: `status` in one service, `status_code` in
another and `http_status` in a third produce three label families that cannot be joined. Same for
unnormalised values (`GET` versus `get`). Pick one name and one form, repository-wide.

## Static target labels versus dynamic sample labels

- **Target labels** are set once per scrape target (`env`, `cluster`, `team`, `workload`,
  `service`). Their cardinality is proportional to the number of *targets*, not the number of
  requests — cheap, and high query value. Use them freely.
- **Sample labels** are emitted by the application per measurement (`status_code`, `method`,
  `cache_hit`). They multiply by their value count. Keep them to single digits or low tens.

A corollary that removes a whole class of problems: `instance`, `pod`, `node` and `host` should
come from service discovery, never from application code. An application emitting its own
`instance` collides with the target label, forces an `honor_labels` decision nobody wants to make,
and produces `exported_instance` in the data.

## Info metrics

To *know* a value like `version` without paying for it on every series, attach it to one info
metric and join at query time:

```
app_build_info{app="payment-api", version="2.4.1", git_sha="a1b2c3"} 1
```

```promql
sum by (version) (
  rate(http_requests_total{app="payment-api"}[5m])
  * on (app) group_left (version) app_build_info
)
```

`version` now exists on exactly one series per build rather than on every metric, and the
deploy-driven churn disappears.

PromQL's `info()` function automates this join against the conventional `target_info` metric
(experimental, Prometheus 3.x, needs `--enable-feature=promql-experimental-functions`). Use it
when joining against `target_info`; keep the explicit `group_left` form for custom info metrics,
older versions, or anywhere the feature flag is not enabled. [official]

## Exemplars

An exemplar attaches a `trace_id` — or any key-value pair — to a specific sample without creating
a label dimension. This is the sanctioned home for the identifiers that must not be labels:
`trace_id` for trace correlation, a request identifier for a targeted lookup, anything that is
useful once and ruinous always.

Exemplars need Prometheus 2.26+ and exemplar storage enabled on the server. They are read through
a UI's exemplar support, not through PromQL aggregation. [official]

## The five levers, in order

1. **Fix the application.** Templated routes, bounded error enums, no identifiers as labels, no
   user-supplied strings as label values, no dynamically constructed label names. Saves cost in
   every downstream system at once.
2. **Target-time relabelling.** Additive: set `env`, `cluster`, `team`, `workload` on discovered
   targets; drop entire targets you do not want to scrape. Cheap, and it adds identity rather
   than destroying it.
3. **Post-ingest aggregation.** For structural cardinality you cannot fix at the source. Must be
   counter-reset-aware, recorded and reversible.
4. **Metric-level drops after scrape.** Only the two safe uses: drop an entire metric by
   `__name__`, or remove a label that exactly duplicates a target label. Nothing else.
5. **Recording rules.** Pre-aggregate expensive series into cheaper recorded ones. This reduces
   *query* cost only — the raw series still exist and still cost ingest.

Recording rules carry their own trap: aggregate **after** the rate, not before. `sum without (pod)
(rate(x[5m]))` is correct; `rate(sum without (pod) (x)[5m:])` merges counter resets and is the
same corruption as `labeldrop` in a different syntax.

## Emergency procedure

When the store is actively OOMing or rejecting writes:

1. Identify the offender from `status/tsdb`. One metric usually dominates.
2. Drop that entire metric by `__name__`, and say out loud that the metric is gone until the
   source fix ships. Test the rule in a non-production environment first if there is any chance to.
3. Do **not** reach for `labeldrop` on a distinguishing label, and do not normalise a label value
   at scrape. Either one converts a visible outage into invisible wrong numbers, and the second
   failure is much more expensive than the first.
4. Once stable, fix the source, then remove the emergency drop.
5. Add the guard: an alert on series count growth for the affected metric, so the next occurrence
   is caught before the store falls over.

<!-- sources: grafana-skills, addyosmani-agent-skills, o11y-dev-otel, dash0-agent-skills, prometheus -->
