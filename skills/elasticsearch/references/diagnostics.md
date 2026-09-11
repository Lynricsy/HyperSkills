# Diagnostics

Verified against: Elasticsearch 9.5.3.

## Contents

- [Triage order](#triage-order)
- [Reading a profile](#reading-a-profile)
- [Error string to cause](#error-string-to-cause)
- [Cluster status in one screen](#cluster-status-in-one-screen)
- [Slow logs](#slow-logs)
- [Is it the query or the cluster?](#is-it-the-query-or-the-cluster)
- [Benchmarking honestly](#benchmarking-honestly)

## Triage order

Each step is cheaper than the next and eliminates a whole class of cause. Do not skip to step 6.

| # | Question | Call |
|---|---|---|
| 1 | Does the document exist at all? | `GET /{index}/_doc/{id}` — if not, this is an ingest problem |
| 2 | Does the query parse the way you think? | `GET /{index}/_validate/query?explain=true` — a misplaced brace turns a `filter` into a no-op |
| 3 | What terms are actually indexed? | `POST /{index}/_analyze` with the field and the text — compare to the query terms |
| 4 | Why did *this* document not match? | `GET /{index}/_explain/{id}` with the query body — names the clause that failed |
| 5 | Why is it ranked *here*? | The same search with `"explain": true` — boost, then idf, then tf, then length norm |
| 6 | Where does the time go? | The same search with `"profile": true` — per shard, per clause |
| 7 | Query or cluster? | Re-run with `?preference=_shards:0` — see below |

Steps 1–3 take seconds each and explain most reports. "Search returns nothing" is almost never a
search problem.

## Reading a profile

`"profile": true` on a search returns `profile.shards[]`, each with `searches[]` (the query tree
and a `collector` tree) and `aggregations[]`.

- Sort the query tree's nodes by `time_in_nanos` and name the top one. That node is the finding;
  everything else is noise.
- `breakdown` decomposes each node. `next_doc` dominating means the query is iterating documents
  (a wildcard, a scan); `build_scorer` dominating means construction cost (a huge `terms` list);
  `score` dominating means genuine scoring work.
- `rewrite_time` on a multi-term query is the term-dictionary enumeration — this is where a
  `wildcard` or `regexp` shows up before it has matched anything.
- The collector tree shows how much time went to sorting versus collecting.
- `profile` adds its own overhead, so treat the absolute numbers as relative weights. The ratio is
  the signal.

Measured on 9.5.3 on a one-document index, `wildcard: {"status.keyword": "*ctiv*"}` profiles as
`MultiTermQueryConstantScoreBlendedWrapper` at 5 096 401 ns against 108 855 ns for the equivalent
`TermQuery` — the shape of the finding is visible with no data at all.

Report a performance finding as: top node type and description, its `time_in_nanos`, the rewrite,
and the same numbers after. A `took` that improved without the profile changing is a warm cache,
not a fix.

## Error string to cause

Match on the exception `type`; the human-readable text drifts between versions.

| Exception | Means | First move |
|---|---|---|
| `illegal_argument_exception: Fielddata is disabled on [f]` | Aggregating or sorting a `text` field | Use the `.keyword` sub-field. Never `fielddata: true` |
| `illegal_argument_exception: Limit of total fields [1000] has been exceeded` | Mapping explosion, almost always a dynamic object | `flattened` or `dynamic: strict`; raising the limit postpones the outage |
| `illegal_argument_exception: Result window is too large` | `from + size` past `index.max_result_window` | `search_after` + point-in-time |
| `strict_dynamic_mapping_exception` | A field arrived that the strict mapping does not define | Fix the producer, or add the field deliberately |
| `mapper_parsing_exception` | Value does not fit the mapped type | Fix the producer or coerce in an ingest pipeline; the mapping cannot change |
| `document_parsing_exception` | Malformed JSON or a type conflict in the document | Same |
| `version_conflict_engine_exception` | Concurrent write to the same `_id` | `retry_on_conflict` for updates; `if_seq_no` + `if_primary_term` for read-modify-write |
| `es_rejected_execution_exception` | A thread-pool queue is full | Back off and reduce concurrency; this is the ceiling, not a transient |
| `circuit_breaking_exception` | The request wants more heap than it may have | Narrow the aggregation or batch. Raising the breaker kills the node instead |
| `too_many_buckets_exception` | Past `search.max_buckets` (65 536) | `composite` pagination or a coarser interval |
| `cluster_block_exception ... read-only-allow-delete` | Flood-stage disk watermark | Free disk; the block clears below the high watermark |
| `cluster_block_exception ... blocked by: [FORBIDDEN/12/index read-only]` | Someone set it deliberately, or an ILM step did | Find out which before clearing it |
| `search_phase_execution_exception` | A shard-level failure, aggregated | The real error is inside `failed_shards[].reason` — read that, not the wrapper |
| `index_not_found_exception` on a wildcard | The pattern matched nothing | `ignore_unavailable` / `allow_no_indices`, or the alias was never swapped |
| `security_exception: current license is non-compliant for [X]` | Feature above the licence tier | `GET /_license`; RRF and the `linear` retriever need Enterprise |
| `illegal_argument_exception: only write ops with an op_type of create are allowed in data streams` | `PUT /{stream}/_doc/{id}` against a data stream | Target the backing index, or use `_update_by_query` |
| `circuit_breaking_exception: [parent]` | Cluster-wide memory pressure | Usually another request; check `GET /_nodes/stats/breaker` for which breaker and which node |

`search_phase_execution_exception` deserves emphasis: it is a wrapper. Reporting it without opening
`failed_shards[].reason` is reporting that something failed.

## Cluster status in one screen

```
GET /_cluster/health?level=indices              # green/yellow/red, and where
GET /_cat/indices?v&s=store.size:desc           # size, docs, health per index
GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason
GET /_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,load_1m,disk.used_percent
GET /_cat/thread_pool/search,write?v&h=node_name,name,active,queue,rejected
GET /_cat/allocation?v                          # disk per node
POST /_cluster/allocation/explain               # why THIS shard is unassigned
GET /_nodes/hot_threads                         # what a pegged node is executing
GET /_tasks?actions=*search*&detailed           # what is running right now
```

Colour semantics: **green** every primary and replica assigned; **yellow** every primary assigned,
some replica is not — degraded redundancy, not data loss; **red** at least one primary unassigned —
that shard's data is unavailable right now.

`GET /_health_report` gives Elasticsearch's own diagnosis with remediation hints and is worth
reading before forming a theory.

## Slow logs

Per index, thresholds per level, separately for query and fetch phases:

```json
PUT /{index}/_settings
{ "index.search.slowlog.threshold.query.warn": "5s",
  "index.search.slowlog.threshold.query.info": "2s",
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.indexing.slowlog.threshold.index.warn": "5s" }
```

- Thresholds are **per shard**, not per request. A request that takes 3s because it hit 20 shards
  at 150 ms each never appears.
- A slow *fetch* phase with a fast query phase means `_source` retrieval, large documents, or
  highlighting — not the query.
- The indexing slow log truncates the source at `index.indexing.slowlog.source` characters
  (default 1000); set it to `false` if the logs must not contain document content.
- These settings are dynamic, so they can be turned on during an incident and off afterwards.

## Is it the query or the cluster?

Re-run the same query against a single shard:

```
GET /{index}/_search?preference=_shards:0
```

Similar latency means the cost is in the query. Wildly different latency across shards means one
node or one shard is the problem — an unbalanced shard, a cold shard whose data is not in page
cache, or a node with a different hardware or GC profile. `GET /_cat/nodes` and `_nodes/hot_threads`
take it from there.

`preference` also pins repeated requests to the same shard copies, which removes cache variance
from a before/after measurement.

## Benchmarking honestly

- Do not co-locate the load generator with the cluster under test. They perturb each other's
  measurements, and the effect is large enough to invert a comparison.
- A benchmark against a cluster you did not provision cannot collect host-level metrics (CPU, GC,
  disk I/O, index size). Those numbers are directional, not reproducible — say so when quoting
  them.
- Never benchmark production. The tooling creates, writes to and deletes indices, and competing
  traffic makes the result meaningless in both directions.
- Warm up. The first query after a refresh pays for global ordinals, and the first query on a cold
  shard pays for page cache. Measure the steady state, and measure it more than once.

<!-- sources: clawic-elasticsearch, elastic-agent-skills, elastic-rally, elastic-docs -->
