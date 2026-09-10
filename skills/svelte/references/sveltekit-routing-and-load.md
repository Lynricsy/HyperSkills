# SvelteKit routing and data loading

Verified against: SvelteKit 2.70.

## Contents

- [Route files](#route-files)
- [Universal versus server `load`](#universal-versus-server-load)
- [What a server `load` may return](#what-a-server-load-may-return)
- [Custom types across the boundary: `transport`](#custom-types-across-the-boundary-transport)
- [Reading the data in the component](#reading-the-data-in-the-component)
- [`page`, `navigating`, `updated`](#page-navigating-updated)
- [Waterfalls: `await parent()` and `fetch`](#waterfalls-await-parent-and-fetch)
- [Streaming promises](#streaming-promises)
- [Invalidation](#invalidation)
- [Server-only modules and environment variables](#server-only-modules-and-environment-variables)
- [Page options](#page-options)
- [`+server.js` endpoints](#serverjs-endpoints)

## Route files

Everything under `src/routes` with a `+` prefix is a route file. The ones that
decide behaviour:

| File | Runs | Purpose |
|---|---|---|
| `+page.svelte` | client + SSR | the page component |
| `+page.js` | server + client | universal `load`, page options |
| `+page.server.js` | server only | server `load`, form `actions` |
| `+layout.svelte` / `.js` / `.server.js` | as above | shared shell and data for a subtree |
| `+error.svelte` | client + SSR | nearest error boundary for the segment |
| `+server.js` | server only | `GET`/`POST`/… HTTP endpoints |

Directory names drive the URL: `[slug]` is a parameter, `[...rest]` a rest
parameter, `[[optional]]` an optional one, `(group)` a layout group that does
not appear in the path, `[slug=integer]` a matcher from `src/params/integer.js`.
A leading `+layout@` or `+page@` resets inheritance to a named ancestor layout.

`./$types` supplies `PageProps`, `LayoutProps`, `PageLoad`, `PageServerLoad`,
`Actions` and `RequestHandler` for the current route; generated types are the
reason route code needs no manual typing.

## Universal versus server `load`

A route may have both. The server one runs first and its return value arrives as
the universal one's `data` property.

- **Server `load` (`+page.server.js`)** runs only on the server, on the first
  request and on every client navigation (as a `fetch` to the server). It can
  read the database, secrets, `event.locals`, `cookies` and `request`.
- **Universal `load` (`+page.js`)** runs on the server during SSR and then again
  in the browser during hydration and on every subsequent client navigation. It
  cannot import server-only modules and must tolerate both environments.

Pick the server one whenever the work needs server resources or must stay
private. Pick the universal one when calling a public API directly from the
browser is preferable to routing through your server, or when the return value
cannot be serialized (a component constructor, a class instance).

The universal `load` running in the browser is what makes `localStorage`,
`window` and `document` a hazard: guard them with `browser` from
`$app/environment`, or read them in an effect in the component instead, which is
usually the better place.

Importing anything from `$lib/server/*` into `+page.js` is not a runtime bug to
be handled — SvelteKit refuses the build with an illegal-import error, and the
work has to move into `+page.server.js`.

## What a server `load` may return

Server `load` return values are serialized with
[devalue](https://github.com/rich-harris/devalue), not `JSON.stringify`. That
means anything JSON can express **plus** `BigInt`, `Date`, `Map`, `Set`,
`RegExp`, and repeated or cyclical references.

So `return { generatedAt: new Date() }` is correct and arrives as a `Date` — do
not convert dates to ISO strings on the way out and parse them back on the way
in. What genuinely cannot cross are values devalue has no representation for:
class instances, functions, `Symbol`s, DOM nodes.

A universal `load` has no such restriction, because its return value never
leaves the process it was created in.

## Custom types across the boundary: `transport`

To send a class instance from a server `load` or a form action, register a
transporter in `src/hooks.js` (the universal hooks file — it runs on both sides,
which is what makes symmetric encode/decode possible):

```js
// src/hooks.js
import { Invoice } from '$lib/models/invoice';

/** @type {import('@sveltejs/kit').Transport} */
export const transport = {
  Invoice: {
    encode: (value) => value instanceof Invoice && [value.toJSON()],
    decode: ([raw]) => new Invoice(raw)
  }
};
```

`encode` must return a falsy value for anything that is not an instance of the
type. The alternative, when the class exists only to add derived getters, is to
return plain data and compute in the component or in a universal `load`.

## Reading the data in the component

```svelte
<script lang="ts">
  import type { PageProps } from './$types';
  let { data, form }: PageProps = $props();
</script>
```

`export let data` is legacy-mode syntax; in a runes-mode component it does not
compile. `PageProps` (and `LayoutProps`) exist from SvelteKit 2.16; before that,
type `data` and `form` individually with `PageData` and `ActionData`.

`data` is replaced, not mutated, on navigation. Never mutate `data` — write to
local `$state` seeded from it, and remember that navigating to the same route
with different params reuses the component instance, so a value initialised once
from `data` will not refresh. Derive from `data` instead.

## `page`, `navigating`, `updated`

Import them from `$app/state`, which exposes plain reactive objects:

```svelte
<script>
  import { page, navigating } from '$app/state';
</script>

{#if navigating.to}<progress></progress>{/if}
<p>{page.url.pathname} {page.status}</p>
```

`$app/stores` still exists in SvelteKit 2 but is deprecated: `$page.url` becomes
`page.url`, with no `$` prefix. `npx sv migrate app-state` does the rewrite.
`$app/state` needs SvelteKit 2.12+ and Svelte 5, because the objects are runes.

`page.data` merges every `load` return value for the current route;
`page.form` holds the most recent form action result app-wide.

## Waterfalls: `await parent()` and `fetch`

Layout and page `load` functions run concurrently — until one calls
`await parent()`, which serialises it behind its ancestors. Start independent
work before awaiting the parent:

```js
export async function load({ parent, fetch }) {
  const ratesPromise = fetch('/api/rates').then((r) => r.json()); // starts now
  const { locale } = await parent();
  return { locale, rates: await ratesPromise };
}
```

An auth guard in `+layout.server.js` only protects children that actually
`await parent()`, so it is not a guard. Check authorisation in `handle` (for
whole subtrees) or in each `+page.server.js`/action that touches protected data.

The `fetch` passed to `load` is not the global one: it inherits `cookie` and
`authorization` headers for same-origin requests, can call internal routes
without an HTTP round trip during SSR, and has its responses inlined into the
rendered HTML so hydration does not repeat them.

## Streaming promises

A server `load` may return a promise as a property value; SvelteKit streams the
resolution to the browser and the page renders the rest immediately.

```js
export async function load({ locals }) {
  return {
    user: await locals.getUser(),              // awaited: needed for the shell
    comments: loadComments()                   // streamed
  };
}
```

In the component, resolve it with `{#await data.comments}`. Streaming needs
JavaScript, so a page that must work without it cannot rely on this. Do not
return promises from a *universal* `load` on a server-rendered page: they are
not streamed, and the promise is simply recreated when the function re-runs in
the browser. Attach a `.catch` to any streamed promise, or the rejection becomes
an unhandled error.

## Invalidation

A `load` function re-runs when a param it read changed, when a URL property it
read changed, when a parent it awaited re-ran, or when a dependency it declared
was invalidated.

Dependencies come from two places: `fetch(url)` inside a *universal* `load`, and
an explicit `depends(...)`. A server `load` never registers a fetched URL as a
dependency — that would leak the URL to the client — so a server `load` that
should be re-runnable must declare a custom identifier:

```js
export async function load({ depends }) {
  depends('app:rates');
  return { rates: await db.rates.all() };
}
```

```js
import { invalidate, invalidateAll } from '$app/navigation';

invalidate('app:rates');                       // just the loads that declared it
invalidate((url) => url.pathname === '/api/x'); // predicate form
invalidateAll();                               // every load for the current page
```

Custom identifiers must be `[a-z]:`-prefixed. Reach for `invalidateAll()` only
after a change whose blast radius you genuinely cannot scope — a sign-in, for
example, where `event.locals` changed for every loader.

## Server-only modules and environment variables

Two mechanisms, both enforced at build time:

- `$env/static/private` and `$env/dynamic/private` can only be imported from
  server-only code. `$env/static/public` and `$env/dynamic/public` require the
  `PUBLIC_` prefix and are safe to ship.
- Your own modules become server-only by living in `src/lib/server/` or by
  carrying a `.server.` segment in the filename.

`process.env` bypasses all of it: it is not validated, not statically replaced,
and not available on every adapter. Prefer `$env/static/private` so a missing
variable fails the build rather than the request. A secret returned from `load`
is serialized into the HTML payload no matter which module it came from — the
boundary that matters is the return value, not the import.

## Page options

Exported from `+page.js`/`+page.server.js` (per page) or the layout equivalents
(inherited):

- `prerender = true` renders at build time. A prerendered page cannot read
  `url.searchParams`, cannot have form actions, and cannot use `depends`-based
  invalidation. `prerender = 'auto'` prerenders and keeps the page dynamic-
  capable; `entries` lists the dynamic routes to crawl.
- `ssr = false` skips server rendering for that route, turning it into a
  client-only page. Only correct for something genuinely browser-dependent; it
  costs the first contentful paint.
- `csr = false` ships no JavaScript for the route. Links do full navigations,
  form actions still work, `use:enhance` does nothing.
- `trailingSlash`, `config` (adapter-specific deployment config).

## `+server.js` endpoints

Export `GET`, `POST`, `PATCH`, `PUT`, `DELETE`, `OPTIONS`, `HEAD`, or a
`fallback`. Return a `Response`; `json()` and `text()` from `@sveltejs/kit` are
the shortcuts. Read the request with `await request.json()` or
`await request.formData()`.

Add an endpoint when a third party or a client-side script must call the route
over HTTP. Do not add one just so `+page.svelte` can fetch its own data — that
is what `load` (and, in a page that also writes, a form action) is for, and the
endpoint version costs an extra round trip plus hand-written serialization.

<!-- sources: sveltekit-core, spences10-svelte, ejirocodes-svelte5, awesome-copilot, svelte-dev-docs -->
