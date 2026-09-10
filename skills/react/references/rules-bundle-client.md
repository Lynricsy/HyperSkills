# Bundle and client-fetching rules

`bundle-*` decides what ships to the browser; it moves Time to Interactive and
Largest Contentful Paint directly. `client-*` covers data and listeners once
the code is there.

Verified against: React 19.3, Next.js 16.3.

## Contents

- `bundle-barrel-imports` — never import from a library barrel
- `bundle-dynamic-imports` — load off-path components on demand
- `bundle-analyzable-paths` — keep import and file paths statically readable
- `bundle-conditional` — load feature data only when the feature turns on
- `bundle-defer-third-party` — analytics after hydration
- `bundle-preload` — preload on intent
- `client-swr-dedup` — one request per key, not per instance
- `client-event-listeners` — one global listener for N consumers
- `client-passive-event-listeners` — passive touch and wheel
- `client-localstorage-schema` — version, minimize, guard

---

## `bundle-barrel-imports`

Impact: CRITICAL. Icon and component libraries re-export thousands of modules
from their entry file. Importing a name from that entry loads the whole graph:
hundreds of milliseconds per cold start and seconds of extra dev-server work.

Tree shaking does not save you. If the library is external it is not optimized
at all, and bundling it to enable shaking makes builds substantially slower.

```tsx
// Incorrect
import { Check, X, Menu } from 'lucide-react'
import { Button, TextField } from '@mui/material'
```

Preferred fix in Next.js (13.5+) — keep the ergonomic import and let the build
rewrite it:

```js
// next.config.js
module.exports = {
  experimental: {
    optimizePackageImports: ['lucide-react', '@mui/material'],
  },
}
```

Outside Next.js, import the source path directly:

```tsx
import Button from '@mui/material/Button'
```

One caveat with direct paths: some libraries (notably `lucide-react`) ship no
type declarations for their deep paths, so the import resolves to `any` and
fails under `noImplicitAny`. Check for `.d.ts` files at the subpath before
switching, or prefer `optimizePackageImports`.

Commonly affected: `lucide-react`, `@mui/material`, `@mui/icons-material`,
`@tabler/icons-react`, `react-icons`, `@headlessui/react`, `@radix-ui/react-*`,
`lodash`, `ramda`, `date-fns`, `rxjs`, `react-use`.

---

## `bundle-dynamic-imports`

Impact: CRITICAL. A component that is not on the first paint should not be in
the first bundle.

```tsx
// Incorrect — the editor ships to everyone
import { MonacoEditor } from './monaco-editor'

// Correct (Next.js)
import dynamic from 'next/dynamic'
const MonacoEditor = dynamic(
  () => import('./monaco-editor').then((m) => m.MonacoEditor),
  { ssr: false },
)
```

Outside Next.js the equivalent is `React.lazy` plus a `<Suspense>` boundary.
Reach for this when the component is heavy *and* conditionally rendered:
editors, charts, maps, rich text, PDF viewers, video players.

---

## `bundle-analyzable-paths`

Impact: HIGH. Bundlers and Next.js file tracing work from paths they can read
at build time. Hiding the real path in a variable forces the tool to include
every candidate, widen the trace, or warn that it cannot analyze the import.
The cost is a larger server bundle, slower builds, worse cold starts.

```ts
// Incorrect — the bundler cannot tell what may be imported
const Page = await import(PAGE_MODULES[pageName])

// Correct — an explicit map of thunks
const PAGE_MODULES = {
  home: () => import('./pages/home'),
  settings: () => import('./pages/settings'),
} as const
const Page = await PAGE_MODULES[pageName]()
```

The same holds for the file system, where Next.js traces `import`, `require`
and `fs` usage:

```ts
// Incorrect — even a two-value enum hides the final path
const baseDir = path.join(process.cwd(), 'content/' + kind)

// Correct — each final path is literal at the call site
const baseDir = isBlog
  ? path.join(process.cwd(), 'content/blog')
  : path.join(process.cwd(), 'content/docs')
```

---

## `bundle-conditional`

Impact: HIGH. Large data or modules behind a feature flag load when the feature
activates, not at import time.

```tsx
useEffect(() => {
  if (!enabled || frames || typeof window === 'undefined') return
  import('./animation-frames.js')
    .then((mod) => setFrames(mod.frames))
    .catch(() => setEnabled(false))
}, [enabled, frames, setEnabled])
```

The `typeof window === 'undefined'` guard also keeps the module out of the
server bundle, which shrinks the build.

---

## `bundle-defer-third-party`

Impact: MEDIUM. Analytics, logging and error tracking do not block
interaction, so they should not block the initial bundle.

```tsx
const Analytics = dynamic(
  () => import('@vercel/analytics/react').then((m) => m.Analytics),
  { ssr: false },
)
```

---

## `bundle-preload`

Impact: MEDIUM, on perceived speed rather than bytes. Start the download on
intent, before the click:

```tsx
const preload = () => {
  if (typeof window !== 'undefined') void import('./monaco-editor')
}

<button onMouseEnter={preload} onFocus={preload} onClick={open}>Open editor</button>
```

`onFocus` matters: without it, keyboard users get none of the benefit.

---

## `client-swr-dedup`

Impact: MEDIUM-HIGH. A `useEffect` plus `fetch` in a component means one
request per mounted instance, no cache, no revalidation, and a race whenever
the key changes.

```tsx
// Incorrect
const [users, setUsers] = useState([])
useEffect(() => { fetch('/api/users').then((r) => r.json()).then(setUsers) }, [])

// Correct — instances share one request
const { data: users } = useSWR('/api/users', fetcher)
```

Use the project's existing server-cache library. SWR and React Query both
deduplicate; do not add a second one. In an App Router project, prefer passing
the data down from a Server Component and reach for a client cache only for
data that must refresh without a navigation.

If you must hand-roll a fetch effect, it needs an `AbortController` and a
`.catch` — otherwise a slow earlier response overwrites a newer one and a failed
request leaves the UI stuck on its loading state forever.

---

## `client-event-listeners`

Impact: LOW, but it scales with instance count. A hook that registers a global
listener registers one per call site. Keep a module-level registry of callbacks
and one shared subscription, so N consumers cost one listener.

---

## `client-passive-event-listeners`

Impact: MEDIUM on scroll smoothness. The browser must wait for a non-passive
`touchstart` or `wheel` listener to finish before it knows whether
`preventDefault()` was called, which delays the scroll.

```ts
document.addEventListener('wheel', onWheel, { passive: true })
```

Use `passive: true` for tracking, analytics and any listener that never calls
`preventDefault()`. Omit it when implementing custom swipe or zoom gestures.

---

## `client-localstorage-schema`

Impact: MEDIUM. Web storage is synchronous, throws in several real situations,
and outlives your schema.

```ts
const VERSION = 'v2'

function saveConfig(config: { theme: string; language: string }) {
  try {
    localStorage.setItem(`userConfig:${VERSION}`, JSON.stringify(config))
  } catch {
    // Throws in private browsing, when the quota is exceeded, or when disabled.
  }
}
```

Three requirements: version the key so old shapes are ignorable, store only the
fields the UI needs (never tokens, PII or internal flags), and wrap every read
and write in `try`/`catch`. Migrate by reading the old key once and removing it.

Cache reads in memory when they happen more than once
(see `js-cache-storage` in the JS reference), and invalidate that cache from a
`storage` event if another tab can write the same key.

<!-- sources: vercel-react-bp, openai-plugins-nextjs, nextjs-docs -->
