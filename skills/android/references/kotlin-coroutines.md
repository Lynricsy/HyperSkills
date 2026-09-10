# Kotlin and coroutines on Android

## Contents

- [Language habits that matter on Android](#language-habits-that-matter-on-android)
- [Structured concurrency](#structured-concurrency)
- [Dispatchers and main-safety](#dispatchers-and-main-safety)
- [Cancellation](#cancellation)
- [Error handling](#error-handling)
- [Flow, StateFlow, SharedFlow](#flow-stateflow-sharedflow)
- [Bridging callbacks](#bridging-callbacks)
- [Converting Java and RxJava code](#converting-java-and-rxjava-code)

## Language habits that matter on Android

- Model closed sets of outcomes as `sealed interface` hierarchies and consume them with an
  exhaustive `when`. Adding a case then becomes a compile error at every call site instead
  of a silent fallthrough.
- Prefer `data class` for state and `value class` for typed identifiers (`UserId`,
  `Millis`); the latter costs nothing at runtime while stopping argument-order bugs.
- Extension functions belong near the type they extend, not in a `Utils.kt` grab bag that
  every module depends on.
- Explicit backing fields (`val state: StateFlow<T> field = MutableStateFlow(…)`) remove
  the `_state`/`state` pair; stable from Kotlin 2.4, experimental behind
  `-Xexplicit-backing-fields` in 2.3. On older toolchains keep the private-property form.
- Turn on explicit API mode (`kotlin { explicitApi() }`) in library modules so every public
  declaration needs a visibility and a return type — the cheapest defence against
  accidentally publishing internals.
- `lateinit var` in a class that survives configuration changes is a crash waiting for a
  process restart. Prefer a nullable with a checked accessor, or constructor injection.

## Structured concurrency

Every coroutine has a parent scope, and cancelling the parent cancels the children. That
is the whole leak-prevention mechanism, so never opt out of it:

- `viewModelScope` in a ViewModel — cancelled in `onCleared()`.
- `lifecycleScope` in an Activity/Fragment, only for UI work.
- An injected application-wide scope
  (`CoroutineScope(SupervisorJob() + Dispatchers.Default)`) for work that must outlive the
  screen that started it, such as a write that should complete after the user navigates
  away.
- `GlobalScope` never. It has no parent, cannot be cancelled, and cannot be substituted in
  a test.

`coroutineScope { }` fails fast: one failing child cancels the siblings and rethrows.
`supervisorScope { }` isolates failures. Pick by whether the results are jointly required.

## Dispatchers and main-safety

A `suspend` function is main-safe when the caller can invoke it from `Dispatchers.Main`
without blocking. Achieve that inside the function, not at the call site:

```kotlin
class UserRepository(
    private val api: UserApi,
    private val ioDispatcher: CoroutineDispatcher,   // injected, not hardcoded
) {
    suspend fun load(id: UserId): User = withContext(ioDispatcher) { api.get(id).toDomain() }
}
```

Hardcoding `Dispatchers.IO` inside the class makes the class untestable — there is no seam
to replace it with a `TestDispatcher`. Inject it, defaulting to the real one if you like.

`Dispatchers.Default` for CPU work, `Dispatchers.IO` for blocking IO,
`Dispatchers.Main.immediate` when you are already on the main thread and want to avoid a
re-dispatch. Room and Retrofit `suspend` functions are already main-safe; wrapping them in
`withContext(Dispatchers.IO)` adds a thread hop for nothing.

## Cancellation

Cancellation is cooperative. A coroutine that never suspends never notices it was
cancelled:

```kotlin
while (hasMore) {
    ensureActive()            // or yield()
    processChunk()
}
```

`try/finally` runs on cancellation, but the block is already cancelled, so a suspending
call inside it needs `withContext(NonCancellable)`. Reserve that for cleanup that must
complete (closing a file, flushing a write) — it is not a general escape hatch.

Never catch `CancellationException` in a broad `catch (e: Exception)` without rethrowing:
swallowing it breaks the cancellation chain and the parent believes the child is still
running.

## Error handling

- Expected failures are values: return a `Result`-like sealed type from the repository and
  let the ViewModel map it to state.
- Unexpected failures propagate. A `CoroutineExceptionHandler` is a last-resort net at the
  scope root, not a per-call `catch`.
- `async` defers its exception to `await()`. An `async` whose result is never awaited
  hides the failure entirely.
- With `SupervisorJob`, a child failure does not cancel siblings — but the exception still
  has to go somewhere, which means a handler on the scope or a `try/catch` in the child.

## Flow, StateFlow, SharedFlow

| Type | Use for |
|---|---|
| `Flow` | Cold streams: a query, a paged source, anything with a producer per collector |
| `StateFlow` | Current-value state with conflation and an initial value |
| `SharedFlow` | Hot broadcasts with an explicit replay policy |
| `Channel` | Exactly-once delivery to a single consumer |

Rules that repeatedly matter:

- Never expose `MutableStateFlow`/`MutableSharedFlow` publicly; expose `StateFlow`/`Flow`.
- `StateFlow` conflates and compares with `equals`. Emitting a value equal to the current
  one produces nothing — which is why mutating a list in place and re-assigning it emits
  nothing at all.
- Update with `update { it.copy(...) }`; a read-modify-write on `.value` loses concurrent
  updates.
- `stateIn(scope, SharingStarted.WhileSubscribed(5_000), initial)` is the standard cold→hot
  conversion: the grace period survives a rotation instead of restarting the upstream. It
  also means nothing runs until someone collects, which any test has to account for.
- Do operator work (`map`, `filter`, `combine`) on the flow, not in the collector; that is
  where the dispatcher and backpressure decisions live.
- `flowOn` changes the upstream context only. It cannot change the collector's context.

For one-off UI actions, prefer state over a hot event stream; a `replay = 0` broadcast
drops the action whenever nothing happens to be collecting.

## Bridging callbacks

`suspendCancellableCoroutine` for a one-shot callback, `callbackFlow` for a stream. Both
must unregister:

```kotlin
fun locationUpdates(): Flow<Location> = callbackFlow {
    val listener = LocationListener { trySend(it) }
    manager.requestLocationUpdates(listener)
    awaitClose { manager.removeUpdates(listener) }   // mandatory; omitting it leaks
}.conflate()
```

`awaitClose` is required — `callbackFlow` throws without it. `trySend` is the non-suspending
send for callbacks that cannot suspend; pair it with `conflate()` or a buffer when the
source is faster than the UI.

## Converting Java and RxJava code

When converting Java to Kotlin, detect the frameworks in play first (Android, Spring,
Jackson, Lombok, JUnit) — each has conversion rules the IDE's mechanical converter gets
wrong, particularly around nullability annotations and static/companion members. Convert
in two commits: one pure `git mv` rename, one with the content change, so the file history
survives the rename.

RxJava mapping, for incremental migration:

| RxJava | Coroutines |
|---|---|
| `Single`, `Maybe`, `Completable` | `suspend fun` |
| `Observable`, `Flowable` | `Flow` |
| `subscribeOn` | `withContext` / `flowOn` |
| `observeOn(mainThread)` | collect in a lifecycle-aware scope |
| `CompositeDisposable` | the enclosing scope's cancellation |
| `BehaviorSubject` | `StateFlow` |
| `PublishSubject` | `SharedFlow` |

Migrate at a boundary (one repository at a time) and use `kotlinx-coroutines-rx3`
adapters to keep both worlds working during the transition rather than converting the
whole graph in one commit.

<!-- sources: silvermoon-android, jetbrains-kotlin, kotlin-docs, android-docs -->
