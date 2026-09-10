# Pinia stores

Verified against: Pinia 4.0

## Contents

- [Install](#install)
- [Setup store or option store](#setup-store-or-option-store)
- [Return every state ref](#return-every-state-ref)
- [Destructuring a store](#destructuring-a-store)
- [Store design](#store-design)
- [Mutating state](#mutating-state)
- [Using a store outside a component](#using-a-store-outside-a-component)
- [SSR](#ssr)
- [Cross-cutting hooks and plugins](#cross-cutting-hooks-and-plugins)

## Install

```bash
npm install pinia @vue/devtools-api
```

Since Pinia 4, `@vue/devtools-api` is a required peer dependency and the package
is ESM only. Installing `pinia` alone resolves, then fails at runtime in the
devtools integration.

## Setup store or option store

Setup stores (a function body) are the default in a Composition API codebase:
they can hold watchers, call composables, and `inject()` app-level providers.

```ts
export const useCartStore = defineStore('cart', () => {
  const lines = ref<CartLine[]>([])
  const subtotal = computed(() => lines.value.reduce(
    (sum, l) => sum + l.qty * l.unitPrice, 0,
  ))
  function add(line: CartLine) { /* ... */ }

  return { lines, subtotal, add }
})
```

The mapping is mechanical: `ref()` becomes state, `computed()` becomes a getter,
a function becomes an action. Option stores (`{ state, getters, actions }`) are
the escape hatch when a store is pure data and the team prefers the flatter
shape; they also track state automatically, which removes the next section's
failure mode.

## Return every state ref

**Every** state ref must be in the returned object, and none of them may be
wrapped in `readonly()`. A ref left out — or made readonly — is invisible to
Pinia, which breaks SSR hydration, devtools and every plugin (persistence
included), with no error at any point.

```ts
// Broken: authToken never crosses to the client, lines is not state at all
return { lines: readonly(lines), name, isLoggedIn, login }

// Correct: everything returned raw; `_` prefix signals "internal"
return { lines, name, _authToken: authToken, isLoggedIn, login }
```

There is no private state in a setup store. If a value must not be written from
outside, the enforcement is convention (a prefix) plus review, not `readonly()`.

## Destructuring a store

The store instance is a reactive object, so destructuring state or getters off
it produces detached values — the single most common reason a Pinia-backed UI
stops updating.

```ts
const cart = useCartStore()
const { lines, subtotal } = storeToRefs(cart)  // state + getters, as refs
const { add, clear } = cart                    // actions destructure directly
```

`storeToRefs` skips actions and non-reactive properties, and it picks up
properties added by plugins.

## Store design

- One store per domain (`cart`, `session`, `catalog`), not one per component and
  not one global store.
- Component-only state stays in the component. Reaching for a store first turns
  every read into a subscription and every test into a fixture.
- Getters are pure and synchronous. Anything async is an action.
- Actions own side effects, including the request lifecycle; expose `status`/
  `error` state from the store rather than making callers track it.
- A store may use another store: call `useOtherStore()` inside the action or the
  getter body, not at module level.

## Mutating state

```ts
cart.lines.push(line)                    // direct mutation is fine
cart.$patch({ couponCode: '', lines: [] }) // batched: one subscription trigger
cart.$patch(state => { state.lines.length = 0 }) // function form for arrays
cart.$reset()                            // option stores only
```

`$reset()` is generated from `state()`, so a setup store does not have one:
define your own `$reset()` in the store body and return it.

## Using a store outside a component

`useStore()` injects the active `pinia` instance. Outside a component there is
nothing to inject from, so the call must happen after `app.use(pinia)` and,
inside a router guard, inside the guard body:

```ts
router.beforeEach((to) => {
  const session = useSessionStore()   // inside the callback: pinia is installed
  if (to.meta.requiresAuth && !session.isLoggedIn) return '/login'
})
```

A `useStore()` at module top level runs at import time and throws
`getActivePinia was called with no active Pinia`. In an SSR app, hoisting a
store to module scope is worse than an error: it shares one store across every
request.

## SSR

- Hydrate `pinia.state.value` from the serialised server state **before** any
  `useStore()` call on the client.
- Serialise with an escaping serialiser (`devalue`), not `JSON.stringify` — store
  state can contain user-controlled strings.
- Setup stores that call composables need more care under SSR: anything reading
  the request must be created per request.
- On Nuxt, `@pinia/nuxt` wires all of this; state travels in the Nuxt payload
  and the store is request-scoped automatically.

## Cross-cutting hooks and plugins

`store.$subscribe(cb)` observes state changes, `store.$onAction(cb)` observes
action calls including `after`/`onError` hooks — use these for persistence,
analytics and error reporting instead of duplicating calls inside every action.
A Pinia plugin (`pinia.use(fn)`) adds properties or behaviour to every store;
properties it adds are picked up by `storeToRefs`.

<!-- sources: vuejs-ai-skills, awesome-copilot, awesome-skills-code-review, pinia-docs -->
