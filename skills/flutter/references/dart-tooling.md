# Tooling: analyzer, fixes, pub, runtime errors

## Contents

- [analysis_options.yaml](#analysis_optionsyaml)
- [Suppressing a diagnostic](#suppressing-a-diagnostic)
- [dart fix and format](#dart-fix-and-format)
- [Dependency conflicts](#dependency-conflicts)
- [Code generation](#code-generation)
- [Runtime error triage](#runtime-error-triage)
- [Hot reload vs hot restart](#hot-reload-vs-hot-restart)

## analysis_options.yaml

```yaml
include: package:flutter_lints/flutter.yaml     # package:lints/recommended.yaml for pure Dart

analyzer:
  exclude:
    - "**/*.g.dart"
    - "**/*.freezed.dart"
  language:
    strict-casts: true          # no implicit dynamic -> T
    strict-inference: true      # no silently inferred dynamic
    strict-raw-types: true      # no bare List/Map
  errors:
    invalid_annotation_target: ignore   # freezed + json_serializable noise

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_literals_to_create_immutables: true
    use_super_parameters: true
    avoid_print: true

formatter:
  page_width: 100
```

- Use either the map form (`rule: true/false`) or the list form (`- rule`) under
  `rules`, never both in the same block — mixing them is a config error.
- Exclude generated files instead of littering them with ignores.
- CI runs `flutter analyze --fatal-infos`; locally, treat a non-empty analyzer
  output as a failing build.

## Suppressing a diagnostic

| Scope | Syntax |
|---|---|
| One line | `// ignore: unused_local_variable` above or at end of the line |
| Whole file | `// ignore_for_file: type=lint` at the top |
| Directory | `analyzer: exclude:` glob |
| pubspec | `# ignore: sort_pub_dependencies` |

Every ignore carries a reason on the same line:
`// ignore: avoid_dynamic_calls — third-party JSON, shape verified in tests`.
An ignore without a reason is indistinguishable from a bug someone hid.

## dart fix and format

```bash
dart fix --dry-run     # list proposed changes
dart fix --apply       # apply them
dart format .          # then format
flutter analyze        # then verify
```

`dart fix` only fixes what a lint or deprecation rule describes, so enabling the
relevant lint first is what unlocks the automated migration. Review the dry run:
mechanical fixes occasionally change behaviour (for example removing an `await`
the analyzer believes is redundant).

## Dependency conflicts

```bash
flutter pub outdated       # current / upgradable / resolvable / latest
flutter pub upgrade        # within existing constraints
flutter pub deps           # who depends on the pinned version
```

Resolution order for "version solving failed":

1. Read the message — it names the two packages and the constraint that clashes.
2. `flutter pub deps` to find the package pinning the old version; upgrade that
   package if a newer release relaxes the bound.
3. Only then `dependency_overrides`, with a comment naming the upstream issue.
   An override forces an untested combination; delete it once upstream releases.
4. `flutter pub cache repair` when the failure is a corrupted cache rather than a
   constraint (checksum errors, missing files).

Commit `pubspec.lock` for applications, never for published packages.

## Code generation

```bash
dart run build_runner build --delete-conflicting-outputs
dart run build_runner watch --delete-conflicting-outputs
```

Used by `freezed`, `json_serializable`, `riverpod_generator`, `go_router_builder`,
`mockito`, `drift`. Rules:

- Generated files (`*.g.dart`, `*.freezed.dart`) are outputs: never hand-edit,
  and either commit them consistently or ignore them consistently.
- `part 'x.g.dart';` must match the file name exactly, or generation silently
  produces nothing for that file.
- After changing a signature, regenerate before running tests; stale mocks are a
  common source of "impossible" test failures.
- `--delete-conflicting-outputs` is the default answer to
  "Conflicting outputs were detected".

## Runtime error triage

| Error | Typical cause |
|---|---|
| `Null check operator used on a null value` | the null-assertion operator applied to a value that is not loaded yet; handle the loading state instead |
| `type 'Null' is not a subtype of type 'X'` | JSON field missing or misspelled; validate in `fromJson` |
| `LateInitializationError` | `late` field read before assignment; initialise in `initState` or make it nullable |
| `setState() called after dispose()` | async callback completing after the widget is gone; check `mounted` |
| `Concurrent modification during iteration` | mutating a list inside a `for` over it; iterate a copy |
| `Unhandled exception ... in a Future` | missing `catchError`/`try` around a fire-and-forget future |
| `MissingPluginException` | plugin registered after a hot restart, or a platform without an implementation; do a full restart |

Read the **first** frame of the stack that belongs to your package: framework
frames above it describe the mechanism, not the mistake. Wire
`FlutterError.onError` and `PlatformDispatcher.instance.onError` in `main` to
report the ones that reach production.

## Hot reload vs hot restart

- Hot reload (`r`) re-runs `build`, keeps state — does not pick up changes to
  `main()`, global variables, `initState` bodies already executed, enum values or
  generic type declarations.
- Hot restart (`R`) rebuilds the isolate and drops state — use it after changing
  initialisation, DI wiring or generated code.
- A change that "did not take effect" after hot reload is usually one of the
  above rather than a caching bug; restart before debugging further.

<!-- sources: dart-official, sgruhier-flutter, evanca-rules -->
