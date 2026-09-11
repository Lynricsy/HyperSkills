# Query DSL

Verified against: Elasticsearch 9.5.3 (Lucene 10.5.1).

## Contents

- [Filter context is the first decision](#filter-context-is-the-first-decision)
- [bool, and what its four clauses actually mean](#bool-and-what-its-four-clauses-actually-mean)
- [Query types that matter, and their traps](#query-types-that-matter-and-their-traps)
- [Wildcards, prefixes and regexp](#wildcards-prefixes-and-regexp)
- [Pagination](#pagination)
- [Fetching less: _source filtering, fields, docvalue_fields](#fetching-less-_source-filtering-fields-docvalue_fields)
- [Caches and what defeats them](#caches-and-what-defeats-them)
- [Percolator: matching queries against a document](#percolator-matching-queries-against-a-document)
- [Verifying a query before trusting it](#verifying-a-query-before-trusting-it)

## Filter context is the first decision

For every clause, ask: if I removed this, would different documents come back, or would the same
documents come back in a different order?

- Different documents → `bool.filter` or `bool.must_not`. Skips scoring entirely and is cacheable.
- Different order → `bool.must` or `bool.should`. Scored.

Tenant ids, status flags, date ranges, term lists, geo boxes, permission checks: always filter.
The rewrite is mechanical and never changes the result set — only the scores and the cost.

```json
{ "query": { "bool": {
  "filter": [ { "term": { "status": "active" } }, { "term": { "tenant_id": "acme" } } ],
  "must":   [ { "match": { "description": "wireless keyboard" } } ] } } }
```

## bool, and what its four clauses actually mean

| Clause | Contributes to score | Required |
|---|---|---|
| `must` | yes | yes |
| `filter` | no | yes |
| `should` | yes | see below |
| `must_not` | no | must not match |

`should` is the one that surprises people. Alone in a `bool`, at least one `should` clause must
match. Alongside a `must` or `filter`, zero `should` clauses need to match — they only add score.
`minimum_should_match` makes the intent explicit; write it rather than relying on the default.

`must_not` in a `bool` that has no other clause matches everything else, which on a large index is
usually not what was meant — pair it with a `filter` that bounds the candidate set.

## Query types that matter, and their traps

| Need | Query | Trap |
|---|---|---|
| Exact value | `term` / `terms` | Not analysed: on a `text` field it returns zero hits and no error. `terms` caps at `index.max_terms_count` (65 536); beyond that use a terms lookup against another index |
| Human-typed words | `match` | `operator` defaults to `or`, so one matching word is a hit. `minimum_should_match: "75%"` is usually what was wanted |
| Exact phrase | `match_phrase` | `slop: 0` by default; "quick brown fox" does not match "quick fox" |
| Words across fields | `multi_match` | `best_fields` (default) takes the single best field's score; `cross_fields` blends them but requires one analyzer across all listed fields |
| Numbers, dates, versions | `range` in filter context | Unrounded `now` defeats the request cache; use `now-7d/d`. Date maths is evaluated per shard |
| Field present | `exists` | Empty string and empty array count as present; `null`, a missing key, and a value rejected by `ignore_above`/`ignore_malformed` do not |
| Typo tolerance | `match` with `fuzziness: "AUTO"` | AUTO is 0 edits for 1–2 characters, 1 for 3–5, 2 above — short queries get no tolerance |
| Prefix | `match_bool_prefix`, or `search_as_you_type` | `prefix` on a high-cardinality `keyword` scans the term dictionary; index-time `edge_ngram` moves the cost to write time |
| One document must rank first | query rules (`rule` query) | Creating the ruleset pins nothing; the search body must contain the `rule` query with matching `match_criteria` |
| Array element must satisfy two predicates together | `nested` query | Without `nested` mapping the object array is flattened and predicates cross-match |
| Combine any of the above | `bool` | See the `should` rule above |

`query_string` accepts Lucene syntax from the user, including `*:*`, field names and boolean
operators, and throws a parse error on unbalanced input. Never put user text in it. Use
`simple_query_string`, which has no parse errors and no field access, if the product really wants
operator syntax.

## Wildcards, prefixes and regexp

A leading `*` cannot use the term dictionary; the query enumerates terms. Measured on 9.5.3 with a
one-document index, `wildcard: {"status.keyword": "*ctiv*"}` profiles at 5 096 401 ns as a
`MultiTermQueryConstantScoreBlendedWrapper`, against 108 855 ns for the equivalent `TermQuery` —
a 47× difference before any data volume is involved.

Choose by intent:

| Intent | Do this instead |
|---|---|
| Substring in prose | `match` / `match_phrase` on the analysed `text` field |
| Substring in an identifier or path | `wildcard` **field type** (it indexes n-grams for this), or an ngram analyzer |
| Prefix (`timeout*`) | `prefix` on `keyword` for small term dictionaries, `edge_ngram` at index time otherwise |
| Suffix | Index a reversed copy of the field and use `prefix` on it |

`regexp` has the same term-enumeration cost plus a `max_determinized_states` ceiling. If a regexp
is the requirement, anchor it so it does not start with `.*`.

## Pagination

`from` + `size` makes every shard sort and ship `from + size` hits to the coordinating node, so
page 500 costs each shard exactly what returning 10 000 documents costs. `index.max_result_window`
(10 000) turns that into a hard error rather than a slow query:

```
Result window is too large, from + size must be less than or equal to: [10000] but was [10010].
```

Raising the setting raises the memory each search costs on the coordinating node. Do not.

| Use case | Mechanism |
|---|---|
| User-facing "next page" | `search_after` on a tie-broken sort (`[{"@timestamp":"desc"},{"_shard_doc":"asc"}]`) plus a point-in-time |
| Exporting everything | PIT + `search_after`, or `_reindex` to another index |
| Jump to page 500 | Do not offer it. No search engine can do this cheaply; narrow the query instead |

A point-in-time (`POST /{index}/_pit?keep_alive=5m`) freezes the segment set so results stay
consistent across pages and merges cannot drop or duplicate a document. It also holds those
segments on disk, so keep `keep_alive` short and close the PIT when done.

`scroll` still exists and is superseded by PIT + `search_after`; it holds a search context per
scroll and cannot be parallelised as cleanly.

## Fetching less: _source filtering, fields, docvalue_fields

Returning the whole `_source` for 100 hits is often more expensive than matching them.

- `"_source": ["title", "price"]` filters at the coordinating node after the document is fetched
  and decompressed — it saves network, not disk reads.
- `"fields": ["title", "price"]` returns values formatted per the mapping, works on runtime fields
  and multi-fields, and is the modern default for "give me these fields".
- `"docvalue_fields"` reads from columnar storage without touching `_source` at all — cheapest for
  numerics and keywords, capped at `index.max_docvalue_fields_search` (100).
- `"size": 0` when only aggregations are wanted. Shipping hits nobody reads is pure waste.

`track_total_hits` defaults to `10000`: past that the response reports
`"total": {"value": 10000, "relation": "gte"}`. Set it to `true` only when an exact count is a
product requirement, because it forces every matching document to be counted.

## Caches and what defeats them

| Cache | Scope | Populated by | Defeated by |
|---|---|---|---|
| Node query cache | Per node, filter clauses | Filters reused across requests on segments above a size threshold | Putting the clause in `must` instead of `filter` |
| Shard request cache | Per shard, whole response | `size: 0` requests (aggregations) | Any unrounded `now`, since the request body differs every time |
| Page cache (OS) | Per node | Everything Lucene reads | Giving the JVM more than half the RAM |

Rounding date maths (`now-1h/h`) is the single highest-leverage caching change on a dashboard
workload: it makes consecutive requests within the rounding window byte-identical.

## Percolator: matching queries against a document

The `percolator` field type stores a query as a document; `percolate` then asks "which stored
queries match this incoming document". That is the mechanism for saved searches and alert rules —
running every saved query against the index on a timer is the version that does not scale.

The percolator index must have the same mapping as the index the queries were written against, or
field references resolve differently and the stored queries silently mean something else.

## Verifying a query before trusting it

In this order, because each is cheaper than the next:

1. `GET /{index}/_validate/query?explain=true` — does it parse and what did it rewrite to? A
   misplaced brace turns a `filter` into a no-op that matches everything.
2. `POST /{index}/_analyze` — are the terms you are searching for the terms in the index?
3. `GET /{index}/_explain/{id}` — why did *this* document not match, clause by clause.
4. `"explain": true` on the search — why is it ranked *here*.
5. `"profile": true` — where does the time go, per shard and per clause.

<!-- sources: elastic-agent-skills, clawic-elasticsearch, elastic-docs -->
