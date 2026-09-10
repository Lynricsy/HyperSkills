# The View system and Compose interop

## Contents

- [When you still touch Views](#when-you-still-touch-views)
- [Compose inside Views](#compose-inside-views)
- [Views inside Compose](#views-inside-compose)
- [Migrating a screen](#migrating-a-screen)
- [View-system habits worth keeping right](#view-system-habits-worth-keeping-right)

## When you still touch Views

Most real apps are hybrid, and that is a supported steady state, not a debt to pay off
this quarter. You will still work with Views for: `RecyclerView`-heavy legacy screens,
`Fragment`-based navigation, `AppWidget` and notification layouts (RemoteViews — Compose
Glance is a separate API), `MapView`, `WebView`, `SurfaceView`/`TextureView` for camera and
video, and third-party SDKs that only ship a custom `View`.

## Compose inside Views

```kotlin
findViewById<ComposeView>(R.id.compose_root).apply {
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
    setContent { AppTheme { FeatureScreen() } }
}
```

- The composition strategy matters. The default disposes when the `View` detaches from the
  window, which is wrong inside a `Fragment` using `viewLifecycleOwner`, inside a
  `RecyclerView` item, and inside a transition that detaches temporarily.
  `DisposeOnViewTreeLifecycleDestroyed` is the right default for Fragment-hosted content.
- In a `RecyclerView`, a `ComposeView` per item costs a composition per item and loses the
  pooling that made `RecyclerView` fast. Migrate the whole list to `LazyColumn` rather than
  Composifying rows one at a time.
- `ComposeView` needs a `ViewTreeLifecycleOwner`, `ViewTreeSavedStateRegistryOwner` and
  `ViewTreeViewModelStoreOwner`. Inside an Activity or Fragment those are set for you; in
  a custom window, dialog or `RemoteViews`-adjacent context you must set them yourself.

## Views inside Compose

```kotlin
AndroidView(
    factory = { context -> MapView(context) },   // called once
    update = { view -> view.setZoom(zoom) },      // called on every recomposition of a read state
    onRelease = { view -> view.onDestroy() },
    modifier = Modifier.fillMaxSize(),
)
```

- `factory` runs once; `update` runs on first composition and whenever a state it reads
  changes. Constructing anything in `update` allocates per recomposition.
- Use `AndroidViewBinding` when the thing you are embedding is an existing XML layout with
  view binding generated — it saves hand-writing the factory.
- Views that own their own lifecycle (`MapView`, `WebView`, `PlayerView`) need their
  lifecycle callbacks forwarded from a `DisposableEffect` on the current `LifecycleOwner`,
  and their teardown in `onRelease`. Skipping this leaks the renderer process or the map
  surface.
- `AndroidView` measures the wrapped View with the Compose constraints; a legacy View that
  assumes `WRAP_CONTENT` inside an unbounded parent will measure to zero. Give it a size.

## Migrating a screen

Order matters, because each step is independently verifiable:

1. **Pick the candidate**: self-contained, low traffic, few custom Views, already covered
   by a test or a screenshot.
2. **Capture the baseline**: screenshot plus the list of interactions. This is the
   acceptance criterion for the whole migration.
3. **Bridge the theme first**: map the XML theme's colours, typography and shapes onto the
   `MaterialTheme` so both rendering paths look identical while they coexist. A layout
   migration on top of an unmigrated theme produces diffs you cannot attribute.
4. **Move state ownership**: introduce a `ViewModel` exposing UI state before touching the
   layout, and let the XML screen render from it. Do not carry `findViewById` state into
   the composable.
5. **Replace the layout**: swap the root for a `ComposeView`, or migrate inner components
   first and host them in the existing hierarchy. Both directions are supported.
6. **Verify parity**: compare screenshots at the default and 1.5 font scales, re-run the
   behaviour test, check the accessibility tree.
7. **Delete**: only now remove the XML layout, the custom View class and the resources no
   longer referenced.

Layout translation, for orientation: `LinearLayout` → `Column`/`Row`;
`FrameLayout` → `Box`; `ConstraintLayout` → `Column`/`Row`/`Box` first, and the Compose
`ConstraintLayout` only when the constraint graph genuinely does not decompose;
`RecyclerView` → `LazyColumn`/`LazyRow`/`LazyVerticalGrid`; `ScrollView` →
`Modifier.verticalScroll` (a short page) or `LazyColumn` (a long or dynamic one);
`ViewPager2` → `HorizontalPager`; `include` → a composable function; `merge` → nothing,
it was a View-hierarchy-depth workaround Compose does not need.

## View-system habits worth keeping right

While the Views are still there:

- Use view binding, never `findViewById` with a cast, and never Kotlin synthetics (removed).
- In a `Fragment`, null the binding in `onDestroyView` — the `View` outlives nothing, but
  the `Fragment` outlives the `View`, and the retained binding leaks the whole hierarchy.
- Observe with `viewLifecycleOwner`, not the Fragment, and collect inside
  `repeatOnLifecycle(STARTED)`.
- `RecyclerView` needs `DiffUtil`/`ListAdapter` and stable ids; `notifyDataSetChanged()`
  rebinds everything and kills item animations, exactly like a missing `key` in a
  `LazyColumn`.
- Keep the hierarchy shallow; nested weights in `LinearLayout` force double measurement of
  the subtree.

<!-- sources: android-official, aldefy-compose, android-docs -->
