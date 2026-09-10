# Next.js metadata, assets, error UI and boundaries

Everything between the route file and the pixels: metadata and social images,
`next/image`, `next/font`, `next/script`, error and not-found UI, the Suspense
bailout rules, and parallel/intercepting routes.

Verified against: Next.js 16.3.

## Contents

- Metadata
- OG image generation
- File-based metadata conventions
- `next/image`
- `next/font`
- `next/script`
- Error and not-found UI
- Redirects and auth errors
- Suspense boundaries and the CSR bailout
- Hydration errors
- Parallel and intercepting routes

---

## Metadata

`metadata` and `generateMetadata` work in Server Components only. A `'use
client'` page cannot export either — remove the directive and push client logic
into children, or move the metadata to the parent layout.

```tsx
export const metadata: Metadata = { title: 'Page title', description: '...' }

// or, per route
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPost(slug) // wrap getPost in cache() — the page needs it too
  return { title: post.title, description: post.description }
}
```

Wrap any loader used by both `generateMetadata` and the page in `cache()`, or
the request runs twice.

A title template in the root layout keeps naming consistent:

```tsx
export const metadata: Metadata = {
  title: { default: 'Site name', template: '%s | Site name' },
}
```

`viewport` is a separate export from `metadata` (static `viewport` or
`generateViewport`) so that metadata can stream.

For most sites static metadata files are enough; reach for `generateMetadata`
only when the content genuinely varies per route.

---

## OG image generation

```tsx
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from 'next/og'

export const alt = 'Blog post'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPost(slug)

  return new ImageResponse(
    <div style={{ display: 'flex', width: '100%', height: '100%', fontSize: 64 }}>
      {post.title}
    </div>,
    { ...size },
  )
}
```

Four constraints that cause most failures:

- Import from `next/og`, not `@vercel/og`.
- Stay on the default Node.js runtime.
- No `searchParams` — an image route only sees route params.
- Flexbox only. No CSS Grid, and styles must be inline objects.

Load custom fonts at module level, not per request (`server-hoist-static-io`).
`twitter-image` is optional: Twitter falls back to the Open Graph image. Use
`generateImageMetadata` for several images per route.

---

## File-based metadata conventions

Drop these in `app/` (or a route segment) and Next.js wires them up:
`favicon.ico`, `icon.png` / `icon.svg`, `apple-icon.png`,
`opengraph-image.png`, `twitter-image.png`, `sitemap.ts`, `robots.ts`,
`manifest.ts`. Use `generateSitemaps` to shard a large sitemap.

---

## `next/image`

```tsx
import Image from 'next/image'

// Local import — dimensions and blur hash are inferred
import hero from './hero.png'
<Image src={hero} alt="Hero" placeholder="blur" priority />

// Remote — width and height are required, and the host must be allowed
<Image src="https://cdn.example.com/a.jpg" alt="A" width={800} height={400} />
```

```js
// next.config.js — remote hosts must be declared
module.exports = {
  images: {
    remotePatterns: [{ protocol: 'https', hostname: 'cdn.example.com', pathname: '/images/**' }],
  },
}
```

Rules that matter:

- `fill` without `sizes` downloads the largest candidate. Always pair them:
  `sizes="100vw"` for a full-width hero,
  `sizes="(max-width: 768px) 100vw, 33vw"` for a three-column grid.
- `priority` on the LCP image only. Everything below the fold is lazy by
  default and needs nothing.
- `width` and `height` are display dimensions, not an aspect ratio. `width={16}
  height={9}` requests a 16-pixel image.
- With `output: 'export'` there is no optimizer: use `unoptimized`, or a custom
  loader.

---

## `next/font`

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  )
}
```

Four failure modes:

- Calling the font loader inside a component creates a new instance on every
  render. Call it once at module scope — in the layout, or in a shared
  `lib/fonts.ts` that components import.
- A `<link>` to Google Fonts, or `@import` in CSS, blocks rendering and gives up
  self-hosting and the zero-layout-shift guarantee. `next/font` exists to
  replace both.
- Omitting `subsets` loads every character range.
- For a non-variable font, list only the weights in use.

`display: 'swap'` is the default and the right choice for body text.

---

## `next/script`

```tsx
import Script from 'next/script'

<Script src="https://example.com/a.js" strategy="afterInteractive" />
<Script id="show-banner">{`document.getElementById('banner')?.classList.remove('hidden')`}</Script>
```

| Issue | Fix |
|---|---|
| bare `<script src>` | use `next/script` |
| inline `<Script>` without `id` | add `id` — Next.js cannot track it otherwise |
| `<Script>` inside `next/head` | move it out; it positions itself |
| hand-written Google Analytics or Tag Manager | use `@next/third-parties/google` |
| `strategy="beforeInteractive"` outside the root layout | it has no effect there |

Strategies: `afterInteractive` (default), `lazyOnload` (idle time),
`beforeInteractive` (root layout only, use sparingly), `worker`
(experimental).

---

## Error and not-found UI

`error.tsx` must be a Client Component and receives `error` and `reset`:

```tsx
'use client'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

Errors bubble to the nearest `error.tsx` at or above the failing segment. An
error thrown by the root layout itself is caught only by `global-error.tsx`,
which replaces the document and therefore must render its own `<html>` and
`<body>`.

`notFound()` renders the closest `not-found.tsx`.

---

## Redirects and auth errors

```tsx
import { redirect, permanentRedirect, notFound, forbidden, unauthorized } from 'next/navigation'
```

- `redirect()` — 307, the default choice.
- `permanentRedirect()` — 308; browsers cache it, so use it only for a real URL
  migration.
- `notFound()` / `forbidden()` / `unauthorized()` — render `not-found.tsx`,
  `forbidden.tsx`, `unauthorized.tsx`.

All of them signal by throwing. Never call one inside a `try` block whose
`catch` swallows errors: the navigation is cancelled and replaced by your error
branch. Call them after the `try`, or start the `catch` with
`unstable_rethrow(error)`.

---

## Suspense boundaries and the CSR bailout

| Hook | Needs a Suspense boundary |
|---|---|
| `useSearchParams()` | yes, always in a static route |
| `usePathname()` | yes in a dynamic route (optional with `generateStaticParams`) |
| `useParams()` | no |
| `useRouter()` | no |

Without the boundary the whole page falls back to client rendering, so the
static shell is lost. Wrap the consumer, not the page:

```tsx
<Suspense fallback={<SearchBarSkeleton />}>
  <SearchBar />
</Suspense>
```

---

## Hydration errors

The message is "Hydration failed because the initial UI does not match" or
"Text content does not match server-rendered HTML". In development, click the
error to see the server/client diff.

| Cause | Fix |
|---|---|
| `window`, `document`, `localStorage` read during render | read it after mount, or inject the value with an inline script before hydration |
| `new Date().toLocaleString()` — server and client timezones differ | render after mount, or mark that element `suppressHydrationWarning` |
| `Math.random()` for a key or id | `useId()` |
| invalid nesting — `<div>` inside `<p>`, `<p>` inside `<p>` | fix the markup; the browser silently reparents it, so the trees differ |
| a third-party script mutating the DOM during hydration | load it with `next/script` and `strategy="afterInteractive"` |

The flicker-free pattern for storage-dependent UI and the correct scope for
`suppressHydrationWarning` are in `rules-rendering-rerender.md`.

---

## Parallel and intercepting routes

Parallel routes render several pages in one layout; intercepting routes show
different UI for an in-app navigation than for a direct hit. Together they make
the modal-over-a-list pattern.

```
app/
  @modal/
    default.tsx            # required — returns null
    (.)photos/[id]/page.tsx  # the modal
  photos/[id]/page.tsx     # the full page, for direct access
  layout.tsx               # receives { children, modal }
```

Matchers name **route segments**, not folders: `(.)` same level, `(..)` one
segment up, `(..)(..)` two, `(...)` from the root. If `@modal` lives in
`app/dashboard/`, then `(.)photos` intercepts `/dashboard/photos`.

Three gotchas, in order of how often they bite:

1. **Every `@slot` folder needs `default.tsx`.** Without it, refreshing any page
   404s, because Next.js cannot decide what to render in the slot. Nested route
   groups each need their own.
2. **Close a modal with `router.back()`**, never `router.push()` or a `<Link>`.
   `push` adds a history entry (so Back re-opens the modal) and does not clear
   the intercepted route.
3. **A direct hit bypasses the interceptor** — the full page renders and no
   modal appears. That is the intended behaviour; render the modal from the full
   page too if you want it on direct access.

<!-- sources: openai-plugins-nextjs, nextjs-docs, vercel-react-bp -->
