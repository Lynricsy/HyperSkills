# Cloudflare limits, defaults and version gates

Verified against: wrangler 4.131.0, workerd 1.20260910.1. Every number here was re-read from
`developers.cloudflare.com` rather than recalled. When a number decides an architecture — a
per-key write rate, a storage ceiling — quote it with its unit and say which plan it belongs
to, because most of them differ between Free and Paid.

## Contents

- [Workers plan limits](#workers-plan-limits)
- [CPU time versus wall time](#cpu-time-versus-wall-time)
- [Request, response and bundle limits](#request-response-and-bundle-limits)
- [Store limits side by side](#store-limits-side-by-side)
- [Static asset limits](#static-asset-limits)
- [Version and feature gates](#version-and-feature-gates)
- [Retired names that are still in circulation](#retired-names-that-are-still-in-circulation)
- [Invocation outcomes and error codes](#invocation-outcomes-and-error-codes)

## Workers plan limits

| Limit | Workers Free | Workers Paid |
|---|---|---|
| Requests | 100,000/day (resets midnight UTC) | no limit |
| CPU time per HTTP request | 10 ms (fixed) | 30 s default, 5 min ceiling |
| Memory per isolate | 128 MB | 128 MB |
| Subrequests per invocation | 50 | 10,000 default (raisable to 10M) |
| Subrequests to internal services | 1,000 | matches the configured limit |
| Simultaneous connections awaiting headers | 6 | 6 |
| Variables (secrets + text) per Worker | 64 | 128 |
| Variable size | 5 KB | 5 KB |
| Worker size (uncompressed) | 64 MiB | 64 MiB |
| Worker startup time | 1 s | 1 s |
| Workers per account | 100 | 500 |
| Cron Triggers per account | 5 | 250 |

The daily-request cap on Free is **Error 1027**, and the route's fail mode decides whether
exceeding it bypasses the Worker (fail open) or serves the error page (fail closed).

## CPU time versus wall time

CPU time counts only time the CPU spends executing your code. Waiting on `fetch`, KV, D1, R2
or a socket does not count. The average Worker uses about 2.2 ms; auth, SSR and large payload
parsing land around 10–20 ms.

| Trigger | CPU time | Wall time |
|---|---|---|
| HTTP request | 10 ms Free / 30 s default, 300,000 ms ceiling Paid | unlimited while the client stays connected |
| Cron Trigger | 10 ms Free / 30 s (< 1 h interval), 15 min (≥ 1 h interval) | 15 min |
| Queue consumer | as HTTP, `limits.cpu_ms` applies | 15 min |
| Durable Object alarm | as HTTP; each incoming request or WebSocket message resets the budget | 15 min |
| Durable Object RPC/HTTP | as HTTP | unlimited while the caller stays connected |
| Workflow step | as HTTP | unlimited per step |

Raising the ceiling is one field:

```jsonc
{ "limits": { "cpu_ms": 300000 } }  // default 30000; 300000 = 5 minutes, the maximum
```

`waitUntil()` extends execution for up to **30 seconds** after the response is sent or the
client disconnects. The runtime also gives in-flight requests a 30-second grace period across
its own (several-times-weekly) updates.

## Request, response and bundle limits

| Limit | Value |
|---|---|
| URL size | 16 KB |
| Request header size (total) | 128 KB |
| Response header size (total) | 128 KB |
| Response body size | not enforced by Workers (CDN cache limits still apply: 512 MB Free/Pro/Business, 5 GB Enterprise) |
| Request body size | 100 MB Free/Pro, 200 MB Business, up to 5 GB Enterprise (self-serve) |

Request body size follows the **Cloudflare zone plan**, not the Workers plan, and exceeding it
returns 413. `wrangler deploy --outdir bundled/ --dry-run` prints `Total Upload` — that
uncompressed number is what the 64 MiB limit measures; the `gzip` figure is informational.

## Store limits side by side

| | Workers KV | R2 | D1 | Durable Object (SQLite) | Queues |
|---|---|---|---|---|---|
| Consistency | eventually consistent, up to 60 s or more between locations | strongly consistent per object | serialised per database | serialised per object | at-least-once delivery |
| Same-key write rate | **1/second** | **1/second** (429 beyond) | n/a (single-threaded DB) | n/a (serialised) | 5,000 msg/s per queue |
| Value / object size | 25 MiB | 5 TiB object; 4.995 GiB single-part upload; 10,000 parts | 2 MB per string/BLOB/row | key+value ≤ 2 MB; 2 MB per row | 128 KB per message |
| Key size | 512 bytes | 1,024 bytes | n/a | n/a | n/a |
| Metadata | 1,024 bytes | 8,192 bytes | n/a | n/a | ~100 bytes internal, counts to message size |
| Total size | 1 GB Free / unlimited Paid | unlimited | 500 MB Free / **10 GB Paid, not raisable** | 10 GB per object | 25 GB backlog per queue |
| Count | 1,000 namespaces/account | 1,000,000 buckets/account | 10 DBs Free / 50,000 Paid | unlimited objects; 100/500 classes | 10,000 queues/account |
| Per-invocation ops | 1,000 external-service ops | counts as subrequests | 50 Free / 1,000 Paid queries | n/a | n/a |

Other numbers worth having exact:

- KV `cacheTtl` defaults to **60 seconds**, minimum 30 seconds. Raising it is the main KV read
  optimisation.
- KV Free write allowance is 1,000 writes/day **to different keys**; the same-key 1/second cap
  applies on both plans.
- D1: 100 columns per table, 100 KB SQL statement, 100 bound parameters, 32 function
  arguments, 50-byte `LIKE`/`GLOB` pattern, 30 s query duration (which also caps a `batch()`).
  Each database is one Durable Object and processes one query at a time; ~1,000 queries/second
  at 1 ms each, ~10/second at 100 ms each, then `overloaded`.
- Durable Objects: ~1,000 requests/second soft limit per individual object, then `overloaded`.
  Exceeding 10 GB fails writes with `database or disk is full: SQLITE_FULL` while reads and
  deletes keep working. Key-value-backed objects (legacy) cap keys at 2 KiB and values at
  128 KiB. WebSocket received-message size is 32 MiB.
- Queues: 100 messages per consumer batch, 100 messages or 256 KB per `sendBatch`, 100
  retries, 60 s max batch wait, 250 concurrent push consumers, 12 h `visibilityTimeout` for
  pull queues, 24 h `delaySeconds`. Retention defaults to 345,600 s (4 days), configurable
  60 s–14 days, fixed at 24 h on Free. Consumer defaults: `max_batch_size` 10,
  `max_batch_timeout` 5 s, `max_retries` 3 — and with no `dead_letter_queue`, messages that
  exhaust retries are **discarded**.
- R2 REST API: 1,200 requests per 5 minutes account-wide. Bucket management operations: 50/s
  per bucket. The `r2.dev` subdomain is rate limited and throttled and is not for production.
- D1 Time Travel: 30 days Paid / 7 days Free, 10 restores per 10 minutes per database.

## Static asset limits

| Limit | Workers Free | Workers Paid |
|---|---|---|
| Asset files per Worker version | 20,000 | 100,000 |
| Individual asset file size | 25 MiB | 25 MiB |

`_redirects` allows 2,000 static plus 100 dynamic rules (2,100 total), each declaration
limited to 1,000 characters.

## Version and feature gates

| Gate | What it unlocks |
|---|---|
| Wrangler 4.107+ | declarative Durable Object `exports` lifecycle map |
| Wrangler 3.73+ | versions/gradual-deployment commands without the `--x-versions` flag |
| Wrangler 3.40+ | gradual deployments at all |
| `@cloudflare/vitest-plugin` v1 | replaces `@cloudflare/vitest-pool-workers`; same API and Vitest config |
| `compatibility_date` ≥ 2024-04-03 | Durable Object RPC method calls on a stub |
| `compatibility_flags: ["nodejs_compat"]` | `node:*` built-ins, and what most npm packages need |
| API upload with no date | defaults to **2021-11-02**, before any flag took effect |

Version gates for wrangler come from `packages/wrangler/CHANGELOG.md` in
`cloudflare/workers-sdk`; runtime gates come from the compatibility-flags page. Do not infer a
gate from a release date.

## Retired names that are still in circulation

| Stale | Current |
|---|---|
| Bundled / Unbound usage models ("10 ms or 50 ms CPU") | Free 10 ms fixed; Paid 30 s default with a 5 min ceiling via `limits.cpu_ms` |
| `migrations` array as *the* Durable Object lifecycle | `exports` map; `migrations` is the legacy flow and mutually exclusive with it |
| `@cloudflare/vitest-pool-workers` | `@cloudflare/vitest-plugin` |
| `unstable_dev()` for tests | the Vitest plugin for unit tests, `createTestHarness()` for integration |
| `this.state` in a Durable Object | `this.ctx` |
| Pages as the default for new full-stack projects | Workers with static assets |
| DynamoDB-style external lock tables, KV-based counters | a Durable Object |

## Invocation outcomes and error codes

| Signal | Meaning | Where to look |
|---|---|---|
| `exceededCpu` / Error 1102 | CPU limit hit (`Worker exceeded resource limits`) | Workers Logs, Logpush `workers_trace_events`, dashboard Invocation Statuses |
| `exceededMemory` / Error 1102 | 128 MB isolate limit; often `Memory limit would be exceeded before EOF` while buffering | same |
| Error 1027 | Free daily request limit | dashboard |
| `overloaded` | a single Durable Object or D1 database is past its request/query rate | caller's exception |
| `SQLITE_FULL` | Durable Object hit its 10 GB storage ceiling; reads and deletes still work | caller's exception |
| `Cannot perform I/O on behalf of a different request` | an I/O object created in one request was used in another | runtime exception |
| `Illegal invocation` | a method was called without its receiver, typically a destructured `ctx` | runtime exception |
| `storage_type_mismatch` | an `exports` entry tried to change a provisioned namespace's storage backend | deploy output |
| `tombstone_delete_blocked_by_external_bindings` | another Worker still binds the namespace being deleted | deploy output |

<!-- sources: cloudflare-docs, workers-sdk, cloudflare-skills -->
