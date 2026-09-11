# Redis Query Engine, vectors and semantic search

Verified against: Redis 8.10.1 (`MODULE LIST` reports `search 81000`, `ReJSON 81000`,
`vectorset 1`, `bf 81001`, `timeseries 81000`).

## Contents

- [Is the engine there](#is-the-engine-there)
- [Index creation](#index-creation)
- [Field types and the exact-match trap](#field-types-and-the-exact-match-trap)
- [Query syntax](#query-syntax)
- [Debugging a query that returns nothing](#debugging-a-query-that-returns-nothing)
- [Aggregation](#aggregation)
- [Vector fields](#vector-fields)
- [Vector sets](#vector-sets)
- [Choosing between the two vector mechanisms](#choosing-between-the-two-vector-mechanisms)
- [Hybrid retrieval](#hybrid-retrieval)
- [Index lifecycle](#index-lifecycle)
- [Semantic cache index](#semantic-cache-index)

## Is the engine there

`MODULE LIST` is the check. The 8.x official server bundles the query engine, JSON, Bloom,
time-series and vector sets; a 7.x server or a self-compiled build has none of them unless
Redis Stack modules were loaded. Command availability floors that matter: `FT.SEARCH` and
`FT.AGGREGATE` from 2.0 as a module and 8.0 built in, `FT.HYBRID` from 8.4, vector sets from
8.0. Establish the version before proposing any of them.

## Index creation

An index is a view over keys matching a prefix. The documents stay ordinary Hashes or JSON
documents; the index is maintained synchronously on write.

```
FT.CREATE idx:products ON HASH PREFIX 1 product:
  SCHEMA
    name        TEXT WEIGHT 2.0
    description TEXT
    status      TAG SORTABLE
    sku         TAG
    price       NUMERIC SORTABLE
    location    GEO
    embedding   VECTOR HNSW 6 TYPE FLOAT32 DIM 1536 DISTANCE_METRIC COSINE
```

- **Always set `PREFIX`.** Without it the index matches every key of that type in the database,
  which indexes unrelated data and costs memory and write latency on every unrelated write.
- Indexing is not free: every write to a matching key updates the index on the command thread.
  A prefix that accidentally matches a high-write key space shows up as a latency regression
  with no slow command to blame.
- `SORTABLE` stores a copy of the value for sorting and for fast `RETURN`, at a memory cost.
  `UNF` (un-normalised form) keeps the original casing for a `TAG` that will be returned.
- For JSON: `ON JSON` and `$.path.to.field AS alias`. The alias is what queries use; the raw
  path is not queryable. Arrays of scalars index as multi-values; arrays of objects need one
  path per field.
- `NOOFFSETS`, `NOFREQS`, `NOHL` shrink the index by dropping capabilities (phrase matching,
  scoring, highlighting). Only drop what the queries demonstrably do not use.

## Field types and the exact-match trap

| Type | Query form | Use for |
|---|---|---|
| `TEXT` | `@name:wireless` | Human prose; tokenised, stemmed, stop-worded, scored |
| `TAG` | `@status:{active}` | Identifiers, enums, statuses, SKUs, foreign keys — matched whole |
| `NUMERIC` | `@price:[100 500]` | Numbers, timestamps, ranges, sorting |
| `GEO` | `@loc:[lon lat radius unit]` | Point-radius search |
| `GEOSHAPE` | `@area:[WITHIN $poly]` | Polygons, containment |
| `VECTOR` | `*=>[KNN 10 @embedding $v]` | Similarity |

The trap, measured `[verified]`. With `sku` declared as `TEXT`:

```
HSET p:1 name "wireless headphones" status active sku "ABC-123"
FT.SEARCH idx '@sku:ABC-123' NOCONTENT   ->  0 results
FT.EXPLAIN idx '@sku:ABC-123'
  @sku:INTERSECT {
    @sku:UNION { @sku:abc  @sku:+abc(expanded) }
    @sku:UNION { @sku:-123 @sku:+-123(expanded) }
  }
```

The tokeniser split on the hyphen and the query became an intersection of two stemmed tokens,
one of which parses oddly. No error, no warning, zero rows. With the same value in a `TAG`
field, `@sku:{ABC\-123}` matches exactly.

Two more measured behaviours from the same index `[verified]`:

- `@status:{active}` returned only the document whose status is exactly `active`, not the one
  with `active-trial` — `TAG` matches the whole value (splitting only on the configured
  separator, comma by default).
- `@name:headphone` returned **both** documents whose name contains "headphones" — `TEXT` is
  stemmed, which is desirable for prose and wrong for codes.

Rule: if a human would not read the value as a sentence, it is a `TAG`. Escape `-`, `.`, `@`,
`:` and spaces inside `TAG` values, or set a `SEPARATOR` that does not occur in the data.

## Query syntax

- Space is AND, `|` is OR, `-` is NOT, `~` marks a clause optional (it contributes to score
  without filtering), `=>{$weight: 2.0}` boosts a clause.
- Parenthesise. `@a:{x} | @b:{y} @c:{z}` does not group the way most readers expect.
- `LIMIT 0 20` — the default is 10 rows, and deep `LIMIT 100000 20` pagination costs the
  server the whole prefix. Page by a sortable field's last value where possible.
- `RETURN n f1 f2` restricts the reply to the fields you need; `NOCONTENT` returns ids only.
  Both matter: the default returns whole documents.
- `SORTBY field [ASC|DESC]` needs the field to be `SORTABLE` to be cheap.
- `DIALECT 2` is the default since Redis 8 and is required for vector query syntax. On older
  servers pass it explicitly; a query written for dialect 2 silently parses differently under
  dialect 1.
- `PARAMS 2 name value` plus `$name` in the query is how to pass a value — required for
  vectors (binary) and the right habit for user input generally.
- Stop words are dropped from `TEXT` queries, so a search for a phrase made of stop words
  returns nothing. `STOPWORDS 0` at index creation disables the list.

## Debugging a query that returns nothing

In this order:

1. `FT.EXPLAIN idx '<query>'` — how the query parsed. Most empty results are visible here:
   a tokenised identifier, a stop word dropped, a clause grouped unexpectedly.
2. `FT.INFO idx` — `num_docs` (is anything indexed at all?), `hash_indexing_failures` (are
   writes being rejected, e.g. a non-numeric value in a `NUMERIC` field?), and the schema as
   the server understands it.
3. `FT.PROFILE idx SEARCH QUERY '<query>'` — per-iterator counters and timing, which shows
   which clause eliminated everything.
4. Check the prefix: `FT.CREATE ... PREFIX 1 product:` does not index `products:1`. An index
   over zero documents returns zero rows without complaint.
5. Check the type: an index created `ON HASH` ignores JSON documents entirely and vice versa.

`hash_indexing_failures` above zero is the field most often overlooked — the write succeeded,
the indexing did not, and the document is simply absent from every query.

## Aggregation

`FT.AGGREGATE` is a pipeline for faceting and computed output.

```
FT.AGGREGATE idx:orders '@status:{shipped}'
  LOAD 2 @category @amount
  GROUPBY 1 @category
    REDUCE SUM 1 @amount AS revenue
    REDUCE COUNT 0 AS orders
  SORTBY 2 @revenue DESC
  LIMIT 0 5
```

- Stages run in order: `LOAD`, `APPLY` (computed fields), `FILTER` (post-query, so it cannot
  use an index), `GROUPBY` + `REDUCE`, `SORTBY`, `LIMIT`.
- `LOAD` reads from the document, which is a key lookup per row — `SORTABLE` fields come from
  the index instead and are much cheaper.
- `FILTER` after `GROUPBY` is a scan over the groups; push every condition the index can serve
  into the query string instead.
- For large result sets use `WITHCURSOR COUNT n` and `FT.CURSOR READ` so the server pages
  rather than materialising everything.

## Vector fields

```
embedding VECTOR HNSW 6 TYPE FLOAT32 DIM 1536 DISTANCE_METRIC COSINE
```

Three settings must match the embedding model exactly, and a mismatch produces plausible
nonsense rather than an error:

- `DIM` — the model's output dimensionality.
- `DISTANCE_METRIC` — `COSINE` for normalised text embeddings (the common case), `IP` for
  unnormalised inner product, `L2` for Euclidean. The query's ordering is meaningless if this
  disagrees with how the vectors were produced.
- `TYPE` — `FLOAT32` normally; `FLOAT16` or `BFLOAT16` only when memory is the binding
  constraint, and then measure recall before and after.

```
FT.SEARCH idx:docs '*=>[KNN 5 @embedding $vec AS score]'
  PARAMS 2 vec "<raw little-endian float32 bytes>"
  SORTBY score
  DIALECT 2
```

- The vector is passed as raw bytes, not as text. A vector serialised as JSON silently fails to
  match anything.
- `SORTBY score` is needed to get the results in similarity order; without it the order is the
  engine's.
- Algorithm choice: `FLAT` is exact and cheap to build, fine below roughly ten thousand vectors
  or when recall must be 100%. `HNSW` is approximate, much faster at scale, and costs memory.
- HNSW parameters: `M` (graph connectivity, 16–64) and `EF_CONSTRUCTION` (build-time candidate
  list, 100–500) are fixed at creation and changing them requires a rebuild. `EF_RUNTIME` is
  the query-time recall knob and can be tuned per query.
- Establish recall with a measurement, not a parameter: run the same queries against a `FLAT`
  copy of the data and compare the returned id sets.

## Vector sets

A separate engine (`vectorset` in `MODULE LIST`), schema-less, addressed by key:

```
VADD vs VALUES 3 1 0 0 a
VADD vs VALUES 3 0 1 0 b
VADD vs VALUES 3 0.9 0.1 0 c
VSIM vs VALUES 3 1 0 0 WITHSCORES COUNT 2   ->  a 1 , c 0.996941864490509
VDIM vs                                      ->  3
VINFO vs  ->  quant-type int8  hnsw-m 16  vector-dim 3  size 3 ...
```

All verified `[verified]`. Two things to know before using one:

- **Quantisation is on by default.** `VINFO` reports `quant-type int8` on a set created with no
  options, which is lossy. Pass `NOQUANT` when exactness matters and accept roughly four times
  the memory, or `BIN` for binary quantisation when memory dominates.
- `VSIM` scores are similarities in `[0, 1]` where 1 is identical — the opposite direction from
  a distance. Getting this backwards inverts a threshold.
- Elements can carry attributes (`VSETATTR`/`VADD ... SETATTR`) and `VSIM ... FILTER` applies a
  simple expression over them, but this is not the full query language of an RQE index.

## Choosing between the two vector mechanisms

| Situation | Mechanism |
|---|---|
| The query also filters on attributes, tags, numeric ranges or full text | RQE `VECTOR` field |
| The vectors belong to documents that already exist as Hashes or JSON | RQE `VECTOR` field |
| Lexical and vector scores must be fused | RQE, `FT.HYBRID` (8.4+) |
| A standalone nearest-neighbour collection, no schema, minimal memory | Vector set |
| Millions of vectors where int8 quantisation is acceptable | Vector set |

Do not mix them for one corpus. Two indexes over the same data double the write cost and drift
apart.

## Hybrid retrieval

Two different things get called hybrid:

**Filter-then-vector** (any version) — attribute filters narrow the candidate set before the
similarity comparison, inside one query:

```
FT.SEARCH idx:docs '(@category:{tech} @published:[1735689600 +inf])=>[KNN 10 @embedding $vec AS score]'
  PARAMS 2 vec "..." SORTBY score DIALECT 2
```

Always prefer this to fetching a wide result and filtering client-side: the client-side version
is slower *and* less accurate, because the KNN already discarded the matching documents that
ranked below the cut.

**Score fusion** (`FT.HYBRID`, 8.4+) — a lexical leg and a vector leg with an explicit fusion
stage (`COMBINE RRF` or `LINEAR`). Use it when a keyword match and a semantic match should both
contribute to ranking. On servers below 8.4 the approximation is filter-then-vector plus
client-side re-ranking, and it is an approximation.

A filtered KNN can under-return: if the filter is very selective, the approximate search may
not find `K` matching neighbours in the candidates it explored. Iterative or exhaustive search
modes exist for this case; the symptom is fewer rows than `K` with no error.

## Index lifecycle

- Schema changes: `FT.ALTER idx SCHEMA ADD field TYPE` adds a field and backfills it. Removing
  or retyping a field requires a new index.
- Zero-downtime rebuild: create `idx:products_v2`, wait for `FT.INFO` to show
  `indexing: 0`/`percent_indexed: 1`, then `FT.ALIASUPDATE products idx:products_v2`. Queries
  address the alias, never the versioned name.
- `FT.DROPINDEX idx` drops the index and keeps the documents; `FT.DROPINDEX idx DD` deletes the
  documents too — a destructive flag one character away from the safe form.
- `FT._LIST` enumerates indexes. `FT.INFO` reports `num_docs`, `inverted_sz_mb`,
  `vector_index_sz_mb` and `hash_indexing_failures`; export the last one.
- In Cluster mode an index spans the shards and queries fan out, so a query's latency is the
  slowest shard's. Index memory is per shard.

## Semantic cache index

A semantic cache is an ordinary RQE index used for a particular purpose. The Redis-side design:

```
FT.CREATE idx:llmcache ON HASH PREFIX 1 llmcache:<model>:
  SCHEMA
    prompt      TEXT NOINDEX
    response    TEXT NOINDEX
    task        TAG
    prompt_vec  VECTOR HNSW 6 TYPE FLOAT32 DIM <model dim> DISTANCE_METRIC COSINE
```

- Entry keys carry the model name, because one index belongs to exactly one embedding model and
  dimensionality. Changing models means a new index and a cold cache; there is no migration.
- Every entry gets a TTL. A semantic cache without expiry is a permanent record of one day's
  model behaviour and of whatever the underlying data said then.
- `task` is a mandatory filter, not a nicety: a support prompt and a code prompt can be close
  in embedding space and their answers are unrelated. Filter on it in the query, or use
  separate indexes.
- The threshold is the whole design. Decide whether your client exposes a similarity (larger is
  stricter) or a distance (smaller is stricter), then measure: embed a few hundred prompt pairs
  you consider equivalent and a few hundred you do not, plot the two distributions, and put the
  cut where they separate. A constant copied from documentation written against the other
  convention inverts the behaviour.
- Store the prompt embeddings in a second, longer-lived key space: a repeated prompt's embedding
  is reusable even when the response must be regenerated.
- Never semantically cache answers where a near-miss is harmful — prices, balances,
  entitlements, medical or legal text. Hash the normalised prompt and cache exactly instead.

<!-- sources: redis-agent-skills, redisvl, redis-io-docs -->
