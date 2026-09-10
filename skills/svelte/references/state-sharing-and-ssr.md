# Sharing state without leaking it across users

Verified against: Svelte 5.57, SvelteKit 2.70.

## Contents

- [Why module-level state is a security bug on the server](#why-module-level-state-is-a-security-bug-on-the-server)
- [The decision order](#the-decision-order)
- [Context with `createContext`](#context-with-createcontext)
- [Keeping reactivity across the context boundary](#keeping-reactivity-across-the-context-boundary)
- [Reactive classes as the shared unit](#reactive-classes-as-the-shared-unit)
- [Where stores are still the right answer](#where-stores-are-still-the-right-answer)
- [State in the URL and in snapshots](#state-in-the-url-and-in-snapshots)

## Why module-level state is a security bug on the server

A browser is stateful; a server is not, and a long-lived server process is
shared by every visitor. Any value held at module scope — in a `.svelte.js`
module, in `+page.server.js`, in a `$lib` helper — is one value for all of them.

```js
// +page.server.js — never do this
let lastEmail = '';

export const actions = {
  login: async ({ request }) => {
    lastEmail = String((await request.formData()).get('email'));
  }
};
```

Alice logs in, Bob loads the page, Bob sees Alice's email. The same shape
appears as a "cache" (`let cachedRates`), a "current user" holder, or a request
counter. It also loses the data whenever the process restarts, so it is not even
a working cache.

This is the single most common mistake when a Svelte 4 store is ported
mechanically to `export const store = $state({...})`: the syntax modernises and
the cross-request leak is introduced at the same time. A `writable` store at
module scope has always had the same problem; runes did not create it, but a
migration is when it gets written.

Per-user data belongs in a cookie plus a database, read through `event.locals`
in `handle`. Per-request derived data belongs in `load`'s return value.

## The decision order

1. Props, then a `children` snippet. Most "shared state" is one component
   passing a value two levels down.
2. `$state` in the nearest common ancestor, passed down.
3. Context, when the ancestor does not know its descendants (a compound
   component, a form, a theme).
4. `.svelte.js` module state — client-only apps, or genuinely global immutable
   configuration. In an SSR app this is the option that needs justification.
5. The URL (`page.url.searchParams` plus `goto`) for anything that should
   survive a reload or be shareable.

## Context with `createContext`

`createContext` (Svelte 5.40+) returns a `[get, set]` pair (plus `has`) and
removes both the string key and the `unknown` return type of
`getContext`/`setContext`:

```ts
// user-context.ts
import { createContext } from 'svelte';

export const [getUser, setUser] = createContext<() => User>();
```

```svelte
<!-- +layout.svelte -->
<script>
  import { setUser } from './user-context';
  let { data } = $props();
  setUser(() => data.user);
</script>
```

```svelte
<!-- deep/child.svelte -->
<script>
  import { getUser } from './user-context';
  const user = getUser();
</script>

<p>{user().name}</p>
```

Context is set during component initialisation only, and it is scoped to the
component subtree — which is why it is safe under SSR: each request renders its
own tree. On earlier Svelte versions use `setContext(key, value)` /
`getContext(key)` with a module-level `Symbol` as the key.

## Keeping reactivity across the context boundary

Context stores a *value*. Putting `data.user` in it stores the object that
existed at initialisation, and later updates never arrive. Store a function (as
above) or an object whose properties are read at use time — the same
pass-by-value rule that applies to any function taking state.

One SSR-specific consequence: updating context-based state from a deeper
component during server rendering does not affect an ancestor that has already
rendered, while on the client it does. That asymmetry shows up as content
flashing during hydration, so pass state down rather than pushing it up.

## Reactive classes as the shared unit

```js
// cart.svelte.js
export class Cart {
  items = $state([]);
  total = $derived(this.items.reduce((sum, i) => sum + i.price, 0));

  add(item) { this.items.push(item); }
}
```

Instantiate it where it belongs — in a layout, put the instance in context; in
a client-only widget, instantiate it in the component. Do not instantiate it at
module scope in an SSR app, for the reason above.

Exporting state from a module has a compiler rule of its own: a `$state`
variable that is reassigned cannot be exported, because references to it are
rewritten inside its own file and importers would receive the signal object.
Export a container and mutate its properties, or export accessor functions.

## Where stores are still the right answer

`svelte/store` is not removed and `$store` auto-subscription still works. Keep
or reach for a store when:

- an existing library's public API is a store (many still are), or
- the value must be consumed by non-Svelte code through `.subscribe()` /
  `get()`, or
- code outside a component needs to observe changes without an effect.

For new application state inside components, a `$state` field is smaller and
type-safe without a wrapper. Do not convert a store that a third party consumes
just to remove the `$`.

## State in the URL and in snapshots

Filters, tabs, pagination and sort order belong in `page.url.searchParams`;
navigate with `goto(url, { replaceState: true, keepFocus: true, noScroll: true })`
so the page does not jump. SvelteKit re-runs the `load` functions that depend on
the URL, which is the invalidation mechanism you would otherwise hand-write.

Ephemeral DOM state that should survive back/forward but not a reload — scroll
position inside a pane, a partially typed comment — belongs in a `snapshot`
export from `+page.svelte`, not in a store.

<!-- sources: svelte-ai-tools, svelte-core, sveltekit-core, spences10-svelte, ejirocodes-svelte5, svelte-dev-docs -->
