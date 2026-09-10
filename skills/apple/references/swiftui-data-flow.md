# SwiftUI data flow

Verified against: iOS 26.6 SDK.

Ownership, observation granularity, and bindings. The failures here are silent: the code
compiles, renders, and quietly ignores updates or invalidates far more than it should.

## Contents

- [Ownership table](#ownership-table)
- [Passed values are never @State](#passed-values-are-never-state)
- [@Observable models](#observable-models)
- [Observation granularity](#observation-granularity)
- [Narrow the inputs](#narrow-the-inputs)
- [Bindings](#bindings)
- [Environment](#environment)
- [Side effects](#side-effects)
- [Old patterns](#old-patterns)

## Ownership table

| Situation | Property wrapper |
|---|---|
| Value type owned by this view | `@State private var` |
| Value type owned by an ancestor, child writes back | `@Binding var` |
| Value type owned by an ancestor, child only reads | plain `let` / `var` |
| `@Observable` object created by this view | `@State private var` |
| `@Observable` object injected, child only reads | plain `let` / `var` |
| `@Observable` object injected, child needs bindings | `@Bindable var` |
| `@Observable` object shared down a subtree | `.environment(obj)` + `@Environment(T.self)` |
| Non-observable expensive object kept alive (a `CIContext`, a renderer) | `@State private var`, used purely as a cache |

`@State` must be `private`. It is view-local storage; anything non-private advertises an
ownership the framework does not actually give the caller. If you find a non-private
`@State` while doing unrelated work, report it rather than changing it.

## Passed values are never @State

The single most damaging data-flow bug in generated SwiftUI. `@State` initialises its
storage on first appearance and then **ignores the initialiser argument forever**. A row
declared this way shows the value it was first created with and never updates:

```swift
// Wrong: the parent's updated `item` is dropped after first render.
struct Row: View {
    @State var item: Item
}

// Right: an input the parent owns.
struct Row: View {
    let item: Item
}

// Right, when the row must write back:
struct Row: View {
    @Binding var item: Item
}
```

The same rule applies to `@StateObject` for injected reference types: `@StateObject` is for
objects the view creates, `@ObservedObject` for objects handed to it.

## @Observable models

Use `@Observable` for classes that feed views. It generates per-property observation, so a
view that reads `model.title` invalidates on `title` changes and not on `description`
changes. `ObservableObject`'s `objectWillChange` broadcast cannot do that.

Mark `@Observable` classes `@MainActor` unless the module sets
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`. Views read the model on the main actor during
body evaluation; without the annotation, background writes race with those reads, and Swift 6
strict concurrency flags it.

```swift
@MainActor
@Observable
final class OrderModel {
    var status: DeliveryStatus = .placed
}
```

`@Observable` is not supported on `actor` types.

**Make stored-property types `Equatable`.** The generated setter skips invalidation when
the new value equals the old one — but only when it can compare them. A non-`Equatable`
enum or struct means every assignment invalidates every reader, which matters for
properties written repeatedly with the same value (polling, streaming, timers). For
collection properties the conformance delegates to the element type: a `[Ingredient]` where
`Ingredient` is not `Equatable` invalidates on every assignment.

Never put `@AppStorage` inside an `@Observable` class, even with `@ObservationIgnored`. It
does not trigger view updates from there.

## Observation granularity

The tracking unit is the **stored property**, not a field inside it. Reading any field of a
stored struct, or any element of a stored `Array` / `Dictionary` / `Set`, creates a
dependency on the entire property.

Computed properties inherit the dependencies of whatever they read. Wrapping a lookup in a
computed property looks like narrowing and is not:

```swift
// Still depends on the whole `users` array — the computed body reads it.
var currentUser: User? { users.first { $0.id == currentUserID } }
```

Fix by caching the derived value as its own stored property and recomputing it in `didSet`
on each input, so views depend only on the prepared property:

```swift
@MainActor
@Observable
final class AppState {
    var users: [User] = [] { didSet { recomputeCurrentUser() } }
    var currentUserID: User.ID? { didSet { recomputeCurrentUser() } }
    private(set) var currentUser: User?

    private func recomputeCurrentUser() {
        currentUser = users.first { $0.id == currentUserID }
    }
}
```

For rows over a collection, pass each row the field it renders rather than the model plus an
index. `UserRow(model: model, index: i)` makes every row depend on the whole array. For
multi-field rows, store per-element `@Observable` instances on the model and pass the
instance.

Reading several individual properties of one model is fine — that is exactly what
per-property tracking is for. The problem is compound properties, not property count.

## Narrow the inputs

A large `struct` passed whole into a subtree gives every view a comparison surface as wide
as the struct. Pass each view the fields it reads:

```swift
// Wrong: any change to any User field re-runs this body.
struct NameBadge: View { let user: User }

// Right.
struct NameBadge: View { let name: String }
```

When every field really is consumed somewhere, split the payload into per-view structs, or
hold it in an `@Observable` model and pass the model — reference comparison is pointer
identity and costs nothing.

## Bindings

Never build a binding with `Binding(get:set:)` inside `body`. Each evaluation allocates a
fresh closure pair, which defeats comparison and causes spurious invalidation.

```swift
// Wrong
let b = Binding(get: { model[scoreFor: player] },
                set: { model[scoreFor: player] = $0 })

// Right: project through a subscript. Add the subscript to the model if it lacks one.
@Bindable var model = model
PlayerScoreRow(player: player, score: $model[scoreFor: player])
```

The equivalent for side effects is `$state` plus `onChange(of:)` rather than a custom
setter.

Numeric text entry binds to the number, not a string:
`TextField("Score", value: $score, format: .number)` with `.keyboardType(.numberPad)` or
`.decimalPad`. The keyboard modifier alone does not parse anything.

## Environment

Define custom keys with `@Entry`:

```swift
extension EnvironmentValues {
    @Entry var accentPalette: Palette = .standard
}
```

Three rules the compiler will not enforce:

1. **Never store a closure or function value in your own environment or focused-value key.**
   Function values cannot be compared, so every reader in the subtree invalidates on every
   environment write. Wrapping the closure in a struct does not help — the struct is rebuilt
   with a fresh closure each pass. Defunctionalise: declare a protocol with a named method
   (or `callAsFunction`), inject a concrete conforming struct that captures what it needs.
   This does *not* apply to framework keys such as `\.openURL`, `\.dismiss`, or `\.refresh`;
   those are designed to wrap a closure.
2. **`@Entry` defaults must be stable.** Every environment write re-evaluates the default for
   readers that fall back to it, so `Model()`, `Date()`, `UUID()`, or any fresh allocation
   invalidates the subtree on unrelated writes. Back the default with a `static let`, or make
   the entry optional with a `nil` default. Literals and case-only enums are already stable.
3. **Do not read an environment value you no longer use.** An unused `@Environment` property
   still subscribes the view to that key.

`FocusedValues` entries are always optional and cannot declare a different default.

## Side effects

When a view reads a dependency *only* to run `onChange` — never to render — the read still
invalidates the whole body. Move the dependency and the `onChange` into a `ViewModifier` so
only the modifier invalidates:

```swift
struct WordCountLogger: ViewModifier {
    let document: DocumentModel
    func body(content: Content) -> some View {
        content.onChange(of: document.wordCount) { log(document.wordCount) }
    }
}
```

Apply this only when the dependency is not also rendered and the host body is expensive.
On a trivial body the extra view costs more than it saves.

## Old patterns

<details>
<summary>Legacy observation, still valid but not for new code</summary>

`ObservableObject` / `@Published` / `@StateObject` / `@ObservedObject` / `@EnvironmentObject`
remain supported and are the right call in two situations: a Combine-based pipeline such as
a debouncer (add `import Combine`; SwiftUI no longer re-exports it), and a legacy codebase
where converting the object graph would be a larger change than the task at hand. In both
cases keep `@StateObject` for view-created objects and `@ObservedObject` for injected ones.

</details>

<!-- sources: apple-xcode27, avdlee-swiftui, twostraws-swiftui, apple-docs -->
