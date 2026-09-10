# Injection and in-process testing

Verified against: Node.js 24 LTS, Fastify 5.12, NestJS 12, Hono 4.13

## Contents

- [The seam is a factory](#the-seam-is-a-factory)
- [Substituting a dependency](#substituting-a-dependency)
- [In-process HTTP, not a port](#in-process-http-not-a-port)
- [The built-in runner](#the-built-in-runner)
- [Fixture lifetime](#fixture-lifetime)
- [Time, randomness and identifiers](#time-randomness-and-identifiers)
- [Real infrastructure versus a double](#real-infrastructure-versus-a-double)
- [A suite that hangs or flakes](#a-suite-that-hangs-or-flakes)

This file covers how to make a Node service exercisable. What deserves a test
at all, and how to drive design from tests, is the `test-driven-development`
skill's subject.

## The seam is a factory

Untestable code is almost always code that reaches out for its dependencies
instead of receiving them:

```ts
// Untestable: importing this module opens a pool and reads the environment.
import { pool } from '../db.ts'
export async function getOrder(id: string) {
  return pool.query('select * from orders where id = $1', [id])
}
```

Two consequences: a test cannot run without a live database, and nothing can
close the pool the import opened — which is also why the suite then hangs.

The fix is one function that takes what it needs and returns the wired app:

```ts
export type Deps = { db: Db; clock: () => Date; billing: BillingClient }

export function buildApp(config: Config, deps: Deps) {
  const app = createServer(config)
  app.register(orderRoutes, { deps })
  return app
}

// src/main.ts — the only place that constructs real dependencies
const app = buildApp(config, { db: createDb(config.database), clock: () => new Date(), billing: createBilling(config) })
```

`main.ts` stays the only module with side effects at import time. Everything
else is a function of its arguments, which is what makes both tests and a
second entry point (a worker, a CLI) possible.

Each framework has its own idiom for the same seam, and using the framework's
one is better than layering a second: Fastify uses plugin registration and
decorators, NestJS uses providers and module overrides, Hono uses closures or
typed `Variables`. See the branch reference.

## Substituting a dependency

Prefer a hand-written stub over a mocking framework for anything you own. A
stub is code — it type-checks against the real interface, so it breaks when the
interface changes, which is exactly when you want to know:

```ts
const billing: BillingClient = {
  charge: async () => ({ status: 'declined', code: 'INSUFFICIENT_FUNDS' }),
}
```

Reach for `mock.fn()` from `node:test` when the assertion is about the call
itself — that a retry happened three times, that the outbox row was written once
— and assert on `mock.calls`, not on the return value.

Module mocking (`mock.module()`, `vi.mock()`) is the last resort. It works
around a missing seam instead of adding one, and it silently stops matching the
real module after a refactor. If a test needs module mocking, the production
code usually needs a parameter.

## In-process HTTP, not a port

Every framework here can take a request without a socket. Use it:

| Framework | Entry point |
|---|---|
| Fastify | `await app.inject({ method: 'POST', url: '/orders', payload })` |
| Hono | `await app.request('/orders', { method: 'POST', body, headers })` |
| NestJS | `supertest(app.getHttpServer())` after `app.init()` |

This removes the port race that makes parallel suites flaky, keeps the
assertion on the real routing, validation and serialisation path, and needs no
teardown beyond closing the app. It is also the only way to assert on the
serialised body — a unit test of the handler function returns objects and
therefore proves nothing about the response schema.

One trap that costs an hour every time: a JSON body needs the matching
content-type header, or the framework does not parse it and the handler sees an
empty object. Hono documents this explicitly for its `app.request()`; Fastify's
`inject` sets it for you when you pass `payload` as an object but not when you
pass a string.

## The built-in runner

`node:test` needs no dependency, and the assertions come with it:

```ts
import { test, before, after } from 'node:test'
import assert from 'node:assert/strict'
import { buildApp } from '../src/app.ts'

let app: Awaited<ReturnType<typeof buildApp>>

before(async () => {
  app = buildApp(testConfig, { db: fakeDb(), clock: () => new Date('2026-01-01'), billing: stubBilling })
  await app.ready()
})
after(async () => { await app.close() })

test('rejects an order with no items', async () => {
  const res = await app.inject({ method: 'POST', url: '/orders', payload: { items: [] } })
  assert.equal(res.statusCode, 400)
  assert.equal(res.json().code, 'ORDER_EMPTY')
})
```

```bash
node --test                                    # discovers test files
node --test --test-only                        # only tests marked { only: true }
node --test --test-name-pattern='shutdown'     # by name
node --test --experimental-test-coverage       # coverage, no extra tool
node --test --watch                            # re-run on change
```

Vitest is the reasonable alternative when the project already uses it for
front-end code and wants one runner and one config. Do not add a second runner
to a project that has one.

`.ts` test files run directly on Node 22.6+ through type stripping, provided
they avoid enums, namespaces and parameter properties — the last one matters
because NestJS constructor injection is normally written with parameter
properties, so a NestJS project usually still compiles or uses a loader.

## Fixture lifetime

Build per test file, not per test, and not once for the whole run:

- Per test is slow and usually unnecessary; a fresh app per assertion hides the
  state leaks you want to find.
- Once globally means one test's data decides another's outcome, and the failure
  moves when you reorder.

Whatever a fixture opens, its teardown closes — in the same file. A resource
opened in `before` and closed nowhere is the hanging-suite bug from
`lifecycle-and-shutdown.md`.

## Time, randomness and identifiers

Anything non-deterministic enters through a dependency (`clock`, `uuid`,
`random`) rather than being called directly. Then a test sets it, and no test
needs a fake-timer library.

Where fake timers are genuinely needed — asserting a retry backoff, a scheduled
flush — `node:test` has `mock.timers`:

```ts
import { mock } from 'node:test'

mock.timers.enable({ apis: ['setTimeout'] })
const promise = retryingCall()
mock.timers.tick(1_000)
await promise
mock.timers.reset()
```

Always `reset()`. Leaked fake timers make every later test in the process wait
for a clock that no longer advances, and the failure appears in an unrelated
file.

## Real infrastructure versus a double

The rule that holds up: **test your logic against a double, test your queries
against the real engine.** An in-memory substitute for a database has different
SQL, different types and different constraint behaviour, so a green test against
it says nothing about production. Testcontainers (or a disposable local
instance) is the answer for the query layer; a stub is the answer for everything
above it.

For outbound HTTP, assert on the request you issued, not only on the stubbed
reply. A test that stubs `fetch` and checks the parsed result passes even when
the code sends the wrong path or forgets the idempotency key.

## A suite that hangs or flakes

Both symptoms have a short list of causes, and both are usually the production
bug appearing early:

**Hangs** — an open handle. Isolate to one file, enumerate handles (see
`lifecycle-and-shutdown.md`), and close it where it was created. Usual
suspects: a pool from a module-level import, a server bound to a port instead of
injected, an interval with no `clearInterval`, fake timers never reset.

**Flakes** — order dependence or a real race. Run the suspect file alone: if it
passes alone and fails in the suite, it is shared state (a module-level cache,
a mutated `process.env`, a database row another file wrote). If it fails alone
too, it is timing — an unawaited promise, a `setTimeout` used as a
synchronisation primitive, or an assertion on something the code only eventually
does.

Never paper over a flake with a retry or a sleep. A flaky test about
concurrency is usually reporting rule 12: the state is shared and production
hits it too.

<!-- sources: mcollina-skills, kadajett-nestjs, nodejs-docs, fastify-docs, hono-docs, nestjs-docs -->
