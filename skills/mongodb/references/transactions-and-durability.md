# Transactions, concurrency and durability

Verified against: MongoDB 8.3.9.

## Contents

- [The single-document guarantee](#the-single-document-guarantee)
- [Transactions](#transactions)
- [The retry contract](#the-retry-contract)
- [Limits that abort a transaction](#limits-that-abort-a-transaction)
- [Retryable writes and reads](#retryable-writes-and-reads)
- [Write concern](#write-concern)
- [Read concern](#read-concern)
- [Causal consistency](#causal-consistency)
- [Change streams](#change-streams)

## The single-document guarantee

Every write to a single document is atomic, including writes that touch many fields and
many array elements. Most of what people reach for transactions to do is already covered by
`$inc`, `$push` with `$slice`, `$addToSet`, `$setOnInsert`, `findOneAndUpdate` with an
upsert, and aggregation-pipeline updates that compute the new value from the old one.

Reach for a transaction only when an invariant genuinely spans documents — a ledger's two
sides, a bidirectional embedding, a move between collections. If the model makes that
common, the model is the problem.

## Transactions

```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await accounts.updateOne({ _id: from }, { $inc: { cents: -n } }, { session });
    await accounts.updateOne({ _id: to },   { $inc: { cents:  n } }, { session });
    await entries.insertOne({ from, to, n, at: new Date() }, { session });
  }, { readConcern: { level: "snapshot" },
       writeConcern: { w: "majority" },
       readPreference: "primary" });
} finally {
  await session.endSession();
}
```

Rules that are not negotiable:

- **Every operation takes the `session`.** An operation that forgets it runs outside the
  transaction and commits immediately — a silent partial write.
- **The callback may run more than once.** `withTransaction` retries it on
  `TransientTransactionError`. Anything inside it must be idempotent and must not mutate
  state outside MongoDB.
- **No external I/O inside.** An HTTP call in the callback holds locks and the transaction's
  lifetime budget while a third party is slow, and it will be issued twice on a retry.
- Reads inside the transaction see a snapshot from its start; they do not see other
  sessions' concurrent commits.
- Transactions require a replica set or sharded cluster — never a standalone `mongod`.
- Time-series collections do not accept writes inside a transaction (reads are fine).

## The retry contract

Manual `startTransaction` / `commitTransaction` is where correctness gets lost, because two
error labels must be handled and they mean different things:

| Label | Meaning | Action |
|---|---|---|
| `TransientTransactionError` | the transaction aborted before committing (write conflict, stepdown) | retry the whole transaction from the start |
| `UnknownTransactionCommitResult` | the commit was sent and the outcome is unknown | retry the **commit** — it is idempotent |

`withTransaction` implements both loops. Use it instead of writing them.

Write conflicts are normal: two transactions touching the same document produce
`WriteConflict` on one of them. Transactions wait only 5 ms by default to acquire their
locks, so a contended hot document produces aborts rather than queuing. Shorten
transactions and spread the contention rather than raising timeouts.

## Limits that abort a transaction

| Limit | Default | Symptom |
|---|---|---|
| Runtime (`transactionLifetimeLimitSeconds`) | 60 s (verified) | the transaction is expired and aborted by the periodic cleanup |
| Oplog entry | 16 MB per entry | a transaction writing too much fails to commit |
| WiredTiger cache pressure | — | `TransactionTooLargeForCache`, or a write-conflict abort |
| Lock acquisition | 5 ms | `WriteConflict` |

A long-running transaction also pins the snapshot, which holds history in the cache for
everything else. Keep them to a few documents and a few milliseconds.

## Retryable writes and reads

`retryWrites` is on by default in current drivers, and turning it off is what turns a
stepdown into a duplicated write. With it on, the driver attaches a transaction number and
retries once; the server recognises the number and does not apply the operation twice. An
application-level retry has no such number and cannot tell "the write failed" from "the
acknowledgement was lost".

- Covered: `insertOne`, `updateOne`, `deleteOne`, `findOneAndUpdate`, `bulkWrite` of
  single-document operations, `replaceOne`.
- Not covered: `updateMany`, `deleteMany`. Make those idempotent yourself or drive them
  from a bounded, resumable loop.
- `findOneAndUpdate` stores a pre-image for the retry, which is why it costs more than
  `updateOne`.

`retryReads` is on by default too; the cases where it matters are the same — a network blip
during a failover.

An idempotency key in the document (a unique index on the caller's request id) survives
cases retryable writes do not, such as the application process itself restarting.

## Write concern

The implicit default is `{w: "majority"}` unless the set contains arbiters and the
non-arbiters do not outnumber the voting majority, in which case it is `{w: 1}`
(the server evaluates
`if (#arbiters > 0) AND (#non-arbiters <= majority(#voting-nodes))`). Check what is actually
in force:

```javascript
db.adminCommand({ getDefaultRWConcern: 1 })
```

| Setting | Means | Costs |
|---|---|---|
| `w: 0` | fire and forget | errors are invisible, including duplicate-key |
| `w: 1` | the primary has it in memory | an election can roll it back |
| `w: "majority"` | a majority has it durably in their oplog | one extra network round trip to the slowest of the majority |
| `j: true` | written to the on-disk journal | a disk sync per write |

`w: "majority"` is the right default for anything a user has been told happened. `w: 1` is
a deliberate choice for data that is reconstructible. `wtimeout` bounds the wait but does
**not** undo a write that eventually succeeds — a `wtimeout` error means "unknown", not
"failed".

## Read concern

| Level | Sees | Use for |
|---|---|---|
| `local` (default) | the node's latest data, which may roll back | most reads |
| `available` | same, minus orphan filtering on shards | lowest latency, sharded, tolerant of duplicates |
| `majority` | data that cannot be rolled back | reads that must agree with an acknowledged write |
| `snapshot` | a single point in time across the whole read | multi-statement transactions, consistent reports |
| `linearizable` | reflects all majority-acknowledged writes | single-document reads that must be up to date; requires `maxTimeMS` and only works on the primary |

Reading your own write from a secondary is the classic bug: `secondaryPreferred` after a
write can return the pre-write value. Fix it with `primary` for that read, or with causal
consistency.

## Causal consistency

A session gives read-your-writes across nodes:

```javascript
const session = client.startSession({ causalConsistency: true });
await orders.insertOne(doc, { session });
const back = await orders.findOne({ _id: doc._id }, { session, readPreference: "secondary" });
```

The session carries the cluster time forward, so the secondary waits until it has caught up
past the write. It costs latency on the read, not correctness — which is the trade to make
explicit when someone asks for "reads from secondaries to reduce load".

## Change streams

```javascript
const stream = coll.watch(pipeline, { fullDocument: "updateLookup", resumeAfter: token });
```

- They read the oplog, so the resume token is only valid while the oplog still covers it.
  Persist the token with the work it represents, and handle the resumable-error path by
  falling back to a full resync.
- `fullDocument: "updateLookup"` fetches the current document at lookup time, not the
  document as it was at the change — the two differ under concurrent writes.
  `fullDocumentBeforeChange` needs `changeStreamPreAndPostImages` enabled on the collection.
- The oplog window is the real bound on how long a consumer may be down. Check it with
  `rs.printReplicationInfo()` before assuming a nightly consumer can resume.
- Filter inside the `watch` pipeline rather than in the application; unfiltered streams on a
  busy cluster are expensive on both ends.

<!-- sources: mongodb-agent-skills, mongodb-docs -->
