# Data structures, encodings and memory

Verified against: Redis 8.10.1 (`redis:8-alpine`, `redis_mode:standalone`).

## Contents

- [Choosing by access pattern](#choosing-by-access-pattern)
- [String](#string)
- [Hash](#hash)
- [List](#list)
- [Set](#set)
- [Sorted set](#sorted-set)
- [Stream](#stream)
- [JSON](#json)
- [Bitmap, HyperLogLog, Bloom](#bitmap-hyperloglog-bloom)
- [Geospatial](#geospatial)
- [Vector storage](#vector-storage)
- [Encodings and the thresholds that matter](#encodings-and-the-thresholds-that-matter)
- [Big keys](#big-keys)
- [Memory accounting](#memory-accounting)

## Choosing by access pattern

Answer these five before naming a type. The data's shape answers none of them.

1. **How is it read?** Whole value, one field, a rank range, a membership test, a time range.
2. **How does it shrink?** Never, by TTL on the key, by TTL per field, by explicit trim, by
   score range.
3. **Is a single element addressable?** If the code needs one field out of twelve, a
   serialised blob is the wrong container.
4. **How large does it get, and is that bounded by anything?** Unbounded growth in one key is
   the most common Redis production failure.
5. **Must two of these keys change atomically?** That answer forces a script, and in Cluster
   a hash tag.

| Question the code asks | Structure | Why not the obvious alternative |
|---|---|---|
| "give me this whole cached page" | String | — |
| "increment this counter" | String + `INCR` | A Hash field also works (`HINCRBY`) and is cheaper when counters cluster per entity |
| "read/update one field of this object" | Hash | A JSON string forces read-modify-write and loses concurrent updates |
| "the newest 20 of this user's events" | List with `LPUSH` + `LTRIM`, or a sorted set by timestamp | An unbounded List is a memory leak with a nice API |
| "is X in this collection" | Set + `SISMEMBER` | Fetching the collection to test in the client is O(N) on the server |
| "how many distinct X today" (approximate) | HyperLogLog | A Set of 10M ids costs gigabytes; a HLL costs 12 KB |
| "rank / top N / range by score" | Sorted set | — |
| "every consumer must see every event, and survive a restart" | Stream + consumer group | Pub/Sub drops anything published while a subscriber is away |
| "nearest neighbours of this embedding" | RQE `VECTOR` field or a vector set | — |
| "did this user do X on day N" over a year | Bitmap (`SETBIT`/`BITCOUNT`) | 365 Sets of user ids versus 365 bitmaps of `n/8` bytes |

## String

The only type with no internal structure, and the only one where the value can be an integer
Redis will do arithmetic on.

- `SET key value EX n` / `PX n` / `EXAT ts` / `KEEPTTL` / `NX` / `XX` / `GET`. One round trip
  does what people write three commands for; `SET ... NX EX n GET` is the whole lock primitive.
- `INCR`, `INCRBY`, `INCRBYFLOAT`, `DECR` are atomic and create the key at 0. `INCR` on a
  value that is not an integer errors rather than resetting.
- `APPEND` and `SETRANGE` grow the value in place; `SETRANGE` past the end zero-fills, so
  `SETRANGE key 10000000 x` allocates 10 MB in one command.
- `GETRANGE`/`SETRANGE` make a String usable as a fixed-layout record, but a Hash is clearer
  and no more expensive.
- `MGET`/`MSET` batch, and are the multi-key commands most likely to break on Cluster.
- Values are opaque byte strings. Serialisation and deserialisation belong to the application:
  Redis will not parse JSON in a String, and a client that "automatically serialises objects"
  is doing it above the protocol.

## Hash

The default container for an entity whose fields change independently.

- `HSET`/`HGET`/`HDEL`/`HINCRBY`/`HRANDFIELD`. `HGETALL` is O(N) over the whole hash — fine
  for a 12-field session, a latency source for a 50 000-field hash. Use `HMGET` for known
  fields and `HSCAN` to iterate.
- **Per-field TTL (7.4+):** `HEXPIRE key seconds FIELDS n f1 ...`, `HPEXPIRE`, `HPERSIST`,
  `HTTL`. Fields without a TTL report `-1`. `[verified]` A hash carrying field TTLs reports
  `OBJECT ENCODING` as `listpackex` rather than `listpack`.
- **(8.0+)** `HGETEX` reads and sets expiry in one call, `HGETDEL` reads and deletes — the
  two operations previously needing a script.
- The key's own TTL is independent of field TTLs, and adding a field does not extend it
  `[verified]`.

## List

A doubly linked structure of listpack nodes. Good at both ends, bad in the middle.

- `LPUSH`/`RPUSH`/`LPOP`/`RPOP` are O(1); `LPOP key count` pops many in one call.
- `LINSERT`, `LSET`, `LREM` and `LRANGE` over the middle are O(N).
- `LTRIM key 0 n-1` right after the push is what keeps a "recent items" list bounded. Without
  it the list is unbounded, and `LRANGE key 0 -1` then transfers everything.
- `LPOS` finds an element's index without fetching the list.
- `BLPOP`/`BRPOP`/`BLMOVE` block. They belong on a dedicated connection.
- A bare `LPOP` as a queue read loses the message if the consumer dies before finishing; see
  `references/streams-and-messaging.md` for the two correct shapes.

## Set

Unordered, unique. Three encodings, and a real cliff between them.

- `SADD`/`SREM`/`SISMEMBER`/`SMISMEMBER`/`SCARD` are O(1).
- `SMEMBERS` is O(N) and serialises the whole set into one reply. On a 2M-member set this
  blocks the server for tens of milliseconds. `SSCAN` iterates, `SRANDMEMBER key count`
  samples, `SINTERCARD numkeys k1 k2 LIMIT n` answers "do these overlap by at least n" without
  materialising the intersection.
- `SINTER`/`SUNION`/`SDIFF` are O(N) in the inputs and their `*STORE` variants write a new key
  of that size. They are multi-key, so they need a hash tag on Cluster.
- If the members are timestamps or scores in disguise, it is a sorted set.

## Sorted set

Members unique, each with a float score. The workhorse for anything ordered, rate-limited or
time-bucketed.

- `ZADD` with `GT`/`LT`/`NX`/`XX`/`CH` covers "only raise the score", "only insert",
  "tell me whether anything changed" without a read first.
- `ZRANGE key start stop [BYSCORE|BYLEX] [REV] [LIMIT offset count]` replaced the older
  `ZREVRANGE`/`ZRANGEBYSCORE` family; `ZRANGESTORE` writes the slice to another key.
- `ZREMRANGEBYRANK`/`ZREMRANGEBYSCORE` are how a leaderboard or a sliding window stays bounded.
- Deep pagination is O(log N + offset): `ZRANGE key 1000000 1000049` walks. Page by score
  (last seen score as the cursor) when the set is large.
- A sliding-window rate limiter is a sorted set of request timestamps plus
  `ZREMRANGEBYSCORE key 0 <now-window>` then `ZCARD`; put both in a script so the trim and
  the count cannot interleave.

## Stream

An append-only log of entries, each with a monotonic `<ms>-<seq>` id and a flat field map.

- `XADD key * field value ...`; `XADD key MAXLEN ~ 10000 *` caps it approximately and cheaply.
- `XRANGE`/`XREVRANGE` for time-range reads, `XLEN` for size, `XINFO STREAM` for the shape.
- Consumer groups, acknowledgement and recovery are in
  `references/streams-and-messaging.md`. What matters for storage: a stream is not
  self-trimming, so a producer with no `MAXLEN` and no `XTRIM` job is an unbounded key.
- Entries are immutable; `XDEL` removes an entry but does not reclaim the id.

## JSON

Available when `MODULE LIST` reports `ReJSON` — bundled in the 8.x official image `[verified]`.

- `JSON.SET key $.path value`, `JSON.GET key $.a.b`, `JSON.ARRAPPEND`, `JSON.NUMINCRBY`.
  Path-level updates without rewriting the document, which is the one thing a JSON string in a
  String cannot do.
- Choose JSON over a Hash when the document is genuinely nested or has arrays. A flat object
  is cheaper and simpler as a Hash, and a Hash supports per-field TTL, which JSON does not.
- RQE can index JSON paths (`ON JSON`, `$.field AS alias`), which is the usual reason to pick
  JSON over a Hash for searchable documents.

## Bitmap, HyperLogLog, Bloom

All three trade exactness for size, and all three are Strings or module types rather than
distinct "collections".

- **Bitmap**: `SETBIT`/`GETBIT`/`BITCOUNT`/`BITPOS`/`BITOP`/`BITFIELD` over a String. Ideal
  for dense per-id booleans ("did user N do X today"). A sparse high id allocates everything
  below it, so map ids to a dense range first.
- **HyperLogLog**: `PFADD`/`PFCOUNT`/`PFMERGE`. Fixed ~12 KB per key, standard error ~0.81%.
  Use it for distinct counts you will never need to enumerate; it cannot answer membership.
- **Bloom filter** (`MODULE LIST` shows `bf`, bundled on 8.x `[verified]`):
  `BF.RESERVE key error_rate capacity`, `BF.ADD`, `BF.EXISTS`, `BF.MADD`/`BF.MEXISTS`. No false
  negatives, tunable false positives, no deletion. The standard front-door for cache
  penetration. Size it at reserve time: an under-sized filter scales out and its error rate
  degrades.

## Geospatial

`GEOADD`/`GEOSEARCH`/`GEODIST` are a sorted set with geohash scores, so every sorted-set rule
applies — including that the whole index is one key on one slot. `GEOSEARCHSTORE` writes
results elsewhere. For polygon queries, or geo combined with attribute filters, use an RQE
`GEO`/`GEOSHAPE` field instead (`references/search-and-vectors.md`).

## Vector storage

Two independent mechanisms; `MODULE LIST` shows them as separate engines (`search` and
`vectorset`) `[verified]`.

- **RQE `VECTOR` field** — declared inside `FT.CREATE` alongside `TEXT`/`TAG`/`NUMERIC`, so one
  query can filter by attributes and rank by similarity. Choose this whenever the search is not
  purely vector.
- **Vector set (8.0+)** — `VADD key VALUES dim v1 v2 ... element`, `VSIM`, `VDIM`, `VINFO`,
  `VREM`. A standalone HNSW collection with no schema. `VINFO` on a freshly created set reports
  `quant-type int8` and `hnsw-m 16` `[verified]`: quantisation is on by default and lossy, so
  pass `NOQUANT` when exactness matters and accept the memory.

## Encodings and the thresholds that matter

`OBJECT ENCODING key` reports the representation. Small collections use a compact contiguous
listpack; past a threshold Redis converts to the general structure and **never converts back**,
even if the collection shrinks again.

Defaults measured on 8.10.1 `[verified]` — read them per instance with `CONFIG GET`, because
these are exactly the numbers that get changed and mis-remembered:

```
hash-max-listpack-entries  512      hash-max-listpack-value   64
zset-max-listpack-entries  128      zset-max-listpack-value   64
set-max-intset-entries     512      set-max-listpack-entries  128
list-max-listpack-size     -2       (size-based: 8 KB per node, not an entry count)
```

Measured transitions `[verified]`:

| Case | `OBJECT ENCODING` |
|---|---|
| Hash, 128 fields / 129 fields | `listpack` / `listpack` (the entry limit is 512, not 128) |
| Hash, one 64-byte value / one 65-byte value | `listpack` / `hashtable` |
| Hash with any field TTL set | `listpackex` |
| Set of integers only | `intset` |
| Same set after adding one non-integer | `listpack` |
| Set, 129 string members | `hashtable` |
| Sorted set, 128 / 129 members | `listpack` / `skiplist` |
| String `"12345"` / `"short"` / 45 characters | `int` / `embstr` / `raw` (embstr holds ≤44 bytes) |

Two consequences worth acting on. A single oversized *value* promotes the whole collection, so
one 200-byte field in an otherwise tiny hash costs the compact encoding. And because conversion
is one-way, a collection that briefly spiked stays expensive until the key is rewritten.

## Big keys

- `redis-cli --bigkeys` samples the keyspace and reports the largest key per type. It runs
  `SCAN` plus a size command per key, so it is safe on a live instance but approximate.
- `redis-cli --memkeys` does the same by `MEMORY USAGE` rather than element count — the number
  that actually matters.
- `MEMORY USAGE key [SAMPLES n]` gives bytes for one key including overhead.
- Splitting patterns: shard by bucket (`leaderboard:{2026-09}:eu`), by hash of the member
  (`set:users:{03}` for 16 or 256 buckets), or by time window. Merge client-side, and accept
  that ranking across shards needs a merge step.
- Deleting a big key blocks: use `UNLINK` (asynchronous reclaim) rather than `DEL`, and prefer
  `lazyfree-lazy-user-del yes` if the application cannot be changed.

## Memory accounting

- `INFO memory`: `used_memory` is what Redis allocated, `used_memory_rss` what the OS sees,
  `mem_fragmentation_ratio` the quotient. A ratio well above 1 after heavy deletion is
  fragmentation, not data; `activedefrag yes` addresses it at a CPU cost.
- Overhead per key is real: expect on the order of 50–100 bytes for the key object, the dict
  entry and the expiry entry before any value. Ten million tiny keys is a gigabyte of
  bookkeeping — which is the argument for grouping related fields into one Hash rather than
  spreading them across keys.
- `MEMORY STATS` breaks the total down by keyspace, client buffers, replication backlog, AOF
  buffer and overhead. Client output buffers are the growth nobody expects: a slow consumer of
  a large reply is charged to Redis.
- `MEMORY DOCTOR` refuses to answer on a small or lightly used instance `[verified]`, so its
  silence is not a clean bill of health.

<!-- sources: redis-agent-skills, redis-io-docs, redis-oss, redisvl -->
