# Architecture, modules and DI

## Contents

- [Layers](#layers)
- [Modelling UI state](#modelling-ui-state)
- [ViewModel-originated actions](#viewmodel-originated-actions)
- [The data layer](#the-data-layer)
- [Modularization](#modularization)
- [Dependency injection](#dependency-injection)
- [Working in an existing codebase](#working-in-an-existing-codebase)

## Layers

Three layers, dependencies pointing inwards only:

```
UI (Activity/Fragment/Composable + ViewModel)
        │  depends on
        ▼
Domain (use cases, domain models, repository interfaces)   ← optional
        │  depends on
        ▼
Data (repository implementations, network + database data sources)
```

- The **domain** layer, if present, is pure Kotlin: no `android.*`, no Compose, no
  Retrofit types. That is what makes it unit-testable off-device and shareable from
  `commonMain`.
- The **UI** layer never touches a data source directly. A composable calling a DAO is the
  same defect as a composable calling Retrofit.
- Add a use case only when logic spans repositories, is genuinely complex, or has more
  than one caller. A one-line pass-through use case per repository method is ceremony.

## Modelling UI state

Expose exactly one state object per screen, immutable and compared by value:

```kotlin
data class NewsUiState(
    val articles: ImmutableList<Article> = persistentListOf(),
    val isRefreshing: Boolean = false,
    val userMessage: String? = null,
)

class NewsViewModel(private val repo: NewsRepository) : ViewModel() {
    val uiState: StateFlow<NewsUiState> = /* … */
        repo.observeArticles()
            .map { NewsUiState(articles = it.toImmutableList()) }
            .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), NewsUiState())
}
```

- Use a sealed hierarchy instead of a flat data class when the states are genuinely
  disjoint (`Loading` / `Content` / `Error`) and the UI renders them exhaustively. Use a
  data class when fields combine (refreshing *and* showing content).
- Never expose the `MutableStateFlow`. Either back it with a private property, or use
  Kotlin's explicit backing field (`val uiState: StateFlow<T> field = MutableStateFlow(…)`,
  stable from Kotlin 2.4).
- Update with `update { it.copy(...) }` rather than read-modify-write on `.value`, which
  loses concurrent updates.
- Keep collections inside the state stable (`ImmutableList`) so the composables reading
  them can actually skip.

## ViewModel-originated actions

Navigation requests, snackbars and dialogs that originate in the ViewModel are **fields of
the UI state**, not events on a side channel:

```kotlin
// state
data class LoginUiState(val inProgress: Boolean = false, val loggedIn: Boolean = false)

// UI
LaunchedEffect(state.loggedIn) { if (state.loggedIn) onLoggedIn() }
```

Transient messages follow the same shape with an explicit acknowledgement: the state
carries `userMessage: String?`, the UI shows it, and after it is dismissed the UI calls
`viewModel.messageShown()` so the ViewModel clears the field.

The reason is durability. A `SharedFlow(replay = 0)` or a hot event bus drops the event if
nothing is collecting at that instant — exactly what happens during a configuration change
or a process restart. State survives both, and with `SavedStateHandle` it survives process
death too.

The one legitimate escape hatch is an action that must be delivered *exactly once* and
must not be replayed on recomposition (a one-shot "open the share sheet"): a
`Channel(Channel.BUFFERED)` exposed as `receiveAsFlow()`. Use it deliberately and note
that it, too, is lost on process death.

User events go the other way and need no machinery: the composable takes an
`on<Verb><Target>: () -> Unit` lambda, and the route composable wires it to a ViewModel
method named after the action (`refresh()`, `login()`). Never pass the ViewModel down to
get there.

## The data layer

- One repository per data *type*, not per screen. It is the single source of truth for
  that type and owns caching, conflict resolution and mapping to domain models.
- Repository methods are **main-safe**: one-shot work is a `suspend fun` that does its own
  `withContext(ioDispatcher)`, continuous data is a `Flow`. The caller must never need to
  know which dispatcher to use.
- Data sources are thin: Retrofit interface, Room DAO, DataStore. They map transport
  errors into domain errors; they do not decide policy.
- Offline-first reads from the database and writes through it, with the network as a
  synchroniser. The `Flow` the UI observes always comes from the database, so a successful
  sync updates the UI with no extra plumbing.

## Modularization

A workable default layout, adopted progressively rather than up front:

```
:app                  wiring, Application class, navigation host
:core:model           pure Kotlin models
:core:domain          use cases + repository interfaces (pure Kotlin)
:core:data            repository implementations, network, database
:core:designsystem    theme, tokens, shared composables
:core:common          dispatchers, Result types, small utilities
:feature:<name>       one feature: UI + ViewModel, depends on :core:domain and :core:designsystem
```

- Feature modules do not depend on each other. Cross-feature navigation goes through the
  navigation graph the `:app` module assembles.
- Split when a boundary is real (independent ownership, genuinely reusable, build-time
  pain), not to hit a module count. Every split adds a build graph edge and a Gradle
  configuration cost.
- Keep the module graph shallow and wide; a deep chain serialises the build.

## Dependency injection

Hilt is the default for an Android-only app; Koin or kotlin-inject for a Kotlin
Multiplatform project, where Hilt's annotation processing does not reach the shared source
sets.

With Hilt:

- `@HiltAndroidApp` on the `Application`, `@AndroidEntryPoint` on Activities/Fragments,
  `@HiltViewModel` with constructor injection on ViewModels.
- `@Binds` in an abstract module to bind an interface to its implementation; `@Provides`
  only when you must construct the object yourself.
- Scope deliberately: `SingletonComponent` for genuinely app-wide objects (database,
  `OkHttpClient`), `ViewModelComponent` for per-screen collaborators. Everything in
  `SingletonComponent` is memory you never get back.
- Inject dispatchers with a qualifier rather than referring to `Dispatchers.IO` inside a
  class, so tests can substitute a `TestDispatcher`.

Whatever the container, constructor injection is the mechanism. Service-locator lookups
inside a class hide the dependency from both the compiler and the test.

## Working in an existing codebase

Read before you write, and adapt rather than convert:

- If the app already follows MVI with its own base class and naming, keep it. What matters
  is unidirectional data flow, not a particular `Reducer` type.
- If it is Views + Fragments, add Compose at the edges with `ComposeView` instead of
  proposing a rewrite.
- Only propose a structural change when the user asks for one, or when the existing code
  actually violates the flow — business logic inside a composable, state mutated from two
  owners, a data source called from the UI.

<!-- sources: silvermoon-android, drjacky-ninja, meetmiyani-compose, android-official, android-docs -->
