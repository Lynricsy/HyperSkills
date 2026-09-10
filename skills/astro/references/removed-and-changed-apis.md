# Removed and changed APIs

Verified against: Astro 7.3

Read this before writing Astro code from memory. Most wrong Astro output is not
invented — it is a correct Astro 4 or 5 answer that no longer runs.

## Contents

- [Version floors](#version-floors)
- [Removed: replace on sight](#removed-replace-on-sight)
- [Changed defaults](#changed-defaults)
- [Experimental flags that no longer exist](#experimental-flags-that-no-longer-exist)
- [Integration and adapter APIs](#integration-and-adapter-apis)
- [Upgrade order](#upgrade-order)

## Version floors

| | Requirement |
|---|---|
| Node | 22.12+ (18 and 20 dropped in Astro 6) |
| Vite | 8 in Astro 7, 7 in Astro 6 |
| Zod | 4 (Astro 6+) |
| Config file | `.mjs`, `.js`, `.ts`, `.mts` — CommonJS config removed |
| Compiler | Rust (`@astrojs/compiler-rs`), strict about invalid HTML |

## Removed: replace on sight

| Old | Current |
|---|---|
| `output: 'hybrid'` | `output: 'static'` (default) + `export const prerender = false` per route |
| `src/content/config.ts` | `src/content.config.ts` |
| `defineCollection({ type: 'content' \| 'data' })` | `defineCollection({ loader: glob(…) \| file(…) })` |
| `legacy.collections` flag | Nothing; the content layer is the only implementation |
| `entry.slug` | `entry.id` |
| `getEntryBySlug()`, `getDataEntryById()` | `getEntry()` |
| `entry.render()` | `render(entry)` from `astro:content` |
| `z` from `astro:content`, `astro:schema` | `z` from `astro/zod` |
| `z.string().email()`, `z.string().url()` | `z.email()`, `z.url()` (Zod 4) |
| `{ message: "…" }` in a Zod validator | `{ error: "…" }` |
| `Astro.glob()` | `import.meta.glob()` — returns an object, not a promise |
| `<ViewTransitions />` | `<ClientRouter />` from `astro:transitions` |
| `handleForms` prop on the router | Nothing; form handling is always on |
| `TRANSITION_*` constants, `isTransitionBeforePreparationEvent()`, `createAnimationScope()` | Compare `event.type` to `'astro:before-preparation'` etc.; drop the scope helper |
| `Astro.site` / `Astro.generator` inside `getStaticPaths()` | `import.meta.env.SITE`; no replacement for `generator` |
| `getStaticPaths()` returning numeric `params` | Strings only |
| `serializeActionResult()` / `deserializeActionResult()` imports | Obtain both from `getActionContext()` |
| `rewrite()` on the action context | Rewrite from the page with `Astro.rewrite()` |
| Session driver as a bare string | `sessionDrivers.<driver>(…)` from `astro/config` |
| Session `test` driver | Nothing |
| `import.meta.env.ASSETS_PREFIX` | `build.assetsPrefix` from `astro:config/server` |
| `emitESMImage()` | `emitImageMetadata()` |
| `prefetch()` `with` option | Nothing |
| `@astrojs/db`, `astro db/login/logout/link/init` | `node:sqlite`, Drizzle, or a hosted database |
| `@astrojs/tailwind` | `@tailwindcss/vite` plus `@import "tailwindcss"` |
| `%25` in a route filename | Rename the route |
| `experimental.rustCompiler`, `queuedRendering`, `advancedRouting`, `cache`, `routeRules`, `logger` | Remove the flag; see below |

## Changed defaults

| Behaviour | Now |
|---|---|
| `compressHTML` | `'jsx'` — whitespace around elements is stripped; write `{" "}` to keep a needed space |
| Markdown processor | Sätteri; remark/rehype needs `@astrojs/markdown-remark` + `markdown.processor: unified()` |
| `<script>` / `<style>` order | Rendered in source order |
| `import.meta.env` | Always inlined at build time |
| Markdown heading ids | Trailing hyphen where the old algorithm dropped one; hand-written anchors may need updating |
| Image service | Always crops, never upscales; rasterises SVG when a raster format is requested |
| `getImage()` | Throws when called on the client |
| `Astro.url.pathname` | Normalised/decoded; use `new URL(Astro.request.url).pathname` for the raw form |
| `i18n.routing.redirectToDefaultLocale` | Default changed in Astro 6 — set it and `prefixDefaultLocale` explicitly |
| Endpoints with a file extension | Not reachable with a trailing slash |
| `src/fetch.ts` | Reserved filename (advanced routing); rename yours or set `fetchFile` |
| `astro dev` under an agent | Detaches to the background; manage with `astro dev status/logs/stop` |

## Experimental flags that no longer exist

Stable and unconditional as of Astro 7: `csp` (now `security.csp`), `fonts`
(now top-level `fonts`), `staticImportMetaEnv`, `preserveScriptOrder`,
`headingIdCompat`, `rustCompiler`, `queuedRendering`, `advancedRouting` (now
top-level `fetchFile`), `cache` and `routeRules` (now top-level), `logger` (now
top-level). Actions, server islands, sessions and the content layer left
`experimental` earlier still.

An `experimental` block naming any of these is a build error, not a no-op.
Delete the block; move `cache`, `routeRules`, `logger` and `fetchFile` to the
top level.

Still experimental in 7.x: `chromeDevtoolsWorkspace`, `clientPrerender`,
`collectionStorage`, `contentIntellisense`, `incrementalBuild`,
`svgOptimization`. Confirm any of these against the experimental-flags reference
before recommending them.

## Integration and adapter APIs

Relevant when a project has a local integration or a pinned community adapter:

| Old | Current |
|---|---|
| `routes` on `astro:build:done` | `astro:routes:resolved` hook; `distURL` from the `assets` map |
| `entryPoints` on `astro:build:ssr` | Removed |
| `astro:ssr-manifest` virtual module | `astro:config/server` |
| `RouteData.generate()` | Removed |
| `app.render(request, routeData, locals)` | `app.render(request, { routeData, locals })` |
| `app.setManifestData()` | Create a new `App` |
| `NodeApp`, `loadApp()`, `loadManifest()` from `astro/app/node` | `createApp()` |
| `createExports()` / `start()` | New adapter entrypoint API |
| `SSRManifest` path strings | `URL` objects — read `.href` |
| `vite.build.rollupOptions.output` | `vite.environments.client.build.rollupOptions.output` |
| Content loader `schema` as a function | `createSchema()`, with `satisfies` for the loader type |

All official adapters took a major version for Astro 6's Vite Environments work;
the Cloudflare adapter changed substantially. Read the adapter's own changelog
before assuming a config still applies.

## Upgrade order

- [ ] `npx @astrojs/upgrade` — Astro and every official integration together, so
      the adapter and renderers move in lockstep.
- [ ] Raise Node to 22.12+ locally and in the deploy target before anything
      else; a version error there masks every other failure.
- [ ] Delete the `experimental` block, relocating `cache`, `routeRules`,
      `logger` and `fetchFile` to the top level.
- [ ] Fix content collections first — config path, loaders, `astro/zod`, `id`,
      `render()`. Nothing else typechecks until collection types regenerate, so
      run `astro sync` after this step.
- [ ] Sweep the Removed table across the repo; each row is a mechanical
      substitution.
- [ ] Build and fix compiler errors: unclosed tags, then invalid nesting.
- [ ] Compare rendered output for whitespace between inline elements
      (`compressHTML: 'jsx'`) and for Markdown rendered by Sätteri.
- [ ] Check heading anchors if the site has hand-written `#fragment` links.
- [ ] `astro build && astro preview`, then exercise on-demand routes, forms,
      sessions and caching — none of which behave correctly under `astro dev`.

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev -->
