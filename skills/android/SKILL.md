---
name: android
description: "Develops native Android apps with Kotlin, Jetpack Compose and Gradle."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# android

## Scope

Covers native Android application and library modules written in Kotlin: language and
coroutine usage, Jetpack Compose and the View system that still surrounds it, layered
architecture and dependency injection, navigation, the Gradle/AGP build, testing at every
layer, runtime performance and app size, platform runtime concerns (lifecycle, insets,
permissions, background work, exported components), and the Kotlin Multiplatform /
Compose Multiplatform boundary an Android module shares code across.

Not covered: Flutter and Dart, including its Android embedding — use the `flutter` skill.
React Native and Expo, including Hermes, Turbo Modules and EAS — use the `react-native`
skill. Native iOS, macOS, Swift and SwiftUI, including the Swift side of a Kotlin
Multiplatform project — use the `apple` skill. Server-side Kotlin on Spring Boot is not
covered here at all; neither are Play Store listing/ASO work, vendor SDK integrations
(Firebase, analytics, payments), and game engines.

Paths below are relative to this skill's directory.

## Core rules

1. Read `settings.gradle.kts`, `gradle/libs.versions.toml` and the target module's build
   file before adding a dependency or changing the build. Everything below depends on
   which AGP, Kotlin and Compose versions the project is actually on.
2. Adopt the stack already in the project — Hilt or Koin, Navigation 2 or Navigation 3,
   MVVM or MVI, Views or Compose. A second DI graph or a second navigation system in one
   app means two sources of truth for the same screen.
3. Actions that originate in the ViewModel (navigate, show a snackbar) become fields of
   the UI state, which the UI consumes and then tells the ViewModel to clear. A
   `SharedFlow(replay = 0)` event bus silently drops those actions across a configuration
   change or process death.
4. Expose `StateFlow`/`Flow`, never the `MutableStateFlow`/`MutableSharedFlow` behind it.
   A public mutable stream lets any caller write state the owner is responsible for.
5. Collect with `collectAsStateWithLifecycle()` in Compose and
   `repeatOnLifecycle(Lifecycle.State.STARTED)` in Views. `collectAsState()` and a bare
   `lifecycleScope.launch { collect() }` keep the upstream running while the app is
   backgrounded.
6. Never pass a `Flow` or a `ViewModel` into a child composable. A `Flow` parameter is
   unstable so the child can never skip, and a `ViewModel` parameter couples a reusable
   component to one screen. Pass the collected value and lambdas.
7. Inject `CoroutineDispatcher`s through the constructor instead of hardcoding
   `Dispatchers.IO` inside a class — a hardcoded dispatcher cannot be replaced in a test.
8. Keep domain and model modules pure Kotlin with no `android.*` import. That is what
   makes them unit-testable off-device and reusable from `commonMain`.
9. Strong skipping (Kotlin 2.0.20+) makes every restartable composable skippable, but
   unstable parameters are compared with `===`, so a freshly allocated `List` still fails
   the skip. Stability work is not obsolete; it changed shape.
10. `@Stable` and `@Immutable` are contracts, not hints. On a class holding a `var` or a
    mutable collection they cause silently missed recompositions — a correctness bug, not
    a slow frame.
11. Give every `items()`/`itemsIndexed()` a stable `key`, and a mixed feed also a
    `contentType`. Index identity discards composition state and scroll restoration on
    insert or remove, and leaves `Modifier.animateItem()` nothing to animate from.
12. Read high-frequency state (scroll offset, drag delta, animation progress) inside a
    lambda modifier — `offset { }`, `graphicsLayer { }`, `drawBehind { }` — not in the
    composable body. A read in Composition invalidates Composition, Layout and Draw; a
    read in the lambda invalidates only Layout or Draw.
13. Reach for `derivedStateOf` only when the input changes far more often than the output.
    Anything it captures that is not snapshot state is frozen at first composition, which
    is a silent staleness bug rather than a visible one.
14. Modifier order is semantics, not style: `.clickable` before `.padding` makes the
    padding tappable, and `.background` after `.padding` paints only the inner bounds.
15. Judge performance only on a release build with R8 enabled. Debug builds add Live
    Literals, which distorts Compose compiler reports and Layout Inspector counts.
16. Base shrinking on `getDefaultProguardFile("proguard-android-optimize.txt")` — AGP 9
    rejects `proguard-android.txt` because it carries `-dontoptimize` — then write keep
    rules narrowly and let libraries ship their own. Under AGP 9's strict full mode,
    `-keep class A` no longer implies `-keep class A { <init>(); }`, so blanket rules
    both over-keep and under-keep at the same time.
17. Declare versions in `gradle/libs.versions.toml` and share build configuration through
    `build-logic` convention plugins. A version literal in a module build file is a
    version that will drift away from every other module.
18. On AGP 9, built-in Kotlin is the default: remove the `org.jetbrains.kotlin.android`
    plugin, drop `kotlin("kapt")` in favour of KSP (or `com.android.legacy-kapt` for
    processors with no KSP support), and replace `applicationVariants` with
    `androidComponents.onVariants`.
19. Prefer KSP over kapt. Check compatibility by looking inside the processor jar for
    `services/com.google.devtools.ksp.processing.SymbolProcessorProvider`; kapt runs a
    full Java stub-generation pass that KSP skips.
20. Put pure logic and Compose/Espresso behaviour tests in `test` running on Robolectric;
    reserve `androidTest` for what genuinely needs a device — Room DAOs (the on-device
    SQLite engine differs), system UI interaction, real rendering and edge-to-edge.
21. Prefer a fake at the repository or data-source boundary over a mocking library. Add
    MockK only when there is no interface you can implement.
22. A `stateIn(SharingStarted.WhileSubscribed(...))` flow produces nothing until something
    collects it — in a test, start collection before asserting or every assertion sees the
    initial value.
23. Migrate XML to Compose one screen or component at a time, keeping `ComposeView` and
    `AndroidView` interop in place. A big-bang rewrite loses behaviour parity with no way
    to bisect the regression.
24. Call `enableEdgeToEdge()` and consume `WindowInsets` in the layout instead of
    hardcoding bar heights; from targetSdk 35 the system draws edge-to-edge whether the
    app is ready or not.
25. Validate every Intent an exported component receives, and never forward a
    caller-supplied Intent or `Uri` extra into `startActivity`/`grantUriPermission`
    unchecked — that is the Intent-redirection privilege escalation.

## Workflows

### add-feature

- [ ] Read the build files (rule 1) and one existing feature module to copy its structure,
      DI style and naming.
- [ ] Place code by layer: `:feature:<name>` owns UI + ViewModel; `:core:data` owns
      repositories and data sources; `:core:model`/`:core:domain` stay pure Kotlin.
- [ ] Define the UI state type first — an immutable `data class` or a sealed hierarchy —
      including any transient message or navigation flag (rule 3).
- [ ] Write the data source, then the repository (single source of truth, main-safe
      `suspend` / `Flow`), then the ViewModel. Add a use case only when logic spans
      repositories or has more than one caller.
- [ ] Build the UI last: a stateless composable that takes state plus lambdas, wrapped by
      a screen-level composable that owns the ViewModel.
- [ ] Register the destination in the navigation graph and the bindings in the DI module.
- [ ] Add tests per `add-tests`.
- [ ] **Gate:** `./gradlew :feature:<name>:assembleDebug :feature:<name>:testDebugUnitTest`
      passes, and `./gradlew lint` reports no new issues.

### fix-compose-jank

- [ ] Reproduce on a **release** build with R8 on and a Baseline Profile installed
      (rule 15). Numbers from a debug build cannot be acted on.
- [ ] Classify the symptom: slow cold start, first-scroll jank, steady-state scroll jank,
      or an animation that stutters. They have different causes and different fixes.
- [ ] For scroll and animation, look for the wrong-phase read first (rule 12), then for
      missing `key`/`contentType` (rule 11), then for allocation inside the item lambda.
- [ ] Generate Compose compiler reports for the module and read
      `*-composables.txt`/`*-classes.txt`; fix the unstable types the reports name
      (rules 9, 10).
- [ ] For cold start, add or regenerate a Baseline Profile with `BaselineProfileRule`, then
      prove the delta with `MacrobenchmarkRule` under
      `CompilationMode.Partial(BaselineProfileMode.Require)`.
- [ ] If the code review is inconclusive, record a Perfetto system trace and work from the
      frame timeline rather than guessing.
- [ ] **Gate:** a Macrobenchmark run on the same device and variant shows the metric moved,
      quoted with device, variant, compilation mode and iteration count.

### upgrade-build

- [ ] Record the current AGP, Gradle, Kotlin, KSP and JDK versions before editing anything.
- [ ] Branch on project shape: a plain Android app follows the AGP 9 steps in rule 18; a
      Kotlin Multiplatform project instead moves to
      `com.android.kotlin.multiplatform.library` and extracts the Android application into
      its own subproject (see `references/kmp-compose-multiplatform.md`).
- [ ] Work one concern per commit: version bump, then plugin removal, then kapt→KSP, then
      DSL/variant-API rewrites, then `gradle.properties` cleanup.
- [ ] Re-check third-party Gradle plugins against the new AGP before blaming your own build
      logic; an incompatible plugin surfaces as a `ClassCastException` on the old DSL types.
- [ ] Remove the temporary opt-out flags (`android.newDsl`, `android.builtInKotlin`, …) once
      the build is green — they are transitional, not configuration.
- [ ] **Gate:** IDE sync succeeds, then `./gradlew help` and `./gradlew build --dry-run`
      succeed, then a real `./gradlew assembleRelease`.

### add-tests

- [ ] Decide the layer and the source set with rule 20 before writing a line.
- [ ] For a ViewModel: swap the main dispatcher for a `TestDispatcher`, use `runTest`, and
      start collecting any `stateIn`-backed state before asserting (rule 22).
- [ ] For a repository or data source: fake the boundary below it (rule 21) and assert the
      request that was actually issued, not just the stubbed reply.
- [ ] For Compose behaviour: launch with `createAndroidComposeRule<ComponentActivity>()`,
      match by semantics first and fall back to `testTag` only when a match needs more than
      three matchers, and cover state restoration.
- [ ] For screenshots: screen-level shots across compact/medium/expanded widths plus a
      font-scale variant; component-level shots per theme. Screenshots assert appearance,
      never behaviour.
- [ ] Skip tests for Activities, layout-only composables and DI wiring — they assert the
      framework, not your code.
- [ ] **Gate:** `./gradlew testDebugUnitTest` passes, the new test fails when the behaviour
      under test is broken, and any `androidTest` addition passes on a Gradle-managed device.

### migrate-xml-to-compose

- [ ] Pick one screen: self-contained, low-traffic, few custom Views, and covered by a test
      or a screenshot you can compare against.
- [ ] Capture the current appearance and behaviour first — a screenshot plus the list of
      interactions is the acceptance criterion.
- [ ] Bridge the theme before the layout: map the XML theme attributes onto a
      `MaterialTheme` so both worlds render the same colours and typography.
- [ ] Replace the layout inside-out with `ComposeView`, or host remaining Views inside
      `AndroidView`; both directions are supported and mixing is the expected steady state.
- [ ] Move state ownership to a ViewModel as you go; do not carry `findViewById` state into
      the composable.
- [ ] Delete the XML, the custom View class and its unused resources only after parity is
      confirmed.
- [ ] **Gate:** screenshot comparison shows parity at the default and 1.5 font scales, and
      the screen's behaviour test still passes.

### review

- [ ] Establish the diff scope, then read its tests first — they state what the author
      believes the code does.
- [ ] Walk the Core rules in order; they are ordered by how often each one is the real
      defect.
- [ ] Check layer discipline: no `android.*` in domain, no data source called from a
      composable, no `Context` held past a lifecycle boundary.
- [ ] Check the recomposition surface: unstable parameters, missing `key`, wrong-phase
      reads, `collectAsState` without lifecycle.
- [ ] Check the build diff separately: version literals outside the catalog, new keep
      rules, a new plugin that duplicates an existing one.
- [ ] Report with the Output format below, and run `./gradlew lint` rather than guessing
      which findings Lint already reports.
- [ ] **Gate:** every finding carries `path:line`, one line of reasoning, and a concrete fix.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Kotlin and coroutines | Writing suspend/Flow code, dispatchers, cancellation, scopes | `references/kotlin-coroutines.md` |
| Architecture and DI | Structuring modules, UI state, ViewModel, Hilt/Koin wiring | `references/architecture.md` |
| Compose state | `remember`, hoisting, side effects, `CompositionLocal`, effect keys | `references/compose-state.md` |
| Compose performance | Jank, recomposition storms, stability reports, Baseline Profiles, R8 | `references/compose-performance.md` |
| Compose UI | Composable API design, theming, adaptive layout, previews, accessibility | `references/compose-ui.md` |
| Navigation | Adding destinations, deep links, back handling, Navigation 2→3 | `references/navigation.md` |
| View system and interop | Touching XML layouts, custom Views, `ComposeView`/`AndroidView` | `references/views-interop.md` |
| Gradle and AGP | Version catalogs, convention plugins, AGP 9 migration, build speed | `references/gradle-build.md` |
| Testing | Choosing a test type, source set, framework, or fixing a flaky test | `references/testing.md` |
| Platform runtime | Lifecycle, insets and edge-to-edge, permissions, WorkManager, Intent security | `references/platform-runtime.md` |
| Kotlin Multiplatform | Sharing code with iOS/desktop, `expect`/`actual`, Compose Multiplatform | `references/kmp-compose-multiplatform.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
feature/news/src/main/kotlin/.../NewsScreen.kt
  L48 blocking - @Immutable on Article, which holds `var readCount` and a MutableList.
       The contract is broken, so edits are not recomposed.
       before: @Immutable data class Article(..., var readCount: Int, val tags: MutableList<String>)
       after:  @Immutable data class Article(..., val readCount: Int, val tags: ImmutableList<String>)
  L71 important - items(articles) has no key; insert/remove discards composition state
       and scroll position. Use items(articles, key = { it.id }).
  L96 minor - .clickable before .padding makes the 16dp margin tappable.

feature/news/src/main/kotlin/.../NewsViewModel.kt
  ✓ pass
```

Severities: `blocking` (crash, data loss, wrong behaviour, removed API), `important`
(recomposition storms, leaks, layer violations, missing lifecycle awareness), `minor`
(naming, ordering, dead code). End with a one-line verdict: ship, ship after blocking
fixes, or rework.

## Environment

JDK 17 or newer and the Android SDK; Gradle comes from the project's wrapper. Commands
used by the workflows:

```bash
./gradlew help                       # cheapest configuration-phase smoke test
./gradlew build --dry-run            # task graph resolves after a build change
./gradlew :app:assembleRelease       # the only variant worth measuring
./gradlew testDebugUnitTest          # local + Robolectric tests
./gradlew lint                       # Android Lint; treat new issues as failures
```

Device-dependent steps (`connectedDebugAndroidTest`, Macrobenchmark, Perfetto capture,
`adb`) need a connected device, an emulator or a Gradle-managed device; Baseline Profile
generation and Macrobenchmark additionally require a release-signed target. Kotlin
Multiplatform iOS targets additionally require macOS with Xcode.
