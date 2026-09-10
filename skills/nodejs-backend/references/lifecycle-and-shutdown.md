# Process and request lifecycle

Verified against: Node.js 24 LTS, Fastify 5.12, NestJS 12, Hono 4.13

## Contents

- [The four phases](#the-four-phases)
- [Startup: fail loudly, fail early](#startup-fail-loudly-fail-early)
- [Signals and the one shutdown path](#signals-and-the-one-shutdown-path)
- [Drain order](#drain-order)
- [Readiness versus liveness](#readiness-versus-liveness)
- [Timeouts and cancellation](#timeouts-and-cancellation)
- [Background loops](#background-loops)
- [Fatal errors](#fatal-errors)
- [A process that will not exit](#a-process-that-will-not-exit)
- [When to reach for worker threads](#when-to-reach-for-worker-threads)

## The four phases

```
boot        validate config -> open resources -> register routes -> listen
serving     accept -> route -> handle -> respond
closing     fail readiness -> refuse new -> finish in-flight -> close resources
exited      no open handles left; exit code says whether it was clean
```

Most production incidents in a Node service are a missing step in `closing`,
not a bug in `serving`. Deploys happen far more often than edge cases.

## Startup: fail loudly, fail early

Validate configuration before opening anything (see
`config-and-secrets.md`). Then open resources in a fixed order and remember
that order — shutdown walks it backwards.

Two failure modes worth naming:

- **Fire-and-forget initialisation.** A start hook that calls
  `this.pool.connect()` without awaiting it reports the process ready while the
  pool is still connecting, so the first requests fail with an error that has
  nothing to do with their input. Await every resource you claim to have opened.
- **Work in a constructor.** Reading a file or contacting a service from a
  constructor blocks the whole wiring phase and cannot be awaited or retried.
  Constructors assign; start hooks connect.

## Signals and the one shutdown path

An orchestrator sends `SIGTERM` and then waits out its grace period before
`SIGKILL`. `SIGINT` arrives from a terminal. Handle both through one function,
make it idempotent, and let it decide the exit code.

```ts
let closing = false

async function shutdown(signal: string): Promise<void> {
  if (closing) return          // a second SIGTERM must not start a second drain
  closing = true
  log.info({ signal }, 'shutting down')

  // Last resort only. The happy path exits because no handles are left open.
  const hardExit = setTimeout(() => {
    log.error('drain timed out; forcing exit')
    process.exit(1)
  }, DRAIN_TIMEOUT_MS).unref()

  try {
    await app.close()          // framework: refuse new, finish in-flight
    await broker.disconnect()  // then reverse creation order
    await pool.end()
    clearTimeout(hardExit)
  } catch (err) {
    log.error({ err }, 'shutdown failed')
    process.exit(1)
  }
}

for (const signal of ['SIGTERM', 'SIGINT'] as const) {
  process.on(signal, () => void shutdown(signal))
}
```

Three details that are easy to get wrong:

- `process.exit()` in the handler itself is the bug this whole file exists to
  prevent: it truncates every in-flight response and abandons open
  transactions. Reach for it only after the drain timeout has already fired.
- `.unref()` on the timeout keeps the timer from being the reason the process
  stays alive.
- The grace period configured in the orchestrator must exceed
  `DRAIN_TIMEOUT_MS`. If it does not, the platform kills the process before your
  own timeout ever runs and the timeout is decoration.

A shutdown coordinator library (`close-with-grace` is the usual choice in this
ecosystem) packages the same shape: one callback, a delay, and signal plus
fatal-error wiring. Use it if the project already depends on it; the invariant
is the order, not the package.

## Drain order

Close in reverse order of creation, and understand what "close" means for each
layer:

1. **HTTP acceptance.** Stop taking new connections and answer anything that
   still arrives with a 503 plus `Connection: close`, so the load balancer stops
   choosing this instance.
2. **In-flight requests.** Let them finish. This is the step that needs the
   timeout, because one hung request otherwise holds the process forever.
3. **Idle keep-alive connections.** These are not requests. They must be closed
   explicitly or the server never reports itself closed. Frameworks expose this
   as an option — Fastify's `forceCloseConnections` defaults to `"idle"`, which
   closes idle sockets while letting in-flight requests continue.
4. **Consumers and schedulers.** Stop pulling new work before closing the store
   it writes to, otherwise a consumer fails mid-message against a closed pool.
5. **Stores and clients.** Connection pools, caches, brokers, file handles.
6. **Timers and watchers.** Anything created with `setInterval` or a filesystem
   watcher keeps the event loop alive.

## Readiness versus liveness

They answer different questions and must not share a handler.

| Probe | Question | During shutdown | On a failed dependency |
|---|---|---|---|
| Liveness | Is this process still functioning? | keeps passing | keeps passing |
| Readiness | Should traffic be routed here? | fails immediately | fails |

Failing liveness during shutdown gets the process killed mid-drain, which is
exactly what the drain was avoiding. Passing readiness during shutdown keeps
traffic arriving at a closing process. Set the readiness flag in the first line
of the shutdown function, before anything else.

Checking dependencies inside a liveness probe is the other common mistake: a
brief database blip then restarts every replica at once.

## Timeouts and cancellation

Every inbound request needs a deadline and every outbound call needs one too,
otherwise a slow upstream converts into unbounded concurrency locally.

- Set a server-level request timeout, and a shorter one per route where the work
  is known to be quick.
- Propagate the incoming request's abort signal into the calls made on its
  behalf. `fetch`, `stream.pipeline` and most database drivers accept a
  `signal`, so a client hangup or a timeout stops the work behind it instead of
  leaving it to complete into a socket nobody is reading.
- A framework timeout is usually **cooperative**: it sends the error response
  but does not stop your handler. Fastify documents exactly this for
  `handlerTimeout` — the 503 goes out and `request.signal` aborts, but the
  handler's async work continues until it observes the signal. Without wiring
  the signal through, the timeout limits latency but not load.

## Background loops

A timer callback has no caller, so nothing catches what it rejects, and rule 7
means an unhandled rejection ends the process. Two guards, always both:

```ts
let running = false

async function tick(): Promise<void> {
  if (running) return          // no re-entry: a slow tick must not overlap
  running = true
  try {
    await flushOutbox()
  } catch (err) {
    log.error({ err }, 'outbox flush failed')   // never leave it unhandled
  } finally {
    running = false
  }
}

const timer = setInterval(() => void tick(), 1_000)
// shutdown: clearInterval(timer), then await the in-flight tick before closing
// the store it writes to.
```

Overlapping ticks are worse than a late tick: two flushes select the same
unsent rows and publish them twice. If the work must not be duplicated across
replicas either, the claim has to happen in the store (a conditional update),
not in the process.

## Fatal errors

The default for an unhandled rejection has been fatal since Node 15
(`--unhandled-rejections=throw`: emit `unhandledRejection`, and with no listener
raise it as an uncaught exception). That default is correct — the process has
reached a state nobody reasoned about.

So the handler you may register is a *reporting* handler, not a rescue:

```ts
process.on('uncaughtException', (err) => {
  log.fatal({ err }, 'uncaught exception')
  void shutdown('uncaughtException')     // drain, then exit non-zero
})
```

Registering an `unhandledRejection` listener that only logs is worse than
having none, because it disables the fatal default and the service keeps
serving from broken state. If a specific promise may reject, catch it there.

## A process that will not exit

`node --test` that hangs, "the process did not exit", a CI job that times out
after the suite passes: that is an open handle, not slow code. Something is
still referenced by the event loop.

Work it in this order:

1. Isolate to one file or one test, so the handle count is small.
2. Enumerate what is open. `why-is-node-running` (triggered by `SIGUSR1`) prints
   the remaining handles with the stack that created each one.
3. Fix it where it was created. A resource opened in a fixture is closed in
   that fixture's teardown; a timer created per request is cleared on the
   response path.
4. Re-run isolated, then the full suite. A handle leak that only appears in the
   full suite is usually shared module-level state (rule 12).

Common culprits: a `setInterval` with no `clearInterval`, a connection pool
never ended, a server bound to a port instead of tested in process (see
`testing-and-injection.md`), a `readline` interface left open, a listener added
per request to a long-lived emitter.

## When to reach for worker threads

Rule 21 says nothing synchronous and unbounded runs in a request path. When the
work is genuinely CPU-bound — image processing, large-document parsing,
cryptography beyond a single hash — the two real options are a worker thread
pool inside the process or a queue consumed by a separate process.

Choose the queue when the work can be asynchronous from the client's point of
view: it survives a restart, scales independently, and keeps the API process
uniform. Choose worker threads when the caller must wait for the result. Do not
choose either for I/O-bound work; awaiting I/O does not block the loop, and a
worker thread will only add serialisation cost.

<!-- sources: mcollina-skills, nodejs-docs, fastify-docs, nestjs-docs, kadajett-nestjs -->
