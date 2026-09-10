# Lists, rendering and interaction performance

Verified against: React Native 0.87, @shopify/flash-list 2.x, react-native-reanimated 4.x.

## Contents

- [Pick the list](#pick-the-list)
- [FlashList v2 vs v1](#flashlist-v2-vs-v1)
- [Row rules that decide the frame rate](#row-rules-that-decide-the-frame-rate)
- [Images in rows](#images-in-rows)
- [Text input latency](#text-input-latency)
- [Animations and gestures](#animations-and-gestures)
- [View hierarchy and flattening](#view-hierarchy-and-flattening)
- [What not to "optimize"](#what-not-to-optimize)
- [Old patterns](#old-patterns)

## Pick the list

| Situation | Use |
|---|---|
| A handful of rows, bounded and known | `ScrollView` is fine |
| Long or unbounded list, uniform rows | `FlatList` |
| Long list, complex or mixed rows, New Architecture | `FlashList` |
| Fixed row height and `FlatList` | add `getItemLayout` to skip measurement |

`FlashList` recycles cells instead of mounting new ones, which is what keeps
memory flat while scrolling a large list. It requires the New Architecture (the
only runtime from 0.82, so this is a constraint only for older projects).

The failure this table exists to prevent: a `ScrollView` wrapping
`items.map(...)`. Every row mounts, lays out and allocates native views before
the first frame, so the cost scales with the data length rather than the screen.

## FlashList v2 vs v1

Read the installed major (`node -p "require('@shopify/flash-list/package.json').version"`)
before writing or reviewing FlashList code.

| Prop | v1 | v2 |
|---|---|---|
| `estimatedItemSize` | required for good behaviour | removed/inert — v2 measures items itself |
| `estimatedListSize` | optional hint | inert |
| `estimatedFirstItemOffset` | optional hint | inert |
| `getItemType` | recommended for mixed rows | recommended for mixed rows |

Two symmetrical mistakes, both common: adding `estimatedItemSize` to a v2 list
(harmless but misleading, and it signals a stale mental model), and *flagging it
as missing* during a review of a v2 list. Neither is a fix.

## Row rules that decide the frame rate

- **`getItemType` for heterogeneous rows.** Return a stable string per row shape
  (`'post' | 'ad' | 'divider'`). Without it the recycler hands a post cell to an
  ad row, which unmounts and remounts the subtree — worse than no recycling.
- **Stable keys from data, never the index.** An index key makes every row after
  an insertion look changed, and it defeats recycling identity on reorder.
- **Hoist `renderItem`, `keyExtractor` and row callbacks** out of the parent, or
  memoize them. Defined inline they get a new identity per parent render, so the
  list re-renders every visible row on any parent state change — including the
  state that only one row cares about.
- **Row state belongs in the row.** A `selectedId` in the screen component
  re-renders the whole list per tap; holding "am I expanded" inside the row (or
  in an external store the row subscribes to) re-renders one cell.
- **Move per-row construction to module scope.** `new Intl.DateTimeFormat(...)`,
  `new Date()` formatting tables, regexes and derived lookup maps built inside
  `renderItem` are rebuilt for every row on every pass. Intl objects are
  particularly expensive to construct.
- **Keep row components cheap and side-effect free.** A recycled row that runs
  an effect on mount runs it again on every reuse. Fetching, measuring or timing
  inside a row multiplies by the scroll distance.
- **No inline style objects in a row.** `style={{padding: 12}}` allocates a new
  object per render and defeats the style-diffing fast path; use
  `StyleSheet.create` once.
- **Never nest a scrollable inside a same-axis scrollable.** A vertical
  `FlatList` inside a vertical `ScrollView` renders with unbounded height, which
  disables virtualization entirely — the exact opposite of the intent.

## Images in rows

- Give every remote image explicit dimensions (or a flex parent with a known
  size). An image without them lays out at zero and then reflows the row when
  the response arrives.
- Request an image at display size rather than downscaling a full-resolution
  asset on device; decode cost, not network cost, is what drops frames while
  scrolling.
- In Expo projects prefer `expo-image` — it brings caching, transitions and
  placeholder support that the core `Image` leaves to you.

## Text input latency

A `TextInput` driven as a controlled component sends every keystroke to
JavaScript and the resulting `value` back to native. Under load — a list
re-rendering behind the keyboard, an expensive filter — the two directions fight
and characters appear late or out of order.

- Let the input own its text: `defaultValue` plus `onChangeText` writing to a
  ref, and read the ref when the value is actually needed (submit, debounce
  boundary).
- When a controlled value is unavoidable (validation as you type), keep the
  input's render subtree tiny so a keystroke cannot re-render anything
  expensive, and defer the derived work (`useDeferredValue`, or a debounce).
- Do not "fix" input lag by memoizing the parent; the round trip is the problem,
  not the parent's render.

## Animations and gestures

- Animate `transform` and `opacity`. Those compose on the existing layout;
  width, height, margin, padding and flex properties re-run layout every frame.
- Run animations in Reanimated worklets so the frames are produced off the
  JavaScript thread. A JS-driven `Animated` timing loop stops when the JS thread
  is busy — which is exactly when the animation matters.
- Derive dependent animated values with `useDerivedValue` rather than writing
  several shared values from one gesture handler.
- Handle press with a gesture (`Gesture.Tap`) when the press competes with a pan
  or a scroll; a plain `Pressable` inside an active gesture area can miss or
  double-fire.
- Reanimated 4 needs `react-native-worklets` installed (Expo SDK 54+ resolves it
  with `npx expo install react-native-worklets`). A missing worklets package
  fails at runtime with a worklet-context error, not at build time.
- With React Compiler enabled, a shared value read during render is still a
  mutable read the compiler cannot see; keep shared-value access inside worklets
  and `useAnimatedStyle`.

## View hierarchy and flattening

React Native collapses views that add nothing to the rendered output, but a view
that carries a prop the platform must honour (`onLayout`, a background, opacity,
a testID on some platforms, `pointerEvents`) cannot be flattened. Deeply nested
wrapper `View`s inside a recycled row therefore turn into real native views and
cost real layout time. Inspect the actual hierarchy in the platform's view
debugger before adding another wrapper.

## What not to "optimize"

- Do not add `useMemo` / `useCallback` / `React.memo` because a component "looks
  heavy". Profile first; unprofiled memoization adds dependency-array bugs and
  keeps stale values alive. In a React Compiler project it is also redundant.
- Do not report component tree depth or component count as a performance
  finding. They correlate with nothing measurable on their own.
- Do not claim a stale-closure bug without showing the stale read path or a
  repro; it is the most-guessed and least-verified React Native diagnosis.
- Do not tune `FlatList` window props (`windowSize`, `maxToRenderPerBatch`,
  `initialNumToRender`) before the list is virtualized at all. They trade
  blank-cell risk against work per batch and only matter once the structure is
  right.

## Old patterns

<details>
<summary><code>removeClippedSubviews</code> and manual <code>shouldComponentUpdate</code> row guards</summary>

Both predate the current renderer and virtualization defaults.
`removeClippedSubviews` can still help a pathological `FlatList` on Android, but
it is a workaround with clipping artefacts, not a first move — and it does
nothing for a `FlashList`. Reach for the structural fix (virtualize, recycle,
stable identities) first.

</details>

<!-- sources: callstack-rn, vercel-rn-rules, expo-official, rn-docs -->
