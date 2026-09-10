# Structured logging and request context

Verified against: Node.js 24 LTS, pino 10, Fastify 5.12, NestJS 12, Hono 4.13

## Contents

- [One logger, JSON, stdout](#one-logger-json-stdout)
- [Log the error object, not its message](#log-the-error-object-not-its-message)
- [Redaction belongs in the logger](#redaction-belongs-in-the-logger)
- [Per-request child loggers](#per-request-child-loggers)
- [Why AsyncLocalStorage and not a field](#why-asynclocalstorage-and-not-a-field)
- [Entering the store once per request](#entering-the-store-once-per-request)
- [run versus enterWith versus withScope](#run-versus-enterwith-versus-withscope)
- [Diagnosing context loss](#diagnosing-context-loss)
- [What belongs in the store](#what-belongs-in-the-store)

## One logger, JSON, stdout

Write JSON to stdout and let the platform ship it. A log line that has to be
parsed with a regex cannot be queried, and interleaved `console.log` output from
several modules cannot be correlated at all.

```ts
import pino from 'pino'

export const log = pino({
  level: config.logLevel,               // from validated config, not NODE_ENV
  redact: ['req.headers.authorization', 'req.headers.cookie', '*.password'],
  formatters: { level: (label) => ({ level: label }) },
})
```

Pretty-printing is a local-development transport, never a production
dependency: it costs CPU per line and produces output the log store cannot
index. Keep it behind an explicit variable (`LOG_PRETTY`), which is the same
per-concern rule as rule 15.

Fastify has this logger built in — pass `logger: { ... }` to the factory instead
of constructing a second one, so request logging and your own logging share
serialisers and redaction.

## Log the error object, not its message

```ts
log.error({ err }, 'charge failed')      // serialiser records err.stack, err.code, err.cause
log.error(err.message)                   // stack thrown away, no code, no cause
```

The second form is the most common logging defect in a Node service, and it is
invisible until an incident: the log has a sentence and no stack, so nobody can
tell which of four call sites produced it.

In NestJS, the built-in `Logger` from `@nestjs/common` does not accept a
structured-metadata argument the way pino does — it stringifies the object into
the message. A project that wants structured logs replaces it (`nestjs-pino` is
the usual choice) rather than passing objects to the default logger and hoping.

## Redaction belongs in the logger

Configure `redact` paths once at construction. Redacting at call sites means
every future call site is a chance to leak, and the leak is permanent because
the log store already has the line.

Redact at minimum: `authorization` and `cookie` headers, `set-cookie`, anything
named `password`, `token`, `secret` or `apiKey`, and payment fields. Then check
what your framework logs by default — request logging that includes the full
header set or the request body will happily log a bearer token unless the
serialiser drops it.

## Per-request child loggers

Bind the request id once and let every line inherit it:

```ts
// Fastify does this for you: request.log is a child logger with reqId bound.
request.log.info({ orderId }, 'order accepted')
```

Elsewhere, create the child in the first middleware and put it in the request
context store, so code three layers down does not have to receive the logger as
a parameter.

The id itself: take it from the inbound header if the edge sets one
(`x-request-id`, or the W3C `traceparent` when there is tracing), otherwise
generate one with `crypto.randomUUID()`. Return it in the response — it is the
only thing that connects a user's screenshot to your logs, and it is what a 5xx
body carries instead of the error text.

## Why AsyncLocalStorage and not a field

Node handles concurrent requests on one thread with **one instance** of your
service class. A field on that instance is shared by every request in flight:

```ts
@Injectable()
class AuditService {
  private currentUserId: string | null = null      // shared by all requests

  bindRequest(userId: string) { this.currentUserId = userId }
  record(action: string) { log.info({ user: this.currentUserId, action }) }
}
```

Request A sets the field and awaits a query. Request B arrives during that await
and overwrites it. Request A resumes and logs B's user. The bug scales with
traffic, which is why it passes every test and appears only in production — and
why the symptom is "the audit log is occasionally wrong" rather than an error.

`AsyncLocalStorage` fixes it at the right level: the store is attached to the
asynchronous execution context, so each request's continuation reads its own
copy without threading a parameter through every function.

## Entering the store once per request

```ts
import { AsyncLocalStorage } from 'node:async_hooks'

type RequestContext = { requestId: string; userId?: string; log: pino.Logger }

const context = new AsyncLocalStorage<RequestContext>()

export function currentContext(): RequestContext {
  const store = context.getStore()
  if (!store) throw new Error('no request context: called outside a request')
  return store
}

// One entry point, as early in the request as possible.
app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] ?? crypto.randomUUID()
  context.run({ requestId, log: log.child({ requestId }) }, next)
})
```

Two things to get right:

- **Enter once, at the edge.** Entering again deeper in the stack creates a
  second store and the outer values disappear for that subtree.
- **Mutate the store, do not replace it.** Authentication runs after context
  creation, so it sets `store.userId`. Calling `run()` again with a new object
  gives the rest of the request a different store than the logger got.

Throwing when the store is missing is deliberate. Returning a default hides the
one case worth knowing about: code that is running outside any request — a
timer, a consumer, shutdown — and therefore has no request id to log. Those
paths create their own store explicitly.

Frameworks that provide this: NestJS via `nestjs-cls`, Hono via
`contextStorage()` from `hono/context-storage` (which is `AsyncLocalStorage`
underneath, and needs the `nodejs_als` compatibility flag on Cloudflare
Workers). Fastify has no built-in equivalent; a `fastify-plugin` wrapping the
`onRequest` hook is the idiomatic place.

## run versus enterWith versus withScope

| API | Scope | Use it when |
|---|---|---|
| `run(store, cb)` | exactly the callback and everything it awaits | the default — always this for a request |
| `enterWith(store)` | the rest of the current synchronous execution **and everything after it** in that turn | almost never |
| `withScope(store)` with `using` | the enclosing block, restored on exit (Node 24.20+/25.9+, Experimental) | synchronous blocks where the previous store must come back even on a throw |

`enterWith()` is the trap. It does not end with your function: entered inside
one event listener, it is still the current store for the *next* listener on
that same event. In a server that means one request's context becomes another's.
Reach for it only when there is no callback to wrap, and never on a request
path.

## Diagnosing context loss

`getStore()` returning `undefined` where you expected a store has a small set of
causes. Bisect by logging `getStore()` after each suspicious call; the last one
before `undefined` is the culprit.

- A callback-based API that does not preserve the context. Promisify it with
  `util.promisify` and it starts working, because native promises carry the
  context.
- A custom thenable or a hand-rolled promise implementation. Wrap the operation
  with `AsyncResource` so the callback runs in the right context.
- A listener registered on a long-lived emitter *outside* the request, then
  invoked during one. It runs in the context where it was registered, not where
  it fired. Bind it with `AsyncResource.bind` or
  `AsyncLocalStorage.bind(fn)` at registration time.
- A queue or worker boundary. Context does not cross a process or a thread;
  serialise the ids into the message and re-enter a store on the other side.

## What belongs in the store

Keep it small: request id and trace context, the authenticated principal, the
tenant, the child logger, and a deadline or abort signal. Everything in there is
implicit input to every function below, so a large store is a hidden parameter
list nobody can see.

What does not belong: the request and response objects (they keep the whole
socket alive and invite handler code to bypass the framework), mutable business
state (that is a parameter), and anything a background job would also need —
if a consumer needs it too, it is an argument, not context.

<!-- sources: mcollina-skills, kadajett-nestjs, myatminlu-nestjs, nodejs-docs, fastify-docs, hono-docs, nestjs-docs -->
