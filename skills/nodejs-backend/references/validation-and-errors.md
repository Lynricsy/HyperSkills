# Boundary validation and error handling

Verified against: Node.js 24 LTS, Fastify 5.12, NestJS 12, Hono 4.13

## Contents

- [Two schemas per endpoint](#two-schemas-per-endpoint)
- [Which validator to use](#which-validator-to-use)
- [Coercion and unknown properties](#coercion-and-unknown-properties)
- [Error taxonomy](#error-taxonomy)
- [Building errors](#building-errors)
- [What a response body may contain](#what-a-response-body-may-contain)
- [Where the error handler cannot reach](#where-the-error-handler-cannot-reach)
- [Logging an error once](#logging-an-error-once)
- [Retries and idempotency](#retries-and-idempotency)

## Two schemas per endpoint

The input schema and the output schema do different jobs, and skipping the
second one is the more expensive mistake.

- **Input schema** — rejects malformed data at the boundary, so the service
  layer never has to ask whether a field exists. It also documents the endpoint
  and, in Fastify, compiles into a fast validator.
- **Output schema** — decides what leaves the process. Without it, whatever the
  query returned is serialised, so a column added to the table this morning is
  in the API this afternoon. With it, unlisted properties are dropped.

That dropping cuts both ways: a response schema that omits a field you meant to
return silently removes it, and the endpoint looks broken with no error
anywhere. When a field disappears from a response, check the response schema
before checking the query.

## Which validator to use

Use the framework's native mechanism, because that is what the framework
compiles, reports and documents:

| Framework | Default | Reads validated data as |
|---|---|---|
| Fastify | JSON Schema in the route's `schema` option | `request.body` / `request.params` / `request.query`, already validated |
| NestJS | `class-validator` DTOs behind a global `ValidationPipe` | the typed DTO parameter |
| Hono | a Standard Schema validator middleware | `c.req.valid('json' \| 'query' \| 'param' \| 'header' \| 'form' \| 'cookie')` |

For a project that already models everything in Zod, keep Zod and connect it
through the framework's own extension point rather than parsing by hand inside
handlers — `fastify-type-provider-zod` for Fastify, `@hono/zod-validator` for
Hono, a Zod-backed pipe for NestJS. Hand-parsing in the handler loses the
framework's error shaping, its generated types, and in Fastify the compiled
serializer.

Never reach for the raw body after a validator has run. `await c.req.json()`
next to a validator middleware reparses the request and discards the validated
result; the same is true of reading `request.raw` in Fastify.

## Coercion and unknown properties

Query strings and path parameters arrive as strings, so validators coerce.
Fastify's Ajv instances coerce types by default, which is what makes
`?page=2` land as a number — and also what makes a schema-less endpoint accept
whatever the client sent. Know which of these your project has enabled:

- **Coercion on** — convenient for query and params; on a JSON body it can turn
  a client bug into silently wrong data.
- **Unknown properties removed** — a body property not in the schema is
  stripped before the handler sees it.
- **Unknown properties rejected** — the request fails instead. Prefer this on
  write endpoints: silently ignoring an unknown field means a client that
  misspelled `discount` believes the discount was applied.

In NestJS the equivalent is one pipe configuration, and the defaults are not
what you want: `new ValidationPipe()` on its own passes unknown properties
straight through. `{ whitelist: true, forbidNonWhitelisted: true, transform:
true }` is the production setting.

## Error taxonomy

Every error has three audiences and one field each:

| Field | Audience | Stability |
|---|---|---|
| HTTP status | caches, proxies, retry logic | fixed by the class of failure |
| `code` | client code that branches | stable forever; never reworded |
| correlation id | whoever reads the logs | per request |

The human-readable message is for humans only. A client that branches on
message text breaks at the next reword, so give it a code — `ORDER_NOT_FOUND`,
`PAYMENT_DECLINED` — and keep those codes in one module so they are typed at
every usage site and never quietly renamed.

Two classes to separate, because they get different treatment:

- **Expected** — validation failure, not found, conflict, upstream refusal. The
  client can act on it, so it gets a code and a message. Do not log these as
  errors; they are the API working.
- **Unexpected** — a bug, a driver failure, an exhausted pool. The client can do
  nothing except retry later, so it gets a generic body and a correlation id.
  Log it with the full error object.

The specific status codes, the response envelope and how the API versions its
errors are contract design and out of scope here — this skill only requires
that there be exactly one contract and that expected and unexpected errors are
distinguishable.

## Building errors

Attach the code where the error is created, and keep the original:

```ts
class AppError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
    options?: { cause?: unknown },
  ) {
    super(message, options)
    this.name = new.target.name
  }
}

// Wrapping: the cause is the only thing that explains a three-hop failure.
try {
  return await billing.charge(order)
} catch (err) {
  throw new AppError('charge failed', 'PAYMENT_UPSTREAM', 502, { cause: err })
}
```

Check errors by code, not by class. `instanceof` breaks across module instances
(two copies of a package in the tree, a worker boundary, a test double), and a
duck-typed check keeps working:

```ts
function hasCode(err: unknown, code: string): boolean {
  return err instanceof Error && (err as { code?: unknown }).code === code
}
```

Never swallow. An empty `catch` converts a failure into wrong data, which costs
more to diagnose than the crash it avoided. Either handle the error — meaning
you have a concrete recovery — or add context and rethrow.

## What a response body may contain

This is the single most commonly leaked surface in a Node service, because the
frameworks disagree about it and one of them is generous by default.

**Fastify** sends `statusCode`, `error`, `message` and `code` from its default
error handler, and the `message` is `error.message` verbatim — for every status
including 500. Fastify does not distinguish development from production. So an
unhandled `ER_BAD_FIELD_ERROR` returns the column name and the query text to
the caller. Registering an error handler that replaces the payload for anything
you did not raise deliberately is mandatory, not a hardening extra. Note also
that a route-level response schema replaces the built-in serializer, so a
schema declaring `stack` will happily serialise it.

**NestJS** returns the message for its own `HttpException` subclasses and a
generic `Internal server error` for everything else, which is the safer
default; the leak there comes from a hand-written filter that formats
`exception.message` for all cases.

**Hono** returns a bare `Internal Server Error` unless `onError` says otherwise,
so the leak comes from `onError` returning `String(err)` or `err.message`.

The invariant across all three: the branch that handles an error you did not
raise on purpose produces a body built from constants plus the correlation id.

## Where the error handler cannot reach

A global handler covers less than it looks like it does:

- **Before routing.** A malformed request line, a body over the size limit, a
  content-type with no parser, a TLS error: these are answered by the framework
  before your handler exists. Configure their responses rather than assuming
  the handler shapes them.
- **After the response started.** Once headers are sent — a streamed response, a
  file download — the handler cannot change the status. It must check for that
  and stop, otherwise it throws a second error while handling the first. In
  NestJS this is a `response.headersSent` check in the filter; with the Hono
  streaming helpers, `onError` is not invoked at all for an error thrown inside
  the stream callback, so the callback needs its own error handler.
- **Outside HTTP.** A NestJS `@Catch()` filter also runs for queue workers,
  gateways and microservice transports, where there is no HTTP response to
  write. Branch on the host type first (`host.getType()`), or the filter throws
  in the one context where the failure matters most.
- **Outside a request.** Timers, consumers and shutdown code have no request to
  attach an error to; they need their own logging (see
  `lifecycle-and-shutdown.md`).

## Logging an error once

Log where you have the most context and only there. The two failure modes are
mirror images: logging at every layer produces five entries per failure and the
stack is hard to match; logging nowhere leaves a 500 with no explanation.

The rule that works: rethrow with `cause` on the way up, log once in the error
handler, and pass the error object — not its message — to the logger so the
serialiser records `err.stack`.

## Retries and idempotency

Retry only what is safe to repeat, and only where you know the failure was
transient: a connection reset, a 429 or a 503 with a hint, a timeout on a read.
Never retry a 4xx other than 429, and never retry a non-idempotent write
without a client-supplied idempotency key that the store enforces.

Retries must be bounded and jittered, and the retry budget must fit inside the
caller's deadline — three attempts with a fixed 1 s backoff behind a 2 s client
timeout costs the upstream three times the load and returns nothing.

<!-- sources: mcollina-skills, myatminlu-nestjs, kadajett-nestjs, thecodepace-fastify, fastify-docs, nestjs-docs, hono-docs -->
