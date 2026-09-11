# Transactions, scripting and locks

Verified against: Redis 8.10.1.

## Contents

- [What atomicity means here](#what-atomicity-means-here)
- [MULTI/EXEC](#multiexec)
- [WATCH: optimistic concurrency](#watch-optimistic-concurrency)
- [Pipelines are not transactions](#pipelines-are-not-transactions)
- [Lua scripts](#lua-scripts)
- [Functions](#functions)
- [Choosing between MULTI, Lua and a function](#choosing-between-multi-lua-and-a-function)
- [Locks](#locks)
- [Why Redlock does not give what people think](#why-redlock-does-not-give-what-people-think)

## What atomicity means here

Redis gives **isolation**: while a transaction or a script runs, no other client's command
interleaves. It does not give **rollback**: there is no undo log, so a failure partway through
leaves the earlier writes in place.

Measured `[verified]`:

```
MULTI
INCR counter          -> QUEUED
LPUSH str x           -> QUEUED       (str holds a string)
INCR counter          -> QUEUED
EXEC
  1) 1
  2) WRONGTYPE Operation against a key holding the wrong kind of value
  3) 2
GET counter -> 2                      # both INCRs applied; nothing rolled back
```

```
MULTI
INCR counter2         -> QUEUED
NOSUCHCOMMAND a       -> ERR unknown command 'NOSUCHCOMMAND'
EXEC                  -> EXECABORT Transaction discarded because of previous errors.
GET counter2 -> (nil)                 # nothing ran
```

```
EVAL "redis.call('SET',KEYS[1],'first')
      redis.call('LPUSH',KEYS[2],'x')
      redis.call('INCR',KEYS[2])
      return 1" 2 la lb
  -> WRONGTYPE Operation against a key holding the wrong kind of value
GET la  -> "first"                    # the script's earlier write survived
TYPE lb -> list
```

So: errors detected **while queuing** (unknown command, wrong arity) abort everything; errors
detected **at execution** (wrong type, out of range, OOM) do not. A script must therefore
validate before it writes, because it cannot clean up after itself.

## MULTI/EXEC

- `MULTI`, then commands (each replying `QUEUED`), then `EXEC` which returns an array of
  replies in order. `DISCARD` throws the queue away.
- Command *syntax* is checked at queue time; *semantics* are not. `LPUSH` on a string key
  queues fine and fails at `EXEC`.
- The whole block is one unit on the wire when the client sends it as one write, so it is also
  one round trip — that, plus isolation, is most of why people use it.
- On Cluster every key in the block must hash to one slot, or the server rejects the `EXEC`.
- Nothing inside can branch on a value read inside the same transaction: replies only arrive
  after `EXEC`. Conditional logic needs `WATCH` or a script.

## WATCH: optimistic concurrency

`WATCH` marks keys; if any of them is modified by anyone before `EXEC`, `EXEC` returns nil and
nothing ran.

```
WATCH balance:42
current = GET balance:42
if current < amount:
    UNWATCH
    reject
MULTI
DECRBY balance:42 amount
LPUSH ledger:42 <entry>
EXEC            # nil means retry the whole read-check-write
```

- The retry loop is the application's responsibility, and it must be bounded. Under high
  contention on one key, the retries themselves become the load — that case wants a script.
- `WATCH` is per connection and is cleared by `EXEC`, `DISCARD` or `UNWATCH`. On a
  transaction-mode connection pool, a `WATCH` and its `EXEC` must be on the same leased
  connection, which is easy to get wrong.
- `WATCH` on a key that does not exist still works: creation counts as modification.

## Pipelines are not transactions

A pipeline is a batching optimisation: N commands written without waiting for each reply, then
all replies read. It removes N−1 round trips, which is usually the entire latency of a bulk
operation.

- Commands in a pipeline are **not** isolated; other clients' commands can interleave.
- Any command can fail independently, and the client must inspect each reply. A client library
  that raises on the first error may leave later replies unread on the socket.
- A pipeline that is too large blocks: the server buffers the whole batch's replies and both
  sides hold them in memory. Chunk bulk work into batches of a few hundred to a few thousand
  commands rather than one pipeline of a million.
- On Cluster a pipeline must be split per node by the client. A cluster-aware client does this;
  a single-node client pointed at one node returns `MOVED` for every key it does not own.
- Most client libraries fold `MULTI`/`EXEC` into their pipeline API as a flag. Setting that
  flag buys isolation and the Cluster single-slot requirement; leaving it off is the right
  default for independent reads.

## Lua scripts

`EVAL script numkeys key... arg...`, `EVALSHA sha1 ...`, `SCRIPT LOAD`, `SCRIPT EXISTS`,
`SCRIPT FLUSH`.

- A script runs to completion with nothing interleaved, which is how to make a
  read-then-conditional-write atomic without a `WATCH` retry loop.
- **Declare every key in `KEYS`.** Not a style rule: Cluster routes by the declared keys, and a
  key accessed without being declared makes the script incorrect on a cluster (and is rejected
  when it lands in another slot).
- Every key in one script must be in one slot on Cluster. A script that touches `cart:<id>` and
  a global counter must either bring them into one slot with a hash tag or move the counter out
  of the script.
- Keep scripts short. A long script blocks every other client for its whole duration; there is
  no preemption. `busy-reply-threshold` (formerly `lua-time-limit`) only controls when the
  server starts answering `BUSY` to *other* clients — it does not interrupt the script.
  `SCRIPT KILL` works only for a script that has not yet written.
- Scripts must be deterministic. Do not use `math.random` without seeding from an argument, do
  not read the clock inside the script, and do not iterate an unordered reply
  (`HGETALL`, `SMEMBERS`, `KEYS`) in a way that affects what you write — sort it first.
- `redis.call` raises on error and aborts the script; `redis.pcall` returns the error so the
  script can handle it. Since there is no rollback, validate with `redis.call` reads *before*
  any write.
- `EVALSHA` saves sending the body. Handle `NOSCRIPT` by falling back to `EVAL` — a restart or
  a `SCRIPT FLUSH` empties the cache, and a replica may not have the script.

## Functions

`FUNCTION LOAD` registers a named library that persists in the keyspace, is replicated, and
survives restart — unlike the ephemeral script cache.

```lua
#!lua name=applib
redis.register_function('cas_del', function(keys, args)
  if redis.call('GET', keys[1]) == args[1] then
    return redis.call('DEL', keys[1])
  end
  return 0
end)
```

```
redis-cli -x FUNCTION LOAD REPLACE < applib.lua      -> applib
SET lock:x token1
FCALL cas_del 1 lock:x token2 -> 0                   # wrong token, nothing deleted
FCALL cas_del 1 lock:x token1 -> 1                   # released
```

Both verified `[verified]`. `FUNCTION LIST`, `FUNCTION STATS`, `FUNCTION DUMP`/`RESTORE`, and
`FCALL_RO` for a read-only call that may run on a replica.

Prefer a function over an `EVALSHA` for anything permanent: it is deployed once, named, and
callable by name from every client without each client shipping the body. Keep `EVAL` for
one-off administrative work.

## Choosing between MULTI, Lua and a function

| Need | Use |
|---|---|
| Several independent commands, one round trip | Pipeline, no transaction |
| Several commands that must not interleave, no branching on values | `MULTI`/`EXEC` |
| Read a value, decide, then write — low contention | `WATCH` + `MULTI` with a bounded retry |
| Read a value, decide, then write — high contention or complex logic | Script |
| The same logic called from several services or languages | `FUNCTION LOAD`, call by name |

## Locks

A Redis lock is a **lease**. It is correct for coordination ("only one worker should refresh
this cache entry") and insufficient for correctness ("only one process may write this file").

```
# acquire
SET lock:<name> <random-token> NX PX <ttl_ms>     -> OK or nil        [verified]

# release, via a function or script so it is compare-and-delete
if GET lock:<name> == <token>: DEL lock:<name>
```

Rules that come from the failure modes:

- **`NX` and an expiry in the same command.** `SETNX` followed by `EXPIRE` leaves a permanent
  lock if the client dies between them.
- **A unique token per acquisition, and compare-and-delete on release.** A plain
  `DEL lock:<name>` lets a slow holder whose lease already expired delete the lock the *next*
  holder took, so two workers then run concurrently and neither knows.
- **The TTL is a bet on the work's duration.** Size it from the measured worst case. Extending
  it from a watchdog (re-`PEXPIRE` only if the token still matches) narrows the window but
  never closes it.
- **There is no fencing token.** Redis does not give you a monotonically increasing lock
  generation that the protected resource can check, so a paused holder that resumes after its
  lease expired *will* act. If the resource cannot reject a stale writer itself (a conditional
  write, a version column, an idempotency key), a Redis lock cannot make the operation safe.
- **Blocking acquisition** is a bounded retry loop with jitter, or `BLPOP` on a one-element
  list used as a semaphore. Never an unbounded spin.
- **Reentrancy does not exist.** If the same logical task can try to take the lock twice, the
  second attempt fails; encode the holder in the value and handle it explicitly.

## Why Redlock does not give what people think

The multi-node lock algorithm (acquire on a majority of independent Redis nodes, compare
elapsed time against the TTL) is often presented as making the lock safe. It changes the
availability story, not the safety story:

- It still has no fencing token, so the paused-holder problem above is unchanged.
- Its safety argument depends on bounded clock drift and bounded process pauses. A GC pause,
  a VM migration or an NTP step breaks the assumption, and none of those are observable from
  inside the algorithm.
- It needs genuinely independent nodes. Running it against a primary and its replicas gives
  nothing, because a failover can hand the same lock to a second holder — the single-node
  failure mode it was meant to remove.

Use a single-node lease for coordination and efficiency. When correctness depends on mutual
exclusion, put the invariant in the resource: a unique constraint, a conditional update on a
version, or an idempotency key the downstream service enforces.

<!-- sources: redis-agent-skills, redis-io-docs, redis-oss -->
