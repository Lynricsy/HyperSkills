# Persistence, replication and diagnosis

Verified against: Redis 8.10.1.

## Contents

- [Stock configuration and what it costs](#stock-configuration-and-what-it-costs)
- [RDB snapshots](#rdb-snapshots)
- [AOF](#aof)
- [Choosing a durability level](#choosing-a-durability-level)
- [Fork, copy-on-write and memory](#fork-copy-on-write-and-memory)
- [Replication](#replication)
- [Failover](#failover)
- [INFO: the fields worth exporting](#info-the-fields-worth-exporting)
- [SLOWLOG](#slowlog)
- [Latency monitoring](#latency-monitoring)
- [Memory diagnosis](#memory-diagnosis)
- [Connections and clients](#connections-and-clients)
- [redis-cli diagnostic modes](#redis-cli-diagnostic-modes)
- [A triage order that works](#a-triage-order-that-works)

## Stock configuration and what it costs

Measured on a fresh `redis:8-alpine` with no overrides `[verified]`:

```
maxmemory          0                              # unlimited
maxmemory-policy   noeviction
appendonly         no
save               3600 1  300 100  60 10000
timeout            0
tcp-keepalive      300
maxclients         10000
appendfsync        everysec                       # only applies once appendonly is yes
auto-aof-rewrite-percentage 100
slowlog-log-slower-than     10000                 # microseconds
slowlog-max-len             128
latency-monitor-threshold   0                     # disabled
notify-keyspace-events      (empty)               # disabled
```

Read that as a list of production problems: the instance has no memory ceiling and will be
stopped by the kernel rather than by Redis; it will refuse writes rather than evict once a
ceiling is set; it persists only by snapshot with a window up to an hour; and latency
monitoring is off, so the first incident has no history.

## RDB snapshots

A point-in-time binary dump of the whole dataset, written by a forked child.

- `save <seconds> <changes>` lines are OR-ed save points. The default
  `3600 1 300 100 60 10000` means: after 1 change wait an hour, after 100 changes wait 5
  minutes, after 10000 changes wait a minute. **The worst-case loss is the longest window that
  applies to your write rate** — an hour on a quiet instance.
- `BGSAVE` forks and writes in the background. `SAVE` blocks the server for the whole dump and
  exists only for controlled shutdowns.
- `SHUTDOWN` saves by default if save points are configured; `SHUTDOWN NOSAVE` does not. A
  container killed with `SIGKILL` never gets the chance either way.
- `rdb_last_bgsave_status:err` in `INFO persistence` is the field that goes unnoticed: if the
  disk is full or permissions changed, Redis keeps serving and keeps failing to save. Alert on
  it and on `rdb_changes_since_last_save`.
- `stop-writes-on-bgsave-error yes` (the default) turns a failed snapshot into refused writes,
  which is a surprise during an incident. Know which way it is set before the incident.
- An RDB is portable and compact, so it is the right tool for cloning an instance and for
  restore-from-backup. It is the wrong tool for a small loss window.

## AOF

An append-only log of the write commands, replayed on start.

- `appendonly yes` enables it. `appendfsync` decides the loss window: `always` (fsync per write,
  slowest, sub-command loss), `everysec` (default, up to ~1 second), `no` (the OS decides,
  seconds to a minute).
- `everysec` is not exactly one second: an fsync that takes longer than a second delays the next
  one, so the real window under disk pressure is worse than advertised. `aof_delayed_fsync` in
  `INFO persistence` counts the occurrences.
- The log is rewritten when it grows past `auto-aof-rewrite-percentage` (100 — i.e. double)
  over `auto-aof-rewrite-min-size`. Rewrite forks, so the fork cost below applies.
- Modern Redis uses a multi-part AOF (a base RDB plus incremental files, listed in a manifest
  under `appenddirname`). Do not hand-edit or hand-copy individual files; copy the directory.
- `redis-check-aof --fix` truncates a partial final command after an unclean stop. It removes
  data; take a copy first.
- `BGREWRITEAOF` triggers a rewrite manually. `aof_rewrite_in_progress` and
  `aof_last_bgrewrite_status` are the fields to watch.

## Choosing a durability level

| Data | Configuration | Loss window |
|---|---|---|
| Cache with a source of truth elsewhere | `appendonly no`, `save ""` (no snapshots at all) | Everything, on purpose. Faster and avoids fork pauses; the cache repopulates |
| Cache that is expensive to rebuild | `appendonly no`, keep save points | Up to the longest save window; the instance warms from the RDB after a restart |
| Queue, session store, counters | `appendonly yes`, `appendfsync everysec` | ~1 second, more under disk pressure |
| Source of truth | `appendonly yes` + `appendfsync everysec` + a replica + `WAIT` on the writes that matter | ~1 second locally; `WAIT` bounds the loss to what has not reached a replica |
| Money, ledgers, anything unreconstructable | Not this. Use a database with synchronous durability; keep Redis as the cache or index in front | — |

State the window in the answer. "We enabled AOF" is not a durability statement; "we lose up to
about a second of writes, and up to a second more when the disk is slow" is.

## Fork, copy-on-write and memory

Both `BGSAVE` and an AOF rewrite `fork()`. The child shares pages copy-on-write, so memory
grows with the *write rate during the dump*, not with the dataset — but on a write-heavy
instance that can approach a second copy of the data.

- Size the box for `used_memory` plus the fork headroom plus replication buffers, not for
  `used_memory` alone. This is the main reason `maxmemory` should be well below physical RAM.
- `latest_fork_usec` in `INFO stats` is the pause the fork itself cost. On a large instance with
  transparent huge pages enabled it can reach hundreds of milliseconds; disabling THP is the
  standard remedy and Redis logs a warning about it at startup.
- Disable persistence entirely on a pure cache (`appendonly no` and `save ""`) and the fork
  pauses disappear with it.

## Replication

- `REPLICAOF <host> <port>` (or `replicaof` in the config) starts replication. The replica does
  a full sync (the primary forks an RDB) then streams the command backlog.
- Asynchronous by default: the primary acknowledges a write before any replica has it. A
  failover therefore loses the unreplicated tail.
- `repl-backlog-size` decides whether a briefly disconnected replica can do a partial
  resynchronisation instead of a full one. Too small, and every network blip costs a full sync
  and a fork on the primary.
- Replicas are read-only unless `replica-read-only no` — which you almost never want, since a
  write to a replica is lost at the next sync.
- A replica does not expire keys independently; it waits for the primary's `DEL`. A logically
  expired key still counts in the replica's `DBSIZE` while reads correctly return empty.
- `WAIT <numreplicas> <timeout>` returns how many replicas acknowledged everything written on
  this connection. Useful around a critical write; it does not make replication synchronous.
- `min-replicas-to-write` / `min-replicas-max-lag` make the primary refuse writes when too few
  replicas are current — trading availability for a bounded loss window.

Fields to watch: `role`, `connected_slaves`, each replica's `offset` against
`master_repl_offset`, `master_link_status`, `master_last_io_seconds_ago`,
`rdb_bgsave_in_progress` during a full sync.

## Failover

- A replica alone is not high availability: something has to promote it and tell clients. That
  something is Redis Sentinel (for standalone replication) or the cluster bus (for Cluster).
- Sentinel needs at least three sentinels for a quorum, and clients must ask a sentinel for the
  current primary rather than connecting to a fixed host. A Sentinel deployment where clients
  hold a hard-coded address does nothing on failover.
- Cluster promotes a replica automatically when a majority of primaries agree a primary is
  failing; a cluster with no replica per shard cannot fail over at all.
- `FAILOVER` performs a coordinated handover with no data loss window; it answers
  `ERR No failover in progress` when there is nothing to abort `[verified]`. Use it for planned
  maintenance instead of killing the primary.
- Rehearse it. The question is not whether a replica gets promoted but what the application
  does during the gap: how long the errors last, whether the client reconnects, and what was
  lost.

## INFO: the fields worth exporting

| Section | Field | Why it matters |
|---|---|---|
| memory | `used_memory`, `maxmemory` | Alert on the ratio well before the ceiling — headroom is needed for forks and buffers |
| memory | `mem_fragmentation_ratio` | Well above 1 after mass deletion means fragmentation, not data |
| memory | `maxmemory_policy` | Catches the policy being changed underneath you |
| stats | `evicted_keys` | Non-zero on a source of truth is data loss |
| stats | `expired_keys` | Distinguishes TTL expiry from eviction — the two get confused constantly |
| stats | `keyspace_hits`, `keyspace_misses` | Instance-wide, so only meaningful when the instance is a single-purpose cache |
| stats | `rejected_connections` | Non-zero means `maxclients` was hit |
| stats | `latest_fork_usec` | The pause a background save cost |
| clients | `connected_clients`, `blocked_clients` | Blocked clients sustained above zero means blocking reads are queueing |
| clients | `client_output_buffer_limit_disconnections` | Slow consumers being dropped |
| persistence | `rdb_last_bgsave_status`, `aof_last_write_status` | A silently failing save |
| persistence | `rdb_changes_since_last_save` | How much is currently unsaved |
| replication | `master_link_status`, replica `offset` lag | A replica serving stale data |
| commandstats | per-command `calls`, `usec_per_call` | Finds the one O(N) command behind the p99 |
| latencystats | per-command percentiles | Same, with the distribution |

`INFO` is a snapshot and `CONFIG RESETSTAT` zeroes the counters, so a scrape interval and a
restart both matter when reading a graph.

## SLOWLOG

- Records commands whose *execution* exceeded `slowlog-log-slower-than` microseconds — default
  10000, i.e. 10 ms `[verified]`. The time excludes network and the time spent waiting to be
  scheduled, so a command can be slow for the client without appearing here.
- `slowlog-max-len` is 128 entries by default `[verified]`: on a busy instance the interesting
  entry rolls out within seconds. Raise it, or scrape it.
- `SLOWLOG GET <n>` returns id, timestamp, duration in microseconds, the command with its
  arguments, and the client address and name. Naming clients (`CLIENT SETNAME`) is what turns
  that last field into an answer.
- `SLOWLOG RESET` clears it. Set the threshold to the latency budget, not to a round number —
  a 1 ms budget with a 10 ms threshold logs nothing.
- Setting `slowlog-log-slower-than 0` logs everything, which is a useful five-second experiment
  and a bad permanent setting.

## Latency monitoring

- `latency-monitor-threshold` is 0 by default, meaning disabled: `LATENCY DOCTOR` answers that
  monitoring is off rather than reporting health `[verified]`. Set it (in milliseconds) as part
  of provisioning, not during the incident.
- `LATENCY HISTORY <event>` and `LATENCY LATEST` report per-event spikes: `command`,
  `fork`, `expire-cycle`, `aof-write`, `eviction-del` and others. The event name is the
  diagnosis — `fork` points at persistence, `expire-cycle` at a mass expiry, `command` at an
  O(N) call.
- `redis-cli --latency` and `--latency-history` measure round-trip `PING` from the client, which
  includes the network and the queue behind a blocked server. Run it from the application's
  host: a fast `--latency` from the Redis host with a slow application means the problem is not
  Redis.
- `--intrinsic-latency <seconds>` measures what the kernel and CPU can do at all, which is the
  floor any tuning is measured against.

## Memory diagnosis

- `MEMORY USAGE <key> [SAMPLES n]` — bytes for one key including overhead. `SAMPLES 0` measures
  every element instead of sampling.
- `MEMORY STATS` — the breakdown: dataset, keys overhead, expires overhead, client buffers,
  replication backlog, AOF buffer, per-database totals.
- `MEMORY DOCTOR` — a prose summary, which declines to answer on a small or lightly loaded
  instance `[verified]`. Silence is not health.
- `redis-cli --bigkeys` — largest key per type by element count, via `SCAN`. Safe on a live
  instance, approximate by construction.
- `redis-cli --memkeys` — the same walk ranked by `MEMORY USAGE`, which is the number that
  actually matters.
- `redis-cli --hotkeys` — requires an LFU policy, because it reads `OBJECT FREQ`.
- Growth that is not data: client output buffers (a slow consumer of a big reply), the
  replication backlog, the AOF buffer during a stalled fsync, and fragmentation. Each shows up
  in `MEMORY STATS` under its own name.

## Connections and clients

- `CLIENT LIST` — one line per connection with `age`, `idle`, `cmd`, `multi`, `tot-mem` and
  buffer sizes. The way to find a connection parked in `blpop` or one whose output buffer is
  growing.
- `CLIENT INFO` — the same for the current connection.
- `CLIENT SETNAME` / `CLIENT SETINFO lib-name` — do this in every service. Without it
  `CLIENT LIST` and `SLOWLOG` identify callers only by ephemeral port.
- `CLIENT KILL ID <id>` / `LADDR` / `MAXAGE` — targeted disconnection, which is the safe way
  to clear a stuck consumer without restarting anything.
- `CLIENT NO-EVICT on` — exempts this connection from client eviction under
  `maxmemory-clients`, worth setting on an admin or monitoring connection `[verified]`.
- `CLIENT NO-TOUCH on` — this connection's reads do not update LRU/LFU metadata `[verified]`,
  so an inspection tool does not make cold keys look hot.
- `CLIENT UNPAUSE` / `CLIENT PAUSE <ms> [WRITE|ALL]` — used during a planned failover to stop
  writes briefly. Know it exists before you need it.

## A triage order that works

1. **Is it blocked or slow?** `INFO clients` (`blocked_clients`), `CLIENT LIST` for a stuck
   connection, `INFO stats` (`rejected_connections`). A blocked server is a different problem
   from a slow command.
2. **What is slow?** `SLOWLOG GET 25`, then `INFO commandstats` for the command mix. One O(N)
   command at a low rate explains more p99 than a million `GET`s.
3. **Is it memory?** `INFO memory` (`used_memory` vs `maxmemory`, fragmentation),
   `INFO stats` (`evicted_keys`, `expired_keys`), then `--memkeys`.
4. **Is it persistence?** `INFO persistence` (`rdb_last_bgsave_status`, `aof_delayed_fsync`,
   `latest_fork_usec`), `LATENCY LATEST` for `fork` and `aof-write` events.
5. **Is it replication?** `INFO replication` for link status and offset lag.
6. **Is it the network or the client?** `redis-cli --latency` from the application host versus
   from the Redis host, and `--intrinsic-latency` for the floor.

Quote the numbers from each step you ran. A conclusion without the counter that supports it is
a guess.

<!-- sources: redis-agent-skills, redis-io-docs, redis-oss, lude-kit-redis -->
