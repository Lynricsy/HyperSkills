---
name: svelte
description: "Develops Svelte and SvelteKit applications with runes, routing and server data flows."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# svelte

Paths below are relative to this skill's directory.

## Scope

Svelte 5 application code and SvelteKit 2 routes: the reactivity model, the
component and template surface, data loading, mutations, hooks, deployment
shape, testing, and migration from Svelte 4 / SvelteKit 1.

Not covered — do not answer from this skill:

- Visual and UX design decisions, Tailwind conventions, spacing and type
  scales, accessibility audits. Use the `frontend-design` skill.
- React and Next.js. Use the `react` skill. Vue and Nuxt: use the `vue` skill.
  Astro islands, content collections and hydration directives: use the `astro`
  skill.
- Type-layer modelling, `tsconfig` design and generic inference. Use the
  `typescript` skill; this skill covers only the Svelte-specific typing surface
  (`./$types`, `PageProps`, `App.Locals`, `App.Error`).
- Standalone Node server frameworks — Fastify, NestJS, Hono. Use the
  `nodejs-backend` skill. `+server.js` endpoints are covered here.
- Svelte 3 and 4 as a target. Legacy syntax appears only as the source side of
  a migration.
- Database, ORM and query design; component-library internals; hosting-provider
  configuration beyond which adapter to install.

## Core rules

Each rule is an invariant: violating it is a bug, a leak, or a measurable
regression. Rule ids in parentheses are the ids cited by `## Output format`.

1. Detect the stack before advising (`stack-detection`): read `package.json`
   for the `svelte` and `@sveltejs/kit` versions, `svelte.config.js` for
   `compilerOptions.runes` and any `experimental` flags, and the component
   itself for whether it is in runes or legacy mode. `2.70.x` is the stable
   SvelteKit line and svelte.dev documents it; `3.0.0-next.*` moves config into
   `vite.config.js`, replaces `$lib` with `#lib` and removes `$app/stores`.
   Advice for the wrong line does not merely underperform, it fails to build.
2. Never mix runes with legacy reactivity in one component
   (`no-mixed-modes`). `$state` beside `$:` or `export let` is a compile error.
   Mode is per file, so migrate a component completely or leave it alone.
3. Compute derived values with `$derived` / `$derived.by`, never with an
   `$effect` that assigns (`derived-not-effect`). A `$:` block that assigns to a
   variable is a derivation even though it was written as a statement — porting
   it to an effect adds a render pass and can loop.
4. Use `$state.raw` for values that are only ever replaced — API responses,
   poll results, large tables (`raw-for-replaced`). Deep reactivity costs a
   proxy per object; `$state.raw` is the answer, not a workaround for broken
   reactivity.
5. Effects never run on the server, so never wrap an effect body in
   `if (browser)` (`no-browser-guard-in-effect`). The guard hides the fact that
   the code is client-only and suppresses nothing.
6. Read every dependency unconditionally before branching or awaiting inside an
   effect (`read-deps-first`). `chart?.update(scheme)` never registers `scheme`
   when `chart` is nullish, and state read after an `await` is outside the
   tracking scope.
7. Pass state to functions and context as a getter, not a value
   (`state-by-reference`). JavaScript is pass-by-value; `setContext('user',
   data.user)` freezes the object that existed at init.
8. Two-way binding is opt-in: `let { value = $bindable() } = $props()`
   (`bindable-explicit`). Components report upward through callback props;
   `createEventDispatcher` is deprecated and its `.detail` wrapper is gone.
9. Render snippets, never interpolate them: `{@render children()}`, and
   `{@render header?.()}` when the prop is optional (`render-snippets`).
   `{children}` silently renders nothing.
10. Key every `{#each}` by a stable id, and compare list items by id
    (`keyed-each`). Without a key, a mid-list delete re-labels the survivors
    and destroys their component state, focus and scroll.
11. Prefer `{@attach fn}` over `use:action` for DOM and third-party library
    integration (`attach-over-action`). Attachments re-run when the state they
    read changes; actions do not.
12. Never hold per-user mutable state at module scope in an SSR app
    (`no-module-scope-state`). A server process is shared: `let lastEmail` in
    `+page.server.js` or `export const user = $state({})` in a `.svelte.js`
    module shows one visitor's data to the next. Use a cookie plus a database
    through `event.locals`, or context.
13. Never `export let` a `$state` variable that gets reassigned
    (`no-exported-reassigned-state`). The compiler rewrites references inside
    that file only; importers receive the signal object. Export a container and
    mutate it, or export accessors.
14. Keep secrets on the server twice over (`server-only-boundary`): import
    `$env/static/private` and `$lib/server/*` only from server files, and never
    return a secret from `load` — the return value is serialized into the HTML.
    `process.env` is not validated and not available on every adapter.
15. A universal `load` (`+page.js`) runs in the browser too
    (`universal-load-is-client`). Guard `window`, `document` and
    `localStorage` with `browser` from `$app/environment`, or read them in the
    component. Importing a server-only module here fails the build.
16. Server `load` and action return values are serialized with devalue, not
    JSON (`devalue-not-json`). `Date`, `Map`, `Set`, `BigInt`, `RegExp` and
    cyclical references cross intact — do not stringify them. Class instances
    need a `transport` transporter in `src/hooks.js`, or plain data instead.
17. Read route data with `let { data, form }: PageProps = $props()` and page
    state with `page` from `$app/state` (`runes-route-props`). `export let
    data` is legacy syntax; `$page` from `$app/stores` is deprecated.
18. A server `load` never tracks a URL it fetched, so declare
    `depends('app:x')` and call `invalidate('app:x')` (`explicit-depends`).
    Only universal `load` fetches register as dependencies; tracking server
    fetches would leak private URLs, and it was removed in SvelteKit 2.
19. Start independent work before `await parent()` (`no-parent-waterfall`).
    Layout and page `load` run concurrently until a `parent()` await serialises
    them.
20. `fail(400, {...})` for invalid input, `error()` for a page that cannot be
    served, `redirect(303, ...)` when done (`fail-not-error`). Routing
    validation through `error()` throws away everything the user typed. In
    SvelteKit 2 both `error()` and `redirect()` throw by themselves — drop the
    `throw`.
21. `cookies.set`, `cookies.delete` and `cookies.serialize` require an explicit
    `path` (`cookie-path`). SvelteKit 2 throws without it, because the browser
    default scopes the cookie to the parent of the current path.
22. A form posts to an action: `method="POST"`, an action in
    `+page.server.js`, and `use:enhance` imported from `$app/forms`
    (`form-actions-not-fetch`). A hand-rolled `fetch('?/login')` cannot read
    the typed result envelope, discards the server's messages, and stops
    working without JavaScript.
23. Authorise in `handle` or at the point of access, never behind
    `await parent()` (`auth-not-in-layout-load`). A child `load` that does not
    await its parent runs anyway, and `+server.js` never involves layouts.
24. Name the opt-in when recommending an experimental feature
    (`flag-experimental`). Remote functions (SvelteKit 2.27+) and `await`
    expressions (Svelte 5.36+) need `kit.experimental.remoteFunctions` and
    `compilerOptions.experimental.async`; enabling async changes effect
    ordering app-wide, so it is not a per-route choice.
25. Verify with the compiler, not by reading (`verify-with-tooling`):
    `npx @sveltejs/mcp svelte-autofixer <file>` on each touched `.svelte` file,
    then `npx sv check`. The autofixer names legacy syntax and non-reactive
    updates that look fine on the page.

## Workflows

**Stack detection (run first, every workflow).** The answers decide which rules
apply and which syntax is legal:

```bash
grep -E '"(svelte|@sveltejs/kit|vite|vitest)"' package.json
cat svelte.config.js 2>/dev/null            # runes flag, adapter, experimental
grep -rlE '\$:|export let|on:[a-z]+=|<slot' src --include=*.svelte | head
```

- No `@sveltejs/kit` → skip every `sveltekit-*` reference; the route rules do
  not apply.
- `@sveltejs/kit` on `3.0.0-next.*` → read the version table at the end of
  `references/migration.md` before writing config, env imports or `$lib` paths.
- Legacy-mode files present → the task is a migration, not a bug fix. Say so
  rather than half-converting one component.
- `experimental.async` or `experimental.remoteFunctions` already on → those
  APIs are in scope; otherwise mention the flag before using them.

### implement-component

- [ ] Run stack detection.
- [ ] Fetch the API surface you are unsure about rather than recalling it:
      `npx @sveltejs/mcp list-sections` then
      `npx @sveltejs/mcp get-documentation "<section>,<section>"`.
- [ ] Decide what is reactive. Only values something reactive reads get
      `$state`; values only ever replaced get `$state.raw` (rules 4, 3).
- [ ] Write the props line first — `$props()` with defaults, `$bindable()` only
      where the parent must write back, callback props for events (rule 8).
- [ ] Express composition with snippets and `children`, not boolean props
      (`references/components-and-templates.md`).
- [ ] Put DOM and library integration in `{@attach ...}`; keep `$effect` for
      things that are genuinely outside Svelte (rules 11, 5, 6).
- [ ] Decide where the state lives before sharing it — props, then ancestor
      `$state`, then context; module scope needs a reason
      (`references/state-sharing-and-ssr.md`, rule 12).
- [ ] Handle loading, empty and error states in the same pass; wrap risky
      subtrees in `<svelte:boundary>` with a `failed` snippet.
- [ ] **Gate — COMPILER CLEAN:** `npx @sveltejs/mcp svelte-autofixer` reports
      no issues for each new or edited `.svelte` file, and `npx sv check`
      passes.

### implement-route

- [ ] Run stack detection.
- [ ] Place each read: server resources or secrets → `+page.server.js`; public
      API called directly from the browser or a non-serializable return value →
      `+page.js`; an HTTP contract for a third party → `+server.js` (rules 14,
      15, and `references/sveltekit-routing-and-load.md`).
- [ ] Check what crosses the boundary: devalue types pass, class instances need
      `transport` or flattening (rule 16).
- [ ] Start independent fetches before `await parent()` (rule 19); stream the
      slow property instead of blocking the shell.
- [ ] Declare `depends()` for anything that must be re-runnable, and pick the
      narrowest invalidation call (rule 18).
- [ ] Write mutations as form actions: `fail` / `error` / `redirect(303)`,
      cookies with `path`, `use:enhance` from `$app/forms`
      (`references/sveltekit-forms-and-mutations.md`, rules 20–22).
- [ ] Put session resolution in `handle` and the authorisation check at each
      read or write (rule 23, `references/sveltekit-hooks-and-deployment.md`).
- [ ] Read the data with `$props()` and `page` from `$app/state` (rule 17).
- [ ] **Gate — WORKS WITHOUT JAVASCRIPT:** the mutation path is a real
      `<form method="POST">` whose action succeeds with `use:enhance` removed,
      no secret appears in the rendered payload, and `npx sv check` passes.

### migrate-to-runes

Full procedure and the translation table: `references/migration.md`.

- [ ] Confirm a clean git tree — `sv migrate` refuses a dirty one, and that
      refusal is the only undo.
- [ ] `npx sv migrate svelte-5`, then review the diff before touching
      anything.
- [ ] Grep for `svelte/legacy` and `@migration-task`. Every `run(...)` is an
      unresolved question: decide `$derived` or `$effect` per site (rule 3).
      Every `preventDefault(...)` wrapper becomes an inline call.
- [ ] Convert what the script refuses to: `createEventDispatcher` to callback
      props, `beforeUpdate`/`afterUpdate` to `$effect.pre` plus `tick()`.
- [ ] Make the judgement calls the script cannot: `$state` vs `$state.raw`,
      store → context vs store → module state, unkeyed `{#each}`,
      identity comparisons against list items (rules 4, 10, 12).
- [ ] Leave stores that non-Svelte code consumes through `.subscribe()` alone.
- [ ] Set `compilerOptions.runes: true` last, so anything missed becomes a
      compile error.
- [ ] **Gate — NO LEGACY RESIDUE:** no `svelte/legacy` import, no
      `@migration-task` comment, no `$:` / `export let` / `on:` / `<slot`
      remaining in migrated files, `npx sv check` passes, and the autofixer is
      clean on each converted component.

### debug-reactivity

For "the UI does not update", "the effect runs too often", "it works on reload
but not on navigation".

- [ ] Run stack detection: a legacy-mode component and a runes-mode component
      fail for different reasons.
- [ ] Confirm the value is reactive at all — a plain `let` mutated in a handler
      updates nothing in runes mode.
- [ ] Add `$inspect.trace('label')` as the first statement of the suspect
      `$effect` or `$derived.by` and read which dependency fired. Do not bisect
      by commenting code out.
- [ ] Walk the tracking traps in order: optional chaining short-circuit, read
      after `await`, destructured snapshot, state passed by value (rule 6, 7).
- [ ] For "stale after navigation", check the route layer instead: SvelteKit
      reuses the component across param changes, `data` is replaced rather than
      mutated, and a server `load` does not track its fetches (rules 17, 18).
- [ ] For "wrong on the server / flashes on hydration", look for module-scope
      state and for context updated from a descendant during SSR (rule 12).
- [ ] **Gate — CAUSE NAMED AND PROVEN:** the answer names the specific
      dependency or boundary at fault, and a test reproduces it —
      `$effect.root` plus `flushSync` for a rune, a component test for a
      component (`references/testing.md`).

### review-svelte

- [ ] Run stack detection and state the versions in the report header;
      version-gated findings are otherwise unfalsifiable.
- [ ] Read each file completely before judging. Report findings; do not rewrite
      unless asked.
- [ ] Walk the categories in blast-radius order and record every hit with its
      rule id: cross-request state leaks and secret exposure (rules 12, 14) →
      server/client boundary (15, 16) → auth placement (23) → mutation
      correctness (20, 21, 22) → reactivity correctness (2–7) → template
      correctness (9, 10) → invalidation and waterfalls (18, 19) → legacy
      residue (11, 17).
- [ ] Drop findings whose fix costs more than they return, and say which.
- [ ] **Gate — CITED AND ORDERED:** every finding carries `path:line`, a rule id
      and a fix; findings are ordered by blast radius, not file order. Take the
      id from the `Contents` list of the reference you actually read; if none
      fits, use `correctness`.

## Topic router

| Topic | Read when | File |
|---|---|---|
| `$state`, `$state.raw`, `$derived`, `$effect` variants, tracking traps, `$props`, `$bindable`, reactive classes, `.svelte.js` modules, `createSubscriber`, `$inspect.trace` | Writing or debugging any reactive value | `references/runes-and-reactivity.md` |
| Snippets and `{@render}`, `{@attach}`, keyed each, bindings, events, dynamic components, `<svelte:boundary>`, scoped CSS, `class` arrays | Writing or reviewing component markup | `references/components-and-templates.md` |
| Module-scope leaks, `createContext`, reactivity across the context boundary, stores vs runes, URL and snapshot state | State needs to be shared, or an SSR app shows the wrong user's data | `references/state-sharing-and-ssr.md` |
| Route files, universal vs server `load`, devalue and `transport`, `$app/state`, waterfalls, streaming, `depends`/`invalidate`, page options, `+server.js` | Anything under `src/routes` that reads data | `references/sveltekit-routing-and-load.md` |
| Form actions, `fail`/`error`/`redirect`, cookies, `use:enhance`, `applyAction`, `deserialize`, remote functions | Anything that writes data | `references/sveltekit-forms-and-mutations.md` |
| `handle`, `locals`, `resolve` options, `handleFetch`, `handleError`, `reroute`, `init`, adapters, prerendering, auth placement | Cross-cutting server behaviour, deployment target, or an error contract | `references/sveltekit-hooks-and-deployment.md` |
| Vitest client/server projects, filename rules, `$effect.root` and `flushSync`, `vitest-browser-svelte` locators, testing `load` and actions, Playwright, `sv check` | Writing or fixing a test, or closing any workflow gate | `references/testing.md` |
| Svelte 4 → 5 table, `sv migrate` output, `svelte/legacy` escape hatches, runes-mode behaviour changes, SvelteKit 1 → 2, SvelteKit 3 differences | Porting old code, or the project is on `3.0.0-next.*` | `references/migration.md` |

## Output format

Use exactly this shape for `review-svelte`. No preamble and no summary of what
the code does — the reader wrote it.

```
## <path>

<path>:<line> - <rule-id>: <what is wrong>
  Impact: <what it costs, concretely>
  Fix: <the change, one or two lines of code when that is clearer than prose>

## <next path>
...

## Verdict
<counts by category, then the one change to make first>
```

A correctness bug the rule set does not name uses `correctness` in the id
position. Files that pass get one line: `<path> - ✓ pass`.

Worked example:

```
## src/routes/login/+page.server.ts

src/routes/login/+page.server.ts:6 - no-module-scope-state: `let lastEmail` at
  module scope
  Impact: one value for the whole server process — the next visitor's login page
  is prefilled with the previous visitor's email address.
  Fix: store it in a cookie, or drop the prefill.

src/routes/login/+page.server.ts:21 - fail-not-error: `error(400, ...)` for a
  missing field
  Impact: renders +error.svelte and discards everything the user typed.
  Fix: `return fail(400, { email, missing: true })` and render the message from
  the `form` prop.

## Verdict
1 cross-request leak, 1 mutation, 0 reactivity. Fix the module-scope state
first — it is a data leak, not a UX problem.
```

## Environment

- Node.js 18.13+ for SvelteKit 2; use the project's own package runner
  (`npm` / `pnpm` / `bun` / `yarn`) as declared by `packageManager`.
- `npx sv check` needs `svelte-check` in the project's devDependencies
  (`npm i -D svelte-check`).
- `npx sv add vitest` and `npx sv add playwright` generate the test setup;
  browser-mode tests need Playwright's browsers installed
  (`npx playwright install chromium`).
- `npx @sveltejs/mcp list-sections`, `get-documentation "<sections>"` and
  `svelte-autofixer <file-or-code>` are the official CLI for current
  documentation and compiler diagnostics. They require network access on first
  run; when the network is unavailable, say that the API surface could not be
  confirmed rather than recalling it. Passing inline code through a shell needs
  `$` escaped as `\$` so runes survive.
