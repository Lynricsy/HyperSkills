# Compose performance

Verified against: Kotlin 2.0.20+ with the `org.jetbrains.kotlin.plugin.compose` plugin,
AGP 8.2+ (Baseline Profile Generator module), AGP 9 defaults where noted.

## Contents

- [The three phases](#the-three-phases)
- [Stability, and what strong skipping changed](#stability-and-what-strong-skipping-changed)
- [Reading a Compose compiler report](#reading-a-compose-compiler-report)
- [Fixing unstable types](#fixing-unstable-types)
- [Lazy layouts](#lazy-layouts)
- [Modifier chains](#modifier-chains)
- [derivedStateOf vs snapshotFlow](#derivedstateof-vs-snapshotflow)
- [Measuring: debug lies](#measuring-debug-lies)
- [Baseline Profiles and Macrobenchmark](#baseline-profiles-and-macrobenchmark)
- [R8 for Compose](#r8-for-compose)
- [Triage order](#triage-order)

## The three phases

Compose runs **Composition → Layout → Draw** per frame. A state read during phase N
invalidates phase N and every phase below it. This single fact explains most scroll and
animation jank: the value changes every frame, but it is being read in Composition, so the
whole subtree is rebuilt sixty times a second.

The fix is always the same shape — move the read down a phase by reading it inside a
lambda:

```kotlin
// Composition-phase read: the whole composable restarts per frame.
Box(Modifier.offset(x = dragOffset.dp))
Box(Modifier.alpha(progress.value))

// Layout/Draw-phase read: only layout or draw re-runs.
Box(Modifier.offset { IntOffset(dragOffset.roundToPx(), 0) })
Box(Modifier.graphicsLayer { alpha = progress.value })
Box(Modifier.drawBehind { drawRect(color, alpha = progress.value) })
```

Modifier-phase cheat sheet:

| Modifier | Phase it invalidates | Lambda form available |
|---|---|---|
| `offset(x, y)` | Composition | `offset { IntOffset(...) }` |
| `alpha(f)` | Composition | `graphicsLayer { alpha = f }` |
| `padding(dp)` | Composition | none — use `layout { }` or `offset { }` |
| `background(color)` | Composition | `drawBehind { drawRect(...) }` |
| `graphicsLayer { }` | Layout (block runs in Draw) | itself |
| `drawBehind`, `drawWithCache` | Draw | itself |

`padding` has no lambda overload. An animated inset is therefore expressed as
`Modifier.offset { }` or a custom `Modifier.layout { }`, never as animated `padding`.

When a hot value has to cross a composable boundary, pass `() -> Float` instead of
`Float`. The callee reads it inside its own lambda modifier and the caller never
recomposes the callee.

## Stability, and what strong skipping changed

Strong skipping is the default from Kotlin **2.0.20**. It does two things:

1. Every restartable composable becomes skippable regardless of parameter stability.
   Stable parameters are compared with `equals`, **unstable parameters with `===`**.
2. Every *capturing* lambda literal written inside a `@Composable` function is wrapped in
   `remember(captures) { }`. Capture-less lambdas were already compiler-emitted singletons
   and are not wrapped.

The common misreading is "stability no longer matters". It does, for a concrete reason:
`===` on a freshly allocated `List` is always false, so a composable taking
`List<Article>` that is rebuilt by `map` upstream never skips. Strong skipping made
skipping *possible* everywhere; stable types are what make it *happen*.

Escape hatches, both rare:

- `@DontMemoize` on a lambda whose auto-`remember` you must suppress.
- `@NonSkippableComposable` on a composable that must run every time.

Disabling the mode itself (`composeCompiler { featureFlags.add(ComposeFeatureFlag.StrongSkipping.disabled()) }`)
is a diagnostic step, not a fix. The legacy `enableStrongSkippingMode` property is
deprecated in favour of the feature-flag DSL.

Lambdas written in a **non-composable** scope are not auto-memoized: `LazyListScope.items { }`,
`Modifier.pointerInput { }`, object expressions. Wrap those in `remember` by hand when they
capture something expensive.

## Reading a Compose compiler report

Enable reports for the module, then build the **release** variant:

```kotlin
composeCompiler {
    reportsDestination = layout.buildDirectory.dir("compose_compiler")
    metricsDestination = layout.buildDirectory.dir("compose_compiler")
}
```

`<module>-composables.txt` lists each composable as `restartable skippable fun Foo(...)`.
`<module>-classes.txt` classifies each type as `stable`, `unstable` or `runtime`.

`runtime stable` is **not** a bug. It means the compiler proved stability conditional on
type arguments and emitted a `$stable: Int` field the runtime ANDs against the substituted
argument stabilities. The cost is one field load and a bitwise AND.

The classifications that need action are `unstable` on a class you own, and `restartable`
without `skippable` on a composable you did not annotate `@NonSkippableComposable`.

Why the compiler decides what it decides, in the order it checks:

| Situation | Result |
|---|---|
| Primitive, `String`, function type, `Unit` | stable, immediately |
| `@Stable` / `@Immutable` present | stable, no field analysis |
| Known construct (`Pair`, `Triple`, `Result`, `ImmutableList`, …) | stable in its type arguments |
| Declared in another module | `runtime` via a generated `$stable` field |
| Java type | unstable — final fields look like `var` without Kotlin metadata |
| Interface (`List`, `Set`, your own) | unknown; runtime falls back to `===` |
| Anything else | field-by-field: one `var` or one unstable field ⇒ unstable |

Recursive types (`class Node(val children: List<Node>)`) are conservatively unstable
because the algorithm bails on cycles; `@Immutable` on the class short-circuits that.

## Fixing unstable types

| Cause | Fix |
|---|---|
| `var` property | make it `val`; model change as a new instance |
| `List`/`Set`/`Map` field or parameter | `kotlinx.collections.immutable` `ImmutableList` etc., or `@Immutable` on a type you can guarantee |
| Java or third-party type you cannot edit | add its fully-qualified name to a stability configuration file and wire it with `composeCompiler { stabilityConfigurationFiles.add(...) }` |
| `Flow<T>` parameter | remove it; collect in the caller with `collectAsStateWithLifecycle()` and pass the value |
| Interface-typed parameter | narrow to the concrete stable type where you can |

Two things that look like fixes and are not:

- Wrapping the call site in `Row`/`Column`/`Box`. Those are **inline** composables: they
  are not restartable or skippable to begin with, so the wrap creates a new restart scope
  without addressing the unstable parameter.
- Annotating `@Stable` on a class that still mutates. That is a broken contract, and the
  symptom is a missing recomposition — a correctness bug, worse than the slow frame it was
  meant to remove.

Prefer `@Immutable` over `@Stable` when the type genuinely never changes: `@Stable` only
promises change notification, `@Immutable` additionally lets the compiler promote property
reads to static expressions and elide equality probes.

## Lazy layouts

```kotlin
LazyColumn {
    items(
        items = articles,
        key = { it.id },              // stable, unique, not the index
        contentType = { it.kind },    // only for mixed feeds
    ) { article ->
        ArticleRow(article, Modifier.animateItem())
    }
}
```

- **No key** means index identity. On insert, remove or reorder, every position past the
  change point looks like a different item: composition state and scroll restoration are
  lost and `Modifier.animateItem()` has nothing to animate from.
- **An unstable key** is worse than none. `UUID.randomUUID()`, `hashCode()` of a mutable
  type, or the item's list position all change under you and discard the cached composition
  every pass.
- **`contentType`** lets the layout recycle compositions between items of the same kind. In
  a mixed feed without it, every row that scrolls into a slot previously held by another
  type is rebuilt from scratch.
- **Allocation inside the item lambda** — `painterResource`, `BorderStroke`, a formatter —
  compounds at scroll velocity. Hoist it above the `LazyColumn` or `remember` it.
- Prefetch is on by default; only reach for an explicit prefetch strategy when a profile
  shows the default window is too small for your item cost.

An unstable item composable cancels all of the above: the row recomposes on every scroll
tick even with perfect keys.

## Modifier chains

Order is evaluated top-down for layout and inside-out for drawing, which makes the chain
semantic rather than cosmetic:

```kotlin
// The 16dp margin is tappable, and the ripple overflows the visible card.
Modifier.clickable(onClick = onClick).padding(16.dp).background(Color.Red)

// Tap target and background match the visible card; padding is inside it.
Modifier.background(Color.Red).clickable(onClick = onClick).padding(16.dp)
```

- `background` before `padding` paints the outer bounds; after `padding` it paints only the
  inner bounds.
- `clip` must come before `background` for the background to be clipped; a `clip` after it
  affects children only.
- `graphicsLayer` wraps only what is **below** it in the chain.
- `size` after `padding` sizes the inner content; `padding` after `size` shrinks it.

Hoisting a shared `Modifier` chain into a `val` is usually not a win — modifier factories
are cheap and the hoist costs a comparison — unless the chain is long and the call site is
inside a hot item lambda.

## derivedStateOf vs snapshotFlow

`derivedStateOf` earns its snapshot subscription only when the **input changes far more
often than the output**:

```kotlin
// Good: index changes per scrolled item, the boolean flips twice.
val showFab by remember { derivedStateOf { listState.firstVisibleItemIndex > 5 } }

// Pure overhead: both change at the same rate.
val fullName by remember { derivedStateOf { "$first $last" } }   // just compute it
```

The silent bug is capturing a non-snapshot value inside the `remember` block: the captured
`threshold` is frozen at first composition and later values are ignored forever. Either
make it state, or pass it as a `remember` key.

When the goal is a *side effect* rather than a value, use `snapshotFlow` instead —
`derivedStateOf` has no place to run a side effect, and a side effect in a composable body
runs on every recomposition:

```kotlin
LaunchedEffect(listState) {
    snapshotFlow { listState.firstVisibleItemIndex }
        .map { it > 5 }
        .distinctUntilChanged()
        .collect { analytics.log(it) }
}
```

For high-frequency flows feeding the UI, `.conflate()` plus `.distinctUntilChanged()`
before collection removes emissions the frame budget cannot use anyway.

## Measuring: debug lies

Four mechanisms make a debug build unrepresentative: Live Literals wraps every constant in
a getter, the code runs without R8 optimisation, no Baseline Profile is applied, and
Layout Inspector counts are sampled approximations. Consequences:

- Compiler reports read from a debug build show false-positive unstable parameters.
- Layout Inspector recomposition counts can double or halve in release.
- A Macrobenchmark against a debug target under `CompilationMode.None` measures JIT warmup,
  not your app.

Every performance number you report carries its provenance: device, variant, compilation
mode, iteration count. A number without them cannot be reviewed or reproduced.

Use the **skip count**, not the recompose count, as the health metric: a composable that
recomposes often but skips almost always is fine.

## Baseline Profiles and Macrobenchmark

Compose ships unbundled from the platform, so no version of Android AOT-compiles it for
you. A Baseline Profile ships the compilation hint list inside the APK; the published
gains are roughly 30% faster cold start and 40% smoother first scroll on the journeys that
were profiled.

Generation and measurement are two separate tests in a `:baselineprofile` module (Android
Studio scaffolds it via **New Module → Baseline Profile Generator**, AGP 8.2+):

```kotlin
@get:Rule val rule = BaselineProfileRule()

@Test fun startupAndScroll() = rule.collect(packageName = TARGET) {
    pressHome(); startActivityAndWait()
    device.findObject(By.res("feed")).fling(Direction.DOWN)
}
```

```kotlin
@get:Rule val benchmark = MacrobenchmarkRule()

@Test fun startup() = benchmark.measureRepeated(
    packageName = TARGET,
    metrics = listOf(StartupTimingMetric(), FrameTimingMetric()),
    compilationMode = CompilationMode.Partial(BaselineProfileMode.Require),
    startupMode = StartupMode.COLD,
    iterations = 10,
) { pressHome(); startActivityAndWait() }
```

`BaselineProfileMode.Require` fails the run if the profile was not actually applied, which
is what makes the measurement trustworthy. Verify the profile shipped by checking for
`assets/dexopt/baseline.prof` in the APK.

Report time-to-fully-drawn accurately with `ReportDrawn`, `ReportDrawnWhen` or
`ReportDrawnAfter` from `androidx.activity.compose`; without them, "fully drawn" is the
first frame, which for a list screen is the skeleton, not the content.

## R8 for Compose

R8 is not optional for a Compose app: lambda grouping, `sourceInformation` stripping,
composable-argument constant folding and `ComposerImpl` devirtualisation only run when
optimisation is on.

- Use `getDefaultProguardFile("proguard-android-optimize.txt")`. From AGP 9 the
  non-optimize file is rejected outright, because it carries `-dontoptimize`.
- Do not add wildcard keeps for `androidx.compose.**`. Compose ships correct consumer rules;
  a blanket keep undoes every optimisation above and bloats `classes.dex`.
- Do not blanket-keep `kotlin.Metadata`. Find the reflective consumer
  (kotlinx.serialization, Moshi, Gson, Hilt) and keep narrowly for that consumer.
- Do not use `-dontobfuscate` "for readable stacks". Ship with R8 on and deobfuscate with
  `retrace` and `mapping.txt`; otherwise the variant you measured is not the variant you
  shipped.
- Under AGP 9, `android.r8.strictFullModeForKeepRules` defaults on: `-keep class A` no
  longer implies `-keep class A { <init>(); }`. Add the constructor explicitly where
  reflection needs it.

## Triage order

1. Release build, R8 on, Baseline Profile applied — otherwise stop and fix that first.
2. Name the symptom: cold start / first scroll / steady scroll / animation.
3. Code review for wrong-phase reads, missing keys, allocation in item lambdas.
4. Compose compiler reports for unstable types.
5. Layout Inspector recomposition counts and Argument Change Reasons to confirm the
   suspect; never to draw the conclusion.
6. Perfetto trace when the frame timeline is needed (which thread, which slice).
7. Macrobenchmark before and after to prove the delta.

<!-- sources: skydoves-compose-perf, android-official, aldefy-compose, android-docs -->
