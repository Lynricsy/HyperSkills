# Migrating an Express service

Verified against: Express 5.2, Fastify 5.12, NestJS 12, Hono 4.13

This is the only file in this skill that covers Express, because Express is not
where a new Node service starts. It ships no validation, no serialization, no
structured logging and no shutdown drain, so every rule in `SKILL.md` lands on
an Express codebase as "add another library" — which is exactly the argument for
moving. The real question in an Express project is therefore *how to get off
it*, and that is what this file answers.

If the project is staying on Express 4, do the 4 → 5 step first: it is small,
mechanical, and closes real gaps (async error propagation, dotfile serving)
that would otherwise be carried into the target framework.

## Contents

- [Express 4 to Express 5 first](#express-4-to-express-5-first)
- [Choosing the target](#choosing-the-target)
- [Order of work](#order-of-work)
- [Middleware mapping](#middleware-mapping)
- [Request and response API mapping](#request-and-response-api-mapping)
- [Error handling](#error-handling)
- [Validation arrives with the migration](#validation-arrives-with-the-migration)
- [Running both stacks during the move](#running-both-stacks-during-the-move)
- [Parity check](#parity-check)

## Express 4 to Express 5 first

Express 5 needs Node 18+. The changes that actually break running code:

- **Path syntax.** A bare `*` must be named: `/*` becomes `/*splat`, and
  `/{*splat}` if it must also match the root. `?` for optional segments is gone
  — `/:file.:ext?` becomes `/:file{.:ext}`. Regex characters in a path string
  are no longer supported; use an array of paths instead. Parentheses, square
  brackets, question mark, plus and exclamation mark are now reserved
  characters in a path and need escaping with a backslash.
- **`req.params`** has a null prototype for string paths, wildcard captures are
  **arrays** rather than strings, and unmatched parameters are omitted instead
  of present-and-empty. Code doing `req.params.hasOwnProperty(...)` or relying
  on `''` breaks.
- **`req.body` is `undefined`** when no body parser ran, where Express 4 gave
  `{}`. Every `req.body.foo` on an unparsed route now throws.
- **`req.query`** is a getter (no longer assignable) and the default parser is
  `simple` instead of `extended`, so nested bracket syntax stops producing
  nested objects.
- **`express.urlencoded()`** defaults to `extended: false`.
- **`express.static()`** defaults `dotfiles` to `"ignore"` and now applies the
  check to hidden *directories* too, so `/.well-known/...` returns 404 unless
  you pass `dotfiles: 'allow'`. This silently breaks ACME challenges and app
  links.
- **Removed signatures.** `res.send(body, status)`, `res.json(obj, status)`,
  `res.redirect(url, status)` (argument order flipped), `res.send(status)` (use
  `res.sendStatus`), `res.sendfile` (now `res.sendFile`), `req.param(name)`,
  `app.del()`, `res.redirect('back')`.
- **`res.status()`** only accepts 100–999 and throws otherwise; `res.vary()`
  throws without an argument.
- **`app.listen`** passes a listen error to the callback instead of throwing, so
  a callback that ignores its first argument now swallows `EADDRINUSE`.

The genuine improvement: **a rejected promise from an async handler or
middleware is forwarded to the error handler**, as if `next(err)` had been
called. So the `.catch(next)` wrappers and `asyncHandler` helpers that every
Express 4 codebase accumulated can go.

`npx codemod@latest @expressjs/v5-migration-recipe` mechanises most of the
removed signatures. Run it, then read the diff — the path-syntax and
`req.params` changes need judgement.

## Choosing the target

Pick one and record why; a half-migration leaves two conventions and no
benefit.

| Target | Choose it when | What it costs |
|---|---|---|
| **Fastify** | The service is a JSON HTTP API on Node and you want validation, serialization and logging without assembling them. Closest conceptual move: middleware → hooks, `app.use` scoping → plugin encapsulation. | Learning the plugin/encapsulation model; Express middleware needs `@fastify/middie` or replacement. |
| **NestJS** | The codebase is large, several teams touch it, and you want enforced module boundaries and DI. Its default platform *is* Express, so the HTTP layer can stay identical while the structure changes. | Decorators, a container, and a build step; substantial ceremony for a small service. |
| **Hono** | The service is small, or it must also run on Workers/Deno/Bun, or it is edge-deployed. | A Web-standard API (`Request`/`Response`) rather than `req`/`res`, so every handler body changes. |

Two honest non-answers: if the service is a thin proxy with three routes and no
growth expected, migrating buys little — apply the general rules in place. And
if the team has no capacity to finish, do not start; an Express service with
correct validation, logging and shutdown beats a half-migrated one.

## Order of work

1. **Express 4 → 5** if applicable (above), on its own, with tests green.
2. **Configuration** — one validated module (`config-and-secrets.md`). No
   framework dependency, and it makes everything after this observable.
3. **Logging and request context** — structured logger, request id, context
   store (`logging-and-request-context.md`). Still framework-independent.
4. **Shutdown** — the drain path (`lifecycle-and-shutdown.md`). Express has no
   built-in drain, so this is new code either way; writing it now means the
   migration does not also have to invent it.
5. **Routes, one group at a time** — behind a prefix on the new framework,
   adding schemas as you go.
6. **Delete the Express entry point** when the last group has moved. Until then
   it is the production path.

Steps 2–4 are the ones that pay off even if the migration stalls, which is why
they come first.

## Middleware mapping

Inventory the middleware chain **in order**, and classify each entry:

| Express middleware | Fastify | NestJS | Hono |
|---|---|---|---|
| `express.json()` | built in (content-type parsers) | built in | built in via `c.req.json()` / validators |
| `express.urlencoded()` | built in | built in | built in |
| `cors` | `@fastify/cors` | `app.enableCors()` | `hono/cors` |
| `helmet` | `@fastify/helmet` | `helmet()` middleware | `hono/secure-headers` |
| `compression` | `@fastify/compress` | `compression()` middleware | `hono/compress` |
| `express-rate-limit` | `@fastify/rate-limit` | `@nestjs/throttler` | `hono-rate-limiter` |
| `morgan` | built-in request logging | replaced logger | `hono/logger` |
| `cookie-parser` | `@fastify/cookie` | `cookie-parser` middleware | `hono/cookie` |
| `multer` | `@fastify/multipart` | `FileInterceptor` | `c.req.parseBody()` |
| `express-session` | `@fastify/session` | `express-session` middleware | `hono-sessions` |
| custom auth middleware | `onRequest`/`preHandler` hook in a scope | guard | middleware on a path prefix |
| custom `next(err)` middleware | `setErrorHandler` | exception filter | `app.onError` |
| `app.use('/admin', guard)` | a `register()` scope with a hook | module + guard | `app.use('/admin/*', ...)` |

Two structural notes:

- **Path-prefixed `app.use` is scoping done by hand.** In Fastify that is a
  registered scope, in Hono a path-matched middleware, in NestJS a module. Do
  not port the `if (req.path.startsWith('/public')) return next()` check inside
  a global middleware — express it as a boundary and it stops being wrong when a
  route moves.
- **Express-compatible middleware adapters exist** (`@fastify/middie`,
  Nest's `app.use`) and are the right escape hatch for one genuinely custom
  middleware you do not want to rewrite yet. They are not a migration strategy:
  middleware running through an adapter does not participate in the new
  framework's hooks, error handling or typing.

## Request and response API mapping

| Express | Fastify | NestJS (Express platform) | Hono |
|---|---|---|---|
| `req.body` | `request.body` (validated) | DTO parameter | `c.req.valid('json')` |
| `req.params.id` | `request.params.id` | `@Param('id')` | `c.req.param('id')` |
| `req.query` | `request.query` | `@Query()` | `c.req.query()` |
| `req.headers.x` | `request.headers.x` | `@Headers('x')` | `c.req.header('x')` |
| `res.status(201).json(x)` | `return x` / `reply.code(201).send(x)` | `return x` + `@HttpCode(201)` | `return c.json(x, 201)` |
| `res.send(text)` | `return text` | `return text` | `return c.text(text)` |
| `res.set('h', v)` | `reply.header('h', v)` | `@Header('h', v)` | `c.header('h', v)` |
| `res.redirect(302, url)` | `reply.redirect(url, 302)` | `@Redirect(url, 302)` | `c.redirect(url, 302)` |
| `stream.pipe(res)` | `return stream` | `StreamableFile` | `stream(c, ...)` |
| `next(err)` | `throw err` | `throw err` | `throw err` |
| `next()` in middleware | omit (hooks return) | `next()` | `await next()` |

The pattern behind the table: Express hands you a mutable `res` and you write
to it; all three targets take a **returned value** and serialise it. That is
what makes response schemas and typed responses possible, and it is the part of
the diff that looks largest and matters least.

## Error handling

Express error handling is an arity-4 middleware registered last, and errors are
routed to it by `next(err)` — or, in Express 5, by a rejected promise.

What changes, and it changes for the better: in all three targets a thrown error
reaches one handler without a `next` to remember, and the handler is registered
declaratively rather than by position. Port it as one handler that branches on
intent (see `validation-and-errors.md`), and take the opportunity to stop
sending internal messages — an Express error handler that does
`res.status(500).json({ error: err.message })` is the most copied snippet in
the ecosystem and it leaks.

Watch the ordering trap on the way out: in Express, a handler registered before
a route never sees that route's errors. That positional rule disappears, so a
migration that mechanically keeps "register the error handler last" is
harmless — but a migration that keeps *several* error middlewares in a specific
order needs each of them classified first, because only one of them survives.

## Validation arrives with the migration

Most Express codebases validate ad hoc — a few `if (!req.body.email)` checks, or
`express-validator` on some routes. The migration is when schemas appear, and
that is most of the value:

- Every route gets an input schema, so the handler stops checking for
  `undefined`.
- Every route gets a response schema (Fastify), a serializer
  (`ClassSerializerInterceptor` in NestJS) or an explicit response type (Hono),
  so the response stops being "whatever the query returned".
- `express-validator` chains become one schema per operation. Do not port the
  chains; they encode the same rules in a form the new framework cannot compile
  or type.

This is also the step that changes behaviour, which is why the parity check
below is per group: a route that previously accepted an unknown field now
rejects it, and that is a deliberate change to write down rather than a
regression.

## Running both stacks during the move

Two workable arrangements:

- **Reverse proxy split.** Both processes run; the proxy routes moved prefixes
  to the new one. Cleanest rollback (change one route rule), needs a deploy
  path for two services.
- **Mount inside one process.** Keep the Express app and let unmigrated paths
  fall through to it: `@fastify/express` for Fastify, `app.use(expressApp)` in
  NestJS. One process, one deploy — but both middleware chains are live at
  once, so the request context store must be entered on the outer one and read
  by both. This arrangement is **not available for Hono**: `app.mount()` takes
  a fetch-style `(Request) => Response` handler, and an Express app is not one,
  so a Hono migration uses the proxy split.

Either way, put shutdown in the new stack and have it close the Express server
too; two independent signal handlers race.

## Parity check

Per route group, before deleting the Express version:

- Same status code, headers and body for the happy path, byte for byte where
  the body is not intentionally reshaped.
- Error responses **equal or narrower**. Narrower is the goal (no more leaked
  messages); wider is a regression and the one direction to fail the check on.
- Auth behaviour unchanged: every route the Express middleware protected is
  covered by a hook, guard or path-matched middleware in the new stack. Check
  the routes that were protected *by position* in the chain — those are the ones
  a migration silently opens.
- Deliberate differences written down: fields now rejected, fields now dropped
  by a response schema, a 400 where there used to be a 500.

<!-- sources: express-docs, mcollina-skills, kadajett-nestjs, secondsky-hono, fastify-docs, nestjs-docs, hono-docs -->
