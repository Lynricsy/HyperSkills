# Next.js data fetching and server caching

Which mechanism moves the data, and how to keep the server side off the
critical path. Read this when deciding how data flows, or when reviewing server
performance.

Verified against: Next.js 16.3.

## Contents

- Choosing the mechanism
- Server Components (reads)
- Server Actions (writes)
- Route Handlers (external callers)
- Client Components that need data
- `server-parallel-fetching` — composition parallelizes
- `server-parallel-nested-fetching` — chain per item
- `async-api-routes` — start early, await late
- `server-cache-react` — per-request deduplication
- `server-cache-lru` — cross-request caching
- `server-hoist-static-io` — module-level static reads
- `server-no-shared-module-state` — module scope is process-wide
- `server-after-nonblocking` — work after the response

---

## Choosing the mechanism

| Need | Use | Caching |
|---|---|---|
| Read data for your own UI | fetch directly in a Server Component | full Next.js caching |
| Mutate from your own UI, including forms | Server Action | none (always POST) |
| Serve a webhook, a mobile app, or any external caller | Route Handler | `GET` can be HTTP-cached |
| Read from a Client Component that must refresh without navigating | Route Handler plus a client cache, or a Server Action | HTTP cache headers |

The two mistakes this table exists to prevent: building a Route Handler that
only your own Server Component calls (a pointless HTTP round trip), and using a
Server Action for a cacheable read (Actions are POST, so nothing caches).

---

## Server Components (reads)

```tsx
// app/users/page.tsx
export default async function UsersPage() {
  const users = await db.user.findMany()
  return <ul>{users.map((u) => <li key={u.id}>{u.name}</li>)}</ul>
}
```

No API layer to maintain, no client-server waterfall, secrets stay on the
server. `fetch` is request-memoized inside a single render, so the same URL and
options resolve once.

---

## Server Actions (writes)

```tsx
// app/actions.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const session = await verifySession()
  if (!session) throw new Error('Unauthorized')

  const title = String(formData.get('title') ?? '')
  await db.post.create({ data: { title, authorId: session.user.id } })
  revalidatePath('/posts')
}
```

Requirements, in order: validate the input, verify the session, check
authorization, then mutate. `server-auth-actions` is CRITICAL because an Action
is a public endpoint — an unauthenticated caller can invoke it directly, and no
middleware or layout guard runs.

Constraints: POST only, internal callers only, serializable return values only.

Do not wrap `redirect()`, `permanentRedirect()`, `notFound()`, `forbidden()` or
`unauthorized()` in a `try` block — they signal by throwing, and catching that
throw cancels the navigation. Call them after the `try`, or re-throw with
`unstable_rethrow(error)` at the top of the `catch`.

---

## Route Handlers (external callers)

```ts
// app/api/users/[id]/route.ts
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const user = await getUser(id)
  if (!user) return Response.json({ error: 'Not found' }, { status: 404 })
  return Response.json(user)
}
```

Methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`.

A handler runs in a Server-Component-like environment: `async`/`await`,
`cookies()`, `headers()` and Node APIs are available; React hooks, React DOM
(including `renderToString`) and browser APIs are not.

---

## Client Components that need data

In preference order:

1. Pass it down from a Server Component as an initial value. No extra round
   trip, and the data is in the HTML.
2. A Route Handler plus the project's client cache (SWR / React Query), when
   the data must refresh without a navigation.
3. A Server Action called from an effect. It works, but it is POST, so nothing
   caches it; prefer a Route Handler for reads.

A hand-written `useEffect` plus `fetch` is the option to argue against: one
request per instance, no cache, no deduplication, and a race whenever the key
changes. See `client-swr-dedup` in `rules-bundle-client.md`.

---

## `server-parallel-fetching` — composition parallelizes

Impact: CRITICAL. Server Components in a parent-child chain execute
sequentially; siblings execute concurrently. Restructure so the fetches are
siblings.

```tsx
// Incorrect — Sidebar cannot start until the page's await resolves
export default async function Page() {
  const header = await fetchHeader()
  return (<div><div>{header}</div><Sidebar /></div>)
}

// Correct — Header and Sidebar fetch at the same time
export default function Page() {
  return (<div><Header /><Sidebar /></div>)
}
```

The `children` variant works the same way: a layout that renders `{children}`
does not block them, so pushing a fetch into a child of the layout parallelizes
it against the layout's own work.

---

## `server-parallel-nested-fetching` — chain per item

Impact: CRITICAL. Two sequential `Promise.all` calls let the slowest item of the
first batch block every item of the second.

```tsx
// Incorrect — one slow chat blocks all 100 author lookups
const chats = await Promise.all(chatIds.map((id) => getChat(id)))
const authors = await Promise.all(chats.map((c) => getUser(c.author)))

// Correct — each item chains its own follow-up
const authors = await Promise.all(
  chatIds.map((id) => getChat(id).then((chat) => getUser(chat.author))),
)
```

---

## `async-api-routes` — start early, await late

Impact: CRITICAL. Inside a Route Handler or Server Action, create the promises
for independent work immediately and await as late as possible.

```ts
export async function GET() {
  const sessionPromise = auth()
  const configPromise = fetchConfig()

  const session = await sessionPromise
  const [config, data] = await Promise.all([configPromise, fetchData(session.user.id)])

  return Response.json({ data, config })
}
```

---

## `server-cache-react` — per-request deduplication

Impact: MEDIUM. `cache()` from React deduplicates a call within one request —
the case that matters for auth checks and database queries, which `fetch`
memoization does not cover.

```ts
import { cache } from 'react'

export const getCurrentUser = cache(async () => {
  const session = await auth()
  if (!session?.user?.id) return null
  return db.user.findUnique({ where: { id: session.user.id } })
})
```

The trap: `cache()` compares arguments with `Object.is`, so an inline object
argument never hits.

```ts
const getUser = cache(async (params: { uid: number }) => /* ... */)
getUser({ uid: 1 })
getUser({ uid: 1 }) // miss — a new object each call

const getUserById = cache(async (uid: number) => /* ... */)
getUserById(1)
getUserById(1) // hit
```

Take primitives, or pass the same reference. This is also how the preload
pattern works: call `void getUser(id)` early without awaiting, then `await
getUser(id)` where the value is needed — the second call returns the in-flight
promise.

`fetch` in Next.js is already request-memoized by URL and options, so
`cache()` is for everything else: database queries, file reads, heavy
computation, auth.

---

## `server-cache-lru` — cross-request caching

Impact: HIGH where it applies. `cache()` lasts one request. For data reused
across a user's consecutive requests, add a bounded LRU with a TTL:

```ts
import { LRUCache } from 'lru-cache'

const users = new LRUCache<string, User>({ max: 1000, ttl: 5 * 60 * 1000 })
```

This only helps when requests share a process — which they do on platforms that
keep one instance warm across concurrent requests. In classic per-invocation
serverless each request may be isolated, so reach for a shared store instead.
Never cache per-user data under a key that is not the user.

---

## `server-hoist-static-io` — module-level static reads

Impact: HIGH. Module-level code runs once per instance; handler bodies run per
request. Static assets — fonts for social images, logos, config, templates —
belong at module level.

```ts
// Runs once, when the module is first imported
const fontData = fetch(new URL('./fonts/Inter.ttf', import.meta.url)).then((r) => r.arrayBuffer())

export async function GET() {
  const font = await fontData
  // ...
}
```

Do not hoist anything that varies per request or per user, may change while the
process lives (use a TTL cache instead), is large enough to matter in memory, or
is sensitive enough that it should not sit in a long-lived process.

---

## `server-no-shared-module-state` — module scope is process-wide

Impact: HIGH, and a security bug when violated. Server renders run
concurrently in one process. A mutable module-level variable holding
request data leaks between requests.

```tsx
// Incorrect — request B can overwrite currentUser while request A still renders
let currentUser: User | null = null

export default async function Page() {
  currentUser = await auth()
  return <Dashboard />
}

// Correct — request data stays in the render tree
export default async function Page() {
  const user = await auth()
  return <Dashboard user={user} />
}
```

Safe at module scope: immutable config and assets loaded once, caches designed
for cross-request reuse and keyed correctly, singletons that hold no
request-specific mutable state.

---

## `server-after-nonblocking` — work after the response

Impact: MEDIUM. `after()` schedules work to run once the response has finished
streaming — analytics, audit logs, notifications, cache invalidation, cleanup.

```ts
import { after } from 'next/server'
import { headers } from 'next/headers'

export async function POST(request: Request) {
  await updateDatabase(request)

  after(async () => {
    logUserAction({ userAgent: (await headers()).get('user-agent') ?? 'unknown' })
  })

  return Response.json({ status: 'ok' })
}
```

It runs even when the response fails or redirects, and works in Server Actions,
Route Handlers and Server Components. Do not put anything the response depends
on inside it.

<!-- sources: vercel-react-bp, openai-plugins-nextjs, nextjs-docs, react-docs -->
