---
name: flutter
description: "Develops cross-platform Flutter apps with Dart, widgets and state management."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# flutter

## Scope

Covers Flutter application and Dart package work: widget composition and layout,
the three state-management stacks in real use, navigation and deep links,
testing at every layer, performance, localization, networking and
serialization, Dart 3 language features, analyzer/tooling hygiene, and the
Dart↔native boundary (platform channels, Pigeon, FFI).

Not covered: writing native iOS/Android UI or platform SDK code beyond the
channel boundary — use the `apple` or `android` skill. Other cross-platform
stacks: React Native and Expo belong to the `react-native` skill. Also out of
scope: Flutter web hosting/CI/store release, Firebase and other vendor SDKs,
and game engines (Flame). For visual/UX design decisions or web frontends, use
the `frontend-design` skill instead.

Paths below are relative to this skill's directory.

## Core rules

1. Detect the stack before touching state: read `pubspec.yaml`. `flutter_riverpod` /
   `hooks_riverpod` / `riverpod_annotation` → Riverpod; `flutter_bloc` → Bloc/Cubit;
   neither → `ChangeNotifier` + `ListenableBuilder`. Two state solutions in one app
   means two sources of truth for the same screen.
2. In Riverpod, `StateProvider`, `StateNotifierProvider` and `ChangeNotifierProvider`
   are legacy — they survive only for migration. New code uses `Notifier`/`AsyncNotifier`
   behind `NotifierProvider`/`AsyncNotifierProvider`.
3. Put `ProviderScope` (or the root `BlocProvider`) in `runApp`, not inside `MyApp`:
   inside the app widget, provider state dies on every root rebuild and tests observe a
   different tree than production.
4. Mark every constructor `const` that the analyzer allows, and prefer `Padding`,
   `SizedBox`, `ColoredBox` over `Container` — a const subtree is skipped during rebuild;
   `Container` is rarely const-able.
5. Extract widget classes, never `Widget _buildHeader()` helpers: a method rebuilds with
   its parent, cannot be const, and shows up as an anonymous node in DevTools.
6. Any list that can exceed one screen uses `ListView.builder`/`GridView.builder`/
   `SliverList`. A `Column` (or `ListView(children: [...])`) builds and lays out every
   child up front, even the ones nobody scrolls to.
7. Guard `BuildContext` after every `await`: `if (!context.mounted) return;` before
   `Navigator`, `ScaffoldMessenger`, `Theme.of` and friends. The widget may be gone.
8. No IO, no network calls, no `setState` inside `build()`. `build` runs on every
   dependency change and every frame that invalidates the subtree.
9. Keep decisions out of widgets: formatting and show/hide are fine, anything that
   transforms or decides about data belongs in the notifier/cubit/view model, which never
   sees a `BuildContext`.
10. Model state as an immutable value compared by value (`Equatable`, `freezed`, or a
    sealed hierarchy), and assign new collections (`state = [...state, item]`). In-place
    mutation leaves `==` true and listeners silent.
11. Dispose what you create: controllers and `FocusNode`s in `dispose()`, provider
    subscriptions and timers in `ref.onDispose`, streams in `Bloc.close`.
12. Base layout decisions on constraints (`LayoutBuilder`) or window size
    (`MediaQuery.sizeOf`), never on device type or `orientationOf` — apps run in split
    screen, on foldables and in resizable desktop windows.
13. Finish every change with the gate: `dart format .`, then `flutter analyze` with zero
    issues, then `flutter test`. Analyzer info-level lints count; silence one only with
    `// ignore: <code> — <reason>`.

## Workflows

### add-feature

- [ ] Read `pubspec.yaml` for the state, routing, DI and mocking packages already in use
      (rule 1); follow them instead of introducing a new one.
- [ ] Place files feature-first: `lib/features/<feature>/{data,domain?,ui}/`. Never create
      top-level `blocs/`, `widgets/`, `models/` buckets.
- [ ] Define the immutable state type first (sealed hierarchy, or `AsyncValue<T>` when the
      state is exactly loading/data/error).
- [ ] Write the service (raw API/plugin wrapper), then the repository (single source of
      truth, caching, domain models), then the notifier/cubit/view model.
- [ ] Add a use case only when logic spans repositories, is genuinely complex, or has more
      than one caller.
- [ ] Build the view last: `ConsumerWidget`/`BlocBuilder`/`ListenableBuilder` renders the
      state exhaustively; callbacks dispatch intents.
- [ ] Register the route in the router; register dependencies where the app already does.
- [ ] Write tests for the notifier/repository logic (see `add-tests`).
- [ ] **Gate:** `flutter analyze` reports no issues and `flutter test` passes.

### fix-layout-overflow

- [ ] Read the first exception in the console, not the cascade. `RenderBox was not laid
      out` is a downstream symptom — scroll up to the real constraint violation.
- [ ] Match the message to the fix:
  - `RenderFlex overflowed` → wrap the offending child in `Expanded` (must fit) or
    `Flexible` (may shrink); for text also consider `softWrap`/`overflow`.
  - `Vertical viewport was given unbounded height` → the scrollable sits in a `Column`;
    wrap it in `Expanded`, or give it a height, or switch the parent to `CustomScrollView`.
  - `An InputDecorator ... cannot have an unbounded width` → wrap the field in `Expanded`
    inside the `Row`.
  - `Incorrect use of ParentDataWidget` → `Expanded`/`Flexible` must be a direct child of
    `Row`/`Column`/`Flex`, `Positioned` of `Stack`.
- [ ] If the constraint chain is unclear, run the app and inspect it in DevTools, or set
      `debugPaintSizeEnabled = true` temporarily.
- [ ] Hot reload and resize the window through the small and large breakpoints.
- [ ] **Gate:** no exception in the console and no overflow stripes at either breakpoint.

### add-tests

- [ ] Pick the layer: pure logic and repositories → `test` (unit); one widget or screen →
      `flutter_test` widget test; a full user journey on a device → `integration_test`.
- [ ] Use the project's mocking library — `mocktail` unless `pubspec.yaml` already has
      `mockito` + `build_runner`. Mock at the repository or client boundary, not the
      class under test.
- [ ] With `mocktail`, call `registerFallbackValue` in `setUpAll` for every custom type
      used with `any()`; without it the matcher throws at runtime.
- [ ] Assert on observable behaviour: emitted states, thrown types
      (`throwsA(isA<MyException>())`), rendered widgets. A test that only replays a stub
      cannot fail when the code breaks.
- [ ] For Riverpod, override the dependency provider in a fresh `ProviderContainer` per
      test and `addTearDown(container.dispose)`; never mock a `Notifier` with
      `implements`.
- [ ] **Gate:** `flutter test` (or `dart test` for a pure Dart package) passes, and the
      new test fails when the behaviour under test is broken.

### upgrade-dependencies

- [ ] Run `flutter pub outdated` and read the "Resolvable" column before editing anything.
- [ ] Upgrade within constraints first (`flutter pub upgrade`), then majors one package
      per commit so a regression has one suspect.
- [ ] On a version-solving conflict, run `flutter pub deps` to find who pins the old
      version; prefer bumping that package over a `dependency_overrides` entry, and delete
      any override you add as soon as upstream catches up.
- [ ] Run `dart fix --dry-run`, review, then `dart fix --apply` for mechanical deprecations.
- [ ] **Gate:** `flutter analyze` clean and `flutter test` green on the upgraded lockfile.

### review

- [ ] Establish the diff scope, then read the tests in it first: they state what the author
      believes the code does.
- [ ] Walk the Core rules in order — they are ordered by how often each one is the actual
      defect.
- [ ] Check layer discipline: no `BuildContext` in logic classes, no service calls from a
      widget, no feature reaching into another feature's internals.
- [ ] Check lifecycle: disposal, `context.mounted`, provider scope and `autoDispose`.
- [ ] Check the rebuild surface: missing `const`, whole-object `watch` where a `select`
      belongs, an eager list where a lazy builder belongs.
- [ ] Report using the Output format below; run `flutter analyze` yourself rather than
      guessing which findings the analyzer already covers, and skip those it does.
- [ ] **Gate:** every finding carries `path:line`, a one-line reason, and a concrete fix.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Layers, folders, DI | Structuring a project or feature, or deciding where logic lives | `references/architecture.md` |
| Riverpod | The project depends on any `riverpod` package | `references/state-riverpod.md` |
| Bloc / Cubit | The project depends on `flutter_bloc` | `references/state-bloc.md` |
| Provider / ChangeNotifier | No Riverpod or Bloc; official MVVM baseline | `references/state-provider-changenotifier.md` |
| Routing, deep links | Adding routes, tabs, auth redirects, or app links | `references/navigation.md` |
| Tests | Writing or reviewing unit, widget, integration or E2E tests | `references/testing.md` |
| Widgets and layout | Building UI, adaptive layouts, or debugging constraints | `references/widgets-layout.md` |
| Performance | Jank, dropped frames, slow lists, memory growth | `references/performance.md` |
| Dart 3 language | Patterns, records, sealed classes, primary constructors | `references/dart-language.md` |
| Tooling | Analyzer config, `dart fix`, coverage, pub conflicts | `references/dart-tooling.md` |
| Localization | Adding `.arb` strings, plurals, locale handling | `references/localization.md` |
| JSON and HTTP | Models, parsing, network calls, isolates | `references/json-http.md` |
| Native interop | MethodChannel, EventChannel, Pigeon, FFI/ffigen | `references/platform-channels-ffi.md` |
| Accessibility | Semantics, screen readers, text scaling, contrast | `references/accessibility.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
lib/features/cart/ui/cart_page.dart
  L42 blocking - `ref.read(cartProvider)` in build() reads once and skips rebuilds.
       Use `ref.watch`.
       before: final cart = ref.read(cartProvider);
       after:  final cart = ref.watch(cartProvider);
  L88 important - ScaffoldMessenger.of(context) used after `await` without
       `if (!context.mounted) return;`.
  L15 minor - `EdgeInsets.all(8)` can be const.

lib/features/cart/data/cart_repository.dart
  ✓ pass
```

Severities: `blocking` (crash, data loss, wrong behaviour, legacy API that will be
removed), `important` (rebuild storms, leaks, layer violations), `minor` (const,
naming, dead code). End with a one-line verdict: ship, ship after blocking fixes, or
rework.

## Environment

Flutter SDK on `PATH` (`flutter --version` also reports the bundled Dart). Commands used
by the workflows:

```bash
flutter analyze          # zero issues is the bar; add --fatal-infos in CI
flutter test             # dart test for a pure Dart package
flutter pub outdated     # before any dependency change
dart fix --apply         # mechanical deprecation fixes
dart format .
```

Device-dependent steps (`flutter drive`, `patrol test`, `adb`, `xcrun simctl`) need a
connected device, emulator or simulator; iOS steps additionally need macOS with Xcode.
