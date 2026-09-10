# Dart 3 language features

## Contents

- [Pattern matching](#pattern-matching)
- [Switch statements vs expressions](#switch-statements-vs-expressions)
- [Records](#records)
- [Class modifiers](#class-modifiers)
- [Primary constructors (Dart 3.13+)](#primary-constructors-dart-313)
- [Everyday idioms](#everyday-idioms)
- [Failure catalogue](#failure-catalogue)

## Pattern matching

| Pattern | Syntax | Use for |
|---|---|---|
| Object | `User(:final name)` | destructure by getter name |
| Map | `{'id': int id}` | validate and extract JSON in one step |
| List | `[first, ...rest]` | fixed shapes, head/tail |
| Record | `(int x, :final y)` | multiple return values |
| Relational | `>= 18` | ranges, combined with `&&` |
| Logical | `A() \|\| B()`, `p && q` | share a body / add a constraint |
| Null-check | `final v?` | match only when non-null, bind non-nullable |
| Wildcard | `_` | ignore a position |

```dart
if (json case {'user': {'name': String name, 'age': int age}}) {
  return User(name: name, age: age);          // both validated and bound
}
```

Rules that bite: both branches of `||` must bind exactly the same variables;
`&&` branches must not bind overlapping ones; `when` guards run after the
pattern matches and may reference the bound variables.

## Switch statements vs expressions

```dart
// expression: produces a value, must be exhaustive, comma-separated
final area = switch (shape) {
  Square(:final side) => side * side,
  Circle(:final radius) => math.pi * radius * radius,
};

// statement: performs effects, no `break` needed, empty cases fall through
switch (status) {
  case Status.idle:
  case Status.done:
    stopSpinner();
  case Status.loading:
    startSpinner();
}
```

Exhaustiveness only works over `sealed` types and enums. If the analyzer reports
"the type X is not exhaustively matched", add the missing case rather than a `_`
fallback — the fallback is what silently swallows the next subclass someone adds.

## Records

```dart
(double lat, double lng) location() => (52.52, 13.40);
final (lat, lng) = location();

({String name, int age}) parsed = (name: 'Ada', age: 36);
```

- Structural equality is built in, so records are safe as map keys and as
  Riverpod `.family` arguments (a fresh `List` is not).
- Use records for a private, local pair of values. Once the shape crosses an API
  boundary or grows a third field, promote it to a class with named fields —
  positional record fields have no name to read at the call site.

## Class modifiers

| Modifier | Effect | Use for |
|---|---|---|
| `sealed` | abstract + all subtypes must be in the same library; enables exhaustive switch | state hierarchies, result types |
| `final` (on a class) | no extension or implementation outside the library | value types you must be able to evolve |
| `base` | subtypes must be `base`/`final`/`sealed`; implementation is inherited, not re-implemented | classes with invariants in their bodies |
| `interface` | implementable, not extendable | pure contracts |
| `mixin class` | usable as both | rare; prefer one or the other |

The default (`class`) is still extendable and implementable by anyone —
including test doubles, which is why `implements MyRepository` works in mocks.
Marking a repository interface `abstract interface class` states the intent.

## Primary constructors (Dart 3.13+)

Available by default from Dart 3.13; in 3.12 only behind
`--enable-experiment=primary-constructors`; unavailable before that. Check the
SDK constraint in `pubspec.yaml` before using them in a shared package.

```dart
// declaring parameters create the fields
class Point(final int x, final int y);

// const version: `const` goes before the class name
class const Rgb(final int r, final int g, final int b);

// assertions and derived fields go in the body via `this :`
class Rect(final double width, final double height) {
  final double area = width * height;      // primary initializer scope
  this : assert(width >= 0);
}
```

- A class with a primary constructor cannot declare another non-redirecting
  generative constructor; in-body ones must redirect (`new zero() : this(0, 0);`).
- `late` field initializers cannot see primary constructor parameters — the
  parameter is out of scope there, and referring to it is a compile-time error
  (or silently resolves to a same-named field).
- Extension types must use a primary constructor; the representation field may be
  `final` but never `var`.
- The empty-body semicolon form (`class C(int x);`) also applies to mixins,
  extensions and extension types.

## Everyday idioms

- Collection `if`/`for`/spread instead of building lists imperatively:
  `[header, ...items, if (canAddMore) addButton]`.
- Cascades for configuration: `controller..text = 'x'..selection = ...`.
- `final` by default; `var` when reassigned; explicit types on public APIs.
- Named parameters with `required` for anything with more than two arguments;
  positional booleans are unreadable at the call site.
- Prefer expression bodies (`=>`) for one-liners, and drop redundant
  `async`/`await` when a function only forwards a future.
- Extension methods for utilities on types you do not own; keep them in one
  `extensions.dart` per feature so they are discoverable.
- `Object.hash(a, b, c)` for hand-written `hashCode`; better, generate value
  types with `freezed` or extend `Equatable`.

## Failure catalogue

| Symptom | Cause |
|---|---|
| `The type 'X' is not exhaustively matched` | non-sealed supertype, or a new subclass added |
| Pattern variables "not defined" in a `\|\|` branch | branches bind different variable sets |
| Record used as a map key behaves oddly | field names differ; `(a: 1)` and `(b: 1)` are different types |
| `The class 'X' can't be extended outside of its library` | `final`/`interface` modifier; implement the interface instead |
| Primary constructor rejected by the analyzer | SDK below 3.13, or a second generative constructor in the body |
| `dart fix` rewrites more than expected | run `dart fix --dry-run` first and review the diff |

<!-- sources: dart-official, evanca-rules, sgruhier-flutter -->
