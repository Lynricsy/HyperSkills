# Testing: unit, widget, integration, E2E

## Contents

- [Pick the layer](#pick-the-layer)
- [Does this test earn its place](#does-this-test-earn-its-place)
- [Unit tests](#unit-tests)
- [Mocking: mocktail and mockito](#mocking-mocktail-and-mockito)
- [Widget tests](#widget-tests)
- [Testing state holders](#testing-state-holders)
- [Golden tests](#golden-tests)
- [Integration tests](#integration-tests)
- [Patrol for native dialogs](#patrol-for-native-dialogs)
- [Coverage](#coverage)
- [Failure catalogue](#failure-catalogue)

## Pick the layer

| Target | Kind | Tools | Command |
|---|---|---|---|
| Pure Dart logic, repositories, notifiers/blocs | unit | `test`, `bloc_test`, `mocktail` | `flutter test` / `dart test` |
| One widget or screen | widget | `flutter_test`, `WidgetTester` | `flutter test` |
| Pixel output of a widget | golden | `matchesGoldenFile` | `flutter test --update-goldens` to record |
| A user journey on a real device | integration | `integration_test` | `flutter test integration_test` or `flutter drive` |
| A journey crossing native permission dialogs | E2E | `patrol` | `patrol test` |

Default to unit tests for logic and widget tests for rendering. Integration tests
are slow and flaky by nature — reserve them for the two or three journeys whose
failure would ship a dead app.

## Does this test earn its place

Ask: *can this fail if the production code breaks?* A test that stubs a method and
then asserts the stub's return value proves only that the mocking library works.

```dart
// worthless: asserts the mock
when(() => repo.getUser()).thenAnswer((_) async => user);
expect(await repo.getUser(), user);

// useful: asserts what the notifier does with the repository's answer
when(() => repo.getUser()).thenThrow(NetworkException());
await container.read(profileProvider.notifier).load();
expect(container.read(profileProvider), isA<AsyncError>());
```

Test observable behaviour: emitted states, thrown types, rendered widgets, calls
that must reach a boundary. Do not test private helpers, framework behaviour, or
generated `copyWith`.

## Unit tests

```dart
void main() {
  group('CartTotal', () {
    late Cart cart;
    setUp(() => cart = Cart());

    test('sums line items including tax', () { ... });
    test('throws on a negative quantity', () {
      expect(() => cart.add(item, quantity: -1), throwsA(isA<ArgumentError>()));
    });
  });
}
```

- One `group` per class under test; name tests after the behaviour
  ("emits failure when the API returns 500").
- Use expressive matchers: `isEmpty`, `throwsA(isA<T>())`, `completion(...)`,
  `emitsInOrder([...])`. `expect(result != null, true)` hides what failed.
- `setUp` builds fresh objects per test; `tearDown` closes streams and controllers.
- Mirror `lib/` under `test/`, one `_test.dart` per source file.

## Mocking: mocktail and mockito

Default to **mocktail** — no code generation, so no `build_runner` step in CI and
no stale `.mocks.dart`. Use **mockito** only when the project already has it, or
when you need generated stubs for a large API surface.

```dart
import 'package:mocktail/mocktail.dart';

class MockWeatherApi extends Mock implements WeatherApi {}
class FakeUri extends Fake implements Uri {}

void main() {
  setUpAll(() => registerFallbackValue(FakeUri()));   // needed for any() on Uri

  late MockWeatherApi api;
  setUp(() => api = MockWeatherApi());

  test('maps a 500 to WeatherException', () {
    when(() => api.get(any())).thenAnswer((_) async => Response('', 500));
    expect(() => WeatherRepository(api).fetch('Berlin'),
        throwsA(isA<WeatherException>()));
  });
}
```

- `registerFallbackValue` is required in `setUpAll` for every non-primitive type
  used with `any()`, `captureAny()` or `any(named:)`; without it mocktail throws
  at match time with a message naming the type.
- `thenAnswer` for futures and streams, `thenReturn` for plain values,
  `thenThrow` for errors.
- Prefer a real object, then a `Fake`, then a `Mock`. Reach for `Mock` only when
  the test needs `verify(...)` on interactions.
- Never add `@override` implementations to a class extending `Mock`.
- Mock at the boundary the class under test talks to (repository, http client),
  not at the class under test itself.
- mockito equivalent: annotate with `@GenerateNiceMocks([MockSpec<WeatherApi>()])`
  and run `dart run build_runner build --delete-conflicting-outputs`. Regenerate
  after every signature change or the mocks silently drift.
- For HTTP specifically, `package:http/testing.dart`'s `MockClient` handler is a
  legitimate alternative to a mock class when no interaction verification is
  needed.

## Widget tests

```dart
testWidgets('shows the error message and a retry button', (tester) async {
  await tester.pumpWidget(
    MaterialApp(home: ProfileView(viewModel: FailingViewModel())),
  );

  await tester.pump();                       // one frame
  expect(find.text('Network unavailable'), findsOneWidget);

  await tester.tap(find.byKey(const Key('retry')));
  await tester.pumpAndSettle();              // run animations to completion
  expect(find.byType(CircularProgressIndicator), findsOneWidget);
});
```

- Wrap the widget under test in `MaterialApp` (or at least `Directionality` +
  `MediaQuery`) or inherited lookups throw.
- `pump()` advances one frame; `pumpAndSettle()` pumps until no frame is
  scheduled — it times out on an infinite animation, which is a real finding, not
  a test bug.
- Prefer `find.byKey` over `find.text` for anything localised or dynamic; add
  `Key`s in the production widget for exactly the elements tests touch.
- Off-screen items in a lazy list are not built: `await tester.scrollUntilVisible(
  itemFinder, 500, scrollable: find.byType(Scrollable))` first.
- Set a deterministic surface when layout matters:
  `tester.view.physicalSize = const Size(1080, 1920);` with
  `addTearDown(tester.view.reset)`.
- Test text scaling with `MediaQuery(data: MediaQueryData(textScaler: TextScaler.linear(2)), ...)`.

## Testing state holders

- **Riverpod**: fresh `ProviderContainer(overrides: [repoProvider.overrideWithValue(mock)])`
  per test, `addTearDown(container.dispose)`, `container.listen` for autoDispose
  providers. Override dependencies, not the notifier.
- **Bloc**: `blocTest<C, S>(build:, act:, expect:)` from `bloc_test`; `whenListen`
  to drive a mocked cubit in a widget test.
- **ChangeNotifier**: call the method, then assert getters, or attach a listener
  and count notifications when the number of rebuilds is the contract.

## Golden tests

```dart
await expectLater(find.byType(PriceTag), matchesGoldenFile('goldens/price_tag.png'));
```

Goldens are font- and platform-sensitive: run them on one platform (usually CI
Linux) or they will fail on somebody's machine forever. Regenerate deliberately
with `flutter test --update-goldens` and review the image diff in the PR.

## Integration tests

```dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('checkout happy path', (tester) async {
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    ...
  });
}
```

- Files live in `integration_test/`, dependencies are
  `dev:integration_test:{"sdk":"flutter"}` and `dev:flutter_test:{"sdk":"flutter"}`.
- Run with `flutter test integration_test` on an attached device, or via
  `flutter drive --driver=test_driver/integration_test.dart --target=integration_test/app_test.dart`
  when you need a host-side driver (web with `chromedriver`, or timeline capture).
- Prefer waiting on a condition (`tester.pumpAndSettle`, a finder becoming
  non-empty) over `Future.delayed`; fixed sleeps are what make suites flaky.

## Patrol for native dialogs

`patrol` drives permission sheets, notifications and WebViews that `WidgetTester`
cannot reach:

```dart
patrolTest('grants location permission', ($) async {
  await $.pumpWidgetAndSettle(const MyApp());
  await $('Enable location').tap();
  await $.native.grantPermissionWhenInUse();
  expect($('Nearby stores'), findsOneWidget);
});
```

Run with `patrol test`; it needs its own CLI (`dart pub global activate patrol_cli`)
and a device. Keep patrol tests to journeys that genuinely cross the native
boundary.

## Coverage

```bash
flutter test --coverage                       # writes coverage/lcov.info
dart run coverage:format_coverage ...         # pure Dart packages
genhtml coverage/lcov.info -o coverage/html   # optional local report
```

Exclude generated files (`*.g.dart`, `*.freezed.dart`) from the report rather than
writing tests for them. Coverage is a map of untested areas, not a target.

## Failure catalogue

| Symptom | Cause |
|---|---|
| `type 'Null' is not a subtype of ...` in a mocktail test | missing `registerFallbackValue` or an unstubbed method |
| `pumpAndSettle timed out` | an animation that never ends (indeterminate progress indicator) |
| Widget not found | it is off-screen in a lazy list, or behind an unpumped frame |
| `No MediaQuery widget ancestor` | pumped the widget without `MaterialApp` |
| Test passes alone, fails in the suite | shared container/singleton state; build fresh objects in `setUp` |
| Golden fails only on CI | font or platform difference; pin goldens to one platform |
| mockito mocks out of date | `build_runner` not re-run after a signature change |

<!-- sources: flutter-official, dart-official, evanca-rules, harish-flutter-tester, sgruhier-flutter -->
