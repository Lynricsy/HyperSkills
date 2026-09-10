# JSONB, full-text search and pgvector

Verified against: PostgreSQL 18.6, pgvector 0.8.6

## Contents

- JSONB: operators and the text trap
- JSONB indexing and operator classes
- Promoting a JSONB field to a column
- JSONB update cost
- Full-text search
- Trigram search for substrings
- pgvector: index and operator pairing
- pgvector: recall, parameters and filters
- Hybrid retrieval

## JSONB: operators and the text trap

| Operator | Returns | Note |
|---|---|---|
| `->` | `jsonb` | Keeps the type; chainable |
| `->>` | `text` | **Always text**, whatever the JSON type was |
| `#>` / `#>>` | `jsonb` / `text` | Path form, `'{a,b}'` |
| `@>` | `boolean` | Containment; indexable by GIN |
| `?` `?|` `?&` | `boolean` | Key existence; GIN with the default operator class only |
| `[...]` | `jsonb` | Subscripting (PG 14+), also assignable |

`->>` returning text is the source of most JSONB bugs: comparisons become lexical, so
`'9' > '10'` and dates sort by their first character. Cast at the point of use, and remember
the cast must match the index expression if there is one:

```sql
WHERE (payload->>'amount')::numeric > 100
WHERE (payload->>'created_at')::timestamptz > now() - interval '7 days'
```

Two more:

- A **missing key** and a **JSON null** both give SQL `NULL` from `->>`. Distinguish with
  `payload ? 'k'` first, then `payload->'k' = 'null'::jsonb`.
- JSONB arrays are **zero**-indexed (`payload->'items'->0`), while SQL arrays are one-indexed.

## JSONB indexing and operator classes

```sql
CREATE INDEX docs_payload_gin      ON docs USING gin (payload);                    -- jsonb_ops
CREATE INDEX docs_payload_pathops  ON docs USING gin (payload jsonb_path_ops);
```

| | `jsonb_ops` (default) | `jsonb_path_ops` |
|---|---|---|
| `@>` containment | yes | yes |
| `?`, `?|`, `?&` key existence | yes | **no** |
| Size (100k docs, measured) | 6984 kB | 6584 kB |
| Buffers for one `@>` lookup (measured) | 35 | 4 |

`jsonb_path_ops` indexes hashed paths rather than every key and value, so it is smaller and
much faster for containment — and simply cannot answer key-existence queries. Verified: with
only a `jsonb_path_ops` index and `enable_seqscan = off`, `payload ? 'nested'` still produced
a disabled sequential scan.

Pick `jsonb_path_ops` when the workload is `@>` only, the default when `?` is also needed, and
create both only if you have measured that you need both.

**GIN does not accelerate `->>` equality.** A GIN index on the whole column does nothing for
`payload->>'status' = 'shipped'`. That needs a B-tree on the expression:

```sql
CREATE INDEX docs_status ON docs ((payload->>'status'));
```

or, better for anything queried regularly, a promoted column.

## Promoting a JSONB field to a column

Anything filtered, sorted, joined or constrained on should be a real column. A stored
generated column keeps the JSONB payload as the source of truth while giving the planner
something to index:

```sql
ALTER TABLE docs
  ADD COLUMN price_cents bigint
  GENERATED ALWAYS AS ((payload->>'price')::bigint) STORED;

CREATE INDEX docs_price ON docs (price_cents);
```

Guard the payload's shape while you are there, because JSONB accepts scalars and arrays at
the top level too:

```sql
ALTER TABLE docs ADD CONSTRAINT docs_payload_object
  CHECK (jsonb_typeof(payload) = 'object');
```

## JSONB update cost

`jsonb_set` is not an in-place edit. Postgres has no partial-column update: changing one key
in a 40 kB document writes a whole new 40 kB row version, and the old one becomes a dead
tuple. A table of large documents with frequent small updates bloats fast — that is a schema
signal, not a vacuum-tuning problem: move the frequently-updated fields out into columns.

`jsonb_set` also only creates the **final** element of a path. `jsonb_set(doc, '{a,b,c}',
'1')` is a no-op if `a` or `a.b` does not exist; use `||` to merge a nested object, or
`jsonb_set` with `create_if_missing` per level.

## Full-text search

Always pass the language configuration explicitly, in both the index and the query. The
single-argument forms depend on `default_text_search_config`, so the same query can index one
way and search another:

```sql
ALTER TABLE articles
  ADD COLUMN search tsvector
  GENERATED ALWAYS AS (
      to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, ''))
  ) STORED;

CREATE INDEX articles_search ON articles USING gin (search);

SELECT id, title, ts_rank(search, q) AS rank
FROM articles, websearch_to_tsquery('english', $1) q
WHERE search @@ q
ORDER BY rank DESC
LIMIT 20;
```

The generated column is the maintenance-free version of what used to need a trigger. Use
`websearch_to_tsquery` for anything a user types — it accepts quoted phrases, `or` and `-`
and never raises a syntax error, unlike `to_tsquery`, which rejects a bare space. Use
`to_tsquery` only for programmatic queries where you control the operators (`&`, `|`, `<->`,
prefix `post:*`).

Weighting lets a title beat a body:

```sql
setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
setweight(to_tsvector('english', coalesce(body,  '')), 'B')
```

Postgres full-text search has no BM25 and no cross-document term statistics; `ts_rank` scores
within the document. If ranking quality is the requirement rather than "find the rows", that
is a search engine's job, not this one's.

## Trigram search for substrings

`LIKE '%needle%'` cannot use a B-tree at all. `pg_trgm` plus GIN indexes three-character
shingles and makes both substring and fuzzy matching indexable:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX users_name_trgm ON users USING gin (name gin_trgm_ops);

SELECT * FROM users WHERE name ILIKE '%smi%';
SELECT * FROM users WHERE name % 'jonh smith' ORDER BY similarity(name, 'jonh smith') DESC;
```

For a prefix-only search (`LIKE 'smi%'`) a plain B-tree works under the C collation, or a
`text_pattern_ops` index otherwise — no extension needed.

## pgvector: index and operator pairing

The index operator class and the query operator must match, or the index is silently ignored
— no error, just a sequential scan and a sort.

| Distance | Operator | Operator class |
|---|---|---|
| Cosine | `<=>` | `vector_cosine_ops` |
| L2 / Euclidean | `<->` | `vector_l2_ops` |
| Inner product | `<#>` | `vector_ip_ops` |

Verified on 20k rows with only a `vector_cosine_ops` HNSW index:

```
-- ORDER BY v <=> $1
 Index Scan using emb_cos on emb
   Order By: (v <=> ...)
-- ORDER BY v <-> $1        (same index, wrong operator)
 Sort  (Sort Method: top-N heapsort)
   ->  Seq Scan on emb  (actual rows=20000.00)
```

Use HNSW rather than IVFFlat for new work: no training step, better recall at the same
latency, and it works on an empty table. IVFFlat's `lists` must be chosen against the final
row count and the index rebuilt when the data grows.

```sql
CREATE INDEX emb_cos ON embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 128);
```

`m` and `ef_construction` are build-time and immutable — changing them means dropping and
rebuilding the index. `m` in the 8–64 range trades index size and build time for recall.

The column's dimension is fixed, and HNSW refuses more than 2000 dimensions:

```
ERROR:  column cannot have more than 2000 dimensions for hnsw index
```

For 3072-dimension embeddings, index the half-precision cast, which raises the ceiling to
4000 at a small recall cost:

```sql
CREATE INDEX ON embeddings USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);
-- and query with the same cast:
ORDER BY embedding::halfvec(3072) <=> $1::halfvec(3072)
```

Run `ANALYZE` after a bulk load and after building the index; without statistics the planner
may not choose the index at all.

## pgvector: recall, parameters and filters

`hnsw.ef_search` (default 40, verified) is the search-time knob: higher means more candidates
examined, higher recall, more latency. Production values are typically 100–200. It is a
per-session GUC, so set it on the connection that serves search:

```sql
SET hnsw.ef_search = 100;
```

**A `WHERE` clause is applied after the index walk.** The index returns `ef_search`
candidates by distance and the filter then removes some of them, so a selective filter can
return fewer rows than the `LIMIT` asks for. Observed on a filtered top-5 query:

```
 Index Scan using emb_cos on emb
   Order By: (v <=> ...)
   Filter: (tag = 3)
   Rows Removed by Filter: 41
```

Forty-one candidates discarded to produce five results — and with a more selective filter the
walk runs out first. Three responses, in order of preference:

1. A **partial HNSW index** per filter value, when the filter takes a handful of known values:
   `CREATE INDEX ... USING hnsw (...) WHERE tenant_id = 42` — exact, and each index is small.
2. **Iterative scan** (pgvector 0.8+): `SET hnsw.iterative_scan = strict_order;` lets the scan
   continue past the first batch until the `LIMIT` is satisfied, bounded by
   `hnsw.max_scan_tuples`.
3. Raise `hnsw.ef_search` so the first batch is bigger — the blunt option, and it costs
   latency on every query, filtered or not.

## Hybrid retrieval

Combining lexical and vector results is usually reciprocal rank fusion rather than a weighted
sum of scores, because `ts_rank` and cosine distance are not on comparable scales:

```sql
WITH lex AS (
    SELECT id, row_number() OVER (ORDER BY ts_rank(search, q) DESC) AS rnk
    FROM docs, websearch_to_tsquery('english', $1) q
    WHERE search @@ q LIMIT 50
), vec AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> $2) AS rnk
    FROM docs ORDER BY embedding <=> $2 LIMIT 50
)
SELECT id, sum(1.0 / (60 + rnk)) AS score
FROM (SELECT * FROM lex UNION ALL SELECT * FROM vec) u
GROUP BY id ORDER BY score DESC LIMIT 10;
```

The constant 60 is the conventional RRF damping term; it flattens the contribution of the
long tail so a document ranked first in one list is not swamped. Both branches need their
`LIMIT` — fusing full result sets throws away the point of the exercise.

<!-- sources: postgresql-docs, pgvector, microsoft-postgres-skills, supabase-postgres-bp, neon-postgres-skills, awesome-copilot-pg -->
