# Vue Router

Verified against: Vue Router 5.3

## Contents

- [What changed in Router 5](#what-changed-in-router-5)
- [Route params do not re-run the component](#route-params-do-not-re-run-the-component)
- [Navigation guards return, they do not call next](#navigation-guards-return-they-do-not-call-next)
- [Where each guard belongs](#where-each-guard-belongs)
- [Lazy routes and code splitting](#lazy-routes-and-code-splitting)
- [Typed routes](#typed-routes)
- [Route meta](#route-meta)
- [Scroll behaviour](#scroll-behaviour)
- [State that belongs in the URL](#state-that-belongs-in-the-url)

## What changed in Router 5

Router 5 merges `unplugin-vue-router` — file-based routing and generated route
types — into the core package. For a v4 project that was not using that plugin
there are **no breaking changes**: bump the dependency. The one exception is the
IIFE build, which no longer inlines `@vue/devtools-api`.

Migrating off `unplugin-vue-router` is import-path work:
`unplugin-vue-router/vite` becomes `vue-router/vite` (other bundlers:
`vue-router/unplugin`).

## Route params do not re-run the component

Navigating `/users/1` → `/users/2` reuses the same component instance. No
lifecycle hook fires, so data loaded in `onMounted` stays on screen showing the
previous user. This is the single most common Vue Router bug.

```ts
const route = useRoute()
const user = ref<User | null>(null)

watch(
  () => route.params.id,
  async (id) => { user.value = await fetchUser(id as string) },
  { immediate: true },   // covers first load and every later param change
)
```

`onBeforeRouteUpdate((to, from) => ...)` is the alternative when the data must
be in place before the view updates. `<RouterView :key="route.fullPath" />`
also works but destroys and rebuilds the component on every param change,
losing all of its state — use it only when a full reset is the intent.

Query-only changes (`?tab=a` → `?tab=b`) behave the same way: watch
`route.query.tab` specifically; a watcher on `route.params` will not fire.

## Navigation guards return, they do not call next

```ts
router.beforeEach(async (to) => {
  const session = useSessionStore()          // inside the guard: see references/pinia.md
  if (!to.meta.requiresAuth) return
  if (!session.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})
```

Return values: `undefined` proceeds, `false` cancels, a path string or route
location redirects, an `Error` cancels and reaches `router.onError`.

The `next` callback still exists for backwards compatibility and is where guard
bugs come from: forgetting it hangs navigation forever, calling it twice throws,
and in an async guard the code after a `next('/login')` keeps running and calls
it again. Do not mix styles — a guard that returns a value must not also accept
`next`.

Guard loops: a `beforeEach` that redirects to a route which itself fails the
same condition loops until the router bails. Always exempt the redirect target
(`if (to.name === 'login') return`).

## Where each guard belongs

| Guard | Scope | Use for |
|---|---|---|
| `router.beforeEach` | Global, every navigation | Auth, feature flags, analytics |
| `beforeEnter` on a record | That route only, and not on param change | Route-specific preconditions |
| `onBeforeRouteUpdate` | In-component, same route, new params | Reloading param-driven data |
| `onBeforeRouteLeave` | In-component | Unsaved-changes confirmation |
| `router.afterEach` | Global, after commit | Titles, scroll, logging — cannot cancel |

`beforeEnter` does not run when only the params change, which makes it the wrong
place for param-driven data loading.

In-component guards registered as options (`beforeRouteEnter`) have no `this`
before the component is created; in `<script setup>` use the
`onBeforeRouteUpdate` / `onBeforeRouteLeave` composables instead.

## Lazy routes and code splitting

```ts
{ path: '/reports', component: () => import('../views/ReportsView.vue') }
```

A dynamic import per route is what makes the router split bundles. A static
import of every view ships the whole app in the entry chunk.

## Typed routes

With file-based routing the route map is generated. Manually, augment
`TypesConfig` with a `RouteRecordInfo` map so `router.push`, `RouterLink`'s `to`
and `useRoute().params` are all checked:

```ts
export interface RouteNamedMap {
  'user-detail': RouteRecordInfo<
    'user-detail',
    '/users/:id',
    { id: string | number },   // accepted by push()
    { id: string },            // returned by useRoute()
    never                      // child route names
  >
}
declare module 'vue-router' {
  interface TypesConfig { RouteNamedMap: RouteNamedMap }
}
```

Note the two param types: pushing accepts a number, reading always gives a
string. Code that compares `route.params.id === someNumber` fails silently.

## Route meta

Declare the shape once so `to.meta` is typed everywhere:

```ts
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    layout?: 'default' | 'minimal'
  }
}
```

`meta` is merged from all matched records, so a parent's `requiresAuth` applies
to children.

## Scroll behaviour

`scrollBehavior(to, from, savedPosition)` returning `savedPosition` restores the
browser's position on back/forward; return `{ top: 0 }` otherwise, and
`{ el: to.hash }` for anchors. Without it, navigating to a new route keeps the
previous scroll offset.

## State that belongs in the URL

Filters, pagination, sort order, active tab and search text belong in the query
string, not in a store: they survive reload, they are shareable, and the back
button works. Keep only state that has no meaningful URL representation (auth
session, draft form contents) outside the URL.

<!-- sources: vuejs-ai-skills, onmax-nuxt-skills, awesome-copilot, router-docs -->
