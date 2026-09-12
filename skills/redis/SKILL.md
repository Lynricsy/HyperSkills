---
name: redis
description: "Designs and operates Redis data structures, caching, streams and clusters."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# redis

## Scope

Covers Redis the server and the code that talks to it: structure selection and the encodings
behind it, key naming, expiry and eviction, persistence and replication, transactions and
scripting, locks, Pub/Sub and Streams, Cluster, connections and pipelining, the cache patterns
that keep a database alive, the Redis Query Engine including vector search and semantic
caching, ACLs, and the commands that answer "what is this instance doing right now".

The body is written against **Redis 8.10** (current stable; 8.10.1 at time of writing, with
8.8.x, 8.6.x, 8.4.x, 8.2.x, 7.4.x, 7.2.x and 6.2.x still maintained). Rules that need a server
newer than 7.2 carry a gate such as `(7.4+)`. Confidence markers: `[verified]` measured here
against 8.10.1, `[official]` from Redis documentation, `[community]` otherwise.

Not covered:

- Relational schema, indexes and query plans. Use the `postgres` skill.
- Document modelling, aggregation pipelines and Atlas Search. Use the `mongodb` skill.
- A full-text search platform's own index lifecycle, relevance tuning and cluster operations.
  Use the `elasticsearch` skill.
- How a given framework wires a cache, a session store or a queue up: annotations, config
  files, DI, ORM second-level caches, migration of cache code. Use the `java-spring`,
  `laravel`, `fastapi` or `nodejs-backend` skill. This skill covers what those integrations
  do *to Redis* — the key shapes they produce, the TTLs they set or fail to set, the commands
  they issue per request.
- Application-level cache architecture: which layer should hold which data, whether to cache
  at the CDN or in-process, cache hierarchies across services. That is a design question for
  the owning service, not a Redis question.
- Memcached. Not covered — the eviction, expiry and data-structure model is different, and
  nothing here transfers.
- Managed-hosting control planes: instance sizing and SKUs, provider backup and restore,
  IAM-based auth, private endpoints, shard scaling through a provider API, Redis Cloud or
  Redis Software administration, and vendor products layered on Redis. No skill in this
  library covers those; say so rather than improvising provider commands. Everything at the
  command and key-design level below still applies on a managed instance, but `CONFIG SET`,
  `DEBUG`, `MODULE LOAD` and the config file usually will not.

## Core rules

1. Establish the server before quoting a gated rule: `INFO server` for `redis_version` and
   `redis_mode`, `MODULE LIST` for the query engine and JSON. Hash-field TTLs need 7.4,
   `FT.HYBRID` needs 8.4, vector sets need 8.0, and a `cluster` instance rejects multi-key
   code that works standalone.
2. Command execution is single-threaded. Every O(N) command is latency for every other
   client, which is why `KEYS`, `SMEMBERS`, `HGETALL`, `LRANGE key 0 -1`, `SORT` and
   `SUNIONSTORE` over large containers are dangerous — the problem is head-of-line blocking,
   not bandwidth.
3. Read the configuration from the instance, never from memory:
   `CONFIG GET maxmemory maxmemory-policy appendonly save`. The stock values are `maxmemory 0`,
   `noeviction`, `appendonly no`, `save 3600 1 300 100 60 10000` `[verified]` — an unbounded
   instance whose only limit is the kernel OOM killer, with a loss window up to an hour.
4. Choose the structure from the access pattern: how you read it (whole / by field / by rank /
   by membership), how it shrinks, whether entries expire individually, and whether two of
   these keys must be touched atomically. Data shape alone never decides
   (`references/data-structures.md`).
5. A serialised JSON document in a String makes every field update a read-modify-write of the
   whole value, and makes concurrent updates lose writes. Use a Hash when fields change
   independently; add `HEXPIRE`/`HGETEX` (7.4+) when individual fields must expire.
6. `OBJECT ENCODING` is the memory story, and the thresholds are per-instance config, not
   folklore: on 8.10.1 the defaults are `hash-max-listpack-entries 512`,
   `zset-max-listpack-entries 128`, `set-max-listpack-entries 128`, value limit 64 bytes
   `[verified]`. Read them with `CONFIG GET hash-max-listpack-*` before claiming a structure
   has been promoted to a hashtable.
7. One key lives in one slot and is served by one core, so a single huge key — a 60M-member
   sorted set, a 2M-member set — is both a latency source and the reason one cluster shard is
   four times the size of the others. Split by bucket or move it out.
8. A plain `SET` replaces the key *including its expiry*, so a session refresh written as
   `SET key <new payload>` silently makes the key immortal. `KEEPTTL` preserves it; `APPEND`,
   `SETRANGE`, `INCR`, `HSET` and `RENAME` preserve it; `GETSET` clears it `[verified]`.
9. Every cache key gets an explicit TTL at write time, and the TTL gets jitter. A batch warmed
   with one constant TTL expires as a batch, which is how a warm-up job becomes a database
   outage an hour later.
10. `volatile-lru` and its siblings only consider keys that have a TTL. With no such key the
    instance answers writes with `OOM command not allowed when used memory > 'maxmemory'` —
    byte-identical to `noeviction` `[verified]`. Pure cache: `allkeys-lru` or `allkeys-lfu`.
    Source of truth: `noeviction` plus an alert. `volatile-*` only when both live in one
    instance *and* every cache key has a TTL.
11. An expired key keeps its memory until something touches it or the active-expiry cycle
    reaches it: with active expiry disabled, 300 keys stayed in `DBSIZE` a full second after
    expiry and `used_memory` did not drop; one `EXISTS` freed one key, a full `SCAN` freed all
    of them `[verified]`. `DBSIZE` counts keys that are already logically gone.
12. `SCAN` guarantees only that every element present for the whole iteration is returned at
    least once; it may return duplicates and it may miss keys added mid-iteration. `COUNT` is
    a hint per call, and `MATCH` filters *after* the bucket is read, so a selective pattern
    over a large keyspace still costs a full walk.
13. On the miss path, concurrent requests for the same key all recompute it. Serialise them
    with a single-flight lock (`SET lock:<key> <token> NX EX <n>`, the loser waits or serves
    stale) or refresh ahead of expiry; a longer TTL does not fix it, it only moves it.
14. Requests for keys that will never exist bypass the cache entirely. Cache the negative
    result under a short TTL with a sentinel distinguishable from a real payload, and put a
    Bloom filter (`BF.RESERVE`/`BF.EXISTS`, built in on 8.0+) in front when the id space is
    attacker-controlled.
15. Never invalidate by pattern. `KEYS product:*` blocks the server for the whole keyspace and
    `SCAN` merely spreads the same work out. Maintain a reverse index of the keys a change
    affects, or version the prefix so one write invalidates a whole class
    (`references/caching-patterns.md`).
16. `MULTI`/`EXEC` and Lua give **isolation, not rollback**. An error while queuing (unknown
    command, wrong arity) aborts the whole transaction with `EXECABORT`; an error at execution
    time does not — `MULTI; INCR c; LPUSH str x; INCR c; EXEC` leaves `c` at 2, and a script
    that fails halfway keeps the writes it already made `[verified]`.
17. A pipeline is not a transaction. It is one round trip for N independent commands, and any
    of them can fail on its own. Reach for `WATCH` + `MULTI` for compare-and-set, or a script
    when the read and the write must not be separated.
18. A Redis lock is a lease, not mutual exclusion. Store a unique token as the value, release
    only via a compare-and-delete script or `FCALL`, and accept that a holder which overruns
    the TTL loses the lock while still working. There is no fencing token, so anything whose
    correctness depends on exclusivity needs the guard in the resource itself
    (`references/transactions-and-scripting.md`).
19. Pub/Sub is at-most-once with no backlog: a subscriber that is not connected at publish
    time never learns the message happened, and a slow one is disconnected on
    `client-output-buffer-limit`. Anything that must survive a restart is a Stream.
20. Stream consumer groups are at-least-once. `XREADGROUP` hands an entry over and keeps it
    pending until `XACK`, so the handler must be idempotent, a dead consumer's entries need
    `XAUTOCLAIM`, and the stream needs `MAXLEN`/`XTRIM` or it grows forever.
21. In Cluster mode a key maps to one of 16384 slots by CRC16 of the key name, and every
    multi-key command — `MGET`, `SDIFF`, `MULTI`, a pipeline sent as one unit, a script with
    two `KEYS` — requires all keys in one slot. A hash tag `{...}` makes only the tagged
    substring count; scope it to the entity (`user:{1001}:profile`), never to a bare id, and
    only where a multi-key operation actually exists.
22. A cluster client must follow `MOVED` and `ASK` and refresh its slot map; pointing a
    single-node client at one cluster node works until the first resharding. Replica reads are
    opt-in and asynchronous, so read-your-own-writes breaks — fine for leaderboards and price
    lookups, wrong for state a request just wrote.
23. Share connections: a pool that leases per call, or a single multiplexed connection. Never
    one connection per request. Blocking commands (`BLPOP`, `BLMOVE`, `XREAD BLOCK`) need
    their own connection, because on a multiplexed one they stall every other caller. Set both
    a connect timeout and a command timeout, connect the shorter of the two.
24. Out of the box the `default` user is `on nopass ~* +@all` `[verified]` — full access with
    no password. Give each application its own ACL user with the key patterns and command
    categories it needs, and remove capability by category (`-@dangerous`, `-@admin`) rather
    than by renaming commands, which breaks clients and cluster tooling silently
    (`references/security.md`).
25. Finish by measuring, and quote the numbers: `DBSIZE`, `INFO memory` (`used_memory`,
    `mem_fragmentation_ratio`, `evicted_keys`, `expired_keys`), `INFO stats`
    (`keyspace_hits`/`keyspace_misses`, `rejected_connections`), `SLOWLOG GET`, and
    `redis-cli --bigkeys` before and after. "It should be faster now" is not a result.

Paths below are relative to this skill's directory.

## Workflows

### choose-structures-and-design-the-key-space

- [ ] Write down the read patterns first — by id, by field, by rank, by membership, by time
      range — and the write patterns beside them. Then pick per pattern, not per entity
      (`references/data-structures.md`).
- [ ] Reject the two defaults people reach for without thinking: a serialised blob in a String
      (read-modify-write, lost updates) and a List named "queue" (no acknowledgement).
- [ ] Fix the naming: lowercase, colon-separated, `service:entity:id:attribute`, a tenant
      segment in front when the instance is shared, and no URLs or free text as keys
      (`references/keyspace-and-expiry.md`).
- [ ] Decide the expiry policy per key class at design time: which keys have a TTL, whether it
      slides, and what must happen when one is evicted early.
- [ ] Size it: estimate members per key and bytes per member, check the resulting encoding
      against the instance's listpack thresholds, and split anything heading past a few
      thousand members or a megabyte.
- [ ] Note every place two keys must change together — that is either a script, or a hash tag
      if the instance is or may become a cluster.
- [ ] **Gate — measured on a real instance:** load a representative sample, then confirm
      `MEMORY USAGE <key>`, `OBJECT ENCODING <key>` and `DEBUG SLEEP`-free `SLOWLOG` are what
      the design assumed. Quote the per-key bytes and the projected total.

### fix-a-cache-that-is-hurting-the-database

- [ ] Classify the symptom before changing code: a periodic spike is synchronised expiry, a
      spike on one id is a hot-key stampede, a flood of misses on ids that do not exist is
      penetration, and a permanent regression is usually eviction or a missing TTL
      (`references/caching-patterns.md`).
- [ ] Check the eviction policy against the key population: `CONFIG GET maxmemory
      maxmemory-policy` plus `INFO stats` for `evicted_keys` and `expired_keys`. A
      `volatile-*` policy with unexpired keys is the whole bug.
- [ ] Add jitter to every batch-written TTL, and refresh hot keys ahead of expiry rather than
      on the miss.
- [ ] Put a single-flight lock on the recompute path and decide explicitly what the losers
      do — wait with a bounded retry, or serve the stale value.
- [ ] Cache negative lookups with a sentinel and a short TTL; add a Bloom filter if the id
      space is unbounded.
- [ ] Replace pattern-based invalidation with a reverse index or a versioned prefix, and make
      every write path that mutates the source also touch the cache.
- [ ] Audit the refresh writes for dropped expiry: any `SET` that is meant to update a value
      but keep the TTL needs `KEEPTTL` or an explicit re-`EXPIRE`.
- [ ] **Gate — the source load actually fell:** re-run the scenario and quote the before/after
      of `keyspace_hits`/`keyspace_misses`, the query count on the source, and the p99 of the
      endpoint. A hit-ratio number is only meaningful for the cache-aside prefixes —
      `INFO stats` is instance-wide and includes session, lock and queue traffic.

### diagnose-memory-eviction-or-latency

- [ ] Separate "slow" from "blocked" first: `INFO clients` for `blocked_clients`,
      `CLIENT LIST` for a connection stuck in a blocking read, `INFO stats` for
      `rejected_connections` against `maxclients` (`references/operations.md`).
- [ ] Get the slow commands rather than guessing: `SLOWLOG GET 25`. The threshold is
      `slowlog-log-slower-than`, 10000 microseconds by default, and the log holds
      `slowlog-max-len` 128 entries `[verified]` — read it before it rolls.
- [ ] Turn on latency monitoring if the answer is not in `SLOWLOG`:
      `latency-monitor-threshold` defaults to 0, meaning `LATENCY DOCTOR` and
      `LATENCY HISTORY` have nothing to report until you set it `[verified]`.
- [ ] Attribute memory: `INFO memory` for `used_memory` versus `maxmemory` and
      `mem_fragmentation_ratio`, `redis-cli --bigkeys` for the shape of the keyspace,
      `MEMORY USAGE` on the suspects. `MEMORY DOCTOR` declines to answer on a small instance,
      so do not treat its silence as health `[verified]`.
- [ ] Decide whether the growth is data, expired-but-untouched keys, client output buffers or
      fragmentation — each has a different fix, and only the first is solved by a bigger box.
- [ ] Check the command mix with `INFO commandstats` and `INFO latencystats`: one O(N) command
      at low rate explains more p99 than a million `GET`s.
- [ ] **Gate — the number moved:** re-run the load and quote `used_memory`, `evicted_keys`,
      the `SLOWLOG` entry count above threshold, and the p99 from `--latency-history`.

### move-code-onto-a-cluster

- [ ] Inventory every multi-key operation in the code: `MGET`/`MSET`, set and zset store
      commands, `MULTI` blocks, scripts with more than one key, and any pipeline whose
      commands are assumed to run together (`references/cluster-and-connections.md`).
- [ ] For each one, decide between a hash tag and decomposition. Tag when the keys genuinely
      belong to one entity; decompose when the grouping was incidental — tagging everything
      rebuilds a single-node bottleneck inside the cluster.
- [ ] Choose the tag scope deliberately: the entity, not the raw id, so unrelated namespaces
      do not collide on one slot.
- [ ] Swap the client for a cluster-aware one and confirm it splits pipelines per node and
      follows `MOVED`/`ASK`; a single-node client aimed at one node is a latent outage.
- [ ] Find the keys that cannot shard — one enormous sorted set, set or stream — and split or
      relocate them before blaming the shard balance.
- [ ] Decide replica reads per call site, not globally, and list the call sites that must stay
      on the primary because they read what they just wrote.
- [ ] **Gate — proven on a cluster:** run the suite against a real 3-primary cluster (not a
      single node), confirm zero `CROSSSLOT` errors, and check distribution with
      `CLUSTER KEYSLOT` on the tagged keys plus `DBSIZE` per node.

### build-a-queue-that-does-not-lose-messages

- [ ] Decide the delivery guarantee out loud. At-most-once is a List; at-least-once needs a
      Stream with a consumer group; exactly-once does not exist and has to become
      at-least-once plus an idempotent handler (`references/streams-and-messaging.md`).
- [ ] For at-least-once, lay out the four commands together: `XADD` to produce, `XREADGROUP`
      to claim, `XACK` after the side effect succeeded, `XAUTOCLAIM` to recover a dead
      consumer's pending entries.
- [ ] Make the handler idempotent before wiring the ack: a `SET done:<id> 1 NX EX <n>` guard
      or an idempotency key on the downstream call.
- [ ] Bound the stream: `XADD ... MAXLEN ~ <n>` or a periodic `XTRIM MINID`, and decide what
      happens to entries nobody ever acked.
- [ ] Give consumers their own connections — a blocking read on a shared multiplexed
      connection stalls unrelated traffic.
- [ ] If a List has to stay, make it `BLMOVE` from the queue into a per-consumer processing
      list and add the reaper that returns abandoned items.
- [ ] **Gate — kill a consumer mid-work:** send `SIGKILL` to a consumer between claim and ack,
      then show the entry in `XPENDING` and show `XAUTOCLAIM` handing it to another consumer
      and the work completing exactly once from the outside.

### design-or-debug-a-search-or-vector-index

- [ ] Confirm the engine exists and its version: `MODULE LIST` for `search`, `ReJSON`,
      `vectorset`. On 8.x the official image ships them; on 7.x it does not
      (`references/search-and-vectors.md`).
- [ ] Match the field type to the query, not the value's Java type. An exact-match value in a
      `TEXT` field is tokenised and stemmed, so `@sku:ABC-123` returns **zero** results
      `[verified]` — `TAG` is the type for identifiers, statuses and enums.
- [ ] Use `FT.EXPLAIN` on any query that returns nothing before touching the schema; it shows
      how the query was parsed, which is usually the whole answer.
- [ ] For vectors, make `DIM`, `DISTANCE_METRIC` and `TYPE` follow the embedding model
      exactly; a mismatch produces plausible garbage rather than an error. Choose the
      mechanism deliberately: an RQE `VECTOR` field when the query also filters on attributes
      or full text, a vector set (`VADD`/`VSIM`) for a standalone KNN collection — its default
      `quant-type` is `int8`, which is lossy `[verified]`.
- [ ] Filter before the vector comparison in the same query rather than over-fetching and
      filtering client-side.
- [ ] Change schemas behind an alias (`FT.ALIASUPDATE`) so queries never point at an index
      being rebuilt.
- [ ] **Gate — profiled, not assumed:** run `FT.PROFILE ... SEARCH QUERY "..."` on the real
      query and quote the returned counters, plus a recall spot-check against a brute-force
      `FLAT` result for the vector case.

### review-a-deployment-config

- [ ] Read the four settings that decide whether the instance survives contact with
      production: `maxmemory`, `maxmemory-policy`, `appendonly`, `save`. Say what each stock
      value costs here (`references/operations.md`).
- [ ] State the durability window explicitly. RDB-only with the default save points loses up
      to an hour; AOF with `appendfsync everysec` loses about a second; `always` costs
      throughput. Then say whether that is acceptable for *this* data, and whether the data
      exists anywhere else.
- [ ] Check the replication and failover story: `INFO replication` for the role and lag, and
      whether anything actually promotes a replica. A replica alone is not high availability.
- [ ] Audit access: `ACL LIST`, whether `default` still has `nopass`, whether TLS is on, what
      `bind` and `protected-mode` are, and which commands the application user can reach
      (`references/security.md`).
- [ ] Check the connection ceiling: `maxclients` against pool size times instance count, and
      `INFO stats` for `rejected_connections`.
- [ ] Confirm observability exists before the incident: metrics exported from `INFO`, a
      `slowlog-log-slower-than` that matches the latency budget, and
      `latency-monitor-threshold` set to something other than 0.
- [ ] **Gate — the failure was rehearsed:** kill the primary on a staging copy and record what
      the application does, how long the gap is, and what data is missing afterwards.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Structure selection per access pattern, Hash versus JSON, encodings and the measured listpack thresholds, big-key detection and splitting, Bitmap, HyperLogLog, geospatial, Bloom, Stream and vector-set storage, memory accounting | Deciding how to store something, or auditing what is already stored | `references/data-structures.md` |
| Key naming and namespaces, the full TTL-preservation table, `EXPIRE` family and hash-field TTLs, lazy versus active expiry, every `maxmemory-policy` and its failure mode, LRU/LFU sampling, keyspace notifications | Keys vanish, keys never vanish, or writes start failing with OOM | `references/keyspace-and-expiry.md` |
| Cache-aside and write paths, TTL jitter, single-flight and stale-while-revalidate, negative caching and Bloom filters, versioned-prefix and reverse-index invalidation, client-side caching, rate limiting, semantic caching for LLM responses | Building or repairing a cache in front of another system | `references/caching-patterns.md` |
| `MULTI`/`WATCH` semantics, pipelines versus transactions, Lua versus `FUNCTION`, script replication and determinism, lock leases with token release, why Redlock does not give what people think | Two operations must not interleave, or a lock is misbehaving | `references/transactions-and-scripting.md` |
| Pub/Sub delivery and output-buffer limits, keyspace notifications as an event source, Stream anatomy, consumer groups, `XPENDING`/`XAUTOCLAIM` recovery, trimming, List queue patterns and their limits | Messages are lost, duplicated or piling up | `references/streams-and-messaging.md` |
| Slot mapping and hash tags, the full `CROSSSLOT` surface, `MOVED`/`ASK` and slot-map refresh, resharding, connection pooling versus multiplexing, pipelining, timeouts and retries, replica reads | Moving to Cluster, or a client is the bottleneck | `references/cluster-and-connections.md` |
| RDB save points and AOF fsync policies with their loss windows, rewrite behaviour, replication and failover, `WAIT`, the `INFO` fields worth alerting on, `SLOWLOG`, `LATENCY`, `MEMORY`, `--bigkeys`, `--latency-history` | Deciding durability, or answering "what is it doing right now" | `references/operations.md` |
| ACL users, selectors and command categories, the `default` user's stock permissions, TLS, `bind` and `protected-mode`, why `rename-command` is the fallback, script and injection surface, audit checklist | Hardening an instance or reviewing one against a finding | `references/security.md` |
| `FT.CREATE` schema design, field types and the exact-match trap, query-syntax and tokenisation gotchas, `FT.EXPLAIN`/`FT.PROFILE`, vector fields versus vector sets, HNSW parameters, hybrid retrieval, index aliases | Working on a Redis Query Engine index or vector search | `references/search-and-vectors.md` |

## Output format

When reviewing Redis usage — code, `redis.conf`, or both — group findings by file and lead each
with the location and the blast radius:

```
worker.py:22 - data-loss - RPOP removes the job before ship() succeeds, so a worker killed
  mid-flight drops the order. Replace with XREADGROUP + XACK after ship(), and XAUTOCLAIM to
  recover a dead consumer's pending entries.
redis.conf:4 - outage - maxmemory-policy volatile-lru with no TTL on any key behaves exactly
  like noeviction: writes fail with OOM. Set allkeys-lru for a pure cache.
```

Order findings by blast radius: data loss first, then availability (OOM, blocking commands,
connection exhaustion), then correctness (lost updates, stale reads), then cost and style. For
a performance finding, quote the evidence — a `SLOWLOG` entry, a `MEMORY USAGE`, an
`OBJECT ENCODING`, a `--bigkeys` line — rather than asserting that something is slow, and give
the before/after command.

## Environment

- Reproduce against the same major version as production. `docker run -d --name r
  redis:8-alpine` is enough to settle expiry, eviction, encoding, transaction and cluster-slot
  questions, and running the question beats quoting a blog post. Add
  `redis-server --enable-debug-command yes` when a test needs `DEBUG`, which is refused by
  default.
- `MODULE LIST` tells you whether the query engine, JSON, Bloom and time-series are present.
  The 8.x official image bundles them; older images and self-compiled servers do not.
- `redis-cli` carries the diagnostics worth knowing: `--bigkeys`, `--memkeys`, `--hotkeys`
  (needs an LFU policy), `--latency-history`, `--stat`, and `--cluster check`.
- `DEBUG`, `CONFIG SET`, `MODULE LOAD` and `FLUSHALL` are commonly disabled or ACL-blocked on
  managed instances. Check `ACL WHOAMI` and `ACL GETUSER <user>` before proposing a command
  the application's credentials cannot run.
