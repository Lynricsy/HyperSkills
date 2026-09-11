# Document modelling

Verified against: MongoDB 8.3.9 (measurements), MongoDB 8.0 (version gates).

## Contents

- [Start from access patterns](#start-from-access-patterns)
- [Embed or reference](#embed-or-reference)
- [Array growth is the decision that ages worst](#array-growth-is-the-decision-that-ages-worst)
- [Document size and the working set](#document-size-and-the-working-set)
- [Patterns worth naming](#patterns-worth-naming)
- [Schema versioning](#schema-versioning)
- [`$jsonSchema` validation](#jsonschema-validation)
- [Time-series collections](#time-series-collections)
- [Diagnostics](#diagnostics)

## Start from access patterns

The useful input is not an entity-relationship diagram — it is a table of operations:

| Operation | Filter | Sort | Fields returned | Frequency | Write that follows |
|---|---|---|---|---|---|

Fill that in before proposing a shape. Two products with identical entities need opposite
models when one renders a thread and the other renders an activity feed. When the code
exists, read the query call sites; when it does not, ask. A model derived from entities
reproduces the relational schema and then pays `$lookup` for it forever.

`db.serverStatus().opcounters` tells you whether the workload is read- or write-dominated,
which decides how much duplication is affordable.

## Embed or reference

Embed when all three hold:

- the child is meaningless without the parent,
- the parent's hot read needs the child anyway,
- the collection of children has a bound you can state and enforce.

Reference when any of these hold: the child is queried on its own, the relationship is
many-to-many, the children outlive or outgrow the parent, or the two sides are written at
very different rates.

Cardinality alone does not decide it. "Fewer than 100" is not a rule — 100 one-kilobyte
subdocuments and 100 one-megabyte subdocuments are different problems. What decides it is
whether the bound exists at all.

For many-to-many, pick the direction you query most and embed a summary there
(`{userId, displayName}`), leaving the other direction to a query on the referencing field.
Embedding both directions doubles the write path and needs a transaction to stay
consistent; do it only when both directions are hot and the arrays are small.

For trees, parent references (`{_id, parent}` plus an index on `parent`) handle "children
of X"; an array of ancestors handles "everything under X" in one indexed query; a
materialised path handles both at the cost of rewriting descendants on a move. `$graphLookup`
exists for recursive traversal but reads the collection per level, so it is a reporting
tool, not a request-path tool.

## Array growth is the decision that ages worst

Every update to a document rewrites the document, so appending to an embedded array costs
more the longer the array is. Measured on 8.3.9, appending 20 000 messages:

| Write path | Time | Result |
|---|---|---|
| `updateOne({_id}, {$push: {messages: m}})` | 38 526 ms | final `$bsonSize` 977 805 bytes |
| `insertOne({threadId, ...m})` into a child collection | 5 393 ms | — |

Seven times slower at 20 000 elements, and the ratio keeps growing. The 16 MB limit is the
end state, not the problem.

The three fixes, in the order to consider them:

1. **Child collection.** The default for anything append-only and unbounded. Index
   `{parentId: 1, sortKey: -1}` and page it.
2. **Bucket.** Group a fixed number of items per document when reads always want a group —
   a page of trades, an hour of events. Upsert into the current bucket with a guard so the
   array stays bounded:

   ```javascript
   db.trades.findOneAndUpdate(
     { accountId: 123, count: { $lt: 100 } },
     { $push: { history: trade }, $inc: { count: 1 },
       $setOnInsert: { accountId: 123, opened: new Date() } },
     { upsert: true, sort: { opened: -1 } }
   )
   ```

   One read returns one page and the document count drops by the bucket factor. Do not
   bucket when items are randomly accessed by their own id, or when their sizes vary wildly.
3. **Capped tail.** `$push` with `$each` and `$slice` keeps a bounded cache of the most
   recent items beside the authoritative child collection. Verified: 5 000 pushes with
   `$slice: -50` leave exactly 50 elements.

   ```javascript
   db.threads.updateOne(
     { _id: threadId },
     { $push: { recent: { $each: [msg], $slice: -50, $sort: { at: -1 } } },
       $inc: { messageCount: 1 } }
   )
   ```

   This is a cache, not a fix — the history still has to live somewhere.

## Document size and the working set

16 MB is the hard limit and the two errors differ by path:

```
insert: object to insert too large. size in bytes: 16777241, max size: 16777216
update: Plan executor error during update :: caused by ::
        Resulting document after update is larger than 16777216
```

Design for ~1 MB. MongoDB reads whole documents into the WiredTiger cache even when the
projection asks for three fields, so a document carrying a 500 KB cold half evicts other
documents on every hot read. Splitting hot from cold (the subset pattern) is the fix;
projection only saves network bytes unless the query is fully covered by an index.

Signals that the split is overdue: documents routinely over ~200 KB, an array whose length
keeps climbing, reads that only ever need the newest N elements, updates that get slower as
the document grows.

## Patterns worth naming

| Pattern | Use when | Cost you are accepting |
|---|---|---|
| Subset | A large child set where the hot path needs only the top few | The embedded subset needs refreshing |
| Extended reference | A join exists only to fetch two or three fields of the other side | Those fields go stale; renames fan out |
| Computed | An aggregate is read far more often than its inputs change | The computation must be re-run on every input change |
| Bucket | Items are consumed in fixed-size groups | Single-item access gains an indirection |
| Outlier | A small minority of documents are orders of magnitude larger | Read paths need a branch for the overflow flag |
| Polymorphic | Variants share most fields and are always queried together | Validation must be per-variant |
| Attribute | Many sparse, unpredictable optional fields, each searchable | Queries move to `{k, v}` array form with a compound index on `{"attrs.k": 1, "attrs.v": 1}` |
| Approximation | A counter whose exact value nobody acts on | The number is wrong by design; say so in the API |
| Archive | Old data is queried rarely and differently | Two read paths, and a window where a record is in neither |

Every one of these duplicates or defers something. Write the refresh path down beside the
pattern — the failure mode is never the pattern, it is the rename that nobody costed.

## Schema versioning

Add the version field before the first migration, not during it:

```javascript
{ _id: ..., schemaVersion: 2, ... }
```

The online migration is: readers tolerate both shapes → writers emit the new shape →
backfill in batches ordered by `_id` → readers drop the old branch → validator tightened.
Backfill with an aggregation-pipeline update so the server computes the new shape without a
round trip:

```javascript
db.users.updateMany(
  { schemaVersion: { $lt: 2 }, _id: { $gt: lastId, $lte: batchEnd } },
  [{ $set: { fullName: { $concat: ["$first", " ", "$last"] }, schemaVersion: 2 } }]
)
```

Bound each batch, pause between batches, and watch replication lag: a backfill that outruns
the secondaries is an availability incident, not a slow job.

## `$jsonSchema` validation

```javascript
db.createCollection("users", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["email", "schemaVersion"],
    properties: {
      email: { bsonType: "string", pattern: "^.+@.+$" },
      age: { bsonType: ["int", "long", "double"], minimum: 0 },
      addresses: { bsonType: "array", maxItems: 10 }
    }
  }},
  validationLevel: "moderate",
  validationAction: "warn"
})
```

On an existing collection start at `moderate` / `warn` (existing invalid documents are left
alone and violations are logged), then tighten to `strict` / `error` once the backfill is
done.

The trap: `bsonType: "int"` means BSON int32 and rejects a double even when the value is
integral. Verified on 8.3.9 — `insertOne({age: 5})` from `mongosh` passes because the shell
narrows integral JS numbers to int32, while `insertOne({age: Double(5)})` is rejected with
`"reason":"type did not match"`. The Node driver sends JS numbers as doubles, so a validator
that passes in the shell fails from the application. Use `"number"`, or list the BSON types
you accept.

Rejections come back in `errInfo.details.schemaRulesNotSatisfied`, which names the operator
and the offending property; log that field rather than the bare error message.

## Time-series collections

```javascript
db.createCollection("readings", {
  timeseries: { timeField: "ts", metaField: "meta", granularity: "minutes" },
  expireAfterSeconds: 60 * 60 * 24 * 90
})
```

They bucket, compress and index automatically, and are the right answer for append-only
measurements — not the manual bucket pattern.

- `metaField` must be static for a series and of moderate cardinality. A unique id in there
  produces one bucket per document and removes the entire benefit.
- `granularity` (`seconds` / `minutes` / `hours`, or explicit `bucketMaxSpanSeconds` +
  `bucketRoundingSeconds` on 6.3+) must match the ingest rate.
- Constraints that surprise people: single-document updates are rejected outright —
  verified, `updateOne` returns *"Cannot perform a non-multi update on a time-series
  collection"* — and writes are not allowed inside transactions (reads are). Secondary
  indexes on measurement fields are allowed.
- `expireAfterSeconds` on the collection is the retention mechanism; there is no separate
  TTL index to create.

## Diagnostics

```javascript
// Largest documents
db.coll.aggregate([
  { $project: { size: { $bsonSize: "$$ROOT" } } },
  { $sort: { size: -1 } }, { $limit: 10 }
])

// Longest arrays, and how much of the document they are
db.coll.aggregate([
  { $project: {
      total: { $bsonSize: "$$ROOT" },
      arrayLen: { $size: { $ifNull: ["$messages", []] } },
      arraySize: { $bsonSize: { $ifNull: ["$messages", []] } } } },
  { $match: { arrayLen: { $gt: 100 } } },
  { $sort: { arrayLen: -1 } }, { $limit: 10 }
])

// Cache pressure — is the working set resident?
db.serverStatus().wiredTiger.cache
```

<!-- sources: mongodb-agent-skills, mongodb-docs, azure-documentdb-kit, edd-skill -->
