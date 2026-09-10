# ForEach identity, List, and Table

Verified against: iOS 26.6 SDK.

`ForEach` diffs identifiers between body evaluations to decide what was inserted, removed,
moved, or merely updated. Unstable identity is not a style problem: per-row `@State`,
focus, selection, and scroll position reset, animations degrade into replacements, and
subtrees rebuild that could have been reused.

Everything here applies equally to every data-driven initialiser that behaves like
`ForEach`: `List(_:id:rowContent:)`, `List(_:id:selection:rowContent:)`, `Table(_:)`,
`OutlineGroup(_:id:children:content:)`, and `Picker` content built from a collection.

## Contents

- [The two requirements](#the-two-requirements)
- [Position is not identity](#position-is-not-identity)
- [Identity must outlive the view](#identity-must-outlive-the-view)
- [Do not mint ids inside body](#do-not-mint-ids-inside-body)
- [Keep ids cheap to hash](#keep-ids-cheap-to-hash)
- [Row structure](#row-structure)
- [Filtering and sorting](#filtering-and-sorting)

## The two requirements

An element's id must be **stable** (same element, same id across body evaluations, even
when its position changes) and **unique** (no two elements share an id in one `ForEach`).

Prefer `Identifiable` conformance over an explicit `id:` key path when the element has a
natural identity — it documents identity on the type and unlocks `sheet(item:)`,
`confirmationDialog(_:presenting:)`, and navigation values. Use an explicit key path when
the type is not yours to change, or when identity in this context lives on a different
property. Do not add `Identifiable` to a type that has no meaningful identity just to make
`ForEach` compile.

## Position is not identity

```swift
// Wrong. After a reorder or an insert, index 3 refers to a different element and
// SwiftUI reads it as "the element at 3 changed", not "B moved from 3 to 4".
ForEach(items.indices, id: \.self) { index in
    ItemRow(item: items[index])
}

// Right.
ForEach(items) { item in
    ItemRow(item: item)
}
```

Treat `.indices`, `id: \.self` on a non-key-like value, and `id: \.offset` as the same
defect. `enumerated()` itself is fine when the row genuinely needs its position — take the
id from the element and pass the index as ordinary data:

```swift
ForEach(items.enumerated(), id: \.element.id) { index, item in
    ItemRow(number: index + 1, item: item)
}
```

Since Swift 6.1 `enumerated()` conditionally conforms to `RandomAccessCollection`, so no
`Array(...)` wrapper is needed; the wrapper also forces an eager copy on every body pass.

## Identity must outlive the view

Deriving an id from a mutable property destroys the row every time the property changes:

```swift
// Wrong: typing in the row's text field renames the item, which changes its id,
// which recreates the row. Focus is lost on every keystroke.
struct Item: Identifiable {
    var id: String { title }
    var title: String
}

// Right: identity is independent of editable content.
struct Item: Identifiable {
    let id: UUID
    var title: String
}
```

A natural immutable key — a server id, a file URL, a catalogue SKU — is better than a
synthesised one because it survives a round trip through storage.

## Do not mint ids inside body

```swift
// Wrong: `Item(title:)` runs a fresh `UUID()` on every body evaluation, so ForEach
// sees the entire collection replaced each time.
ForEach(titles.map { Item(title: $0) }) { item in Text(item.title) }
```

`let id = UUID()` as a default is fine; constructing the value somewhere that does not
outlive `body` is the bug. Create the elements once in the model layer.

## Keep ids cheap to hash

Ids are hashed on every diff, for every row. `id: \.self` on a large `Hashable` struct
feeds every stored property — long strings, nested arrays — into the hasher on every
update. Use a small primitive (`UUID`, `Int`, a short `String`, a `URL`) and keep passing
the full element to the row view. Do not remove the `Hashable` conformance to "fix" this;
it is likely used for selection or navigation values.

## Row structure

- Each `ForEach` element must produce a **constant number of views**. A row that emits one
  view in one state and two in another changes the container's structure, not just its
  content.
- `List` rows should be **unary** — one view per row. A row that returns several siblings
  makes `List` synthesise structure it then has to maintain.
- For large collections inside a `ScrollView`, use `LazyVStack` / `LazyHStack`. An eager
  `VStack` with hundreds of children builds all of them up front.
- `List` is already lazy; do not wrap its content in a `LazyVStack`.

## Filtering and sorting

Do not transform the collection inside the `List` or `ForEach` initialiser:

```swift
// Wrong: re-filters on every body evaluation.
ForEach(items.filter { $0.isVisible }) { … }
```

Derive the transformed collection from the source of truth with a `let` earlier in `body`,
or precompute it on the model. Caching it in `@State` is a last resort: you then own
invalidation, and stale UI is the failure mode when you get it wrong.

If the same sort closure appears in several places, conform the element type to
`Comparable` so the ordering is defined once.

<!-- sources: apple-xcode27, avdlee-swiftui, twostraws-swiftui -->
