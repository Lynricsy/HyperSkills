# Replica sets and sharding

Verified against: MongoDB 8.0 / 8.3 documentation and an 8.3.9 single-node replica set.

## Contents

- [Replica-set shape](#replica-set-shape)
- [The oplog window](#the-oplog-window)
- [Read preference](#read-preference)
- [Elections and what the application sees](#elections-and-what-the-application-sees)
- [When to shard, and when not to](#when-to-shard-and-when-not-to)
- [Choosing a shard key](#choosing-a-shard-key)
- [Targeted versus broadcast operations](#targeted-versus-broadcast-operations)
- [Chunks, jumbo chunks and the balancer](#chunks-jumbo-chunks-and-the-balancer)
- [Changing a shard key](#changing-a-shard-key)
- [Operational differences under `mongos`](#operational-differences-under-mongos)

## Replica-set shape

Three data-bearing members is the working minimum: it survives one failure and keeps a
voting majority. Arbiters look like a cheap third vote and are not — a set of two
data-bearing members plus an arbiter has an implicit default write concern of `{w: 1}`,
because the non-arbiters do not outnumber the voting majority, and cannot honour
`w: "majority"` when one data node is down. Sharded clusters also refuse multi-shard
transactions that touch a shard whose set contains an arbiter.

Hidden and delayed members serve backups and human error respectively; neither takes
application reads. `priority: 0` keeps a member from becoming primary — useful for a
member in a distant region whose promotion would move every write across an ocean.

## The oplog window

The oplog is a capped collection; its window is how far a secondary may fall behind, how
long a change-stream consumer may be down, and how long an initial sync may take before it
fails.

```javascript
rs.printReplicationInfo()           // size and the time range it currently holds
rs.printSecondaryReplicationInfo()  // per-secondary lag
```

Any bulk operation — a backfill, an `updateMany`, an index build's oplog entries — consumes
the window faster than the steady state. Check the window before a backfill, not after the
secondaries have fallen out of it.

## Read preference

| Mode | Reads from | Cost |
|---|---|---|
| `primary` (default) | primary only | all load on one node |
| `primaryPreferred` | primary, secondaries if it is down | stale reads exactly when things are worst |
| `secondary` | secondaries only | fails when none are available |
| `secondaryPreferred` | secondaries, primary as fallback | stale reads |
| `nearest` | lowest latency, either role | stale reads, unpredictable which |

Secondaries apply the oplog asynchronously, so any non-primary mode returns data that may
be older than an acknowledged write. `maxStalenessSeconds` (minimum 90) bounds how stale,
it does not eliminate staleness. Reading your own write from a secondary needs causal
consistency in the same session.

Secondary reads do not add write capacity and do not always add read capacity: every
secondary applies the full write workload anyway. They help when the reads are analytical
and can tolerate lag, and when they are tagged to a member that is not also serving the
primary's traffic.

## Elections and what the application sees

During an election, writes fail for a few seconds with
`NotWritablePrimary` / `PrimarySteppedDown`. With `retryWrites` on, the driver absorbs most
of that. What it cannot absorb is a write acknowledged at `w: 1` on the old primary that
was never replicated — that one is rolled back and written to a rollback file on disk.

`rs.stepDown()` is the way to rehearse this against a real deployment.

## When to shard, and when not to

Shard when one of these is true and cannot be fixed another way: the working set no longer
fits in the largest affordable machine's RAM, write throughput exceeds one primary, or the
data must live in specific geographies (zone sharding).

Do not shard to fix a bad index, a bad model or a bad query — sharding multiplies all
three. Vertical scaling, archiving cold data with a TTL index, and fixing the working set
are cheaper, and reversible.

Sharding is close to irreversible in practice: a sharded collection cannot be unsharded
without copying it out and back.

## Choosing a shard key

Four properties, and they trade against each other:

1. **Cardinality** — the number of distinct values bounds the number of chunks. A boolean
   shard key gives two chunks forever.
2. **Frequency** — one value holding most documents produces a jumbo chunk that cannot be
   split.
3. **Monotonicity** — a timestamp or an ObjectId always inserts at the top of the range, so
   one shard takes every write. Hash the key, or prefix it with something that spreads.
4. **Query alignment** — the key should appear in the common queries, or every query
   broadcasts.

The usual answer is a compound key that leads with the tenant, customer or device the
queries filter on and trails with something that spreads within it. Hashed keys spread
perfectly and give up range queries and sorts on that field.

The shard key must be present in every document and, once chosen, is in every index that
must be unique: a unique index on a sharded collection has to be prefixed by the shard key.

## Targeted versus broadcast operations

A query carrying the shard key (or its prefix) goes to one shard. Anything else is a
scatter-gather to every shard, and its latency is the slowest shard's. `explain` on a
`mongos` reports `shards` — count them.

`updateOne`, `deleteOne`, `replaceOne` and `findOneAndUpdate` on a sharded collection must
either include the shard key in the filter or run inside a retryable write or transaction.
Sorts and `$group` over a scatter-gather merge on the `mongos`, which is where a sharded
cluster runs out of memory in a way a replica set does not.

`$lookup` across shards is executed by pulling the foreign side to where it is needed;
between two large sharded collections it is a design smell rather than a tuning problem.

## Chunks, jumbo chunks and the balancer

Default range size is 128 MB. A chunk that exceeds it and cannot be split — because every
document in it has the same shard key value — is a **jumbo** chunk: the balancer will not
move it, so the shard holding it keeps growing. The fix is a shard key with better
frequency characteristics, which means resharding.

The balancer migrates ranges in the background and competes for I/O; it has a window
(`sh.setBalancerState`, balancing window in `config.settings`) for a reason.

## Changing a shard key

- `refineCollectionShardKey` appends fields to an existing key, improving cardinality
  without moving data. Cheap, and usually enough for a jumbo-chunk problem.
- `reshardCollection` rewrites the collection under a new key. It needs roughly 1.2× the
  collection's size free on each shard and runs for as long as the copy takes. Since 8.0 it
  can also redistribute onto the same key (`forceRedistribution: true`) to fill new shards;
  since 8.0.10 it works on time-series collections.

Both are `mongos`-level operations, so they are unavailable on a replica set — which is
the point of getting the key right before sharding.

## Operational differences under `mongos`

- `db.currentOp()` and `killOp` are per-shard; op ids are prefixed with the shard name.
- Collection statistics are aggregated and can hide a skew — check per shard.
- Orphaned documents (left by an interrupted migration) are filtered by `SHARDING_FILTER`
  in the plan; `readConcern: "available"` skips that filter and can return them.
- Change streams opened on a `mongos` cover the whole cluster and merge in cluster-time
  order, which costs latency proportional to the slowest shard.

<!-- sources: mongodb-docs, azure-documentdb-kit, mongodb-agent-skills -->
