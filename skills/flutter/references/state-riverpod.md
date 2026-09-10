# Riverpod (3.x)

Verified against: riverpod / flutter_riverpod 3.x.

## Contents

- [Provider selection](#provider-selection)
- [Legacy providers and how to replace them](#legacy-providers-and-how-to-replace-them)
- [Writing a Notifier](#writing-a-notifier)
- [Writing an AsyncNotifier](#writing-an-asyncnotifier)
- [ref: watch, read, listen](#ref-watch-read-listen)
- [Lifetime: autoDispose, family, keepAlive](#lifetime-autodispose-family-keepalive)
- [Widget wiring and select](#widget-wiring-and-select)
- [Code generation](#code-generation)
- [Testing](#testing)
- [Failure catalogue](#failure-catalogue)

## Provider selection

| Provider | Use for |
|---|---|
| `Provider` | A dependency (client, repository, use case) or a value derived from others |
| `NotifierProvider` | Mutable state built synchronously, changed by methods |
| `AsyncNotifierProvider` | State loaded asynchronously and then mutated (refresh, retry, optimistic update) |
| `StreamNotifierProvider` | State driven by a stream (live query, socket) |
| `FutureProvider` | A one-shot async read with no methods afterwards |
| `StreamProvider` | A stream with no methods afterwards |

## Legacy providers and how to replace them

`StateProvider`, `StateNotifierProvider` and `ChangeNotifierProvider` are legacy in
Riverpod 3 [official]. They still compile so that old code can migrate, but new
code does not use them, and an example that uses them is an example written for
Riverpod 1.x.

```dart
// legacy
class TodoNotifier extends StateNotifier<List<Todo>> {
  TodoNotifier(this._api) : super([]);
  final TodoApi _api;
}
final todoProvider = StateNotifierProvider<TodoNotifier, List<Todo>>(
  (ref) => TodoNotifier(ref.watch(todoApiProvider)),
);

// current
class TodoNotifier extends Notifier<List<Todo>> {
  @override
  List<Todo> build() => const [];

  TodoApi get _api => ref.read(todoApiProvider);

  Future<void> load() async => state = await _api.fetchAll();
}
final todoProvider = NotifierProvider<TodoNotifier, List<Todo>>(TodoNotifier.new);
```

Migration mapping:

| Legacy | Replacement |
|---|---|
| `StateNotifier<T>` + `StateNotifierProvider` | `Notifier<T>` + `NotifierProvider`; move constructor work into `build()` |
| `StateProvider<T>` | `NotifierProvider` with a `set`/`update` method, so the mutation has a name |
| `ChangeNotifierProvider` | `NotifierProvider` with an immutable state, or keep the `ChangeNotifier` and expose it through a plain `Provider` while migrating |
| Constructor dependencies | `ref.watch`/`ref.read` inside `build()` — the notifier has `ref` directly |

## Writing a Notifier

```dart
sealed class AuthState {
  const AuthState();
}
final class AuthInitial extends AuthState { const AuthInitial(); }
final class AuthLoading extends AuthState { const AuthLoading(); }
final class AuthSignedIn extends AuthState {
  const AuthSignedIn(this.user);
  final User user;
}
final class AuthFailed extends AuthState {
  const AuthFailed(this.message);
  final String message;
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthInitial();

  Future<void> signIn(String email, String password) async {
    state = const AuthLoading();
    try {
      state = AuthSignedIn(await ref.read(authRepositoryProvider).signIn(email, password));
    } on AuthException catch (e) {
      state = AuthFailed(e.message);
    }
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);
```

`build()` returns the initial value and is re-run whenever a watched dependency
changes. Riverpod skips notifying listeners when the new state `==` the old one,
so give state classes value equality (`Equatable`, `freezed`, or hand-written
`==`) — otherwise identical rebuilds still propagate.

## Writing an AsyncNotifier

Use `AsyncNotifier<T>` when the state is exactly loading / data / error; the
`AsyncValue<T>` wrapper already models the three cases, so do not hand-roll a
sealed hierarchy for them.

```dart
class ProfileNotifier extends AsyncNotifier<User> {
  @override
  Future<User> build() => ref.watch(profileRepositoryProvider).fetch();

  Future<void> refresh() async {
    ref.invalidateSelf();
    await future;                       // `future` re-runs build() and awaits it
  }

  Future<void> rename(String name) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(profileRepositoryProvider).rename(name);
      return state.requireValue.copyWith(name: name);
    });
  }
}
```

- Throwing inside `build()` is how the state becomes `AsyncError`; there is no
  separate error state to construct.
- `AsyncValue.guard` is the mutation-time equivalent — it captures the throw
  instead of letting it escape the callback.
- `ref.watch` inside `build()`, so the async state reloads when its inputs change.

## ref: watch, read, listen

| Call | Where | Purpose |
|---|---|---|
| `ref.watch` | `build()` of a widget, provider or notifier | react to changes |
| `ref.read` | callbacks, intent methods | one-shot access |
| `ref.listen` | `build()` of a widget | side effects: snackbar, navigation, dialog |
| `ref.onDispose` | provider/notifier body | cancel timers, subscriptions |

- Never `ref.watch` inside a callback or a notifier method: it re-subscribes on
  every invocation and buys nothing.
- Never `ref.read` something whose changes should rebuild the widget. Reading to
  "avoid rebuilds" is a `select` problem, not a `read` problem.
- Never call `ref.listen` from inside a notifier to navigate — navigation is the
  widget's job.
- After an `await` inside a widget callback, check `context.mounted` before using
  `context`, and be aware the provider may have been disposed.

## Lifetime: autoDispose, family, keepAlive

- Hand-written providers are kept alive by default; add `.autoDispose` for
  screen-scoped state so it clears when the last listener unmounts. Code-generated
  providers are auto-disposed by default; opt out with `@Riverpod(keepAlive: true)`.
- App-scoped dependencies (http client, repositories) stay alive; screen state
  usually should not.
- Use `.family` for state parameterised by an id or page rather than threading the
  argument through every method. Family arguments need value equality — records or
  const collections, never a fresh `List`/`Map` literal per build.
- `ref.invalidate(p)` destroys and lazily rebuilds; `ref.refresh(p)` does the same
  and returns the new value — use the return value or the call is pointless.

## Widget wiring and select

```dart
void main() => runApp(const ProviderScope(child: MyApp()));   // not inside MyApp
```

```dart
class AuthPage extends ConsumerWidget {
  const AuthPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen(authProvider, (previous, next) {
      if (next is AuthFailed) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(next.message)));
      }
    });

    return switch (ref.watch(authProvider)) {
      AuthInitial() || AuthLoading() => const Center(child: CircularProgressIndicator()),
      AuthSignedIn(:final user) => Text('Signed in as ${user.email}'),
      AuthFailed() => const _RetryButton(),
    };
  }
}
```

`select` only pays off in the widget that would otherwise rebuild. If the same
widget also watches the provider unqualified, it rebuilds anyway; push the narrow
watch down into a small leaf widget.

```dart
final email = ref.watch(profileProvider.select((v) => v.value?.email));
```

## Testing

```dart
class MockAuthRepository extends Mock implements AuthRepository {}

ProviderContainer makeContainer(AuthRepository repo) {
  final container = ProviderContainer(
    overrides: [authRepositoryProvider.overrideWithValue(repo)],
  );
  addTearDown(container.dispose);
  return container;
}
```

- One fresh container per test; never share state between tests.
- Override the *dependency* (repository/use case provider), not the notifier.
- If a notifier really must be faked, subclass it — `implements`/`with Mock` on a
  `Notifier` breaks its internal wiring.
- For `autoDispose` providers use `container.listen(...)` rather than
  `container.read(...)`, or the state is disposed between reads.
- Widget tests: wrap in `ProviderScope(overrides: [...])`, and reach the container
  with `ProviderScope.containerOf(tester.element(find.byType(MyWidget)))`.

## Failure catalogue

| Symptom | Cause |
|---|---|
| UI never updates after a mutation | collection mutated in place; assign a new value |
| Rebuild storm | whole-object `watch` where a `select` belongs, or state without `==` |
| State resets on navigation | screen-scoped provider without `keepAlive`, or `ProviderScope` inside `MyApp` |
| `Bad state: Tried to read a provider after dispose` | `ref` used after an `await` in a disposed autoDispose provider; capture the value before the await |
| Family provider recomputes every build | argument is a fresh `List`/`Map`; use a record or a const value |
| Test sees stale state | container reused across tests, or `read` used on an autoDispose provider |

<!-- sources: sgruhier-flutter, evanca-rules, harish-flutter-tester -->
