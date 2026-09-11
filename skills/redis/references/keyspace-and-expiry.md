# Key space, expiry and eviction

Verified against: Redis 8.10.1.

## Contents

- [Key naming](#key-naming)
- [Setting expiry](#setting-expiry)
- [Which commands preserve a TTL](#which-commands-preserve-a-ttl)
- [How a key actually expires](#how-a-key-actually-expires)
- [maxmemory and the eight policies](#maxmemory-and-the-eight-policies)
- [LRU and LFU are approximate](#lru-and-lfu-are-approximate)
- [Reading the eviction and expiry counters](#reading-the-eviction-and-expiry-counters)
- [Scanning the keyspace](#scanning-the-keyspace)
- [Keyspace notifications](#keyspace-notifications)
- [Multiple databases](#multiple-databases)

## Key naming

The convention is `service:entity:id:attribute`, lowercase, colon-separated. It is not
cosmetic: the prefix is what an ACL pattern (`~cache:*`), a `SCAN MATCH`, a metric dimension
and a cluster hash tag all key off.

- Put the tenant first when one instance serves several: `tenant:42:user:7:cart`. That single
  decision is what makes per-tenant ACLs and per-tenant cleanup possible later.
- Keep keys short. The key is stored per entry, appears in every command, in `SLOWLOG`, and in
  the replication stream. A 120-character key on 10M entries is over a gigabyte of names.
- Never use a URL, an email or free text as a key. Extract a stable id, or hash the string and
  keep the original in the value.
- Encode the schema version in the prefix when the value's shape may change
  (`v2:product:8361`); a deploy that changes the payload then cannot read the old one by
  accident, and the old generation expires on its own.
- One convention per service, applied everywhere. Mixed conventions make every future
  `SCAN MATCH` and ACL pattern wrong in a way nobody notices.

## Setting expiry

| Intent | Command |
|---|---|
| Write with a TTL in one round trip | `SET key v EX 300` (seconds) / `PX 300000` (ms) |
| Write with an absolute deadline | `SET key v EXAT <unix-seconds>` / `PXAT <unix-ms>` |
| Update the value, keep the deadline | `SET key v KEEPTTL` |
| Add or replace a TTL on an existing key | `EXPIRE key 300` / `PEXPIRE` / `EXPIREAT` |
| Only extend, only shorten, only if absent | `EXPIRE key 300 GT` / `LT` / `NX` / `XX` (7.0+) |
| Read and set the TTL together | `GETEX key EX 300` |
| Remove the TTL | `PERSIST key` |
| Inspect | `TTL key` (seconds; `-1` no TTL, `-2` no key), `PTTL` |
| Per field of a hash (7.4+) | `HEXPIRE key 300 FIELDS 1 f` / `HPEXPIRE` / `HTTL` / `HPERSIST` |
| Read a hash field and set its TTL, or read and delete (8.0+) | `HGETEX` / `HGETDEL` |

`EXPIRE key 0` and a TTL in the past delete the key immediately.

## Which commands preserve a TTL

This is the single most common silent bug in Redis code: a refresh written as a plain `SET`
makes a key immortal, or a "sliding" session that never actually slides. Measured `[verified]`:

| Sequence | Resulting `TTL` |
|---|---|
| `SET k v EX 100` then `SET k v2` | `-1` — the expiry is gone |
| `SET k v EX 100` then `SET k v2 KEEPTTL` | `100` |
| `SET k v EX 100` then `APPEND k x` | `100` |
| `SET k vvvv EX 100` then `SETRANGE k 1 z` | `100` |
| `SET k v EX 100` then `GETSET k w` | `-1` |
| `SET c 1 EX 100` then `INCR c` | `100` |
| `HSET h f 1`, `EXPIRE h 100`, then `HSET h g 2` | `100` — a new field does not extend the key |
| `SET a v EX 100`, `SET b w`, then `RENAME a b` | `100` on `b` — the TTL travels with the value |
| `HEXPIRE sess 100 FIELDS 1 a` then `HTTL sess FIELDS 2 a b` | `100`, `-1` |

The rule underneath: commands that *replace the whole key* (`SET` without `KEEPTTL`, `GETSET`,
`SET ... GET`) discard the expiry; commands that *modify the existing value* keep it. When in
doubt, re-set the expiry explicitly — an extra `EXPIRE` costs a round trip, an immortal session
key costs memory forever.

## How a key actually expires

Two mechanisms, and the difference is visible in metrics.

- **Lazy**: any access to a logically expired key deletes it and behaves as a miss.
- **Active**: a background cycle samples keys with TTLs from each database and deletes the
  expired ones. It is sampling, not a sweep, so the delay is probabilistic.

Measured with active expiry turned off (`DEBUG SET-ACTIVE-EXPIRE 0`), 300 keys written with
`PX 200` `[verified]`:

```
one second after every key had logically expired:
  DBSIZE                     -> 300
  used_memory                -> unchanged (1582632 -> 1607320)
  EXISTS ex:1                -> 0      and DBSIZE drops to 299
  a full SCAN of the keyspace -> DBSIZE drops to 0
after re-enabling active expiry:
  DBSIZE                     -> 0 within a second
```

Consequences:

- `DBSIZE` and `INFO keyspace` count keys that are already logically gone. A key count that
  does not match your model is not necessarily a bug in the application.
- Expired keys hold their memory until something reaches them. On an instance at its
  `maxmemory` ceiling, that memory is not available for new writes yet — which is why "the TTL
  already passed" does not prevent an OOM error.
- A replica does not expire keys on its own; the primary propagates the deletion. A read on a
  replica of a logically expired key returns empty rather than the value, but `DBSIZE` on the
  replica still counts it.
- Expiry is not an event delivery mechanism unless you turn notifications on — see below.

## maxmemory and the eight policies

`maxmemory` defaults to `0` (unlimited) and `maxmemory-policy` to `noeviction` `[verified]`. An
instance left that way grows until the kernel OOM killer stops it, which loses everything in
memory at once.

| Policy | Candidate set | Behaviour at the ceiling |
|---|---|---|
| `noeviction` | none | Writes fail: `OOM command not allowed when used memory > 'maxmemory'`. Reads still work |
| `allkeys-lru` | every key | Evicts approximately least-recently-used |
| `allkeys-lfu` | every key | Evicts approximately least-frequently-used |
| `allkeys-random` | every key | Evicts at random |
| `volatile-lru` | keys with a TTL | LRU among them |
| `volatile-lfu` | keys with a TTL | LFU among them |
| `volatile-random` | keys with a TTL | Random among them |
| `volatile-ttl` | keys with a TTL | Shortest remaining TTL first |

The trap, measured `[verified]` with `maxmemory 3mb` and 1 KB values:

```
noeviction,   no TTLs  -> write #1078 fails: OOM command not allowed when used memory > 'maxmemory'.
volatile-lru, no TTLs  -> the same error, byte for byte
allkeys-lru,  no TTLs  -> OK; 3000 writes leave DBSIZE 1553 with evicted_keys 1470
```

`volatile-*` with no evictable candidate *is* `noeviction`. Choose deliberately:

- **Pure cache** — `allkeys-lru`, or `allkeys-lfu` when a small hot set matters more than
  recency (LFU resists a scan flushing the cache).
- **Source of truth / queue / session store you cannot lose** — `noeviction`, plus an alert on
  `used_memory` against `maxmemory` well before the ceiling, because reaching it is an outage.
- **Mixed instance** — `volatile-lru` *and* an invariant that every cache key is written with a
  TTL. Verify the invariant rather than assuming it: a single code path writing without `EX`
  turns the policy into `noeviction`.

Leave headroom. Replication backlog, client output buffers, the AOF buffer and a fork for a
background save all need memory that is not counted in your data size; sizing `maxmemory` at
the full instance RAM guarantees an OOM under load.

`CLIENT NO-EVICT on` exempts a connection from *client* eviction (the mechanism that drops
clients whose buffers grow past `maxmemory-clients`), which is worth setting on an
administrative or monitoring connection so it survives the incident it is there to observe
`[verified]`. It has nothing to do with key eviction.

## LRU and LFU are approximate

- Both sample `maxmemory-samples` keys (default 5) and evict the best candidate among them, so
  the eviction order is close to, not equal to, true LRU/LFU. Raising the sample count trades
  CPU for accuracy.
- LFU has a decay: `lfu-decay-time` (minutes) halves counters so yesterday's hot key does not
  stay hot forever, and `lfu-log-factor` controls how quickly the counter saturates.
- `OBJECT FREQ key` returns the LFU counter but errors unless an LFU policy is active:
  `ERR An LFU maxmemory policy is not selected, access frequency not tracked` `[verified]`.
  `OBJECT IDLETIME` is the LRU equivalent and needs a non-LFU policy.
- `redis-cli --hotkeys` works only under an LFU policy, for the same reason.
- Switching policies at runtime is allowed, but the tracking data takes time to become
  meaningful; the server says so in the error above.

## Reading the eviction and expiry counters

`INFO stats` separates the two causes of a key disappearing, which is how you tell a TTL from
an eviction:

- `expired_keys` — deleted because their TTL passed; `expired_keys_active` is the subset the
  background cycle found `[verified]`.
- `expired_subkeys` — hash fields deleted by a field TTL (7.4+).
- `evicted_keys` — deleted to stay under `maxmemory`. **Any non-zero value on an instance you
  treat as a source of truth is data loss**, and on a cache it is the signal to resize or
  lower TTLs.
- `keyspace_hits` / `keyspace_misses` — instance-wide read hit ratio. It aggregates cache
  reads with session, lock, queue and counter traffic, so on a mixed instance the ratio means
  nothing; compute per-prefix ratios in the application if you need them.
- `rejected_connections` — connections refused at `maxclients` (default 10000 `[verified]`).

`INFO memory` adds `maxmemory_policy` so a dashboard can alert on the policy changing under it.

## Scanning the keyspace

`KEYS pattern` walks every key in one command and blocks everything else. It belongs in a
`redis-cli` session on a development box and nowhere else. `SCAN` is the replacement, with
guarantees worth knowing precisely:

- Guaranteed: every element present from the start to the end of a full iteration is returned
  at least once.
- Not guaranteed: no duplicates (a key can appear more than once), and elements added or
  removed mid-iteration may or may not appear. A full iteration over a keyspace that shrank by
  75% mid-run returned no duplicates in one measured run `[verified]`, but the guarantee does
  not promise that — the consumer must be idempotent.
- `COUNT` is a per-call hint, not a page size; the reply can be empty while the cursor is
  non-zero, and the loop must terminate on `cursor == 0` rather than on an empty reply.
- `MATCH` filters *after* the bucket is read, so `SCAN 0 MATCH rare:* COUNT 100` still walks
  the whole keyspace to find a handful of keys. Pattern-matching is not an index.
- `TYPE` narrows the reply server-side (`SCAN 0 TYPE zset`).
- Container variants `HSCAN` (`NOVALUES` in 7.4+), `SSCAN`, `ZSCAN` iterate one large key.
- Scanning a whole keyspace to find work is a design smell: keep a Set or sorted set of the
  keys you will need to revisit.

## Keyspace notifications

Off by default: `notify-keyspace-events` is the empty string `[verified]`. Turning it on takes
a flag string, e.g. `CONFIG SET notify-keyspace-events Ex` for expired-key events on the
`__keyevent@<db>__:expired` channel.

Treat them as a hint, never as a ledger:

- Delivery is Pub/Sub, so at-most-once. A subscriber that is down misses the window entirely.
- The `expired` event fires when the key is actually deleted — lazily on access or by the
  active cycle — not at the moment the TTL passed. The delay is unbounded for a key nobody
  touches.
- The event carries the key name, never the value. A cache invalidation listener that needs the
  old value cannot have it.
- Enabling `K` (keyspace) and `A` (all classes) on a busy instance is a significant publish
  load on the same single thread that serves commands.

If something must reliably react to a key's lifecycle, write an entry to a Stream in the same
transaction or script as the key change.

## Multiple databases

`SELECT n` gives 16 logical databases by default. They share one instance, one memory limit,
one CPU and one eviction policy, and Redis Cluster supports only database 0. They are a
development convenience, not isolation — use a key prefix instead, which survives the move to
Cluster and works with ACL patterns.

<!-- sources: redis-agent-skills, redis-io-docs, redis-oss, awesome-copilot-redis -->
