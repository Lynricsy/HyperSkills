# Composables: contracts and lifetimes

Verified against: Vue 3.5

## Contents

- [What belongs in a composable](#what-belongs-in-a-composable)
- [Accept refs, getters or values](#accept-refs-getters-or-values)
- [Return refs, never a reactive object](#return-refs-never-a-reactive-object)
- [Own the teardown](#own-the-teardown)
- [Call-site restrictions](#call-site-restrictions)
- [Module scope is shared state](#module-scope-is-shared-state)
- [Keep the setup phase synchronous](#keep-the-setup-phase-synchronous)
- [Do not reimplement VueUse](#do-not-reimplement-vueuse)

## What belongs in a composable

Extract into `use*()` when logic is stateful, reused, or side-effect heavy —
subscriptions, timers, observers, request lifecycles, form state machines. A
pure transformation is a plain function in `utils/`, not a composable; wrapping
it in `use*` implies reactivity that is not there.

A composable owns state and effects. It does not render, and it does not reach
into a specific component's DOM.

## Accept refs, getters or values

Normalise inputs so callers do not have to think about it:

```ts
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useSearch(query: MaybeRefOrGetter<string>) {
  const results = ref<Result[]>([])

  watchEffect(async () => {
    const q = toValue(query)          // ref, getter or plain value
    const controller = new AbortController()
    onWatcherCleanup(() => controller.abort())
    results.value = await fetchResults(q, controller.signal)
  })

  return { results }
}

useSearch('vue')                 // constant
useSearch(queryRef)              // ref
useSearch(() => props.category)  // getter — the only shape that tracks a prop
```

`toValue()` must be called **inside** the tracked scope. Calling it once at the
top of the composable snapshots the value and the effect never re-runs.

## Return refs, never a reactive object

```ts
return { x, y }                  // destructuring keeps reactivity
return reactive({ x, y })        // destructuring detaches
```

Return `computed()` for derived values so callers cannot write to them, and
return functions for the actions. Name the pair after the domain, not the
mechanism (`useCart`, not `useCartRefs`).

## Own the teardown

Whatever the composable subscribes to, it unsubscribes. A caller that has to
remember a `stop()` call will eventually forget.

```ts
export function useResize(onResize: () => void) {
  onMounted(() => window.addEventListener('resize', onResize))
  onUnmounted(() => window.removeEventListener('resize', onResize))
}
```

When the composable can also be used outside a component (inside a store, or a
manually created scope), use `onScopeDispose()` instead of `onUnmounted()`: it
works in both places. `effectScope()` groups several effects so one `stop()`
disposes them together — the shape to use for a shared/singleton composable.

## Call-site restrictions

A composable that registers lifecycle hooks, calls `inject()`, or relies on the
current instance must be called synchronously from `<script setup>` or `setup()`.
Called from an event handler, a `setTimeout`, or after an `await`, the hooks
register against nothing and `inject()` returns the default — silently.

If a composable must be callable from anywhere, it cannot use `inject` or
lifecycle hooks; make it take its dependencies as arguments instead.

## Module scope is shared state

```ts
// composables/useUser.ts
const user = ref<User | null>(null)   // one instance for the whole process
export const useUser = () => user
```

In a client-only SPA this is a deliberate singleton. Under SSR it is a
cross-request leak: the module lives for the server's lifetime, so one user's
data is served to the next request. Either scope the state per request through
the framework's mechanism (`useState` in Nuxt — see `references/nuxt.md`) or a
store created per request, or create the state inside the composable so each
caller gets its own.

## Keep the setup phase synchronous

Expose async work as returned functions rather than making the composable
itself `async`:

```ts
// Prefer
export function useProfile(id: MaybeRefOrGetter<string>) {
  const data = ref<Profile | null>(null)
  const load = async () => { data.value = await fetchProfile(toValue(id)) }
  return { data, load }
}
```

An `async` composable forces its caller into async setup, which requires a
`<Suspense>` boundary above it and drops any `defineExpose` and lifecycle hook
registered after the await.

## Do not reimplement VueUse

`useStorage`, `useEventListener`, `useDebounceFn`, `useIntersectionObserver`,
`useMediaQuery`, `createReusableTemplate` and friends already handle the SSR
guards and cleanup. Install `@vueuse/core` and use them; write a local
composable only for domain logic. When names collide, Vue's own `toRef`,
`toRefs` and `toValue` are the canonical reactivity utilities — check the import
path if one of them behaves oddly.

<!-- sources: vuejs-ai-skills, onmax-nuxt-skills, antfu-skills, awesome-copilot, vue-docs -->
