# Routing, output modes and rendering

Verified against: Astro 7.3

## Contents

- [Project shape](#project-shape)
- [Output mode and adapters](#output-mode-and-adapters)
- [Per-route `prerender`](#per-route-prerender)
- [Dynamic routes: static](#dynamic-routes-static)
- [Dynamic routes: on demand](#dynamic-routes-on-demand)
- [Pagination](#pagination)
- [Route priority](#route-priority)
- [Redirects and rewrites](#redirects-and-rewrites)
- [Endpoints](#endpoints)
- [Response headers and streaming](#response-headers-and-streaming)
- [Route caching](#route-caching)
- [Advanced routing (`src/fetch.ts`)](#advanced-routing-srcfetchts)

## Project shape

```
src/
  pages/            required — every file here becomes a route
  components/
  layouts/
  content.config.ts build-time collections
  live.config.ts    live collections
  actions/index.ts  actions
  middleware.ts     middleware
  fetch.ts          reserved: advanced routing entrypoint
public/             copied verbatim, never processed
astro.config.mjs    .mjs / .js / .ts / .mts only — CommonJS config is not supported
```

Files and directories under `src/pages/` whose name starts with `_` are ignored
by the router, which is the supported way to colocate helpers next to routes.

## Output mode and adapters

`output` accepts exactly two values: `[official]`

- `'static'` (default) — every route is prerendered unless it opts out.
- `'server'` — every route renders on demand unless it opts in to prerendering.

There is no `'hybrid'`. It was removed; the behaviour people used it for is the
default `'static'` mode plus `export const prerender = false` on the routes that
need a server. `output: 'server'` adds no capability — it only flips the default,
and it flips away the ability to serve most of the site as cacheable static
HTML. Choose it only when the majority of routes read per-request data.

Any on-demand rendering needs an adapter, and so do server islands and sessions
even on an otherwise static site:

```bash
npx astro add node      # or vercel | netlify | cloudflare
```

Adapters also unlock host features on static sites (image CDNs, cache
providers), so "static site, no adapter" is a choice, not a rule.

## Per-route `prerender`

```astro
---
export const prerender = false;  // this route renders on demand
---
```

The export must be at the top level of a page or endpoint module. It is what
makes cookies, request headers, form actions, sessions and per-request data work
on that route. A route left prerendered will happily read `Astro.cookies` at
build time and bake the build-time answer into HTML — a class of bug that never
throws.

## Dynamic routes: static

A `[param]` or `[...rest]` route in a static build must export
`getStaticPaths()` returning `{ params, props? }` objects:

```astro
---
// src/pages/dogs/[dog].astro
export function getStaticPaths() {
  return [{ params: { dog: "clifford" } }, { params: { dog: "rover" } }];
}
const { dog } = Astro.params;
---
```

Rules that bite:

- Param values must be strings. A number is rejected. `[official]`
- Params are **not** decoded. Apply `decodeURI()` when a value is
  percent-encoded. `[official]`
- The `Astro` global is not available inside `getStaticPaths()`. Use
  `import.meta.env.SITE` in place of `Astro.site`; `Astro.generator` has no
  replacement there. `[official]`
- A rest param set to `undefined` matches the parent path itself, which is how
  one `[...slug].astro` serves `/` as well as `/a/b/c`.
- `props` is the channel for data you already fetched while building the path
  list. Passing the entry through `props` avoids querying it again per page.

## Dynamic routes: on demand

On-demand routes have no build-time path list, so `getStaticPaths()` must not be
used — and because it is absent, `props` is unavailable and every page must
resolve its own data from `Astro.params` or `Astro.request`. `[official]`

Only one rest param per on-demand route file:
`src/pages/[locale]/[...slug].astro` is fine, `[...locale]/[...slug].astro` is
not.

## Pagination

`getStaticPaths({ paginate })` splits a list into routes; the page receives a
`page` prop carrying `data`, `url.prev`, `url.next`, `currentPage`, `lastPage`
and the totals. Nested pagination returns an array of `paginate()` results, one
per group, which is how `/tags/[tag]/[page]` is built.

## Route priority

When several routes could build one URL, Astro sorts by: reserved routes → more
path segments → static over dynamic → named params over rest params →
prerendered over on-demand dynamic → endpoints over pages → files over
configured redirects → alphabetical. `[official]`

The practical reading: `posts/create.astro` always wins over
`posts/[page].astro`, which always wins over `posts/[...slug].astro`, and a real
file always wins over a `redirects` entry with the same path.

## Redirects and rewrites

Configured redirects are for permanently moved URLs:

```js
export default defineConfig({
  redirects: {
    "/old-page": "/new-page",
    "/blog/[...slug]": "/articles/[...slug]",   // params must match on both sides
    "/legacy": { status: 302, destination: "/new" },
  },
});
```

In a static build these become `meta refresh` HTML files unless the adapter
writes host-level redirect config instead.

`Astro.redirect(path, status?)` is the dynamic form and must be called at page
level: on-demand pages stream, so by the time a child component runs the status
line is already sent. `[official]`

`Astro.rewrite(path)` serves different content under the current URL — no
browser navigation, no address change. It triggers a complete new rendering
phase, so middleware runs again for the rewritten route. Use it for aliasing and
for rendering `/404` in place, and use a redirect when the URL should actually
change.

## Endpoints

A `.ts`/`.js` file in `src/pages/` exporting `GET`, `POST` etc. is an endpoint.
It receives the endpoint context and must return a `Response`. Prerendered
endpoints are built once; add `export const prerender = false` for anything
request-dependent.

Endpoints whose filename carries an extension (`/api/data.json.ts`) cannot be
reached with a trailing slash. `[official]`

## Response headers and streaming

On-demand rendering streams HTML, which constrains where the response can still
be shaped: `Astro.response.status`, `Astro.response.headers` and returning a
`Response` only work at page level, never inside a component or layout, because
headers are already flushed by then. `[official]`

Astro renders and flushes components as it encounters them, so ordering
independent `await`s to start together still matters — a sequential chain of
fetches in one frontmatter block holds the whole stream.

## Route caching

Route caching gives on-demand routes platform-agnostic HTTP caching. Configure a
provider, then set directives per route or declaratively: `[official]`

```js
import { defineConfig, memoryCache } from "astro/config";
import node from "@astrojs/node";

export default defineConfig({
  adapter: node({ mode: "standalone" }),
  cache: { provider: memoryCache() },
  routeRules: {
    "/api/[...path]": { swr: 600 },
    "/products/[...slug]": { maxAge: 3600, tags: ["products"] },
  },
});
```

```astro
---
if (Astro.cache.enabled) {
  Astro.cache.set({ maxAge: 3600, tags: ["product", Astro.params.id] });
}
if (isPersonalized) Astro.cache.set(false);   // opt out of a matching route rule
---
```

`cache` and `routeRules` are top-level config, not `experimental`. The
Netlify, Vercel and Cloudflare adapters ship CDN cache providers that push
directives to the edge instead of holding responses in memory; they are still
opt-in. `cache.enabled` is always `false` in dev and `cache.set()` is a no-op
there, so verify caching against `astro build && astro preview`. Repeated
`set()` calls merge: scalars last-write-wins, `tags` accumulate.

## Advanced routing (`src/fetch.ts`)

Astro 7 handles requests through a fixed pipeline — trailing-slash
normalisation, redirects, sessions, actions, middleware, page rendering, i18n,
caching. `src/fetch.ts` replaces that pipeline with an exported object whose
`fetch(request)` returns a `Response`, letting you reorder stages, wrap them, or
front them with Hono via `astro/hono`. `[official]`

Two consequences for ordinary projects:

- `src/fetch.ts` is a **reserved filename**. An existing file with that name is
  loaded as a routing entrypoint and breaks the build. Rename it, or set
  `fetchFile: "./src/router.ts"` / `fetchFile: null` in the config.
- Reach for it only when the fixed pipeline genuinely does not fit. Ordinary
  request interception belongs in `src/middleware.ts`.

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev -->
