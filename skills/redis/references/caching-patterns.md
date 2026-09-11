# Caching patterns

Verified against: Redis 8.10.1.

## Contents

- [Cache-aside, and the write side](#cache-aside-and-the-write-side)
- [Avalanche: synchronised expiry](#avalanche-synchronised-expiry)
- [Stampede: many readers, one cold key](#stampede-many-readers-one-cold-key)
- [Penetration: keys that will never exist](#penetration-keys-that-will-never-exist)
- [Invalidation without KEYS](#invalidation-without-keys)
- [Sessions](#sessions)
- [Rate limiting](#rate-limiting)
- [Client-side caching](#client-side-caching)
- [Semantic caching for LLM responses](#semantic-caching-for-llm-responses)
- [What Redis will not do for you](#what-redis-will-not-do-for-you)

## Cache-aside, and the write side

The read path everyone writes correctly:

```
value = GET cache:<k>
if value is nil:
    value = load_from_source(k)
    SET cache:<k> serialize(value) EX <ttl + jitter>
return deserialize(value)
```

Three details that are usually missing:

1. **Every write carries a TTL.** `SET` without `EX` on a cache key is how a cache becomes a
   heap. If the TTL genuinely must be indefinite, the key is not a cache entry.
2. **The value is bytes.** Redis stores an opaque byte string; serialisation format, encoding
   and versioning are the application's problem. A client library that "serialises objects
   automatically" is doing it above the protocol, and a second service reading the same key in
   another language will not agree with it.
3. **The write path matters more than the read path.** Decide per key class:

| Write strategy | What happens on update | Use when |
|---|---|---|
| Invalidate (delete) | `DEL`/`UNLINK` the key; next read repopulates | Default. Simple, and never serves a value that was never true |
| Write-through | Write source, then `SET` the new value | Hot keys whose recompute is expensive; costs a stale window if the two writes interleave with another writer |
| Write-behind | Write cache, queue the source write | Only with a durable queue and an accepted loss window. Not a Redis decision — it changes the system's consistency model |

Invalidate-then-write and write-then-invalidate both have a race against a concurrent reader
repopulating from a stale source read. If the window matters, delete after the source commit
*and* set a short TTL so the worst case self-heals.

## Avalanche: synchronised expiry

A warm-up job, a deploy or a mass import writes thousands of keys with the same constant TTL.
They expire in the same second, every request misses, and the source takes the full load at
once — typically an hour after the job ran, which makes the cause hard to see.

Fix at the write, not the read:

```
SET cache:<k> v EX <base_ttl + random(0, base_ttl // 10)>
```

- Jitter proportional to the TTL (5–20%) is enough to spread the herd.
- For keys that must stay warm, refresh at ~80% of the TTL from a background task instead of
  letting them expire.
- Raising the TTL does not fix it; it moves the outage later and makes it larger.
- Check for a second synchronisation source: an eviction storm under `allkeys-lru` produces the
  same signature, and `INFO stats` distinguishes them (`expired_keys` versus `evicted_keys`).

## Stampede: many readers, one cold key

One hot key expires; every concurrent request misses and every one of them calls the source.

Single-flight with a lock key:

```
value = GET cache:<k>
if value is not nil: return value

if SET lock:<k> <token> NX EX 5 == OK:          # one winner
    value = load_from_source(k)
    SET cache:<k> v EX <ttl + jitter>
    <compare-and-delete lock:<k> if it still holds token>
    return value
else:                                            # losers
    wait briefly and re-GET, bounded retries
    or return the stale value if one is available
```

- The lock TTL must exceed the source call's worst case, or two callers recompute anyway. Pick
  it from the measured p99, not from a round number.
- Release with a compare-and-delete script so a slow winner cannot delete a lock the next
  holder took — see `references/transactions-and-scripting.md`.
- **Stale-while-revalidate** avoids the wait entirely: store the payload with a logical
  freshness timestamp inside it and a Redis TTL well beyond it. Readers past the logical
  deadline serve the stale value and trigger one refresh. This keeps p99 flat, at the cost of
  serving known-stale data for the refresh duration.
- Decide what the losers do explicitly. Unbounded waiting converts a cache miss into a thread
  pool exhaustion, which is worse than one slow request.

## Penetration: keys that will never exist

Requests for ids that do not exist in the source never populate the cache, so every one of them
reaches the database. A crawler or a scanner enumerating random ids is indistinguishable from
an attack.

- **Cache the negative result.** Write a sentinel the code can tell apart from a real payload
  (an empty marker, not an empty string that a real value could also be) with a short TTL —
  seconds to a minute — so a later insert is visible quickly.
- **Bloom filter in front** when the id space is unbounded or attacker-controlled
  (`BF.RESERVE ids 0.001 10000000`, then `BF.EXISTS ids <id>` before touching cache or source).
  No false negatives, so a "not present" answer is final; a false positive only costs one
  normal lookup. Bloom filters do not support deletion, so rebuild periodically from the source
  rather than trying to remove ids.
- **Validate the id shape first.** A UUID-shaped route parameter that is not a UUID never needs
  to reach Redis at all.
- Size the filter at `BF.RESERVE` time. An under-provisioned filter scales out and its false
  positive rate degrades from the configured value.

## Invalidation without KEYS

`KEYS product:*` blocks the single-threaded server for the whole keyspace walk, and `SCAN`
merely spreads the same total work across many round trips while other writes change the set
underneath. Neither is an invalidation mechanism.

Two shapes that work:

**Reverse index.** Maintain the mapping from a change to the keys it affects, at write time:

```
SADD cache:index:category:<cid> cache:product:<pid>    # when the entry is cached
# on a category change:
members = SMEMBERS cache:index:category:<cid>     # or SSCAN if large
UNLINK <members...>
DEL cache:index:category:<cid>
```

The index is itself a key that needs a TTL or explicit cleanup, and on Cluster the members and
the index must share a slot (hash tag) if you want to delete them in one call.

**Versioned prefix.** Keep a counter per class and put it in the key:

```
version = GET cache:ver:category:<cid>      # or INCR to invalidate
key     = f"cache:v{version}:product:{pid}"
```

One `INCR` invalidates the whole class in O(1); the old generation is unreachable and expires
on its own TTL. Costs one extra read per request unless the version is itself cached in-process
with a short TTL. This is the right default when a single change invalidates many keys.

For per-key invalidation on write, neither is needed: `UNLINK cache:product:<pid>` from the code
path that mutated the product.

## Sessions

- A session is a Hash, not a JSON string: the mobile client updating one field should issue
  `HSET session:<id> push_token <v>`, not read-modify-write of a multi-kilobyte blob.
- Sliding expiry is explicit. Every authenticated request either `EXPIRE session:<id> <ttl>` or
  writes with `KEEPTTL` plus a separate refresh — a plain `SET` of the payload silently makes
  the session immortal `[verified]`.
- With a Hash, `HEXPIRE` (7.4+) lets a short-lived field (a CSRF token, a step in a wizard)
  expire without touching the session's own TTL.
- Logout must delete the key, not just clear a cookie; otherwise a stolen session id stays
  valid for the remaining TTL.
- A session store is not a cache: it must not be evicted. Either give it its own instance with
  `noeviction`, or keep it on an instance whose policy is `volatile-*` and make sure everything
  *else* there has a TTL too.

## Rate limiting

Three shapes, in increasing cost and accuracy:

**Fixed window** — one counter per window, cheapest, allows a 2x burst at the boundary:

```
n = INCR rl:<subject>:<window>
if n == 1: EXPIRE rl:<subject>:<window> <window_seconds>
allow = n <= limit
```

The `INCR`-then-`EXPIRE` pair must be a script, or a crash between them leaves a counter with
no TTL that blocks the subject forever.

**Sliding window log** — a sorted set of request timestamps; exact, costs memory proportional
to the limit:

```
ZREMRANGEBYSCORE rl:<subject> 0 <now_ms - window_ms>
ZCARD rl:<subject>
ZADD rl:<subject> <now_ms> <unique_id>
EXPIRE rl:<subject> <window_seconds>
```

All four in one script — otherwise two concurrent callers both read a count below the limit.

**Token bucket** — a Hash of `tokens` and `last_refill`, refilled by elapsed time inside a
script. Handles bursts deliberately rather than accidentally.

In all three: prefix the key per limiter (`rl:search:<ip>`, `rl:login:<user>`) so two limiters
cannot consume each other's budget, and return the limit state to the caller — a `429` with
`Retry-After` derived from the window's reset time, not a bare rejection.

## Client-side caching

RESP3 client-side caching (client tracking) keeps a local copy in the application process and
has the server push an invalidation when the key changes. It removes the round trip entirely for
hot, rarely-written keys — feature flags, configuration, reference data.

- Requires RESP3 (`HELLO 3`) and client support; it is a protocol feature, not a config flag.
- Broadcast mode with a prefix (`CLIENT TRACKING on BCAST PREFIX config:`) sends invalidations
  for a whole prefix without the server tracking individual keys; default mode tracks the keys
  the client read, at server-side memory cost.
- Wrong for write-heavy data: the invalidation traffic exceeds the saved reads.
- The local copy is stale for the duration of the invalidation round trip. Anything that cannot
  tolerate a few milliseconds of staleness must not be locally cached.
- The cache is per process, so a large fleet multiplies the memory, and a process restart is a
  cold cache.

## Semantic caching for LLM responses

The mechanism: embed the prompt, search a vector index of previous prompts, and if the nearest
neighbour is close enough return its stored response instead of calling the model.

- Store prompt embedding, response, and the attributes you will need to filter on (model name,
  task type, tenant, prompt version) in one Hash or JSON document indexed by RQE, with a
  `VECTOR` field. `references/search-and-vectors.md` covers the index.
- **Get the threshold's direction right.** Some interfaces take a *similarity* (larger is
  stricter, ~0.9–0.95 typical); the Redis vector-library interface takes a *distance* (smaller
  is stricter). Copying a constant from the wrong convention inverts the behaviour and turns
  the cache into a random-answer generator. Confirm which one your client exposes, then measure
  the distance distribution over a few hundred real prompt pairs — pairs you consider
  equivalent and pairs you do not — and set the cut between the two clusters.
- **One cache per task.** A support question and a code question can be close in embedding
  space and have nothing to do with each other. Separate key prefixes and separate indexes, or
  one index with a mandatory attribute filter on task type.
- **One index per embedding model and dimensionality.** Changing the model invalidates every
  stored vector; there is no migration, only a rebuild, so the model name belongs in the index
  or key name.
- **Every entry gets a TTL.** LLM answers go stale with the underlying data, and a semantic
  cache without expiry is a permanent record of one day's model behaviour.
- Cache the prompt embeddings separately from the responses: the embedding of a repeated prompt
  is reusable even when the response must be regenerated, and the two have different natural
  lifetimes.
- Never semantically cache anything where a near-miss is harmful — prices, balances,
  entitlements, medical or legal answers. Exact-match caching on a normalised prompt hash is
  the safe variant there.

## What Redis will not do for you

- It will not tell you that two services disagree about a key's serialisation format.
- It will not make a cache coherent with its source. Every pattern above has a stale window;
  the choice is how long and who sees it.
- It will not enforce that every cache key has a TTL. That is a code review rule, and the
  measurable proxy is `INFO keyspace`'s `expires=` count against the key count for the prefix.
- It will not distinguish a cache read from a session read in `keyspace_hits`. Per-prefix hit
  ratios have to be measured in the application.

<!-- sources: redis-agent-skills, awesome-copilot-redis, redisvl, redis-io-docs -->
