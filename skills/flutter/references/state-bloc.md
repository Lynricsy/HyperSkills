# Bloc and Cubit

Verified against: bloc / flutter_bloc 8.x–9.x.

## Contents

- [Cubit or Bloc](#cubit-or-bloc)
- [Modelling state](#modelling-state)
- [Naming](#naming)
- [Cubit](#cubit)
- [Bloc](#bloc)
- [Widget wiring](#widget-wiring)
- [Event transformers](#event-transformers)
- [Testing](#testing)
- [Failure catalogue](#failure-catalogue)

## Cubit or Bloc

| Situation | Use |
|---|---|
| State changes triggered by direct method calls | `Cubit` |
| Traceable event log, replay, analytics on intents | `Bloc` |
| Debounce, throttle, drop or sequence incoming intents | `Bloc` with an event transformer |

Default to `Cubit`; move to `Bloc` when one of the two right-hand rows becomes
true. Rewriting a Cubit into a Bloc later is mechanical.

## Modelling state

Two shapes, both valid. Pick one per feature and stay with it.

**Sealed hierarchy** — mutually exclusive situations, exhaustive `switch`,
per-case fields:

```dart
sealed class LoginState extends Equatable {
  const LoginState();
  @override
  List<Object?> get props => const [];
}
final class LoginInitial extends LoginState { const LoginInitial(); }
final class LoginInProgress extends LoginState { const LoginInProgress(); }
final class LoginSuccess extends LoginState {
  const LoginSuccess(this.user);
  final User user;
  @override
  List<Object?> get props => [user];
}
final class LoginFailure extends LoginState {
  const LoginFailure(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}
```

**Single class with a status enum** — many shared fields, and previous data must
survive a failure (a list that stays on screen while a refresh fails):

```dart
enum LoginStatus { initial, loading, success, failure }

class LoginState extends Equatable {
  const LoginState({this.status = LoginStatus.initial, this.user, this.error});
  final LoginStatus status;
  final User? user;
  final String? error;

  LoginState copyWith({LoginStatus? status, User? user, String? error}) =>
      LoginState(status: status ?? this.status, user: user ?? this.user, error: error);

  @override
  List<Object?> get props => [status, user, error];
}
```

Rules for both shapes:

- Extend `Equatable` (or use `freezed`) and list **every** field in `props`.
  A field missing from `props` produces a state that compares equal to the
  previous one, and bloc drops equal states — the UI silently never updates.
- Emit a new instance every time; never mutate and re-emit the same object.
- `copyWith` cannot set a field back to `null` with the `?? this.x` idiom. When
  clearing matters (an error that must disappear), pass the field through
  directly as in `error` above, or use a sentinel/`freezed`'s explicit `null`.
- One-off effects (snackbar, navigation) are not state. Emit them through
  `BlocListener` on a transient field, or a dedicated event/stream.

## Naming

- Events are past tense, named after what happened: `LoginSubmitted`,
  `ProfileRequested`, `AuthenticationStarted`.
- States are nouns describing a snapshot: `LoginInProgress`, `LoginSuccess`.
- Base classes are `<Subject>Event` / `<Subject>State`.

## Cubit

```dart
class LoginCubit extends Cubit<LoginState> {
  LoginCubit(this._auth) : super(const LoginState());
  final AuthRepository _auth;

  Future<void> submit(String email, String password) async {
    emit(state.copyWith(status: LoginStatus.loading));
    try {
      final user = await _auth.signIn(email, password);
      emit(state.copyWith(status: LoginStatus.success, user: user));
    } on AuthException catch (e) {
      emit(state.copyWith(status: LoginStatus.failure, error: e.message));
    }
  }
}
```

`emit` is only ever called inside the cubit/bloc. Public methods return `void` or
`Future<void>`; a method that returns state invites the UI to bypass the stream.

## Bloc

```dart
class LoginBloc extends Bloc<LoginEvent, LoginState> {
  LoginBloc(this._auth) : super(const LoginInitial()) {
    on<LoginSubmitted>(_onSubmitted);
  }
  final AuthRepository _auth;

  Future<void> _onSubmitted(LoginSubmitted event, Emitter<LoginState> emit) async {
    emit(const LoginInProgress());
    try {
      emit(LoginSuccess(await _auth.signIn(event.email, event.password)));
    } on AuthException catch (e) {
      emit(LoginFailure(e.message));
    }
  }
}
```

- The handler must not `emit` after it returns. For stream-driven state use
  `await emit.forEach(stream, onData: ...)` or `emit.onEach`, which keep the
  handler alive for the subscription's lifetime and cancel it on close.
- Override `close()` to cancel anything the bloc created, and call `super.close()`.

## Widget wiring

```dart
class LoginPage extends StatelessWidget {          // creates, does not render
  const LoginPage({super.key});
  @override
  Widget build(BuildContext context) => BlocProvider(
        create: (context) => LoginCubit(context.read<AuthRepository>()),
        child: const LoginView(),
      );
}
```

| Widget | Use |
|---|---|
| `BlocBuilder` | render from state |
| `BlocSelector` | render from one field; skips rebuilds for the rest |
| `BlocListener` | side effects — snackbar, navigation, dialog |
| `BlocConsumer` | both, in one widget |
| `context.select<Cubit, T>((c) => c.state.field)` | narrow rebuild inline |

The `Page`/`View` split matters for tests: the view can be pumped with a mocked
cubit, while the page owns construction. Use `BlocProvider.value` when passing an
existing instance (a test double, or a bloc from an ancestor) — `create` in that
position closes the bloc the ancestor still needs.

## Event transformers

`package:bloc_concurrency` supplies the four useful policies. The default is
`concurrent()` for `Bloc` handlers registered without a transformer.

| Transformer | Use for |
|---|---|
| `sequential()` | writes that must not interleave |
| `droppable()` | submit buttons: ignore taps while one is in flight |
| `restartable()` | search-as-you-type: cancel the previous run |
| `concurrent()` | independent reads |

```dart
on<SearchChanged>(_onSearch, transformer: restartable());
```

Debounce by composing a stream transformer with `restartable()`:
`transformer: (events, mapper) => restartable()(events.debounce(...), mapper)`.

## Testing

```dart
blocTest<LoginCubit, LoginState>(
  'emits loading then success',
  setUp: () => when(() => auth.signIn(any(), any())).thenAnswer((_) async => user),
  build: () => LoginCubit(auth),
  act: (cubit) => cubit.submit('a@b.c', 'pw'),
  expect: () => [
    const LoginState(status: LoginStatus.loading),
    LoginState(status: LoginStatus.success, user: user),
  ],
);
```

- `blocTest` from `package:bloc_test`; mock the repository, never the cubit under
  test.
- For widget tests, `whenListen(mockCubit, Stream.fromIterable([...]), initialState: ...)`
  drives a mocked cubit's stream.
- Assert on the emitted sequence, not on internal fields; the sequence is what the
  UI actually consumes.

## Failure catalogue

| Symptom | Cause |
|---|---|
| UI does not update although `emit` ran | field missing from `props`, or the same instance re-emitted |
| `emit was called after an event handler completed` | async work outstanding after the handler returned; use `emit.forEach`/`await` |
| Error cannot be cleared | `copyWith` with `?? this.field` cannot write `null` |
| Bloc closed too early | `BlocProvider(create:)` used where `BlocProvider.value` was needed |
| Double submit | handler registered without `droppable()` |
| Test passes but app is stuck | `blocTest` asserted states that the UI never selects on |

<!-- sources: evanca-rules, sgruhier-flutter -->
