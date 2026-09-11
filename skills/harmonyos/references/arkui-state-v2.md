# State management V2

Verified against: OpenHarmony application-dev docs, `ui/state-management/arkts-new-*` (API 12–26.0.0).

## Contents

- [Availability](#availability)
- [Decorator map](#decorator-map)
- [@ComponentV2 and @Local](#componentv2-and-local)
- [@Param: the input](#param-the-input)
- [@Once](#once)
- [@Event: the output](#event-the-output)
- [@ObservedV2 and @Trace](#observedv2-and-trace)
- [@Monitor](#monitor)
- [@Computed](#computed)
- [@Provider and @Consumer](#provider-and-consumer)
- [Failure table](#failure-table)

## Availability

V2 arrived in **API version 12**: `@ComponentV2`, `@Local`, `@Param`, `@Once`, `@Event`,
`@Provider`, `@Consumer`, `@Monitor`, `@Computed`, `@ObservedV2`, `@Trace`. Atomic services
gained them in the same version. **ArkTS widgets (cards)** are later and uneven:
`@ObservedV2`/`@Trace` since API 12, but `@Local`, `@Param`, `@Once`, `@Event`, `@Monitor`,
`@Computed`, `@Provider`/`@Consumer` only since **API 23**. If the module builds a widget,
check the project's API version before reaching for V2 there.

## Decorator map

| Decorator | Role | Initialized from parent | Local init |
|---|---|---|---|
| `@Local` | internal component state | forbidden | required |
| `@Param` | external input; read-only inside the component | allowed | allowed |
| `@Once` | accept the first value only; auxiliary to `@Param` | — | — |
| `@Event` | output callback the child invokes to change parent state | allowed | optional (defaults to an empty function) |
| `@Provider` | cross-level provider, matched by alias | forbidden | required |
| `@Consumer` | cross-level consumer, nearest `@Provider` upwards | forbidden | required |
| `@Monitor` | method decorator; watches named state paths | — | — |
| `@Computed` | getter decorator; cached derived value, read-only | forbidden | — |
| `@ObservedV2` | marks a class observable | — | — |
| `@Trace` | marks a class property observable | — | — |
| `@Type` | pins a class property's type for serialization | — | — |
| `@ReusableV2` | marks a V2 component reusable | — | — |

The shape to aim for: **`@Local` down as `@Param`, changes back up as `@Event`**, with the
model classes carrying `@ObservedV2` + `@Trace`.

## @ComponentV2 and @Local

`@Local` fixes a real V1 defect: a V1 `@State` field can be overwritten by the parent
during construction, so a component's "internal" state is not actually internal and the
component never learns it was overridden. `@Local` must be initialized inside the
component and cannot be initialized externally, which makes the boundary enforceable.

`@Local` observes:

- primitives (`number`, `boolean`, `string`) — value changes;
- objects and classes — replacement of the whole object;
- arrays — the array itself and its items;
- built-ins `Array`, `Set`, `Map`, `Date` — changes made through their APIs;
- `null`, `undefined` and union types.

It does **not** observe properties of a nested object. That is `@Trace`'s job, not
`@Local`'s, and conflating the two is the usual cause of "I set the field and nothing
re-rendered".

## @Param: the input

- Supports any data source: plain variables, state variables, constants, function return
  values.
- When the data source is itself a state variable, its changes propagate into `@Param`.
- Cannot be assigned to inside the component. For class-typed values `@Param` holds a
  **reference**, so mutating a property of that object does reach the data source — but
  reassigning the variable does not, and is rejected.
- Observes primitives, objects, classes, nested built-ins (`Array`, `Set`, `Map`, `Date`),
  `null`, `undefined` and unions.

The design intent is that `@Param` replaces the V1 tangle of `@State`/`@Prop`/`@Link`/
`@ObjectLink` as *the* way to accept input, with `@Event` supplying the write path. If you
find yourself wanting `@Link` semantics in a V2 component, you want `@Param` + `@Event`.

## @Once

`@Once` takes the initial value from the data source and then ignores further changes.

- Legal **only** together with `@Param`, **only** inside `@ComponentV2`. Standalone
  `@Once`, `@Local @Once`, and `@Once @Param` inside a `@Component` are all errors.
- Order does not matter: `@Param @Once` and `@Once @Param` are identical.
- It does not weaken `@Param`'s own observation; it intercepts data-source updates only.
- With `@Once` present you may write to the `@Param` variable locally — that is the one
  case where a `@Param` is writable.

Use it for "seed from the parent, then own it", e.g. a draft form initialized from a saved
record.

## @Event: the output

```ts
@ComponentV2
struct Child {
  @Param count: number = 0;
  @Event onCountChange: (next: number) => void = () => {};

  build() {
    Button('+').onClick(() => { this.onCountChange(this.count + 1); })
  }
}
```

- Only arrow-function types. Decorating a non-function has no effect at all in
  `@ComponentV2` (silent no-op), and is a compile error in `@Component`.
- If the parent passes nothing, an empty function is generated — so a missing wiring shows
  up as a dead button, not a crash. When a child's whole purpose is to report upward, give
  the `@Event` a default that logs, so the gap is visible in a trace.
- You choose the parameters and return type; there is no fixed signature.

## @ObservedV2 and @Trace

```ts
@ObservedV2
class LineItem {
  @Trace qty: number = 1;   // observed
  sku: string = '';         // NOT observed
}
```

Non-negotiables:

- The two must be used **as a pair**. Either alone does nothing.
- Instances must be created with `new`. An object that reaches the class type by cast has
  no observation capability.
- Only `@Trace`-marked properties are observed; changing an unmarked property updates the
  data and never the UI. This is a silent staleness bug with no diagnostic.
- Nested classes work — but every level must be `@ObservedV2` and the leaf property
  `@Trace`. One un-decorated level breaks the chain.
- Inheritance works the same way: the property must be `@Trace` and its owning class
  `@ObservedV2`, whether that is the parent or the child class.
- When a `@Trace` property changes, only the components bound to *that property*
  re-render — which is the performance argument for V2 over V1.

`@ObservedV2`/`@Trace` may be used in both `@ComponentV2` and `@Component`, but never
combined with V1 observation: a V1 decorator may not decorate an `@ObservedV2` class, and
that prohibition survives the API 19 relaxation of the other mixing rules.

## @Monitor

`@Monitor` decorates a callback and names the state paths to watch.

- Usable in `@ComponentV2` on `@Local`, `@Param`, `@Provider`, `@Consumer`, `@Computed`;
  and in an `@ObservedV2` class on `@Trace` properties. It cannot watch anything else,
  and it cannot be used in a class that is not `@ObservedV2`.
- Change detection is strict equality (`===`). Within one event, the initial and final
  values are compared, so a value that changes and changes back does not fire.
- One `@Monitor` may watch several paths; if they change together in one event the callback
  fires **once**.
- It can reach into nested classes, multi-dimensional arrays and object arrays — provided
  the nesting is `@ObservedV2`/`@Trace` all the way down.
- **It cannot observe item changes when watching a whole array**, and it cannot see changes
  made through built-in APIs on `Array`, `Map`, `Date`, `Set`. `@Monitor('items')` on an
  array gives you replacement events only.
- In inheritance, parent and child may both declare a `@Monitor` for the same property;
  both callbacks fire.

Unlike V1's `@Watch`, `@Monitor` receives the before value as well as the after value —
that is the main reason to migrate a `@Watch`.

## @Computed

```ts
@Computed
get sum(): number { return this.count1 + this.count2 + this.count3; }
```

- Decorates a getter only. On a field or a plain method it is a compile error.
- Recomputes on initialization and when a state variable it reads changes; otherwise the
  cached value is returned.
- Read-only. Assigning to a `@Computed` property is rejected.
- In `@ComponentV2` it is computed eagerly at component creation; inside an `@ObservedV2`
  class it initializes **asynchronously** after the instance is created, so do not depend
  on its value in the constructor.
- Do nothing but derive data inside it. Mutating state from a `@Computed` getter produces
  untracked data or an application freeze.
- Not worth it for trivial arithmetic — it has its own bookkeeping cost. Use it when the
  same non-trivial expression is bound in several places.

A `@Computed` property may initialize a child's `@Param`, which is the clean way to pass a
derived value down.

## @Provider and @Consumer

```ts
@Provider('theme') theme: Theme = new Theme();   // parent
@Consumer('theme') theme: Theme = new Theme();   // any descendant
```

- V2-only: using them in `@Component` is a compile error.
- Matched by **alias**, defaulting to the property name. The alias is the only key — unlike
  V1, there is no fallback from alias to property name.
- Both require local initialization and forbid initialization from the parent.
- `@Consumer` walks up to the nearest `@Provider` with the same key; if none exists it
  keeps its local default instead of throwing. (V1 `@Consume` threw before API 20, and
  supports a default from API 20.)
- Overloading is on by default: duplicate `@Provider` keys are allowed and the nearest one
  wins. V1 `@Provide` forbids duplicates unless `allowOverride` is set.
- Function types are supported, which V1 `@Provide`/`@Consume` do not support — this is the
  clean way to push a callback through several levels.
- Observation is equivalent to `@Trace`: own-value changes synchronize both ways. Nesting
  still needs `@Trace` on the inner class.
- Since **API 22**, `BuildOptions.enableProvideConsumeCrossing = true` on a `BuilderNode`
  extends the two-way link across the BuilderNode boundary.

They couple a component to its position in the tree. Use them for genuinely ambient
concerns (theme, locale, a session object) and pass everything else explicitly.

## Failure table

| Written | Result |
|---|---|
| `@State` / `@Prop` / `@Link` / `@ObjectLink` inside `@ComponentV2` | compile error |
| `@Local` / `@Param` / `@Event` / `@Monitor` / `@Consumer` inside `@Component` | compile error |
| `@Once` alone, or with `@Local` | compile error |
| `@Computed` on a field or a non-getter | compile error |
| `@Event` on a non-function inside `@ComponentV2` | silently no-op |
| `@Param` assigned locally without `@Once` | compile error |
| Property in `@ObservedV2` class without `@Trace` | silent stale UI |
| `@ObservedV2` class instance built by cast instead of `new` | silent stale UI |
| `@Monitor` on a whole array, expecting item changes | callback never fires |
| Mutating state inside a `@Computed` getter | untracked data or app freeze |
| `@Consumer` with no matching `@Provider` | falls back to local default, no error |

<!-- sources: openharmony-docs, corey-harmonyos, yibaiba-ark, huawei-docs -->
