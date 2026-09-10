# JavaScript and advanced-hook rules

Low to medium impact per site; they matter in hot paths — render loops, event
handlers, list mapping over thousands of items. Apply them where a profile
points, not everywhere.

Verified against: React 19.3.

## Contents

- Data structures: `js-index-maps`, `js-set-map-lookups`
- Iteration: `js-combine-iterations`, `js-flatmap-filter`, `js-min-max-loop`, `js-early-exit`, `js-length-check-first`
- Immutability: `js-tosorted-immutable`
- Caching: `js-cache-function-results`, `js-cache-property-access`, `js-cache-storage`, `js-hoist-regexp`
- DOM and scheduling: `js-batch-dom-css`, `js-request-idle-callback`
- Advanced hooks: `advanced-use-latest`, `advanced-effect-event-deps`, `advanced-event-handler-refs`

---

## Data structures

### `js-index-maps`

Repeated `.find()` by the same key is O(n) per lookup. Build the index once.

```ts
// Incorrect — 1000 orders x 1000 users = 1,000,000 comparisons
orders.map((o) => ({ ...o, user: users.find((u) => u.id === o.userId) }))

// Correct — 2000 operations
const userById = new Map(users.map((u) => [u.id, u]))
orders.map((o) => ({ ...o, user: userById.get(o.userId) }))
```

### `js-set-map-lookups`

`array.includes(x)` inside a filter is the same mistake in miniature. Convert
the haystack to a `Set` once, then `has`.

---

## Iteration

### `js-combine-iterations`

Three `.filter()` passes over the same array are three traversals. One `for`
loop pushing into three arrays is one.

### `js-flatmap-filter`

`.map(...).filter(Boolean)` builds an intermediate array and traverses twice.
`.flatMap()` does both in one pass:

```ts
const names = users.flatMap((u) => (u.isActive ? [u.name] : []))
```

### `js-min-max-loop`

Sorting to read one element is O(n log n) for an O(n) answer. Loop once,
tracking the extreme. Same for "oldest and newest": one pass, two variables.

### `js-early-exit`

Return as soon as the answer is known instead of setting a flag and finishing
the loop.

### `js-length-check-first`

Before an expensive comparison of two collections — sort, deep equality,
serialization — compare lengths. Different lengths mean not equal, at O(1).

```ts
function hasChanges(current: string[], original: string[]) {
  if (current.length !== original.length) return true
  const a = current.toSorted()
  const b = original.toSorted()
  return a.some((value, i) => value !== b[i])
}
```

---

## Immutability

### `js-tosorted-immutable`

This is a correctness rule, not a micro-optimization. `.sort()`, `.reverse()`
and `.splice()` mutate in place. Applied to a prop or a state value they rewrite
data the component does not own, break React's immutability model, and produce
stale-closure bugs.

```tsx
// Incorrect — rewrites the caller's array during render
const sorted = useMemo(() => users.sort(byName), [users])

// Correct
const sorted = useMemo(() => users.toSorted(byName), [users])
```

Immutable counterparts: `toSorted`, `toReversed`, `toSpliced`, `with`. All are
available in current browsers and Node 20+; the fallback is an explicit copy,
`[...items].sort(...)`.

Sorting the result of a `.filter()` or `.map()` is safe — those already return a
new array. The bug is sorting the prop or state value itself.

---

## Caching

### `js-cache-function-results`

When a pure function runs repeatedly with the same inputs during render
(slugify, format, parse), memoize it in a module-level `Map`. Bound the cache,
or key it on data that is naturally bounded, so it cannot grow without limit.

### `js-cache-property-access`

In a hot loop, hoist deep property chains and `array.length` out of the loop
body. Only worth doing where the loop is actually hot.

### `js-cache-storage`

`localStorage`, `sessionStorage` and `document.cookie` are synchronous and slow.
Cache reads in a module-level `Map`, keep it in sync on write, and invalidate it
from a `storage` event if another tab can change the same key. A `Map` rather
than a hook, so utilities and event handlers can use it too.

### `js-hoist-regexp`

Do not construct a `RegExp` during render. Hoist a constant pattern to module
scope; memoize a query-dependent one on the query (and escape the input).

A global (`/g`) regex carries mutable `lastIndex` state, so a shared instance
returns alternating results from repeated `.test()` calls. Do not share one.

---

## DOM and scheduling

### `js-batch-dom-css`

Consecutive style writes are batched by the browser. Reading a layout property
(`offsetWidth`, `getBoundingClientRect()`, `getComputedStyle()`) between writes
forces a synchronous reflow each time. Group all reads, then all writes — or all
writes, then one read.

### `js-request-idle-callback`

Defer non-critical follow-up work — analytics, recent-search persistence,
prefetching — to `requestIdleCallback`, so it cannot compete with the
interaction that triggered it. Pass a `timeout` for work that must eventually
run.

---

## Advanced hooks

### `advanced-use-latest`

`useEffectEvent` (React 19.2+) gives a stable function that always calls the
latest version of a callback, so the effect stops re-running when the callback's
identity changes.

```tsx
const onSearchEvent = useEffectEvent(onSearch)

useEffect(() => {
  const timeout = setTimeout(() => onSearchEvent(query), 300)
  return () => clearTimeout(timeout)
}, [query]) // onSearch is no longer a dependency
```

### `advanced-effect-event-deps`

The function returned by `useEffectEvent` intentionally has a new identity every
render. Putting it in a dependency array makes the effect re-run every render
and trips the hooks lint rule. Depend on the reactive values only, and call the
Effect Event from inside the effect body.

### `advanced-event-handler-refs`

Before React 19.2, the same result came from a ref: store the handler in a ref,
update it in an effect, and subscribe with a stable wrapper that reads
`ref.current`. Use this only when the project cannot yet use `useEffectEvent`.

<details>
<summary>Old pattern: handler-in-a-ref</summary>

```tsx
function useWindowEvent(event: string, handler: (e: Event) => void) {
  const handlerRef = useRef(handler)
  useEffect(() => { handlerRef.current = handler }, [handler])

  useEffect(() => {
    const listener = (e: Event) => handlerRef.current(e)
    window.addEventListener(event, listener)
    return () => window.removeEventListener(event, listener)
  }, [event])
}
```

</details>

<!-- sources: vercel-react-bp, react-docs -->
