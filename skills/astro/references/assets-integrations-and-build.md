# Images, fonts, integrations and the build

Verified against: Astro 7.3

## Contents

- [Where images live](#where-images-live)
- [`<Image />` and `<Picture />`](#image--and-picture-)
- [Responsive images](#responsive-images)
- [Remote images](#remote-images)
- [SVG components](#svg-components)
- [`getImage()`](#getimage)
- [Fonts](#fonts)
- [Integrations](#integrations)
- [Vite configuration](#vite-configuration)
- [Styles](#styles)
- [Markdown processor](#markdown-processor)
- [Build and CLI](#build-and-cli)
- [Testing](#testing)

## Where images live

`src/` images are imported, hashed, transformed and optimised. `public/` images
are copied verbatim: never optimised, never responsive, referenced by their path
relative to `public/`. Prefer `src/` unless the URL must be stable and
predictable. `[official]`

## `<Image />` and `<Picture />`

```astro
---
import { Image, Picture } from "astro:assets";
import hero from "../assets/hero.png";   // 1600x900
---
<Image src={hero} alt="A description." />
<Picture src={hero} formats={["avif", "webp"]} alt="A description." />
```

- `alt` is required on both. A missing `alt` is a build error, not a lint
  warning — `alt=""` is the correct value for decorative images.
- Dimensions are inferred from an imported `src`, which is what prevents layout
  shift. A `public/` or unconfigured remote `src` needs explicit `width` and
  `height`.
- Transformation happens at build time for prerendered pages and per request for
  on-demand pages.
- The default Sharp service **crops** to the requested aspect ratio and **never
  upscales**. Asking for dimensions larger than the source silently returns the
  source size, so a design that depends on upscaling needs a different service
  or pre-scaled assets. `[official]`
- SVG sources are rasterised when a raster format is requested. Branch on the
  format before converting if the collection mixes SVG and raster.
- Astro components (`<Image />`, `<Picture />`, SVG components) cannot be used
  inside a framework component. Pass the rendered element in as a child or named
  slot from the `.astro` file.

## Responsive images

Setting `layout` — per component, or globally with `image.layout` — makes Astro
generate `srcset` and `sizes`:

| `layout` | Behaviour |
|---|---|
| `constrained` | Scales down to the container, never past the given dimensions |
| `full-width` | Always fills the container |
| `fixed` | Keeps its dimensions |

`image.layout` also applies to Markdown `![]()` images. The generated markup
needs CSS to actually resize: enable `image.responsiveStyles: true` for Astro's
minimal global styles, or leave it `false` and own the styling. With Tailwind 4,
leave it `false` — Tailwind's rules live in a cascade layer and therefore lose
to Astro's unlayered styles. `[official]`

`fit` and `position` props override `object-fit` / `object-position` per image.

## Remote images

Remote images are only optimised when their source is allow-listed:

```js
export default defineConfig({
  image: {
    domains: ["astro.build"],
    remotePatterns: [{ protocol: "https" }],
  },
});
```

Unlisted remote images still render through `<Image />` — unoptimised, but with
CLS protection from explicit dimensions.

If the adapter's runtime cannot run Sharp (Cloudflare, for example), configure
`image.service` to `passthroughImageService()`. The components keep working and
keep enforcing `alt` and dimensions; no transformation happens.

## SVG components

An imported `.svg` file can be used as a component; Astro inlines the markup, so
attributes passed to it land on the `<svg>` element. Useful for icons that must
inherit `currentColor`.

## `getImage()`

`getImage({ src, format, width })` returns the processed image's attributes for
places a component cannot go: an endpoint building an OG image, a CSS custom
property, a `data-` attribute.

It is server-only and **throws when called on the client**. Call it in
frontmatter and pass the resulting `src` down. `[official]`

## Fonts

Fonts are configured at the top level (no experimental flag) and served from
your own origin, which avoids the third-party request entirely:

```js
import { defineConfig, fontProviders } from "astro/config";

export default defineConfig({
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: "Inter",
      cssVariable: "--font-inter",
      weights: [400, 600],
      styles: ["normal"],
      subsets: ["latin"],
      fallbacks: ["sans-serif"],
    },
  ],
});
```

```astro
---
import { Font } from "astro:assets";
---
<Font cssVariable="--font-inter" preload />
```

- The `<Font />` component belongs in `<head>`; without it the family is
  configured but never linked, and the CSS variable resolves to nothing.
- Built-in providers: `local`, `adobe`, `bunny`, `fontshare`, `fontsource`,
  `google`, `googleIcons`, `npm`.
- Declare only the weights, styles and subsets actually used — each combination
  is a downloaded file. Repeating the same family (same `name`, `cssVariable`,
  `provider`) with different combinations is supported and merges.
- Variable fonts take a range: `weights: ["300 700"]`.
- `preload` blocks other resources; reserve it for above-the-fold families.
- `fallbacks` matching the primary's metrics is what removes the swap-time
  layout shift.
- Cache lives in `.astro/fonts` (dev) and `node_modules/.astro/fonts` (build);
  delete those to force a re-download.

## Integrations

```bash
npx astro add react sitemap      # installs and edits astro.config in one step
npx @astrojs/upgrade             # upgrade astro and all official integrations together
```

`integrations` accepts factory calls, arrays and inline objects, and **ignores
falsy entries** — so `integrations: [isProd && sitemap()]` is a legitimate
conditional rather than something to guard.

Writing one: hooks fire as `astro:config:setup` (register renderers, inject
routes and scripts, `updateConfig`, add Vite plugins), `astro:config:done`,
`astro:server:setup`, `astro:build:start`, `astro:routes:resolved`,
`astro:build:ssr`, `astro:build:done`. In Astro 6+, `routes` moved off
`astro:build:done` to `astro:routes:resolved`, and `entryPoints` was removed
from `astro:build:ssr`. `astro:ssr-manifest` is gone; read config from
`astro:config/server`.

Run `astro sync` after adding or changing an integration so generated types
match.

## Vite configuration

Vite options nest under `vite` in `astro.config.*`. Astro 7 runs Vite 8 with the
Environments API, which relocates per-environment build config:

```js
export default defineConfig({
  vite: {
    environments: {
      client: {
        build: { rollupOptions: { output: { manualChunks: { /* … */ } } } },
      },
    },
  },
});
```

`vite.build.rollupOptions.output` no longer applies to the client bundle. Plugin
authors should read Vite's own migration guide; most application code needs no
change beyond this relocation. `[official]`

## Styles

A `<style>` in an `.astro` component is scoped to that component. `is:global`
opts out, `define:vars` passes frontmatter values in as custom properties (and
is the one attribute that does not imply `is:inline`).

Astro 7 compresses HTML with JSX whitespace rules by default
(`compressHTML: 'jsx'`): whitespace and line breaks around elements are removed,
whitespace inside a single line is kept. A layout that relied on a newline
between two inline elements loses that space — write it explicitly as `{" "}`,
or set `compressHTML: true` (HTML-aware) or `false` (preserve everything).
`[official]`

## Markdown processor

Astro 7 renders `.md` with Sätteri (`@astrojs/markdown-satteri`), not the
remark/rehype pipeline. Projects that depend on remark or rehype plugins must
install `@astrojs/markdown-remark` and select it: `[official]`

```js
import { unified } from "@astrojs/markdown-remark";

export default defineConfig({
  markdown: { processor: unified() },
});
```

`markdown.remarkPlugins`, `rehypePlugins` and `remarkRehype` still work but now
require that package. Check for these options before advising a plugin.

## Build and CLI

```bash
npx astro dev            # dev server; auto-detaches under an AI agent (see below)
npx astro build          # production build
npx astro preview        # serve the build — the only way to test caching and adapters locally
npx astro check          # type and diagnostic check
npx astro sync           # regenerate .astro/types.d.ts
npx astro add <name>     # install and wire an integration
npx astro create-key     # stable ASTRO_KEY for server islands
```

Two Astro 7 behaviours to expect:

- **Background dev server.** When an AI coding agent is detected, `astro dev`
  detaches, writes `.astro/dev.json` with the URL, port and PID, and returns.
  Manage it with `astro dev status`, `astro dev logs [--follow]` and
  `astro dev stop`; `ASTRO_DEV_BACKGROUND=0` opts out. Do not start a second
  server for the same project — the lock file prevents it. `[official]`
- **Rust compiler.** The compiler errors on unclosed non-void tags and no longer
  silently repairs invalid nesting such as a `<div>` inside a `<p>`. A template
  that built under an older Astro can now fail, or render differently where the
  browser closes an element early. It also serialises CSS colours and `url()`
  quoting differently, which only matters to exact-string tests. `[official]`

Node 22.12 or newer is required.

## Testing

- **Unit / component:** Vitest with `getViteConfig()` from `astro/config`, which
  applies the project's Astro config to the test environment. Render `.astro`
  components with the Container API
  (`experimental_AstroContainer.create()` then `renderToString()`). Astro
  components can only be rendered in the `node` environment — a `jsdom` or
  `happy-dom` environment fails, so give those tests their own environment
  entry. `[official]`
- **End to end:** Playwright against `astro preview`, via `webServer` in
  `playwright.config.ts`. Prefer `preview` over `dev`: prerendering, adapters,
  caching and asset hashing only behave correctly in a build.

<!-- sources: withastro-docs, awesome-copilot-astro, withastro-astro-skills, gigio-astro-dev, incluud-astro-skills -->
