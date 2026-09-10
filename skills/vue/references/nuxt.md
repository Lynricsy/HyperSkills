# Nuxt

Verified against: Nuxt 4.5

## Contents

- [Directory conventions](#directory-conventions)
- [Choosing a data primitive](#choosing-a-data-primitive)
- [data is a shallow ref](#data-is-a-shallow-ref)
- [Keys, sharing and de-duplication](#keys-sharing-and-de-duplication)
- [await, lazy and immediate](#await-lazy-and-immediate)
- [Wrapping the fetch layer](#wrapping-the-fetch-layer)
- [State that survives hydration](#state-that-survives-hydration)
- [Hydration mismatches](#hydration-mismatches)
- [The server/client boundary](#the-serverclient-boundary)
- [Nuxt instance unavailable](#nuxt-instance-unavailable)
- [Runtime config and secrets](#runtime-config-and-secrets)
- [Server routes from the Vue side](#server-routes-from-the-vue-side)
- [Pages, layouts and route metadata](#pages-layouts-and-route-metadata)

## Directory conventions

Application code lives under `app/` (`app/pages`, `app/components`,
`app/composables`, `app/layouts`, `app/middleware`, `app/plugins`, `app/utils`,
`app/app.vue`). Server code lives under `server/`, code shared by both under
`shared/`, static files under `public/`. `app/pages/` is optional — without it
`vue-router` is not even bundled.

Components, composables and utils in those directories are auto-imported; a
manual import of an auto-imported symbol is noise but not an error. After
changing `nuxt.config`, a module, an alias or anything that generates types, run
`nuxt prepare` before trusting a type error.

## Choosing a data primitive

| Primitive | Use for | Why not the others |
|---|---|---|
| `useFetch(url, opts)` | One HTTP endpoint fetched for the component's initial render | Wraps `useAsyncData` + `$fetch`, derives a key, forwards request context |
| `useAsyncData(key, fn)` | Custom async logic: an SDK call, several requests, or a shared explicit key | `useFetch` cannot express it |
| `$fetch(url, opts)` | Event-driven requests — form submits, button actions | No payload transfer and no de-duplication |
| `callOnce(fn)` | A side effect that must run once across SSR and client navigation | `useAsyncData` handlers must be side-effect free |

Calling bare `$fetch` during setup fetches **twice** — once on the server to
render the HTML, once again during hydration — because its result is not placed
in the Nuxt payload. That double request is the reason `useFetch` exists.

`useAsyncData` handlers should return a truthy value and stay free of side
effects. Pass the handler's abort `signal` through to cancellable work:
`useAsyncData('cart', (_app, { signal }) => $fetch('/api/cart', { signal }))`.

## data is a shallow ref

`deep` defaults to `false`, so `data` is a shallow ref: mutating anything inside
it triggers no re-render.

```ts
const { data: projects } = await useFetch('/api/projects')

projects.value[0].archived = true                     // nothing renders
projects.value = projects.value.map(...)              // renders
// or, when in-place mutation is really wanted:
await useFetch('/api/projects', { deep: true })
```

Prefer replacing the value or calling `refresh()`. `deep: true` costs a deep
proxy over the whole payload on every render.

## Keys, sharing and de-duplication

`useFetch` builds its key from the URL, the options **and the call site**. Two
components fetching the same URL therefore get two keys and two requests. That
is by design, not a bug — pass one explicit `key` when the data should be
shared:

```ts
// both components
const { data } = await useFetch('/api/projects', { key: 'projects' })
// or, in the component that only reads
const { data } = useNuxtData('projects')
```

`useAsyncData` uses its string first argument as the key, and generates one from
the call site when the first argument is the handler. Any reusable wrapper must
pass an explicit key, otherwise every call site gets its own cache entry.

Calls sharing a key share `data`, `error` and `status`, so these options **must
match** across them: `handler`, `deep`, `transform`, `pick`, `getCachedData`,
`default`. A mismatch logs a development warning. These may safely differ:
`server`, `lazy`, `immediate`, `dedupe`, `watch`. Need independent instances?
Use different keys.

Keys may be refs, computeds or getters — the request re-runs and stale entries
are cleaned up when the key changes.

Payload size: `pick: ['id', 'name']` or a `transform` function keeps unused
fields out of the serialised payload. Neither reduces what the API sends; both
reduce what ships in the HTML.

Cache utilities: `useNuxtData(key)` reads, `refreshNuxtData(key)` refetches,
`clearNuxtData(key)` discards. Reach for these before layering a second cache.

## await, lazy and immediate

`await` does not change the server-rendered HTML — the server always waits and
serialises the full result. It changes what happens next:

- `await useFetch(...)` — code after the call can rely on `data`; client-side
  navigation blocks until the data resolves.
- `useFetch(..., { lazy: true })` / `useLazyFetch(...)` — navigation happens
  immediately and the component renders `status === 'pending'` first.
- `{ server: false }` — client-only. On first load nothing is fetched until
  hydration finishes, so a pending state is mandatory.
- `{ immediate: false }` — nothing runs until `execute()` is called.

`await` and `lazy` are independent, and combining them misleads: on client
navigation `await useLazyFetch(...)` resolves immediately with `data` still at
its default. Choose one intent and express it with `lazy`.

Always render off `status` (`idle` / `pending` / `success` / `error`) and
`error`, not off a truthiness check on `data`.

## Wrapping the fetch layer

```ts
// app/composables/useAPI.ts
export const useAPI = createUseFetch({
  baseURL: 'https://api.example.com',
  onRequest({ options }) { /* attach auth */ },
  async onResponseError({ response }) {
    if (response.status === 401) await navigateTo('/login')
  },
})
```

`createUseFetch` is a compiler macro: it only works as an **exported**
declaration in a scanned directory, and Nuxt injects the de-duplication keys at
build time. `useFetch` itself is a reserved name that the compiler transforms,
so a hand-written `export function useFetch()` breaks the build — that is the
reason the factory exists.

For lower-level control, create a `$fetch` instance in a plugin
(`$fetch.create({ baseURL })`, provided as `$api`) and call it inside
`useAsyncData`.

Server-side relative requests: `useFetch` forwards the incoming request's
cookies and headers automatically. A hand-rolled helper must use
`useRequestFetch()` to get that; plain `$fetch` deliberately does not forward.

## State that survives hydration

`useState(key, init)` is the request-isolated, payload-transferred state
primitive. Its initialiser must be serialisable and side-effect free.

```ts
// app/composables/useSelectedTeam.ts
export const useSelectedTeam = () => useState<string | null>('selected-team', () => null)
```

A module-level `ref` in a composable file is a cross-request leak on the server:
the module lives for the server's lifetime, so one visitor's data is served to
the next. Use `useState`, or a store (`@pinia/nuxt` scopes stores per request).

Reach for a store when the domain needs actions, derived state and persistence;
`useState` is for a value.

## Hydration mismatches

A mismatch is not cosmetic: Vue discards the server HTML for that subtree and
re-renders it, costing time-to-interactive and sometimes losing event listeners.
Never ignore the warning. The causes, and the fixes:

| Cause | Fix |
|---|---|
| `localStorage` / `window` read during setup | `useCookie('theme', { default: () => 'light' })`, or read it in `onMounted` |
| `Math.random()` in render | `useState('seed', () => Math.random())` |
| `new Date()` / relative times | `<NuxtTime>`, or compute after mount, or `<ClientOnly>` with a `#fallback` |
| Viewport-conditional rendering | CSS media queries, or `<ClientOnly>` |
| A third-party library mutating the DOM | Import it dynamically inside `onMounted` |

`<ClientOnly>` always needs a `#fallback` — without one the slot renders empty
on the server and the layout jumps on hydration.

## The server/client boundary

- `import.meta.server` / `import.meta.client` are the branch conditions; they are
  statically replaced, so the other branch is tree-shaken out.
- `.client.ts` / `.server.ts` plugin suffixes do the same at file granularity.
- `onMounted` is the only place guaranteed to have a DOM.
- `*.server.vue` server components render on the server only and never ship
  their JS. `experimental.componentIslands` defaults to `'auto'`, so this works
  without configuration; `'local+remote'` is needed only for remote islands.
- Getting the browser-only library right is usually
  `onMounted(async () => { const { X } = await import('x'); ... })`, not a
  top-level import behind an `if`.

## Nuxt instance unavailable

Nuxt composables need the Nuxt instance, which is available in `<script setup>`,
`setup()`, `defineNuxtPlugin()` and `defineNuxtRouteMiddleware()` callbacks —
and only synchronously.

```ts
// Wrong: module scope, evaluated at import time
const config = useRuntimeConfig()
export const useApiBase = () => config.public.apiBase

// Wrong: context is gone after the await
await somethingAsync()
const route = useRoute()

// Right: call composables first, then await
const route = useRoute()
const config = useRuntimeConfig()
await somethingAsync()
```

Route middleware receives `to` and `from`; use those rather than `useRoute()`,
which reflects the current (not the target) route during navigation.

## Runtime config and secrets

Top-level `runtimeConfig` keys are **server-only**. Only `runtimeConfig.public`
(and Nuxt's internal `app`) reach the client. A component template reading a
private key gets `undefined` on the client — and if it ever did resolve, the
secret would be in the HTML. Keep secrets server-side and expose a server route
instead. Override values with `NUXT_`-prefixed environment variables rather than
editing the config per environment.

## Server routes from the Vue side

`server/api/projects.get.ts` becomes `GET /api/projects`, callable as
`useFetch('/api/projects')` with no base URL and with request cookies forwarded.
The method suffix (`.get`, `.post`) is the routing mechanism; a single handler
that branches on the method is the older, less type-friendly shape.

Validate input in the handler and throw `createError({ statusCode, statusMessage })`
so `useFetch`'s `error` ref carries a usable status. Caching for a route is
declared in `nuxt.config`'s `routeRules` (`{ '/api/stats': { swr: 600 } }`),
not by hand-rolling a cache in the component.

## Pages, layouts and route metadata

`definePageMeta({ layout: 'minimal', middleware: ['auth'] })` is a compiler
macro: top level in the page, statically analysable, no variables from the
surrounding scope. `<NuxtPage>` renders the matched page, `<NuxtLayout>` the
layout, `<NuxtLink>` prefetches on viewport entry.

SEO metadata: `useSeoMeta()` for the typed common surface (title, description,
Open Graph), `useHead()` for links, scripts and attributes outside it. Both
participate in Nuxt's head lifecycle, so setting `document.title` by hand
fights them.

<!-- sources: onmax-nuxt-skills, antfu-skills, vuejs-ai-skills, nuxt-docs -->
