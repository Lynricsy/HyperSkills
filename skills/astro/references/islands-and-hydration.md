# Islands and hydration

Verified against: Astro 7.3

## Contents

- [The default is zero JavaScript](#the-default-is-zero-javascript)
- [Choosing a client directive](#choosing-a-client-directive)
- [Directive options that exist](#directive-options-that-exist)
- [`client:only` and fallback content](#clientonly-and-fallback-content)
- [The island boundary](#the-island-boundary)
- [Sharing state between islands](#sharing-state-between-islands)
- [Props crossing the boundary](#props-crossing-the-boundary)
- [Children and named slots](#children-and-named-slots)
- [Server islands (`server:defer`)](#server-islands-serverdefer)
- [Scripts in `.astro` components](#scripts-in-astro-components)
- [Reviewing a page's hydration](#reviewing-a-pages-hydration)

## The default is zero JavaScript

A framework component rendered without a `client:*` directive is executed once on
the server and emitted as HTML. Its JavaScript, and its framework runtime, never
reach the browser. `[official]`

```astro
<Chart data={rows} />              <!-- static HTML, 0 KB shipped -->
<Chart data={rows} client:load />  <!-- island: framework + component shipped -->
```

This is why an audit starts by deleting directives rather than downgrading them.
A footer, a breadcrumb trail or a product grid that only renders markup does not
need any directive; changing `client:load` to `client:visible` on such a
component still ships the framework runtime, just later.

A directive is only valid on a UI framework component imported directly into an
`.astro` file. It does nothing on a dynamic tag (`<Tag />` where `Tag` is a
variable) and nothing on components passed through MDX's `components` prop, and
applying one to an `.astro` component is an error — `.astro` components have no
client runtime at all. `[official]`

## Choosing a client directive

| Directive | Fires when | Use for |
|---|---|---|
| `client:load` | Immediately on page load | Above-the-fold controls the visitor may use in the first seconds |
| `client:idle` | After initial load, on `requestIdleCallback` (falls back to `load`) | Visible but non-urgent controls |
| `client:visible` | When the element enters the viewport (`IntersectionObserver`) | Below-the-fold and expensive widgets |
| `client:media="(query)"` | When the media query matches | Controls that only exist at some viewport sizes |
| `client:only="framework"` | Immediately, **without** server-rendering the component | Components that cannot render on the server at all |

Two failure modes are worth naming because they look like optimisations:

- `client:visible` uses an `IntersectionObserver`, so an element already on
  screen intersects on the first callback: the directive costs an observer and
  buys nothing. Use `client:load` for the header, hero and anything above the
  fold, which is why the documentation scopes `client:visible` to elements far
  down the page. `[official]`
- `client:idle` waits for a real `requestIdleCallback`, which a loaded low-end
  device may not deliver for a long time — that is what the `timeout` option
  exists to bound. Anything a visitor may touch early belongs on `client:load`.
  `[official]`

If a component is already hidden and shown by a CSS media query, use
`client:visible` rather than repeating the query in `client:media` — the hidden
element never intersects, so it never hydrates. `[official]`

## Directive options that exist

Only these options are supported. Anything else is silently ignored, so an
invented option reads as working code that never takes effect. `[official]`

```astro
<Widget client:idle={{ timeout: 500 }} />            <!-- ms ceiling before hydrating anyway -->
<Carousel client:visible={{ rootMargin: "200px" }} /> <!-- hydrate before it scrolls into view -->
```

`client:visible` takes `rootMargin` and nothing else — there is no `threshold`
option. `rootMargin` is the useful knob: it buys download and hydration time on
a slow connection so the widget is interactive by the time it is on screen.

## `client:only` and fallback content

`client:only` skips server rendering, so Astro cannot infer the framework from
the file extension at build time. The framework name is required and must be the
renderer's own id: `"react"`, `"preact"`, `"svelte"`, `"vue"`, `"solid-js"`.
`[official]`

Because nothing is server-rendered, the slot is empty until the bundle lands.
Fill it:

```astro
<Editor client:only="react">
  <div slot="fallback">Loading editor…</div>
</Editor>
```

Reach for `client:only` only when server rendering genuinely fails — a component
that touches `window` at module scope, or a third-party widget that assumes a
DOM. Everything else pays for `client:only` in an empty first paint and a
content shift.

## The island boundary

Every `client:*` directive creates an independent root. Two islands on one page
do not share a component tree, a renderer instance, or any provider above them.
`[official]`

The consequence people hit first: a context provider cannot cross the boundary.

```astro
<!-- Broken: three roots. AddToCart's useCart() sees no provider. -->
<CartProvider client:load>
  <AddToCart client:load product={product} />
</CartProvider>
<CartCount client:load />
```

```astro
<!-- Works: one root. The provider and its consumers are inside one island. -->
<CartIsland client:load product={product} />
```

Hydrate the smallest subtree that contains both the provider and every consumer
that needs it. When consumers are far apart on the page (a header count and a
product button), one island cannot contain both — use a shared store instead.

## Sharing state between islands

Islands communicate through something outside the component tree. In order of
preference:

1. **URL state** — search params for filters, sort, pagination and tabs. Free to
   share, survives navigation and is linkable.
2. **A framework-agnostic store** — a signal/atom module imported by each island
   (for example nanostores). The module instance is shared across islands
   because it is a plain ES module in the same bundle graph.
3. **DOM custom events** on `document` — fine for one-off notifications, poor as
   a state container because late-hydrating islands miss earlier events.
4. **Server state** — a cookie or session read by a server island, when the
   value must also be correct in the initial HTML.

Do not reach for a global provider mounted "high up" to fix a cross-island
problem: there is no position high enough, because the `.astro` page itself is
not part of any island.

## Props crossing the boundary

Props passed to a hydrated component are serialised into the HTML and parsed
again in the browser. Supported: plain objects, `number`, `string`, `Array`,
`Map`, `Set`, `RegExp`, `Date`, `BigInt`, `URL`, `Uint8Array`, `Uint16Array`,
`Uint32Array`, `Infinity`. `[official]`

Functions are not serialisable. A callback prop works during server rendering
and is simply absent on the client, which surfaces as a dead button rather than
an error — keep the handler inside the island. Class instances arrive as plain
data and throw on their first method call. Circular references fail outright.

Everything passed is also page weight, twice over: once in the HTML and once in
the hydration payload. Pass the three fields the island reads, not the record it
reads them from.

## Children and named slots

Children can be passed from `.astro` into a framework component, including
Astro-rendered static content:

```astro
<ReactSidebar>
  <AstroCard slot="header" />   <!-- static HTML, becomes a prop -->
  <p>Body text</p>
</ReactSidebar>
```

React, Preact and Solid receive the default children as `children` and each
named slot as a top-level prop with the name camel-cased (`social-links` →
`socialLinks`). Svelte and Vue receive them through `<slot>` / `<slot name="…">`
with the name preserved as written. `[official]`

Render props do not work across this boundary — an `.astro` component cannot
provide the client-side callback the pattern needs. Use a named slot.

A framework component file cannot import an `.astro` component, and cannot mix
frameworks. Only `.astro` files may compose components from several frameworks,
and a single page may hold React, Svelte and Vue islands side by side; each
framework's runtime is sent once no matter how many islands use it. `[official]`

## Server islands (`server:defer`)

`server:defer` on an `.astro` component defers that component's server rendering
out of the page render. The page ships immediately with the `slot="fallback"`
content, and the island is fetched from a dedicated endpoint and swapped in.
`[official]`

```astro
---
import PriceBadge from "../components/PriceBadge.astro";
import PricePlaceholder from "../components/PricePlaceholder.astro";
---
<PriceBadge server:defer sku={product.sku}>
  <PricePlaceholder slot="fallback" />
</PriceBadge>
```

This is the tool for per-request data on an otherwise cacheable page: the shell
stays static and aggressively cacheable while the avatar, cart count, price or
A/B variant renders per visitor. It needs an adapter installed, even if the rest
of the site is static.

Constraints worth knowing before designing around it:

- **Props are encrypted into the request URL.** Past roughly 2 KB of query
  string Astro switches to `POST`, and `POST` responses are not browser-cached —
  which silently deletes the caching benefit that motivated the island. Pass
  identifiers, not payloads. `[official]`
- **The island runs in its own request.** `Astro.url` and `Astro.request.url`
  report `/_server-islands/<Name>`, not the visitor's page. Read the `Referer`
  header when the island genuinely needs the page URL, and prefer passing the
  value as a prop. `[official]`
- **The encryption key is regenerated per build.** Under rolling deployments,
  multi-region hosting, or a CDN still serving pages built with the previous
  key, decryption fails. Generate a stable key with `astro create-key` and set
  it as `ASTRO_KEY` in the build environment. `[official]`
- Provide fallback content of the same shape as the real content. An empty
  fallback trades a slow page for a shifting one.

Choosing between the three rendering modes for one region of a page:

```
Needs server data on every request (cookies, session, live price)?
  yes -> server:defer
  no  -> Needs browser interactivity (events, local state)?
           yes -> client:* on the smallest interactive subtree
           no  -> no directive at all
```

## Scripts in `.astro` components

For behaviour that does not need a framework, a `<script>` tag in an `.astro`
component is the cheapest option: it is bundled, deduplicated and type-checked,
and it ships no runtime. A hamburger toggle, a copy button or a theme switch
belongs here rather than in a hydrated component. `[official]`

`<script>` and `<style>` tags render in the order they are written. Any
attribute other than `src` implies `is:inline`, which opts the tag out of
bundling, deduplication and import resolution — `define:vars` on a `<style>` is
the one exception. `[official]`

`define:vars` passes JSON-serialisable frontmatter values into an inline script
or into CSS custom properties, which is how a script gets server data without a
data attribute of its own.

## Reviewing a page's hydration

Walk the page in this order; each step is cheaper than the next.

1. Every directive on a component with no event handler, no local state and no
   browser API: delete it.
2. Every `client:load` below the fold: `client:visible`, with `rootMargin` if it
   is heavy.
3. Every `client:load` that only exists for a toggle: replace the island with a
   `<script>`.
4. Every island whose props carry a whole record: narrow to the fields read.
5. Every provider/consumer pair split across directives: collapse into one
   island or move to a store.
6. Every per-request value fetched into a prerendered page: `server:defer`.

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev, incluud-astro-skills -->
