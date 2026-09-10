# Cache Components and instant navigation

Two jobs: turning `cacheComponents` on without drowning in blocking-route
errors (adoption), and growing a route's static shell until its navigation is
instant, with a test that keeps it that way (optimization).

Verified against: Next.js 16.3, `@next/playwright` 16.3. Requires Next.js
16.3+ with `cacheComponents: true`; below that, none of the verdicts here mean
anything — upgrade with `npx @next/codemod@latest upgrade latest` first, then
read the version upgrade guide for what the codemod does not cover.

## Contents

- The model
- Adoption: enabling the flag — Adoption: the per-route loop
- Optimization: the loop and its gates — The rig — The `instant()` guard
- Blocking shapes and their fixes — Reusing loading UI
- Two navigations, two shells — After optimization

---

## The model

With `cacheComponents: true` every route must be prerenderable. A route that
reads request-time data outside a `<Suspense>` boundary is "blocking" and fails
the build. A read inside a `'use cache'` function is a cache boundary, not a
blocking read.

The goal state for a route that reads request data is Partial Prerender
(`◐` in the build's route table): a static shell prerenders and commits
immediately, and the request-specific parts stream in behind their fallbacks.

`export const instant = false` marks a segment as allowed to block. It clears
the error in dev and in the build. It does **not** make the route instant — it
records a decision to accept a blocking route. On a layout it covers the whole
subtree at build time, but client navigations still validate each descendant
segment on its own.

Two more traps worth knowing before you start. First, `◐` says a shell exists,
not that it has content: a `<Suspense>` boundary around the whole page body
prerenders an almost-empty document and still reports `◐`. Second, sync
non-deterministic calls (`new Date()`, `Date.now()`, `Math.random()`,
`crypto.randomUUID()`) fail the build **even with** `instant = false` — the
opt-out does not suppress them.

---

## Adoption: enabling the flag

Preconditions, all of them blocking:

- An App Router project. The flag does nothing for `pages/`. A hybrid app is
  fine — `app/` routes are affected, `pages/` routes are not.
- Locate `next.config.{js,ts,mjs,cjs}` first: that is the project root, and an
  agent invoked from a subdirectory otherwise looks for `app/` in the wrong
  place. If both `app/` and `src/app/` exist, Next.js builds `app/` and never
  looks at `src/app/` — say so and ask which tree is intended.
- Remove `experimental.dynamicIO`; it was renamed to top-level `cacheComponents`
  and the old key now aborts the build. `experimental.useCache` is a deprecated
  alias and redundant once `cacheComponents` is set.
- Inventory `export const dynamic`, `revalidate` and `fetchCache`.
  `cacheComponents: true` errors on any file that still exports one, and no
  codemod removes them. Translate each per the migration guide.
- A file with a top-level `'use cache'` directive cannot also export `instant`.
  If both are present, the directive was wrong for that route; remove it first.

If the app already uses `'use cache'`, the pre-flag build fails asking you to
enable the flag. Enabling it is therefore the first step, not a later one — say
so up front so it does not read as a regression.

Two strategies:

- **Quiet pre-step, then adopt.** Run
  `npx @next/codemod@latest cache-components-instant-false ./app` to insert
  `export const instant = false` plus a `// TODO: Cache Components adoption`
  comment into every `page` / `layout` / `default` file, set
  `cacheComponents: true`, get the build passing, ship that as one reviewable
  change, then remove the opt-outs feature by feature. The TODO comments are
  the work queue.
- **Straight through.** Set the flag and fix whatever the build reports, all on
  one branch.

The codemod refuses to run on a dirty tree, and a wrong path is not an error —
it reports `0 ok` and exits `0`, so read the file count. It opts out *every*
segment on purpose: resolution is top-down and the highest explicit config
wins, so with an opt-out on each segment, removing one validates only that
segment. Remove them top-down — a leaf's removal does nothing while an ancestor
still holds one.

---

## Adoption: the per-route loop

Work one product surface at a time (`app/settings/profile/**`, not
`app/dashboard/**`), layouts before pages.

- [ ] Remove the segment's opt-out (or target the failing route).
- [ ] Reload the route in `next dev` and read the overlay. `next dev` is the
      working surface: it reports per-route errors with stacks and fix cards.
      The route still returns HTTP 200, so read the overlay, not the status.
- [ ] Fetch the docs page linked from the error
      (`https://nextjs.org/docs/messages/<slug>`) and apply the recipe from
      there. The inline message is a summary; do not improvise from it.
- [ ] Verify in a browser that the first paint shows what you intended in the
      shell — not a fallback, not an empty shell streaming everything.
- [ ] Re-check siblings if the fix touched shared code. A layout change can fix
      one route and break its neighbour.
- [ ] `next build` as the gate for the feature.

A passing build mid-walk does not mean the layout is clean: while descendants
still hold their own opt-outs they shadow the inherited validation, so the
layout's blocking reads only surface once nothing below it shadows them.

Escalate rather than deciding alone when the blocking code is a security gate
(`await verifyAccess()`, an auth redirect, a flag check): wrapping a gate in
`<Suspense>` defeats it, and only the author knows whether to keep the route
blocking, restructure it, or move the check into `proxy.ts`. If a gate looks
redundant, say so plainly instead of quietly relocating it. A deliberate,
documented Block is a legitimate end state — keep `instant = false` and rewrite
its TODO into a reason; an undocumented leftover opt-out is not.

---

## Optimization: the loop and its gates

Run this once per target route, in order.

```
- [ ] P  PREREQS      16.3+ with cacheComponents; @next/playwright on the same release line
- [ ] 0  SETUP        once per repo: how this project builds, deploys, authenticates, tests
- [ ] A  RIG          a production build with the testing API exposed
- [ ] B  BASELINE     unlocked: the shell marker renders for the test user (delete before shipping)
- [ ] C  RED          locked instant(): the shell does not commit  ← this test ships
- [ ]    C-gate       is the RED trustworthy? stop until it is
- [ ] D  FIX          push each Suspense down to the read it guards
- [ ]    D1           reuse the route's existing loading UI
- [ ]    D2           the shell matches the real render at every breakpoint
- [ ] E  PARITY       only whether the route is instant has changed
- [ ] F  DIFFERENTIAL revert only the fix → RED; re-apply → GREEN
```

The verification loop is the invariant; the rig is yours. Maximizing the shell
is worthless unless you can prove it, and hand-timing a navigation is too flaky
to be a proof.

**The C-gate.** A RED that is red for the wrong reason sends you optimizing a
route that was never broken. The question that settles it: does the shell
marker render *without* the lock, as the test user? Answer it by re-running the
unlocked baseline as that user — not by adding assertions to the shipped test.

---

## The rig

Any production-like build that exposes the testing API: a local
`next build && next start`, a CI or staging container, a preview deploy. The
verdict comes from the build, not the platform. Two invariants:

- **Never measure on `next dev`.** It does not prefetch and its lock is
  unreliable for blocking routes, so a dev result is neither a valid RED nor a
  valid GREEN.
- **The build must expose the testing API**, or `instant()` silently no-ops and
  the test passes vacuously. Wire the flag to a condition true for every
  measured build and never true in production:

```ts
// next.config.ts
export default {
  cacheComponents: true,
  experimental: {
    // Use whatever your platform provides; record the choice with the rig.
    exposeTestingApiInProductionBuild: process.env.EXPOSE_TESTING_API === '1',
  },
}
```

For a deployed or remote build, confirm the artifact contains the commit under
test before trusting a verdict — a stale deploy reads as a false RED or GREEN.
Record the rig once per repository (how it builds, how the testing API is
exposed, how it runs, who the test user is) in a committed file, so later runs
read it instead of rediscovering it.

---

## The `instant()` guard

`instant()` from `@next/playwright` gates dynamic data and asserts what is
available immediately. It is a ruler, not a stopwatch: assert that the shell
appears under the lock; never add timeouts or timing races.

```ts
import { test, expect } from '@playwright/test'
import { instant } from '@next/playwright'

// A synchronous node of the destination's static shell — a header, an action
// button, a column heading. Never data that streams in, and never something
// gated by a flag, plan or role the test user lacks.
const SHELL_MARKER = '[data-testid="dashboard-shell"]'

test('dashboard shell commits under instant()', async ({ page }) => {
  await page.goto('/')
  const trigger = page.getByTestId('dashboard-link')
  await expect(trigger).toBeVisible()

  await instant(page, async () => {
    await trigger.click()
    await expect(page.locator(SHELL_MARKER)).toBeVisible()
  })
})
```

- **Soft navigation** — click a real `<Link>`; the committed shell is the
  destination's prefetched App Shell. Under the lock the router prefetches for
  you, so do not add waits or hovers.
- **Initial load** — call `page.goto()` inside `instant()` with the `baseURL`
  option, and establish the session without navigating the page (inject storage
  state, or log in on a separate context). A login helper that navigates the
  page itself completes before the lock engages, measuring the wrong navigation.
- Prefer a `data-testid` on a known-static node over a guessed role and
  accessible name, for both the marker and the trigger.

---

## Blocking shapes and their fixes

Each build error prints a `https://nextjs.org/docs/messages/<slug>` link — that
page is the recipe. The shapes below are the ones worth recognizing on sight.

**1. A top-level `await` in a page or layout.** The most common shape. It makes
everything below it dynamic. Pass the promise down and await it inside a
`<Suspense>`-wrapped child.

```tsx
// Incorrect — the top-level await blocks the whole subtree
export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const product = await db.products.findBySlug(slug)
  return <h1>{product.name}</h1>
}

// Correct — pass the promise down, await it inside the boundary
export default function Page({ params }: { params: Promise<{ slug: string }> }) {
  return (
    <Suspense fallback={<ProductSkeleton />}>
      <Product params={params} />
    </Suspense>
  )
}

async function Product({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const product = await db.products.findBySlug(slug)
  return <h1>{product.name}</h1>
}
```

A page-level `await params` blocks exactly the way the layout's does — fix both.

**2. `cookies()` or `headers()` in a layout.** Start the read without awaiting
it and pass the promise down; `{children}` and the surrounding chrome stay in
the shell while only the consumer streams.

```tsx
export default function Layout({ children }: { children: React.ReactNode }) {
  const cookieStore = cookies() // not awaited
  return (
    <body>
      <nav>
        <Suspense fallback={<UserMenuSkeleton />}>
          <UserMenu cookiePromise={cookieStore} />
        </Suspense>
      </nav>
      {children}
    </body>
  )
}
```

**3. An uncached fetch or database read.** Decide per source. Same for everyone
and rarely changing → `'use cache'`, and it joins the shell. Per-request and
must be fresh → leave it uncached behind a boundary.

```tsx
async function getProduct(slug: string) {
  'use cache' // resolved at prerender → lands in the shell
  return db.products.findBySlug(slug)
}
```

A bare `'use cache'` uses the `default` lifetime; choose one explicitly with
`cacheLife('<profile>')` — `default`, `seconds`, `minutes`, `hours`, `days`,
`weeks`, `max`. It is in-memory and does not persist across instances, so a
durable shell needs the remote cache variant.

**4. Dynamic `params`.** Enumerate them with `generateStaticParams` so `await
params` resolves at build time, or treat them as request-time and wrap the
consumers. When *any* dynamic segment in the route lacks
`generateStaticParams`, the route is a fallback route and **all** its params
defer to request time — including the enumerated ones.

**5. `searchParams`.** Never known at build time, so awaiting them (or calling
`useSearchParams()`) suspends on an initial load. Isolate the consumer. On a
client navigation the router already has the URL, so the same consumer resolves
synchronously — the boundary is still required for the page-load path.

**6. Non-deterministic values.** Choose: per-request → `await connection()`
inside a `<Suspense>`-wrapped child; fixed for everyone → `'use cache'`.

**7. Dynamic `generateMetadata`.** Prefer a static `metadata` export, or
`'use cache'` when it depends on external rather than request data. If it
genuinely needs `cookies()` or `headers()`, keep it dynamic and add a
`connection()`-gated marker component inside a boundary so the rest of the page
still prerenders. `generateViewport` is the same, except a dynamic viewport
blocks the whole page — there the only instant fixes are a static export or
`'use cache'`.

**8. Keep the LCP element out of every boundary.** Usually the main heading; it
cannot paint until the boundary resolves.

**9. Put the boundary below the shared layout.** One boundary in the root layout
passes an initial-load check while leaving sibling client navigations blocking.
Place it below the lowest layout the source and destination share, and prefer
several per-component boundaries in the page over one coarse layout boundary.

All nine avoid the same anti-pattern: one coarse `<Suspense>` high in the tree
keeps the layout UI out of the shell (only a throwaway copy is prerendered),
replaces the whole subtree when it resolves — discarding client state and
shifting layout — and its hand-built fallback drifts as the UI changes. **The
rule:** if an element renders in both the fallback and the resolved tree, hoist
it above the boundary.

---

## Reusing loading UI

Before writing a skeleton, look for the one that already exists, in this order:
the route's `loading.tsx`; an exported `*Skeleton` colocated with the component;
the fallback already inside the component's own `<Suspense>`.

The divergence point is the lowest layout the source and destination routes
share: a soft navigation re-renders only the segments below it, an initial load
re-runs every layout from the root. So a `loading.tsx` above the divergence
point fills only the initial-load shell; one at the destination segment serves
both.

If a component has no skeleton, extract its loading markup into a colocated
one. Do not author a fresh skeleton mirroring the page layout: it duplicates
structure, drifts as the page changes, and pulls the design back toward one
coarse boundary. `fallback={null}` is correct only where the deferred component
renders nothing on success — a gate, or a flag-gated control that would flash
and collapse. For data, the fallback must be a real skeleton.

A skeleton frozen to one breakpoint misaligns at the others. Let one responsive
component render both the live UI and the shell, and verify by re-asserting the
marker at two widths — `await page.setViewportSize({ width: 1280, height: 800 })`
then `{ width: 390, height: 844 }`.

---

## Two navigations, two shells

A route reaches the user two ways and both must be instant: an **initial load**
commits the prerendered static shell, and a **client navigation** commits the
destination's prefetched App Shell, re-rendering only the segments that change.
The fixes are identical; the test differs only in how the navigation is driven.
The two shells can differ — guard the one you ship, and both when both matter.
With parallel routes, only the slots that change re-render on a client
navigation, so do not chase a slot the navigation never touches.

**Parity check before shipping (phase E).** The push-down is a mechanical
transform, not a redesign: same tree, same data, same ordering, same empty and
error states, same redirects, same interactions. Confirm specifically that a
deferred `redirect()` or `notFound()` still fires (now at request time), that
both viewports reach the real UI after the stream, and that client state — open
menus, scroll, focus, input — survives. If anything else changed, reduce the
refactor.

**When URL data cannot be pushed down** — the whole page depends on `params`,
`searchParams` or the full URL — there may be no meaningful static shell. Do
not force one; per-link prefetching is a different mechanism with a per-link
server cost.

---

## After optimization

Check whether the app has adopted Partial Prefetching:

```bash
rg -n "partialPrefetching|prefetch\s*=\s*['\"]partial['\"]" --glob 'next.config.*' --glob 'app/**' --glob 'src/app/**'
```

`partialPrefetching: true` in the config means globally adopted; only
`prefetch = 'partial'` matches means an incremental rollout, and those
destination segments are the adopted ones. Once adopted, a targeted
`<Link prefetch={true}>` is worth considering for the URL-data routes that had
no shell to grow — and only there, so the shared App Shell stays the low-cost
default everywhere else.

<!-- sources: nextjs-cache-components, nextjs-docs -->
