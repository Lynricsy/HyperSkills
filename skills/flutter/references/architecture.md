# Architecture: layers, folders, dependency injection

## Contents

- [The two layers (three when earned)](#the-two-layers-three-when-earned)
- [Folder policy: feature-first](#folder-policy-feature-first)
- [Who may talk to whom](#who-may-talk-to-whom)
- [Dependency injection by stack](#dependency-injection-by-stack)
- [When to escalate](#when-to-escalate)
- [Review triggers](#review-triggers)

## The two layers (three when earned)

```
UI layer     views + one business-logic holder per screen
                 (Notifier | Cubit/Bloc | ViewModel)
   |  state flows down, intents flow up
Logic layer  use cases / interactors            <- optional
   |
Data layer   repositories (single source of truth) + services (raw IO)
```

- **Service**: wraps one external thing — an HTTP client, a database, a plugin.
  Stateless, returns raw/API models.
- **Repository**: the single source of truth for one kind of data. It is the only
  place allowed to mutate that data, and the only place that caches, retries,
  merges sources, and converts API models into domain models.
- **Business-logic holder**: converts domain data into the UI state a screen needs
  and exposes intent methods. It never imports `flutter/material.dart` for logic
  purposes and never holds a `BuildContext`.
- **Use case**: earns its place only when logic spans repositories, is genuinely
  complex, or has more than one caller. A use case that forwards one call to one
  repository is a file with no content.

A repository never depends on another repository — that is the fastest way to a
dependency cycle and a second source of truth. Compose them in a use case instead.

## Folder policy: feature-first

```
lib/
  main.dart
  app.dart
  core/                 cross-feature: theme, router, network client, DI setup
  features/
    auth/
      data/             auth_api_service.dart, auth_repository.dart
      domain/           optional: sign_in.dart (use case), models
      ui/               auth_notifier.dart, login_page.dart, widgets/
    orders/
      data/ domain/ ui/
  shared/               widgets and models used by two or more features
```

Rules that make this hold up:

- No top-level `blocs/`, `widgets/`, `models/`, `screens/` buckets. Type-first
  buckets scatter one feature across four directories and make deletion unsafe.
- A feature imports `core/` and `shared/`, never another feature's `data/` or
  `ui/`. When two features need the same thing, it moves to `shared/`.
- Name the logic holder after the stack the project uses: `*_notifier.dart`,
  `*_cubit.dart`/`*_bloc.dart`, `*_viewmodel.dart`. Consistency beats preference.
- Mirror the tree under `test/`. One test file per source file makes "is this
  covered?" a `ls`, not a search.

## Who may talk to whom

| From | May call | Must not |
|---|---|---|
| View | its logic holder | repositories, services, `http`, plugins |
| Logic holder | use cases, repository interfaces | services, other screens' holders, `BuildContext` |
| Use case | repository interfaces | services, UI types |
| Repository | services, other data sources | UI types, other repositories |
| Service | the outside world | anything above it |

Type the dependency as the interface (`AuthRepository`), never the implementation
(`AuthRepositoryImpl`). The implementation type in a constructor is what makes a
test need a real network.

## Dependency injection by stack

- **Riverpod**: providers *are* the container. One `Provider` per service,
  repository and use case, each `ref.watch`-ing its dependencies. No `get_it`
  alongside it — two containers means two lifetimes for the same object.
- **Bloc**: `RepositoryProvider` above the `BlocProvider` that needs it; a
  `<Feature>Page` creates the bloc, a `<Feature>View` renders. `get_it` is the
  common alternative when the app is not widget-scoped.
- **ChangeNotifier/MVVM**: constructor injection plus `Provider`/`MultiProvider`
  at the root, or a plain service locator in `core/di/`.

Whatever the mechanism, constructor injection is the rule and the locator is only
the place that wires it up. A class that reaches into the locator inside its own
methods cannot be tested without the locator.

## When to escalate

| Signal | Move to |
|---|---|
| One logic holder coordinates three repositories | extract a use case |
| Two features need the same non-trivial flow | shared use case in `core/` or a package |
| More than ~2 teams, or clearly separate domains | melos monorepo, one package per domain |
| A feature package needs its own strings | give the package its own `.arb` files; do not reach into the app's |

Do not start there. A clean-architecture package split on day one of a CRUD app
costs more than it returns; add the layer when a concrete pain shows up.

## Review triggers

- A widget importing `http`, `dio`, `sqflite`, or a repository directly.
- `BuildContext` stored in, or passed into, a notifier/cubit/view model.
- A repository importing another repository.
- A use case whose body is a single forwarding call.
- A feature directory importing `../other_feature/...`.
- Mutable public fields on a state class, or `state.items.add(...)` in a holder.

<!-- sources: flutter-official, evanca-rules, sgruhier-flutter -->
