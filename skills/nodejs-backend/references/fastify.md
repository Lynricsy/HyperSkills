# Fastify branch

Verified against: Fastify 5.12

## Contents

- [Project shape](#project-shape)
- [Encapsulation is the whole model](#encapsulation-is-the-whole-model)
- [When to wrap in fastify-plugin](#when-to-wrap-in-fastify-plugin)
- [Hook order and what each one is for](#hook-order-and-what-each-one-is-for)
- [Decorators and per-request state](#decorators-and-per-request-state)
- [Schemas: validation and serialization](#schemas-validation-and-serialization)
- [Zod instead of JSON Schema](#zod-instead-of-json-schema)
- [Errors: the default handler leaks](#errors-the-default-handler-leaks)
- [Sending a response](#sending-a-response)
- [Timeouts and cancellation](#timeouts-and-cancellation)
- [Shutdown](#shutdown)
- [Logging](#logging)
- [Testing with inject](#testing-with-inject)
- [TypeScript](#typescript)

## Project shape

```
src/
  app.ts          buildApp(config, deps) -> FastifyInstance   (no listen here)
  main.ts         reads config, builds, listens, wires signals
  plugins/        cross-cutting: db, auth, metrics   (fastify-plugin wrapped)
  routes/         one file per route group           (plain plugins, prefixed)
```

The split matters: `app.ts` never calls `listen`, so tests get the same wiring
production has without binding a port. `main.ts` is the only module with side
effects at import time.

`@fastify/autoload` registers everything under `plugins/` and `routes/` by
directory convention. It saves a registration list; it also means a file's
position on disk is its wiring, so a misplaced file silently changes scope.

## Encapsulation is the whole model

Every `register()` creates a child context. Decorators, hooks and plugins added
inside are invisible to the parent and to siblings:

```ts
app.register(async (scope) => {
  scope.addHook('onRequest', requireAuth)   // applies only inside this scope
  scope.get('/profile', handler)
})

app.get('/health', handler)                 // no auth hook here
```

This is the feature to reach for constantly, and the one most often fought
against. Authenticated routes are a scope with an auth hook; public routes are
outside it. A rate limiter for one route group is a scope. No `if
(request.url.startsWith('/public')) return` inside a global hook — that check
is a scope boundary written by hand, and it will be wrong the day a route moves.

## When to wrap in fastify-plugin

`fastify-plugin` opts a plugin *out* of encapsulation, so its decorators and
hooks land in the parent:

```ts
import fp from 'fastify-plugin'

export default fp(async function db(app, opts) {
  const pool = createPool(opts)
  app.decorate('db', pool)
  app.addHook('onClose', async () => { await pool.end() })
}, { name: 'db', dependencies: [] })
```

The rule: **infrastructure is wrapped, features are not.** A database, a logger
child, an auth verifier are shared, so they are wrapped. A route group is
scoped, so it is not. Wrapping a route group makes its hooks global, which is
how an auth hook ends up on the health check.

Two details:

- Register the `onClose` hook in the same plugin that created the resource.
  Closing it from `main.ts` works until someone reorders registration.
- `name` and `dependencies` make load-order errors fail at boot with a readable
  message instead of at first request with `undefined is not a function`.

## Hook order and what each one is for

```
onRequest → preParsing → preValidation → preHandler → handler
          → preSerialization → onSend → onResponse
```

| Hook | Use it for | Do not |
|---|---|---|
| `onRequest` | request id, context store entry, cheap auth on headers | read the body — it is not parsed yet |
| `preParsing` | transform the raw payload stream | anything needing parsed values |
| `preValidation` | normalise a field before the schema sees it | reject on business rules |
| `preHandler` | authorization, loading the entity the route needs | anything the handler could do itself |
| `preSerialization` | reshape the payload object | assume it is a string |
| `onSend` | headers, last-chance payload rewrite (it is a string here) | expect to change the status |
| `onResponse` | logging, metrics | anything that can fail meaningfully |

`onResponse` runs **after the response is sent** and cannot change it. So a
database transaction must be committed inside the handler or the service it
calls — never in `onResponse`, where a failed commit cannot alter the 200 the
client already has. `onError` for rollback is fine; commit is not a hook's job.

Hooks of the same type run in registration order, and all of them must be
registered before `listen()`. Adding a hook or a decorator after the server
started throws (`FST_ERR_DEC_AFTER_START` for decorators).

## Decorators and per-request state

Three surfaces: `decorate` (instance), `decorateRequest`, `decorateReply`.

`decorateRequest` with a reference type is rejected at boot:

```ts
app.decorateRequest('ctx', { traceId: '', tenant: '' })   // FST_ERR_DEC_REFERENCE_TYPE
```

Fastify blocks it because that single object would be shared by every request,
so one request's `tenant` would be visible to another — a cross-tenant leak, not
a style problem. Two correct forms:

```ts
// 1. Declare without a value, fill in onRequest. Preferred: the hook can do work.
app.decorateRequest('ctx')
app.addHook('onRequest', async (req) => {
  req.ctx = { traceId: req.id, tenant: readTenant(req) }
})

// 2. Getter over a holder, when every request must have it lazily.
app.decorateRequest('holder')
app.decorateRequest('ctx', {
  getter() { return (this.holder ??= {}) },
})
```

Primitives are copied, so `decorateRequest('startTime', 0)` is fine. Keep the
declared shape close to the eventual one — the object's hidden class is created
once per request either way, and declaring `''` for a string keeps it monomorphic.

Never use an arrow function as a decorator body: it loses the `this` binding to
the request or reply.

## Schemas: validation and serialization

The `schema` option does two separate jobs, and the second is the one people
skip:

```ts
app.get('/orders/:id', {
  schema: {
    params: { type: 'object', required: ['id'], properties: { id: { type: 'string', format: 'uuid' } } },
    response: {
      200: {
        type: 'object',
        properties: { id: { type: 'string' }, total: { type: 'number' }, status: { type: 'string' } },
      },
    },
  },
}, async (req) => orders.byId(req.params.id))
```

- **Validation** compiles through Ajv. Body validation only runs for
  `application/json` unless the schema declares `content` per media type — so a
  route accepting `text/csv` is unvalidated unless you say so.
- **Serialization** compiles through `fast-json-stringify` and **drops any
  property not in the schema**. That is the mechanism that keeps a new database
  column out of the API, and it is also why a field can vanish from a response
  with no error anywhere: check the response schema before the query.

Ajv is configured to coerce types by default, which is what makes `?limit=10`
arrive as a number. On a JSON body that coercion can accept a client bug
silently, so consider a body-specific compiler with `coerceTypes: false` and
`additionalProperties: false` on write routes.

Register shared fragments with `app.addSchema({ $id, ... })` and reference them
by `$id`. Schema `$id`s are scoped like everything else, so a fragment added in
a child scope is not visible to a sibling.

Treat schemas as code: validation and serialization compile through
`new Function()`, so a schema built from user input is remote code execution.

## Zod instead of JSON Schema

For a project already modelling in Zod, connect it as a **type provider** rather
than parsing in handlers:

```ts
import { serializerCompiler, validatorCompiler, type ZodTypeProvider } from 'fastify-type-provider-zod'

app.setValidatorCompiler(validatorCompiler)
app.setSerializerCompiler(serializerCompiler)

app.withTypeProvider<ZodTypeProvider>().post('/orders', {
  schema: { body: CreateOrder, response: { 201: OrderView } },
}, async (req) => orders.create(req.body))   // req.body is typed from the schema
```

Parsing inside the handler (`CreateOrder.parse(req.body)`) throws away three
things: the framework's error shaping, the inferred request types, and the
compiled response serializer — so the response goes out through generic
`JSON.stringify` and the property-dropping guarantee is gone.

## Errors: the default handler leaks

Fastify's default error handler sends `statusCode`, `error`, `message` and
`code`, where `message` is `error.message` **verbatim, for every status
including 500**, and Fastify does not distinguish development from production.
An unhandled driver error therefore returns something like:

```json
{ "statusCode": 500, "code": "ER_BAD_FIELD_ERROR", "error": "Internal Server Error",
  "message": "Unknown column 'username' in 'field list'" }
```

So an error handler is mandatory, and it must branch on intent:

```ts
app.setErrorHandler((error, request, reply) => {
  request.log.error({ err: error }, 'request failed')   // the object, not .message

  if (error.validation) {
    return reply.status(400).send({ code: 'VALIDATION_FAILED', requestId: request.id })
  }
  if (error instanceof AppError) {                       // raised on purpose
    return reply.status(error.status).send({ code: error.code, requestId: request.id })
  }
  return reply.status(500).send({ code: 'INTERNAL', requestId: request.id })
})
```

Related traps:

- A response schema **replaces** the built-in error serializer for that status,
  so a schema declaring `stack` will serialise it. Do not put `stack` in a
  schema.
- `setNotFoundHandler` is separate and also scoped; without one, a 404 body has
  a different shape from every other error in your API.
- Errors thrown before routing — body too large, unparseable content type, bad
  URL — are answered by the framework, not by this handler. `frameworkErrors`
  is where those are shaped.
- Use `@fastify/error` (`createError(code, message, status)`) so codes are
  declared once rather than spelled inline.

## Sending a response

Return the payload from an `async` handler; that is the whole contract. Mixing
styles is where the confusion is:

- `return payload` — normal case.
- `return reply.send(payload)` — when you set headers or a status first, or
  when sending a stream. Returning `reply` tells Fastify the reply is handled.
- `reply.send(payload)` with no return in an `async` handler makes Fastify wait
  for the promise and then find the reply already sent. Add the `return`.
- Sending twice throws `FST_ERR_REP_ALREADY_SENT`. In a hook that rejects a
  request, `reply.send(...)` and then `return` — do not fall through.

A `Readable` returned from a handler is streamed with backpressure from the
socket; set `Content-Type` first, and know that once the stream starts the error
handler can no longer change the status.

## Timeouts and cancellation

- `requestTimeout` bounds receiving the request. It defaults to `0` (no limit),
  which is a denial-of-service surface when the service is exposed without a
  reverse proxy.
- `handlerTimeout` bounds the whole route lifecycle and can be set per route.
  It is **cooperative**: the 503 goes out and `request.signal` is aborted, but
  the handler keeps running until it observes the signal. Pass
  `request.signal` into `fetch`, driver calls and `pipeline` so the work
  actually stops.
- `keepAliveTimeout` defaults to 72 s and must be longer than the load
  balancer's idle timeout, or the balancer reuses a socket Fastify just closed
  and the client sees a sporadic 502.

## Shutdown

`app.close()` implements the drain from `lifecycle-and-shutdown.md`:

1. flags the instance closing — new requests get 503 with `Connection: close`
   (`return503OnClosing`, default `true`);
2. runs `preClose` hooks while in-flight requests are still active;
3. drains connections per `forceCloseConnections` (default `"idle"`: close idle
   keep-alive sockets, let in-flight requests finish);
4. stops accepting and waits for in-flight requests;
5. runs `onClose` hooks — where each plugin closes what it opened;
6. resolves.

So `await app.close()` is the whole HTTP part of shutdown. What it does not do
is close resources you registered outside an `onClose` hook, or exit the
process. Set `forceCloseConnections: false` only when a proxy already handles
draining, and never `true` on a service with slow requests — it destroys them
mid-response.

One trap the step list hides: **draining happens once, at step 3.** A
keep-alive socket that is still serving a request then, and only becomes idle
afterwards, is never revisited — so `server.close()` waits for it until
`keepAliveTimeout` (72 s by default), long past any sane drain budget.
Measured with one slow request on a keep-alive agent: `close()` had still not
resolved after 8 s. `forceCloseConnections: true` avoids it by destroying
in-flight responses, which is worse. The fix is to keep sweeping while
draining:

```ts
const sweep = setInterval(() => app.server.closeIdleConnections?.(), 250).unref()
await app.close()          // same test: resolved 50 ms after the slow request
clearInterval(sweep)
```

Connections still writing a response are unaffected by `closeIdleConnections`,
so this shortens shutdown without truncating anything. Alternatively set
`keepAliveTimeout` below the drain timeout and accept the extra reconnects.

## Testing with inject

```ts
const app = buildApp(testConfig, { db: fakeDb })
await app.ready()                      // plugins loaded, routes registered
const res = await app.inject({ method: 'POST', url: '/orders', payload: { items: [] } })
assert.equal(res.statusCode, 400)
assert.equal(res.json().code, 'VALIDATION_FAILED')
await app.close()
```

`inject` goes through the real routing, hooks, validation and serialization path
without a socket, so the assertion covers the response schema too. `await
app.ready()` is required — without it, plugin registration may not have
finished and the route 404s. Test a plugin in isolation by registering only it
and asserting `app.hasDecorator('db')`.

## TypeScript

Extend the interfaces once, in one `.d.ts` or module block:

```ts
declare module 'fastify' {
  interface FastifyInstance { db: Db }
  interface FastifyRequest { ctx: RequestContext }
  interface FastifyReply { problem(status: number, code: string): void }
}
```

Without this, every decorator access is an `any` cast and the compiler cannot
tell you that a decorator is missing in a scope.

For request and body types, prefer a type provider (JSON Schema via
`@fastify/type-provider-typebox`, or Zod as above) over hand-written generics on
the route: the generics drift from the schema and then lie.

Running `.ts` directly through Node's type stripping works for Fastify code
because it needs no decorators or `emitDecoratorMetadata`; keep enums,
namespaces and parameter properties out of the files you run that way.

<!-- sources: mcollina-skills, thecodepace-fastify, fastify-docs, nodejs-docs -->
