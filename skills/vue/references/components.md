# Components: macros, contracts, lifecycle, built-ins

Verified against: Vue 3.5

## Contents

- [SFC shape](#sfc-shape)
- [Props and emits](#props-and-emits)
- [defineModel](#definemodel)
- [Slots and fallthrough attributes](#slots-and-fallthrough-attributes)
- [defineExpose and template refs](#defineexpose-and-template-refs)
- [Lifecycle registration is synchronous](#lifecycle-registration-is-synchronous)
- [provide / inject](#provide--inject)
- [Built-in components](#built-in-components)
- [Template rules that silently misbehave](#template-rules-that-silently-misbehave)
- [Scoped styles](#scoped-styles)

## SFC shape

`<script setup lang="ts">`, then `<template>`, then `<style scoped>`. Component
names are PascalCase and multi-word (`UserCard`, never `Card`) so they cannot
collide with a current or future HTML element.

Split a component when it owns more than one responsibility — typically
orchestration plus several independent presentational sections. Concrete
triggers: three or more distinct UI sections (form, filters, list, footer), or a
repeated template block that wants to be a row/card component. Route-level views
and the app root stay composition surfaces: layout, provider wiring, and feature
composition, not feature implementations.

## Props and emits

Declare both with the type-based generic form; the runtime object form loses
inference.

```ts
const { category, pageSize = 20 } = defineProps<{
  category: string
  pageSize?: number
}>()

const emit = defineEmits<{
  update: [id: number, value: string]
  close: []
}>()
```

- Defaults: prefer destructure defaults (3.5+); `withDefaults()` is the fallback
  on 3.4 and below. Do not mix both.
- Reactivity boundaries of destructured props: see `references/reactivity.md`.
- Declare every event you emit. An undeclared event falls through to the root
  element as a native listener as well, so a `@click` you emit yourself fires
  twice.
- Template listeners are kebab-case (`@update-item`), the emitted name in script
  is camelCase (`emit('updateItem')`).
- `defineProps`/`defineEmits` must be top level in `<script setup>`; they are
  compiled away, so they cannot live in a branch, a loop or a nested function.

## defineModel

`defineModel<T>()` (3.4+) is the way to implement `v-model` on a component. It
replaces the manual `modelValue` prop plus `update:modelValue` emit.

```ts
const title = defineModel<string>()                    // v-model
const firstName = defineModel<string>('firstName')     // v-model:first-name
const [text, modifiers] = defineModel<string>({ set: v => v.trim() })
```

Two failure modes worth remembering:

- **Object mutation does not emit.** `model.value.name = 'x'` mutates the
  parent's object without telling it anything, so anything watching the model
  never fires. Replace the value: `model.value = { ...model.value, name: 'x' }`.
- **`default` without `required` de-syncs.** The child shows the default while
  the parent still holds `undefined`, and initialisation emits twice. Either
  declare `{ required: true }` and let the parent own the value, or give the
  parent the same default.

Reading `model.value` immediately after writing it returns the old value; the
update lands after `await nextTick()`.

## Slots and fallthrough attributes

Use the `#name` shorthand and an explicit `<template>` per slot. Scoped slots
pass data outward: `<slot :item="item" />` consumed as `#default="{ item }"`.
Type them with `defineSlots<{ default(props: { item: T }): any }>()` when the
component is part of a shared API.

A single-root component forwards unmatched attributes and listeners to that root
automatically. Two cases need action:

- Multi-root (or `<Teleport>`-rooted) components forward nothing — bind
  `v-bind="$attrs"` on the intended element or Vue warns.
- Wrapper components that must put attributes somewhere other than the root set
  `defineOptions({ inheritAttrs: false })` and bind `$attrs` explicitly.

Precedence matters and changed in Vue 3: a fallthrough attribute **overwrites**
the same attribute set inside the component, except `class` and `style`, which
merge. A `<button data-testid="submit">` inside the component therefore loses
its own value the moment a parent passes `data-testid`. When the component's
value must win, set `inheritAttrs: false` and bind `$attrs` *before* the
explicit attribute.

## defineExpose and template refs

A `<script setup>` component exposes nothing by default. `defineExpose({ open })`
publishes an explicit imperative API — keep it to two or three methods.

`defineExpose` must run before any top-level `await` [community]. After the
first await the component is in async setup and the expose call does not reach
the instance, so the parent's ref resolves to an empty object.

```ts
const input = useTemplateRef<HTMLInputElement>('search') // 3.5+
onMounted(() => input.value?.focus())
```

`useTemplateRef(name)` is typed and refactor-safe; the older
`const el = ref(null)` + matching `ref="el"` still works. Either way the ref is
`null` while the element is behind a `v-if`, and it is only populated after
mount — always use `?.`, and use `flush: 'post'` if a watcher needs the element.

## Lifecycle registration is synchronous

`onMounted`, `onUnmounted`, `provide`, `defineExpose` and watcher creation must
happen synchronously during setup. Any of them after an `await`, inside a
`setTimeout` or in a callback registers against no instance and never runs — no
error, no warning.

```ts
// Wrong: hook registered after the await; never fires.
const data = await load()
onMounted(() => track(data))

// Right: register first, await inside.
onMounted(async () => track(await load()))
```

`onMounted`, `onUpdated` and `onUnmounted` do not run on the server. Anything
that must happen during SSR belongs in `onServerPrefetch` or in the framework's
data layer. `onErrorCaptured` is the component-level error boundary; return
`false` to stop propagation.

## provide / inject

Provide the ref, not its value — `provide(key, count)`, never
`provide(key, count.value)`. Type the channel with an `InjectionKey<T>` symbol so
both ends agree, and give `inject` a default (or assert) so the consumer is not
silently `undefined`.

```ts
export const cartKey = Symbol() as InjectionKey<{
  lines: Readonly<Ref<CartLine[]>>
  add: (line: CartLine) => void
}>
```

Hand children `readonly(state)` plus explicit updater functions rather than the
mutable source; otherwise any descendant can write to it and the origin of a
change becomes unfindable. Use injection for cross-cutting context down one
subtree; use a store for app-wide state (`references/pinia.md`).

## Built-in components

| Component | Use for | Trap |
|---|---|---|
| `<Teleport to="body">` | Modals, toasts, tooltips escaping `overflow`/stacking | Target must exist; `defer` (3.5+) waits for a target rendered later in the same cycle |
| `<Suspense>` | Async `setup` and lazy components, with `#fallback` | Still experimental API surface; one boundary per async subtree, not per component |
| `<Transition>` / `<TransitionGroup>` | Enter/leave and list moves | `TransitionGroup` children need stable `:key`; a mid-transition unmount plus `KeepAlive` leaks listeners |
| `<KeepAlive>` | Caching view state across toggles | Cached components keep running watchers; use `include`/`exclude`/`max` and handle `onActivated`/`onDeactivated` |
| `<component :is>` + `defineAsyncComponent` | Dynamic and code-split components | Async component errors need `errorComponent` or an `onErrorCaptured` above them |

## Template rules that silently misbehave

- Never put `v-if` and `v-for` on the same element: `v-if` is evaluated first, so
  the loop variable does not exist yet. Filter in a `computed`, or wrap in
  `<template v-for>` with the `v-if` on the child.
- `:key` on `v-for` must be a stable identity. An index key makes Vue reuse the
  wrong DOM node the moment the list reorders, which shows up as inputs keeping
  the previous row's text.
- Move filtering, sorting and formatting out of the template into `computed`.
  A template expression re-runs on every render; a computed caches.
- `v-show` toggles `display` and keeps the component mounted (cheap toggles);
  `v-if` unmounts (expensive subtrees, or state that must reset).
- `v-html` renders raw HTML — never with user-supplied content.
- Same-name shorthand (3.4+): `<Row :item :index />` for `:item="item"`.

## Scoped styles

`<style scoped>` adds a data attribute to the component's own elements only, so
child component internals are unreachable. Reach in deliberately with
`:deep(.child-class)`, style slotted content with `:slotted()`, and escape with
`:global()`. `v-bind()` in a style block wires a reactive value into CSS as a
custom property, which is the clean way to drive style from state instead of
computing class strings.

<!-- sources: vuejs-ai-skills, onmax-nuxt-skills, antfu-skills, awesome-copilot, vue-docs -->
