---
name: nodejs-backend
description: "Builds Node.js HTTP services with Fastify, NestJS, Hono or Express."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# nodejs-backend

Paths below are relative to this skill's directory.

## Scope

Server-side Node.js: the shape of a service that survives production. The
general layer — lifecycle, validation, errors, logging, configuration,
injection, streams, the event loop — is in `## Core rules` and applies whatever
the framework is. Framework-specific mechanics live in one branch reference per
framework, selected from `package.json` (rule 1).

Written against **Node.js 24 LTS**, Fastify 5, NestJS 12 and Hono 4. Rules that
need a newer runtime carry a version floor inline.

Not covered — do not answer from this skill:

- Next.js route handlers, server actions and React Server Components, and any
  React or client-side concern. Use the `react` skill.
- Type-level modelling: generics, conditional types, `tsconfig` design, domain
  modelling in the type system. Use the `typescript` skill; this skill covers
  the runtime side of the same code.
- What deserves a test and how to drive design from tests. Use the
  `test-driven-development` skill; this skill covers how to make a service
  injectable and how to exercise it in process.
- Working a reproducible local failure down to a root cause. Use the
  `debugging` skill; come back here for the Node-specific suspects.
- REST contract and OpenAPI design (resource modelling, URI and status-code
  choice, pagination style, versioning). Use the `api-design` skill.
- GraphQL schema design and operations. Use the `graphql` skill.
- Container images, Compose and Kubernetes deployment configuration. Use the
  `containers` skill; for the cloud infrastructure underneath it, use `terraform`.

## Core rules

Each rule is an invariant: violating it is a bug, a leak or a measurable
regression.

1. Read `package.json` before anything else and take the branch it names:
   `fastify` → `references/fastify.md`, `@nestjs/core` → `references/nestjs.md`,
   `hono` → `references/hono.md`, only `express` →
   `references/express-migration.md`. Also read `engines.node` and the start
   script. Every rule below lands differently per framework, and advice aimed
   at the wrong one is worse than no advice.
2. Target the active LTS line and state a floor whenever a rule depends on one.
   Node 20 is end-of-life; `--env-file`, `node:test` and type stripping all
   differ by line, so an unqualified "use X" is wrong on half of them.
3. Validate every request at the boundary with a schema, and give responses an
   output schema too. The input schema is the only thing keeping malformed data
   out of the service layer; the output schema is what stops a `select *` from
   shipping the column somebody added yesterday.
4. A 5xx body carries a status, a stable code and a correlation id — never the
   underlying error's text. Fastify's default handler forwards `error.message`
   and `error.code` verbatim on 500 and does not distinguish development from
   production, so a driver error publishes your schema and query text.
5. Every error carries a stable machine-readable `code`, and every wrapped error
   keeps the original in `cause`. Clients that branch on `message` break at the
   next reword, and a discarded `cause` turns a three-hop failure into an
   unanswerable log line.
6. One shutdown path per process: stop accepting, drain in-flight work, close
   resources in reverse order of creation, then exit — with a bounded timeout as
   the last resort. `process.exit()` inside a signal handler cuts responses
   mid-flight and abandons open transactions.
7. Never install an `unhandledRejection` or `uncaughtException` handler that
   keeps the process running. Since Node 15 an unhandled rejection is fatal by
   design; a process that survives an unknown error keeps serving from
   corrupted state. Log it, then hand over to the shutdown path in rule 6.
8. Every background loop — `setInterval`, queue consumer, outbox flusher —
   awaits its own work, catches its own errors and refuses to re-enter. A
   promise rejected inside a timer callback has no caller to catch it, and
   overlapping ticks double-process the same rows.
9. Readiness and liveness are separate endpoints, and readiness starts failing
   the instant shutdown begins. A single `/health` that stays green through
   shutdown keeps the load balancer sending traffic into a closing process.
10. Log JSON to stdout through one logger, with a per-request child logger
    carrying the request id. Concatenated strings cannot be queried, and
    logging `error.message` instead of the error object throws the stack away.
11. Redact secrets in the logger's configuration, not at call sites. One
    forgotten call site is a credential in your log store forever.
12. Request-scoped values — request id, tenant, user, trace context — live in an
    `AsyncLocalStorage` store entered once per request, never in a module-level
    variable or a field on a long-lived service. Node serves concurrent requests
    on one thread through one instance of that service, so the next request
    overwrites the field while the first is still awaiting.
13. Enter that store with `run()`, not `enterWith()`. `enterWith()` persists for
    the rest of the current synchronous execution, so it bleeds into every other
    listener on the same event.
14. Configuration is read once at startup, validated against a schema, and
    exposed as one typed frozen object. A missing variable must fail the boot,
    not the first request that happens to need it.
15. Give each concern its own environment variable instead of branching on
    `NODE_ENV`. One variable cannot mean log verbosity, rate-limit bypass and
    database choice at once. Keep `NODE_ENV` for the tools that genuinely read
    it (package managers, framework defaults) and hang no application behaviour
    on it.
16. Secrets arrive at runtime as environment variables or mounted files — never
    baked into an image, committed, logged, returned in an error body, or used
    as a metric tag.
17. Build dependencies at the edge and pass them in: a factory that returns the
    configured app, constructor parameters, or the framework's own provider
    mechanism. A handler that imports a live client module cannot be tested
    without that client, and nothing can close what it opened.
18. Exercise HTTP behaviour through the framework's in-process request entry
    point rather than by binding a port. It removes the port race, keeps the
    assertion on the real routing and serialization path, and needs no teardown
    beyond closing the app.
19. Anything unbounded — a query result set, a file, an upload, an upstream
    response — moves as a stream through `pipeline()` from
    `node:stream/promises`, and is never materialised into a string or array
    first. Memory then scales with the chunk size instead of the payload, and
    `pipeline` is what propagates the error and destroys the whole chain.
20. Honour backpressure: either let `pipeline` handle it, or check what
    `write()` returned and await the `drain` event. Ignoring the signal turns
    one slow consumer into unbounded buffering inside your process.
21. Nothing synchronous and unbounded runs in a request path: no `*Sync`
    filesystem call, no parse or stringify of a multi-megabyte payload, no
    hashing or compression loop. One blocked tick delays every other in-flight
    request on that instance, so the symptom appears on unrelated endpoints.
22. Measure before optimising, and quote the number in the answer:
    `--cpu-prof` for CPU, two heap snapshots for growth, event-loop delay for
    stalls. Both a missing index and a blocking loop look like "the endpoint is
    slow" from the outside.

## Workflows

**Stack detection (run first, every workflow).** The answers select the branch:

```bash
cat package.json                 # framework dep, engines.node, start/test scripts
node --version                   # what actually runs
ls src/*.ts src/**/*.module.ts 2>/dev/null | head
```

- `fastify` present → `references/fastify.md` governs plugins, hooks,
  decorators and schemas.
- `@nestjs/core` present → `references/nestjs.md` governs modules, provider
  scopes, filters and lifecycle hooks.
- `hono` present → `references/hono.md`; also check for `@hono/node-server`,
  without which the app has no Node entry point.
- Only `express` → the project is a migration candidate; use
  `references/express-migration.md` and pick the target framework before
  writing code.
- Two frameworks present → find out which one owns the HTTP entry point before
  advising; a NestJS project on `@nestjs/platform-fastify` follows the NestJS
  branch for wiring and the Fastify branch for the request lifecycle.

### implement-endpoint

- [ ] Run stack detection; read one existing endpoint and adopt its layering,
      error contract and naming instead of introducing a second convention.
- [ ] Declare the input schema and the response schema before the handler body
      (rule 3), using the branch's default validator.
- [ ] Keep the handler thin: parse, delegate to a service that takes its
      dependencies as parameters (rule 17), map the result.
- [ ] Decide the failure cases explicitly and give each a stable code (rules
      4–5). Nothing internal reaches the response body.
- [ ] Anything unbounded streams (rule 19); anything CPU-bound leaves the
      request path (rule 21).
- [ ] Read request context from the store, never from a service field (rule 12).
- [ ] Add an in-process test through the framework's request entry point (rule
      18); see `references/testing-and-injection.md`.
- [ ] **Gate — CLEAN BOOT AND GREEN INJECT:** the project's typecheck, lint and
      test commands pass; the app boots with the new route registered and no new
      startup warning; the new test fails when the handler is reverted.

### review-service

- [ ] Run stack detection and put the runtime and framework versions in the
      report header, so version-gated findings are unambiguous.
- [ ] Read the files in full. Report findings; do not rewrite the code unless
      asked.
- [ ] Walk the rule groups in this order, because it is the order in which they
      cause incidents: what the client can see (rules 3–5) → shutdown and
      background work (rules 6–9) → request context and concurrency (rules
      12–13) → configuration and secrets (rules 14–16) → streams and the event
      loop (rules 19–21) → injection and testability (rules 17–18).
- [ ] Check the branch reference for the framework-specific traps; most real
      defects in a Node service are framework mechanics, not general style.
- [ ] Drop any finding whose fix costs more than it returns, and say what you
      dropped — a report that lists every logging nit buries the leaked stack
      trace.
- [ ] **Gate — CITED AND ORDERED:** every finding carries `path:line`, one line
      of consequence and a concrete fix; findings are ordered by severity, not
      by file order; the report matches `## Output format`.

### harden-for-deploy

Run this before a service first takes real traffic, and after any change to
startup or shutdown.

- [ ] Trace the shutdown path end to end: signal received → readiness fails →
      new requests refused → in-flight requests finish → resources closed in
      reverse order → process exits (rule 6). Write down which line does each
      step; a step with no line is the bug.
- [ ] Confirm every long-lived resource created at startup — connection pools,
      brokers, caches, file handles, timers, watchers — has a matching close,
      and that a failure to close is logged rather than swallowed.
- [ ] Confirm readiness fails first and liveness stays honest (rule 9), and
      that the orchestrator's grace period is longer than the drain timeout.
- [ ] Set a timeout on every inbound request and every outbound call, and
      propagate cancellation from the incoming request's abort signal so a
      client hangup stops the work behind it.
- [ ] Audit what a 5xx returns for each failure class: a thrown domain error, a
      validation failure, an upstream timeout, an unexpected exception (rule 4).
- [ ] Audit the boot: every required variable validated (rule 14), no secret in
      the image or the logs (rules 11, 16).
- [ ] **Gate — DRAIN PROVED:** with the server under a slow request, sending
      SIGTERM returns that request's full response, refuses a new one, and the
      process exits on its own within the drain timeout — no `process.exit()`
      needed, no truncated response, exit code 0.

### diagnose-runtime

- [ ] Classify first; the four classes have different first moves: boot failure,
      wrong behaviour under concurrency, growing memory, or slow/stalled
      requests.
- [ ] Boot failure → read the failing validation or the framework's own startup
      error before changing anything; a config schema and a plugin/module
      registration error look alike in a stack trace but not in the message.
- [ ] Wrong behaviour only under load → suspect shared mutable state before
      anything else (rule 12): a field on a singleton, a module-level variable,
      a cached request object, a reference-typed request decorator.
- [ ] Growing memory → two heap snapshots under the same traffic, compare
      retained sizes, then look for the unbounded thing: a buffered response, an
      unbounded cache or map, a listener added per request.
- [ ] Slow or stalled → measure event-loop delay first. High delay means
      blocking work in the request path (rule 21); low delay with slow requests
      means the wait is downstream. A hung process that never exits is open
      handles, not slowness — enumerate them.
- [ ] State the fix as a causal chain from an observed number or log line, and
      repeat the same observation after the change.
- [ ] **Gate — NUMBER MOVED:** the metric that identified the problem is
      re-measured after the fix and reported as a before/after pair.

### migrate-from-express

- [ ] Pick the target from `references/express-migration.md` and record why;
      the mapping differs per target and half-migrations strand the codebase.
- [ ] Inventory the middleware chain in order, marking each entry as: replaced
      by a framework feature, replaced by a plugin, or genuinely custom.
- [ ] Move the shutdown, configuration and logging layers first. They are
      framework-agnostic and make the rest observable.
- [ ] Port one route group at a time behind a prefix, adding the schemas the
      Express version never had (rule 3), and keep the old and new stacks
      running side by side until the group's tests pass on the new one.
- [ ] **Gate — PARITY:** for each ported group, the same requests produce the
      same status codes, headers and bodies as the Express version, and the
      error responses are equal or narrower — never wider.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Signals, drain order, readiness/liveness, timeouts, background loops, worker threads | Anything about startup, shutdown, deploys, or a process that will not exit | `references/lifecycle-and-shutdown.md` |
| Boundary schemas, error taxonomy, `cause` chains, what a 5xx may contain | Writing or reviewing a handler, or an error body is wrong or too revealing | `references/validation-and-errors.md` |
| Structured logging, redaction, correlation ids, `AsyncLocalStorage` stores, context loss | Logs are unqueryable, a request id is missing, or the wrong user appears in a log line | `references/logging-and-request-context.md` |
| Config loading, schema validation, per-concern variables, secret delivery | Adding a setting, wiring a new environment, or auditing secrets | `references/config-and-secrets.md` |
| `pipeline`, async-generator transforms, backpressure, event-loop blocking, profiling | A large payload, an upload, an export, an OOM, or a latency investigation | `references/streams-and-event-loop.md` |
| Factory wiring, dependency substitution, in-process HTTP tests, hanging suites | Making code testable, or a test suite that leaks handles or flakes | `references/testing-and-injection.md` |
| Plugin encapsulation, `fastify-plugin`, hook order, decorators, JSON Schema and Zod type providers, `inject()` | `package.json` has `fastify` | `references/fastify.md` |
| Modules and boundaries, provider scopes, DI tokens, pipes, filters, interceptors, lifecycle hooks, `Test.createTestingModule` | `package.json` has `@nestjs/core` | `references/nestjs.md` |
| Middleware chain, validators and `c.req.valid`, typed `Variables`, `HTTPException`, streaming helpers, `contextStorage`, Node adapter | `package.json` has `hono` | `references/hono.md` |
| Middleware-to-framework mapping, error-handling differences, body parsing, target selection | `package.json` has `express` and the service is moving off it | `references/express-migration.md` |

## Output format

Use this shape for `review-service` and any other report on existing code.
Group by file, order by severity, no preamble — the reader wrote the code.

```
<path>
  L<line> <severity> - <what is wrong and what it costs>
       before: <the offending line, when one line makes it obvious>
       after:  <the fix>
```

Severities: `blocking` (data loss, wrong data served, secret or stack-trace
leak, requests dropped on deploy, cross-request state bleed), `important`
(unbounded memory, blocking call in a request path, missing schema, missing
timeout, untestable wiring), `minor` (naming, log shape, dead code).

End with one line: ship, ship after blocking fixes, or rework.

Worked example:

```
src/server.ts
  L18 blocking - the error handler sends error.message and error.stack, so a
       driver failure returns the query text and file paths to the caller.
       before: reply.status(500).send({ message: error.message, stack: error.stack })
       after:  request.log.error({ err: error }, 'unhandled')
               reply.status(500).send({ code: 'INTERNAL', requestId: request.id })
  L44 blocking - SIGTERM calls process.exit(0), so every in-flight response is
       truncated on each rolling deploy.
       before: process.on('SIGTERM', () => process.exit(0))
       after:  process.on('SIGTERM', () => app.close().then(() => pool.end()))
  L31 important - readFileSync blocks the event loop for the whole file and
       buffers it; every other request on this instance waits.
       after:  await pipeline(createReadStream(path), parseLines, insertBatch)

src/config.ts
  L7 important - PORT and DATABASE_URL are read with `?? default` at first use,
       so a missing DATABASE_URL fails on the first request instead of at boot.
```

## Environment

Node.js 24 LTS or newer; use the project's own package runner (`npm`, `pnpm`,
`yarn` or `bun`) as declared by `packageManager`.

```bash
node --run start                 # runs the package.json script, no shell wrapper
node --env-file=.env src/main.ts # load env without a dependency (Node 20.6+)
node --test --experimental-test-coverage   # built-in runner and coverage
node --cpu-prof src/main.ts      # writes a .cpuprofile for the flame graph
node --heap-prof src/main.ts     # sampling heap profile
node --watch src/main.ts         # restart on change, no nodemon
```

Running `.ts` files directly needs Node 22.6+ with type stripping, and the file
must avoid enums, namespaces and parameter properties; `references/fastify.md`
and `references/testing-and-injection.md` note where that matters.
