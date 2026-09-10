# Async rules — eliminating waterfalls

Highest-impact category. Every sequential `await` on independent work adds a
full round trip that the user waits through. These rules are framework-agnostic;
the server-only variants (`async-api-routes`, `server-parallel-*`,
`server-after-nonblocking`) live in the Next.js data reference.

Verified against: React 19.3.

## Contents

- `async-parallel` — await independent work together
- `async-dependencies` — partial dependencies
- `async-defer-await` — await inside the branch that uses it
- `async-cheap-condition-before-await` — cheap guard first
- `async-suspense-boundaries` — stream the wrapper, not the data
- Sharing one promise across components

---

## `async-parallel` — await independent work together

Impact: CRITICAL. Removes one round trip per collapsed `await`.

```ts
// Incorrect — three round trips, nothing depends on anything
const user = await fetchUser()
const posts = await fetchPosts()
const comments = await fetchComments()

// Correct — one round trip
const [user, posts, comments] = await Promise.all([
  fetchUser(),
  fetchPosts(),
  fetchComments(),
])
```

The signal to look for is a run of `await` statements where no later call
mentions an earlier result.

---

## `async-dependencies` — partial dependencies still parallelize

Impact: CRITICAL. When only *some* work depends on earlier results, a single
`Promise.all` followed by a dependent `await` still serializes the independent
tail.

```ts
// Incorrect — profile waits for config for no reason
const [user, config] = await Promise.all([fetchUser(), fetchConfig()])
const profile = await fetchProfile(user.id)

// Correct — build the chain as a promise, then await everything once
const userPromise = fetchUser()
const profilePromise = userPromise.then((user) => fetchProfile(user.id))

const [user, config, profile] = await Promise.all([
  userPromise,
  fetchConfig(),
  profilePromise,
])
```

The promise-chaining form needs no dependency. Reach for a dependency-graph
helper only when the graph is large enough that the chains stop being readable;
that is a judgement call, not a default.

---

## `async-defer-await` — await inside the branch that uses it

Impact: HIGH. An `await` above a branch is paid by every branch, including the
ones that return immediately.

```ts
// Incorrect — waits for user data even when skipping
async function handle(userId: string, skip: boolean) {
  const data = await fetchUserData(userId)
  if (skip) return { skipped: true }
  return process(data)
}

// Correct
async function handle(userId: string, skip: boolean) {
  if (skip) return { skipped: true }
  return process(await fetchUserData(userId))
}
```

The same shape appears in validation chains: fetch permissions *after* the
existence check, so a missing record costs one query instead of two.

Keep the original order when the later condition is expensive, depends on the
awaited value, or the calls have side effects that must run in a fixed order.

---

## `async-cheap-condition-before-await` — cheap guard first

Impact: HIGH. A specialization of the rule above for feature flags and remote
booleans combined with a local condition.

```ts
// Incorrect — pays for the flag lookup even when the local guard fails
const flag = await getFlag()
if (flag && isEligible) { /* ... */ }

// Correct
if (isEligible) {
  const flag = await getFlag()
  if (flag) { /* ... */ }
}
```

This matters because flag reads usually hit the network, a flag service or a
per-request cache. Reordering removes that cost from the cold path entirely.

---

## `async-suspense-boundaries` — stream the wrapper, not the data

Impact: HIGH. Awaiting data before returning JSX makes the whole layout wait for
the one section that needs it.

```tsx
// Incorrect — sidebar, header and footer all wait on fetchData()
async function Page() {
  const data = await fetchData()
  return (
    <div>
      <Sidebar />
      <Header />
      <DataDisplay data={data} />
      <Footer />
    </div>
  )
}

// Correct — the frame paints immediately, the data streams in
function Page() {
  return (
    <div>
      <Sidebar />
      <Header />
      <Suspense fallback={<Skeleton />}>
        <DataDisplay />
      </Suspense>
      <Footer />
    </div>
  )
}

async function DataDisplay() {
  const data = await fetchData()
  return <div>{data.content}</div>
}
```

Do not use this pattern when the data determines the layout (positioning
depends on it), when the content is above the fold and SEO-critical, or when the
query is fast enough that the fallback would flash. The trade is faster first
paint against a possible layout shift.

---

## Sharing one promise across components

When two components need the same data, start the fetch once and pass the
promise; `use()` unwraps it in each consumer and only one request happens.

```tsx
function Page() {
  const dataPromise = fetchData() // started, not awaited

  return (
    <Suspense fallback={<Skeleton />}>
      <DataDisplay dataPromise={dataPromise} />
      <DataSummary dataPromise={dataPromise} />
    </Suspense>
  )
}

function DataDisplay({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise)
  return <div>{data.content}</div>
}
```

Both consumers suspend on the same promise, so the boundary resolves once. This
is also the way to hand server-started work to a Client Component without
awaiting it on the server first.

<!-- sources: vercel-react-bp, react-docs -->
