---
name: react
description: "Develops React and Next.js web applications, components and server rendering."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# react

Paths below are relative to this skill's directory.

## Scope

React 19+ application engineering and Next.js App Router (15/16+): component
boundaries, composition and state, the performance rule set, App Router
semantics, Cache Components, and shadcn/ui usage.

Not covered — do not answer from this skill:

- Visual and UX design decisions (palette, type scale, spacing, motion,
  accessibility audits). Those belong to the `frontend-design` skill.
- Vue, Svelte, Solid, Astro islands. Use the `vue`, `svelte` or `astro` skill.
- The React Native and Expo runtime — Hermes, the New Architecture, FlashList,
  navigation, EAS. Use the `react-native` skill.
- Pages Router feature work. Only the v16 `middleware.ts` → `proxy.ts` rename
  is covered, because it breaks App Router projects too.
- Test-runner mechanics, CI, container and cloud configuration beyond the three
  self-hosting facts in `references/nextjs-ops-and-debug.md`.
- Server-side Node frameworks — Fastify, NestJS, Hono, and the process,
  logging, shutdown and streams concerns around them. Use the
  `nodejs-backend` skill.
- Component API details of shadcn/ui. Those are fetched at task time from the
  CLI, never recalled from memory — see rule 16.

## Core rules

Each rule is an invariant: violating it is a bug or a measurable regression.
Rule ids in parentheses are the citable ids used by `## Output format`.

1. Detect the stack before advising: read `package.json` (`next` and `react`
   versions, and whether `babel-plugin-react-compiler` is present),
   `next.config.*` (`cacheComponents`), and `components.json` (a shadcn
   project, plus its `base`, `iconLibrary` and Tailwind version). Advice gated
   on the wrong stack is worse than no advice.
2. Start independent async work together and await it once — `Promise.all`, or
   create the promises first and await at the end (`async-parallel`). Each
   sequential `await` adds a full round trip; this is the single largest
   available win.
3. Import icons and components from their source path, or enable
   `optimizePackageImports` (Next.js 13.5+), never from a library's barrel
   entry (`bundle-barrel-imports`). Barrel entries pull thousands of modules
   into every cold start.
4. Load components that are not on the first paint on demand
   (`bundle-dynamic-imports`). A statically imported editor or chart ships to
   every visitor who never opens it.
5. Give sibling Server Components their own fetches instead of fetching in the
   parent (`server-parallel-fetching`). Siblings render concurrently; a
   parent's `await` blocks its whole subtree.
6. Pass only the fields the client component reads across the server/client
   boundary (`server-serialization`). Everything passed is serialized into the
   HTML and into every later RSC payload.
7. A Client Component is never `async` (`rsc-no-async-client`). Only Server
   Components may await; an `async` function under `'use client'` fails at
   runtime.
8. Put `'use client'` on the leaf that needs state, an event handler or a
   browser API — never on a page or layout (`rsc-boundary-at-leaves`). The
   directive is contagious downward: everything the file imports becomes client
   code.
9. Props crossing server → client must be JSON-serializable; functions marked
   `'use server'` are the only exception (`rsc-serializable-props`). A `Date`,
   `Map` or class instance crosses as plain data and then crashes on its first
   method call.
10. Verify authentication and authorization inside every Server Action
    (`server-auth-actions`). Actions are public endpoints; middleware, layout
    and page guards do not run when one is invoked directly.
11. Never define a component inside another component
    (`rerender-no-inline-components`). Each render creates a new component
    type, so React remounts it and destroys its state, focus and scroll.
12. Compute derived values during render; never mirror props or state into
    state with an effect (`rerender-derived-state-no-effect`). The effect adds a
    render pass and lets the copy drift.
13. Never mutate a prop or a state value in place — `toSorted`, `toReversed`,
    `with`, or an explicit copy (`js-tosorted-immutable`). In-place `sort`
    rewrites the caller's array.
14. Add a boolean prop only when it does not select a variant; a variant gets
    its own component composed from shared parts
    (`architecture-avoid-boolean-props`). Every boolean doubles the reachable
    state space, and most of it is unreachable by design.
15. Hold state at the narrowest scope that works, in this order: local →
    lifted → URL search params → server cache (SWR / React Query) → context →
    global store (`state-narrowest-scope`). Reaching for a store first makes
    every later read a subscription.
16. In a shadcn project, run `npx shadcn@latest info --json` before editing and
    `npx shadcn@latest docs <component>` before writing component code
    (`shadcn-fetch-context`). Component APIs change between releases; recalled
    APIs are the top source of broken shadcn code.
17. `className` carries layout only — never component colors or typography
    (`shadcn-classname-layout-only`). Colors come from variants and semantic
    tokens, which is what keeps dark mode and theming working.
18. Never choose a registry on the user's behalf; ask when the request does not
    name one (`shadcn-explicit-registry`). Registries ship different source
    code under the same component name.
19. Anything that differs between the server render and the first client render
    must be read after mount, or written by an inline script before hydration
    (`hydration-no-mismatch`). Reading `window`, `localStorage`, `Date` or
    `Math.random()` during render breaks hydration or flashes wrong content.
20. `suppressHydrationWarning` marks a difference you intend (a locale-formatted
    timestamp), never one you have not explained (`hydration-suppress-narrow`).
    Applied broadly it hides real mismatches.

## Workflows

**Stack detection (run first, every workflow).** The answers decide which rules
apply:

```bash
cat package.json                     # next / react versions, react-compiler
cat components.json 2>/dev/null      # shadcn project? base, iconLibrary, tailwind
grep -rn "cacheComponents\|reactCompiler" next.config.* 2>/dev/null
```

- No `next` dependency → skip every `nextjs-*` reference and rules 5, 6, 10.
- React Compiler enabled → skip the pure-memoization rule entries (keep the
  correctness ones); see the preamble of `references/rules-rendering-rerender.md`.
- `components.json` present → `references/shadcn-ui.md` governs class names.
- `next` below 16.3 → `make-route-instant` does not apply; say so instead of
  approximating it.

### implement-component

- [ ] Run stack detection.
- [ ] Place the file with its tests, hook and types colocated; see
      `references/architecture-and-state.md`.
- [ ] Decide the server/client split before writing JSX: data reads stay in
      Server Components, `'use client'` goes on the interactive leaf (rules 7–9).
- [ ] Choose the state location with the ladder in rule 15.
- [ ] Compose from parts rather than adding a boolean prop (rule 14); for the
      compound-component and context-interface shapes read
      `references/composition-patterns.md`.
- [ ] Handle the loading, empty and error state in the same pass — a component
      without all three is unfinished.
- [ ] Fetch data with the mechanism from
      `references/nextjs-data-and-caching.md` (Server Component read, Server
      Action write, Route Handler for external callers).
- [ ] **Gate — CONTRACT CHECK:** the project's typecheck and lint commands pass,
      no file under `'use client'` is `async`, and no non-serializable value
      crosses the boundary.

### review-performance

- [ ] Run stack detection; note the React and Next versions in the report
      header so version-gated findings are unambiguous.
- [ ] Read the files in full before judging. Report findings, do not rewrite
      the code unless asked.
- [ ] Walk the rule categories in impact order and record every hit with its
      rule id: async waterfalls → bundle → server → client fetching →
      re-render → rendering → JS → advanced. The rule bodies are in
      `references/rules-async.md`, `references/rules-bundle-client.md`,
      `references/nextjs-data-and-caching.md`,
      `references/rules-rendering-rerender.md` and
      `references/rules-js-advanced.md`.
- [ ] Check the RSC boundary separately (rules 7–10) against
      `references/nextjs-app-router.md`.
- [ ] Check composition and state debt against
      `references/composition-patterns.md` and
      `references/architecture-and-state.md`.
- [ ] Drop any finding whose fix costs more than it returns, and say what you
      dropped. A report that flags every `js-*` micro-rule buries the waterfall
      at the top.
- [ ] **Gate — CITED AND ORDERED:** every finding carries a `path:line`, a rule
      id and a fix; findings are ordered by impact, not by file order; the
      report matches `## Output format`. Take each id from the `Contents` list
      of the reference you actually read, not from the 20 ids in `Core rules` —
      those name one rule per category, and citing the nearest one instead of
      the right one (`rerender-derived-state-no-effect` for a non-lazy
      `useState`, which is `rerender-lazy-state-init`) makes the id useless.
      No id fits the finding? Use `correctness`.

### make-route-instant

Requires Next.js 16.3+ with `cacheComponents: true`. On an older version, say
so and offer the upgrade (`npx @next/codemod@latest upgrade latest`) instead of
approximating the workflow. Full recipes: `references/nextjs-cache-components.md`.

- [ ] Confirm the version floor and that `@next/playwright` matches the `next`
      release line.
- [ ] Establish the rig: a production build (`next build && next start`, a
      staging container, or a preview deploy) with the testing API exposed.
      Never measure on `next dev` — it does not prefetch.
- [ ] Baseline, unlocked: drive the real navigation as the test user and assert
      the shell marker renders. This proves the marker is reachable. Delete this
      scaffold before shipping.
- [ ] Red: wrap the same navigation in `instant()` and watch it fail. This is
      the test that ships.
- [ ] Verify the red is trustworthy: the marker renders without the lock, as
      the test user. A red for the wrong reason sends you optimizing a route
      that was never broken.
- [ ] Fix: hoist the static UI and push each `<Suspense>` down to the single
      read it guards. Reuse the route's existing `loading.tsx` or colocated
      skeleton instead of writing a new one.
- [ ] Confirm parity: same content, same redirects, same client state after the
      stream. Only whether the route is instant may change.
- [ ] **Gate — LOCKED GREEN AND DIFFERENTIAL:** the locked test passes on the
      production build, reverting only the fix turns it red again, and the
      committed shell contains real content — an `instant()` pass over
      `fallback={null}` is an empty shell, not an instant route.

### add-shadcn-component

- [ ] `npx shadcn@latest info --json` — read `aliases`, `isRSC`,
      `tailwindVersion`, `base`, `iconLibrary`, `resolvedPaths`,
      `packageManager`, and the installed component list. Use the project's own
      package runner from `packageManager` for every later command.
- [ ] Check the installed list before adding: do not re-add an installed
      component, and do not import one that is not installed.
- [ ] `npx shadcn@latest search <query>` when the needed component is unknown;
      never invent a component name.
- [ ] `npx shadcn@latest docs <component>` and read the returned pages before
      writing code (rule 16).
- [ ] `npx shadcn@latest add <component>` — with the registry the user named
      (rule 18). Preview an update to an existing file with `--dry-run` and
      `--diff`; `--overwrite` needs explicit approval.
- [ ] Re-read every added file: fix imports to the project's `aliases`, swap
      icon imports to the configured `iconLibrary`, and repair composition the
      registry got wrong (an item outside its group, a `Dialog` without a
      title).
- [ ] Apply the class conventions in `references/shadcn-ui.md` (rule 17).
- [ ] **Gate — CONVENTION SWEEP:** the touched files contain no `space-x-`,
      no `space-y-`, no equal `w-N h-N` pair, no manual `z-` on an overlay
      component, no hand-written `dark:` color override, and no raw palette
      color; every form field uses `Field` with `data-invalid` plus
      `aria-invalid` on the control.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Waterfalls, `Promise.all`, Suspense streaming | Any `await` appears in a review or a new data path | `references/rules-async.md` |
| Re-renders, memoization, hydration flicker, `<Activity>` | Reviewing or profiling a client component | `references/rules-rendering-rerender.md` |
| Bundle size, dynamic imports, preloading, client fetching, storage | Something heavy ships to the browser, or a client component fetches | `references/rules-bundle-client.md` |
| Hot-path JavaScript, refs, Effect Events, one-time init | A profile points at a loop or an effect that re-subscribes | `references/rules-js-advanced.md` |
| Compound components, context interfaces, lifted state, variants | A component grew boolean props or its state is trapped | `references/composition-patterns.md` |
| File layout, state selection, container/presentation split, form Actions | Starting a component or feature, or picking where state lives | `references/architecture-and-state.md` |
| Route files, segments, RSC boundary, directives, async `params`, runtime, `proxy.ts` | Writing or fixing anything under `app/` | `references/nextjs-app-router.md` |
| Read/write mechanism choice, Route Handlers, server caching, `after()` | Deciding how data moves, or reviewing server performance | `references/nextjs-data-and-caching.md` |
| Metadata and OG images, `next/image`, `next/font`, `next/script`, error and not-found files, Suspense bailout, parallel routes | Metadata, assets, error UI, modals, or a CSR-bailout warning | `references/nextjs-rendering.md` |
| Package bundling failures, Turbopack migration, bundle analysis, self-hosting, dev-server debugging | A build or runtime import error, or a deploy question | `references/nextjs-ops-and-debug.md` |
| Cache Components adoption, static shell, `use cache`, `instant()` guard | Running `make-route-instant`, or enabling `cacheComponents` | `references/nextjs-cache-components.md` |
| shadcn CLI, styling, forms, composition, icons, `base` vs `radix`, registries, theming | Any task in a project with `components.json` | `references/shadcn-ui.md` |

## Output format

Use exactly this shape for `review-performance`. No preamble, no summary of
what the code does — the reader wrote it.

```
## <path>

<path>:<line> - <rule-id>: <what is wrong>
  Impact: <what it costs, concretely>
  Fix: <the change, one or two lines of code when that is clearer than prose>

## <next path>
...

## Verdict
<counts by severity, then the one change to make first>
```

Rules with no id — a correctness bug the rule set does not name — use
`correctness` in the id position. Files that pass get one line:
`<path> - ✓ pass`.

Worked example:

```
## app/dashboard/page.tsx

app/dashboard/page.tsx:1 - rsc-boundary-at-leaves: 'use client' on the route entry
  Impact: the whole route opts out of server rendering; both fetches wait for
  hydration before they start.
  Fix: drop the directive here, await the data in the page, and move the editor
  toggle into a small client child.

app/dashboard/page.tsx:4 - bundle-barrel-imports: three charts imported from the
  recharts barrel entry
  Impact: pulls the library's full module graph into the client bundle and every
  cold start.
  Fix: add recharts to optimizePackageImports in next.config.ts, or import the
  chart modules directly.

## Verdict
1 boundary, 1 bundle, 0 correctness. Fix the 'use client' boundary first — the
bundle finding shrinks once the charts are behind a client leaf.
```

## Environment

- Node.js 20+; use the project's own package runner (`npm` / `pnpm` / `bun`)
  as reported by `packageManager`.
- Verification commands are the project's own: `next build`, `next dev`, plus
  its typecheck and lint scripts. Read `package.json` rather than assuming
  `npm test`.
- `make-route-instant` additionally needs `@next/playwright` on the same
  release line as `next`, and a production build — check with
  `npm ls next @next/playwright`.
- `add-shadcn-component` needs network access for `npx shadcn@latest`; there is
  no offline substitute, so say so rather than guessing component APIs.
