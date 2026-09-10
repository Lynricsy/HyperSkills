# Testing

## Contents

- [Picking the layer and the source set](#picking-the-layer-and-the-source-set)
- [Auditing an existing setup](#auditing-an-existing-setup)
- [Unit tests](#unit-tests)
- [Coroutines and flows under test](#coroutines-and-flows-under-test)
- [Room and other on-device engines](#room-and-other-on-device-engines)
- [Compose behaviour tests](#compose-behaviour-tests)
- [Screenshot tests](#screenshot-tests)
- [Navigation and end-to-end](#navigation-and-end-to-end)
- [Fakes, and when a mock is unavoidable](#fakes-and-when-a-mock-is-unavoidable)

## Picking the layer and the source set

| What you are testing | Source set | Runner |
|---|---|---|
| ViewModel, repository, use case, mapper, pure Kotlin | `test` | JUnit, plus Robolectric only if an Android type leaks in |
| Compose or Espresso behaviour of a screen | `test` | Robolectric |
| Room DAO and anything that hits SQLite | `androidTest` | instrumented, in-memory database |
| System UI, notifications, permissions dialogs, edge-to-edge rendering, picture-in-picture | `androidTest` | instrumented + UI Automator |
| Screenshots on the host | `test` | Compose Preview Screenshot Testing (Layoutlib) or Roborazzi |
| Screenshots on a device | `androidTest` | Dropshots |
| Whole user journeys (≈5% of the suite) | `androidTest` | Compose test APIs or Espresso, UI Automator for system surfaces |

The default is `test`: it runs in seconds without a device and can be run in bulk. Move a
test to `androidTest` only when it needs something the host cannot provide — most often
the device's own SQLite engine or real rendering.

Do not write tests for Activities, layout-only composables or DI wiring. They assert the
framework's behaviour, not yours.

## Auditing an existing setup

Before adding anything, read `gradle/libs.versions.toml` and the module build files and
answer: which DI container, which unit-test framework, which mocking library (if any),
whether Robolectric is present and in which of its three roles (platform fakes, running
UI tests off-device, screenshot testing via Roborazzi), whether the app is Compose, Views
or hybrid, and which screenshot tool is already wired. Adopt what is there; introducing a
second mocking library or a second screenshot tool doubles the maintenance for no gain.

## Unit tests

Test observable behaviour, not implementation: emitted states, returned values, thrown
types, what the fake was asked for. A test that only replays its own stub cannot fail when
the code breaks.

```kotlin
@Test
fun `adds bookmark and surfaces it in state`() = runTest {
    val repo = FakeBookmarksRepository()
    val vm = BookmarksViewModel(repo)
    backgroundScope.launch { vm.uiState.collect {} }   // see below

    vm.addBookmark("https://example.com", "Example")
    advanceUntilIdle()

    assertThat(vm.uiState.value.items).hasSize(1)
}
```

## Coroutines and flows under test

Two failure modes account for most "the test passes but the code is wrong" reports:

1. **`viewModelScope` runs on `Dispatchers.Main`**, which does not exist off-device.
   Install a test dispatcher once, in a JUnit rule:

   ```kotlin
   class MainDispatcherRule(
       private val dispatcher: TestDispatcher = UnconfinedTestDispatcher(),
   ) : TestWatcher() {
       override fun starting(d: Description) = Dispatchers.setMain(dispatcher)
       override fun finished(d: Description) = Dispatchers.resetMain()
   }
   ```

2. **`stateIn(SharingStarted.WhileSubscribed(…))` produces nothing until collected.**
   Without a collector the upstream never starts and every assertion sees `initialValue` —
   a test that passes for the wrong reason. Start collection first
   (`backgroundScope.launch { state.collect {} }`) or use Turbine's `test { }`, which
   subscribes for you.

Inject dispatchers rather than referencing `Dispatchers.IO` inside a class, so a test can
substitute the same `TestDispatcher` it controls with `advanceUntilIdle()` and
`advanceTimeBy()`.

## Room and other on-device engines

Room DAO tests belong in `androidTest` against an in-memory database, because the SQLite
version and build flags on device differ from the host JVM's:

```kotlin
val db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java)
    .allowMainThreadQueries()      // test-only; never in production code
    .build()
```

Also test the migrations themselves — `MigrationTestHelper` with exported schemas — because
a broken migration corrupts user data and cannot be hotfixed retroactively.

## Compose behaviour tests

```kotlin
@get:Rule val rule = createAndroidComposeRule<ComponentActivity>()
```

`ComponentActivity` rather than a bare `createComposeRule()` gives access to resources and
the activity lifecycle, which is what state-restoration assertions need.

- Match by semantics first (`onNodeWithText`, `onNodeWithContentDescription`, role, state
  descriptions). Fall back to `testTag` only when a single element needs more than three
  matchers — a tag is invisible to accessibility services and to the user.
- Assert state restoration explicitly (`rule.activityRule.scenario.recreate()`); a screen
  that loses its scroll position or text field contents on rotation is a real bug that
  unit tests never see.
- Simulate window sizes, font scales and dark mode with `DeviceConfigurationOverride`
  rather than parameterising the test runner.
- `waitUntil` with a condition beats `Thread.sleep`; the Compose test clock is idle-driven,
  so an infinite animation makes `waitForIdle` hang — pause the clock in that case.

## Screenshot tests

Screenshots assert appearance, never behaviour. Two levels:

- **Screen level**: nine combinations of compact/medium/expanded width (400, 610, 900 dp)
  and height (400, 500, 1000 dp), plus one 400×500 shot per alternative theme and one at
  font scale 1.5.
- **Component level**: each component across themes and font scales.

Do capture states that change the layout drastically (loading, empty, error) by injecting
the state through a fake. Do not try to encode interaction sequences in screenshots.

Host-side tools (Compose Preview Screenshot Testing, Roborazzi) are the default because
they need no device. Use a device-based tool (Dropshots) only when the pixels depend on
the real system — edge-to-edge insets, notifications, system UI overlap.

## Navigation and end-to-end

A navigation test suite covers back handling, deep links, and multi-backstack patterns
such as "exit through home". End-to-end tests are expensive and flaky by nature: keep them
at roughly 5% of the suite, covering the journeys that would lose money if broken, and use
UI Automator only where you must leave the app.

For instrumented runs, prefer Gradle-managed devices so CI and local runs use the same
image; a locally attached emulator with a different API level is a classic source of "only
fails in CI".

## Fakes, and when a mock is unavoidable

Default to a fake: extract an interface, keep the real implementation as `Default…`, and
put the fake in the `test`/`androidTest` source set. A fake is real code that can enforce
invariants, so it catches misuse a stub cannot.

Reach for MockK only when the dependency is a final class you do not own with no
extractable interface. Do not install a mocking library "so it's available".

The value of a fake shows in the scenarios it makes cheap: wrong credentials, server down,
malformed payload, permission denied, no disk space, no front camera — each is a fake
returning a different value, and none of them needs a real backend.

<!-- sources: android-official, silvermoon-android, drjacky-ninja, android-docs -->
