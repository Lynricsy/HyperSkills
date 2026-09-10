# Navigation, presentation, focus, and scrolling

Verified against: iOS 26.6 SDK.

## Contents

- [NavigationStack and NavigationSplitView](#navigationstack-and-navigationsplitview)
- [Sheets, alerts, and dialogs](#sheets-alerts-and-dialogs)
- [Inspector](#inspector)
- [Scrolling](#scrolling)
- [Focus](#focus)

## NavigationStack and NavigationSplitView

`NavigationView` is soft-deprecated. Use `NavigationStack` for a single column and
`NavigationSplitView` for two or three columns.

```swift
NavigationStack(path: $path) {
    List(items) { item in
        NavigationLink(value: item) { ItemRow(item: item) }
    }
    .navigationDestination(for: Item.self) { DetailView(item: $0) }
}
```

Four rules that produce broken navigation when violated:

1. Register `navigationDestination(for:)` **once per data type** in a hierarchy. A duplicate
   registration for the same type is undefined which one wins.
2. Never mix `navigationDestination(for:)` with `NavigationLink(destination:)` in the same
   hierarchy. The two resolution paths interfere and destinations start disappearing.
3. `navigationDestination(for:)` must be inside the container the links live in, not
   attached above the `NavigationStack`.
4. The value type must be `Hashable`; use one destination type per screen kind rather than
   a stringly-typed route enum unless the app already has a router.

Programmatic navigation uses the `path` binding: append to push, `removeLast()` to pop,
`removeAll()` to return to the root. Store the path in the model when deep links or state
restoration matter.

`NavigationSplitView` collapses to a stack on compact widths automatically. Do not branch on
size class to swap containers — the framework already does it, and swapping containers
destroys navigation state.

## Sheets, alerts, and dialogs

- Prefer `sheet(item:)` over `sheet(isPresented:)` when the sheet presents an optional
  value; the item is unwrapped for you and cannot go stale. When the destination view takes
  the item as its only parameter, pass the initialiser directly:
  `.sheet(item: $selected, content: DetailView.init)`.
- Attach `confirmationDialog` to the control that triggers it. The presentation animation
  originates from the attachment point, so attaching it to an ancestor makes it appear from
  the wrong place.
- An alert whose only button dismisses it needs no button at all:
  `.alert("Saved", isPresented: $showAlert) { }`.
- Sheets own their own toolbar and dismissal. Give the sheet's root view a
  `NavigationStack` and let it call `@Environment(\.dismiss)`, rather than reaching back
  into the presenter's state.
- Use `fullScreenCover` only when the task genuinely takes over the screen; a sheet keeps
  the user oriented. On macOS `fullScreenCover` is unavailable — use a sheet or a window.
- (iOS 26+) `navigationTransitionSource(id:in:)` on the presenting control plus
  `navigationTransitionDestination(id:in:)` on the sheet morphs the sheet out of its source.

## Inspector

`inspector(isPresented:)` is a trailing detail pane on macOS and regular-width iPadOS, and
a sheet on compact widths. Size it with `inspectorColumnWidth(min:ideal:max:)`. It is not a
substitute for a sidebar: inspectors show properties of the current selection.

## Scrolling

- `List` for rows with system chrome, selection, swipe actions, and free laziness.
  `ScrollView` + `LazyVStack` when you need full control of row layout.
- `.scrollIndicators(.hidden)`, never `showsIndicators: false`.
- Reading offsets: prefer `scrollTransition` and `visualEffect { content, proxy in }` for
  visual reactions — they run in the render pass and never invalidate a body. Route the
  offset through observable state only when other logic truly needs the number.
- `onScrollGeometryChange(for:of:action:)` (iOS 18+) is the cheap way to react to
  scroll position; `scrollPosition(_:)` gives programmatic control.
- `ScrollViewReader` + `scrollTo(_:anchor:)` still applies when you must jump to an id.
- `scrollTargetBehavior(.paging)` for full-page paging;
  `.scrollTargetBehavior(.viewAligned)` with `scrollTargetLayout()` on the stack to snap to
  items.
- (iOS 26+) `scrollEdgeEffectStyle(_:for:)` controls how content fades under floating
  chrome. Cases are `.automatic`, `.hard`, `.soft`.

## Focus

- `@FocusState` properties are `private`, like `@State`.
- One `Bool` binding for a single field; an optional enum with `focused(_:equals:)` for
  several. An ambiguous binding attached to two fields silently focuses neither reliably.
- Do **not** write `@FocusState` inside a tap handler on a `.focusable()` view. The view is
  already receiving focus from the gesture, and the redundant write revokes it.
- Focusing on appearance is a timing problem: the field must exist before the write lands.
  Set the focus in `task { }` after a `Task.yield()`, or drive it from a state change that
  happens after the first layout, rather than from `onAppear` directly.
- Non-text views need `.focusable()` before `@FocusState` can target them.
- Publish values to menu commands with `focusedValue(_:_:)` and read them with
  `@FocusedValue`. Declare the key with `@Entry` on `FocusedValues`; those entries are always
  optional. Never store a closure in one.

<!-- sources: twostraws-swiftui, avdlee-swiftui, apple-docs -->
