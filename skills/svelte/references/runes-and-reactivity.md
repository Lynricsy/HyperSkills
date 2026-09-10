# Runes and reactivity

Verified against: Svelte 5.57.

## Contents

- [Runes mode versus legacy mode](#runes-mode-versus-legacy-mode)
- [`$state` and `$state.raw`](#state-and-stateraw)
- [`$state.snapshot`](#statesnapshot)
- [`$derived` and `$derived.by`](#derived-and-derivedby)
- [`$effect` and its variants](#effect-and-its-variants)
- [Dependency tracking traps](#dependency-tracking-traps)
- [`$props` and `$bindable`](#props-and-bindable)
- [Reactive classes and `.svelte.js` modules](#reactive-classes-and-sveltejs-modules)
- [Wrapping external sources with `createSubscriber`](#wrapping-external-sources-with-createsubscriber)
- [Debugging with `$inspect.trace`](#debugging-with-inspecttrace)
- [Async reactivity (experimental)](#async-reactivity-experimental)

## Runes mode versus legacy mode

A component compiles in runes mode as soon as it uses a rune; otherwise it stays
in legacy mode, where a bare `let` is reactive and `$:` works. The two cannot be
combined in one component — `$state` plus `$: doubled = count * 2` is a compile
error, not a style choice. Setting `compilerOptions.runes: true` forces runes
mode project-wide and turns every remaining legacy construct into an error,
which is the useful end state of a migration. `runes: false` pins a whole
project to legacy mode.

Mixed-mode projects are legal file by file. That is what makes an incremental
Svelte 4 → 5 migration possible: convert one component at a time and leave the
rest alone. [official]

## `$state` and `$state.raw`

`$state` on an object or array returns a deeply reactive proxy: mutating a
nested property updates the UI. Deep reactivity is not broken and does not need
a workaround — it costs a proxy per object.

Use `$state.raw` when a value is only ever *replaced*, never mutated: API
responses, large tables, parsed config. Raw state cannot be mutated at all, only
reassigned, so `push` on a raw array silently does nothing useful — replace the
array instead. Raw state may *contain* reactive state.

```js
let rows = $state.raw([]);          // replaced wholesale each poll
let draft = $state({ title: '' });  // fields mutated as the user types

setInterval(async () => {
  rows = await fetch('/api/rows').then((r) => r.json()); // reassign, not push
}, 5000);
```

Only declare `$state` for values something reactive reads — a template
expression, a `$derived`, or an `$effect`. A variable read once during setup is a
plain `let`, and marking it `$state` buys a proxy for nothing.

`$state.eager(value)` reads state without waiting for in-flight `await`
expressions to settle; it exists for immediate visual feedback (an
`aria-current` on a nav link during navigation) and is otherwise a way to render
inconsistent UI. [official]

## `$state.snapshot`

Passing a `$state` proxy to a non-Svelte consumer — `structuredClone`,
`JSON.stringify` on an object with getters, an IndexedDB write, a charting
library that inspects prototypes — can behave unexpectedly because the value is
a `Proxy`. `$state.snapshot(value)` returns a plain deep clone. If the value has
a `toJSON` method, the snapshot clones that method's return value instead.

## `$derived` and `$derived.by`

`$derived` takes an *expression*, not a function. Use `$derived.by(() => {...})`
when the computation needs statements. `$derived(expr)` is exactly
`$derived.by(() => expr)`.

Deriveds are lazy and memoised: the expression re-runs when a dependency changed
*and* someone reads the value. An object or array returned from a derived is
returned as-is — it is not made deeply reactive.

Reassigning a derived temporarily overrides it until a dependency changes, which
is how optimistic UI is written (Svelte 5.25+). Declare it `const` when that
override is not wanted; `const doubled = $derived(count * 2)` is the default
choice because it makes the accidental write a compile error.

Anything read synchronously inside the expression is a dependency. That includes
values read inside functions the expression calls.

## `$effect` and its variants

An effect is an escape hatch for talking to something outside Svelte: analytics,
imperative canvas drawing, a third-party widget. It runs after the DOM updates,
never on the server, and re-runs when tracked state changes. It returns an
optional teardown that runs before the next run and on destroy.

```js
$effect(() => {
  const id = setInterval(tick, interval);   // `interval` is tracked
  return () => clearInterval(id);
});
```

Do not use an effect to compute a value — that is `$derived`. Do not use one to
mirror a prop into state; the copy drifts and the extra render pass is
observable. Do not use one to respond to a click; put the code in the handler.
Do not wrap an effect body in `if (browser)`: effects never run during SSR, so
the guard only hides the fact that the code is client-only anyway.

Writing to state that the same effect reads is an infinite loop. If a write is
genuinely required, read the trigger with `untrack(() => value)` from `svelte`
so the write does not re-arm the effect.

Variants, in the order you are likely to need them:

- `$effect.pre` — same semantics, runs before the DOM update. For measuring a
  node before it changes (scroll anchoring, autoscroll).
- `$effect.root(fn)` — creates a non-tracked scope with manual cleanup, usable
  outside component initialisation. This is what makes effects testable.
- `$effect.tracking()` — whether the current code runs inside a tracking scope.
- `$effect.pending()` — count of pending promises in the current boundary; only
  meaningful with `experimental.async`.

## Dependency tracking traps

These produce an effect or derived that "sometimes doesn't update", which is the
hardest reactivity bug to see by reading the code.

- **Optional chaining short-circuits.** In `chart?.update(scheme)`, when `chart`
  is nullish, `scheme` is never evaluated and therefore never becomes a
  dependency. Read the values you depend on unconditionally first, then branch.
- **Reading state after an `await`** inside `$effect.pre` or a plain effect body
  is outside the tracking scope. Read every dependency before the first `await`.
  (Inside a `$derived` expression, `await` *is* tracked — the expression itself
  is special-cased.)
- **Destructuring breaks the link.** `const { total } = summary` snapshots a
  number. Keep the object and read `summary.total` where it is used, or wrap the
  read in a getter or a function.
- **Passing state as an argument passes the value.** JavaScript is
  pass-by-value; `track(count)` hands over a number. Pass `() => count` and call
  it, which is also why SvelteKit's own context guidance passes functions.

## `$props` and `$bindable`

```js
let { title, size = 'md', onselect, children, ...rest } = $props();
```

Treat props as changing values. Anything computed from a prop belongs in
`$derived`, because a plain `const color = type === 'danger' ? ... : ...`
evaluates once and then lies.

A child may temporarily overwrite a non-bindable prop (useful for unsaved
ephemeral state), but that write does not reach the parent. Two-way binding is
opt-in: `let { value = $bindable('') } = $props()`, and only then may the parent
write `<Field bind:value={query} />`. A fallback value on a prop *not* declared
`$bindable` is not turned into a reactive proxy, so mutating it does nothing.

`createEventDispatcher` is deprecated. Components communicate upward through
callback props (`onselect={handler}`), which are plain function props — no
`CustomEvent`, no `.detail`, and they can be spread and forwarded.

`$props.id()` returns a per-instance unique string, for wiring `id`/`for`/
`aria-describedby` pairs without collisions (Svelte 5.20+).

## Reactive classes and `.svelte.js` modules

Runes are compiler constructs and must appear at the top level of a component
script, in a class field, or at the top level of a `.svelte.js` / `.svelte.ts`
module. `let count = $state(0)` inside a plain function is a compile error; the
`.svelte` suffix in the filename is what tells the compiler to process runes in
a non-component file.

```js
// counter.svelte.js
export class Counter {
  count = $state(0);
  double = $derived(this.count * 2);
  increment = () => { this.count += 1; };
}
```

A class with `$state` fields is the replacement for a writable store: shared
between components by reference, with no `$` prefix and no subscription
bookkeeping.

Exporting state from a module has one rule: you may not `export let` a state
variable that gets reassigned. The compiler rewrites each reference to it inside
that file, and importers get the raw signal object instead of the value. Two
ways out — export a container and mutate its properties
(`export const counter = $state({ count: 0 })`), or keep the variable private
and export accessor functions.

`.svelte.js` module state is process-wide on the server, which makes it a
cross-request leak. See `state-sharing-and-ssr.md`.

## Wrapping external sources with `createSubscriber`

For an event-based browser API — `matchMedia`, `IntersectionObserver`, a
WebSocket — `createSubscriber` (Svelte 5.7+) turns it into a getter that
participates in reactivity, without an effect in every consumer:

```js
import { createSubscriber } from 'svelte/reactivity';
import { on } from 'svelte/events';

export class MediaQuery {
  #query;
  #subscribe;

  constructor(query) {
    this.#query = window.matchMedia(`(${query})`);
    this.#subscribe = createSubscriber((update) => on(this.#query, 'change', update));
  }

  get current() {
    this.#subscribe();          // makes the getter reactive when read in an effect
    return this.#query.matches;
  }
}
```

`start` is called once while any reading effect is alive and torn down when the
last one dies. Check `svelte/reactivity` first — `MediaQuery`, `SvelteMap`,
`SvelteSet`, `SvelteDate` and `SvelteURL` already exist.

## Debugging with `$inspect.trace`

When something updates too often or not at all, put `$inspect.trace(label)` as
the *first* statement of the `$effect` or `$derived.by` (or of any function they
call) and read which dependency fired. This is a development-only rune and it
answers the question directly instead of by bisection. `$inspect(...)` logs
values with their reactive dependencies.

## Async reactivity (experimental)

Svelte 5.36+ allows `await` at the top level of `<script>`, inside `$derived`,
and in markup, behind `compilerOptions.experimental.async`. The flag is slated
to disappear in Svelte 6; until then the semantics may change in a minor
release, so do not introduce it into an existing codebase without saying so.

What changes when it is on: updates are synchronised, so the UI does not show a
half-updated state while an `await` is in flight; independent `await`
expressions in markup run in parallel; sequential `let a = $derived(await one())`
/ `let b = $derived(await two())` triggers an `await_waterfall` warning. Loading
UI comes from a `<svelte:boundary>` `pending` snippet for the first render and
from `$effect.pending()` afterwards. Block effects (`{#if}`, `{#each}`) run
before `$effect.pre` in the same component, which is the one behavioural
difference that can break existing code.

<!-- sources: svelte-ai-tools, svelte-core, spences10-svelte, ejirocodes-svelte5, awesome-copilot, svelte-dev-docs -->
