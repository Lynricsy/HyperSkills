# View structure and modifiers

Verified against: iOS 26.6 SDK.

A view is SwiftUI's unit of invalidation. When an input changes, SwiftUI re-runs the body of
the smallest enclosing view that depends on it — so how you factor a hierarchy decides how
much work each update costs, not just how the source reads.

## Contents

- [Sections are View types, not computed properties](#sections-are-view-types-not-computed-properties)
- [Keep init cheap](#keep-init-cheap)
- [Conditional modifiers](#conditional-modifiers)
- [Single-child Group](#single-child-group)
- [Buttons and taps](#buttons-and-taps)
- [Text and formatting](#text-and-formatting)
- [Closures stored on views](#closures-stored-on-views)
- [File layout](#file-layout)

## Sections are View types, not computed properties

A computed property or a `@ViewBuilder` helper method is inlined into the enclosing body. It
shares the parent's invalidation boundary, so it reduces nothing. A separate `View` struct
with narrow inputs invalidates only when *its* inputs change.

```swift
// Wrong shape. Toggling `isExpanded` re-evaluates header, details, and footer.
struct ProfileView: View {
    @State private var isExpanded = false
    let user: User

    var body: some View { VStack { header; details; footer } }

    private var header: some View { … }
    private var details: some View { … }
    private var footer: some View { … }
}

// Right shape. Only ProfileDetails re-evaluates.
struct ProfileView: View {
    @State private var isExpanded = false
    let user: User

    var body: some View {
        VStack {
            ProfileHeader(name: user.name)
            ProfileDetails(bio: user.bio, isExpanded: isExpanded)
            ProfileFooter(followers: user.followers)
        }
    }
}
```

This bites hardest on the shape a prompt asks for most often: a detail screen with named
sections (`ProductDetailView`, `RecipeDetailView`, `ArticleDetailView`). The training-data
answer is one `View` with `private var header: some View`. Factor each named section into
its own `View` struct taking only the fields it renders, and leave the parent as a thin
composition.

Small `@ViewBuilder` fragments reused two or three times inside one body, with no
independent invalidation story, are fine. The rule targets factoring done for organisation
or body length.

Flag a `body` that has grown past roughly a screenful; long bodies are where this defect
accumulates.

## Keep init cheap

A view's `init` runs every time the parent re-evaluates — many times per second inside a
`List`, a lazy stack, or an animated parent. Treat it as a constant-time copy of inputs.

```swift
// Wrong: decodes JSON and allocates a DateFormatter on every parent pass.
init(rawJSON: Data, date: Date) {
    self.summary = try! JSONDecoder().decode(WeatherSummary.self, from: rawJSON)
    let f = DateFormatter(); f.dateStyle = .medium
    self.formattedDate = f.string(from: date)
}

// Right: take prepared values; let Text format.
struct WeatherCard: View {
    let summary: WeatherSummary
    let date: Date

    var body: some View {
        VStack {
            Text(summary.headline)
            Text(date, format: .dateTime.day().month().year())
        }
    }
}
```

The same applies to `body`: assume it runs often. Sorting, filtering, and formatting belong
on the model or in a `let` derived once. Async work belongs in `task(_:)`, which is
cancelled automatically when the view disappears; `onAppear` is not.

## Conditional modifiers

Never define or use an `.if(_:transform:)` view extension. The `if`/`else` inside produces
two different view types, so toggling the condition changes structural identity: descendant
`@State` resets and the change plays as a replacement rather than an animation.

```swift
// Wrong
Text("Hello").if(isHighlighted) { $0.foregroundStyle(.red) }

// Right
Text("Hello").foregroundStyle(isHighlighted ? .red : .primary)
```

When the modifier has no neutral value, gate inside a `ViewModifier` instead. If you meet an
existing `.if` helper during unrelated work, point it out where it wraps animated or
stateful content; do not mass-refactor it.

The same reasoning favours ternaries over `if`/`else` branches in a body when only a
modifier argument differs — branching creates `_ConditionalContent` and rebuilds the
underlying platform view.

## Single-child Group

`Group { Text(status) }` wraps one concrete view in `Group<Text>`. Every chained modifier
must then type-check against the wrapper, for no behavioural benefit. Drop it.

A `Group` whose content is a `ForEach`, several siblings, or an `if`/`else`
(`_ConditionalContent`) is doing real work — that is what `Group` is for, and removing it
would either drop a shared modifier or force you to repeat it per branch.

## Buttons and taps

- Every tappable element is a `Button`. Use `onTapGesture` only when you need tap location
  or tap count; if you must, add `.accessibilityAddTraits(.isButton)`.
- Prefer the label-plus-symbol initialiser: `Button("Add User", systemImage: "plus",
  action: addUser)`. Pass the method directly when the signature matches instead of
  wrapping it in a closure.
- An icon-only button must still carry text. Apply `.labelStyle(.iconOnly)` to keep it
  visually icon-only while VoiceOver keeps the label. Toolbars already do this.
- Extract button actions into methods. Layout and logic in the same closure is how business
  logic ends up inside `body`.

## Text and formatting

- `Text(value, format: …)` beats a stored formatter. `Text(100, format: .currency(code: "USD"))`,
  `Text(date, format: .dateTime.day().month().year())`.
- Prefer `TextField(..., axis: .vertical)` with `lineLimit(5...)` over `TextEditor` unless a
  full-screen editing surface is required — `TextField` supports placeholder text.
- `TabView(selection:)` binds to an enum, not an `Int` or `String`:
  `Tab("Home", systemImage: "house", value: .home)`.
- Render a view to an image with `ImageRenderer`.

## Closures stored on views

Storing an escaping `@ViewBuilder` closure on a view keeps a heap allocation per instance
and defers building. Store the built value instead; the synthesised initialiser still
accepts builder syntax at the call site.

```swift
// Prefer
struct CardView<Content: View>: View {
    @ViewBuilder let content: Content
    var body: some View { VStack { content }.padding() }
}
```

Avoid `AnyView`. Reach for `@ViewBuilder`, `Group`, or generics; `AnyView` erases the type
SwiftUI uses to diff.

## File layout

One type per file — struct, class, or enum. Flag files that define several. Group folders by
app feature rather than by kind. Do not introduce a third-party framework without asking.

<!-- sources: apple-xcode27, twostraws-swiftui, avdlee-swiftui -->
