# ArkUI declarative UI

Verified against: OpenHarmony application-dev docs, `ui/state-management/arkts-declarative-ui-description`, `arkts-create-custom-components`, `arkts-page-custom-components-lifecycle`, `arkts-builder`, `arkts-builderparam`, `arkts-require`, `ui/rendering-control/*`.

## Contents

- [Component anatomy](#component-anatomy)
- [build() is a description, not a procedure](#build-is-a-description-not-a-procedure)
- [Lifecycle](#lifecycle)
- [Rendering control and list keys](#rendering-control-and-list-keys)
- [@Builder, @LocalBuilder, @BuilderParam](#builder-localbuilder-builderparam)
- [Styles, @Extend and @Require](#styles-extend-and-require)
- [Resources](#resources)
- [Adaptive layout](#adaptive-layout)
- [Component reuse and freezing](#component-reuse-and-freezing)
- [Known bad patterns](#known-bad-patterns)

## Component anatomy

```ts
@Entry                        // a page: must be registered in main_pages.json
@Component                    // V1 custom component (@ComponentV2 for V2)
struct Index {
  @State message: string = 'hi';

  aboutToAppear(): void {}

  build() {                   // exactly one root container
    Column() {
      Text(this.message).fontSize(20)
      Button('go').onClick(() => {})
    }
    .width('100%')
  }
}
```

Facts that bite:

- `struct`, not `class`. It cannot have a constructor; initialize fields at declaration.
- `@Entry` marks a **page**; an `@Entry` page must be declared in the module's
  `main_pages.json` (referenced from `module.json5` via `"pages": "$profile:main_pages"`).
  A page file that nobody registered builds fine and cannot be routed to.
- `build()` must have exactly one root component. For an `@Entry` page that root must be a
  container (`Column`, `Row`, `Stack`, …), not a leaf like `Text`.
- Attribute methods chain onto the component and are order-sensitive in the same way
  Compose modifiers are: `.backgroundColor()` after `.padding()` paints only the inner
  bounds, and a tap handler placed before padding does not cover the padding.
- A component's member variables are private to it unless a state decorator makes them
  part of the constructor surface.

## build() is a description, not a procedure

`build()` re-runs whenever any state it reads changes. Everything below therefore executes
an unbounded number of times, which is why the framework rejects or you must avoid:

- assigning to state (`this.x = …`) — either a compile error in `build()` or an infinite
  re-render loop;
- `await` / async work;
- `console` / `hilog` calls — they will flood the log at frame rate;
- allocating a new object or array per call and passing it to a child — the child sees a
  new identity every time and can never skip;
- `switch`, `try/catch` and similar statement forms; use `if`/`else` and `ForEach` inside
  the UI description.

Do the work in `aboutToAppear`, an event handler, a `@Monitor`/`@Watch` callback, or a
`@Computed` getter, and let `build()` read the result.

## Lifecycle

Page-level (`@Entry` components only):

| Callback | When |
|---|---|
| `onPageShow` | page becomes visible |
| `onPageHide` | page becomes hidden |
| `onBackPress` | system back; return `true` to consume it |

Component-level (any custom component):

| Callback | When |
|---|---|
| `aboutToAppear` | after the instance is created, before `build()` — state may be set here |
| `onDidBuild` | after `build()` has completed (do not mutate state here) |
| `aboutToDisappear` | before destruction — release subscriptions, timers, handles |

Ownership rule: whatever you acquire in `aboutToAppear` you release in
`aboutToDisappear` — `emitter`/`eventHub` subscriptions, `setInterval`/`setTimeout`
handles, `relationalStore` `ResultSet` objects, file descriptors, animators, scroller and
web controllers. A leaked `ResultSet` holds a database connection; the RDB store has only
four read connections and one write connection, so a handful of leaks stalls every
subsequent query.

Under the `Navigation` framework the page-level callbacks belong to `NavDestination`
instead — see `references/arkui-navigation.md`.

## Rendering control and list keys

- `if / else if / else` for conditional subtrees. A branch switch destroys the old subtree
  and its component state.
- `ForEach(array, itemGenerator, keyGenerator)` builds **every** child eagerly. Fine for a
  short, fully-known list.
- `LazyForEach(dataSource, itemGenerator, keyGenerator)` with an `IDataSource`
  implementation builds only what is visible. Use it for anything long, paged or remote.
- `Repeat` (`ui/rendering-control/arkts-new-rendering-control-repeat`) is the V2-era list
  renderer with virtual scrolling and template-by-type support.

The `keyGenerator` is not optional in practice. If you omit it or derive the key from the
index, then inserting or removing an item renumbers everything after it, so the framework
rebuilds those items: component state is discarded, scroll position jumps, and item
animations have nothing to animate from. Key on a stable domain id.

Two related traps:

- `this.items = [...this.items]` to "force a refresh" replaces the array identity and
  re-renders the whole list. If the items are observable, mutate them; if you must
  replace, replace with `slice()`/`concat()` semantics and keep keys stable so the
  framework can diff.
- A `LazyForEach` data source must notify the framework (`notifyDataAdd`,
  `notifyDataChange`, …). Mutating the backing array without notifying leaves the list
  showing stale rows with no error.

## @Builder, @LocalBuilder, @BuilderParam

- `@Builder` declares a reusable UI fragment, either as a global function or a component
  method. Parameters are passed by value for primitives; to get by-reference behaviour pass
  a single object parameter.
- `@LocalBuilder` preserves the parent-child component relationship, which matters when the
  fragment reads the component's state — a plain `@Builder` passed around can lose it.
- `@BuilderParam` is the slot: a component declares `@BuilderParam content: () => void` and
  the caller supplies a trailing builder. This is how you write a layout wrapper without
  reaching for a generic children array.

Prefer a small `@Builder` over copying the same three-component cluster in five places, but
do not build a component framework out of builders — a `@Component` with `@Param`s is
easier to reason about and can hold state.

## Styles, @Extend and @Require

- `@Styles` factors out a set of common attributes; `@Extend(Component)` factors out
  attributes specific to one component type; `@AnimatableExtend` exposes an animatable
  custom attribute.
- `@Require` marks a parameter as mandatory at construction, turning "caller forgot to pass
  it" from a silent default into a compile error. Worth adding to every `@Param`/`@Prop`
  that has no sensible default.

## Resources

Use `$r('app.string.name')` / `$rawfile('x.json')` and the `$media:` / `$color:` /
`$string:` / `$profile:` forms in configuration. Two constraints:

- The argument must be a **static literal**. `$r(someVariable)` does not resolve at build
  time; use a switch over literal keys, or `resourceManager` APIs for a dynamic lookup.
- System resource names (`sys.symbol.*`, system icon ids) vary across SDK versions. A name
  that resolves on one SDK produces "unknown resource name" on another, so verify any
  system resource against the SDK the project actually builds with.

Hardcoded strings, colours and sizes also block localization and dark mode, both of which
are checked during AppGallery review.

## Adaptive layout

One codebase serves phone, foldable, tablet and PC. The tools are breakpoints and
`GridRow`/`GridCol`, `Flex` with wrapping, `mediaquery` (via `UIContext.getMediaQuery()`),
`layoutWeight`, percentage and `'auto'` sizing, and `SideBarContainer`/`Navigation`'s
`Auto` mode for single- vs double-column.

The failure mode is not ugliness, it is unreachable UI: a fixed-height bottom bar plus a
larger system font, or a fixed-width sheet on a folded screen, pushes controls off-screen.
Check every screen at the default and an enlarged font scale, in both orientations, on the
`deviceTypes` declared in `module.json5`.

## Component reuse and freezing

- `@Reusable` (V1) / `@ReusableV2` (V2) let the framework recycle component instances in a
  list instead of recreating them. A reusable component must reset all of its state in
  `aboutToReuse`; state left over from the previous item is the classic recycling bug.
- Component freezing (`freezeWhenInactive`) stops inactive components — a hidden tab, a
  page below the top of the navigation stack — from re-rendering on state changes. Without
  it, a state update fans out to every off-screen page that reads it.

## Known bad patterns

| Pattern | Consequence |
|---|---|
| State assignment or `await` inside `build()` | infinite re-render or compile error |
| `ForEach` without a stable `keyGenerator` | lost item state and scroll position on insert/remove |
| `ForEach` over a long or remote list | every row built up front; first paint stalls |
| `LazyForEach` whose data source never notifies | stale rows, no error |
| `[...arr]` / `{...obj}` to trigger a refresh | full-list re-render; also `arkts-no-spread` in many positions |
| `$r(variable)` | resource not resolved; static literal required |
| Unverified `sys.symbol.*` / system icon name | "unknown resource name" on a different SDK |
| No `aboutToDisappear` cleanup | leaked subscriptions, timers, `ResultSet`, connections |
| `@Reusable` component that does not reset in `aboutToReuse` | previous item's content shown |
| Hardcoded colours/sizes/strings | broken dark mode, localization and large-font layouts |
| `@Entry` page missing from `main_pages.json` | unroutable page, builds cleanly |

<!-- sources: openharmony-docs, corey-harmonyos, yibaiba-ark, earfrog-arkts, huawei-docs -->
