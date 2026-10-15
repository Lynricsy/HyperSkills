# Hooks, errors, and deployment

Verified against: SvelteKit 2.70 and 3.1.

## Contents

- [The three hook files](#the-three-hook-files)
- [`handle` and `event.locals`](#handle-and-eventlocals)
- [`resolve` options](#resolve-options)
- [`handleFetch`](#handlefetch)
- [`handleError` and the error contract](#handleerror-and-the-error-contract)
- [`reroute`](#reroute)
- [`init`](#init)
- [Adapters](#adapters)
- [Prerendering and static output](#prerendering-and-static-output)
- [Auth placement](#auth-placement)

## The three hook files

| File | Runs | Exports |
|---|---|---|
| `src/hooks.server.js` | server | `handle`, `handleFetch`, `handleError`, `init` (plus `handleValidationError` on SvelteKit 2) |
| `src/hooks.client.js` | browser | `handleError`, `init` |
| `src/hooks.js` | both | `reroute`, `transport` |

The universal `hooks.js` is easy to miss and is the only place `transport` can
live, because encode runs on the server and decode in the browser.

## `handle` and `event.locals`

`handle` wraps every request, including data requests, form action posts and
`+server.js` endpoints. It is the one place that sees all of them, which makes
it the correct home for session resolution:

```js
// src/hooks.server.js
export async function handle({ event, resolve }) {
  event.locals.user = await getUser(event.cookies.get('session'));
  return resolve(event);
}
```

Declare the shape in `src/app.d.ts` under `App.Locals` or every `load` reads
`any`. Compose several hooks with `sequence` from `@sveltejs/kit/hooks`.

Mutating the returned response's headers is not always safe: a `Response` from
a redirect has immutable headers and setting one throws a `TypeError`. Clone the
response, or set the header on the `resolve` result only when you constructed it.

## `resolve` options

`resolve(event, opts)` accepts:

- `transformPageChunk({ html, done })` — rewrite the streamed HTML. Chunks are
  not guaranteed to be well-formed, so string replacement must not assume
  balanced tags. This is how a language attribute or a nonce gets injected.
- `filterSerializedResponseHeaders(name, value)` — which headers of a `load`
  `fetch` response get inlined into the HTML. Default: none. If a client-side
  consumer needs `content-range` or an `x-` header, it has to be allowed here.
- `preload({ type, path })` — which build assets get `<link rel=preload>`.
  Not called in dev mode, so a preload bug only appears in a production build.

## `handleFetch`

Rewrites or replaces the `fetch` calls made inside `load`, actions, endpoints
and other hooks on the server. Two real uses: sending a request to an internal
origin instead of over the public network during SSR, and forwarding cookies
across sibling subdomains, which SvelteKit cannot do automatically because it
cannot know which domain a parent-domain cookie belongs to.

## `handleError` and the error contract

On SvelteKit 2, expected errors — anything raised with `error(status,
message)` — render `+error.svelte` with their message shown as-is, and only
unexpected errors reach `handleError`, as status 500 and the message "Internal
Error". SvelteKit 3 calls `handleError` for every error and passes a `kind`:
`app` (your `error()`), `framework` (404, 405, 413), `validation` (a remote
function argument that failed its Standard Schema) or `unknown` (anything
thrown). The returned object may override `status` and `message`.

`handleError` exists to log the real error somewhere and to return a *safe*
shape for `page.error`. Extend it by declaring `App.Error` in `src/app.d.ts`;
it must keep `message: string`. Returning the raw `error.message` of an
unexpected error defeats the purpose — that string is exactly what SvelteKit
withheld from the client.

Remote-function validation failures default to a 400 with "Bad Request"
(`handleValidationError` on SvelteKit 2, `kind: 'validation'` on 3). Do not
echo the issues back by default: the likeliest cause is a hostile request, and
a detailed message tells the caller what shape to send next.

## `reroute`

Maps an incoming URL to a different route without changing the address bar:
localised paths (`/de/ueber-uns` → `/[[lang]]/about`), legacy URLs, A/B splits.
It must be pure and idempotent — SvelteKit caches the result per URL on the
client — and it may be async since 2.18, in which case it delays every
navigation, so it must be fast. `params` and `id` are unavailable to
`handleFetch` from inside `reroute`, because the route is not resolved yet.

## `init`

Runs once before the app starts handling requests (server) or before hydration
(client). Use it for a database connection pool or an error-reporting SDK.
Async work in the client `init` delays hydration.

## Adapters

The adapter is set in `vite.config.js` as the `adapter` option of `sveltekit({...})`
on SvelteKit 3, and in `svelte.config.js` under `kit.adapter` on 2. Official
ones: `adapter-auto`, `adapter-node`, `adapter-bun`, `adapter-static`,
`adapter-vercel`, `adapter-netlify`, `adapter-cloudflare`. Everything else is
community-provided.

`adapter-auto` is a convenience for the supported hosts and has no
configuration options. Once the deployment target is known, install that
adapter explicitly — it is what makes the platform's options (Node middleware
mode, Vercel ISR and runtime, Cloudflare bindings) reachable at all.

Adapter-specific request context arrives as `event.platform`: Cloudflare's
`env` with KV, R2, D1 and Durable Object bindings; Vercel's and Netlify's
request context. Reading `event.platform` in code that also runs under a
different adapter is a runtime `undefined`, so keep the access in one module.

`adapter-static` requires every route to be prerenderable; a single form action
or an un-prerenderable dynamic page fails the build. For a client-rendered SPA
with a static host, add a fallback page instead of dropping the adapter.

## Prerendering and static output

Prerendering crawls from the site's entry points, so a page reachable only
through a client-side `goto` is never found. `export const entries` on the route
lists the dynamic parameter sets for the crawler.

A prerendered page cannot read `url.searchParams` at request time (there is no
request), cannot host form actions, and its `load` runs at build time — so
build-time environment variables, not request-time ones. `prerender = 'auto'`
keeps the route in the dynamic manifest as well, which is how a
"prerender the popular slugs, server-render the long tail" route is expressed.

## Auth placement

Resolve the session in `handle` and authorise where the data is read:

- `handle` — one check for a whole URL subtree (`/admin/**`). It runs for every
  request, so it cannot be bypassed.
- `+page.server.js` / `+layout.server.js` / action / `+server.js` — the check
  that guards a specific read or write.

An `await parent()`-based guard in a layout `load` is not a guard: a child
`load` that never calls `parent()` runs regardless, and a `+server.js` endpoint
under the same path does not involve layouts at all. `ssr = false` moves
rendering to the client but changes nothing about authorisation, because the
server `load` still runs.

<!-- sources: sveltekit-core, spences10-svelte, svelte-dev-docs -->
