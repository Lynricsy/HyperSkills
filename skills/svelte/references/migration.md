# Migrating: Svelte 4 → 5, SvelteKit 1 → 2, SvelteKit 2 → 3

Verified against: Svelte 5.57, SvelteKit 2.70 and 3.1.

## Contents

- [Order of operations](#order-of-operations)
- [Svelte 4 → 5 translation table](#svelte-4--5-translation-table)
- [What the migration script leaves behind](#what-the-migration-script-leaves-behind)
- [Judgement calls the script cannot make](#judgement-calls-the-script-cannot-make)
- [Runes-mode behaviour changes that are not syntax](#runes-mode-behaviour-changes-that-are-not-syntax)
- [Components are functions now](#components-are-functions-now)
- [SvelteKit 1 → 2](#sveltekit-1--2)
- [SvelteKit 2 → 3](#sveltekit-2--3)

## Order of operations

1. Commit first. `sv migrate` prompts before changing a dirty tree (and
   `--no-git-check` skips the prompt), so the commit is the only undo.
2. `npx sv migrate svelte-5` — bumps dependencies and rewrites the mechanical
   parts. Review the diff before doing anything by hand.
3. Grep for `svelte/legacy` and `@migration-task`. Those are the script's
   admissions of defeat and the real work.
4. `npx sv check` until clean, then `npx @sveltejs/mcp svelte-autofixer` on the
   files you touched.
5. Only then set `compilerOptions.runes: true` to make any remaining legacy
   construct a compile error.

Migrating file by file is legal and preferable: legacy mode and runes mode
coexist per component. Do not mix them *inside* one component — `$state`
alongside `$:` is a compile error.

## Svelte 4 → 5 translation table

| Svelte 4 | Svelte 5 | Note |
|---|---|---|
| `let count = 0` (reactive) | `let count = $state(0)` | only if something reactive reads it |
| `$: doubled = count * 2` | `const doubled = $derived(count * 2)` | `$derived.by(() => {...})` for statements |
| `$: { sideEffect(count) }` | `$effect(() => { sideEffect(count); })` | but see below — most are deriveds |
| `$: if (x) doThing()` | call `doThing()` in the handler that changed `x` | an effect here is usually wrong |
| `export let name` | `let { name } = $props()` | |
| `export let value` + parent binds | `let { value = $bindable() } = $props()` | binding is opt-in now |
| `$$props`, `$$restProps` | `let { ...rest } = $props()` | |
| `$$slots` | check the snippet prop for `undefined` | |
| `on:click={fn}` | `onclick={fn}` | |
| `on:click\|preventDefault` | call `event.preventDefault()` in the handler | modifiers are gone |
| `createEventDispatcher()` | callback props: `onselect={fn}` | no `CustomEvent`, no `.detail` |
| `<slot />` | `{@render children()}` | `children` is a reserved prop name |
| `<slot name="x" />` | `{@render x?.()}` + `{#snippet x()}` at the call site | |
| `<svelte:fragment slot="x">` | `{#snippet x()}` | |
| `<svelte:component this={C}>` | `<C />` where `C` is `$state`/`$derived` | components are dynamic by default |
| `<svelte:self />` | `import Self from './This.svelte'` | |
| `use:action` | `{@attach fn}` | attachments react to state |
| `class:active={active}` | `class={['card', { active }]}` | clsx-style, Svelte 5.16+ |
| `writable(...)` + `$store` | class or object with `$state` fields | see `state-sharing-and-ssr.md` |
| `onMount` + `onDestroy` pair | one `$effect` returning a teardown | |
| `beforeUpdate` / `afterUpdate` | `$effect.pre` / `$effect` plus `tick()` | intent-dependent; not automated |
| `new Component({ target })` | `mount(Component, { target })` | |
| `setContext` / `getContext` | `createContext()` | Svelte 5.40+, type-safe |

## What the migration script leaves behind

`npx sv migrate svelte-5` handles dependencies, `let` → `$state`, event
directives, slots → render tags and snippets, and obvious `new Component(...)`
calls. Two escape hatches appear in the output and both are meant to be removed:

- **`run` from `svelte/legacy`.** The script emits it when it cannot tell
  whether a `$:` statement was a derivation or a side effect. `run` mimics `$:`
  by running once on the server and as `$effect.pre` on the client. Read each
  one: most are `$derived`, a few are `$effect`, and leaving `run` in place
  keeps the old ambiguity.
- **`preventDefault` and friends from `svelte/legacy`.** Function wrappers
  standing in for event modifiers. Inline the `event.preventDefault()` call.

Not attempted at all: `createEventDispatcher` (changing it breaks the
component's consumers, which the script cannot see) and
`beforeUpdate`/`afterUpdate` (intent is unrecoverable).

## Judgement calls the script cannot make

- **`$effect` versus `$derived`.** A `$:` block that assigns to a variable is a
  derivation, no matter that it was written as a statement block. Converting it
  to an effect that writes state adds a render pass and can loop. This is the
  single most common bad outcome of a mechanical migration.
- **`$state` versus `$state.raw`.** Values the code only ever replaces — API
  responses, poll results, parsed files — should be `$state.raw`, which skips
  the deep proxy. The script has no way to know which is which.
- **Store → module state versus store → context.** A module-scope `$state` in
  an SSR app is shared by every user. See `state-sharing-and-ssr.md`.
- **Unkeyed `{#each}`.** Svelte 4 code is full of them. Add `(item.id)` while
  you are in the file; also fix any `selected === item` reference comparison,
  which breaks as soon as the list is refetched.
- **Deprecated exports of a store.** A store consumed by non-Svelte code
  through `.subscribe()` should stay a store.

## Runes-mode behaviour changes that are not syntax

- **Classes are no longer auto-reactive.** In Svelte 4, assigning
  `foo.value = 1` invalidated everything referencing `foo`. In Svelte 5,
  reactivity is a runtime property: declare `value = $state(...)` as a class
  field. Wrapping `new Foo()` in `$state(...)` does nothing — only plain objects
  and arrays are proxied.
- **Bindings must be declared.** `bind:` to a prop requires `$bindable()`;
  binding to a component's exported value is no longer allowed.
- **`accessors` and `immutable` compiler options are ignored.**
- **Attribute and HTML parsing are stricter.** `<div foo={bar}">` and
  misplaced elements (a `<tr>` outside a `<tbody>`) that Svelte 4 tolerated now
  warn or error. These are pre-existing bugs the new compiler surfaces.
- **Touch and wheel events are passive** by default.
- **`null` and `undefined` render as the empty string** rather than the text
  "null".
- **Bindings react to form resets.**
- **Scoped CSS uses `:where(...)`**, so specificity no longer changes; and
  `:is()`, `:has()` and `:where()` contents are now scoped, which can turn a
  previously-working global selector into an unused-selector warning.

## Components are functions now

`mount(Component, { target, props })` and `hydrate(...)` replace
`new Component(...)`. The returned object has the component's exports, not
`$on` / `$set` / `$destroy`:

- `$on` → pass callbacks as props (the `events` option exists but is
  discouraged).
- `$set` → create the props object with `$state` in a `.svelte.js` module and
  mutate it.
- `$destroy` → `unmount(app)`.

## SvelteKit 1 → 2

The four that break silently or noisily:

- **`throw redirect(...)` / `throw error(...)` → `redirect(...)` / `error(...)`.**
  The functions throw by themselves.
- **`cookies.set` / `delete` / `serialize` require `path`.** Usually `'/'`.
  Omitting it now throws instead of silently scoping the cookie to the parent
  of the current path.
- **Top-level promises in `load` are no longer awaited automatically.** Await
  them yourself, or return them deliberately for streaming.
- **`goto(url)` no longer accepts external URLs.** Use
  `window.location.href = url`.

Also: `resolvePath` is replaced by `resolveRoute` from `$app/paths`;
`use:enhance` callbacks no longer receive `form` and `data` (use `formElement`
and `formData`); dynamic environment variables cannot be read during
prerendering. `npx sv migrate sveltekit-2` handles the mechanical parts.

## SvelteKit 2 → 3

SvelteKit 3 is the stable line (3.0.0 shipped on 2026-10-01) and svelte.dev
documents it; `2.70.x` remains in use. Detect the line from `package.json`
rather than assuming, and do not move a project to 3 as a side effect of
another task. Upgrade to the latest 2.x first so its deprecation warnings point
at what will break. These are the changes that break code rather than
configuration:

| Area | SvelteKit 2 | SvelteKit 3 |
|---|---|---|
| Svelte config | `svelte.config.js` (`kit.adapter`, `kit.experimental`) | options of the `sveltekit({...})` plugin in `vite.config.js`; former `kit.*` keys are top-level there |
| Environment | `$env/static/private`, `$env/dynamic/public` | `$app/env/private`, `$app/env/public`, declared with `defineEnvVars` in `src/env.js`; `$env/*` are deprecated aliases |
| App environment | `$app/environment` | `$app/env` |
| Lib alias | `$lib` | `#lib`, declared in `package.json` `imports`, with explicit module extensions |
| Page state | `$app/stores` (deprecated) + `$app/state` | `$app/stores` removed |
| Full invalidation | `invalidateAll()` | `refreshAll()`; `invalidateAll` deprecated |
| Navigation | `pushState` / `replaceState`; `goto` `noScroll` / `keepFocus` / `replaceState` / `invalidateAll` | `goto(url, { shallow: true, state })` (pushState/replaceState deprecated); `reset: false`, `replace`, `refreshAll` options |
| Cookie `path` | required | defaults to `'/'` |
| `error()` | `error(status, { message, ...props })` allowed | second argument must be the message string; extra props go in a third argument |
| `handleError` | called for unexpected errors only | called for every error with a `kind` (`app`, `framework`, `validation`, `unknown`) and may set `status`; `handleValidationError` removed |
| Failed form actions | enhanced responses return 200 | the status passed to `fail()` |
| Param matchers | `src/params/<name>.js` | consolidated into `src/params.js` with `defineParams` |
| Server-only dirs | recognised under `src/lib` | any `/server/` segment in the project |
| Types | `Handle` and friends from `@sveltejs/kit` | hooks types from `@sveltejs/kit/hooks`, remote function types from `$app/server`; `RequestEvent` and `Cookies` stay in `@sveltejs/kit` |
| Redirects | external redirects allowed | forbidden unless `redirect(..., { external })` opts in |
| Baseline | — | Node 22.17+, Vite 8.0.12+, TypeScript 6, Svelte 5.57.1+, `@sveltejs/vite-plugin-svelte` 7 |

`npx sv migrate sveltekit-3` runs as selectable tasks (`package-json` and
`tsconfig` are prerequisites; `svelte-config`, `environment`, `paths`,
`external-redirects`, `shallow-routing`, `params`, `app-state` are the rest).
Run one task per commit; the project is not expected to work until all
applicable tasks have run.

<!-- sources: svelte-core, sveltekit-core, sv-cli, svelte-ai-tools, spences10-svelte, ejirocodes-svelte5, svelte-dev-docs -->
