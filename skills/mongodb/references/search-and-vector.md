# Search and vector retrieval

Verified against: MongoDB 8.3.9 (availability tests), MongoDB 8.0/8.3 documentation
(version gates).

## Contents

- [First: is this deployment even capable?](#first-is-this-deployment-even-capable)
- [Choosing between the three](#choosing-between-the-three)
- [Atlas Search index and query](#atlas-search-index-and-query)
- [`$vectorSearch`](#vectorsearch)
- [Hybrid search](#hybrid-search)
- [Automated embedding](#automated-embedding)
- [`$text` on a self-managed deployment](#text-on-a-self-managed-deployment)
- [`$regex` is not search](#regex-is-not-search)

## First: is this deployment even capable?

`$search`, `$vectorSearch` and `$searchMeta` are served by `mongot`, which ships with Atlas
and with an Atlas CLI local deployment. On a plain `mongod` they do not exist. Verified on
a self-managed 8.3.9:

```
Using $search and $vectorSearch aggregation stages requires additional configuration.
Please connect to Atlas or an AtlasCLI local deployment to enable.
```

So the first question is always which deployment the user has. If it is self-managed and
will stay that way, the honest answers are `$text` with its limits, a collation index for
case-insensitive matching, or a dedicated search engine — not an Atlas Search pipeline that
cannot run.

`$rankFusion` and `$scoreFusion` are ordinary aggregation stages and *do* exist on a plain
`mongod` (verified: `$rankFusion` ran over plain sub-pipelines on 8.3.9), but
`$scoreFusion` requires every sub-pipeline to begin with `$search`, `$vectorSearch` or a
custom `$score`, so it is Atlas-bound in practice.

## Choosing between the three

| Need | Use |
|---|---|
| Keyword relevance, typo tolerance, autocomplete, facets, language analysis | Atlas Search (`$search`) |
| "Find things that mean the same thing", RAG retrieval, image or audio similarity | `$vectorSearch` |
| Both signals in one ranked list | `$rankFusion` (8.0+) or `$scoreFusion` (8.3+) |
| Exact field match, prefix match on an indexed field | an ordinary index — not search |

Vector search is not a replacement for keyword search: it cannot find a part number.
Keyword search is not a replacement for vector search: it cannot find a paraphrase. Which
is why hybrid exists.

## Atlas Search index and query

A search index is a separate object from a regular index, defined as JSON and built
asynchronously by `mongot`.

```javascript
// dynamic: index everything; correct for exploration, wasteful in production
{ mappings: { dynamic: true } }

// static: index what you search, with the analyzer you want
{ mappings: { dynamic: false, fields: {
    title:  { type: "string", analyzer: "lucene.standard" },
    title_ac: { type: "autocomplete", tokenization: "edgeGram", minGrams: 2, maxGrams: 15 },
    category: { type: "token" },          // exact-match facet/filter, not analysed
    price:  { type: "number" },
    tags:   { type: "string", analyzer: "lucene.keyword" } } } }
```

Query operators worth knowing apart: `text` (analysed match, `fuzzy.maxEdits` up to 2),
`phrase` (ordered terms, `slop`), `autocomplete` (needs the autocomplete field type),
`equals`/`in` (token fields, no analysis), `range`, `compound` with `must` / `should` /
`filter` / `mustNot`. `filter` clauses do not contribute to the score — put anything that
is a constraint rather than a relevance signal there.

- `$search` must be the first stage in the pipeline.
- The relevance score comes back as `{$meta: "searchScore"}`; facet counts and total counts
  come from `$searchMeta`.
- Changing an analyzer or a field type requires the index to be rebuilt; it is not a
  hot-swap.
- `dynamic: true` plus a large document means indexing megabytes of text nobody searches.

## `$vectorSearch`

Index definition:

```javascript
{ fields: [
    { type: "vector", path: "embedding", numDimensions: 1536,
      similarity: "dotProduct", quantization: "scalar" },
    { type: "filter", path: "tenantId" } ] }
```

| Parameter | Rule |
|---|---|
| `numDimensions` | Must equal the model's output exactly; ≤ 8192; cannot be changed without dropping the index |
| `similarity` | `dotProduct` if the model emits normalised vectors (cheapest), `cosine` if it does not, `euclidean` when using binary quantisation |
| `quantization` | `scalar` (4×) is the usual balance past ~1 M vectors; `binary` needs `numDimensions` divisible by 8 and `euclidean` |
| `type: "filter"` fields | Any field used in `$vectorSearch.filter` must be declared here |

Query:

```javascript
db.docs.aggregate([
  { $vectorSearch: {
      index: "vec", path: "embedding", queryVector: q,
      filter: { tenantId: 4471 },      // pre-filter, applied during the search
      numCandidates: 200, limit: 10 } },
  { $project: { _id: 0, title: 1, score: { $meta: "vectorSearchScore" } } }
])
```

- `$vectorSearch` must be the first stage.
- `numCandidates` is the recall knob: start at 20× `limit`, raise it when relevant results
  are missing, lower it when latency matters more. Maximum 10 000, never below `limit`.
- `filter` inside the stage pre-filters; a `$match` after the stage post-filters and will
  quietly return fewer than `limit` results. Pre-filter unless the predicate cannot be
  expressed there.
- `exact: true` does an exhaustive scan — right for a correctness baseline or under ~10 000
  documents, wrong for a request path.
- The query vector must come from the same model and the same version as the indexed
  vectors. A model upgrade is a full re-embed and a new index.

## Hybrid search

`$rankFusion` (8.0+) combines sub-pipelines by rank using reciprocal-rank fusion, so the
sub-pipelines' incomparable score scales stop mattering:

```javascript
db.docs.aggregate([
  { $rankFusion: { input: { pipelines: {
        lexical: [ { $search: { index: "txt", text: { query: q, path: "body" } } },
                   { $limit: 50 } ],
        semantic: [ { $vectorSearch: { index: "vec", path: "embedding",
                                       queryVector: v, numCandidates: 200, limit: 50 } } ]
      } },
      combination: { weights: { lexical: 0.3, semantic: 0.7 } } } },
  { $limit: 10 }
])
```

`$scoreFusion` (8.3+) combines normalised scores instead of ranks, which keeps score
magnitude information but needs a normalisation choice (`sigmoid`, `minMaxScaler`, `none`)
and requires each sub-pipeline to start with `$search`, `$vectorSearch` or `$score`.

Give each sub-pipeline its own `$limit` — the fusion stage's cost is driven by how much
each branch produces.

## Automated embedding

Atlas can generate and store the embeddings itself using Voyage AI models, so the
application stores text and queries with text. It removes the embedding pipeline and the
model-version drift that comes with it, at the cost of coupling to Voyage models and their
rate limits. Self-managed needs 8.3+ with `mongot` and Voyage API keys configured at
deployment.

Reach for it when there is no embedding infrastructure yet. Keep your own pipeline when the
model matters (a domain-specific model, multimodal input, or an existing corpus embedded
with something else).

## `$text` on a self-managed deployment

`$text` exists everywhere and is the only built-in option off Atlas. Verified on 8.3.9 —
it works, and its limits are real:

- **One text index per collection.** A second `createIndex` with text fields is rejected
  against the existing one, because the index key is the synthetic `_fts`/`_ftsx` pair.
- No fuzzy matching, no autocomplete, no faceting, no per-field analyzers beyond the
  language setting, and only static per-field `weights` for relevance.
- `{$meta: "textScore"}` is available for sorting, but a `$text` query cannot also sort by
  another field using an index.
- Stemming is language-based and set at index time.

Say plainly that it is a keyword filter with weights, not a search engine, and point at the
`elasticsearch` skill when the requirements are real search requirements.

## `$regex` is not search

An unanchored or case-insensitive `$regex` scans the index or the collection. The
alternatives, in order of preference: an anchored case-sensitive regex (`/^Smith/`) which
becomes a range scan; a case-insensitive collation index for equality; a stored normalised
field (lower-cased, accent-stripped) with an ordinary index; and only then a search engine.

<!-- sources: mongodb-agent-skills, mongodb-docs -->
