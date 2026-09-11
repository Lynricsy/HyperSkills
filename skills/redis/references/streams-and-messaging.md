# Pub/Sub, Streams and queues

Verified against: Redis 8.10.1.

## Contents

- [Choosing a messaging primitive](#choosing-a-messaging-primitive)
- [Pub/Sub](#pubsub)
- [Streams](#streams)
- [Consumer groups](#consumer-groups)
- [Recovering a dead consumer's work](#recovering-a-dead-consumers-work)
- [Trimming](#trimming)
- [Lists as queues](#lists-as-queues)
- [Delayed and scheduled work](#delayed-and-scheduled-work)
- [Observing a queue](#observing-a-queue)

## Choosing a messaging primitive

| Requirement | Primitive |
|---|---|
| Fan-out to whoever is listening right now; losing messages is acceptable | Pub/Sub |
| Every consumer group sees every event, and a restart does not lose the backlog | Stream, one group per consumer role |
| Work queue where each item is handled once, and a crashed worker's item is retried | Stream + consumer group + `XACK` |
| Work queue where losing an item on a crash is acceptable | List with `BLMOVE` into a processing list |
| Priority queue | Sorted set scored by priority, popped with `ZPOPMIN` in a script |
| Delayed / scheduled work | Sorted set scored by due timestamp, moved to a stream when due |

"Exactly once" is not on this list because it does not exist. The reachable design is
at-least-once delivery plus an idempotent handler.

## Pub/Sub

`SUBSCRIBE`/`PSUBSCRIBE`/`PUBLISH`, plus `SSUBSCRIBE`/`SPUBLISH` (shard channels, 7.0+) which
are routed by slot and are the only variant that scales on Cluster.

Properties that decide whether it is usable:

- **At-most-once, no backlog.** A message published while a subscriber is disconnected is gone;
  there is no replay, no offset, no acknowledgement. A deploy that restarts consumers loses
  every message published during the restart.
- **A slow subscriber is disconnected**, not buffered indefinitely:
  `client-output-buffer-limit pubsub 32mb 8mb 60` closes a connection whose backlog exceeds the
  hard limit, or the soft limit for the given seconds. The publisher never learns.
- **`PUBLISH` returns the number of receivers**, which is the only delivery feedback available
  and is not a guarantee that any of them processed it.
- On non-shard channels in Cluster mode, a message is broadcast to every node, so heavy
  Pub/Sub traffic costs cluster-wide bandwidth regardless of where the subscriber is.
- Pattern subscriptions (`PSUBSCRIBE`) are matched per published message against every pattern,
  so a busy channel with many patterns is CPU on the command thread.

Good uses: cache invalidation hints, presence, live dashboards, configuration reloads — all
cases where a missed message is repaired by the next one or by a periodic full refresh.
Keyspace notifications are Pub/Sub, and inherit all of the above
(`references/keyspace-and-expiry.md`).

## Streams

An append-only log. Each entry has an id `<milliseconds>-<sequence>` that only increases, and a
flat field/value map.

```
XADD events * type order.paid order_id 4711        # * = server-assigned id
XADD events MAXLEN ~ 100000 * type order.paid ...  # capped at add time
XLEN events
XRANGE events - +  COUNT 10                        # oldest first
XREVRANGE events + - COUNT 10                      # newest first
XINFO STREAM events
```

- Ids are the natural cursor: store the last processed id and resume with
  `XRANGE events (<last-id> +`.
- An explicit id must be greater than the current maximum; `XADD` rejects a smaller one, which
  is how a stream stays ordered even with client-assigned ids.
- `XDEL` removes an entry's content but the id is consumed and the stream's structure (radix
  tree macro-nodes) may not shrink until a rewrite. Streams are for append, not for deletion.
- A stream is one key, so it is one slot and one shard. Partition by writing to
  `events:{shard-n}` if throughput exceeds one core.
- Entries carry no schema. Put a `type` field in every entry and version it, because consumers
  written months apart will read the same stream.

## Consumer groups

A group is a named cursor plus per-consumer pending lists over one stream.

```
XGROUP CREATE events fulfilment 0 MKSTREAM     # 0 = from the start, $ = only new entries
XREADGROUP GROUP fulfilment worker-3 COUNT 10 BLOCK 5000 STREAMS events >
# ... do the work ...
XACK events fulfilment <id>
```

- `>` means "entries never delivered to this group". Any other id means "my own pending
  entries from that id on" — that is the recovery read, not the normal read.
- Delivery is **at-least-once**. An entry handed out stays in the consumer's Pending Entries
  List until `XACK`. If the worker dies after the side effect but before the ack, the entry is
  redelivered and the side effect happens twice.
- Therefore the handler must be idempotent *before* the ack is wired up: a
  `SET done:<entry-id> 1 NX EX <n>` guard, an idempotency key on the downstream call, or a
  unique constraint at the destination.
- Ack after the side effect succeeds, never before. Acking first converts at-least-once into
  at-most-once silently.
- `XINFO GROUPS events` reports `pending`, `last-delivered-id`, `entries-read` and `lag`
  `[verified]`. `lag` is the queue depth to alert on; `pending` growing without bound means
  consumers are claiming and not acking.
- Multiple groups over one stream are independent: an analytics group and a fulfilment group
  each see every entry, with separate cursors.
- `NOACK` in `XREADGROUP` skips the pending list entirely — at-most-once with extra steps.
  Use it only for telemetry.

Measured `[verified]`: after `XREADGROUP ... COUNT 2` on a three-entry stream,
`XPENDING events fulfilment` reports both delivered ids still pending, and
`XAUTOCLAIM events fulfilment other-consumer 0 0` transfers both to another consumer.

## Recovering a dead consumer's work

A crashed consumer's entries stay in its PEL forever unless something claims them. Nothing does
this automatically.

```
XPENDING events fulfilment                              # summary: count, id range, per consumer
XPENDING events fulfilment - + 10 worker-3              # detail: idle ms, delivery count
XAUTOCLAIM events fulfilment worker-9 60000 0 COUNT 50   # claim entries idle > 60s
```

- `XAUTOCLAIM` (6.2+) replaces the `XPENDING` + `XCLAIM` loop and returns a cursor plus the
  claimed entries, and a third element listing ids that no longer exist (deleted from the
  stream while pending) so they can be acked away.
- Run it on a schedule from every consumer, not from a special reaper process — a reaper is
  another thing that can be down.
- Set the min-idle-time above the handler's worst-case duration, or a healthy slow worker gets
  its entry stolen and the work runs twice.
- `XPENDING`'s delivery count is the poison-message signal: an entry delivered five times is
  failing deterministically. Route it to a dead-letter stream and `XACK` it, otherwise it
  blocks the retry budget forever.
- `XGROUP DELCONSUMER` removes a consumer and *drops* its pending entries — claim them first.

## Trimming

A stream never shrinks by itself. Choose one and implement it:

- `XADD key MAXLEN ~ <n> *` — approximate cap at write time, cheap because it only frees whole
  macro-nodes. The exact form (`MAXLEN <n>`, no `~`) costs more and is rarely needed.
- `XADD key MINID ~ <ms-timestamp> *` — retain by age, which is usually what a time-series
  stream wants.
- `XTRIM key MAXLEN|MINID ...` from a periodic job when the producer cannot be changed.
- `LIMIT` bounds the work one trim does, so a backlog is cleared over several calls instead of
  one long block.

Trimming ignores consumer groups: entries can be trimmed away while still pending. Set the
retention above the worst-case consumer lag, and alert on `lag` so the gap is visible before
data is lost.

## Lists as queues

A List is a queue only if losing an item on a consumer crash is acceptable.

```
# producer
LPUSH queue:jobs <payload>

# at-most-once consumer  — the item is gone the instant it is read
BRPOP queue:jobs 5

# reliable-ish consumer — the item is parked where it can be found again
BLMOVE queue:jobs queue:jobs:processing:<worker> RIGHT LEFT 5
# ... work ...
LREM queue:jobs:processing:<worker> 1 <payload>
```

- The `BLMOVE` form needs a reaper: a job that finds processing lists whose worker is gone and
  moves their contents back. That reaper is exactly the machinery a consumer group already has,
  which is why a Stream is the better answer when the change is affordable.
- `LREM` matches by value, so two identical payloads are indistinguishable. Put a unique id in
  every payload.
- A List gives no delivery count, no idle time, no per-consumer view and no lag metric. There is
  no way to answer "what is stuck" other than reading the lists.
- `BLPOP`/`BRPOP`/`BLMOVE` must be on a dedicated connection: on a multiplexed connection they
  stall every other caller sharing it, and a pool leases one connection for the whole block.
- Always pass a timeout. A zero timeout blocks forever and hides a dead producer.

## Delayed and scheduled work

A sorted set scored by the due timestamp, plus a mover:

```
ZADD due <run-at-ms> <job-id>
# every tick, in one script:
ids = ZRANGEBYSCORE due 0 <now-ms> LIMIT 0 100
for each id: XADD jobs * id <id>
ZREM due <ids...>
```

The read and the removal must be in one script, or two movers enqueue the same job. The job
payload lives in a Hash keyed by id; the sorted set holds only ids so the score index stays
small.

## Observing a queue

| Question | Command |
|---|---|
| How far behind is each group | `XINFO GROUPS <stream>` → `lag`, `pending` |
| Who is stuck, and for how long | `XPENDING <stream> <group> - + 20` → idle ms, delivery count |
| Is anything blocking | `INFO clients` → `blocked_clients` |
| Is the stream unbounded | `XLEN`, `MEMORY USAGE <stream>` |
| Are consumers even connected | `XINFO CONSUMERS <stream> <group>` → `inactive`, `pending` |
| List queue depth | `LLEN queue:jobs`, plus `LLEN` on every processing list |

Alert on `lag` and on the oldest `XPENDING` idle time. A queue's length alone does not
distinguish a fast queue from a stalled one.

<!-- sources: redis-agent-skills, redis-io-docs, lude-kit-redis -->
