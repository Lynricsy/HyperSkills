# Actions, middleware, sessions and typed env

Verified against: Astro 7.3

## Contents

- [When an action beats an endpoint](#when-an-action-beats-an-endpoint)
- [Defining actions](#defining-actions)
- [Calling actions from the client](#calling-actions-from-the-client)
- [Form actions (no client JavaScript)](#form-actions-no-client-javascript)
- [Form input validation](#form-input-validation)
- [Displaying field errors](#displaying-field-errors)
- [Errors and status codes](#errors-and-status-codes)
- [Action security](#action-security)
- [Calling actions from server code](#calling-actions-from-server-code)
- [Middleware](#middleware)
- [Sessions](#sessions)
- [Typed environment variables](#typed-environment-variables)

## When an action beats an endpoint

An action is a typed server function callable from the client, from an HTML form
or from other server code. It parses the request, validates the input with Zod
and returns `{ data }` or `{ error }`. Use one for a mutation your own app
performs; use an endpoint when an external caller needs a stable HTTP contract,
or when you must control the exact response shape.

Everything below requires the route to render on demand.

## Defining actions

All actions are exported from the `server` object in `src/actions/index.ts`:

```ts
// src/actions/index.ts
import { defineAction, ActionError } from "astro:actions";
import { z } from "astro/zod";

export const server = {
  likePost: defineAction({
    input: z.object({ postId: z.string() }),
    handler: async (input, ctx) => {
      if (!ctx.cookies.has("session")) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Log in to like a post." });
      }
      return await like(input.postId);
    },
  }),
};
```

Group related actions in nested objects to get namespaced call sites
(`actions.user.createUser()`):

```ts
// src/actions/user.ts
export const user = { getUser: defineAction(/* … */), createUser: defineAction(/* … */) };
// src/actions/index.ts
export const server = { user };
```

`z` comes from `astro/zod`. Omitting `input` entirely hands the handler the raw
`FormData` or parsed JSON instead of a validated object.

## Calling actions from the client

```ts
import { actions } from "astro:actions";

const { data, error } = await actions.likePost({ postId });
if (error) { /* handle */ } else { /* use data */ }
```

Check `error` before `data` — that is what narrows `data` to defined. To skip the
check deliberately, `actions.likePost.orThrow({ postId })` returns the data and
throws instead.

Results are serialised with devalue, not `JSON.stringify`, so `Date`, `Map`,
`Set` and `URL` survive the round trip — and the raw network response is not
readable as JSON. Inspect the returned `data`, not the response body.

To navigate after success, use `navigate()` from `astro:transitions/client`
rather than assigning `location.href`, so client-side routing is preserved.

## Form actions (no client JavaScript)

```astro
---
export const prerender = false;
import { actions } from "astro:actions";

const result = Astro.getActionResult(actions.createProduct);
if (result && !result.error) return Astro.redirect(`/products/${result.data.id}`);
---
<form method="POST" action={actions.createProduct} enctype="multipart/form-data">
  <!-- … -->
</form>
```

Four requirements, each of which fails quietly on its own:

1. `export const prerender = false` on the page. A prerendered page has no
   request to post to. `[official]`
2. `accept: 'form'` on the action. Without it the action expects JSON and the
   submission never validates. `[official]`
3. `method="POST"` and `action={actions.name}` — the object stringifies to the
   query the server dispatches on.
4. `enctype="multipart/form-data"` when the form has a file input, otherwise
   `z.instanceof(File)` never matches. `[official]`

`Astro.getActionResult(action)` returns `{ data }` / `{ error }` when that action
ran during this request and `undefined` otherwise, which is how one page both
renders the form and reacts to its submission.

## Form input validation

With `accept: 'form'`, Astro parses the submission into an object keyed by each
input's `name`, then validates it. The per-type conventions: `[official]`

| Input | Validator |
|---|---|
| `type="text"` and most others | `z.string()` |
| `type="number"` | `z.number()` |
| `type="checkbox"` | `z.coerce.boolean()` |
| `type="file"` | `z.instanceof(File)` |
| Repeated `name` | `z.array(…)` |

Empty submitted inputs become `null`, not `""` — except arrays and booleans. A
schema of `z.string()` on an optional text field therefore fails on an empty
submission; use `.nullable()` or `.optional()` deliberately.

For a form that carries a discriminator field, `z.discriminatedUnion('type', […])`
narrows the handler's input type per branch instead of forcing every field
optional.

## Displaying field errors

```astro
---
import { actions, isInputError } from "astro:actions";
const result = Astro.getActionResult(actions.newsletter);
const fieldErrors = isInputError(result?.error) ? result.error.fields : {};
---
<input name="email" type="email" required aria-describedby="email-error" />
{fieldErrors.email && <p id="email-error">{fieldErrors.email.join(", ")}</p>}
```

`isInputError()` distinguishes validation failures from thrown errors and gives
`fields`, keyed by input name. Native HTML validation (`required`, `type`,
`pattern`) still belongs on the inputs — it is the cheap first pass.

## Errors and status codes

`ActionError` carries a human-readable `code` (`NOT_FOUND`, `UNAUTHORIZED`,
`BAD_REQUEST`, …) that maps to an HTTP status, so failures are visible in
production logs and the client can branch on `error.code`. Returning `undefined`
from a handler instead loses both the status and the reason.

## Action security

Every action is reachable as a public endpoint at `/_actions/<name>` — the
dotted path for nested actions (`/_actions/blog.like`). Middleware guards on the
page do not protect it. Authorize inside every handler, exactly as for an API
route. `[official]`

For a coarse gate in front of all actions, `getActionContext()` in middleware
exposes the inbound action name and whether it came from an RPC call or an HTML
form, and lets you reject the request before the handler runs. It is a gate, not
a substitute for per-handler authorization. The same function supplies
`setActionResult()` / `serializeActionResult()` for persisting a form result
across a redirect; the older `serializeActionResult` / `deserializeActionResult`
imports were removed.

## Middleware

`src/middleware.ts` (or `src/middleware/index.ts`) exports a named `onRequest`
— never a default export:

```ts
import { defineMiddleware, sequence } from "astro:middleware";

const auth = defineMiddleware(async (context, next) => {
  context.locals.user = await userFromCookie(context.cookies);
  return next();
});

export const onRequest = sequence(auth, logging);
```

- Return a `Response` or the result of `next()`. Doing neither is an error.
- `context.locals` is the channel to pages, endpoints and actions; it must stay a
  serialisable object and must not be reassigned wholesale.
- `sequence()` composes middleware; each wraps the rest, so code after `await
  next()` runs on the way out and can post-process the response body.
- `next(path)` rewrites in place without re-running the chain, and the following
  middleware sees the updated context. It rebuilds the `Request`, so consuming
  `Request.body` before or after throws — which is exactly what breaks HTML form
  actions. Rewrite from the page with `Astro.rewrite()` in that case.
  `[official]`
- Middleware runs for on-demand routes only, including 404s, and edge middleware
  does not support sessions.

## Sessions

Sessions store server-side state keyed by a cookie. They need an adapter; the
Node, Cloudflare and Netlify adapters configure a driver automatically, others
need one:

```js
import { defineConfig, sessionDrivers } from "astro/config";

export default defineConfig({
  adapter: vercel(),
  session: { driver: sessionDrivers.lruCache({ max: 800 }) },
});
```

The driver is configured through `sessionDrivers` (or `{ entrypoint }` for a
custom driver); the old bare driver-name string is deprecated. Access is
`Astro.session` in components and `context.session` in endpoints, middleware and
actions, with `get()`, `set()`, `regenerate()` and `destroy()`. Values are
devalue-serialised, so the same types as actions and collections are supported.
Declare `App.SessionData` to type the keys instead of storing `any`.

Driver config is inlined at build time, so an environment variable read there is
frozen into the bundle — pass a runtime-resolved value explicitly if it differs
per environment.

## Typed environment variables

`import.meta.env` is Vite's mechanism: server code sees everything, client code
only sees `PUBLIC_`-prefixed variables, and values are always inlined at build
time. `.env` files are not loaded inside `astro.config.*` — use `process.env`
there.

`astro:env` adds a validated schema on top:

```js
import { defineConfig, envField } from "astro/config";

export default defineConfig({
  env: {
    schema: {
      API_URL: envField.string({ context: "client", access: "public", optional: true }),
      PORT: envField.number({ context: "server", access: "public", default: 4321 }),
      API_SECRET: envField.string({ context: "server", access: "secret" }),
    },
  },
});
```

```ts
import { API_URL } from "astro:env/client";
import { API_SECRET, getSecret } from "astro:env/server";
```

- `context` × `access` decides the module and whether the value is bundled:
  client/public lands in both bundles, server/public in the server bundle,
  server/secret in neither.
- Every secret in the schema is validated as soon as anything is imported from
  `astro:env/server`, including secrets the code never reads. CI builds
  therefore need placeholder values, or `env.validateSecrets: false`.
  `[official]`
- `getSecret(name)` reads a raw or unschematised secret at runtime.
- `astro:env` is a virtual module: it resolves in middleware, routes, endpoints,
  actions and components, not in arbitrary Node scripts.

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev -->
