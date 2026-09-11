# Durable Objects

Verified against: workerd 1.20260910.1, wrangler 4.131.0. This file is the runtime; declaring,
renaming, deleting and transferring a class is a separate topic in the router.

## Contents

- [What a Durable Object actually gives you](#what-a-durable-object-actually-gives-you)
- [Modelling and the shard key](#modelling-and-the-shard-key)
- [Getting a stub](#getting-a-stub)
- [Storage: SQL and the key-value API](#storage-sql-and-the-key-value-api)
- [Gates, blockConcurrencyWhile and atomicity](#gates-blockconcurrencywhile-and-atomicity)
- [Alarms](#alarms)
- [WebSockets and hibernation](#websockets-and-hibernation)
- [Limits that shape the design](#limits-that-shape-the-design)

## What a Durable Object actually gives you

One globally unique, single-threaded instance per id, with storage co-located with the
compute. That buys three things nothing else on the platform offers: serialised access to a
piece of state, a place to put a lock or a counter, and per-entity scheduled work.

Use one when the requirement is coordination or strong consistency: chat rooms, multiplayer
matches, collaborative documents, inventory, bookings, per-tenant or per-user state, long-lived
WebSocket connections, per-entity timers.

Do not use one for stateless request handling (a plain Worker is cheaper and more parallel),
for maximum global read distribution (that is KV or the CDN), or for high fan-out independent
work (that is Queues).

## Modelling and the shard key

The id is the design. Model one object per **coordination atom** — the thing whose state must
be consistent with itself:

| Requirement | Object per | Not |
|---|---|---|
| Chat room membership and history | room | one `ChatService` |
| Per-team API quota | team | one `QuotaService` |
| Seat inventory for an event | event | one `Inventory` |
| Per-user session state | user | one `Sessions` |

The reason is throughput, not taste: an individual object has a soft limit of about **1,000
requests per second** and returns `overloaded` once its queue fills. A single global object is
a bottleneck with a documented ceiling. If one atom is genuinely hotter than that, shard it
deliberately (a parent object that routes to N children, with the child count in its own
storage) rather than hoping.

## Getting a stub

```ts
// Deterministic, derived from a name — the default choice
const stub = env.ROOM.getByName("room-123");

// Equivalent long form
const id = env.ROOM.idFromName("room-123");
const stub = env.ROOM.get(id);

// Unique id — you must persist the string yourself or the object is unreachable
const id = env.ROOM.newUniqueId();
await env.INDEX.put(key, id.toString());
```

`getByName()` and `idFromName()` are the same routing; pick one and use it consistently.
`newUniqueId()` without storing `id.toString()` somewhere durable creates an object nobody can
find again.

Call RPC methods on the stub rather than routing through `fetch()`; this needs
`compatibility_date` ≥ **2024-04-03**. `[official]`

```ts
import { DurableObject } from "cloudflare:workers";

export class Room extends DurableObject<Env> {
  async join(playerId: string): Promise<number> {
    this.ctx.storage.sql.exec(
      "INSERT INTO players (id) VALUES (?) ON CONFLICT(id) DO NOTHING", playerId);
    return this.ctx.storage.sql.exec<{ n: number }>(
      "SELECT count(*) AS n FROM players").one().n;
  }
}
```

Bindings inside the class come from `this.env`, and the state object is `this.ctx` — `env` as a
free variable and `this.state` are both stale patterns.

## Storage: SQL and the key-value API

SQLite-backed objects expose both APIs over the same database.

```ts
// SQL — synchronous, the right default for anything relational or countable
this.ctx.storage.sql.exec("INSERT INTO events (ts, kind) VALUES (?, ?)", Date.now(), kind);
const rows = this.ctx.storage.sql.exec<Row>("SELECT * FROM events WHERE kind = ?", kind).toArray();
const one = this.ctx.storage.sql.exec<{ n: number }>("SELECT count(*) AS n FROM events").one();

// Key-value — async, fine for a handful of scalars
await this.ctx.storage.put("config", { theme: "dark" });
const config = await this.ctx.storage.get<Config>("config");
await this.ctx.storage.delete("config");
```

Create the schema once, in the constructor, guarded by `blockConcurrencyWhile`:

```ts
constructor(ctx: DurableObjectState, env: Env) {
  super(ctx, env);
  ctx.blockConcurrencyWhile(async () => {
    this.ctx.storage.sql.exec(`CREATE TABLE IF NOT EXISTS players (id TEXT PRIMARY KEY)`);
  });
}
```

`storage.put()` accepts structured-clone values, so `Map` and `Set` are fine there; SQL bound
parameters are not structured clone and take only the SQL API's scalar types — encode objects
explicitly. SQLite-backed objects also get Point-in-Time Recovery over the last 30 days, which
covers both SQL and key-value data.

**Persist before caching.** Write to storage, then update the in-memory copy. An object can be
evicted or reset between requests, and an in-memory value that was never written is simply
gone — with no error anywhere.

## Gates, blockConcurrencyWhile and atomicity

The runtime provides input and output gates. While a storage operation is in flight, incoming
events are deferred (input gate) and outgoing responses are held until writes are durable
(output gate). That is why a plain `get` → mutate → `put` inside one Durable Object method is
already atomic with respect to other requests to the same object, and why you do not need a
lock for it.

What breaks that: an `await` on **external** I/O in the middle of a related pair of writes. A
`fetch()` between two `put`s opens a window in which another event can interleave. Group
related writes with no foreign await between them.

`blockConcurrencyWhile()` blocks every other event on the object, including new requests. It
is correct for constructor-time initialisation and for a genuinely exclusive critical section.
It is wrong per request — that serialises everything and destroys throughput — and wrong across
a `fetch()` or any external call, where it converts a slow dependency into an unavailable
object.

## Alarms

```ts
await this.ctx.storage.setAlarm(Date.now() + 60_000);   // replaces any pending alarm
await this.ctx.storage.deleteAlarm();

async alarm(): Promise<void> {
  // retried on failure — must be idempotent
}
```

Three properties decide whether an alarm design is correct:

1. **One alarm per object.** `setAlarm()` replaces; it does not enqueue. Re-arming on every
   incoming request pushes the deadline out forever, which reads as "the alarm never fires".
2. **At-least-once.** A throwing handler is retried with backoff and starts from the top, so a
   loop that emits side effects will re-emit the ones it already did. Record progress — a
   `settled_at`, a cursor, a per-item marker — in the same storage write as the side effect's
   precondition, and make the handler a no-op on replay.
3. **15 minutes of wall time** per alarm invocation, with the usual CPU budget. Long work gets
   chunked across re-armed alarms or handed to a Queue.

Idempotency across a queue boundary cannot be achieved by storage alone: send an
`idempotencyKey` on the message and let the consumer deduplicate.

## WebSockets and hibernation

Use the Hibernation API, not `ws.accept()`. With hibernation the object is evicted from memory
while idle without disconnecting clients, and **Billable Duration charges stop accruing** — for
a chat room that is idle most of the day, that is the difference between a viable design and a
bill. `[official]`

```ts
export class Room extends DurableObject<Env> {
  async fetch(request: Request): Promise<Response> {
    const pair = new WebSocketPair();
    this.ctx.acceptWebSocket(pair[1]);   // not pair[1].accept()
    return new Response(null, { status: 101, webSocket: pair[0] });
  }

  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer) {
    for (const peer of this.ctx.getWebSockets()) peer.send(message);
  }

  async webSocketClose(ws: WebSocket, code: number, reason: string, wasClean: boolean) {}
}
```

Two consequences of hibernation: the **constructor re-runs** when a hibernated object wakes, so
keep it cheap and side-effect free beyond schema setup; and in-memory per-connection state is
lost, so attach it to the socket with `ws.serializeAttachment()` / `ws.deserializeAttachment()`
rather than a `Map` on the instance. `ctx.getWebSockets()` is how you enumerate connections
after a wake.

Received WebSocket messages are capped at 32 MiB, and each incoming message resets the
object's CPU budget.

## Limits that shape the design

- 10 GB storage per SQLite-backed object; past it, writes fail with
  `database or disk is full: SQLITE_FULL` while reads and `DELETE` keep working. Catch it and
  free space rather than letting it surface as a 500.
- Key and value combined ≤ 2 MB; 2 MB per string/BLOB/row; 100 columns per table; 100 KB SQL
  statement; 100 bound parameters.
- ~1,000 requests/second soft limit per object, then `overloaded`.
- CPU 30 s per request by default, raisable to 5 minutes with `limits.cpu_ms`; wall time
  unlimited while a caller, stream or WebSocket is attached.
- 500 Durable Object classes per account on Paid, 100 on Free. Storage is unlimited per
  account on Paid and 5 GB on Free.
- Legacy key-value-backed objects: 2 KiB keys, 128 KiB values, 50 GB per account.

<!-- sources: cloudflare-skills, cloudflare-docs -->
