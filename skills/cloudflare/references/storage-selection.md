# Choosing a Cloudflare storage product

Verified against: documented limits re-read 2026-09; local behaviour on workerd 1.20260910.1.
The decision is made on **consistency** first and quota second. Picking on familiarity is how a
KV counter reaches production.

## Contents

- [Decision table](#decision-table)
- [Workers KV](#workers-kv)
- [Durable Object storage](#durable-object-storage)
- [D1](#d1)
- [R2](#r2)
- [Queues](#queues)
- [Hyperdrive and external databases](#hyperdrive-and-external-databases)
- [Cache API](#cache-api)
- [Patterns that fail, and their fixes](#patterns-that-fail-and-their-fixes)

## Decision table

| Requirement | Use | Why not the obvious alternative |
|---|---|---|
| Read-heavy config, feature flags, allow/deny lists | KV | a DO would serialise reads that need no ordering |
| Counter, quota, rate limit, lock, lease, sequence | Durable Object | KV has no atomic increment and accepts 1 write/s per key |
| Relational queries, joins, reporting per tenant | D1 (one per tenant) | a DO's SQLite is per object and not queryable across objects |
| Blobs, uploads, backups, large exports | R2 | KV caps values at 25 MiB and is not a filesystem |
| Coordination between connected clients (chat, presence, multiplayer) | Durable Object with hibernated WebSockets | KV/D1 cannot hold a connection |
| Decoupling a slow side effect from a request | Queues | `waitUntil` gives 30 s and no retries |
| Multi-step, hours-long, resumable process | Workflows | a Queue message retries the whole step, not the remainder |
| Existing Postgres/MySQL | Hyperdrive | a raw connection per request pays TCP+TLS+auth every time |
| Per-entity scheduled work | Durable Object alarm | Cron Triggers are per Worker, capped at 250/account |
| HTTP response caching in front of an origin | Cache API or cache rules | KV as a response cache adds a store you must invalidate |

## Workers KV

Eventually consistent by design. It stores data centrally and caches it in the locations that
read it.

- A write is **usually** visible immediately in the location where it was made — the docs
  explicitly say not to rely on this — and takes **up to 60 seconds or more** elsewhere as
  cached copies expire.
- **Negative lookups are cached too**, so a newly created key can read as missing for the same
  window, in exactly the places that recently asked for it.
- **1 write per second to the same key**, on Free and Paid alike. Different keys are unlimited
  on Paid; Free allows 1,000 writes/day to different keys.
- No atomic operations and no compare-and-swap. `get` then `put` is a lost-update race, and no
  TTL or retry setting changes that.
- `cacheTtl` defaults to 60 s (minimum 30 s). Raising it is the main read optimisation for
  values that change rarely.
- Value 25 MiB, key 512 bytes, metadata 1,024 bytes, 1,000 operations per Worker invocation.

When write-after-write consistency is needed but KV's read profile is wanted, route **all
writes for a key through one Durable Object** and read from KV everywhere else. That is the
documented pattern, and it keeps the read path cheap.

```ts
// Right use of KV: read-mostly configuration, long cacheTtl, tolerant of staleness
const plan = await env.CONFIG.get(`plan:${team}`, { type: "json", cacheTtl: 3600 });
```

## Durable Object storage

The only strongly consistent, atomically mutable store on the platform. One instance per id,
single-threaded, storage co-located with compute.

- 10 GB per object (SQLite backend), key+value ≤ 2 MB, 2 MB per row.
- ~1,000 requests/second per object, then `overloaded`. The shard key is the scaling decision.
- Input/output gates make a `get`/mutate/`put` inside one method atomic with respect to other
  events on that object — no lock needed, as long as no external `await` sits between related
  writes.
- Point-in-Time Recovery over the last 30 days, covering SQL and key-value data.
- Per-object alarms for scheduled work.

The storage APIs, gating semantics and alarms, and the separate matter of declaring a class,
are covered by the Durable Objects entries in the topic router.

## D1

SQLite as a service, designed for **horizontal scale-out across many small databases** — per
tenant, per user, per entity — not one large one.

- 10 GB maximum per database and **that ceiling cannot be raised**. 500 MB on Free.
- Each database is backed by a single Durable Object and processes **one query at a time**.
  Throughput is the reciprocal of query duration: ~1,000 queries/second at 1 ms, ~10/second at
  100 ms. Too many concurrent requests queue and then return `overloaded`.
- 100 columns per table, 2 MB per row/string/BLOB, 100 KB per SQL statement, 100 bound
  parameters, 30 s per query (which also caps an entire `batch()`).
- Bulk `UPDATE`/`DELETE` over hundreds of thousands of rows exceeds execution limits. Chunk it
  — roughly 1,000 rows per statement — and drive the loop from outside.
- Read replication requires the **Sessions API**: `env.DB.withSession(bookmark)`. Without it
  every query goes to the primary. A session gives sequential consistency across replicas;
  carry `session.getBookmark()` between requests (a header works) to continue it. Replica lag
  is otherwise unbounded.
- Time Travel gives point-in-time recovery for 30 days (Paid) and 10 restores per 10 minutes.
- Index the columns you filter on; an unindexed `WHERE` on a 10 GB database is the usual cause
  of a slow-query-driven `overloaded`.

## R2

S3-compatible object storage with no egress fee, strongly consistent per object.

- Object up to 5 TiB (4.995 TiB in practice); 4.995 GiB per single-part upload; multipart up
  to 10,000 parts.
- **1 concurrent write per second to the same object key**; beyond that, HTTP 429. R2 is not a
  mutable record store.
- Key 1,024 bytes, custom metadata 8,192 bytes, 1,000,000 buckets per account, 50 bucket
  management operations/second per bucket.
- The `r2.dev` subdomain is rate limited and bandwidth throttled and is for testing only.
  Production traffic goes through a custom domain, which also gives cache control, Workers in
  front, and URL-level analytics.
- The Cloudflare REST API for R2 allows 1,200 requests per 5 minutes account-wide — use the
  S3-compatible API or the Workers binding for object operations and keep REST for management.

## Queues

At-least-once delivery, push or pull consumers.

- Message 128 KB (including ~100 bytes of internal metadata); 100 messages or 256 KB per
  `sendBatch`; 5,000 messages/second per queue, beyond which `send` throws `Too Many Requests`.
- Consumer defaults: `max_batch_size` 10, `max_batch_timeout` 5 s, `max_retries` 3. **With no
  `dead_letter_queue`, messages that exhaust their retries are discarded.** Configure one.
- Retention defaults to 4 days, configurable 60 s–14 days, fixed at 24 h on Free. Backlog cap
  25 GB per queue, then `Storage Limit Exceeded` on send.
- 250 concurrent push-consumer invocations; 15 minutes wall time per invocation; CPU raisable
  to 5 minutes with `limits.cpu_ms`.
- At-least-once means consumers must be idempotent. Send an `idempotencyKey` derived from the
  work, not from the send time.
- Match the message body to `contentType`: `json` needs JSON-compatible data, `v8` accepts
  `Map`/`Date`, `bytes` needs an `ArrayBuffer`.

## Hyperdrive and external databases

Hyperdrive keeps a regional connection pool in front of an external Postgres or MySQL, removing
the per-request TCP + TLS + auth handshake (often 300–500 ms). Requires `nodejs_compat`.

```ts
import { Client } from "pg";
const client = new Client({ connectionString: env.HYPERDRIVE.connectionString });
```

Create a client **per request** and let Hyperdrive own the pooling; a module-scope client is
both a cross-request I/O object and a fight with the pool. Never hardcode the upstream
connection string next to a Hyperdrive binding — that bypasses it silently.

## Cache API

The Cache API and cache rules cache HTTP responses at the edge and are the cheapest way to
avoid recomputing a response. They are per-location, not global, and keyed by request. Use them
for response caching; use KV when the value is not a response, or when you need the same value
in every location without each one paying a miss.

## Patterns that fail, and their fixes

| Pattern | Failure | Fix |
|---|---|---|
| KV `get` → `+1` → `put` counter | lost updates; 429 past 1 write/s on the key; regions disagree for up to 60 s | Durable Object per counted entity |
| KV as a lock or lease | no CAS, no atomicity | Durable Object, or a D1 conditional update |
| One global Durable Object fronting a service | `overloaded` at ~1,000 req/s | shard by the coordination atom |
| One D1 database for all tenants | one query at a time, 10 GB hard ceiling | one database per tenant |
| R2 object updated per request | 429 on the same key | append distinct keys, or aggregate in a Durable Object and flush |
| `waitUntil` for a slow third-party call | 30 s budget, no retries, no visibility | Queue with a DLQ |
| A queue step that must resume where it stopped | a retry re-runs the whole batch | Workflows, whose completed steps are persisted |
| Local test passes, production loses writes | local KV is read-after-write consistent | test the consistency assumption against `--remote`, or design it away |

<!-- sources: cloudflare-docs, cloudflare-skills -->
