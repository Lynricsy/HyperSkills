# Cluster, slots and client connections

Verified against: Redis 8.10.1.

## Contents

- [Slots](#slots)
- [The CROSSSLOT surface](#the-crossslot-surface)
- [Hash tags](#hash-tags)
- [What a hash tag cannot fix](#what-a-hash-tag-cannot-fix)
- [MOVED, ASK and the slot map](#moved-ask-and-the-slot-map)
- [Resharding and rebalancing](#resharding-and-rebalancing)
- [Replica reads](#replica-reads)
- [Pooling versus multiplexing](#pooling-versus-multiplexing)
- [Timeouts and retries](#timeouts-and-retries)
- [Pipelining across a cluster](#pipelining-across-a-cluster)
- [Cluster inspection commands](#cluster-inspection-commands)

## Slots

A cluster owns 16384 hash slots divided among the primaries. A key's slot is
`CRC16(key) mod 16384`, computed from the key *name* — nothing about the value, the type or the
command affects it. Each primary owns a contiguous-ish set of slots and serves only those.

Two consequences drive every design decision below:

1. **One key is always in exactly one slot on exactly one primary.** Sharding distributes keys,
   never the contents of a key. A 60M-member sorted set is one key and therefore one core and
   one shard's memory, no matter how many shards exist.
2. **A command touching several keys must find them all in one slot.** The server refuses
   otherwise; it will not fan out on your behalf.

Only database 0 exists in cluster mode; `SELECT 1` fails.

## The CROSSSLOT surface

Anything with more than one key, plus a few things that do not look like they have keys:

| Category | Examples |
|---|---|
| Multi-key reads/writes | `MGET`, `MSET`, `MSETNX`, `DEL k1 k2`, `UNLINK k1 k2`, `EXISTS k1 k2`, `TOUCH` |
| Set/zset algebra | `SINTER`, `SUNION`, `SDIFF` and their `*STORE` forms, `ZUNIONSTORE`, `ZINTERSTORE`, `ZDIFF`, `ZRANGESTORE`, `SINTERCARD` |
| Move/copy between keys | `RENAME`, `COPY`, `SMOVE`, `LMOVE`, `BLMOVE`, `RPOPLPUSH`, `GEOSEARCHSTORE`, `ZPOPMIN` over several keys |
| Transactions | every key inside one `MULTI`/`EXEC` |
| Scripts | every key in `KEYS`, and any key the script touches without declaring it |
| Bit operations | `BITOP` across source keys |
| Pub/Sub | non-shard channels are broadcast cluster-wide; `SSUBSCRIBE`/`SPUBLISH` are slot-routed |

The error text differs by path: a multi-key command gives
`CROSSSLOT Keys in request don't hash to the same slot`, a script gives
`ERR Lua script attempted to access keys of different slots`, and a pipeline sent by a
single-node client against a cluster gives `MOVED` per command instead.

## Hash tags

If a key name contains `{` followed later by `}`, only the substring between the **first** `{`
and the **first following** `}` is hashed. An empty `{}` or a `}` before any `{` disables the
tag and the whole name is hashed.

```
user:{1001}:profile        slot(1001)
user:{1001}:settings       slot(1001)      -> MGET of both is legal
{user:1001}:profile        slot("user:1001")
user:1001:profile          slot("user:1001:profile")  -> different slot from :settings
```

Rules that come from real failures:

- **Scope the tag to the entity, not the bare id.** `{1001}` puts `order:{1001}`,
  `employee:{1001}` and `invoice:{1001}` on the same slot for no reason, concentrating unrelated
  traffic and unbalancing the cluster. Use `{user:1001}` or `user:{1001}:...`.
- **Tag only where a multi-key operation actually exists.** A tag is a constraint on placement;
  applying it everywhere by habit collapses the keyspace onto a few slots and recreates a
  single-node bottleneck inside the cluster.
- **Decide up front.** Adding a tag changes the key name, so retrofitting it means a migration
  (dual-write, backfill, cut over) on live data. Single-key commands work identically on tagged
  and untagged keys, so the tag costs nothing until you need it.
- **A tag is not a transaction.** Keys in one slot may still be read and written by other
  clients between your commands; the tag only makes a multi-key command *legal*.

## What a hash tag cannot fix

- **One oversized key.** Split it: `leaderboard:{2026-09}:eu`, `set:users:{07}` over 16 or 256
  buckets by `hash(member) % n`, or a stream per shard. Merging happens client-side, and a
  global ranking needs a merge step or a separate aggregate.
- **A hot slot.** If one entity is hot, its slot is hot; tags concentrate rather than spread.
  Replicate the hot value to several keys with different tags and read one at random, or cache
  it in the application.
- **Global counters and indexes.** A single `stats:orders` key is one slot. Either accept it
  (an `INCR` is cheap and a single slot handles a lot), or shard the counter into `n` keys and
  sum on read.
- **Cross-entity work.** Two users' data cannot be in one transaction unless you tag them
  together, which defeats sharding. Restructure: one script per entity, or move the invariant
  to a store that supports cross-shard transactions.

## MOVED, ASK and the slot map

- A client that asks the wrong node for a key gets `MOVED <slot> <host:port>`. The correct
  behaviour is to follow it **and refresh the whole slot map**, because a `MOVED` usually means
  the topology changed, not that this one key moved.
- During a slot migration, a key not yet moved answers normally on the source; a key already
  moved answers `ASK <slot> <host:port>`. `ASK` is a one-shot redirect: the client must send
  `ASKING` before the retried command and must **not** update its slot map. Getting this wrong
  produces an intermittent failure that only appears during resharding.
- `CLUSTERDOWN` means a slot has no owner — usually a failed primary with no promoted replica,
  or `cluster-require-full-coverage yes` with a partially-down cluster.
- A single-node client library pointed at a cluster node works for keys that happen to live
  there. It is a latent outage, not a configuration choice: use the cluster client.

## Resharding and rebalancing

- `redis-cli --cluster reshard` and `--cluster rebalance` move slots. Moving a slot moves its
  keys, so a slot holding one 8 GB key blocks on that key's migration.
- Rebalancing counts *slots*, not bytes or traffic. An even slot distribution over uneven keys
  is still an uneven cluster; check per-node `DBSIZE` and `INFO memory` rather than the slot
  count.
- `CLUSTER COUNTKEYSINSLOT <slot>` and `CLUSTER GETKEYSINSLOT <slot> <n>` show what a slot
  holds — the tool for finding the key that made one shard four times the size of its peers.
- Adding a shard does not help a workload dominated by one key or one slot. Confirm the
  distribution is the problem before scaling out.

## Replica reads

Opt-in, both in Cluster and in plain primary/replica replication:

- Cluster clients take a flag (`read_from_replicas` and equivalents) which issues `READONLY` on
  replica connections. Without it every read goes to the primary.
- Replication is asynchronous, so a replica can lag arbitrarily under load. **Read-your-own-
  writes breaks**: a request that just wrote and then reads from a replica can see the old
  value.
- `INFO replication` on the replica gives `master_repl_offset` versus its own offset — the lag
  to alert on. `master_link_status:down` means it is serving stale data with no warning to
  clients.
- `WAIT <numreplicas> <timeout-ms>` blocks until the write has reached N replicas. It bounds the
  loss window for one critical write; it is not a consistency mode and costs a round trip per
  call.
- Suitable for replicas: leaderboards, price lookups, catalogue reads, analytics. Not suitable:
  session state, lock state, queue state, anything the same request wrote.

## Pooling versus multiplexing

Two valid shapes. A connection per request is never one of them — the TCP handshake, the
`AUTH`/`HELLO`, and in cluster mode the slot-map discovery are paid per request, and the
connection count is the number of in-flight requests.

| Shape | How it behaves | Watch out for |
|---|---|---|
| **Pool** — N persistent connections, leased per call | A lease blocks when the pool is exhausted, so the pool size is a concurrency limit | Size against the server, not the app: total connections across all instances must stay well under `maxclients` (default 10000 `[verified]`) and the server has one thread regardless |
| **Multiplex** — one connection, commands interleaved | No lease, no pool exhaustion, fewer sockets | A blocking command (`BLPOP`, `XREAD BLOCK`) stalls everything on that connection; a transaction or `WATCH` needs exclusive use |

Rules either way:

- Create the client once at process or module scope, not per request or per handler.
- Give blocking consumers their own connection, whichever shape the rest of the app uses.
- A pool stacked behind a proxy multiplies: pool size times instances times proxies.
- `INFO clients` for `connected_clients` and `blocked_clients`, `INFO stats` for
  `rejected_connections` — the last one being non-zero means you already exceeded
  `maxclients`.
- `CLIENT LIST` shows per-connection `age`, `idle`, `cmd` and buffer sizes, which is how you
  find the connection that has been in `blpop` for two hours.

## Timeouts and retries

- Set both a connect timeout and a command timeout. Most clients default both to unset
  (`socket_connect_timeout`/`socket_timeout` are `None` in redis-py), which means a dead node
  hangs the caller until the OS gives up.
- Connect timeout shorter than command timeout: failing to reach a node should be fast, while a
  legitimate `BITCOUNT` over a large string may take longer than the connect budget.
- Blocking commands need their server-side timeout (`BLPOP key 5`) to be *shorter* than the
  client's command timeout, or the client gives up on a healthy blocking read.
- Retry only idempotent commands automatically. A retried `INCR` or `LPUSH` after a timeout can
  double-apply, because a timeout does not tell you whether the server ran the command.
- `server timeout` (`CONFIG GET timeout`, default 0 `[verified]`) closes idle client
  connections; 0 means never, which is the right value when the client pools properly.
- `tcp-keepalive` defaults to 300 seconds `[verified]` and is what detects a peer that vanished
  without a FIN — important behind a NAT or a load balancer with its own idle timeout.

## Pipelining across a cluster

- A pipeline of single-key commands is fine and is the main throughput tool: N commands, one
  round trip per node.
- The client must group commands by owning node and send one pipeline per node. Cluster-aware
  clients do this; the replies then need reassembling in the caller's order, which is also the
  client's job.
- A pipeline wrapped in `MULTI` becomes a transaction and therefore inherits the single-slot
  requirement.
- Keep batches bounded (hundreds to a few thousand commands). One enormous pipeline buffers all
  its replies on both sides, and on the server that memory is charged to the client output
  buffer, which can trip `client-output-buffer-limit`.

## Cluster inspection commands

| Question | Command |
|---|---|
| Which slot does this key hash to | `CLUSTER KEYSLOT <key>` |
| Who owns which slots | `CLUSTER SHARDS` (7.0+), `CLUSTER SLOTS` (older), `CLUSTER NODES` |
| Is the cluster healthy | `CLUSTER INFO` → `cluster_state`, `cluster_slots_assigned` |
| How many keys are in a slot | `CLUSTER COUNTKEYSINSLOT <slot>` |
| Which keys are in a slot | `CLUSTER GETKEYSINSLOT <slot> <count>` |
| Are the shards balanced by data, not slots | `redis-cli --cluster call <node> DBSIZE`, `INFO memory` per node |
| End-to-end consistency check | `redis-cli --cluster check <host:port>` |

<!-- sources: redis-agent-skills, redis-io-docs, redis-py, redis-oss -->
