# ES|QL

Verified against: Elasticsearch 9.5.3. Version gates in this file are Elastic Stack versions;
on Serverless (`build_flavor: "serverless"` in `GET /`) every GA and preview feature is available
and `version.number` must not be used for feature checks.

## Contents

- [What it is for, and what it is not for](#what-it-is-for-and-what-it-is-not-for)
- [Shape of a query](#shape-of-a-query)
- [The implicit LIMIT](#the-implicit-limit)
- [Commands worth knowing](#commands-worth-knowing)
- [Full-text search in ES|QL](#full-text-search-in-esql)
- [Joins and enrichment](#joins-and-enrichment)
- [Multi-branch retrieval and fusion](#multi-branch-retrieval-and-fusion)
- [Time series](#time-series)
- [Query directives](#query-directives)
- [Translating Query DSL to ES|QL](#translating-query-dsl-to-esql)

## What it is for, and what it is not for

ES|QL is a piped query language executed at `POST /_query`. Pick it over Query DSL when the task is
**analysis**: filter, transform, group, compute, join, and get a table back.

| Task | Use |
|---|---|
| Ad-hoc slice-and-group over structured data | ES\|QL |
| Computing new columns from existing ones | ES\|QL |
| Joining a lookup index onto results | ES\|QL |
| Time-series rates and downsampling | ES\|QL (`TS`) |
| Ranked document retrieval for an end user | Query DSL — richer relevance controls, retrievers, pagination |
| Paginating a result set | Query DSL — ES\|QL has no `search_after` |
| Aggregations feeding an existing dashboard | Query DSL, unless you are rewriting the dashboard |

ES|QL returns `columns` and `values`, not `hits`. There is no `_source` echo unless you ask for the
`_source` metadata field, and no scoring unless you ask for `METADATA _score`.

## Shape of a query

```esql
FROM logs-app-*
| WHERE @timestamp >= NOW() - 24 hours AND service == "checkout"
| STATS errors = COUNT(*), p95 = PERCENTILE(latency_ms, 95) BY service, bucket = BUCKET(@timestamp, 1 hour)
| SORT errors DESC
| LIMIT 20
```

- One source command (`FROM`, `ROW`, `SHOW`, `TS`) then processing commands separated by `|`.
- `==` for equality, not `=`. `=` is assignment inside `EVAL`/`STATS`.
- `:` is the match operator (`message : "timeout"`), distinct from `==`.
- Field names with dots are literal paths (`service.keyword`), and a `text` field is not directly
  groupable — `STATS ... BY title` on a `text` field fails the same way a `terms` aggregation does;
  group by `title.keyword`.
- Multi-valued fields come back as arrays and most functions return `null` on them. `MV_EXPAND`,
  `MV_COUNT`, `MV_FIRST` and friends are how you deal with them, and forgetting is a common source
  of unexplained nulls.

## The implicit LIMIT

A query with no `LIMIT` returns at most 1000 rows (`esql.query.result_truncation_default_size`).
There is no warning in the response body that truncation happened. Any query whose result is
consumed programmatically must state its own `LIMIT`, and any aggregate whose bucket count could
exceed 1000 needs one too — otherwise the "top" you are reading is an arbitrary 1000 of them.

## Commands worth knowing

| Command | Does | Notes |
|---|---|---|
| `WHERE` | Filter | Push it as early as possible; everything after it processes fewer rows |
| `EVAL` | Compute new columns | Cannot reference a column created later in the same `EVAL` |
| `STATS ... BY` | Aggregate | Drops every column not named in the aggregation or the `BY` |
| `KEEP` / `DROP` | Project | `KEEP` also fixes column order |
| `RENAME old AS new` | Rename | — |
| `SORT` | Order | On a `text` field it fails; sort on the `keyword` sub-field |
| `DISSECT` / `GROK` | Parse a string column | `DISSECT` for fixed delimiters, `GROK` for patterns; both at query time, so a hot path wants an ingest pipeline instead |
| `MV_EXPAND` | One row per value of a multi-valued field | Row count multiplies |
| `SAMPLE` | Probability sample of rows | For exploring a huge index cheaply |
| `CHANGE_POINT` | Detect a change in a metric series | — |
| `COMPLETION` | Call an LLM inference endpoint per row | Tech preview; Platinum licence |

## Full-text search in ES|QL

`MATCH(field, "text")`, the `:` operator, `MATCH_PHRASE`, `QSTR` (Lucene query string) and `KQL`
are available in `WHERE`. Scoring requires opting in:

```esql
FROM articles METADATA _score
| WHERE MATCH(content, "elasticsearch performance")
| SORT _score DESC
| LIMIT 10
```

Without `METADATA _score` the rows come back unordered by relevance and `_score` is not a column.

Choosing between ES|QL and Query DSL for search: ES|QL gives you filter/transform/join around the
search, Query DSL gives you the relevance machinery (retrievers, rescoring, query rules,
`multi_match` types, highlighting, pagination). Search that a user sees generally belongs in Query
DSL; search inside an analysis pipeline belongs in ES|QL.

`RERANK` (GA 9.4) applies an inference endpoint to already-retrieved rows and defaults to 1000
rows (`esql.command.rerank.limit`). Retrieve cheaply with a `LIMIT`, then rerank — never rerank an
unbounded result.

## Joins and enrichment

`LOOKUP JOIN target ON field` (GA 8.19/9.1) joins a lookup index onto the current rows and is the
default choice: no policy to define, changes to the lookup index are visible immediately, and it
supports several join keys. The target index must be created with `index.mode: lookup`.

`ENRICH policy ON field` is the older mechanism, needs `PUT /_enrich/policy/...` plus an execute
step, and serves a *snapshot* of the source data taken at execution time — stale until re-executed.
Use it only on clusters before 8.18.

Neither is a general SQL join: the lookup side must be a lookup-mode index, and the result is a
left join that fills unmatched rows with nulls.

## Multi-branch retrieval and fusion

`FORK` (tech preview, 9.1) runs up to 8 branches over the same input and tags rows with `_fork`.
Each branch has its own implicit `LIMIT 1000`. `FUSE` (tech preview, 9.2) merges those branches and
recomputes `_score`, with `rrf` or `linear` strategies:

```esql
FROM articles METADATA _score, _id, _index
| FORK ( WHERE MATCH(content, "elasticsearch") | SORT _score DESC | LIMIT 50 )
       ( WHERE semantic_content : "how does elasticsearch work" | SORT _score DESC | LIMIT 50 )
| FUSE rrf SCORE BY _score KEY BY _id
| LIMIT 10
```

Same licence gate as the Query DSL fusion retrievers — check `GET /_license` before designing
around it. Constraints: one `FORK` per query, no remote cluster references, not usable inside or
after subqueries.

## Time series

`TS index` is the source command for `time_series`-mode indices. It understands rate-style
functions (`RATE`, `MAX_OVER_TIME`, ...) that need the per-series time dimension, and `TBUCKET` for
time bucketing. Without a `STATS`, `TS` returns rows sorted by `@timestamp` descending. A
`time_series` index requires `index.mode: time_series` with declared `time_series_dimension` fields,
so this is a decision made at index creation, not at query time.

## Query directives

`SET name = "value";` before the source command, one per line, each ending in a semicolon:

| Directive | Since | Effect |
|---|---|---|
| `unmapped_fields` | 9.3 preview | `fail` (default), `nullify`, or `load` (9.4, loads them as `keyword`). Needed when querying across indices where some lack a field |
| `time_zone` | 9.4 GA | Default zone for all date functions. There is **no** per-function timezone argument |
| `approximation` | 9.5 GA | Samples rows and extrapolates `STATS`, returning confidence intervals. `COUNT_DISTINCT`, `MIN`, `MAX`, `TOP` and several others silently fall back to exact execution |

`SET` cannot be used inside a view definition; the caller applies it.

## Translating Query DSL to ES|QL

| Query DSL | ES\|QL |
|---|---|
| `bool.filter: [term]` | `WHERE field == value` |
| `bool.must: [match]` | `WHERE MATCH(field, "...")` + `METADATA _score` |
| `range` | `WHERE field >= x AND field < y` |
| `terms` aggregation | `STATS COUNT(*) BY field` |
| `date_histogram` | `STATS ... BY BUCKET(@timestamp, 1 hour)` |
| `cardinality` | `COUNT_DISTINCT(field)` (same HyperLogLog++ estimate) |
| `percentiles` | `PERCENTILE(field, 95)` (same TDigest estimate) |
| `_source` filtering | `KEEP a, b, c` |
| `from`/`size` pagination | no equivalent — keep pagination in Query DSL |
| `nested` query | no equivalent — ES\|QL does not query `nested` fields |

The estimates carry over: `COUNT_DISTINCT` and `PERCENTILE` in ES|QL are the same approximations
as their aggregation counterparts, with the same caveats about additivity and exactness.

<!-- sources: elastic-agent-skills, elastic-docs, clawic-elasticsearch -->
