---
name: elasticsearch
description: "Guides Elasticsearch index and query work: mapping and field-type choice, text versus keyword and multi-fields, analyzers and tokenization, Query DSL and filter context, ES|QL, BM25 relevance tuning and offline evaluation, aggregations and their accuracy limits, dense_vector and semantic_text retrieval, data streams and reindexing, shard and heap sizing, and reading a search profile. Use when designing or reviewing a mapping, when a term query returns nothing, when an aggregation fails on a text field, when results rank badly, when a search is slow or the cluster is yellow or red, or when adding vector or hybrid search. Do not use for log ingestion pipelines, alerting or tracing-driven incident investigation, for Kibana dashboards and saved objects, or for tuning a relational or document database."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# elasticsearch

## Scope

Covers Elasticsearch itself: index and mapping design, text analysis, the Query DSL, ES|QL,
relevance and its measurement, aggregations, vector and semantic retrieval, data streams and the
index lifecycle, reindexing, shard and heap capacity, cluster allocation, diagnostics, and
cluster-level security.

The body is written against **Elasticsearch 9.5** (9.5.3 at time of writing; 8.19 is the last 8.x
series). Rules that need a particular version carry a gate such as `(9.4+)`. Facts marked as
measured were run against a single-node 9.5.3 instance on a basic licence.

Not covered:

- Relational schema, SQL and plan tuning. Use the `postgres` skill.
- Document-database modelling and aggregation pipelines in MongoDB. Use the `mongodb` skill.
- Key-value caching, expiry and eviction. Use the `redis` skill.
- Log and metric collection pipelines, agents and shippers, alerting rules, SLOs, and working back
  from a production alert to a code path. Use the `observability` skill. Index and query design
  for data that happens to be logs is in scope; getting the
  logs there and paging someone about them is not.
- Kibana: dashboards, Lens, Discover, saved objects, Agent Builder, workflows. Not covered by any
  skill here.
- Managed control planes — Elastic Cloud provisioning, deployment sizing, AWS OpenSearch Service
  domains, billing and autoscaling APIs. The index- and query-level rules still apply on managed
  hosting; node settings, `elasticsearch.yml` and JVM options usually will not.
- OpenSearch-only APIs. It forked from 7.10 and has diverged: `neural` queries, ml-commons,
  search pipelines and PPL do not exist here, and advice written for one is not valid for the
  other without checking.

Paths below are relative to this skill's directory.

## Core rules

1. Establish the version and the licence tier before quoting a rule or designing anything:
   `GET /` and `GET /_license`. Half the guidance in circulation is written for 7.x, and several
   headline retrieval features are above the basic tier.
2. Read the mapping before proposing a query, and the access patterns before proposing a mapping
   (`GET /{index}/_mapping`). Both directions of guessing produce work that cannot be undone
   without a reindex.
3. `text` matches, `keyword` filters. A `text` field is analysed into tokens and a `term` query is
   not analysed, so `term` on `text` returns HTTP 200 with zero hits and no error anywhere.
4. Aggregate and sort on `keyword`, never on `text`. The failure is
   `Fielddata is disabled on [f]`; the fix is the `.keyword` sub-field. Setting `fielddata: true`
   uninverts every distinct term into heap and is the most reliable way to break a cluster.
5. A `keyword` sub-field on a long text body needs `ignore_above`, or the whole string is indexed
   as one term. A field that is only searched should not have the sub-field at all.
6. Dynamic mapping guesses from the first document, and the guess is permanent. Measured on 9.5.3
   a JSON string becomes `text` plus a `keyword` sub-field with `ignore_above: 256`, and `9.99`
   becomes `float`, not `double`. Prefer explicit mappings with `"dynamic": "strict"`.
7. Mappings are append-only. Adding a field is fine; changing a field's type, analyzer, `index` or
   `doc_values` flag is impossible in every version. The path is new index → `_reindex` → alias
   swap, which is why every index that matters is created behind an alias on day one.
8. A dynamic `object` over unbounded keys (Kubernetes labels, headers, experiment buckets) becomes
   `Limit of total fields [1000] has been exceeded`. Map it `flattened`. Raising
   `index.mapping.total_fields.limit` postpones the outage and grows cluster state.
9. If dropping a clause would change *which* documents come back rather than their *order*, it
   belongs in `bool.filter`. Filter context skips scoring and is cacheable; the rewrite never
   changes the result set.
10. An object array flattens and loses per-item association. Measured: with `users` as `object`,
    filtering `users.first: Alice` and `users.last: Jones` matches a document containing Alice
    Smith and Bob Jones. Use `nested` only when a query must combine two fields of one element.
11. A leading `*` cannot use the term dictionary. Measured, a `wildcard: "*ctiv*"` profiles 47×
    slower than the equivalent `TermQuery` on a one-document index. Use `match` on the analysed
    field, the `wildcard` field type, or index-time ngrams.
12. An analyzer that *adds* tokens (`edge_ngram`, index-time synonyms, shingles) must not run at
    search time. Measured, an `edge_ngram` analyzer turns the query `elastic` into
    `[el, ela, elas, elast, elasti, elastic]`, so everything matches everything. Set
    `search_analyzer: standard`.
13. `from + size` beyond `index.max_result_window` (10 000) is a hard error, and every page below
    it makes each shard sort and ship `from + size` hits. User-facing paging is `search_after`
    plus a point-in-time; exports are PIT scans or `_reindex`.
14. A `sort` clause replaces relevance ordering entirely. When every `_score` is 1.0 or `null`, no
    boost anywhere in the query can change anything — remove the sort before tuning relevance.
15. Query rules pin documents; boosts rank them. Creating a ruleset pins nothing: the search body
    must carry a `rule` query whose `match_criteria` supplies every metadata key the criteria use.
16. Every `terms` aggregation is approximate. Report `doc_count_error_upper_bound` and
    `sum_other_doc_count` alongside the buckets; use `composite` when the requirement is to
    enumerate everything rather than to rank the top N.
17. `cardinality` and `percentiles` are estimates (HyperLogLog++ and TDigest). Percentiles are not
    additive — never average a p99 across shards, days or services.
18. `dense_vector` is quantized by default in 9.x. Measured: `int8_hnsw` up to 320 dimensions,
    `bbq_hnsw` with `rescore_vector.oversample: 3.0` from 384 up. Recall is a number you measure
    against exact search, not an assumption; the query-side knob is `num_candidates` and there is
    no `ef_search`. Vectors are also excluded from `_source` by default
    (`index.mapping.exclude_source_vectors`), so code reading an embedding back out of a hit
    silently gets nothing.
19. The Inference API and the `rrf` and `linear` retrievers are Enterprise-tier: measured, all
    three return HTTP 403 `current license is non-compliant` on a basic licence. So on basic
    there is no in-cluster embedding, no ELSER, no semantic reranking and no fusion operator —
    embed outside the cluster, and fuse with a `knn` clause beside a `match` clause in
    `bool.should`, or by reciprocal rank in the application.
20. Licence failures for inference are delayed: a `semantic_text` mapping is accepted and
    `GET /_inference/_all` lists the preconfigured endpoints, and only the first document indexed
    returns the 403. Prove a gated feature end to end, not by creating the index.
21. Shard count comes from data volume: `max(1, ceil(primary_gb / target_shard_size_gb))` with a
    10–50 GB target, never from node count. Budget 20 shards per GB of heap; the hard stop is
    `cluster.max_shards_per_node` (1000, replicas counted).
22. Heap is `min(RAM/2, 31g)`. The other half is the page cache Lucene reads from, and above
    roughly 32 GB the JVM loses compressed object pointers, so 48 GB of heap addresses fewer
    objects than 31 GB.
23. Yellow means a replica is unassigned — degraded redundancy, not data loss. Red means a primary
    is unassigned. On a single node, yellow is the expected state. `unassigned_info.reason` is the
    trigger; the decider with `decision: "NO"` in `_cluster/allocation/explain` is the cause.
24. `search_phase_execution_exception` is a wrapper: the real error is in
    `failed_shards[].reason`. A `_bulk` request likewise returns HTTP 200 while individual items
    fail, so branch on the response's `errors` flag every time — and
    `es_rejected_execution_exception` is the ceiling you were looking for, not a transient to
    retry harder against.
25. Finish with evidence: re-run under `"profile": true` and quote the top node before and after,
    or re-run `_rank_eval` against the judgement set and quote the metric. A `took` that moved
    without the profile changing is a warm cache.

## Workflows

### design-or-review-a-mapping

- [ ] Collect the access pattern per field — searched as prose, filtered exactly, aggregated,
      sorted, or only returned. Missing access patterns are a blocker, not a guess
      (`references/mapping-and-types.md`).
- [ ] Assign the minimal type set: `text` for prose, `keyword` for exact, the multi-field only when
      one logical field is genuinely both, `flattened` for unbounded key spaces, `scaled_float`
      for bounded-precision metrics, `ip`/`version`/`date` where they apply.
- [ ] Strip waste: `doc_values: false` on return-only fields, no `.keyword` on fields nobody
      facets, `ignore_above` on every `keyword` sub-field of a long body.
- [ ] Decide the dynamic policy explicitly — `strict` for anything user-facing, `runtime` when new
      fields must remain queryable without being indexed.
- [ ] Check the array-of-objects fields: does any query need two of their fields to match the same
      element? Only then is `nested` justified.
- [ ] Settle the analysis chain and check the index/search asymmetry for anything that expands
      tokens (`references/analysis.md`).
- [ ] Decide index shape: time-based append-only data is a data stream with rollover, not a hand-
      rolled daily index; everything else is an ordinary index behind an alias
      (`references/data-lifecycle.md`).
- [ ] **Gate — the mapping does what you said:** create it on a scratch index, index one real
      document, then `GET /{index}/_mapping` to confirm nothing was inferred, run one `term`, one
      aggregation and one search against the fields you claimed support them, and confirm each
      works.

### fix-a-query-that-returns-the-wrong-documents

- [ ] `GET /{index}/_doc/{id}` — does the document exist? If not, this is ingest, not search
      (`references/diagnostics.md`).
- [ ] `GET /{index}/_validate/query?explain=true` — does it parse and rewrite to what you meant?
- [ ] `POST /{index}/_analyze` on the field and on the query text — are the terms the same terms?
      This is where `term` on `text` and the index/search analyzer mismatch both surface.
- [ ] Check the mapping for every field the query names: a clause on a sub-field that does not
      exist matches nothing, silently, whatever its boost.
- [ ] `GET /{index}/_explain/{id}` with the query body for one document that should have matched —
      it names the failing clause.
- [ ] Check `bool` semantics: `should` beside a `must` is optional, `must_not` alone matches
      everything else, `minimum_should_match` is not what you assumed (`references/query-dsl.md`).
- [ ] **Gate — the failing case passes:** re-run the original query, show the document in the
      hits, and show that the documents that should not match still do not.

### tune-relevance

- [ ] Remove anything that overrides scoring first — a `sort` clause, `constant_score`, an
      all-filter query. Every `_score` at 1.0 means nothing downstream can help
      (`references/relevance.md`).
- [ ] Build a judgement set before changing anything: 30–50 real queries from the log, graded 0–3,
      plus the queries behind the last few complaints. Record the baseline with `_rank_eval`.
- [ ] Fix structure before boosts: filters out of `must`, `multi_match` across the right fields
      with a deliberate `type`, `minimum_should_match` stated.
- [ ] Read one bad result with `"explain": true` — idf that shows the term is in most documents,
      or a length norm that is doing the ranking, changes what you would have boosted.
- [ ] Apply one lever at a time: field boosts for importance, `rank_feature` for popularity,
      `distance_feature` or a decay for recency, query rules for "this document must be first".
- [ ] Consider a second phase only after the first is right: `rescore` with a phrase query, or a
      `text_similarity_reranker` over the top N.
- [ ] **Gate — the metric moved:** re-run `_rank_eval` with the same judgement set and quote
      nDCG@10 before and after. A change with no number is a guess.

### diagnose-a-slow-search

- [ ] Separate slow from blocked: `GET /_cluster/health` and `GET /_cat/thread_pool/search,write`.
      Remember `rejected` is cumulative since node start — take two samples
      (`references/diagnostics.md`).
- [ ] Run the real query with `"profile": true` and name the top node by `time_in_nanos`. Do not
      propose capacity changes before this exists.
- [ ] Read the `breakdown`: `next_doc` dominating is iteration (a wildcard, a scan);
      `rewrite_time` is term enumeration; `build_scorer` is a huge clause list.
- [ ] Apply the rewrite the profile points at: leading wildcard → `match` on the analysed field;
      non-scoring clauses → `filter`; `match` on a `keyword` → `term`; unrounded `now` → rounded
      date maths so the request cache can work (`references/query-dsl.md`).
- [ ] Check what the response carries: `size` larger than anyone reads, unfiltered `_source`,
      `track_total_hits: true`, deep `from`.
- [ ] Only now look at shape: shard count against data volume, heap against the 31 GB ceiling,
      shards per node against the budget (`references/cluster-operations.md`).
- [ ] **Gate — the profile changed:** re-run with `"profile": true`, quote the old and new top
      node and their `time_in_nanos`, and say explicitly if the result set changed.

### add-vector-or-hybrid-search

- [ ] `GET /_license` first. On basic the Inference API, the `rrf` retriever and the `linear`
      retriever are all 403, so there is no in-cluster embedding and no fusion operator, and the
      design has to embed outside the cluster and fuse by hand
      (`references/vector-and-semantic-search.md`).
- [ ] Choose the method against the corpus: BM25 for exact and rare terms, ELSER or dense vectors
      for paraphrase, hybrid when both matter — which is most of the time.
- [ ] Where inference is available, prefer `semantic_text` unless you need a specific model,
      chunking strategy or quantization setting; it handles chunking, embedding and query
      embedding. Confirm ML-capable nodes exist, and confirm the licence by indexing one document
      rather than by creating the index — the mapping is accepted either way.
- [ ] For explicit `dense_vector`: pin `dims` to the model, match `similarity` to how the vectors
      were produced, read the mapping back to see which quantization you actually got, and decide
      whether `exclude_source_vectors` needs turning off.
- [ ] Put the filter inside the `knn` clause, not around it, so the `k` results are all filtered
      documents.
- [ ] Fuse: `rrf` retriever on Enterprise; on basic a `knn` clause and a lexical clause inside
      `bool.should` with boosts that you tune, or reciprocal-rank fusion in the application.
- [ ] **Gate — recall and relevance are numbers:** measure approximate-versus-exact overlap@k for
      the vector side, and nDCG@10 with `_rank_eval` for the fused result. Raise `num_candidates`
      until recall plateaus.

### change-a-mapping-on-a-live-index

- [ ] Classify the change: additive (a new field, a new multi-field) applies in place; anything
      touching an existing field's type, analyzer, `index` or `doc_values` needs a new index
      (`references/data-lifecycle.md`).
- [ ] For a data stream, check whether a manual rollover is enough — new fields land in the new
      backing index and old data stays readable, with no reindex at all.
- [ ] Create the destination with the complete corrected mapping, `number_of_replicas: 0` and
      `refresh_interval: -1` for the copy.
- [ ] `POST /_reindex` with `wait_for_completion=false` and `"slices": "auto"`; keep the task id
      and read the task's `failures` array rather than assuming success.
- [ ] Decide how writes arriving during the copy are handled — dual write, or a second delta
      reindex bounded by timestamp.
- [ ] Restore replicas and refresh interval, compare `_count` on both sides, then swap the alias in
      one `POST /_aliases` with `remove` and `add` together.
- [ ] **Gate — proven from the application's side:** run the application's real queries against the
      alias, confirm counts and top hits match the old index, and only then delete the source.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Access-pattern-to-type table, dynamic mapping's actual output, multi-fields and `ignore_above`, object/array/`nested`/`join`, `flattened`, `doc_values`/`index`/`_source` modes, runtime fields, the hard limits, index and component templates, why a type change needs a reindex | Designing or reviewing a mapping, or deciding how to store something | `references/mapping-and-types.md` |
| The analysis chain, index versus search analyzer, autocomplete without breaking search, synonyms, per-language fields, keyword normalizers, `_analyze` and `_termvectors` | A query matches nothing, matches everything, or autocomplete behaves oddly | `references/analysis.md` |
| Filter context and caches, `bool` semantics, the query-type table with traps, wildcards and prefixes, pagination and point-in-time, `_source`/`fields`/`docvalue_fields`, percolator, the verification ladder | Writing or reviewing a Query DSL body | `references/query-dsl.md` |
| BM25 and its knobs, `multi_match` types, boosting that works, `rescore` and semantic reranking, query rules wiring, `_rank_eval` and judgement sets, reading an explain tree | Results rank badly, or a relevance change needs proving | `references/relevance.md` |
| Bucket/metric/pipeline families, `terms` error bounds, `composite`, `cardinality` and `percentiles` as estimates, date histograms and time zones, `nested` aggregations, bucket limits and breakers, the field-type mistakes | Building or debugging aggregations, or explaining why the numbers disagree | `references/aggregations.md` |
| The licence gate, retrieval-method comparison, `dense_vector` defaults and quantization, kNN and filters, `semantic_text`, ELSER, hybrid on basic and on Enterprise, chunking, measuring recall | Adding semantic, vector or hybrid retrieval | `references/vector-and-semantic-search.md` |
| When ES\|QL beats Query DSL, query shape, the implicit `LIMIT 1000`, the command table, full-text functions and `METADATA _score`, `LOOKUP JOIN` versus `ENRICH`, `FORK`/`FUSE`, `TS`, `SET` directives, DSL-to-ES\|QL translation | Writing an analytical query, or translating one | `references/esql.md` |
| Aliases and atomic swaps, data streams and their `create`-only rule, rollover conditions, ILM versus the data-stream lifecycle, index modes including `logsdb`, the reindex procedure, bulk indexing, ingest pipelines, snapshots | Setting up time-based data, changing a mapping, or loading in bulk | `references/data-lifecycle.md` |
| The shard-count formula, heap rules, node roles, allocation deciders, disk watermarks, thread pools, circuit breakers, refresh/flush/merge, rolling restarts and version compatibility, authentication and API keys | Sizing a cluster, or a shard will not allocate | `references/cluster-operations.md` |
| The triage ladder, reading a profile, the exception-to-cause table, the cluster-status call set, slow logs, isolating query cost from node cost, benchmarking honestly | Something is slow, failing, or yellow, and you need the cause | `references/diagnostics.md` |

## Output format

When reviewing a mapping, a query or a cluster change, group findings by file and lead each with
the location:

```
events-mapping.json:31 - breaking - `labels` is a dynamic object over unbounded k8s keys, so every
  new key becomes a mapped field; this is the source of `Limit of total fields [1000] has been
  exceeded`. Map it `flattened`; raising the limit grows cluster state instead of fixing it.
```

Order findings by blast radius: things that already fail or lose data first, then things that
require a reindex to fix later, then performance, then style. Separate the two classes explicitly —
what can be applied to the live index, and what needs a new index plus reindex plus alias swap —
because that distinction decides the release plan.

For a performance finding, quote the evidence (`time_in_nanos` and node type from the profile,
`doc_count_error_upper_bound`, the exception's `failed_shards[].reason`) rather than asserting that
something is slow, and give the before and after request bodies.

## Environment

- Reproduce against the same minor version as production, and say so when you cannot. Defaults
  move within a major: which quantization a `dense_vector` gets, whether vectors stay in
  `_source`, and which features the licence gates have all changed inside 9.x, so a finding from
  9.1 is not a finding about 9.5. A single node is enough for mapping behaviour, analysis, query
  semantics, profile shapes and licence gates:
  `docker run --rm -p 9200:9200 -e discovery.type=single-node -e xpack.security.enabled=false
  docker.elastic.co/elasticsearch/elasticsearch:9.5.3`. Expect yellow — the replica has nowhere to
  go — and set `number_of_replicas: 0` if that is in the way.
- `GET /_license` decides which retrieval features exist, and the check has to exercise the
  feature: a `semantic_text` mapping is accepted on any tier and `GET /_inference/_all` lists the
  preconfigured endpoints on any tier, but indexing a document returns
  `403 ... [inference]` below Enterprise.
- `semantic_text`, ELSER and reranking additionally need ML-capable nodes, independently of the
  licence.
- On Elastic Cloud Serverless (`build_flavor: "serverless"` in `GET /`), shard, node, allocation
  and JVM settings do not exist and version numbers must not be used for feature checks.
- Anything written for OpenSearch needs re-verifying here: the APIs diverged after the 7.10 fork.
