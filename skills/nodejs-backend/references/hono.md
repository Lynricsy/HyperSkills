# Hono branch

Verified against: Hono 4.13

## Contents

- [Which runtime](#which-runtime)
- [Handlers return a Response](#handlers-return-a-response)
- [Middleware: await next, always](#middleware-await-next-always)
- [Typing the context](#typing-the-context)
- [Validators and c.req.valid](#validators-and-creqvalid)
- [Errors: HTTPException and onError](#errors-httpexception-and-onerror)
- [Composing an app from sub-apps](#composing-an-app-from-sub-apps)
- [Streaming](#streaming)
- [Request context with contextStorage](#request-context-with-contextstorage)
- [RPC and the typed client](#rpc-and-the-typed-client)
- [Shutdown on Node](#shutdown-on-node)
- [Testing](#testing)

## Which runtime

Hono is written against Web standards — `Request`, `Response`, `ReadableStream`
— and gets a runtime through an adapter. On Node it needs `@hono/node-server`;
without it the app exports a fetch handler nothing calls.

```ts
import { serve } from '@hono/node-server'
const server = serve({ fetch: app.fetch, port: config.port })
```

That is also the first thing to check in a Hono project that "does not start".
Node support requires 18.14.1+, 19.7.0+ or any 20+.

Because the same app can run on Workers, Deno, Bun or Node, be explicit about
which one the advice targets: `node:fs`, `AsyncLocalStorage` and process signals
exist on Node and not everywhere, and `c.env` means the Workers bindings object
on Workers and something else elsewhere.

## Handlers return a Response

```ts
app.get('/orders/:id', async (c) => {
  const order = await orders.byId(c.req.param('id'))
  return c.json(order)                   // the return is the response
})
```

There is no `res.send()`. Everything goes through `c.json()`, `c.text()`,
`c.html()`, `c.body()` or `c.redirect()`, and the value must be **returned**. A
handler that calls `c.json(...)` without returning it finalises nothing and
Hono raises "Context is not finalized".

Status and headers come from the same call or from `c.status()` / `c.header()`
before it: `return c.json(order, 201)`.

## Middleware: await next, always

```ts
app.use('*', async (c, next) => {
  const started = Date.now()
  await next()                            // without this the chain stops here
  c.header('x-response-time', String(Date.now() - started))
})
```

Two failure modes, both silent:

- **Not calling `next()`** ends the chain. Every route below is unreachable and
  nothing logs an error — the symptom is a route that "does nothing" or a
  finalisation error, not a stack trace pointing at the middleware.
- **Not `async`** while writing `await next()` is a syntax error; not awaiting a
  non-async `next()` means the "after" half of the middleware runs before the
  handler finished, so response-time headers and cleanup are wrong.

Middleware is onion-shaped: code before `await next()` runs on the way in, code
after runs on the way out with the response available as `c.res`. To reject a
request, `throw new HTTPException(...)` rather than returning a response from
middleware — the throw is what stops the chain unambiguously.

Order is registration order, and path-matched: `app.use('/admin/*', auth)` scopes
a middleware to a prefix, which is the equivalent of a route group.

## Typing the context

Declare the shape once on the app; `c.set` and `c.get` are then typed:

```ts
type Env = {
  Variables: { requestId: string; user: User }
  Bindings: { KV: KVNamespace }          // Workers only
}

const app = new Hono<Env>()

app.use('*', async (c, next) => {
  c.set('requestId', crypto.randomUUID())
  await next()
})

app.get('/me', (c) => c.json(c.get('user')))   // typed as User
```

Skipping this makes every `c.get()` return `any`, so a renamed variable fails at
runtime instead of at compile time. Sub-apps mounted with `app.route()` need the
same `Env` parameter or they lose the types at the boundary.

## Validators and c.req.valid

Validation is middleware. Read the result with `c.req.valid(target)` — never by
reparsing the request:

```ts
import { zValidator } from '@hono/zod-validator'
import * as z from 'zod'

const CreateExport = z.object({ table: z.enum(['orders', 'invoices']) })

app.post('/exports', zValidator('json', CreateExport), async (c) => {
  const { table } = c.req.valid('json')          // validated and typed
  return c.json(await exports.start(table))
})
```

Targets: `json`, `form`, `query`, `param`, `header`, `cookie`. Calling `await
c.req.json()` in a handler that has a validator reparses the body and throws the
validated value away, along with its types.

Note the `z.enum` above: an allow-list is what makes a value that reaches a data
layer safe. `z.string()` on a table name is a validated string and still an
arbitrary table.

Three things worth knowing:

- **The hook is the customisation point.** The third argument runs with the
  parse result, which is how one error shape is applied across an app:

  ```ts
  export const validate = <T extends z.ZodType>(target: 'json' | 'query', schema: T) =>
    zValidator(target, schema, (result, c) => {
      if (!result.success) throw new HTTPException(400, { cause: result.error })
    })
  ```

  Hooks are current API, not deprecated. Without one, the validator returns its
  own default error body, which will not match the rest of your API.

- **`json` and `form` require a matching `content-type`.** Without
  `Content-Type: application/json` the body is not parsed and the validator sees
  `{}` — so the request fails validation for a reason that has nothing to do
  with its content. This bites hardest in tests written with `app.request()`,
  where the header must be set explicitly.

- **`header` keys must be lowercase.** `value['Idempotency-Key']` is always
  `undefined`; use `value['idempotency-key']`. With a schema, that means the
  schema's keys are lowercase too.

`hono/validator`'s `validator(target, cb)` is the dependency-free form for a
one-off check. `@hono/standard-validator` accepts any Standard Schema library
(Zod, Valibot, ArkType) and is the right default for a project that has not
already committed to one.

## Errors: HTTPException and onError

`HTTPException` is how an intended status leaves any layer — middleware,
validator hook, service:

```ts
import { HTTPException } from 'hono/http-exception'

throw new HTTPException(404, { message: 'order not found' })
```

`app.onError` is the single place unexpected errors become responses, and it is
where the leak happens:

```ts
app.onError((err, c) => {
  const requestId = c.get('requestId')
  console.error({ requestId, err })                     // the object, with stack

  if (err instanceof HTTPException) return err.getResponse()   // intended
  return c.json({ code: 'INTERNAL', requestId }, 500)          // never String(err)
})
```

`return c.json({ error: String(err) }, 500)` publishes the internal error text —
driver messages, file paths, sometimes connection strings — to whoever called.
Hono's own default is a bare `Internal Server Error`, so an `onError` that
formats the error is strictly worse than none unless it branches on intent.

`app.notFound` sets the 404 body; without it a 404 has a different shape from
every other error in the API.

## Composing an app from sub-apps

```ts
const orders = new Hono<Env>()
orders.get('/', listOrders)
orders.get('/:id', getOrder)

app.route('/orders', orders)          // mounts at /orders and /orders/:id
```

Sub-apps are the unit of organisation and the unit of scope: middleware
registered on `orders` applies only there. Keep each sub-app in its own file
exporting the instance, and mount them all in one place, so the route table is
readable from a single file.

`app.basePath('/api/v1')` prefixes an entire app, which is the clean way to
version or namespace without editing every route.

## Streaming

Import the helpers from `hono/streaming`:

```ts
import { stream, streamText, streamSSE } from 'hono/streaming'

app.get('/exports/:id', (c) => {
  c.header('Content-Type', 'text/csv; charset=utf-8')
  return stream(c, async (s) => {
    s.onAbort(() => void cursor.close())          // client hung up: stop the work
    for await (const row of cursor) {
      await s.write(encoder.encode(toCsvRow(row)))   // await = backpressure
    }
  })
})
```

- `stream` for bytes, `streamText` for text (sets chunked encoding and
  `nosniff`), `streamSSE` for server-sent events with `writeSSE` and `sleep`.
- **Await every `write`.** That await is where backpressure lives; a loop that
  ignores it buffers the whole payload inside the process, which is the OOM this
  helper exists to prevent.
- **Register `onAbort`.** Without it a client disconnect leaves the cursor, file
  handle or upstream request running to completion for nobody.
- **`onError` does not fire for an error thrown inside the callback.** The
  response has already started, so it cannot be replaced. The streaming helpers
  take an error handler as their third argument — use it, and accept that the
  status is already sent.

To send a Node stream, convert at the boundary: `c.body(Readable.toWeb(nodeStream))`.

## Request context with contextStorage

```ts
import { contextStorage, getContext } from 'hono/context-storage'

app.use(contextStorage())

// Anywhere below, without threading `c` through every signature:
const requestId = () => getContext<Env>().var.requestId
```

This is `AsyncLocalStorage` underneath, so the general rules in
`logging-and-request-context.md` apply — including that the store does not cross
a queue or worker boundary. `tryGetContext()` returns `undefined` instead of
throwing when there is no context, which is what code shared with a background
job should call.

On Cloudflare Workers it needs the `nodejs_als` (or `nodejs_compat`)
compatibility flag; on Node it works as-is.

## RPC and the typed client

Chaining route definitions produces a type the client can consume:

```ts
const routes = app.post('/orders', zValidator('json', CreateOrder), (c) => c.json(created, 201))
export type AppType = typeof routes

// client
import { hc } from 'hono/client'
const client = hc<AppType>('https://api.example.com')
const res = await client.orders.$post({ json: { items: [] } })
```

The type comes from the **chained** value, not from `app` — assigning routes
separately loses it. And the export must be the type, not the app instance;
exporting the app drags the server code into the client bundle.

This couples client and server at the type level, which is a feature in a
monorepo and a liability across a published API boundary. For a public API,
generate a specification instead — which is contract design, out of scope here.

## Shutdown on Node

`serve()` returns the Node HTTP server, so the drain from
`lifecycle-and-shutdown.md` is available:

```ts
const server = serve({ fetch: app.fetch, port: config.port })

async function shutdown() {
  await new Promise<void>((resolve, reject) =>
    server.close((err) => (err ? reject(err) : resolve())),
  )
  server.closeIdleConnections?.()   // otherwise keep-alive sockets hold the process
  await pool.end()
}
```

Hono itself has no shutdown lifecycle — it is a router over `fetch`, with no
`onClose` equivalent. Every resource the app opened is closed by the code that
opened it, from this one function. Idle keep-alive connections must be closed
explicitly or `server.close()` never completes.

## Testing

```ts
const res = await app.request('/exports', {
  method: 'POST',
  body: JSON.stringify({ table: 'orders' }),
  headers: { 'Content-Type': 'application/json' },   // required, or the body is {}
})
assert.equal(res.status, 200)
assert.deepEqual(await res.json(), { id: 'e1' })
```

`app.request()` takes a path or a `Request` and returns a `Response` without a
socket, so it exercises the real middleware chain, validators and handlers. The
content-type header is not optional: Hono's validators do not parse a `json`
body without it and the test then fails on validation rather than on behaviour.

Because dependencies are usually closures or `Variables`, substitution is a
constructor parameter on the sub-app factory:

```ts
export const buildOrders = (deps: Deps) => new Hono<Env>().get('/', (c) => c.json(deps.orders.list()))
```

That keeps the app a pure function of its dependencies, which is rule 17 with no
container involved.

<!-- sources: secondsky-hono, hono-docs, nodejs-docs -->
