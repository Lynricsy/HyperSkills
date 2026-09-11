# Relevance

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1), basic licence.

## Contents

- [Order of operations](#order-of-operations)
- [How BM25 scores, and the two knobs](#how-bm25-scores-and-the-two-knobs)
- [multi_match: pick the type deliberately](#multi_match-pick-the-type-deliberately)
- [Boosting that works, and boosting that does not](#boosting-that-works-and-boosting-that-does-not)
- [Two-phase ranking: rescore and reranking](#two-phase-ranking-rescore-and-reranking)
- [Query rules for deterministic promotion](#query-rules-for-deterministic-promotion)
- [Measuring: _rank_eval and a judgement set](#measuring-_rank_eval-and-a-judgement-set)
- [Reading an explain output](#reading-an-explain-output)

## Order of operations

Relevance work goes wrong when steps are done out of order. The sequence:

1. **Remove anything that overrides scoring.** A `sort` clause on a field replaces score ordering
   entirely; every `_score` in the response becomes `null` or a constant and no boost anywhere can
   change the result order. If the response shows every hit at `_score: 1.0`, stop and look for the
   `sort`, the `constant_score`, or the all-filter query.
2. **Confirm the fields exist and are the type you think.** `GET /{index}/_mapping`. A clause
   referring to `title.keyword` when `title` has no sub-field matches nothing, silently, whatever
   its boost.
3. **Confirm the terms.** `POST /{index}/_analyze`. Most "bad relevance" is actually "no match".
4. **Fix the query structure** — filters out of `must`, `multi_match` across the right fields.
5. **Then** tune boosts, and only against a judgement set.

## How BM25 scores, and the two knobs

BM25 combines three signals per term: term frequency in the document (with saturation), inverse
document frequency across the shard, and a field-length norm.

Two consequences that drive real decisions:

- **IDF is per shard.** With few documents per shard, the same term can score differently on
  different shards and the top-N ordering wobbles. Use `search_type=dfs_query_then_fetch` when
  diagnosing this; the real fix is fewer, larger shards.
- **Short fields win.** A one-word `title` match outranks the same term buried in a long
  `description` because of the length norm. That is usually the behaviour you want; when it is not
  (tag lists, SKU fields), set `"norms": false` on the field — but this cannot be undone without a
  reindex.

The `BM25` similarity parameters `k1` (term-frequency saturation, default 1.2) and `b` (length
normalisation, default 0.75) are set per field in the mapping and fixed at index creation. Almost
nobody needs to change them, and changing them makes every previous relevance measurement
incomparable. Exhaust query structure and field boosts first.

## multi_match: pick the type deliberately

| `type` | Scores by | Use when |
|---|---|---|
| `best_fields` (default) | The single best-scoring field | Fields are alternative descriptions of the same thing (title, description). Words are expected to co-occur in one field |
| `most_fields` | Sum across all matching fields | The same text is analysed several ways (`title`, `title.english`, `title.ngram`) |
| `cross_fields` | Treats the listed fields as one big field, blending term statistics | The query terms are spread across fields by nature (first name + last name, street + city). **Requires the same analyzer on every listed field** |
| `phrase` / `phrase_prefix` | `match_phrase` per field | Order matters; `phrase_prefix` is the last-term-is-a-prefix variant |
| `bool_prefix` | `match_bool_prefix` per field | Search-as-you-type |

`tie_breaker` (0.0–1.0) on `best_fields` adds a fraction of the other fields' scores, which stops
two documents that both match one field perfectly from being indistinguishable.

Field boosts go in the field list: `["title^3", "description"]`. Start with a boost of 2–3 on the
short precise field; boosts above about 10 usually mean the query structure is wrong.

## Boosting that works, and boosting that does not

| Goal | Mechanism |
|---|---|
| A field matters more | Field boost in `multi_match`, or `boost` on the clause |
| Recent documents rank higher | `function_score` with a `gauss` decay on the date field, or `distance_feature` (cheaper, works as a `should` clause) |
| Popular documents rank higher | `rank_feature` field type + `rank_feature` query — designed for this, saturating by default so one runaway value cannot dominate |
| Certain documents must never appear | `bool.must_not` filter, not a negative boost |
| One document must be first for one query | Query rules (below), not a boost |
| Boost some documents without excluding others | `boosting` query: `positive` plus `negative` with a `negative_boost` factor |

Anti-patterns that keep reappearing:

- Sorting by a business field to "improve relevance". It removes relevance.
- `function_score` with `boost_mode: replace` and a script — this discards BM25 and turns search
  into a ranking by one number.
- Multiplying popularity straight into the score. Popularity distributions are long-tailed, so the
  most popular item wins every query. `rank_feature` with `saturation` exists for exactly this.
- Enormous boosts (`^50`) to force one document to the top. Fragile against every future change,
  and it fails as soon as a second document matches the boosted field.

## Two-phase ranking: rescore and reranking

Cheap query first, expensive scorer over the top N only.

- `rescore` reruns a `query` over the top `window_size` documents **per shard** and combines the
  scores (`query_weight` / `rescore_query_weight`). Classic use: `match` for retrieval,
  `match_phrase` with a slop as the rescorer so phrase-adjacent documents rise.
- The window is per shard, so with 5 shards and `window_size: 50` you rescore up to 250 documents.
  A window smaller than the page size produces a visible discontinuity at the page boundary.
- Semantic reranking uses an inference endpoint over the top N: in Query DSL a
  `text_similarity_reranker` retriever, in ES|QL the `RERANK` command. Both route through the
  Inference API, which is Enterprise-tier — measured, a basic licence returns
  `403 current license is non-compliant for [inference]` even though
  `.rerank-v1-elasticsearch` appears in `GET /_inference/_all`.

## Query rules for deterministic promotion

When the requirement is "this document must be first for this query", scoring is the wrong tool.

1. `PUT /_query_rules/{ruleset_id}` with rules of type `pinned` (promote) or `exclude` (hide).
   `criteria` matches on metadata keys with `exact`, `contains`, `prefix`, `fuzzy` or `always`;
   `actions` names documents by `ids` or by `docs` (`{"_index": ..., "_id": ...}` — use `docs` when
   `_id` is not unique across the searched indices).
2. `POST /_query_rules/{ruleset_id}/_test` with the same `match_criteria` you will send at search
   time, to confirm the rule fires.
3. The search body must contain a `rule` query whose `ruleset_id` points at the ruleset, whose
   `match_criteria` supplies a value for every metadata key the criteria reference, and whose
   `organic` holds the normal relevance query.

**Creating the ruleset pins nothing.** The pin only exists inside a `rule` query. This is the most
common way query rules "do not work".

## Measuring: _rank_eval and a judgement set

Eyeballing page one for two queries is not measurement. `_rank_eval` runs a set of queries against
a set of graded documents and returns a metric.

```json
{
  "requests": [
    { "id": "running-shoes",
      "request": { "query": { "multi_match": { "query": "running shoes", "fields": ["title^3", "description"] } } },
      "ratings": [ { "_index": "catalog", "_id": "P-4417", "rating": 3 },
                   { "_index": "catalog", "_id": "P-2210", "rating": 0 } ] }
  ],
  "metric": { "dcg": { "k": 10, "normalize": true } }
}
```

Available on a basic licence (verified on 9.5.3). Metric choice:

| Metric | Use when |
|---|---|
| `precision` / `recall` | Binary relevant/not, small result sets |
| `mean_reciprocal_rank` | One right answer per query (navigational search) |
| `dcg` with `normalize: true` (nDCG) | Graded relevance, ranking quality over the whole page |
| `expected_reciprocal_rank` | Graded, and a user who stops at the first good result |

Practical minimum: 30–50 queries drawn from the real query log by frequency, graded 0–3, plus
whatever queries the last three complaints were about. Record the metric before the change and
after. A relevance change with no before/after number is a guess that happens to be documented.

`details.<query-id>.unrated_docs` in the response lists returned documents nobody graded — that is
the list to grade next, and a large one means the judgement set is stale.

## Reading an explain output

`"explain": true` on a search, or `GET /{index}/_explain/{id}` with the query body, returns the
score arithmetic. Read it top-down:

1. The top node names the combination (`sum of:` for a `bool`, `max of:` for `best_fields`).
2. Each leaf is one term in one field, decomposed into `boost`, `idf` and `tf`.
3. `idf` shows `n` (documents containing the term) and `N` (documents in the shard) — this is where
   you discover that the term is in 80% of documents and therefore contributes almost nothing.
4. `tf` shows the length norm as `dl` against `avgdl`.

If the document you expected does not appear in `_explain` at all, the problem is matching, not
ranking: go back to `_analyze`.

<!-- sources: elastic-agent-skills, clawic-elasticsearch, opensearch-launchpad, elastic-docs -->
