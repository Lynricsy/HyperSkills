# Compose state and side effects

## Contents

- [State ownership](#state-ownership)
- [remember and its keys](#remember-and-its-keys)
- [Choosing an effect](#choosing-an-effect)
- [Effect keys are the whole game](#effect-keys-are-the-whole-game)
- [Collecting flows](#collecting-flows)
- [CompositionLocal](#compositionlocal)
- [Old patterns](#old-patterns)

## State ownership

State lives at the lowest common ancestor of everything that reads or writes it. A
composable that owns no state takes the value plus lambdas and can be previewed, tested
and reused; a composable that reaches for a `ViewModel` can do none of those things.

The standard shape is a stateful screen wrapper around a stateless content composable:

```kotlin
@Composable
fun NewsRoute(viewModel: NewsViewModel = hiltViewModel(), onOpen: (String) -> Unit) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    NewsScreen(state = state, onRefresh = viewModel::refresh, onOpen = onOpen)
}

@Composable
fun NewsScreen(state: NewsUiState, onRefresh: () -> Unit, onOpen: (String) -> Unit) { … }
```

Three rules follow from this:

- Never pass a `ViewModel` further down than the route composable.
- Never pass a `Flow` into a composable at all: it is unstable, so the callee can never
  skip, and collecting it inside a leaf detaches the collection from the screen's
  lifecycle.
- UI-only state (expanded/collapsed, text field contents, scroll position) belongs in the
  composable; anything the ViewModel must survive a configuration change for belongs in
  the ViewModel.

Use `rememberSaveable` for UI state that must survive process death or configuration
change but does not belong in the ViewModel — a selected tab, a scroll anchor. Types that
are not `Parcelable`/`Serializable` need an explicit `Saver`.

Prefer `mutableIntStateOf`/`mutableLongStateOf`/`mutableFloatStateOf` over
`mutableStateOf(0)`: the generic version autoboxes on every write.

## remember and its keys

`remember(key1, key2) { … }` recomputes when any key changes by `equals`. Two failure
modes dominate:

- **Missing key**: an expensive object built from a parameter is remembered with no key,
  so it keeps the value from first composition after the parameter changes.
- **Unstable key**: keying on a freshly allocated object recomputes every pass, which is
  strictly worse than not remembering at all.

`remember` is not a cache across navigation. When the composable leaves the composition
the value is gone; anything that must survive belongs in `rememberSaveable`, the
ViewModel, or a repository.

## Choosing an effect

| Need | API | Runs on |
|---|---|---|
| Suspend work tied to composition | `LaunchedEffect(keys)` | Composition scope, cancelled on key change or leave |
| Suspend work started by a callback | `rememberCoroutineScope()` | Scope survives recomposition, cancelled on leave |
| Register/unregister a non-Compose listener | `DisposableEffect(keys)` | Enter and leave, with `onDispose` |
| Publish Compose state to a non-Compose object | `SideEffect { }` | After every successful composition |
| Turn a callback or suspend source into state | `produceState(initial, keys)` | Composition scope |
| React to snapshot state changes as a stream | `snapshotFlow { }` inside a `LaunchedEffect` | Composition scope |
| Read the newest value from a long-lived effect | `rememberUpdatedState(value)` | — |

Never launch a coroutine directly in a composable body, and never perform IO, logging or
navigation there. `build`-time code runs on every recomposition and at unpredictable
times.

`rememberUpdatedState` exists for one situation: a `LaunchedEffect(Unit)` that must not
restart but has to see the latest lambda or value. Without it the effect captures the
first value forever; with a real key instead, the effect restarts and loses its progress.

```kotlin
@Composable
fun AutoDismiss(onTimeout: () -> Unit) {
    val currentOnTimeout by rememberUpdatedState(onTimeout)
    LaunchedEffect(Unit) {          // must not restart when the lambda identity changes
        delay(5_000)
        currentOnTimeout()
    }
}
```

## Effect keys are the whole game

`LaunchedEffect(Unit)` means "once per entry into the composition". It is right for a
one-shot animation or a timer, and wrong for anything that depends on a parameter:

```kotlin
// Wrong: the first userId is loaded forever.
LaunchedEffect(Unit) { viewModel.load(userId) }

// Right: relaunches (and cancels the previous load) when userId changes.
LaunchedEffect(userId) { viewModel.load(userId) }
```

`DisposableEffect` must always end in `onDispose`, and its keys must include everything
the registration depends on — most commonly the `LifecycleOwner`:

```kotlin
DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event -> … }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}
```

Cancellation is cooperative: a `LaunchedEffect` body that never suspends cannot be
cancelled. Put a `yield()` or a suspending call in long loops.

## Collecting flows

`collectAsStateWithLifecycle()` (from `androidx.lifecycle:lifecycle-runtime-compose`) is
the default. Plain `collectAsState()` keeps collecting while the app is backgrounded,
which wastes CPU and battery and can deliver updates into a stopped UI.

`minActiveState` defaults to `STARTED`. Lower it to `CREATED` only for something that must
keep updating while off-screen — a widget-backing flow, a foreground-service progress
readout — and note the battery cost.

On the producing side, `stateIn(scope, SharingStarted.WhileSubscribed(5_000), initial)` is
the standard shape: the 5 second grace period keeps the upstream alive across a rotation
instead of restarting a database query. It also means the upstream does not run until
something collects, which any test of that state has to account for.

In the View system the equivalent is:

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect(::render)
    }
}
```

## CompositionLocal

A `CompositionLocal` is for values that a whole subtree needs and almost nobody passes
explicitly: theme, density, layout direction, `LocalContext`. It is not a dependency
injection container — an implicit dependency is invisible at the call site and impossible
to see in a preview or a test.

- `compositionLocalOf` when the value changes and readers must recompose.
- `staticCompositionLocalOf` when it effectively never changes; reads are cheaper, but any
  change recomposes the entire subtree under the provider.
- Always give a default that fails loudly (`error("No X provided")`) rather than a silent
  placeholder.
- Never store mutable state in one; provide immutable snapshots.

## Old patterns

<details>
<summary>Superseded APIs still common in existing code</summary>

- `collectAsState()` → `collectAsStateWithLifecycle()`.
- `mutableStateOf(0)` for primitives → `mutableIntStateOf(0)` and friends.
- `Modifier.composed { }` → the `Modifier.Node` API, which does not allocate per call site
  and participates in modifier reuse.
- `LazyColumn { items { Modifier.animateItemPlacement() } }` → `Modifier.animateItem()`.
- `accompanist-systemuicontroller` → `enableEdgeToEdge()`.
- `accompanist-pager` → `HorizontalPager`/`VerticalPager`; `accompanist-flowlayout` →
  `FlowRow`/`FlowColumn`; `accompanist-swiperefresh` → `PullToRefreshBox`.
- String-based navigation routes → `@Serializable` type-safe routes.

</details>

<!-- sources: aldefy-compose, skydoves-compose-perf, silvermoon-android, android-official, android-docs -->
