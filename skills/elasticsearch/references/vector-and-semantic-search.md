# Vector and semantic search

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1), **basic** licence, single node.

## Contents

- [Licence gate: check this before designing anything](#licence-gate-check-this-before-designing-anything)
- [Choosing a retrieval method](#choosing-a-retrieval-method)
- [dense_vector, and the defaults that surprise people](#dense_vector-and-the-defaults-that-surprise-people)
- [Running a kNN search](#running-a-knn-search)
- [semantic_text: the low-effort path, on a licence that has inference](#semantic_text-the-low-effort-path-on-a-licence-that-has-inference)
- [Sparse vectors and ELSER](#sparse-vectors-and-elser)
- [Hybrid retrieval](#hybrid-retrieval)
- [Chunking](#chunking)
- [Measuring recall](#measuring-recall)

## Licence gate: check this before designing anything

Measured on 9.5.3 with `GET /_license` reporting `"type": "basic"`:

| Feature | Basic licence | Evidence |
|---|---|---|
| `dense_vector` + `knn` | works | kNN search returns hits |
| `sparse_vector` field and query with precomputed weights | works | field type is not gated; producing the weights is |
| `standard` retriever | works | — |
| `_rank_eval` | works | returns `metric_score` |
| **Inference API** | **403** | `POST /_inference/sparse_embedding/.elser-2-elasticsearch` → `security_exception: current license is non-compliant for [inference]` |
| **`semantic_text` ingest** | **403, but only on write** | `PUT` of the mapping succeeds and resolves `inference_id` to `.elser-2-elasticsearch`; the first document indexed fails with the `[inference]` error above |
| **`rrf` retriever** | **403** | `security_exception: current license is non-compliant for [Reciprocal Rank Fusion (RRF)]` |
| **`linear` retriever** | **403** | `security_exception: current license is non-compliant for [linear retriever]` |

Three tier gates are declared `License.OperationMode.ENTERPRISE` in the source:
`INFERENCE_API_FEATURE`, `RANK_RRF_FEATURE` and `LINEAR_RETRIEVER_FEATURE`. So on a basic
licence there is **no in-cluster inference and no fusion operator**: embeddings must be produced
outside the cluster and the two result lists must be fused by the application.

The `semantic_text` case deserves its own warning because the failure is **delayed**. The index
creates, `GET /_inference/_all` happily lists `.elser-2-elasticsearch`,
`.multilingual-e5-small-elasticsearch` and `.rerank-v1-elasticsearch`, and a CI smoke test that
only creates indices goes green. The 403 arrives when production data starts flowing. Prove the
licence allows a feature by exercising it end to end, not by creating the mapping.

## Choosing a retrieval method

| Method | Strong at | Weak at | Cost |
|---|---|---|---|
| BM25 (`match`) | Exact terms, rare and domain-specific vocabulary, operators (`prefix`, `fuzzy`, `regexp`) | Synonyms, paraphrase, cross-lingual | Cheapest to store and query |
| Dense vectors (`dense_vector` + `knn`) | Paraphrase, semantic similarity, cross-lingual with the right model | Exact identifiers, rare tokens the model never saw, explaining *why* something matched | Embedding generation, plus an index that mostly lives in memory |
| Sparse vectors (ELSER) | Semantic recall while staying in the inverted index; no embedding model to host | Languages the model was not trained on | Larger index than BM25, inference at index and query time |
| Hybrid | Everything above, in practice | — | Both pipelines, plus fusion tuning |

Default answer for a text corpus: keep BM25, add one semantic method, fuse. Vectors alone lose
exact-match behaviour that users rely on (part numbers, error codes, names).

## dense_vector, and the defaults that surprise people

```json
{ "emb": { "type": "dense_vector", "dims": 1024, "index": true, "similarity": "cosine" } }
```

Read the mapping back after creating it. Measured defaults on 9.5.3:

| `dims` | Resolved `index_options` |
|---|---|
| ≤ 320 | `{"type": "int8_hnsw", "m": 16, "ef_construction": 100}` |
| ≥ 384 | `{"type": "bbq_hnsw", "m": 16, "ef_construction": 100, "rescore_vector": {"oversample": 3.0}}` |

Three consequences:

- **Quantization is on by default.** `int8` is 4× smaller than `float32`; BBQ (binary quantization)
  is far smaller again and is lossy enough that Elasticsearch pairs it with automatic rescoring —
  `oversample: 3.0` means it retrieves 3× `k` quantized candidates and re-scores them with fuller
  precision. Recall is a measured quantity here, not an assumption.
- **The parameter names are Elasticsearch's, not hnswlib's.** `m` and `ef_construction` live under
  `index_options` and are fixed at index creation. There is no `ef_search`; the query-side recall
  knob is `num_candidates`.
- **`similarity` must match how the model's vectors were produced.** `cosine` normalises;
  `dot_product` requires you to have normalised already; `l2_norm` is Euclidean. Using
  `dot_product` with unnormalised vectors gives scores that are not comparable across documents.

Two more mapping facts:

- **Vectors are excluded from `_source` by default in 9.x.** `index.mapping.exclude_source_vectors`
  is `true`, so `GET /{index}/_doc/{id}` returns everything *except* the vector. Measured. Set it
  to `false` at index creation if the application needs the raw embedding back.
- `"index": false` makes the field exact-search-only (brute force through a `script_score`), which
  is the right choice under roughly 10k vectors — an HNSW graph costs more than it saves there.

`dims` must match the model exactly and cannot be changed. Write the model name and version into
the index name or a metadata field: re-embedding with a different model is a reindex, and there is
no way to tell from the data which model produced a vector.

## Running a kNN search

```json
{ "knn": { "field": "emb", "query_vector": [ ... ], "k": 10, "num_candidates": 100 },
  "size": 10 }
```

- `num_candidates` is per shard and must be ≥ `k`. It is the recall/latency dial: raise it until
  recall against an exact baseline stops improving. 10× `k` is a reasonable starting point.
- `filter` inside the `knn` clause is applied **during** the graph walk (pre-filtering), so the
  `k` results are all filtered documents. A `bool.filter` outside it is applied afterwards and can
  leave you with fewer than `k` hits — occasionally zero. Put the filter inside.
- A very selective filter degrades HNSW: the graph walk keeps landing on excluded documents.
  Elasticsearch falls back to exact search when the filtered set is small enough, but the crossover
  is workload-dependent — measure rather than assume.
- kNN can also be a query clause (`{"knn": {...}}` inside `bool.should`), which is how you combine
  it with BM25 without a fusion retriever.

## semantic_text: the low-effort path, on a licence that has inference

```json
{ "mappings": { "properties": { "body": { "type": "semantic_text" } } } }
```

Measured: this creates successfully with no other configuration and resolves `inference_id` to
`.elser-2-elasticsearch`. The field type then handles chunking, embedding at index time,
embedding the query at search time, and storing the chunks — the whole pipeline that would
otherwise be an ingest pipeline plus application code.

It needs the Inference API, which is Enterprise. On basic the first document indexed into the
field returns `403 current license is non-compliant for [inference]` even though the mapping was
accepted. It also needs ML-capable nodes, or model deployment fails independently of the licence.

Query it with a `semantic` query, or with `match` (which is routed to the semantic query for that
field). Trade-offs against hand-rolled `dense_vector`:

- You do not control the chunking strategy beyond `chunking_settings`, or the vector storage
  options.
- Changing `inference_id` on an existing field is a reindex, same as changing `dims`.

Where inference is available, start with `semantic_text`, and move to explicit `dense_vector`
when you need a specific model, a specific chunking strategy, or control over quantization.
Where it is not, `dense_vector` with vectors produced outside the cluster is the only path.

## Sparse vectors and ELSER

ELSER produces a sparse bag of weighted expansion tokens rather than a dense vector, stored in a
`sparse_vector` field and searched with the `sparse_vector` query. It lives in the inverted index,
so it behaves like BM25 operationally (no graph to build, no memory-resident index) while
retrieving on meaning. It is English-first; `.multilingual-e5-small-elasticsearch` (dense) is the
preconfigured alternative for other languages.

The `sparse_vector` field type and query are not gated — you can index token/weight pairs you
computed elsewhere. Having Elasticsearch produce them with ELSER is, because that goes through
the Inference API.

## Hybrid retrieval

**With an Enterprise licence**, use a fusion retriever:

```json
{ "retriever": { "rrf": {
    "retrievers": [
      { "standard": { "query": { "multi_match": { "query": "...", "fields": ["title^3", "body"] } } } },
      { "knn": { "field": "emb", "query_vector": [ ... ], "k": 50, "num_candidates": 200 } }
    ],
    "rank_window_size": 100, "rank_constant": 20 } } }
```

RRF fuses by rank, not score, so the two systems' incomparable score scales stop mattering.
`rank_window_size` is how deep each retriever is considered; `rank_constant` (default 60) flattens
the contribution of top ranks — lower values weight the very top more heavily.

**On a basic licence**, fuse yourself. Two options:

1. One request, score addition — measured working on 9.5.3:

   ```json
   { "query": { "bool": { "should": [
       { "match": { "txt": "..." } },
       { "knn": { "field": "emb", "query_vector": [ ... ], "num_candidates": 100, "boost": 2.0 } } ] } } }
   ```

   BM25 scores are unbounded and cosine similarities are roughly 0–1, so the `boost` is doing
   normalisation by hand. Tune it against a judgement set; the right value is corpus-specific and
   changes when the analyzer or the model changes.

2. Two requests, fused in the application by reciprocal rank (`1/(k + rank)`, `k` around 60). More
   round trips, but it is scale-free and it is the same maths RRF uses.

ES|QL has its own fusion path (`FORK` branches combined with `FUSE rrf` or `FUSE linear`) which is
subject to the same licence gate.

## Chunking

Embedding models truncate at a token limit, so a long document embedded whole loses its tail and
averages away its specifics.

- Chunk to a few hundred tokens with a small overlap, on a boundary the content has (paragraph,
  heading section) rather than a fixed character count.
- Index one document per chunk with a parent id, or use `nested` chunks so a hit points at the
  parent. `semantic_text` does this for you.
- Return the parent document to the user and the chunk to the model. Users want the page; an LLM
  wants the passage.

## Measuring recall

Approximate kNN has no error message when recall is bad; results are just quietly worse.

1. Build the ground truth: run the same query vectors with `"index": false`-style exact search
   (a `script_score` over the full set, or a small copy of the index) and record the true top-k.
2. Run the approximate search and compute overlap@k.
3. Raise `num_candidates` (and, if you rebuild, `ef_construction` and `m`) until overlap plateaus.
4. Re-measure after any change to quantization, `dims`, the model, or the filter selectivity —
   each of them moves recall independently.

For end-to-end relevance (not just vector recall), `_rank_eval` with a graded judgement set is the
measurement, and it works on a basic licence.

<!-- sources: elastic-agent-skills, opensearch-launchpad, clawic-elasticsearch, wshobson-vector-tuning, elastic-docs, elasticsearch-repo -->
