---
name: astro
description: "Engineers Astro 7 sites: project and route structure including dynamic routes and getStaticPaths, island boundaries and the client:* hydration directives, server islands with server:defer, content collections and the content layer (glob/file loaders, schemas, live collections), output modes and SSR adapters, astro:actions and the HTML form contract, middleware, sessions and astro:env, view transitions with the ClientRouter component, integrations and Vite configuration, image and font optimisation, route caching, and the Astro 5/6/7 removals that a remembered answer still uses. Applies when writing, reviewing, debugging or upgrading Astro code, deciding what to hydrate, or auditing a page that ships too much JavaScript. Do not use for the internal implementation of the framework component inside an island, or for visual design decisions."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# astro

Paths below are relative to this skill's directory.

## Scope

Astro application engineering, written against **Astro 7.3**: project and route
structure, the island model in both directions (`client:*` and `server:defer`),
content collections and the content layer, output modes and adapters,
`astro:actions`, middleware, sessions, `astro:env`, view transitions,
integrations and Vite configuration, images and fonts, route caching, the build
and CLI, and migration from Astro 4/5/6.

The dividing line for islands: this skill owns the **boundary** — which
component becomes an island, which directive it gets, what crosses as props,
what state can be shared, and what the framework renders on the server. It does
not own what happens inside that component.

Not covered — do not answer from this skill:

- The internals of a React island: hooks, effects, context, memoisation,
  re-render behaviour, Next.js. Use the `react` skill.
- The internals of a Vue island: Composition API, reactivity, Pinia, Nuxt. Use
  the `vue` skill.
- The internals of a Svelte island: runes, stores, SvelteKit. Use the `svelte`
  skill.
- Visual and UX design decisions — palette, type scale, spacing, motion design,
  accessibility audits. Use the `frontend-design` skill. This skill covers
  `<Image />`, `<Font />` and `compressHTML` as build mechanics only.
- Type-layer modelling, `tsconfig` strategy and generic design. Use the
  `typescript` skill; this skill covers `astro sync` and the generated
  collection types.
- Standalone Node server frameworks (Fastify, NestJS, Hono as an application
  framework). Use the `nodejs-backend` skill; this skill covers `astro/hono`
  only as an advanced-routing entrypoint.
- Preact, SolidJS and Alpine island internals, Starlight theming, the Astro
  monorepo's own contributor workflow, and REST/OpenAPI contract design. None of
  these has a skill in this library yet; say so rather than improvising.

## Read first

`references/removed-and-changed-apis.md` before writing or reviewing any Astro
API from memory. Most incorrect Astro output is a correct Astro 4 or 5 answer:
`output: 'hybrid'`, `entry.slug`, `post.render()`, `Astro.glob()`,
`<ViewTransitions />`, `z` from `astro:content`, `type: 'content'`. Each of
those is removed, and each one fails at build time in a project that has
upgraded.

## Core rules

1. Read `package.json` (the `astro` version, the adapter, the installed
   renderers), `astro.config.*` (`output`, `adapter`, `integrations`, any
   `experimental` block) and check whether `src/content.config.ts`,
   `src/actions/`, `src/middleware.ts` and `src/live.config.ts` exist, before
   advising anything. Every rule below branches on those answers.
2. A framework component with no `client:*` directive ships no JavaScript at
   all. When a component has no event handler, no local state and no browser
   API, delete the directive instead of downgrading it — a downgrade still
   ships the framework runtime, just later.
3. Match the directive to when the visitor needs it: `client:load` above the
   fold, `client:visible` below it, `client:media` for viewport-conditional UI.
   `client:visible` on an element already on screen is `client:load` plus an
   observer, and `client:idle` can be minutes late on a busy low-end device.
4. `client:visible` accepts `rootMargin` and nothing else; `client:idle` accepts
   `timeout`. An invented option is silently ignored, so it reads as working
   code that never takes effect.
5. Each `client:*` directive creates a separate root. A context provider cannot
   reach a consumer in another island — hydrate one subtree containing both, or
   share through URL state, a store module or custom events.
6. Props crossing into an island are serialised into the HTML and again into the
   hydration payload. Pass the fields the island reads, not the record they came
   from, and never a function: a callback prop works during server rendering and
   is simply missing on the client.
7. `client:only` skips server rendering entirely, so it needs the framework name
   and a `slot="fallback"`. Use it only when server rendering genuinely fails.
8. Per-request data on an otherwise cacheable page belongs in a `server:defer`
   island with fallback content, not in the page. Keep its props small: past
   roughly 2 KB of encrypted query string Astro switches to `POST`, which is not
   browser-cached and deletes the reason for the island.
9. `output` accepts `'static'` or `'server'` only. `'hybrid'` was removed; the
   mixed site is the default `'static'` plus `export const prerender = false` on
   the routes that need a server.
10. Any on-demand rendering requires an adapter — and so do server islands and
    sessions, even on a site that is otherwise entirely static.
11. A route that reads cookies, request headers, sessions, or a form submission
    needs `export const prerender = false`. Left prerendered it reads those at
    build time and bakes the answer into HTML without erroring.
12. Collections live in `src/content.config.ts`, every collection has a
    `loader`, `z` comes from `astro/zod`, the routing key is `entry.id`, and
    rendering is the standalone `render(entry)`. There is no `type:`, no
    `entry.slug` and no `entry.render()`.
13. `getCollection()` returns entries in an unspecified, platform-dependent
    order. Sort explicitly whenever the order is visible.
14. Run `astro sync` after touching `content.config.ts`, `live.config.ts`, the
    config or an integration. A stale `.astro/types.d.ts` is the usual cause of
    a type error that appears immediately after a correct edit.
15. In `getStaticPaths()`, `params` values are strings, they are not
    URL-decoded, and the `Astro` global is unavailable — use
    `import.meta.env.SITE` for `Astro.site`. On-demand dynamic routes must not
    export it at all, and therefore cannot receive `props`.
16. A form posting to an action needs four things together: `prerender = false`
    on the page, `accept: 'form'` on the action, `method="POST"` with
    `action={actions.name}`, and `enctype="multipart/form-data"` when a file
    input is validated by `z.instanceof(File)`. Each one fails silently alone.
17. Every action is a public endpoint at `/_actions/<name>`. Authorize inside
    every handler; a page guard or middleware check does not cover the direct
    call.
18. Middleware exports a named `onRequest` (never a default), returns a
    `Response` or the result of `next()`, and shares data only through
    `context.locals`. `next(path)` rebuilds the `Request`, so reading the body
    around it throws — rewrite from the page with `Astro.rewrite()` when a form
    is involved.
19. Set status, headers and redirects at page level only. On-demand rendering
    streams, so by the time a component or layout runs the response line is
    already sent.
20. With `<ClientRouter />`, bundled module scripts execute once per session.
    Move setup into an `astro:page-load` listener, or mark an inline script
    `data-astro-rerun`; a `DOMContentLoaded` listener never fires again after
    the first navigation.
21. `transition:persist` keeps an island's state but re-renders it with the
    destination page's props. Add `transition:persist-props` when the original
    props must survive too.
22. `<Image />` and `<Picture />` require `alt`, infer dimensions only from an
    imported `src`, always crop, and never upscale. `getImage()` is server-only
    and throws in the browser — call it in frontmatter and pass `src` down.
23. Astro 7's Rust compiler errors on unclosed non-void tags and no longer
    repairs invalid nesting, and `compressHTML: 'jsx'` strips whitespace around
    elements — write `{" "}` where a space between inline elements is meaningful.
24. Verify against `astro build && astro preview`, never `astro dev`.
    Prerendering, adapters, route caching (`cache.enabled` is always `false` in
    dev), sessions and asset hashing behave differently in a build.

## Workflows

**Stack detection (run first, every workflow).**

```bash
cat package.json                                   # astro version, adapter, renderers
cat astro.config.* 2>/dev/null                     # output, adapter, integrations, experimental
ls src/content.config.* src/live.config.* src/middleware.* src/actions 2>/dev/null
ls src/fetch.* 2>/dev/null                         # reserved filename in Astro 7
```

- No `adapter` → nothing renders on demand; server islands, sessions and form
  actions are unavailable until one is added.
- An `experimental` block → check it against
  `references/removed-and-changed-apis.md`; most former flags are now build
  errors.
- Astro below 6 → the removals in that reference have not landed yet; say which
  version the advice targets instead of assuming the current API.

### implement-feature

- [ ] Run stack detection.
- [ ] Decide the rendering mode per route before writing markup: prerendered,
      on demand (`prerender = false`), or prerendered shell plus `server:defer`
      island. `references/routing-and-rendering.md` has the route mechanics.
- [ ] Model the data source: a build-time collection, a live collection, or a
      direct fetch. Define the loader and schema first —
      `references/content-collections.md`.
- [ ] Write the page in `.astro`, static by default. Add interactivity only at
      the leaf that needs it, choosing the directive by rule 3.
- [ ] Handle the loading, empty and error state in the same pass, including the
      `slot="fallback"` of any deferred island.
- [ ] For mutations, add an action rather than an endpoint unless an external
      caller needs the HTTP contract —
      `references/actions-middleware-and-env.md`.
- [ ] **Gate — BUILD AND PREVIEW:** `astro check` and `astro build` pass, and
      the route behaves correctly under `astro preview` (not `astro dev`) with
      the states above exercised.

### audit-hydration

Use when a page ships more JavaScript than it should, or a review touches
`client:*` directives.

- [ ] Run stack detection and note the Astro version in the report header.
- [ ] Read the whole page and the components it hydrates. Report findings; do
      not rewrite unless asked.
- [ ] Walk the six checks in the order given at the end of
      `references/islands-and-hydration.md` — deletions first, then directive
      downgrades, then script replacements, then prop narrowing, then island
      boundaries, then `server:defer` candidates. That order is by payload saved
      per edit.
- [ ] Separately check the island boundary for correctness, not weight: a
      provider split from its consumers, a function passed as a prop, a
      non-serialisable value, a `client:only` without a fallback.
- [ ] Check assets in the same pass — an unimported `src`, a missing `layout`,
      a `preload`ed font that is not above the fold
      (`references/assets-integrations-and-build.md`).
- [ ] Drop any finding whose fix costs more than it saves, and say what was
      dropped.
- [ ] **Gate — CITED AND ORDERED:** every finding carries `path:line`, the
      concrete replacement and what it saves; findings are ordered by impact,
      not file order; the report matches `## Output format`.

### wire-a-form

- [ ] Confirm the page is on demand and an adapter is installed.
- [ ] Define the action with `accept: 'form'` and a Zod schema using the
      form-input conventions (`z.coerce.boolean()` for a checkbox,
      `z.instanceof(File)` for a file, `z.array(…)` for a repeated name).
- [ ] Decide the submission path: form `action={actions.x}` for zero-JS, or
      `actions.x(formData)` from a script or island. Do not mix both for one
      form.
- [ ] Read the result server-side with `Astro.getActionResult()` and handle
      success (redirect or confirmation) and failure separately.
- [ ] Render field errors from `isInputError(result?.error).fields`, keeping the
      native HTML validation attributes as the first pass.
- [ ] Add the authorization check inside the handler, and throw `ActionError`
      with a code rather than returning `undefined`.
- [ ] **Gate — SUBMITS WITHOUT JAVASCRIPT:** on a production build with
      scripting disabled, a valid submission reaches the handler and an invalid
      one re-renders the form with the field message.

### upgrade

- [ ] Establish the current and target versions and read the release the project
      is jumping over — the removals differ between 5→6 and 6→7.
- [ ] Work `references/removed-and-changed-apis.md` in the order of its
      "Upgrade order" checklist; it is ordered so each step's failures are
      attributable.
- [ ] Keep behaviour changes out of the upgrade diff, so any post-upgrade
      failure points at the upgrade.
- [ ] **Gate — CLEAN BUILD AND MATCHED OUTPUT:** `astro check` and
      `astro build` pass with no `experimental` block remaining, and a
      spot-check of rendered pages shows no whitespace or Markdown differences
      beyond the ones deliberately accepted.

### diagnose

- [ ] Classify first: build error, wrong content, missing interactivity, or a
      value that is correct in dev and wrong in production. They have different
      first moves.
- [ ] Build error → check the removed-API table before reading the stack trace;
      the second most common cause is an unclosed tag from the Rust compiler.
- [ ] Wrong content or a stale value in production → check whether the route is
      prerendered. A build-time answer baked into static HTML is the single most
      common Astro bug and it never throws.
- [ ] Missing interactivity → confirm the directive is on a framework component
      imported directly into `.astro`, then check the island boundary (rule 5)
      and prop serialisation (rule 6).
- [ ] Works on first load, broken after navigating → `<ClientRouter />` script
      re-execution (rule 20), `references/view-transitions.md` has the
      symptom table.
- [ ] Collection or type error → `astro sync`, then the failure-mode table in
      `references/content-collections.md`.
- [ ] **Gate — CAUSAL CHAIN:** the explanation runs from an observed error or
      rendered output to the fix, and the same observation is repeated after the
      change on a production build.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Removed and changed APIs, version floors, upgrade order | Before writing any API from memory; any upgrade or build error | `references/removed-and-changed-apis.md` |
| `client:*` directives, island boundaries, shared state, prop serialisation, `server:defer`, `<script>` | Adding or auditing interactivity, or a page that ships too much JavaScript | `references/islands-and-hydration.md` |
| `content.config.ts`, loaders, schemas, references, querying, `render()`, live collections | Any content-driven page, or a collection error | `references/content-collections.md` |
| Project shape, `output`, adapters, `prerender`, dynamic routes, pagination, redirects/rewrites, endpoints, route caching, `src/fetch.ts` | Deciding how a route renders, or adding/fixing a route | `references/routing-and-rendering.md` |
| `astro:actions`, form contracts, field errors, middleware, sessions, `astro:env` | Any mutation, request interception, per-user state, or typed configuration | `references/actions-middleware-and-env.md` |
| `<ClientRouter />`, `transition:*`, lifecycle events, script re-execution | Enabling client-side routing, or something that breaks only after navigating | `references/view-transitions.md` |
| `<Image />`, `<Picture />`, responsive layout, fonts, integrations, Vite config, Markdown processor, CLI, testing | Assets, an integration, a build/CLI question, or setting up tests | `references/assets-integrations-and-build.md` |

## Output format

Use exactly this shape for `audit-hydration` and any other report on existing
code. No preamble and no summary of what the code does — the reader wrote it.

```
## <path>

<path>:<line> - <category>: <what is wrong>
  Cost: <what it ships or breaks, concretely>
  Fix: <the change; one or two lines of code when clearer than prose>

## <next path>
...

## Verdict
<counts by category, then the one change to make first>
```

Categories: `correctness` (broken behaviour — a provider split across islands, a
function prop, a prerendered route reading cookies), `payload` (JavaScript or
bytes that need not ship), `removed-api` (an API this Astro version no longer
has), `minor` (naming, dead code, style). Files that pass get one line:
`<path> - ✓ pass`.

Worked example:

```
## src/pages/products/[id].astro

src/pages/products/[id].astro:26 - payload: SiteNav hydrated with client:load for a
  hamburger toggle
  Cost: ships the React runtime plus the nav component on every page load.
  Fix: drop the directive and toggle the class from a <script> in the .astro file.

src/pages/products/[id].astro:29 - correctness: CartProvider and AddToCart each carry
  client:load, so they are separate island roots and useCart() sees no provider
  Cost: the cart button is inert; the count in the header never updates.
  Fix: hydrate one CartIsland containing both, and move the header count to a shared
  store rather than context.

src/pages/products/[id].astro:35 - payload: ReviewList and RelatedGrid use client:load
  at the bottom of the page
  Cost: ~180 KB downloaded before the visitor scrolls to them.
  Fix: client:visible={{ rootMargin: "200px" }}.

## Verdict
2 payload, 1 correctness, 0 removed-api. Fix the island boundary first — the cart is
broken, not just heavy.
```

## Environment

Node.js 22.12+; use the project's own package runner (`npm` / `pnpm` / `yarn` /
`bun`).

```bash
npx astro dev          # detaches under an AI agent: astro dev status | logs -f | stop
npx astro build        # production build
npx astro preview      # the only local runtime that matches production
npx astro check        # types and diagnostics
npx astro sync         # regenerate .astro/types.d.ts
npx astro add <name>   # install and wire an integration
npx @astrojs/upgrade   # Astro plus every official integration together
npx astro create-key   # stable ASTRO_KEY for server islands
```

Version-sensitive APIs change between minors. When a project pins a version this
skill was not written against, fetch the current behaviour from
<https://docs.astro.build> rather than recalling it.
