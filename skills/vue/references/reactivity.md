# Reactivity: the ways it breaks

Verified against: Vue 3.5

## Contents

- [Choosing a primitive](#choosing-a-primitive)
- [Every way reactivity gets lost](#every-way-reactivity-gets-lost)
- [Reactive props destructure (3.5+)](#reactive-props-destructure-35)
- [computed, watch, watchEffect](#computed-watch-watcheffect)
- [Flush timing](#flush-timing)
- [Async watchers and stale results](#async-watchers-and-stale-results)
- [Deep watch and the same-reference trap](#deep-watch-and-the-same-reference-trap)
- [Opting out: shallow, markRaw, triggerRef](#opting-out-shallow-markraw-triggerref)
- [Scopes and manual teardown](#scopes-and-manual-teardown)

## Choosing a primitive

`ref()` is the default for everything. It works for primitives and objects, it
survives reassignment, and it is the only shape that stays reactive when passed
around or returned from a composable.

| Use | When | Cost |
|---|---|---|
| `ref(x)` | Default. Any value; you reassign `.value` or mutate inside it | Deep proxy on object values |
| `reactive(obj)` | A settled state object you only ever mutate in place | Cannot be reassigned; destructuring detaches |
| `shallowRef(x)` | Large immutable structures, or an opaque external instance | Only `.value` assignment triggers |
| `shallowReactive(obj)` | Container whose nested payloads must stay raw | Nested mutations do not trigger |

`shallowRef` is a performance escape hatch for *large data structures* and for
integrating external state systems — not a default. Deep reactivity only costs
measurably when a single render walks on the order of 100,000 properties
[official]. Using `shallowRef` for a primitive buys nothing and plants a trap:
the day the value becomes an object, nested mutations silently stop rendering.

## Every way reactivity gets lost

Each of these compiles, runs, and silently stops updating. This list is the
first thing to check when "the value changes but the UI does not".

```ts
// 1. Destructuring reactive() detaches the copy from the proxy.
const state = reactive({ count: 0 })
const { count } = state          // plain number, frozen at 0
const { count } = toRefs(state)  // ref, stays live

// 2. Reassigning a reactive() object abandons every existing binding.
let filters = reactive({ q: '' })
filters = reactive({ q: '' })    // template still reads the old proxy
Object.assign(filters, { q: '' }) // correct: mutate in place, keep it const

// 3. Assigning to the ref variable instead of .value.
count = 5          // TypeError on const, silent detachment on let
count.value = 5

// 4. Refs inside arrays and Maps are not unwrapped.
const rows = reactive([ref(1)])
rows[0].value            // .value is required here
const state2 = reactive({ n: ref(1) })
state2.n                 // but a plain object property does unwrap

// 5. Reading a getter's result instead of passing the getter.
watch(props.id, cb)        // passes a number; warns and never fires
watch(() => props.id, cb)  // correct

// 6. Handing a plain value to a composable that expects a source.
useSearch(query.value)   // snapshot
useSearch(() => query.value) // getter; callee normalises with toValue()

// 7. Mutating a shallowRef's contents (including Nuxt's `data`).
list.value.push(item)                 // no render
list.value = [...list.value, item]    // renders
```

Proxy identity: `reactive(raw) !== raw`, and `reactive()` on an already-reactive
object returns the same proxy. Comparing a raw object against something read out
of reactive state fails; compare by id, or normalise one side with `toRaw()`.

## Reactive props destructure (3.5+)

Destructuring the `defineProps()` call is supported and is the idiomatic way to
declare defaults with type-based props. The compiler rewrites later references
to `props.x`, so reactivity is preserved.

```ts
const { category, pageSize = 20 } = defineProps<{
  category: string
  pageSize?: number
}>()
```

Two boundaries decide whether it works:

1. The transform only applies to destructuring **the macro call itself**, in the
   same `<script setup>` block. This is dead:

   ```ts
   const props = defineProps<{ category: string }>()
   const { category } = props   // plain string, never updates
   ```

2. Passing a destructured prop somewhere that needs a *source* still needs a
   getter, because the value itself is just a string:

   ```ts
   watch(category, cb)          // compiler warns; never fires
   watch(() => category, cb)    // correct
   useFilter(() => category)    // correct: callee applies toValue()
   ```

Props are read-only in both styles. `props.x = v` warns; mutating a nested field
of an object prop does not even warn but still corrupts the parent's state.
Emit an event, use `defineModel`, or derive local state.

## computed, watch, watchEffect

Pick by intent, not by convenience:

- Deriving a value → `computed`. It caches and it is the only one the template
  can depend on cheaply.
- Reacting to a *named* change with the old value → `watch`.
- Running an effect over several dependencies you do not want to enumerate →
  `watchEffect`. It runs immediately and re-runs on anything it touched.

```ts
// Wrong: a watcher that assigns a derived value. Extra render pass, and the
// copy drifts whenever a code path forgets to update it.
const total = ref(0)
watchEffect(() => { total.value = items.value.reduce(sum, 0) })

// Right
const total = computed(() => items.value.reduce(sum, 0))
```

A computed getter must be pure: no assignment to other state, no fetch, no
storage write, no emit. Vue caches on dependencies, so a side effect there fires
an unpredictable number of times. Move it into a `watch`.

`computed()` returns a read-only ref. When two-way binding is genuinely needed,
use the `get`/`set` form rather than a watcher pair.

Instead of `onMounted(load); watch(id, load)`, write
`watch(id, load, { immediate: true })` — one code path, no chance of the two
drifting. `{ once: true }` (3.4+) replaces the manual "stop myself" pattern.

`watchEffect` only tracks dependencies read **before its first `await`**.
Anything read after resumption is invisible to the tracker, so the effect never
re-runs for it. Read every dependency synchronously at the top.

## Flush timing

Watchers run before the component re-renders by default, so the DOM they see is
stale. Use `flush: 'post'` (or `watchPostEffect`) when the callback measures or
focuses an element. `flush: 'sync'` fires on every mutation with no batching —
reserve it for debugging.

DOM updates are batched: after changing state, `await nextTick()` before reading
layout.

## Async watchers and stale results

Any watcher that fetches races itself. Two requests in flight, the slower one
lands last, and the UI shows results for a query the user already replaced.
Cancel the previous run:

```ts
watch(query, async (q) => {
  const controller = new AbortController()
  onWatcherCleanup(() => controller.abort())   // 3.5+; or the 3rd `onCleanup` arg
  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, {
    signal: controller.signal,
  })
  results.value = await res.json()
})
```

`onWatcherCleanup` must be called synchronously, before the first `await` —
after that there is no active watcher to register against. A debounce reduces
the number of races; it does not remove them.

## Deep watch and the same-reference trap

With `{ deep: true }` on an object source, `newValue` and `oldValue` are the
same object: Vue hands you the mutated proxy twice. If the callback needs the
previous value, watch a projection (`() => structuredClone(...)`, or the
specific fields) instead. `{ deep: n }` (3.5+) caps traversal depth, which is
usually what an expensive deep watcher actually needed.

## Opting out: shallow, markRaw, triggerRef

An external instance stored in a plain `ref` gets proxied, and libraries that
compare `this` or hold internal caches break in confusing ways. Wrap it:

```ts
const chart = shallowRef<Chart>()            // preferred: no proxy at all
const client = ref(markRaw(new SdkClient())) // when it must live inside reactive state
```

After deliberately mutating deep inside a `shallowRef`, `triggerRef(theRef)`
forces dependents to re-run. Treat that as a considered optimisation, not a
fallback for "it did not update" — replacing the root value is clearer.

## Scopes and manual teardown

Watchers created inside `setup` stop with the component. Watchers created after
an `await`, inside a timeout, or in module scope do not — they leak, and on the
server they leak across requests. Two options: create them synchronously, or own
their lifetime with `effectScope()` and call `scope.stop()`. Inside a scope,
`onScopeDispose()` is the composable-friendly cleanup hook that works even when
there is no component instance.

<!-- sources: vuejs-ai-skills, onmax-nuxt-skills, antfu-skills, awesome-copilot, awesome-skills-code-review, vue-docs -->
