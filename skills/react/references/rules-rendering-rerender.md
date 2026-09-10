# Re-render and rendering rules

Two categories: `rerender-*` cuts wasted renders, `rendering-*` cuts the work
the browser does per render. Medium impact individually; they compound in lists
and on input-driven UI.

Verified against: React 19.3.

**Before applying the memoization entries, check for React Compiler.** If
`babel-plugin-react-compiler` is in `package.json`, or `reactCompiler` is set in
`next.config.*`, the compiler inserts memoization automatically: skip
`rerender-memo`, `rerender-simple-expression-in-memo`,
`rerender-split-combined-hooks` and `rendering-hoist-jsx` as *performance*
findings. The correctness entries below still apply — the compiler does not fix
a mutated prop, a component defined inside a component, or state mirrored
through an effect.

## Contents

- Correctness first: `rerender-no-inline-components`, `rerender-derived-state-no-effect`, `rerender-move-effect-to-event`, `advanced-init-once`
- Subscribing less: `rerender-defer-reads`, `rerender-derived-state`, `rerender-use-ref-transient-values`
- State and callbacks: `rerender-lazy-state-init`, `rerender-functional-setstate`
- Memoization: `rerender-memo`, `rerender-simple-expression-in-memo`, `rerender-split-combined-hooks`, `rerender-dependencies`, non-primitive default props
- Responsiveness: `rerender-transitions`, `rerender-use-deferred-value`, `rendering-usetransition-loading`, `rendering-activity`
- Cheaper renders: `rendering-hoist-jsx`, `rendering-content-visibility`, `rendering-conditional-render`, `rendering-animate-svg-wrapper`, `rendering-svg-precision`
- Hydration: `rendering-hydration-no-flicker`, `rendering-hydration-suppress-warning`
- Resource hints: `rendering-resource-hints`, `rendering-script-defer-async`

---

## Correctness first

### `rerender-no-inline-components`

Impact: HIGH. A component defined inside another component is a new type on
every render, so React unmounts the old instance and mounts a new one.

```tsx
// Incorrect — Avatar remounts on every UserProfile render
function UserProfile({ user, theme }) {
  const Avatar = () => <img src={user.avatarUrl} data-theme={theme} />
  return <Avatar />
}

// Correct — a module-level component with props
function Avatar({ src, theme }: { src: string; theme: string }) {
  return <img src={src} data-theme={theme} />
}
```

Symptoms that point straight at this bug: an input loses focus on every
keystroke, animations restart, effect cleanup and setup run on every parent
render, scroll position resets.

### `rerender-derived-state-no-effect`

Impact: MEDIUM, and a correctness risk. A value computable from props or state
is not state.

```tsx
// Incorrect — an extra render pass, and fullName can drift
const [fullName, setFullName] = useState('')
useEffect(() => setFullName(first + ' ' + last), [first, last])

// Correct
const fullName = first + ' ' + last
```

The same applies to counts, filtered lists and flags mirrored out of another
value. To reset state when a prop changes, change the component's `key` instead
of writing to state in an effect.

### `rerender-move-effect-to-event`

Impact: MEDIUM. A side effect caused by a user action belongs in that action's
handler, not in state plus an effect.

```tsx
// Incorrect — the effect re-runs when theme changes, re-posting the form
const [submitted, setSubmitted] = useState(false)
useEffect(() => {
  if (submitted) { post('/api/register'); showToast('Registered', theme) }
}, [submitted, theme])

// Correct
function handleSubmit() {
  post('/api/register')
  showToast('Registered', theme)
}
```

### `advanced-init-once`

Impact: LOW-MEDIUM. App-wide initialization inside `useEffect([])` runs twice in
development and again on every remount.

```tsx
let didInit = false

function App() {
  useEffect(() => {
    if (didInit) return
    didInit = true
    loadFromStorage()
    checkAuthToken()
  }, [])
}
```

Better still, run it at the top level of the entry module where a guard is not
needed.

---

## Subscribing less

### `rerender-defer-reads`

Impact: MEDIUM. Do not subscribe to changing state that is only read inside a
callback.

```tsx
// Incorrect — re-renders on every search-param change
const searchParams = useSearchParams()
const onShare = () => share(searchParams.get('ref'))

// Correct — read on demand, no subscription
const onShare = () => share(new URLSearchParams(window.location.search).get('ref'))
```

### `rerender-derived-state`

Impact: MEDIUM. Subscribe to the boolean you need, not the continuous value it
comes from.

```tsx
// Incorrect — re-renders on every pixel of resize
const isMobile = useWindowWidth() < 768

// Correct — re-renders only when the boolean flips
const isMobile = useMediaQuery('(max-width: 767px)')
```

### `rerender-use-ref-transient-values`

Impact: MEDIUM. Values that change many times a second and are not read during
render (pointer position, timers, transient flags) belong in a ref; writing a
ref does not re-render. Drive the visual with a direct style write on a
ref'd node.

---

## State and callbacks

### `rerender-lazy-state-init`

Impact: MEDIUM. `useState(expensive())` evaluates the argument on every render
and throws the result away after the first.

```tsx
// Incorrect
const [index, setIndex] = useState(buildSearchIndex(items))

// Correct
const [index, setIndex] = useState(() => buildSearchIndex(items))
```

Use the lazy form for storage reads, `JSON.parse`, index and map construction,
and DOM reads. Skip it for primitives and cheap literals — the closure costs
more than `useState(0)`.

Note the second bug this shape usually hides: state initialized from a prop
never updates when the prop changes. If the value should track the prop, derive
it or memoize it instead of storing it.

### `rerender-functional-setstate`

Impact: MEDIUM. Update from the previous value with the updater form; the
callback then needs no state dependency and cannot capture a stale value.

```tsx
// Incorrect — recreated on every items change, and the second is stale
const addItems = useCallback((next) => setItems([...items, ...next]), [items])
const removeItem = useCallback((id) => setItems(items.filter((i) => i.id !== id)), [])

// Correct — stable and always current
const addItems = useCallback((next) => setItems((curr) => [...curr, ...next]), [])
const removeItem = useCallback((id) => setItems((curr) => curr.filter((i) => i.id !== id)), [])
```

Direct assignment stays fine for a constant or a value that comes purely from
arguments.

---

## Memoization

### `rerender-memo`

Impact: MEDIUM. Extract expensive work into a memoized child so the parent can
return early before that work runs.

```tsx
// Incorrect — the avatar computation runs even while loading
const avatar = useMemo(() => <Avatar id={computeAvatarId(user)} />, [user])
if (loading) return <Skeleton />

// Correct
const UserAvatar = memo(function UserAvatar({ user }) {
  return <Avatar id={useMemo(() => computeAvatarId(user), [user])} />
})
```

### `rerender-simple-expression-in-memo`

Impact: LOW-MEDIUM. A short expression with a primitive result costs less than
the `useMemo` call and its dependency comparison.

```tsx
// Incorrect
const isLoading = useMemo(() => a.isLoading || b.isLoading, [a.isLoading, b.isLoading])
// Correct
const isLoading = a.isLoading || b.isLoading
```

### `rerender-split-combined-hooks`

Impact: MEDIUM. One hook doing two independent jobs re-runs both when either
dependency changes.

```tsx
// Incorrect — changing sortOrder re-filters
const sorted = useMemo(() => {
  const filtered = products.filter((p) => p.category === category)
  return filtered.toSorted(bySort(sortOrder))
}, [products, category, sortOrder])

// Correct
const filtered = useMemo(() => products.filter((p) => p.category === category), [products, category])
const sorted = useMemo(() => filtered.toSorted(bySort(sortOrder)), [filtered, sortOrder])
```

The same applies to a `useEffect` that does two unrelated things — split it so
each runs on its own dependency.

A dependency the body never reads is a separate bug: it re-runs the work and
produces a new array identity, which then wakes every downstream memo and
effect. Remove it, or make the body actually use it.

### `rerender-dependencies`

Impact: LOW. Depend on the primitive you read, not the object that contains it:
`[user.id]`, not `[user]`. For a threshold, compute the boolean outside the
effect and depend on that (`[isMobile]`, not `[width]`), so the effect runs on
the transition instead of on every value.

### Non-primitive default props

A default parameter like `onClick = () => {}` creates a new function on every
render. It does **not** break the `memo()` comparison of its own component —
React compares the props the parent passed, before defaults apply, so an
omitted prop is `undefined` on both renders and the comparison passes. What it
breaks is everything downstream: that identity flows into hook dependency
arrays and into memoized children, and changes every render.

```tsx
// Incorrect — a fresh identity every render, passed on to children and deps
function Toolbar({ onClick = () => {}, items = [] }) {
  useEffect(() => subscribe(onClick), [onClick]) // re-subscribes every render
  return <ItemList items={items} onClick={onClick} />
}

// Correct — stable identities
const NOOP = () => {}
const EMPTY: readonly Item[] = []

function Toolbar({ onClick = NOOP, items = EMPTY }) { /* ... */ }
```

Upstream states this rule as "the default breaks `memo()`", which is not how
`memo` works. Hoist the constant anyway, for the reason above.

---

## Responsiveness

### `rerender-transitions`

Impact: MEDIUM. Mark frequent, non-urgent updates as transitions so they cannot
block input: `const onScroll = () => startTransition(() => setScrollY(window.scrollY))`.

### `rerender-use-deferred-value`

Impact: MEDIUM. When typing drives an expensive render, let the result lag
behind the input.

```tsx
const deferredQuery = useDeferredValue(query)
const filtered = useMemo(
  () => items.filter((item) => match(item, deferredQuery)),
  [items, deferredQuery],
)
const isStale = query !== deferredQuery
```

The `useMemo` is required — without it the expensive work still runs on every
render. `isStale` is also the honest source for a "searching" indicator: a flag
derived only from "the input is non-empty" never turns off.

### `rendering-usetransition-loading`

Impact: LOW. Prefer `useTransition`'s `isPending` over a hand-managed
`isLoading` state: it resets correctly when the transition throws, and a new
transition supersedes a pending one.

### `rendering-activity`

Impact: MEDIUM. `<Activity>` (React 19.2+) hides a subtree while preserving its
state and DOM — the right tool for an expensive panel that toggles often, and
for pre-rendering content that is about to become visible.

```tsx
<Activity mode={isOpen ? 'visible' : 'hidden'}>
  <ExpensiveMenu />
</Activity>
```

---

## Cheaper renders

- `rendering-hoist-jsx` (LOW): a static element defined at module scope is
  created once. Worth it mainly for large static SVG.
- `rendering-content-visibility` (HIGH for long lists): `content-visibility: auto`
  plus `contain-intrinsic-size` lets the browser skip layout and paint for
  off-screen rows. Cheaper than virtualization and needs no library.
- `rendering-conditional-render` (LOW, correctness): use a ternary, not `&&`,
  when the condition can be `0` or `NaN` — `{count && <Badge/>}` renders a bare
  `0`. Write `{count > 0 ? <Badge/> : null}`.
- `rendering-animate-svg-wrapper` (LOW): animate a wrapping `div`, not the
  `svg` element — many browsers do not hardware-accelerate transforms on SVG
  elements. `rendering-svg-precision` (LOW): trim coordinate precision with
  `npx svgo --precision=1 --multipass icon.svg`.

---

## Hydration

### `rendering-hydration-no-flicker`

Impact: MEDIUM. For content that depends on client-only storage, neither
reading during render (breaks SSR) nor reading in an effect (flashes the default
first) is acceptable. Render a stable element and let a synchronous inline
script correct it before hydration:

```tsx
<>
  <div id="theme-wrapper">{children}</div>
  <script
    dangerouslySetInnerHTML={{
      __html: `(function(){try{var t=localStorage.getItem('theme')||'light';
        var el=document.getElementById('theme-wrapper');if(el)el.className=t;}catch(e){}})();`,
    }}
  />
</>
```

### `rendering-hydration-suppress-warning`

Impact: LOW-MEDIUM. `suppressHydrationWarning` is for a difference you intend
and can name — a locale-formatted timestamp, a random id. Wrap the smallest
element that carries the difference. Applied to a subtree it hides real bugs.

---

## Resource hints

### `rendering-resource-hints`

Impact: HIGH for critical resources. `react-dom` exposes `prefetchDNS`,
`preconnect`, `preload`, `preloadModule`, `preinit` and `preinitModule`. Called
from a Server Component they start loading before the client has the HTML.

| API | Use for |
|---|---|
| `prefetchDNS` | a third-party domain you will reach later |
| `preconnect` | an API or CDN you will fetch from immediately |
| `preload` | a critical font, stylesheet or image for this page |
| `preloadModule` | JS for the likely next navigation |
| `preinit` / `preinitModule` | a stylesheet or script that must execute early |

### `rendering-script-defer-async`

Impact: HIGH. A bare `<script src>` blocks HTML parsing. Use `defer` for
DOM-dependent or order-dependent scripts, `async` for independent ones such as
analytics. In Next.js use `next/script` with a `strategy` instead.

<!-- sources: vercel-react-bp, react-docs -->
