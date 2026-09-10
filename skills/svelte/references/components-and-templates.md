# Components and templates

Verified against: Svelte 5.57.

## Contents

- [Snippets and `{@render}`](#snippets-and-render)
- [Attachments replace actions](#attachments-replace-actions)
- [Keyed each blocks](#keyed-each-blocks)
- [Bindings](#bindings)
- [Events](#events)
- [Dynamic components and self-reference](#dynamic-components-and-self-reference)
- [Error and pending boundaries](#error-and-pending-boundaries)
- [Styling a component and its children](#styling-a-component-and-its-children)
- [Class and style attributes](#class-and-style-attributes)

## Snippets and `{@render}`

Snippets replace slots. A snippet is markup declared in the template and
rendered with `{@render ...}`:

```svelte
{#snippet row(item, index)}
  <tr><td>{index}</td><td>{item.name}</td></tr>
{/snippet}

{@render row(first, 0)}
```

Content passed between a component's tags becomes the `children` prop. Named
slots become named snippet props:

```svelte
<!-- Card.svelte -->
<script>
  let { header, children } = $props();
</script>

<article>
  <h2>{@render header?.()}</h2>
  {@render children()}
</article>

<!-- caller -->
<Card>
  {#snippet header()}Invoices{/snippet}
  <p>body</p>
</Card>
```

The three mistakes worth remembering:

- `{children}` renders nothing. A snippet is a function; it must be called
  through `{@render children()}`.
- A snippet prop that may be absent needs `{@render header?.()}`, or an
  `{#if header}` block with an `{:else}` fallback.
- A snippet declared at the top level of a component is visible to `<script>`.
  One that reads no component state can live in `<script module>` and be
  exported for other components to import.

Snippets take parameters, which is what makes a generic list or table component
possible without slot props.

## Attachments replace actions

`{@attach fn}` (Svelte 5.29+) runs `fn(element)` in an effect when the element
mounts and re-runs it when state read inside `fn` changes; the returned function
is the teardown. `use:action` runs once and never reacts, and its `update`
callback is legacy API — prefer an attachment for any new DOM or third-party
library integration.

```svelte
<script>
  import tippy from 'tippy.js';

  let content = $state('Hello');

  function tooltip(text) {
    return (element) => tippy(element, { content: text }).destroy;
  }
</script>

<button {@attach tooltip(content)}>Hover me</button>
```

Because `tooltip(content)` is evaluated inside the effect, the whole attachment
is destroyed and recreated when `content` changes. To keep the expensive setup
once and react to a subset of state, nest an `$effect` inside the attachment:
the outer function runs once, the inner effect re-runs.

An element can carry any number of attachments, and an attachment can be spread
onto a component through props with `createAttachmentKey`.

## Keyed each blocks

```svelte
{#each invoices as invoice (invoice.id)}
  <Row {invoice} />
{/each}
```

Without a key, Svelte updates the DOM of existing items in place and adds or
removes at the end, so a delete in the middle re-labels every surviving row and
destroys component state, focus and scroll position in the process. With a key
it moves, inserts and deletes the right nodes.

The key must identify the item, not its position: never the index. Strings and
numbers are preferred because identity then survives the object being replaced —
which is exactly what happens when a list is refetched and every object is new.
Reference comparisons against list items (`selected === row`) break for the same
reason; compare ids.

Avoid destructuring in the each declaration if the item is bound or mutated:
`{#each items as { count }}` with `bind:value={count}` binds to a local copy.

## Bindings

`bind:value` on an element or a `$bindable` prop is two-way. Function bindings
(Svelte 5.9+) put validation or transformation in the binding itself:

```svelte
<input bind:value={() => value, (v) => (value = v.trim().toLowerCase())} />
```

Read-only bindings such as `clientWidth` take `null` as the getter:
`bind:clientWidth={null, (w) => redraw(w)}`.

`bind:this` gives the DOM node or component instance; declare the target as
`$state` so reads of it are reactive.

## Events

Event handlers are attributes: `onclick`, `oninput`, `onkeydown`. Shorthand
(`{onclick}`) and spreads (`{...props}`) work because they are ordinary props.

Modifiers (`|preventDefault`, `|once`, `|stopPropagation`) no longer exist. Call
the method in the handler, or use `on` from `svelte/events` when the capture or
passive option is needed.

For `window` and `document`, use `<svelte:window onkeydown={...} />` and
`<svelte:document onvisibilitychange={...} />` rather than adding a listener in
an effect — Svelte handles removal, and it works during hydration.

Component-to-parent communication is a callback prop
(`<List onselect={handleSelect} />`), not `createEventDispatcher`.

## Dynamic components and self-reference

A component held in a variable is rendered directly: `<Layout />` where
`Layout` is `$state` or `$derived` swaps the component when the variable
changes. `<svelte:component this={X}>` is legacy. A component references itself
by importing its own file (`import Self from './Tree.svelte'`) instead of
`<svelte:self>`.

## Error and pending boundaries

`<svelte:boundary>` contains a render or effect error so it does not take down
the app:

```svelte
<svelte:boundary onerror={(error) => report(error)}>
  <RiskyWidget />

  {#snippet failed(error, reset)}
    <p>{error.message}</p>
    <button onclick={reset}>Try again</button>
  {/snippet}
</svelte:boundary>
```

A boundary only catches errors from rendering and from effects inside it — not
from event handlers, not from an `await` outside a tracked scope, and not from
code that ran during setup of a parent. Providing `failed` or `onerror` is what
makes it a boundary at all; without either, the error keeps propagating.

The `pending` snippet renders while the boundary's contents resolve for the
first time and requires `experimental.async`.

## Styling a component and its children

Component CSS is scoped. To let a parent influence a child, expose CSS custom
properties: `<Child --accent="red" />` on the caller, `color: var(--accent)` in
the child. A JavaScript value reaches CSS through the `style:` directive —
`<div style:--columns={columns}>` and then `var(--columns)` in `<style>`.

Reach for `:global` only when the target is out of your control (a third-party
component's internals). Prefer the block form so the scoping is explicit:

```svelte
<style>
  .wrapper :global {
    h1 { color: red; }
  }
</style>
```

Unused-selector warnings from `svelte-check` are usually correct: a selector
that only matches child-component markup is scoped away and does nothing.

## Class and style attributes

Since Svelte 5.16 the `class` attribute accepts objects and arrays, flattened by
clsx. Use that instead of the `class:` directive, because it composes with an
incoming `class` prop:

```svelte
<script>
  let { class: className, active } = $props();
</script>

<div class={['card', { active }, className]}>...</div>
```

<!-- sources: svelte-ai-tools, svelte-core, spences10-svelte, ejirocodes-svelte5, awesome-copilot, svelte-dev-docs -->
