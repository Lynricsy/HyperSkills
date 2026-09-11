# Workers runtime semantics

Verified against: workerd 1.20260910.1 (wrangler 4.131.0). The failures below are runtime
failures, not style preferences — each one has an error string or a measurable consequence.

## Contents

- [The isolate model and what it forbids](#the-isolate-model-and-what-it-forbids)
- [Promise lifetime](#promise-lifetime)
- [Streaming and memory](#streaming-and-memory)
- [Handlers and platform classes](#handlers-and-platform-classes)
- [Service bindings and RPC](#service-bindings-and-rpc)
- [Serialization boundaries](#serialization-boundaries)
- [Crypto and secret comparison](#crypto-and-secret-comparison)
- [Error posture](#error-posture)
- [Cron Triggers, Smart Placement and routing](#cron-triggers-smart-placement-and-routing)
- [nodejs_compat](#nodejs_compat)

## The isolate model and what it forbids

A Worker runs in a V8 isolate that the runtime reuses across many requests, from many
different users, and a single isolate serves requests concurrently. Two consequences follow,
and almost every "it works locally" incident is one of them.

**Module-scope mutable state leaks across users.** Top-level `const` holding pure data is
fine; a `let` assigned inside a handler is shared with every later request the isolate serves.

```ts
// Anti-pattern — the first user's session is served to everyone after them
let cachedUser: User | null = null;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (!cachedUser) cachedUser = await env.SESSIONS.get(token, "json");
    return Response.json(cachedUser);
  },
};
```

Pass request state through arguments instead. Module scope is for stateless constants and
clients that hold no per-request data.

**I/O objects belong to the request that created them.** Streams, `Request`/`Response` bodies,
sockets and similar objects cannot be touched from another request's handler. Reproduced
locally:

```
Error: Cannot perform I/O on behalf of a different request. I/O objects (such as streams,
request/response bodies, and others) created in the context of one request handler cannot be
accessed from a different request's handler. This is a limitation of Cloudflare Workers which
allows us to improve overall performance. (I/O type: ReadableStreamSource)
```

That error is the diagnostic signature of caching a body, a stream, or a `Response` in module
scope. `[verified]`

The isolate is also where the 128 MB memory limit lives — per isolate, not per invocation. When
an isolate exceeds it the runtime lets in-flight requests finish and starts a new one; under
heavy load it may cancel incoming requests. `[official]`

## Promise lifetime

A promise that is not awaited, returned, or passed to `ctx.waitUntil()` is floating: the
runtime may cancel it when the response completes, and its rejection is swallowed.

```ts
// Correct — the result is needed before responding
const res = await fetch(url, { method: "POST", body });

// Correct — fire-and-forget work that must still finish
ctx.waitUntil(recordUsage(env, payload));

// Anti-pattern — cancelled on response, error invisible
fetch(webhookUrl, { method: "POST", body });
```

`ctx.waitUntil()` buys up to 30 seconds after the response is sent or the client disconnects.
It is for analytics, cache fills and webhooks — not for work whose result the caller needs.

Never destructure `ctx`: the methods validate their receiver.

```ts
const { waitUntil } = ctx;   // later: "Illegal invocation" [verified]
ctx.waitUntil(p);            // correct
const waitUntil = ctx.waitUntil.bind(ctx);  // correct if a bare function is genuinely needed
```

## Streaming and memory

Buffering an unbounded body is the standard way to OOM a Worker. `await response.text()`,
`.json()` and `.arrayBuffer()` on data of unknown size are the callsites to look for; bounded,
known-size JSON is fine.

```ts
// Pass a body straight through — no buffering
const upstream = await fetch(url);
return new Response(upstream.body, upstream);
```

```ts
// Concatenate several upstreams without holding them in memory
const { readable, writable } = new TransformStream();
ctx.waitUntil((async () => {
  for (const url of urls) {
    const res = await fetch(url);
    if (res.body) await res.body.pipeTo(writable, { preventClose: true });
  }
  await writable.close();
})());
return new Response(readable);
```

Two related habits: cancel bodies you do not read (`response.body.cancel()`) to free memory,
and keep Zod at 4.5.0 or later, since earlier versions retain substantially more heap per
schema and show up as OOMs. `[official]`

Six connections may be waiting for response headers simultaneously; a seventh queues until one
of them gets headers. `fetch`, KV `get`/`put`/`list`/`delete`, Cache `put`/`match`/`delete`, R2
`list`/`get`/`put`/`delete`/`head`, Queues `send`/`sendBatch`, `connect()` and outbound
WebSockets all count while connecting. A `Promise.all` over twenty subrequests therefore
serialises in groups rather than failing, which reads as unexplained latency.

## Handlers and platform classes

Where bindings come from depends on the shape you are in, and getting it wrong is the most
common type error in Workers code:

- Module-export handlers (`fetch`, `scheduled`, `queue`, `email`, `tail`) receive bindings as
  the `env` **parameter**.
- Platform base classes (`WorkerEntrypoint`, `DurableObject`, `Workflow`) reach them through
  `this.env`.

Other rules that survive in old code long after they stopped being correct:

- Platform classes are `extends`, never `implements`. `implements` type-checks and then loses
  `this.ctx` and `this.env` at runtime.
- Most platform classes import from `"cloudflare:workers"`.
- A Durable Object's state object is `this.ctx`; `this.state` is the old name.
- `ExecutionContext` is the third handler parameter and is required for `ctx.waitUntil()`.
- `env` can also be imported directly (`import { env } from "cloudflare:workers"`) when a
  module-level client needs a secret at construction time.

## Service bindings and RPC

Worker-to-Worker calls go through a service binding, not a public URL: no internet hop, no
credential, and type-safe RPC.

```ts
import { WorkerEntrypoint } from "cloudflare:workers";

export class AuthService extends WorkerEntrypoint<Env> {
  async verify(token: string): Promise<{ userId: string } | null> {
    return this.env.SESSIONS.get(token, "json");
  }
}

// caller
const session = await env.AUTH.verify(token);
```

Calling another Worker on the same zone through global `fetch()` without a service binding
fails. RPC stubs are request-scoped resources: they are disposed when the request ends, so a
stub cannot be stashed for a later request any more than a stream can. When targeting a Worker
in a named environment, the `service` field must name `<worker>-<environment>`.

## Serialization boundaries

Structured-clone support in one API says nothing about another. Check the specific boundary:

| Boundary | What is accepted |
|---|---|
| Queue message | must match `contentType`: `json` needs JSON-compatible data, `text` a string, `bytes` an `ArrayBuffer`, `v8` accepts structured-clone values such as `Map` and `Date` |
| Workflow step result | the documented serialization contract for steps, which is narrower than structured clone |
| Durable Object `storage.put()` | structured-clone values, so `Map`/`Set` are fine |
| Durable Object SQL bound parameters | only the SQL API's supported scalar types; encode objects explicitly |
| `WebSocket.send()` | string, `ArrayBuffer` or `ArrayBufferView`; serialise objects yourself |

## Crypto and secret comparison

`Math.random()` is not cryptographically secure — not for tokens, share links, upload keys or
IDs. Use `crypto.randomUUID()` or `crypto.getRandomValues()`.

Secret comparison needs constant time **and** equal lengths, because `timingSafeEqual` rejects
mismatched lengths and a length check of your own leaks the length:

```ts
async function secretsMatch(a: string, b: string): Promise<boolean> {
  const enc = new TextEncoder();
  const [da, db] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  return crypto.subtle.timingSafeEqual(da, db);   // both are 32 bytes
}
```

Hashing first is not decoration: it is what makes the call legal for arbitrary-length inputs.

## Error posture

`ctx.passThroughOnException()` is fail-open — a throwing Worker forwards the request to the
origin. On a Worker with no origin it produces confusing results, and in every case it hides
the exception you are trying to find. Catch, log structured, and return a structured error:

```ts
try {
  return Response.json(await handle(request, env));
} catch (error) {
  console.error(JSON.stringify({ message: "request failed", error: String(error) }));
  return Response.json({ error: "internal_error" }, { status: 500 });
}
```

Use it deliberately, if at all: a Worker that only adds an optional header in front of a real
origin is the case where failing open is the correct product decision.

## Cron Triggers, Smart Placement and routing

- Cron Triggers invoke the `scheduled` handler with a 15-minute wall-time budget, 30 s CPU for
  intervals under an hour and 15 min CPU at or above an hour. Limits are 5 triggers per account
  on Free and 250 on Paid.
- Smart Placement moves invocation closer to a back end when a Worker makes several round
  trips to the same origin or database. It helps a chatty origin-bound Worker and hurts a
  Worker whose job is to answer near the user; it is a config field, not a default.
- Routes have a fail-open/fail-closed mode that decides what happens when the Free daily
  request limit is exceeded. For security-bearing Workers, fail closed.
- Workers do not accept `fetch()` from another Worker on the same zone without a service
  binding; a Custom Domain is the documented exception.

## nodejs_compat

`compatibility_flags: ["nodejs_compat"]` enables the `node:*` built-ins (`node:crypto`,
`node:buffer`, `node:stream`, …). Many npm packages need it, and without it the failure is a
cryptic import error at runtime rather than at build time. Enabling it also makes
`process.env` a way to read variables and secrets, and makes `@types/node` worth installing —
`wrangler types` prints that recommendation itself.

<!-- sources: cloudflare-skills, cloudflare-docs -->
