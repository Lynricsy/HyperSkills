# Reading plans and finding the slow thing

Verified against: MongoDB 8.3.9.

## Contents

- [Is it slow or is it blocked?](#is-it-slow-or-is-it-blocked)
- [`explain` verbosities](#explain-verbosities)
- [The counters that decide everything](#the-counters-that-decide-everything)
- [Stage vocabulary](#stage-vocabulary)
- [Worked example](#worked-example)
- [The plan cache](#the-plan-cache)
- [The profiler and the slow-query log](#the-profiler-and-the-slow-query-log)
- [Pagination](#pagination)
- [Query rewrites that beat an index](#query-rewrites-that-beat-an-index)

## Is it slow or is it blocked?

Before reading a plan, check whether the operation is executing at all:

```javascript
db.currentOp({ secs_running: { $gt: 3 }, op: { $ne: "none" } })
```

Look at `waitingForLock`, `lockStats`, `planSummary` and `msg` (an index build or a
`moveChunk` reports progress there). An operation waiting behind a DDL lock, a stepdown or
a chunk migration is not a plan problem, and no index will fix it.

`db.killOp(opid)` exists; on a `mongos` the op id is prefixed with the shard name.

## `explain` verbosities

| Verbosity | Runs the query? | Use for |
|---|---|---|
| `"queryPlanner"` (default) | no | which index the planner would pick, and the index bounds |
| `"executionStats"` | yes, winning plan only | the counters — this is the default choice |
| `"allPlansExecution"` | yes, all candidate plans | why the planner picked the wrong one |

```javascript
db.coll.find(filter).sort(sort).explain("executionStats")
db.coll.explain("executionStats").aggregate(pipeline)
db.coll.explain("executionStats").update(filter, update)   // does not apply the update
```

`explain` does not honour the plan cache the way a normal query does, so a query that is
slow in production and fast under `explain` is usually a cached-plan problem — see below.

## The counters that decide everything

From `executionStats`:

- `nReturned` — what the user asked for.
- `totalKeysExamined` — index entries walked.
- `totalDocsExamined` — documents fetched from storage.
- `executionTimeMillis` — last, and only as a sanity check.

Read them as ratios:

| Shape | Meaning |
|---|---|
| `keys ≈ docs ≈ nReturned` | healthy |
| `keys ≈ docs >> nReturned` | the index does not express the whole predicate |
| `keys = 0`, `docs = everything` | no usable index at all |
| `docs = nReturned` with a projection | not covered; add the projected fields and `_id: 0` |
| `docs = 0` | covered query |
| `usedDisk: true` on a `SORT` | the sort spilled past 100 MB |

Inside `$lookup` and `$unionWith`, the nested `executionStats` are per-invocation of the
inner pipeline — multiply before comparing.

## Stage vocabulary

| Stage | Says |
|---|---|
| `COLLSCAN` | no index used |
| `IXSCAN` | index walked; read `indexBounds` to see how much of it |
| `FETCH` | documents loaded; a `filter` here is a predicate the index could not express |
| `PROJECTION_COVERED` | no `FETCH` — the index answered everything |
| `PROJECTION_SIMPLE` / `PROJECTION_DEFAULT` | ordinary projection; `DEFAULT` means expressions are involved |
| `SORT` | blocking in-memory sort; `memLimit`, `totalDataSizeSorted` and `usedDisk` are on this node |
| `SORT_MERGE` | sorted results merged from several index ranges — fine |
| `LIMIT` / `SKIP` | `SKIP` still walks what it skips |
| `AND_SORTED` / `OR` | index intersection or a `$or` fan-out |
| `SHARDING_FILTER` | orphan filtering on a shard |
| `GROUP`, `UNPACK_TS_BUCKET` | SBE group; time-series bucket unpacking |

The presence of a `SORT` stage is the single clearest signal: if the query has a `sort()`
and the plan has a `SORT` stage, no index is providing the ordering.

## Worked example

```
nReturned: 25   totalKeysExamined: 812440   totalDocsExamined: 812440
LIMIT -> SORT { createdAt: -1 } usedDisk: true, totalDataSizeSorted: 903118744
      -> FETCH -> IXSCAN { tenantId: 1, type: 1 }
```

The index served both equality predicates (keys = docs, so the `FETCH` added no filter),
but nothing served the ordering, so the server sorted 812 440 documents — 903 MB, spilled —
to return 25. The fix is the sort field appended to the same index:
`{tenantId: 1, type: 1, createdAt: -1}`, after which the plan is `LIMIT → FETCH → IXSCAN`
with 25 keys and no `SORT`.

The mirror image is a plan that has no `SORT` and still takes seconds:

```
nReturned: 100   totalKeysExamined: 41277903   totalDocsExamined: 41277903
LIMIT -> FETCH filter: { type: { $eq: 'payment.failed' } } -> IXSCAN { createdAt: -1 }
```

Here the planner used the ordering index to avoid a sort and then filtered 41 M documents.
The `filter` inside `FETCH` names the missing leading field: `{type: 1, createdAt: -1}`.

## The plan cache

The server caches a winning plan per query shape. Consequences:

- A query can be fast for most parameter values and slow for one, because the cached plan
  was chosen for a different selectivity.
- A newly created index does not take effect for a cached shape until the cache entry is
  evicted (it is, on index creation, on restart, and when the plan's performance degrades).

```javascript
db.coll.getPlanCache().list()
db.coll.getPlanCache().clear()
```

`hint()` forces an index and is the right tool for a diagnosis, and a liability in
application code: it survives the schema change that made it wrong.

## The profiler and the slow-query log

Every operation over `slowms` (default 100 ms) is already in the `mongod` log with its
`planSummary` and `docsExamined` — read that before turning anything on.

```javascript
db.setProfilingLevel(1, { slowms: 200, sampleRate: 0.5 })
db.system.profile.find({ millis: { $gt: 200 } }).sort({ ts: -1 }).limit(20)
db.setProfilingLevel(0)
```

`system.profile` is a capped collection in the same database and profiling costs write
throughput; use a threshold and a sample rate, and turn it off afterwards. Level 2 (all
operations) on a busy collection is itself an incident.

`db.coll.aggregate([{$queryStats: {}}])` (Atlas M10+) aggregates by query shape rather than
by individual operation, which is the better input for "which shapes matter".

## Pagination

`skip(n)` walks and discards every skipped index entry. Measured on an index that serves
the sort:

| Query | keys examined | ms |
|---|---|---|
| `skip(0).limit(20)` | 20 | 1 |
| `skip(10000).limit(20)` | 10 020 | 7 |
| `skip(49000).limit(20)` | 49 020 | 23 |
| `find({..., date: {$lte: anchor}}).limit(20)` | 20 | 0 |

Page by seeking on the sort key instead, carrying the last key of the previous page.
Include a tiebreaker when the sort key is not unique:

```javascript
db.events.find({
  tenantId, $or: [ { createdAt: { $lt: lastAt } },
                   { createdAt: lastAt, _id: { $lt: lastId } } ]
}).sort({ createdAt: -1, _id: -1 }).limit(20)
```

A total count over a large filtered set is a separate, expensive query — `countDocuments`
runs the predicate. `estimatedDocumentCount` reads collection metadata and takes no filter.

## Query rewrites that beat an index

- One query per item in a loop → `find({_id: {$in: ids}})`, one round trip.
- `$where` or server-side JavaScript → `$expr` with aggregation operators; `$where` cannot
  use an index and is deprecated.
- Unanchored or case-insensitive `$regex` → a collation index, or Atlas Search.
- `$ne` / `$nin` on a selective field → express the positive set where possible; a negation
  scans the index.
- `find().toArray()` over a large result → iterate the cursor, or push the reduction into
  an aggregation so the data never crosses the wire.
- `$or` over different fields → each branch needs its own index, or the whole thing becomes
  a collection scan.

<!-- sources: mongodb-agent-skills, mongodb-docs, awesome-copilot -->
