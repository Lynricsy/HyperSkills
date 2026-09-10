# Next.js App Router — files, boundaries, directives

Route structure and the server/client boundary. Read this before writing or
fixing anything under `app/`.

Verified against: Next.js 16.3, React 19.3.

## Contents

- Special files
- Route segments and private folders
- Middleware became `proxy.ts` (Next.js 16+)
- The RSC boundary: what is invalid
- Serializable props
- Directives: `'use client'`, `'use server'`, `'use cache'`
- Async request APIs (Next.js 15+)
- Runtime selection
- Function index

---

## Special files

| File | Purpose | Server / client |
|---|---|---|
| `layout.tsx` | shared wrapper, preserves state across navigation | Server by default |
| `page.tsx` | the route's own UI | Server by default |
| `loading.tsx` | Suspense fallback for the segment | Server by default |
| `error.tsx` | error boundary for the segment | **must be a Client Component** |
| `global-error.tsx` | error boundary for the root layout; must render `<html>` and `<body>` | must be a Client Component |
| `not-found.tsx` | 404 UI | Server by default |
| `forbidden.tsx` / `unauthorized.tsx` | targets of `forbidden()` / `unauthorized()` | Server by default |
| `route.ts` | Route Handler (API endpoint) | server only |
| `template.tsx` | like a layout but remounts on navigation | Server by default |
| `default.tsx` | fallback for a parallel-route slot | Server by default |
| `proxy.ts` | network proxy at the project root (Next.js 16+) | server (Node.js) |
| `opengraph-image.tsx` / `twitter-image.tsx` | generated social images | server |

`route.ts` and `page.tsx` cannot coexist in one folder. Put the endpoint under
`app/api/<name>/route.ts` and the page under `app/<name>/page.tsx`.

---

## Route segments and private folders

| Pattern | Matches |
|---|---|
| `app/users/[id]/page.tsx` | `/users/123` |
| `app/docs/[...slug]/page.tsx` | `/docs/a/b/c` |
| `app/shop/[[...slug]]/page.tsx` | `/shop` and `/shop/a/b` |
| `app/(marketing)/page.tsx` | `/` — a route group never appears in the URL |
| `app/@sidebar/page.tsx` | a parallel-route slot, passed to the layout as a prop |
| `app/_components/Button.tsx` | nothing — a leading underscore excludes the folder from routing |

---

## Middleware became `proxy.ts` (Next.js 16+)

Same capabilities, three renames. Getting this wrong means the file silently
does nothing.

| Version | File | Export | Config export |
|---|---|---|---|
| 14–15 | `middleware.ts` | `middleware()` | `config` |
| 16+ | `proxy.ts` | `proxy()` | `proxyConfig` |

```ts
// proxy.ts, project root
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  return NextResponse.next()
}

export const proxyConfig = { matcher: ['/dashboard/:path*', '/api/:path*'] }
```

`npx @next/codemod@latest upgrade` performs the rename.

---

## The RSC boundary: what is invalid

### A Client Component is never `async`

Only Server Components may be `async`. An `async` function in a file marked
`'use client'` fails at runtime.

```tsx
// Invalid
'use client'
export default async function UserProfile() {
  const user = await getUser()
  return <div>{user.name}</div>
}

// Correct — the server parent awaits, the client child renders
export default async function Page() {
  const user = await getUser()
  return <UserProfile user={user} />
}

// UserProfile.tsx
'use client'
export function UserProfile({ user }: { user: User }) {
  return <div>{user.name}</div>
}
```

The same file usually carries a second, worse bug: server-only imports. A
database client or a secret-bearing SDK imported into a `'use client'` file is
compiled into the browser bundle. Removing the directive fixes both.

### `'use client'` belongs on the leaf

The directive is contagious downward: every module the file imports becomes part
of the client graph. On a `page.tsx` it opts the entire route out of server
rendering — data fetching moves to the browser and cannot start until the
JavaScript has downloaded and hydrated.

Push it down to the smallest component that actually needs state, an event
handler or a browser API. A page that renders four sections where one has a
toggle needs one small client component, not a client page.

`metadata` and `generateMetadata` are Server-Component-only, so a `'use client'`
page cannot export them at all.

---

## Serializable props

Everything crossing server → client is serialized. Only JSON-compatible values
survive.

| Prop | Valid | Fix |
|---|---|---|
| string, number, boolean, plain object, array | yes | — |
| a function marked `'use server'` | yes | — |
| any other function | no | define it inside the client component |
| `Date` | no | send `.toISOString()`, reconstruct on the client |
| `Map` / `Set` | no | send an object or an array |
| class instance | no | send a plain object; methods are stripped |
| `Symbol` (unregistered), circular reference | no | restructure |

The `Date` case is the dangerous one: it crosses as a string without an error,
then throws on the first `.getFullYear()` call in the browser.

Pass only the fields the client reads. Everything else is bytes in the HTML and
in every later RSC payload.

Serialization deduplicates by object *reference*, not by value, so sending both
`items` and `items.toSorted()` sends the data twice. Send the array once and
transform it on the client. The cost is highest for arrays of primitives, where
every element is duplicated.

---

## Directives

### `'use client'`

Marks the module — and everything it imports — as client code. Required for
hooks, event handlers and browser APIs.

### `'use server'`

Marks a function as a Server Action: an HTTP endpoint that can be passed to a
Client Component and used as a `<form action>`. Either at the top of a module
whose exports are all actions, or inline as the first statement of an async
function inside a Server Component.

Because an action is a public endpoint, it must verify authentication and
authorization itself. Middleware, layout guards and page checks do not run when
it is invoked directly.

### `'use cache'`

A Next.js directive that makes a function or component cacheable, and requires
`cacheComponents: true` in `next.config.ts`. See `nextjs-cache-components.md`
for cache profiles, `cacheLife()` and `cacheTag()`.

---

## Async request APIs (Next.js 15+)

`params`, `searchParams`, `cookies()` and `headers()` are all Promises.

```tsx
type Props = {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ query?: string }>
}

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params
  const { query } = await searchParams
}
```

- In a non-async component, unwrap with `use(params)`.
- In a Route Handler the second argument has the same shape:
  `{ params }: { params: Promise<{ id: string }> }`.
- `generateMetadata` receives the same promise-typed props.
- Migration from the sync form: `npx @next/codemod@latest next-async-request-api .`

Under Cache Components, *where* you await these matters as much as awaiting
them — a top-level `await` blocks the route's static shell. See
`nextjs-cache-components.md`.

---

## Runtime selection

Use the default Node.js runtime. Add `export const runtime = 'edge'` only when
the project already uses Edge, or there is a stated latency requirement and
every dependency is Edge-compatible.

| Runtime | Trade |
|---|---|
| Node.js (default) | full Node API, `fs`, full `crypto`, database drivers, most npm packages |
| Edge | smaller cold start, geographic distribution; no `fs`, reduced `crypto`, many packages unusable |

---

## Function index

Client navigation hooks: `useRouter` (`push`, `replace`, `back`, `refresh`),
`usePathname`, `useSearchParams`, `useParams`,
`useSelectedLayoutSegment(s)`, `useLinkStatus`, `useReportWebVitals`.

`useSearchParams` and `usePathname` need a Suspense boundary in some cases or
the route falls back to client rendering — see `nextjs-rendering.md`.

Server functions: `cookies`, `headers`, `draftMode`, `after`, `connection`,
`userAgent`.

Generate functions: `generateStaticParams`, `generateMetadata`,
`generateViewport`, `generateSitemaps`, `generateImageMetadata`.

Request and response helpers: `NextRequest`, `NextResponse`, `ImageResponse`.

Use `next/link` for internal navigation, never a bare `<a>` — an anchor forces a
full document load and discards the client router's prefetch and state.

<!-- sources: openai-plugins-nextjs, nextjs-docs, vercel-react-bp -->
