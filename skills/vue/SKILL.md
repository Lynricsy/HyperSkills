---
name: vue
description: "Engineers Vue 3 applications: the Composition API with `script setup` SFCs, the reactivity system and every way it silently detaches (reactive destructuring, reassigned proxies, missing `.value`, props destructure, shallow refs), `computed` versus `watch` versus `watchEffect`, compiler macros including `defineModel`, provide/inject, composable contracts, Pinia store design, Vue Router guards and param changes, Nuxt 4 file conventions, data fetching and de-duplication, server/client boundaries and hydration mismatches, list and update performance, and Vitest with Vue Test Utils. Use when writing, reviewing, debugging, testing or profiling .vue files, composables, stores, routes or Nuxt pages, or when a value changes and the UI does not. Do not use for visual and UX design decisions, for React or Next.js, or for WeChat mini-programs and uni-app."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# vue

Paths below are relative to this skill's directory.

## Scope

Vue 3 application engineering: single-file components with `<script setup>`, the
reactivity system, composables, Pinia, Vue Router, Nuxt, component and list
performance, and component/composable/store testing.

The body is written against **Vue 3.5**, **Nuxt 4**, **Vue Router 5** and
**Pinia 4** — the current GA lines. Version-sensitive rules carry their floor,
as in `(3.5+)`. Vue 3.6 is still in release candidate and is not covered.

Not covered — do not answer from this skill:

- Visual and UX design decisions: palette, type scale, spacing, motion design,
  accessibility audits. Use the `frontend-design` skill.
- React, Next.js, React Server Components and the React ecosystem. Use the
  `react` skill.
- Type-layer modelling, `tsconfig` design and general TypeScript architecture.
  Use the `typescript` skill; this skill covers typing Vue's own surfaces
  (props, emits, slots, `InjectionKey`, route maps).
- Svelte and SvelteKit. Use the `svelte` skill.
- Astro, islands and hydration directives. Use the `astro` skill. Nuxt's own
  server/client boundary is covered here.
- Server-side Node frameworks — Fastify, NestJS, Hono. Use the
  `nodejs-backend` skill; Nitro server routes are covered here only as far as a
  Vue component consumes them.
- WeChat mini-programs, uni-app and Taro. Not covered: their runtimes have
  different rendering and lifecycle semantics, and no skill in this library
  covers them yet — say so rather than transferring Vue rules to them.
- Options API and JSX/render-function authoring as a default style. Both appear
  only in the context of migrating to `<script setup>`.
- Browser end-to-end testing mechanics, CI configuration, and deployment
  platforms.

## Core rules

Each rule is an invariant: breaking it is a bug or a measurable regression.

1. Read the stack before advising: `package.json` (`vue`, `nuxt`, `pinia`,
   `vue-router` versions), `vite.config.*` or `nuxt.config.*`, and one existing
   component. Half of these rules are version-gated, and Nuxt changes where
   state and data fetching belong.
2. `ref()` is the default primitive. `shallowRef` is an escape hatch for large
   immutable structures and opaque external instances — using it for a
   primitive buys nothing and breaks the day the value becomes an object.
3. Never reassign a `reactive()` object. Replacing the proxy leaves the template
   and every established dependency pointing at the old one; mutate in place and
   declare it `const`.
4. Reactive props destructure works only on the `defineProps()` call itself
   (3.5+). `const props = defineProps(); const { x } = props` is a snapshot, and
   passing a destructured prop to `watch` or an external function still needs a
   getter — `watch(() => x, cb)`, `useThing(() => x)`.
5. Props are read-only in both directions. Mutating a nested field of an object
   prop does not even warn; emit an event or use `defineModel`.
6. A `computed` getter derives and nothing else — no assignment to other state,
   no request, no storage write, no emit. Vue caches on dependencies, so a side
   effect there runs an unpredictable number of times.
7. Derive with `computed`, not with a watcher that assigns a ref. The watcher
   costs an extra render pass and the copy drifts the first time a code path
   forgets it.
8. `watch(src, cb, { immediate: true })` replaces `onMounted(load)` plus
   `watch(src, load)`. Two code paths for one behaviour eventually disagree.
9. Every async watcher cancels its previous run: register
   `onWatcherCleanup(() => controller.abort())` (3.5+, or the third `onCleanup`
   argument) synchronously before the first `await`. Without it the slower
   response lands last and overwrites current data; a debounce narrows the race
   rather than removing it.
10. Lifecycle hooks, `provide`, `defineExpose` and watcher creation must run
    synchronously in setup. After an `await`, inside a timeout, or in a
    callback they register against no instance and never run — silently.
11. `v-if` and `v-for` never share an element: `v-if` is evaluated first, so the
    loop variable does not exist. Filter in a `computed`, or move `v-if` to a
    child of `<template v-for>`.
12. Every `v-for` key is a stable identity, never the array index. An index key
    makes Vue patch the wrong node on reorder, which surfaces as an input
    holding the previous row's text.
13. Filtering, sorting and formatting live in `computed`, not in the template.
    A template expression re-runs on every render; a computed caches.
14. Mutating an object through `defineModel` does not emit — the parent's value
    changes with nothing notified. Replace the value:
    `model.value = { ...model.value, name }`.
15. Declare every event in `defineEmits`. An undeclared event also falls through
    as a native listener, so a `@click` you emit fires twice.
16. `provide` the ref, not `ref.value`, type the channel with an
    `InjectionKey<T>`, and hand children `readonly()` plus explicit updaters.
    Provided state that any descendant can write makes the origin of a change
    unfindable.
17. Composables take `MaybeRefOrGetter` and call `toValue()` inside the tracked
    scope; calling it once at the top snapshots the input and the effect never
    re-runs. They return refs, never a `reactive()` object, so destructuring
    works.
18. State declared at module scope in a composable is one instance per process.
    In an SSR app that is a cross-request leak — one visitor's data served to
    the next. Scope it per request instead.
19. A Pinia setup store must return every state ref, and none of them wrapped in
    `readonly()`. A ref left out, or made readonly, is invisible to Pinia:
    SSR hydration, devtools and every plugin lose it with no error.
20. Destructure a store with `storeToRefs()` for state and getters; actions can
    be destructured directly because they are bound to the store. A plain
    destructure detaches, which is the usual reason a store-backed UI freezes.
21. `useStore()` runs after `app.use(pinia)` and inside a function body — never
    at module top level. At module scope it throws
    `getActivePinia was called with no active Pinia`, and under SSR it would
    share one store across requests.
22. Navigating `/users/1` → `/users/2` reuses the component instance, so no
    lifecycle hook fires. Load param-driven data in
    `watch(() => route.params.id, ..., { immediate: true })` or
    `onBeforeRouteUpdate`.
23. Navigation guards return: `undefined` proceeds, `false` cancels, a route
    location redirects. Do not mix that with the legacy `next` callback —
    forgetting `next` hangs navigation, calling it twice throws.
24. In Nuxt, never call bare `$fetch` during setup: its result is not in the
    payload, so it runs on the server and again on hydration. Use `useFetch`
    or `useAsyncData` for initial data and `$fetch` for event-driven requests,
    and render off the returned `status` and `error` refs — `data` is
    `undefined` on a failure and while a lazy or client-only request is pending.
25. In Nuxt, `data` is a shallow ref (`deep` defaults to `false`) — replace the
    value instead of mutating inside it; and `useFetch` keys include the call
    site, so sharing one request between components needs one explicit `key`.
    Private `runtimeConfig` is server-only: reading it in a component yields
    `undefined` on the client, and a secret must never be in `public`.

## Workflows

**Stack detection (run first, every workflow).**

```bash
cat package.json                      # vue / nuxt / pinia / vue-router versions
ls nuxt.config.* vite.config.* 2>/dev/null
ls app/pages src/pages 2>/dev/null    # Nuxt 4 uses app/
```

- No `nuxt` dependency → skip `references/nuxt.md` and rules 24–25.
- `vue` below 3.5 → rule 4's destructure form is unavailable; `withDefaults` and
  `props.x` are the only options. Say so instead of writing 3.5 code.
- No `pinia` → rules 19–21 do not apply; check whether the project's shared
  state is `provide`/`inject` or a plain composable before proposing a store.

### implement-feature

- [ ] Run stack detection and read one neighbouring component; adopt its file
      layout, naming and prop conventions instead of introducing a second one.
- [ ] Map the components before writing markup: one responsibility per
      component in one sentence, props/emits contract for each, and which parts
      are composition surfaces (route views, app root) versus feature UI.
- [ ] Decide where each piece of state lives, narrowest first: local `ref` →
      lifted to the parent → the URL (filters, pagination, tabs, search) →
      server cache → `provide`/`inject` for one subtree → a store. See
      `references/pinia.md` before adding a store.
- [ ] Write the reactivity layer with rules 2–9 in mind; derived values are
      `computed`, effects are `watch`.
- [ ] Extract stateful or effectful logic into a composable per
      `references/composables.md` — it owns its own teardown.
- [ ] Type the surfaces: `defineProps`/`defineEmits` generics, `defineSlots`
      when the component is shared, `InjectionKey` for injected values.
- [ ] Handle the loading, empty and error state in the same pass. A component
      without all three is unfinished.
- [ ] Add tests per `add-tests`.
- [ ] **Gate — CONTRACT CHECK:** `vue-tsc --noEmit` (or the project's typecheck
      script) and lint pass, the dev console shows no Vue warnings for the new
      path, and no `reactive()` object is reassigned anywhere in the diff.

### diagnose-not-updating

For "the value changes but the UI does not" — the most common Vue bug class.

- [ ] Reproduce and locate the boundary: does the source value actually change
      (log it or watch it), and is the consumer re-rendering at all?
- [ ] Walk the detachment list in `references/reactivity.md` in order —
      destructured `reactive`, reassigned proxy, missing `.value`, destructured
      props, plain value passed as a watch source, ref inside an array, mutated
      shallow ref. One of these is nearly always the answer.
- [ ] If a store is involved, check rule 20 (`storeToRefs`) and rule 19 (state
      not returned) before anything else.
- [ ] If Nuxt data is involved, check rule 25: `data` is shallow.
- [ ] If the value updates but the DOM read is stale, it is flush timing:
      `await nextTick()` or `flush: 'post'`.
- [ ] **Gate — CAUSAL CHAIN:** the explanation names the exact line where
      reactivity is lost and why, and reverting only the fix reproduces the
      symptom again.

### review

- [ ] Establish the diff scope and read its tests first — they state what the
      author believes the code does.
- [ ] Walk the Core rules in order; they are ordered by how often each one is
      the real defect.
- [ ] Check the reactivity surface specifically: detachment, side effects in
      computeds, watchers that should be computeds, uncancelled async watchers,
      hooks registered after an `await`.
- [ ] Check the component contract: mutated props, undeclared emits, object
      mutation through `defineModel`, `defineExpose` after an `await`, missing
      `$attrs` forwarding on a multi-root wrapper.
- [ ] Check the store and route surface against `references/pinia.md` and
      `references/router.md`.
- [ ] On a Nuxt diff, check the server/client boundary and the data layer
      against `references/nuxt.md` — hydration causes, duplicate keys, private
      config in a template.
- [ ] Drop findings whose fix costs more than they return, and say what you
      dropped.
- [ ] Report with `## Output format`.
- [ ] **Gate — CITED AND CONCRETE:** every finding carries `path:line`, one line
      of consequence, and a fix that compiles.

### add-tests

- [ ] Pick the level from `references/testing.md` before writing a line:
      plain function call, component mount, store test, or end-to-end.
- [ ] Drive each test through props, user interactions, emitted events and
      store APIs; assert rendered output, emitted payloads and store state.
- [ ] Composables that use lifecycle hooks or `inject` get a throwaway host
      component; without it the hooks never fire and the test proves nothing.
- [ ] Pinia: `createTestingPinia({ createSpy: vi.fn })` as a mount plugin for
      component tests, `setActivePinia(createPinia())` for store tests.
- [ ] Await the right thing: `await trigger(...)`/`setProps(...)` for renders,
      `flushPromises()` for pending promises. Never a `setTimeout`.
- [ ] Delete snapshot-only tests and `wrapper.vm` assertions rather than
      porting them.
- [ ] **Gate — DIFFERENTIAL:** each new test fails when the behaviour it covers
      is reverted, and the suite passes with no unhandled promise warnings.

### optimize

Only after the behaviour is correct and covered.

- [ ] Measure first: Vue DevTools' component timeline, or
      `app.config.performance = true` plus the browser performance panel. Record
      the number.
- [ ] Use `onRenderTriggered` to answer "why did this component update" instead
      of guessing.
- [ ] Work in payoff order per `references/performance.md`: route-level code
      splitting → list rendering (virtualise, stable keys, inline rows) →
      update frequency (`v-memo` on a measured hot subtree) → reactivity depth
      (`shallowRef`, `markRaw` for external instances).
- [ ] **Gate — MEASURED:** the same measurement is repeated after the change and
      quoted, and no `v-memo` dependency array omits a value the subtree reads.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Primitives, every way reactivity detaches, props destructure, `computed`/`watch`/`watchEffect`, flush timing, watcher cleanup, `shallowRef`/`markRaw`, `effectScope` | Any reactivity question, and every `diagnose-not-updating` run | `references/reactivity.md` |
| `<script setup>` macros, props/emits/`defineModel`/`defineExpose`/slots, template refs, lifecycle timing, provide/inject, built-in components, template rules, scoped styles | Writing or reviewing a component | `references/components.md` |
| Composable contracts, `MaybeRefOrGetter`/`toValue`, teardown ownership, call-site restrictions, module-scope leaks, VueUse boundary | Extracting or reviewing a `use*` function | `references/composables.md` |
| Store shape, returning state, `storeToRefs`, `$patch`/`$reset`/`$subscribe`, use outside components, SSR hydration, plugins | Any Pinia work, or deciding whether state needs a store | `references/pinia.md` |
| Router 5 changes, param-change handling, guard semantics and placement, lazy routes, typed routes, `meta`, scroll behaviour, URL as state | Routing, navigation guards, or param-driven data | `references/router.md` |
| Nuxt 4 directories, data primitive choice, shallow `data`, keys and de-duplication, `await`/`lazy`, `createUseFetch`, `useState`, hydration mismatches, server/client boundary, runtime config, server routes, page meta | Any file in a Nuxt project | `references/nuxt.md` |
| Runner and level choice, public-surface assertions, async flushing, composable hosts, `createTestingPinia` modes, Suspense/Teleport, `mountSuspended`, what not to write | Running `add-tests`, or reviewing a test diff | `references/testing.md` |
| Optimisation order, list rendering, `v-memo`/`v-once`, prop and computed stability, reactivity overhead, bundle and load, measuring | Running `optimize`, or a performance complaint | `references/performance.md` |

## Output format

Use this shape for `review` and for any report on existing code. No preamble —
the reader wrote the code.

```
<path>

<path>:<line> - <severity>: <what is wrong>
  Consequence: <what it costs, concretely>
  Fix: <the change; one or two lines of code when that is clearer than prose>

<next path>
...

## Verdict
<counts by severity, then the one change to make first>
```

Severities: `blocking` (wrong behaviour, lost reactivity, leaked secret,
cross-request state leak), `important` (unnecessary re-render path, missing
cancellation, missing test level, unstable key), `minor` (naming, ordering,
dead code). A file that passes gets one line: `<path> - ✓ pass`.

Worked example:

```
app/components/CartSummary.vue

app/components/CartSummary.vue:6 - blocking: `const { subtotal, lines } = cart`
  destructures the store, so both values are plain snapshots.
  Consequence: the subtotal renders once and never updates again.
  Fix: const { subtotal, lines } = storeToRefs(cart)

app/composables/useSearch.ts

app/composables/useSearch.ts:11 - important: the watcher fetches with no
  cancellation.
  Consequence: a slow earlier request lands last and overwrites results for the
  query the user has already replaced.
  Fix: register onWatcherCleanup(() => controller.abort()) before the first
  await and pass controller.signal to fetch.

## Verdict
1 blocking, 1 important, 0 minor. Fix the store destructure first — the search
race is invisible until the subtotal renders at all.
```

## Environment

Node.js 20+; use the project's own package runner (`npm` / `pnpm` / `yarn` /
`bun`) as declared in `packageManager`.

```bash
npm run dev                       # Vite dev server, or `nuxt dev`
npx vue-tsc --noEmit              # template + script typecheck
npx vitest run                    # unit and component tests
npx nuxt prepare                  # Nuxt: regenerate types after config changes
```

Editor and typecheck support comes from Vue's official language tooling
(`vue-tsc`, Vue Language Tools). `vue-tsc` checks templates, so it reports
errors `tsc` never sees — treat it, not `tsc`, as the typecheck gate. Pinia 4
requires `@vue/devtools-api` to be installed alongside it.
