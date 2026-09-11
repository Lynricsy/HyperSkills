# Connections, cursors and driver behaviour

Verified against: MongoDB 8.3.9 server parameters; driver behaviour as documented for the
current major versions.

## Contents

- [One client per process](#one-client-per-process)
- [The connection arithmetic](#the-connection-arithmetic)
- [Sizing the pool](#sizing-the-pool)
- [Timeouts](#timeouts)
- [Short-lived runtimes](#short-lived-runtimes)
- [What to monitor](#what-to-monitor)
- [Cursors](#cursors)
- [The error taxonomy](#the-error-taxonomy)
- [ODMs](#odms)

## One client per process

A `MongoClient` owns a pool per server, a topology monitor, and background threads.
Constructing one per request means every request pays TCP + TLS + authentication
(50–500 ms), leaves the pool cold, and multiplies the server's connection count by the
request rate. The symptoms are connection churn, `ConnectionPoolCleared`, and server
selection timing out while the server itself looks idle.

Create it at module scope, connect once, never close it except on shutdown. In a serverless
handler that means outside the handler function, so warm invocations reuse it.

## The connection arithmetic

```
server connections = (maxPoolSize + 2) × replica-set members × application instances
```

The `+2` is the monitoring connections each client keeps per member; they are not part of
the pool and are easy to forget. Each connection costs roughly 1 MB of server RAM even
while idle.

A concrete failure: `maxPoolSize: 500`, 24 pods, 3 members → 36 144 potential connections
against a server that will not accept them. Confirm the ceiling from the other side:

```javascript
db.serverStatus().connections   // current, available, totalCreated, active
```

`totalCreated` climbing steadily in steady state is churn, not growth.

## Sizing the pool

Start from concurrency, not from a number in a blog post:

```
pool ≈ peak concurrent operations per instance × average operation duration + 20 %
```

Defaults are `maxPoolSize: 100`, `minPoolSize: 0`. Leave them alone unless there is a
measurement. Rough starting points by shape:

| Shape | `maxPoolSize` | `minPoolSize` | Why |
|---|---|---|---|
| Long-running API server | 50–100 | 10–20 | pre-warmed connections absorb spikes |
| Analytical / batch | 10–20 | 0–5 | few concurrent operations, long ones |
| Serverless function | 3–5 | 0 | every instance has its own pool |

Synchronous drivers (PyMongo, the Java sync driver) need a pool at least as large as the
thread pool, because a thread blocks while it holds a connection. Asynchronous drivers
(Node, Motor) get by with far fewer.

Raising `maxPoolSize` only helps when the wait queue is non-empty **and** the server is not
saturated. When the server is saturated, a bigger pool converts a queue in the client into
contention on the server. Fix the query instead.

## Timeouts

| Option | What it bounds | Getting it wrong |
|---|---|---|
| `connectTimeoutMS` | TCP + TLS handshake | too low on a distant cluster means constant reconnection |
| `socketTimeoutMS` | inactivity on an established socket | must exceed the slowest legitimate operation, or long queries are killed mid-flight |
| `serverSelectionTimeoutMS` | finding a suitable server | too low turns a two-second election into an outage |
| `waitQueueTimeoutMS` | waiting for a pooled connection | fail fast here rather than queueing without bound |
| `maxIdleTimeMS` | how long an idle connection survives | too low causes churn; must be under any intermediate device's idle timeout |
| `maxTimeMS` (per operation) | server-side execution | the only one the *server* enforces — the others are client-side |

`maxTimeMS` is the one that actually stops work on the server. A client-side timeout
abandons the request; the operation keeps running unless `maxTimeMS` bounds it.

## Short-lived runtimes

In Lambda, Cloud Functions or any per-request container:

- Build the client outside the handler and reuse it across warm invocations.
- `maxPoolSize` 3–5, `minPoolSize` 0, `maxIdleTimeMS` 10–30 s.
- Do not `close()` at the end of the handler — that throws away the reuse.
- The cold-start cost is the handshake; `minPoolSize > 0` only helps if the container
  survives long enough to matter.

## What to monitor

Every driver implements the connection-monitoring specification. The two signals worth
alerting on:

- `ConnectionCheckOutFailed` — the pool is exhausted right now.
- `ConnectionCreated` at a high steady rate — churn; the pool is being thrown away.

Alongside them, the wait-queue size and `serverStatus().connections.current`. A wait queue
with a saturated server means the query is the problem; a wait queue with an idle server
means the pool is the problem.

## Cursors

- A cursor is server-side state. It is killed after `cursorTimeoutMillis` of inactivity —
  verified default 600 000 ms — and the client then sees `CursorNotFound` / *"cursor id not
  found"*.
- `noCursorTimeout()` does not fully save you: a **session** idle for more than 30 minutes
  (verified `localLogicalSessionTimeoutMinutes` = 30) is expired and its cursors are killed
  regardless. Long exports need resumable range-based paging, not a long-lived cursor.
- The usual cause of a dying cursor is per-document work in the loop. Read a batch, do the
  slow work outside the iteration, and come back — or page by `_id` range so a restart
  resumes.
- `batchSize` controls documents per round trip. The first batch of a `find` is capped at
  about 101 documents or 1 MB; later batches are up to 16 MB. Raising it cuts round trips
  and raises per-batch memory.
- Always close a cursor you stop iterating early (`cursor.close()`, or a language construct
  that does it). An abandoned cursor holds server resources until it times out.

## The error taxonomy

| Error | Almost always means |
|---|---|
| `MongoServerSelectionError` / `Server selection timed out` | topology unreachable, or every server is at capacity; read the `reason` in the message |
| `MongoWaitQueueTimeoutError` | the client's own pool is exhausted |
| `ConnectionPoolCleared` | the driver dropped the pool after a network error or a stepdown |
| `NotWritablePrimary` / `PrimarySteppedDown` | election in progress — retryable |
| `WriteConflict` | two transactions touched the same document — retry the transaction |
| `CursorNotFound` | the cursor timed out or its session expired |
| `E11000 duplicate key` | a unique index rejected the write; the message names the index and the key |
| `MongoExpiredSessionError` | the session outlived its timeout, usually a client held for too long |
| `Resulting document after update is larger than 16777216` | a document hit the BSON limit — note the message names no collection |

Distinguish client configuration problems (all of the above) from infrastructure ones (DNS
and SRV resolution, IP allow-lists, TLS trust, authentication mechanism mismatch). If
`mongosh` cannot connect from the same host either, it is not the driver.

## ODMs

Mongoose, Prisma, Spring Data and the rest add their own layer on top of the driver.
The recurring problems:

- The ODM's own connection handling can create a second client, or reconnect on every
  model load. Confirm what `serverStatus().connections.totalCreated` says.
- Schema definitions are enforced in the application, not by the server; add `$jsonSchema`
  to the collection if the invariant matters, and expect the ODM's types and the BSON types
  to disagree (integer versus double is the usual one).
- `populate()` and its equivalents are N queries, not a `$lookup`. Read the generated
  operations before judging the server.
- Automatic index creation on startup (`autoIndex`) builds indexes on every deploy and is
  not what you want in production; manage indexes as migrations.

<!-- sources: mongodb-agent-skills, mongodb-docs, azure-documentdb-kit -->
