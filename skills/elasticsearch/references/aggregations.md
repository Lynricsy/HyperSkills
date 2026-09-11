# Aggregations

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1).

## Contents

- [The three families](#the-three-families)
- [terms: approximate by construction](#terms-approximate-by-construction)
- [composite for exhaustive enumeration](#composite-for-exhaustive-enumeration)
- [cardinality is an estimate](#cardinality-is-an-estimate)
- [Percentiles are an estimate too](#percentiles-are-an-estimate-too)
- [Date histograms and time zones](#date-histograms-and-time-zones)
- [nested, reverse_nested and filters](#nested-reverse_nested-and-filters)
- [Memory: buckets, breakers and how to stay under them](#memory-buckets-breakers-and-how-to-stay-under-them)
- [The field type mistakes](#the-field-type-mistakes)

## The three families

| Family | Produces | Examples |
|---|---|---|
| Bucket | Sets of documents | `terms`, `date_histogram`, `histogram`, `range`, `filters`, `composite`, `nested` |
| Metric | Numbers over a bucket | `avg`, `sum`, `min`, `max`, `stats`, `cardinality`, `percentiles`, `top_hits` |
| Pipeline | Numbers over other aggregations' output | `bucket_script`, `derivative`, `moving_fn`, `bucket_selector`, `cumulative_sum` |

Pipeline aggregations run on the coordinating node after the buckets come back, so
`bucket_selector` filters buckets *after* every shard has already built them — it saves response
size, not work.

Always pair aggregations with `"size": 0` unless the hits are genuinely needed. Fetching and
decompressing `_source` for ten documents nobody reads is often the larger half of the request.

## terms: approximate by construction

Every `terms` aggregation is approximate on a multi-shard index, and the response says so. Each
shard returns its own top `shard_size` terms; the coordinating node sums them. A term that ranks
11th on every shard but is globally 3rd can be missed entirely.

Two fields in every response are the evidence:

- `doc_count_error_upper_bound` — the largest possible undercount for any returned bucket.
  Non-zero means the counts may be wrong.
- `sum_other_doc_count` — documents that fell outside the returned buckets. Large relative to the
  returned counts means the picture is partial.

Verified on 9.5.3: both fields are present even on a single-shard index (where they are 0). Quote
them when reporting aggregation results; a top-10 with a `doc_count_error_upper_bound` comparable
to the tenth bucket's count is not a top-10.

Controls:

- `shard_size` (default `size * 1.5 + 10`) — raise it to shrink the error. Cost is per-shard
  memory and network, not per-document work.
- `size` — the number of buckets returned. Raising `size` to "get them all" is what
  `too_many_buckets_exception` is protecting you from; use `composite` instead.
- `show_term_doc_count_error: true` — per-bucket error rather than one global bound.
- `order` by a sub-aggregation's metric makes the error unbounded and unreported. Ordering by
  `_count` or `_key` is the only case with a usable error bound.
- `execution_hint: map` builds the map from values rather than global ordinals; it helps only for
  low-cardinality fields on high-cardinality indices, and hurts otherwise.

`min_doc_count: 0` forces every term in the dictionary into the response, including ones with no
matching documents. On a high-cardinality field this is the fastest way to trip a circuit breaker.

## composite for exhaustive enumeration

`composite` paginates buckets with an `after` key, streaming the whole set in sorted order with
bounded memory. That is the correct tool for "export every value", "reconcile against another
system", and any job whose output feeds a batch process.

What it gives up: it cannot be ordered by a metric (only by the source keys), so "top 10 by
revenue" is still a `terms` aggregation with a generous `shard_size`. And each page is a separate
search request, so a long enumeration should run under a point-in-time to stay consistent.

## cardinality is an estimate

`cardinality` uses HyperLogLog++. `precision_threshold` (default 3000, maximum 40 000) is the count
below which results are near-exact; above it, error grows to a few percent. Memory is roughly
`precision_threshold × 8` bytes per shard per aggregation, so the maximum is not free.

There is no exact distinct count in Elasticsearch. If the number is going on an invoice, compute it
with `composite` enumeration, or in ES|QL, or outside the cluster.

## Percentiles are an estimate too

`percentiles` uses TDigest, which is accurate at the extremes and less so in the middle, and whose
error depends on `compression` (default 100). Two consequences:

- Percentiles are not additive. You cannot average per-shard p99s, and you cannot average yesterday's
  p99 with today's. Aggregate the underlying data, not the percentiles.
- `percentile_ranks` (what percentile is this value) is the inverse and has the same error profile.
- `"hdr": {"number_of_significant_value_digits": 3}` switches to HDRHistogram: bounded memory and
  bounded relative error, better for latency data with a known range.

## Date histograms and time zones

- `calendar_interval` (`1d`, `1M`, `1q`, `1y`) respects daylight saving and month lengths;
  `fixed_interval` (`24h`, `30d`) does not. A "daily" chart built on `fixed_interval: 24h` drifts by
  an hour twice a year.
- `time_zone` shifts bucket boundaries and must match what the UI renders in, or the last bucket of
  each day lands in the wrong place.
- `min_doc_count: 0` plus `extended_bounds` is how you get empty buckets for a continuous chart;
  without them, gaps in the data become gaps in the axis.
- `offset` moves boundaries for business days that do not start at midnight.

## nested, reverse_nested and filters

Aggregating a field inside a `nested` mapping requires a `nested` aggregation with the `path`
first, or the field is not found. `reverse_nested` climbs back out to count parent documents — the
difference between "how many order lines mention this SKU" and "how many orders do".

`filters` (plural) runs several named filters in one pass over the same document set; it is
considerably cheaper than N separate requests or N `filter` sub-aggregations that each re-evaluate
the parent query.

## Memory: buckets, breakers and how to stay under them

Buckets are built in heap on the data node and again on the coordinating node.

| Guard | Default | Symptom |
|---|---|---|
| `search.max_buckets` | 65 536 | `too_many_buckets_exception` |
| Request circuit breaker | 60% of heap | `circuit_breaking_exception` |
| Parent circuit breaker | 95% of real memory | `circuit_breaking_exception`, often on an innocent request |

Bucket count multiplies: a `terms` of 1000 with a nested `date_histogram` of 100 is 100 000
buckets before any metric. Raising `search.max_buckets` converts a rejected request into an OOM;
the fix is a smaller `size`, `composite` pagination, or a coarser interval.

A `circuit_breaking_exception` is a request asking for more heap than it may have. Narrow the
request. Raising the breaker limit turns a failed query into a dead node, and a dead node turns a
yellow cluster into a red one.

`global_ordinals` (how `terms` on `keyword` is executed) are built per segment and cached; the
first aggregation after a refresh pays for them. On a write-heavy index this shows as an
aggregation that is intermittently slow for no visible reason —
`eager_global_ordinals: true` on the field moves that cost to refresh time.

## The field type mistakes

- **`terms` on a `text` field** fails outright:
  `Fielddata is disabled on [title] in [index]. Text fields are not optimised for operations that
  require per-document field data like aggregations and sorting, so these operations are disabled
  by default. Please use a keyword field instead.` (Measured on 9.5.3.) The fix is the `.keyword`
  sub-field. Setting `fielddata: true` uninverts every distinct term of that field into heap and is
  the most reliable way to break a production cluster.
- **`doc_values: false`** on a field somebody later wants to aggregate: same class of failure,
  fixable only by reindexing.
- **Aggregating a `flattened` sub-field** works but everything in it is a `keyword` — no numeric
  metrics, no date histograms.
- **Scripted aggregations** (`script` instead of `field`) run per document with no doc_values
  shortcut. Use a runtime field defined in the mapping if it is reused, and an indexed field if it
  is on a hot path.

<!-- sources: clawic-elasticsearch, elastic-agent-skills, elastic-docs -->
