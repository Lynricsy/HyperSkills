# Aggregation pipelines and bulk writes

Verified against: MongoDB 8.3.9.

## Contents

- [What the optimiser already does](#what-the-optimiser-already-does)
- [`$lookup`](#lookup)
- [`$unwind`](#unwind)
- [`$group` and its accumulators](#group-and-its-accumulators)
- [`$facet` and `$unionWith`](#facet-and-unionwith)
- [Memory and spilling](#memory-and-spilling)
- [`$out`, `$merge` and materialised views](#out-merge-and-materialised-views)
- [Update operators and oplog cost](#update-operators-and-oplog-cost)
- [Bulk writes](#bulk-writes)

## What the optimiser already does

Before rewriting a pipeline by hand, know what the server already handles:

- **`$match` moves ahead of `$sort`.** Verified: `[{$sort}, {$match}, {$limit}]` planned an
  `IXSCAN` on the index serving the `$match`.
- **`$match` moves through a renaming `$project`.** Verified:
  `[{$project: {s: "$status"}}, {$match: {s: "shipped"}}]` still used the index on `status`.
- **Unused fields are pruned.** The optimiser reads the whole pipeline and only materialises
  fields some stage references.
- **`$sort` immediately followed by `$limit`** becomes a top-N sort that tracks N values
  instead of sorting everything. The two stages must be adjacent for this.
- **`$match` is absorbed into the initial query**, so index bounds come from it.

What it cannot do: move a `$match` past a `$group` that aggregates the field, or past
`$unwind` for a field the unwind produces, or use an index for anything after the first
blocking stage.

The practical consequences:

- Put `$match` first, always, and make sure an index serves it.
- Do **not** put a `$project` first to "reduce the data". It buys nothing, and it commonly
  keeps large fields alive because the author listed them. Reshape at the end.
- Keep `$limit` adjacent to its `$sort`.

## `$lookup`

`$lookup` executes a query on the foreign collection for each input document. With no index
on `foreignField` that is a full collection scan per document. Measured, 500 input
documents joined to a 200 000-document collection:

| `foreignField` | index | best of 3 |
|---|---|---|
| `_id` | automatic | 6 ms |
| `name` | none | 13 690 ms |
| `name` | `createIndex({name: 1})` | 3 ms |

Index the `foreignField`. Then, in order of effect:

1. `$match` **before** the lookup, to cut the left side.
2. The `pipeline` form with a `$match` inside, to cut the right side. Note that the
   correlated form takes `let` plus `$expr`, and only an `$expr` equality against an
   indexed field gets index bounds:

   ```javascript
   { $lookup: {
       from: "inventory",
       let: { pid: "$productId" },
       pipeline: [
         { $match: { $expr: { $eq: ["$_id", "$$pid"] }, inStock: true } },
         { $project: { _id: 0, name: 1, price: 1 } }
       ],
       as: "product" } }
   ```

3. `$project` last inside the lookup pipeline, so only the needed fields cross.
4. `$unwind` immediately after the lookup when you want one row per match — adjacent, so
   the server can fold it into the lookup instead of building the full array first.

`$lookup` producing an unbounded `as` array runs into the 16 MB document limit like any
other array. A join fanning out to thousands of matches per input document wants
`$unwind` folded in, or a different model.

Persistent heavy `$lookup` between the same two collections is a modelling signal: either
embed a subset of the foreign fields (extended reference) or accept a materialised view via
`$merge`.

## `$unwind`

`$unwind` multiplies the document count by the array length; every stage after it pays.
Filter before it so the `$match` can use an index, and filter again after it to drop the
elements you do not want:

```javascript
[ { $match: { "items.category": "electronics" } },   // indexed, drops whole documents
  { $unwind: "$items" },
  { $match: { "items.category": "electronics" } } ]  // drops the other elements
```

`$unwind` followed by `$group` back to `_id` is almost always a mistake — `$filter`,
`$map`, `$reduce`, `$sum` over an array and the `$firstN`/`$topN` family do the same work
without the multiplication. Use `preserveNullAndEmptyArrays: true` when a document with an
empty array must survive; the default drops it silently, which is a common source of
missing rows.

## `$group` and its accumulators

`$group` only touches the fields its expressions name, so a `$project` before it saves
nothing. What matters is the accumulators:

- `$push` and `$addToSet` are unbounded. The group's output is one document and is subject
  to the 16 MB limit, so `$push: "$$ROOT"` over a large group fails outright or blows the
  memory budget.
- `$topN`, `$firstN`, `$lastN`, `$maxN` (5.2+) take an `n` and are what "give me a sample"
  should be.
- `$count` in a `$group` is `{$sum: 1}`; the `$count` stage is a separate thing.
- `$group` with `_id: null` over a huge collection is a single document being built in
  memory — check it against the limit.

## `$facet` and `$unionWith`

`$facet` feeds **every** input document into **every** branch, and no branch can use an
index of its own, because the input is already a stream. A cheap `{$count}` branch next to
an expensive aggregation branch therefore costs as much as the expensive one.

Split the branches into independent pipelines, joined with `$unionWith` if a single result
set is required:

```javascript
db.orders.aggregate([
  { $match: q }, { $sort: { total: -1 } }, { $limit: 10 },
  { $unionWith: { coll: "orders", pipeline: [ { $match: q }, { $count: "n" } ] } }
])
```

`$facet` is still right when the branches genuinely share expensive upstream work and
differ only in how they summarise it.

## Memory and spilling

Blocking stages (`$sort`, `$group`, `$bucketAuto`, `$setWindowFields`) get 100 MB of memory
each (`internalQueryMaxBlockingSortMemoryUsageBytes`, verified = 104857600).

`allowDiskUse` defaults to true since 6.0, so the usual symptom is not an error — it is a
silent spill. Look for `usedDisk: true` and `totalDataSizeSorted` in the plan. With
`allowDiskUse: false` the same condition raises:

```
Sort exceeded memory limit of 104857600 bytes, but did not opt in to external sorting.
```

Fixes, in order: an index that provides the sort order, an earlier and more selective
`$match`, `$limit` adjacent to the `$sort`, and only then more memory.

## `$out`, `$merge` and materialised views

- `$out` replaces the target collection atomically at the end. It drops the target's
  indexes with it, and must be the last stage.
- `$merge` (4.2+) upserts into the target and keeps its indexes, so it is what incremental
  materialisation needs. `on` must be backed by a unique index.
- A read-only view (`db.createView`) stores a pipeline, not data: every query against it
  runs the pipeline, and only the pipeline's own first `$match` can use an index.

Re-running an expensive report pipeline into a `$merge` target on a schedule beats
optimising it past a point — say so instead of tuning a 22-minute pipeline to 11 minutes.

## Update operators and oplog cost

- `replaceOne(filter, wholeDoc)` writes the entire document to the oplog. An
  aggregation-pipeline update lets the server compute a delta:
  `updateOne({_id}, [{$set: {...}}])`. On a wide document this is the difference between a
  kilobyte and a byte-sized oplog entry, and the oplog is the replication budget.
- `findOneAndUpdate` retains a copy of the pre-image for retryable writes. Use `updateOne`
  when the returned document is not used.
- Aggregation-pipeline updates (`[{$set}, {$unset}, {$replaceWith}]`) can reference the
  document's own fields, which removes a read-modify-write round trip and its race.
- Positional updates: `$` updates the first array element matched by the filter,
  `$[]` updates all, `$[ident]` with `arrayFilters` updates the ones that match. `$` fails
  silently to do what you meant when the filter did not include the array field.
- `$inc`, `$min`, `$max`, `$mul`, `$setOnInsert` and `$addToSet` are atomic on a single
  document — that is the transaction you usually actually need.

## Bulk writes

`bulkWrite` with `ordered: false` lets the server parallelise and continue past a failure;
`ordered: true` (the default) stops at the first error. Batch inserts with `insertMany`
rather than a loop of `insertOne` — the difference is one round trip per batch instead of
per document.

For a backfill, bound each batch by `_id` range, commit, pause, and watch
`rs.printSecondaryReplicationInfo()`. An unbounded `updateMany` over a large collection
produces one oplog entry per document as fast as the primary can write them, which is how
a backfill becomes a replication-lag incident.

<!-- sources: mongodb-agent-skills, mongodb-docs, azure-documentdb-kit -->
