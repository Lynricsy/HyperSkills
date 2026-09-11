# State management V1 and V1/V2 interop

Verified against: OpenHarmony application-dev docs, `ui/state-management/arkts-state`, `arkts-prop`, `arkts-link`, `arkts-provide-and-consume`, `arkts-observed-and-objectlink`, `arkts-custom-component-mixed-scenarios` (API ≤18), `arkts-v1-v2-mixusage` (API 19+).

## Contents

- [Why V1 still matters](#why-v1-still-matters)
- [V1 decorator table](#v1-decorator-table)
- [@State](#state)
- [@Prop, @Link](#prop-link)
- [@Provide and @Consume](#provide-and-consume)
- [@Observed and @ObjectLink](#observed-and-objectlink)
- [AppStorage and LocalStorage](#appstorage-and-localstorage)
- [Interop: API 19 and later](#interop-api-19-and-later)
- [Old patterns](#old-patterns)
- [Diagnosing a stale V1 UI](#diagnosing-a-stale-v1-ui)

## Why V1 still matters

Most HarmonyOS code in the wild is V1, and a full migration in one step is not practical —
which is exactly why the platform ships interop APIs instead of a hard cutover. Two
operating rules follow:

- Within one component, and preferably within one feature subtree, pick one generation and
  stay in it. Mixing inside a component is a compile error, and mixing across a component
  boundary is a set of narrow, version-dependent allowances.
- Migrate by subtree, leaf-first, with the interop APIs at the seam. Converting a component
  without converting the model class it reads leaves you with a component that compiles and
  does not update.

## V1 decorator table

| Decorator | Purpose |
|---|---|
| `@State` | component-local state, but **can be overwritten from the parent** |
| `@Prop` | one-way parent → child; deep copy |
| `@Link` | two-way parent ↔ child; reference |
| `@ObjectLink` | two-way link to a property of an `@Observed` class instance |
| `@Provide` / `@Consume` | two-way across component levels |
| `@Watch` | callback on change of a decorated variable |
| `@Observed` | marks a class observable (first level only) |
| `@Track` | narrows observation to specific class properties |
| `@StorageLink` / `@StorageProp` | two-way / one-way with `AppStorage` |
| `@LocalStorageLink` / `@LocalStorageProp` | two-way / one-way with a `LocalStorage` |
| `@Reusable` | marks a V1 component reusable |

Multiple decorators on one variable are forbidden; the only exceptions are `@Watch`,
`@Once` and `@Require`.

## @State

- Must be initialized at declaration, otherwise compile error.
- Cannot decorate a `Function`-typed variable. Before API 23 that threw at runtime; since
  **API 23** it is a compile error. If you are on an older SDK and a callback is arriving
  through `@State`, you have a latent runtime failure, not a working pattern.
- Observes value changes for primitives, and whole-object replacement for classes. It does
  **not** observe nested properties.

## @Prop, @Link

`@Prop` deep-copies the value. Everything except primitives, `Map`, `Set`, `Date` and
`Array` is lost in the copy — notably native-backed types such as `PixelMap`, which are
partly implemented in native code and cannot be reproduced by an ArkTS deep copy. A
`@Prop pixelMap` looks correct and yields an unusable image.

Because it is a copy, child writes never reach the parent. That is by design; if you need
write-back, that is `@Link`.

`@Link` requires initialization from the parent and can only be initialized by a V1 state
variable — `@State`, `@Link`, `@Prop`, `@Provide`, `@Consume`, `@ObjectLink`,
`@StorageLink`, `@StorageProp`, `@LocalStorageLink`, `@LocalStorageProp`. A plain variable
or a V2 state variable cannot initialize a `@Link`, and this restriction was **not**
relaxed in API 19. When a V2 parent needs two-way sync with a V1 child, restructure to
`@Param` + `@Event` rather than trying to feed the `@Link`.

`@Link` is private to the component; it is not readable from outside.

## @Provide and @Consume

- Matched by alias first, then by property name — the reverse of V2, where only the alias
  counts.
- `@Provide` **may** be initialized from the parent; V2's `@Provider` may not.
- Duplicate `@Provide` keys in one component tree are rejected unless `allowOverride` is
  set; V2 allows duplicates by default.
- Before **API 20**, `@Consume` had no local default and threw if no `@Provide` was found.
  From API 20 a default may be set; without one it still throws. A V1 component that is
  reused outside its original parent is the usual way this exception reaches production.
- Function types are not supported. Pushing a callback down through levels needs V2's
  `@Provider`/`@Consumer`, or an explicitly threaded parameter.

## @Observed and @ObjectLink

This pair is V1's only route to nested observation, and it is a proxy mechanism rather than
a deep one:

```ts
@Observed class Son { name: string = ''; }
@Observed class Father { son: Son = new Son(); }

// @State father: Father  ->  changing father.son.name does NOT re-render.
// Break the nesting apart: a child component takes @ObjectLink son: Son.
```

So every nesting level you want to observe needs its own component with an `@ObjectLink`.
The component tree ends up shaped by the data model, which is the structural complaint that
produced V2. `@Track` narrows which properties of an `@Observed` class participate, to
avoid re-rendering on unrelated fields.

## AppStorage and LocalStorage

`AppStorage` is process-wide; a `LocalStorage` instance is scoped to a UIAbility's UI
instance. `@StorageLink`/`@StorageProp` and `@LocalStorageLink`/`@LocalStorageProp` bind a
component variable to a key in them.

Two traps worth stating:

- These decorators bind a **snapshot-shaped value** at a key. Binding one to an
  `@ObservedV2` view-model object is a category error: the storage layer neither tracks nor
  round-trips the V2 observation, so updates are lost in one direction or both. Store
  serializable fields, not models.
- `AppStorage.getShared` and other global accessors have `UIContext` equivalents
  (`getSharedLocalStorage`); in a multi-window app use those.

For V2, the persistence counterpart is `PersistenceV2` — see
`references/data-persistence.md`.

## Interop: API 19 and later

Two hard constraints survive every relaxation:

1. **V1 decorators cannot be combined with `@ObservedV2`.** `@ObservedV2`/`@Trace` carries
   its own observation mechanism and the framework refuses to run it alongside V1's. This
   includes V1 receiving an `@ObservedV2`-decorated class through any V1 decorator — a
   compile error.
2. **V1 `@Link` still only accepts a V1 state variable.** Use `@Param` + `@Event` on the V2
   side instead.

Everything else goes through two APIs, both added in **API version 19** on `UIUtils`:

**`UIUtils.enableV2Compatibility(v1State)` — V1 → V2.** Makes a V1 state variable observable
inside `@ComponentV2`.

- Applies only to V1 state variables (`@Observed` instances, `@State`, `@Prop`, `@Link`,
  `@Provide`, `@Consume`, `@ObjectLink`); anything else is returned unchanged, silently.
- Traverses class properties and `Array`/`Set`/`Map` items recursively, stopping each branch
  at the first non-V1-state value.
- Call it **at the construction site of the V2 component** —
  `SubComponentV2({ param: UIUtils.enableV2Compatibility(this.state) })`. Called anywhere
  else, you must call it again every time the whole variable is reassigned, and the day
  someone forgets is the day the subtree stops updating.
- Rejects non-objects, `undefined`, `null`, `@ObservedV2`/`makeObserved` return values, and
  built-ins decorated with V2 decorators.

**`UIUtils.makeV1Observed(plainObject)` — plain data → V1.** Wraps a non-observable object
into a V1-observable one, equivalent to `@Observed`, so the result can initialize an
`@ObjectLink`.

- Converts a plain class, `Array`, `Map`, `Set` or `Date`. Already-V1 state is returned
  unchanged.
- **Wraps the first layer only** — it is not recursive. Nested objects stay unobserved,
  which is the mistake to look for when a `makeV1Observed` fix "half works".
- Rejects `collections` types, `@Sendable` classes, non-objects, `undefined`, `null`, and
  the same V2-origin values as above.

Without `enableV2Compatibility`, complex V1 data passed into `@ComponentV2` arrives as an
inert value: reads work, updates never propagate. No error is reported.

## Old patterns

<details><summary>Mixed-use rules for API version 18 and earlier</summary>

Before the interop APIs existed, the allowances were:

- V2 decorators in a V1 component, and V1 decorators in a V2 component: compile error
  (unchanged today).
- With **no variables passed**, a V1 component may use a V2 component and vice versa,
  including third-party components of the other generation.
- **V1 → V2 with variables:** a V2 component may receive them only through `@Param`. An
  undecorated V1 variable is fine; a V1 *state* variable is restricted to simple types —
  `boolean`, `number`, `enum`, `string`, `undefined`, `null`.
- **V2 → V1 with variables:** the V1 side may receive only through `@State`, `@Prop` or
  `@Provide`. Built-ins (`Array`, `Set`, `Map`, `Date`) are not supported. V2 state
  supports function types and V1 decorators do not, so passing a function is checked at
  runtime.
- `@Link` was already restricted to V1 state variables.

On a project pinned to API ≤18, plan the migration around these limits rather than around
`enableV2Compatibility`, and record the pin in the plan — the correct fix genuinely differs.

</details>

## Diagnosing a stale V1 UI

Work down this list; the answer is almost always in the first three.

1. Is the changed property nested below the decorated variable? V1 `@State`/`@Prop`/`@Link`
   see one level. Nested needs `@Observed` + `@ObjectLink` per level.
2. Is the class actually `@Observed`, and was the instance created with `new`?
3. Did the value cross a generation boundary without `enableV2Compatibility` (API 19+)?
4. Is a V2 model class (`@ObservedV2`) being received by a V1 decorator? That is a compile
   error, so if it builds, it is not this.
5. Was the whole variable reassigned after an `enableV2Compatibility` call made somewhere
   other than the construction site?
6. Is the update happening through a built-in API (`Array.push`, `Map.set`) on a value whose
   observation only covers replacement?

<!-- sources: openharmony-docs, corey-harmonyos, yibaiba-ark, dengshiying-harmonyos, huawei-docs -->
