# SwiftData

Verified against: iOS 26.6 SDK.

Failure modes that compile cleanly. Several of these crash at runtime rather than at build
time, which is why they survive in generated code.

## Contents

- [Model rules](#model-rules)
- [Relationships](#relationships)
- [Saving and identifiers](#saving-and-identifiers)
- [Queries and fetching](#queries-and-fetching)
- [Predicates](#predicates)
- [Indexes](#indexes)
- [CloudKit](#cloudkit)
- [Model inheritance](#model-inheritance)
- [Concurrency](#concurrency)

## Model rules

- `description` is a disallowed property name on a `@Model` class.
- Property observers (`willSet` / `didSet`) on `@Model` properties are silently ignored.
- `@Transient` properties are not persisted, must have a default value, and reset to that
  default on fetch. If the value derives from stored properties, a computed property is
  usually better; use `@Transient` only when the value is expensive to produce.
- `@Attribute(.externalStorage)` is a *hint*, applies only to `Data`, and SwiftData decides.
- Enum properties must conform to `Codable`. Enums with associated values do work, despite
  frequent claims to the contrary.
- `#Unique` appears **once** per model, inside the class. Multiple constraints go in one
  macro as separate key-path arrays: `#Unique<Foo>([\.email], [\.username])`.
- Put an explicit migration schema in place even for lightweight migrations. Retrofitting
  one after shipping is much harder than adding it up front.

## Relationships

- Always declare an explicit delete rule. The default is `.nullify`, which orphans children
  or crashes when the inverse property is non-optional. `@Relationship(deleteRule: .cascade)`
  is the usual intent.
- Place `@Relationship` on **one side only**. Applying it to both creates a circular
  reference.
- Specify the inverse explicitly — `inverse: \Sight.destination`. SwiftData's inference gets
  it wrong often enough that relying on it is a bug source.

## Saving and identifiers

- Autosave frequency is unpredictable in current releases. Call `save()` explicitly where
  correctness matters.
- Do not check `hasChanges` before saving; call `save()` directly.
- Persistent identifiers are **temporary until the first save** — a temporary id begins with
  a lowercase `t`, and the object gets a different id once saved. Never persist or transmit
  an id before saving.

## Queries and fetching

- `@Query` works **only inside SwiftUI views**. In a model or service, use
  `modelContext.fetch(FetchDescriptor<T>())`.
- `ModelContext.fetchCount()` with a fetch descriptor is cheaper when you only need a count,
  but it does **not** live-update — the view must be invalidated by something else.
- `FetchDescriptor.relationshipKeyPathsForPrefetching` avoids N+1 faulting when you know a
  relationship will be traversed. It is empty by default.
- `FetchDescriptor.propertiesToFetch` limits which properties are loaded; all are fetched by
  default.

## Predicates

`#Predicate` supports a subset of Swift. Some unsupported constructs fail to compile; others
compile and then crash at runtime, which is the dangerous category.

Compiles and crashes:

```swift
// Crash at runtime.
#Predicate<Movie> { $0.cast.isEmpty == false }

// Correct.
#Predicate<Movie> { !$0.cast.isEmpty }
```

Also compiles and crashes: predicates over computed properties, over `@Transient`
properties, over fields inside a custom `Codable` struct, and any regular-expression match
(`$0.name.contains(/Titanic/)`). Every predicate must reference data actually stored in the
model.

Does not compile: `hasSuffix`, `lowercased`, `map`, `reduce`, `count(where:)`,
`Collection.first`, and custom operators. `hasPrefix` is unsupported — use
`starts(with:)`.

String matching against user input uses `localizedStandardContains`, not `contains` or
`lowercasedContains`:

```swift
@Query(filter: #Predicate<Movie> { $0.name.localizedStandardContains("titanic") })
private var movies: [Movie]
```

## Indexes

`#Index` (iOS 18+) speeds reads at a small write cost, so it is a poor trade for
write-heavy, read-rare data such as logs.

```swift
@Model class Article {
    #Index<Article>([\.type], [\.type, \.author])   // single and compound
    var type: String
    var author: String
}
```

## CloudKit

These apply only when the container is configured for CloudKit, and getting them wrong
breaks the **local** store too:

- Never use `@Attribute(.unique)` or `#Unique` — CloudKit does not support uniqueness.
- Every property must have a default value or be optional.
- Every relationship must be optional.
- Indexes and model subclasses are supported on the appropriate OS releases.
- CloudKit is eventually consistent. Any code path must work when the data has not synced
  yet.

## Model inheritance

Supported from iOS 26. Uncommon — protocols are usually simpler and better; add subclassing
only when it earns its place.

- Both parent and child classes carry `@Model`.
- Child classes must be marked `@available(iOS 26, *)` **even when the deployment target is
  already 26**. Code that *uses* the model does not need the annotation.
- List parent *and* children in the container's schema; SwiftData does not infer the link.
- A relationship to a parent class may hold any subclass instance.
- `@Query private var articles: [Article]` returns the parent plus every subclass.
  Filter subclasses with `is` inside `#Predicate`; the element type stays the parent, so
  accessing child properties needs a cast. Casting inside the predicate works:

  ```swift
  @Query(filter: #Predicate<Article> { article in
      if let tutorial = article as? Tutorial { tutorial.difficulty < 3 }
      else if let news = article as? News { news.topic == "General" }
      else { false }
  }) private var frontPage: [Article]
  ```

Deep subclass chains complicate migrations; two levels is already a smell.

## Concurrency

`ModelContext` and model instances must never cross actor boundaries. `ModelContainer` and
`PersistentIdentifier` *are* `Sendable`: send the identifier and re-fetch in the destination
context. `@ModelActor` generates the boilerplate for an actor that owns its own context.

<!-- sources: twostraws-swiftdata, twostraws-swiftui, apple-docs -->
