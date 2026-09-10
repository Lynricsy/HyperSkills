# Provider and ChangeNotifier (official MVVM baseline)

Use this when `pubspec.yaml` has neither Riverpod nor Bloc. It is the stack the
official Flutter architecture guidance assumes, and the cheapest one to add.

## Contents

- [Shape of a view model](#shape-of-a-view-model)
- [Listening from the view](#listening-from-the-view)
- [Wiring with package:provider](#wiring-with-packageprovider)
- [Commands and one-off effects](#commands-and-one-off-effects)
- [Failure catalogue](#failure-catalogue)

## Shape of a view model

```dart
class ProfileViewModel extends ChangeNotifier {
  ProfileViewModel({required UserRepository repository}) : _repository = repository;
  final UserRepository _repository;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  User? _user;
  User? get user => _user;

  String? _error;
  String? get error => _error;

  Future<void> load(String id) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _user = await _repository.getUser(id);
    } on RepositoryException catch (e) {
      _error = e.message;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
```

- Private fields, public getters. A public mutable field can be written from a
  widget, and then `notifyListeners` never runs.
- Expose immutable snapshots: return `List.unmodifiable(_items)` or a copy, so a
  view cannot mutate model state behind the notifier's back.
- Exactly one `notifyListeners()` per state transition, in a `finally` when the
  transition can throw. Calling it inside a loop rebuilds the screen per item.
- No `BuildContext` in the view model. It receives repositories, not widgets.

## Listening from the view

`ListenableBuilder` is the framework widget — no package required:

```dart
ListenableBuilder(
  listenable: viewModel,
  builder: (context, _) {
    if (viewModel.isLoading) return const Center(child: CircularProgressIndicator());
    final user = viewModel.user;
    if (user == null) return const Text('Not found');
    return Text(user.name);
  },
)
```

Keep the builder as small as the part that actually depends on the model: the
subtree passed as `child` is built once and reused, so hoist static content into
it.

## Wiring with package:provider

```dart
runApp(
  MultiProvider(
    providers: [
      Provider<UserRepository>(create: (_) => UserRepository(ApiClient())),
      ChangeNotifierProvider(
        create: (context) => ProfileViewModel(repository: context.read<UserRepository>()),
      ),
    ],
    child: const MyApp(),
  ),
);
```

| Call | Rebuilds the widget? | Use in |
|---|---|---|
| `context.watch<T>()` | yes | `build` |
| `context.select<T, R>((t) => t.field)` | only when `field` changes | `build` |
| `context.read<T>()` | no | callbacks, `initState` |
| `Consumer<T>` | yes, only its subtree | `build`, to narrow the rebuild |

`context.read` in `build` is a bug (the widget will not update);
`context.watch` in a callback throws. `ChangeNotifierProvider` disposes the
notifier it creates — pass an existing instance with `.value` instead, or it gets
disposed twice.

## Commands and one-off effects

A snackbar or a navigation is not state: replaying it on the next rebuild shows it
twice. Options, cheapest first:

1. Return a result from the command and act on it in the callback:
   `if (await viewModel.save()) context.go('/done');` — remember `context.mounted`.
2. Expose a `ValueNotifier<Event?>` the view listens to and clears after handling.
3. Move to `flutter_bloc`'s listener model if the screen has many such effects.

## Failure catalogue

| Symptom | Cause |
|---|---|
| Nothing rebuilds | mutated a field without `notifyListeners`, or used `context.read` in `build` |
| Rebuild storms | `notifyListeners` inside a loop, or the whole screen inside one `ListenableBuilder` |
| `A ChangeNotifier was used after being disposed` | provider recreated the model on rebuild; create it once with `create:`, pass existing ones with `.value` |
| Snackbar shows twice | one-off effect stored in state and replayed on rebuild |
| Test needs a widget tree to check logic | view model reaching for `BuildContext`; inject the repository instead |

<!-- sources: flutter-official, evanca-rules -->
