# Performance

Verified against: Vue 3.5

## Contents

- [Order of operations](#order-of-operations)
- [Update cost: where it actually goes](#update-cost-where-it-actually-goes)
- [Large lists](#large-lists)
- [v-memo and v-once](#v-memo-and-v-once)
- [Prop and computed stability](#prop-and-computed-stability)
- [Reactivity overhead](#reactivity-overhead)
- [Bundle and load](#bundle-and-load)
- [Measuring](#measuring)

## Order of operations

Performance work is a separate pass after the behaviour is correct and covered.
Optimising first hides bugs behind memoisation and produces code nobody can
change.

Then, in this order, because that is the order of payoff: page weight and
route-level splitting → list rendering → update frequency → reactivity depth →
micro-optimisation inside a component.

## Update cost: where it actually goes

Vue's compiler already hoists static vnodes and patches only the dynamic parts
of a template. So the wins are not in "avoiding re-renders" generically; they
are in these specific situations:

- A `v-for` over thousands of rows where each row is a component.
- A template expression that filters, sorts or formats on every render.
- A `watch(..., { deep: true })` over a large object.
- Deep reactivity on data that is only ever replaced wholesale.
- An `onUpdated` hook doing real work — it fires on every update of that
  component, including ones it does not care about.

## Large lists

Beyond a few hundred rows, virtualise: render only the visible window
(`useVirtualList` from VueUse, or a dedicated virtual-scroller component).
Nothing else recovers the scroll performance of a 10,000-row table.

Below that threshold, the two cheap wins are: give each row a stable `:key`
(never the index — an index key makes Vue patch the wrong nodes on reorder), and
inline simple rows instead of wrapping each in a component. Every row component
is a component instance, a props object, and a scope; for a plain
`<td>{{ value }}</td>` that overhead is the dominant cost.

## v-memo and v-once

```vue
<div v-memo="[item.id, item.selected]"> … expensive subtree … </div>
<footer v-once> … render-once content … </footer>
```

`v-memo` skips re-rendering a subtree while every listed dependency is
unchanged; it is the tool for "this row's markup is expensive and only two
fields matter". `v-once` renders exactly once and never updates — for genuinely
static content that still needs an initial interpolation.

Both are opt-outs from correctness checking: a dependency missing from the
`v-memo` array means the subtree shows stale data forever. Add them to a
measured hot path, not on principle.

## Prop and computed stability

A `computed` that returns a fresh object or array on every evaluation
invalidates everything downstream, because the identity always differs:

```ts
// Every dependent re-runs on any unrelated change
const options = computed(() => ({ pageSize: props.pageSize }))
```

Keep computeds returning primitives where possible, or derive the object once
from stable inputs. The same applies to props: passing an inline object literal
(`:config="{ dense: true }"`) creates a new object per render, so the child sees
a changed prop every time.

## Reactivity overhead

Deep reactivity costs measurably only for large structures — the documented
threshold is a render that walks on the order of 100,000 properties. When a
payload is that size and is only replaced wholesale, `shallowRef` /
- On Nuxt, `<NuxtLink>` already prefetches in-viewport routes; the `Lazy`
  component prefix plus a hydration strategy
  (`<LazyProductReviews hydrate-on-visible />`) defers the JS cost of
  below-the-fold islands.

External instances — chart objects, editors, SDK clients, map handles — should
never be proxied at all: `shallowRef` them, or `markRaw` them. Proxying them is
both slow and a correctness hazard.

## Bundle and load

- Route components via dynamic `import()` so each route is its own chunk.
- `defineAsyncComponent(() => import('./HeavyEditor.vue'))` for components not on
  the first paint, with `loadingComponent` and `errorComponent` set.
- Import from module paths, not a library's barrel entry, when the library does
  not tree-shake cleanly.
- On Nuxt, `<NuxtLink>` already prefetches in-viewport routes; lazy hydration
  directives on components (`hydrate-on-visible` and friends) defer the JS cost
  of below-the-fold islands.

## Measuring

Read a profile before changing anything. Vue DevTools' component timeline
attributes render time to components; `app.config.performance = true` marks
component init/patch in the browser performance panel. `onRenderTracked` and
`onRenderTriggered` answer "why did this component update", which is the
question that usually matters.

State the number before and after. An optimisation with no measurement is a
guess that also costs readability.

<!-- sources: vuejs-ai-skills, awesome-skills-code-review, awesome-copilot, onmax-nuxt-skills, vue-docs -->
