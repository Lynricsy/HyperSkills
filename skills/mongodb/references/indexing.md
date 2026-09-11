# Indexes

Verified against: MongoDB 8.3.9 (measurements), MongoDB 8.0 (version gates).

## Contents

- [Compound key order: ESR](#compound-key-order-esr)
- [Two single-field indexes are not one compound index](#two-single-field-indexes-are-not-one-compound-index)
- [Sort direction and prefixes](#sort-direction-and-prefixes)
- [Covered queries](#covered-queries)
- [Multikey indexes and parallel arrays](#multikey-indexes-and-parallel-arrays)
- [Index variants and what each is for](#index-variants-and-what-each-is-for)
- [What each operator can do with an index](#what-each-operator-can-do-with-an-index)
- [Collation](#collation)
- [The index budget](#the-index-budget)
- [Removing an index safely](#removing-an-index-safely)
- [Building an index on a live collection](#building-an-index-on-a-live-collection)

## Compound key order: ESR

Equality fields first, then the sort field, then range fields.

- **Equality** — `{f: v}`, `{f: {$eq: v}}`, `$in` with a small list.
- **Sort** — every field of the `sort()`, in order.
- **Range** — `$gt`, `$gte`, `$lt`, `$lte`, `$ne`, a large `$in`, an anchored
  case-sensitive `$regex`.

Measured on 200 000 documents, `find({status, region}).sort({date: -1}).limit(20)`:

| Index | keys examined | docs examined | ms |
|---|---|---|---|
| none | 0 | 200 000 | 74 |
| `{status: 1}` | 50 000 | 50 000 | 57 |
| `{date: -1, status: 1, region: 1}` (sort first) | 319 | 319 | 3 |
| `{status: 1, region: 1, date: -1}` (ESR) | 20 | 20 | 2 |

The sort-first index looks acceptable in that row only because one document in sixteen
matched, so the scan found 20 hits quickly. Change the filter to a value matching one
document and the same index examines all 200 000 keys in 163 ms, while ESR still examines
one. That is the whole argument: a sort-leading index makes the plan's cost depend on the
filter's hit rate, and ESR makes it depend on the result size.

The documented exception is worth knowing and rarely worth using: when the equality field
is barely selective and the range is very selective, Equality → Range → Sort can win by
paying for a blocking sort over far fewer documents. Measure before choosing it.

## Two single-field indexes are not one compound index

Measured, `find({status: 'shipped', region: 'US'})` on the same collection:

| Indexes present | keys | docs | ms |
|---|---|---|---|
| `{status: 1}` and `{region: 1}` | 50 000 | 50 000 | 49 |
| `{status: 1, region: 1}` | 12 500 | 12 500 | 14 |

No index-intersection plan appeared: the planner chose one index and applied the other
predicate as a `FETCH` filter. Treat index intersection as something the planner may do,
never as a substitute for designing the compound index.

## Sort direction and prefixes

`{a: 1, b: 1}` serves `sort({a: 1, b: 1})` and its exact reverse `sort({a: -1, b: -1})`,
because an index can be walked backwards. It does not serve `sort({a: 1, b: -1})` — for a
mixed sort the index directions must match the sort.

Any leftmost prefix of a compound index is itself usable, which is why `{a: 1}` is
redundant once `{a: 1, b: 1}` exists. `{b: 1}` is not redundant: a different leading field
is a different index.

## Covered queries

A query is covered — no document fetch at all — when every field in the filter, the sort
and the projection is in the index, the projection is inclusive, and `_id` is excluded
explicitly. Measured, same query and index:

| Projection | keys | docs |
|---|---|---|
| `{date: 1}` | 20 | 20 |
| `{_id: 0, date: 1}` | 20 | 0 |

Forgetting `_id: 0` is the usual reason a query that should be covered is not. Other
blockers: `$exists` and null-equality predicates (a plain index cannot distinguish missing
from null), and any multikey index whose array field is in the projection.

## Multikey indexes and parallel arrays

An index on an array field indexes one key per element, so a document with 500 tags writes
500 index entries. That fan-out is the real cost of indexing arrays.

A compound index may contain at most one array field, and the failure surfaces at write
time. Verified on 8.3.9: with `{a: [1,2], b: [3,4]}` already in the collection,
`createIndex({a: 1, b: 1})` fails during the build scan; with the index already built over
`{a: [...], b: scalar}` documents, inserting `{a: [5,6], b: [7,8]}` is rejected with
`cannot index parallel arrays [b] [a]`. Applications hit this months after the index was
created, when the second field first receives an array.

`$elemMatch` is the operator that means "one element satisfies all of these", and it is not
optional: `find({items: {$gte: 10, $lte: 20}})` matches a document with `items: [5, 30]`.

## Index variants and what each is for

| Variant | Use for | Watch out for |
|---|---|---|
| Compound | Any query with more than one predicate, or filter + sort | Key order is the whole design |
| Multikey | Array membership | One array field per index; fan-out per element |
| Partial (`partialFilterExpression`) | Indexing the minority of rows a query ever touches | Only used when the query's predicate provably implies the index's — write it literally |
| Sparse | `$exists: true` queries | Superseded by partial indexes for most cases; a sparse index cannot serve a sort over documents missing the field |
| Unique | An invariant, not a performance feature | Missing field counts as `null`, so two documents without the field collide; combine with a partial filter |
| TTL (`expireAfterSeconds`) | Retention | The field must be a BSON date (or an array of dates); deletion runs about once a minute, so expiry is approximate; does not work on the `_id` field |
| Wildcard (`$**`) | Genuinely unpredictable field names | Cannot be compound with another key except a wildcard projection; do not use it to avoid choosing indexes |
| Text | Keyword search on a self-managed deployment | One text index per collection, and that is the hard ceiling |
| `2dsphere` | GeoJSON queries | Coordinates are `[longitude, latitude]`, in that order |
| Hashed | Even shard-key distribution | Cannot serve range queries or sorts |

## What each operator can do with an index

| Predicate | Index use |
|---|---|
| `$eq`, `$in` (small) | Equality bounds — best case |
| `$gt` / `$lt` family | Range bounds; must be last in the key |
| `$ne`, `$nin` | Scans the whole index (matches everything except a point) |
| `$exists: false` | No useful bounds on a plain index |
| `$regex` anchored, case-sensitive (`/^abc/`) | Range bounds on the prefix |
| `$regex` unanchored or `/i` | Full index scan |
| `$where`, server-side JS | No index, deprecated — rewrite as `$expr` |
| `$expr` | Usable since 5.0 for comparisons against a constant; does not get bounds from field-to-field comparisons |
| `$text` | Text index only, and cannot be combined with a sort on another field |

## Collation

A query only uses an index whose collation matches. An index built with the default
(binary) collation is invisible to a query issued with
`.collation({locale: 'es', strength: 2})`, and vice versa. Case-insensitive matching is a
collation decision made at index-creation time, not a query-time flag:

```javascript
db.users.createIndex({ name: 1 }, { collation: { locale: "en", strength: 2 } })
db.users.find({ name: "jose" }).collation({ locale: "en", strength: 2 })
```

## The index budget

A collection accepts at most **64** indexes; verified, the 65th `createIndex` returns
`add index fails, too many indexes for <ns>`. Long before that, each index is work on every
insert, update that touches its keys, and delete, plus cache it takes from the working set.

Past roughly twenty indexes on one collection, require a named query for each. The audit:

```javascript
db.coll.getIndexes()
db.coll.aggregate([{ $indexStats: {} }])   // accesses.ops and accesses.since
db.coll.stats().indexSizes
```

`$indexStats` counters reset when the server restarts, so `accesses.since` is the window
being judged — quote it. An index at zero accesses over a window that includes the monthly
jobs is dead weight; one at zero over two days is unproven.

## Removing an index safely

```javascript
db.coll.hideIndex("status_1")     // planner ignores it; the index is still maintained
// ... one full business cycle ...
db.coll.unhideIndex("status_1")   // instant, if anything regressed
db.coll.dropIndex("status_1")
```

Verified: while hidden, `find({amount: 5})` planned a `COLLSCAN`; after `unhideIndex` the
plan was an `IXSCAN` again. Unhiding costs nothing, re-creating costs a full build — which
is exactly why the hide step exists.

Do not drop an index on the strength of `$indexStats` alone if it is `unique` or TTL: those
enforce something regardless of query usage.

## Building an index on a live collection

On a replica set the build runs on every member and takes an exclusive lock only at the
start and the end, so it does not block writes throughout — but it competes for WiredTiger
cache and I/O for the whole build. Start it in a low-traffic window, and watch replication
lag rather than only the build's progress.

`createIndexes` on a collection that already has an equivalent index with different options
fails rather than silently replacing it; the error names the existing index. To change an
index's options, build the new one under a different name, hide the old one, then drop it.

<!-- sources: mongodb-agent-skills, mongodb-docs, azure-documentdb-kit, awesome-copilot -->
