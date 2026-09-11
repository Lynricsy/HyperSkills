---
name: mongodb
description: "Guides MongoDB work: document modelling (embed versus reference, array growth, bucketing, subset and extended-reference tradeoffs, schema versioning, $jsonSchema validation), update operators, aggregation pipelines (stage order and pushdown, $lookup cost, $facet, blocking-stage memory), index choice and compound key order, reading explain('executionStats'), transactions and retryable writes, read and write concern, replica-set and shard-key behaviour, time-series collections, Atlas Search and $vectorSearch, driver connection pools and cursor lifetime, and online collection change. Use when designing or reviewing a MongoDB collection or pipeline, when a query got slow, when explain shows COLLSCAN or an in-memory SORT, when documents approach the 16 MB limit, when writes are lost or duplicated across a failover, or when connections exhaust. Do not use for relational schema design or SQL tuning, for Firestore, DynamoDB or other non-MongoDB document stores, or for cloud control-plane operations."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# mongodb

## Scope

Covers MongoDB itself: document modelling and its migration path, CRUD and update
operators, the aggregation pipeline, indexes and `explain`, transactions and durability,
replication and sharding semantics, time-series collections, Atlas Search and vector
search, driver-side connection and cursor behaviour, and authentication, authorisation and
encryption at the database level.

The body is written against **MongoDB 8.0** (the current LTS). Rules that need a rapid
release carry a gate such as `(8.3+)`; 8.3.x is the current rapid release and the version
every measurement quoted below was taken on. Nothing here assumes 9.0, which is still in
alpha.

Not covered:

- Relational schema design, SQL, and the tuning of a SQL engine's planner. Use the
  `postgres` skill.
- Key-value caching and eviction policy. Use the `redis` skill.
- A dedicated search platform — analyzer pipelines, cross-cluster replication, index
  lifecycle management. Use the `elasticsearch` skill. This skill covers Atlas Search and
  `$vectorSearch` because they are queried through the aggregation pipeline.
- Firestore, DynamoDB, CosmosDB's own API and other document stores. Their consistency and
  indexing models differ; no skill in this library covers them, so say so rather than
  transferring MongoDB rules onto them.
- Managed control planes: Atlas cluster tiers and scaling, provider backups and PITR,
  network peering, Atlas billing and alerting, `mongodump` scheduling. No skill in this
  library covers those. Everything below still applies on a managed cluster, but
  `setParameter`, `mongod.conf` and OS-level commands usually will not.
- Atlas Stream Processing and Atlas Data Federation.

## Core rules

1. Establish the deployment before quoting anything version- or platform-gated:
   `db.version()` and `db.hello()` (is it a replica set? a `mongos`?), plus whether it is
   Atlas. `$search` and `$vectorSearch` do not exist outside Atlas or an `mongot`-equipped
   deployment — on a self-managed 8.3.9 they fail with *"Using $search and $vectorSearch
   aggregation stages requires additional configuration. Please connect to Atlas…"*.
2. Model from the read and write paths, not from the entities. List what each endpoint
   returns and what each write touches, then shape documents so the hot path is one
   document. Entity diagrams reproduce the relational model and lose to it.
3. Embed only when you can name the bound on the array. "Usually small" is not a bound;
   product rules ("at most 10 addresses"), enforced by `$jsonSchema maxItems`, are.
4. Every `$push` rewrites the entire document and every index entry that covers it, so the
   cost of appending grows with what is already there. Measured on 8.3.9: 20 000 messages
   appended to one document took 38.5 s against 5.4 s for 20 000 inserts into a child
   collection, and the ratio widens as the array grows.
5. 16 MB is a hard BSON limit and the two failure paths read differently — on insert
   `object to insert too large. size in bytes: 16777241, max size: 16777216`, on update
   `Resulting document after update is larger than 16777216`. The update form names no
   collection, so it is routinely misfiled as a driver bug.
6. Treat ~1 MB, not 16 MB, as the design ceiling. Document size is working-set density:
   MongoDB reads whole documents into cache even when the projection is three fields.
7. Copying a field into many documents (extended reference, denormalised counts) is a
   decision to accept staleness. Write down the refresh path at the same time, or the
   rename that touches every copy becomes an outage.
8. `$jsonSchema` with `bsonType: "int"` rejects a BSON double even when the value is
   integral. `mongosh` narrows integral JS numbers to int32 while the Node driver sends
   doubles, so the validator passes in the shell and fails from the application. Use
   `"number"`, or list the types you accept.
9. Order a compound index Equality → Sort → Range. Measured on 200k documents for
   `find({status, region}).sort({date:-1}).limit(20)`: `{status:1, region:1, date:-1}`
   examined 20 keys and 20 documents; `{date:-1, status:1, region:1}` examined 319; with a
   filter value matching one document the sort-leading index degenerated to 200 000 keys
   and 163 ms while ESR stayed at one key.
10. Two single-field indexes are not a substitute for one compound index. With `{status:1}`
    and `{region:1}` both present the planner picked one and filtered the rest — 50 000
    keys and 50 000 documents — against 12 500/12 500 for `{status:1, region:1}`.
11. An index on `{a:1}` is redundant once `{a:1, b:1}` exists, because a B-tree serves any
    leftmost prefix. Every surviving index is write amplification on each insert and update.
12. A covered query needs the projection to exclude `_id` explicitly. Same query, same
    index: `{date:1}` examined 20 documents, `{_id:0, date:1}` examined none.
13. One compound index may contain at most one array field, and the failure surfaces on the
    *write* — `cannot index parallel arrays [b] [a]` — not when the index is created,
    unless a violating document already exists.
14. A collection accepts at most 64 indexes. Attempt 65 and the server answers
    `add index fails, too many indexes for <ns>`. Well before that, an index that
    `$indexStats` shows at zero accesses is pure write cost.
15. `hideIndex` before `dropIndex`. A hidden index is ignored by the planner (the plan falls
    back to `COLLSCAN` immediately) but still maintained, so unhiding is instant while
    re-creating is not.
16. Judge a plan by `totalKeysExamined` and `totalDocsExamined` against `nReturned`, not by
    milliseconds. `totalDocsExamined == nReturned` with a projection means the query is not
    covered; `usedDisk: true` on a `SORT` stage means the sort spilled.
17. `$lookup` runs a query on the foreign collection for every input document, so an
    unindexed `foreignField` is a full scan per document. Measured with 500 input documents
    against a 200k-document foreign collection: 13 690 ms unindexed, 3 ms after
    `createIndex({name: 1})`.
18. The pipeline optimiser already moves `$match` ahead of `$sort` and through a renaming
    `$project`, and already prunes fields it does not need. A leading `$project` therefore
    buys nothing and usually keeps large fields alive; reshape at the end instead.
19. Blocking stages (`$sort`, `$group`) have a 100 MB in-memory budget. `allowDiskUse`
    defaults to true (6.0+), so the usual symptom is not an error but a spill — treat
    `usedDisk: true` as the signal and fix it with an index or an earlier `$match`. With
    `allowDiskUse: false` the same condition raises *"Sort exceeded memory limit of
    104857600 bytes, but did not opt in to external sorting"*.
20. `$push` and `$addToSet` inside `$group` are unbounded accumulators, and the group's
    result is a single document subject to the same 16 MB limit. Use `$topN`/`$firstN` when
    you want a sample.
21. `skip(n)` walks and discards every skipped index entry: `skip(49000)` examined 49 020
    keys where a range predicate on the sort key examined 20. Page with a seek on the last
    key of the previous page.
22. A transaction has a 60-second default runtime (`transactionLifetimeLimitSeconds`) and
    must be retryable as a unit for `TransientTransactionError` and
    `UnknownTransactionCommitResult` — that is what `withTransaction` provides. No external
    I/O inside one: an HTTP call holds locks and burns the budget.
23. `retryWrites` is what makes a write idempotent across a primary stepdown: the driver
    retries once with a transaction number the server deduplicates. An application-level
    retry cannot know whether the first attempt committed, which is how a payment gets paid
    twice. The same applies to `retryReads`.
24. The implicit default write concern is `{w: "majority"}` unless the set has arbiters and
    the non-arbiters do not outnumber the voting majority. A write acknowledged at `w: 1`
    can be rolled back by an election — choose it deliberately and quote the durability cost
    rather than the latency alone.
25. One `MongoClient` per process, reused. Server-side connections are
    `(maxPoolSize + 2) × replica-set members × application instances` — the `+2` is the
    monitoring connections every client opens per member — and a client per request
    multiplies that by the request rate. Cursors idle past `cursorTimeoutMillis` (600 000 ms)
    are killed, and a session idle past 30 minutes kills its cursors even with
    `noCursorTimeout`.

Paths below are relative to this skill's directory.

## Workflows

### design-or-review-a-document-model

- [ ] Write down the access patterns first: for each screen or endpoint, the fields read,
      the filter, the sort, and the write that follows. Ask for them if they are not in the
      code (`references/data-modeling.md`).
- [ ] For every array in the proposed shape, name its bound and what enforces it. An array
      without a bound becomes a child collection or a bucket, not a `$slice`.
- [ ] Separate hot from cold fields. A document whose cold half is ten times its hot half is
      evicting other documents from cache on every read.
- [ ] Decide each duplicated field explicitly — what refreshes it, how stale it may get, and
      what the rename path costs.
- [ ] Put the invariants that matter into `$jsonSchema`, starting at
      `validationLevel: "moderate"` / `validationAction: "warn"` on an existing collection,
      and check the BSON types against what the driver actually sends.
- [ ] Add a schema version field before you need it; a shape that cannot be identified
      cannot be migrated online.
- [ ] **Gate — measured, not assumed:** run the size and array-length aggregations from
      `references/data-modeling.md` against real data and quote the largest document, the
      longest array, and the projected size after a year.

### diagnose-a-slow-query-or-pipeline

- [ ] Separate slow from blocked first: `db.currentOp({secs_running: {$gt: 3}})` and the
      profiler / slow-query log. A query waiting on a lock or a stepdown is not a plan
      problem (`references/query-plans.md`).
- [ ] Get the plan with real parameters: `.explain("executionStats")`, and
      `"allPlansExecution"` when a plan-cache entry is suspected.
- [ ] Read the three counters together — `nReturned`, `totalKeysExamined`,
      `totalDocsExamined` — and name the stage that inflates them.
- [ ] Look for the four signals that name their own fix: `COLLSCAN`, a `SORT` stage (no
      index serves the ordering), `FETCH` with a `filter` (index does not cover the
      predicate), `usedDisk: true` (spilled).
- [ ] For a pipeline, check stage order and the `$lookup` foreign indexes before anything
      else, then the blocking stages (`references/aggregation.md`).
- [ ] Only then change an index, and pick the shape from the predicate, not from the field
      list (`references/indexing.md`).
- [ ] **Gate — the counters moved:** re-run `explain("executionStats")` and quote
      `totalKeysExamined` and `totalDocsExamined` before and after. A plan that changed
      without moving the counters did not help.

### choose-and-prune-indexes

- [ ] Inventory first: `db.coll.getIndexes()` plus
      `db.coll.aggregate([{$indexStats: {}}])`, and note how long the server has been up —
      `$indexStats` counters reset on restart.
- [ ] Group the real queries by predicate shape, then design one compound index per shape in
      Equality → Sort → Range order rather than one index per field.
- [ ] Delete redundancy: any index that is a leftmost prefix of another, and any index at
      zero accesses over a window long enough to include the monthly jobs.
- [ ] Check the special cases the shape implies — at most one array field per compound
      index, a matching collation, a partial filter written to match the query's predicate
      literally, a TTL index's field being a date (`references/indexing.md`).
- [ ] Build on a live collection knowing what it costs: an index build on a replica set runs
      on each member and holds an exclusive lock only at the start and end, but it competes
      for cache the whole time.
- [ ] **Gate — hidden before dropped:** `hideIndex` each candidate, leave it through a full
      business cycle, confirm no plan regressed, and only then drop.

### make-writes-survive-a-failover

- [ ] Establish the current durability: the connection string's `w`, `journal` and
      `retryWrites`, and `db.adminCommand({getDefaultRWConcern: 1})`
      (`references/transactions-and-durability.md`).
- [ ] Turn `retryWrites` on and remove the hand-rolled retry loops it replaces; they are the
      ones that duplicate.
- [ ] Decide `w` per operation class, not globally: `majority` for anything a user is told
      happened, lower only where a lost write is genuinely recoverable.
- [ ] Wrap genuinely multi-document invariants in `withTransaction`, and move every external
      call out of the callback.
- [ ] Make the callback idempotent anyway — it can run more than once — and give it a
      natural idempotency key rather than relying on the transaction.
- [ ] Check the read side for the same failure: a read from a secondary right after a write
      can precede it. Read from the primary, or use the same session for causal consistency.
- [ ] **Gate — proven against an election:** step the primary down
      (`rs.stepDown()`) while the operation runs, and show no lost and no duplicated write.

### change-a-collection-on-a-live-system

- [ ] Classify the change: additive (new optional field), transformative (shape change), or
      destructive (field removal). Only the first is safe without a version field
      (`references/security-and-migrations.md`).
- [ ] Stamp a `schemaVersion` on writes and make readers tolerate both shapes before any
      data moves.
- [ ] Backfill in bounded batches ordered by `_id`, with a pause between batches, and watch
      replication lag — a fast backfill that outruns the secondaries is an availability
      incident.
- [ ] Keep the validator behind the backfill: `validationAction: "warn"` while both shapes
      exist, tightened to `"error"` only after the last old document is gone.
- [ ] Order the deploy around the application: stop reading a field before you stop writing
      it, and stop writing it before you remove it.
- [ ] Write the rollback down first, and name the steps that have none.
- [ ] **Gate — no old shape left:** a count of documents not matching the new
      `schemaVersion` returns zero, and the validator is at `"error"` with no rejections in
      the log.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Embed versus reference by access pattern, array bounds, bucket/subset/extended-reference/outlier/polymorphic patterns, schema versioning, `$jsonSchema` validation, document size diagnostics, time-series collections | Designing or reviewing a collection shape, or documents are growing | `references/data-modeling.md` |
| Index types and what each operator can use, ESR and its exception, covered queries, multikey and parallel arrays, partial/sparse/wildcard/TTL/text/collation, index budget, `$indexStats`, hide-then-drop | Choosing, auditing or removing indexes | `references/indexing.md` |
| `explain` verbosities and what each gives, stage vocabulary, the counters that matter, plan cache and `allPlansExecution`, the profiler and `currentOp`, pagination rewrites | Holding an `explain` output and deciding what to change | `references/query-plans.md` |
| Stage order and what the optimiser already does, `$lookup` forms and cost, `$unwind`, `$facet` versus `$unionWith`, `$group` accumulators, memory and spilling, `$merge`/`$out`, update operators and oplog size | Writing or fixing an aggregation pipeline or a bulk update | `references/aggregation.md` |
| Sessions, `withTransaction` and the retry contract, transaction limits, retryable writes and reads, read and write concern, causal consistency, change streams and resume tokens | Writes must survive a failover, or a multi-document invariant is at stake | `references/transactions-and-durability.md` |
| Replica-set roles and elections, read preference and staleness, oplog window, shard-key selection, targeted versus broadcast queries, chunk and jumbo behaviour, resharding | Deciding read routing, or the deployment is sharded or about to be | `references/replication-and-sharding.md` |
| Pool sizing and the connection arithmetic, timeouts, serverless and short-lived runtimes, cursor lifetime and batch size, bulk writes, the driver error taxonomy, ODM pitfalls | Connections exhaust, a cursor dies, or the driver behaves unexpectedly | `references/connections-and-drivers.md` |
| Atlas Search index definitions and query operators, `$vectorSearch` and index parameters, hybrid `$rankFusion`/`$scoreFusion`, what is available off Atlas, `$text` and its limits | Building search or semantic retrieval on MongoDB | `references/search-and-vector.md` |
| Authentication and role design, network and TLS, field-level and queryable encryption, auditing, and the online procedure for schema, index and field changes | Hardening a deployment, or changing a collection that is in use | `references/security-and-migrations.md` |

## Output format

When reviewing a model, a pipeline or driver code, group findings by file and lead each with
the location:

```
services/chat/store.js:28 - unbounded - $push into threads.messages rewrites the whole
  document per message and has no ceiling; the busiest threads fail at 16 MB. Move messages
  to their own collection keyed by {threadId, at}; keep a $slice-capped tail if the sidebar
  needs one.
```

Order findings by blast radius: writes that will start failing outright, then correctness
(lost or duplicated writes, stale reads), then performance, then style. For a performance
finding, quote the plan evidence — `totalKeysExamined`, `totalDocsExamined`, `nReturned`,
`usedDisk` — rather than asserting that something is slow, and give the before/after shape.

## Environment

- Reproduce against the same major version as production. A single-node replica set is
  enough for transactions, write concern and plan shapes:
  `docker run -d --rm -p 27017:27017 mongo:8.3 --replSet rs0 --bind_ip_all`, then
  `mongosh --eval 'rs.initiate()'`. Settling a version-gated question by running it beats
  quoting a blog post.
- `$search`, `$vectorSearch` and automated embedding need Atlas or a deployment with
  `mongot`; a plain `mongod` rejects those stages. Say which the user has before writing a
  search pipeline.
- Any MongoDB documentation page serves Markdown by appending `.md` to its path
  (`https://www.mongodb.com/docs/manual/reference/write-concern.md`), which is the cheapest
  way to settle a version gate.
- The profiler (`db.setProfilingLevel`) writes into a capped `system.profile` collection in
  the same database and costs write throughput; turn it on with a threshold, not
  wholesale, and turn it back off.
- If a MongoDB MCP server is connected, the same inspection steps (indexes, `explain`,
  sample documents, slow-query logs) are available through it. Treat every write it can
  perform as requiring explicit confirmation first, and prefer a read-only connection.
