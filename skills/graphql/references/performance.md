# Execution performance and demand control

Verified against: dataloader 2.2, graphql-js 17, Apollo Server 5.

## Contents

- [The N+1 problem](#the-n1-problem)
- [DataLoader: the two contracts](#dataloader-the-two-contracts)
- [Batching list-valued relationships](#batching-list-valued-relationships)
- [Batching counts and aggregates](#batching-counts-and-aggregates)
- [Batching outbound service calls](#batching-outbound-service-calls)
- [What batching does not fix](#what-batching-does-not-fix)
- [Depth limiting](#depth-limiting)
- [Breadth, alias and batch limiting](#breadth-alias-and-batch-limiting)
- [Complexity analysis](#complexity-analysis)
- [Rate limiting](#rate-limiting)
- [Caching](#caching)
- [Measuring](#measuring)

## The N+1 problem

GraphQL's execution model calls one resolver per field per object. A feed of 50 posts whose
`author` resolver fetches a row produces 1 query for the posts and 50 for the authors; add
`comments { author }` and it is hundreds. The pattern is inherent to field-level resolution, not
a mistake in any one resolver, which is why the fix is a batching layer rather than a rewrite of
the resolvers. [official]

The resolvers to look for are exactly those that cross a boundary — database, cache, HTTP
service — and run once per parent. Cheap-looking ones count: a `count(*)` per row is an N+1.

## DataLoader: the two contracts

DataLoader collects `load(key)` calls made in the same tick, calls your batch function once with
all the keys, and caches per key for the loader's lifetime. Two contracts, both of which are
violated constantly:

**1. Per-request lifetime.** Construct loaders when the request context is built, never at
module scope.

```js
// context factory — one set of loaders per request
export function createContext({ userId }) {
  return {
    userId,
    loaders: {
      author: new DataLoader((ids) => batchAuthors(ids)),
      commentsByPost: new DataLoader((postIds) => batchCommentsByPost(postIds)),
    },
  };
}

// resolver
const resolvers = {
  Post: {
    author: (post, _args, ctx) => ctx.loaders.author.load(post.authorId),
  },
};
```

A module-level loader is a process-lifetime cache: it serves data mutated by a later request,
and — the serious failure — it serves rows one user was authorised to load to a different user
who was not. This is the single most common DataLoader bug and it is a data-leak class bug, not
a performance one. [verified]

**2. The batch function returns `keys.length` values, in key order.** `null` (or an `Error`
instance) for keys with no row. Anything else silently misattributes children to parents:

```js
async function batchAuthors(ids) {
  const rows = await db.query('SELECT * FROM authors WHERE id = ANY($1)', [ids]);
  const byId = new Map(rows.map((r) => [String(r.id), r]));
  // Same length, same order as `ids`; misses become null.
  return ids.map((id) => byId.get(String(id)) ?? null);
}
```

Returning `rows` directly is wrong even when the count happens to match: SQL gives no ordering
guarantee, so post 7 gets post 3's author. Coerce the key type when building the map — a numeric
column and a string `ID` from GraphQL will not match otherwise.

Other details worth knowing:

- Returning an `Error` in a slot rejects only that `load()` call, which is how one missing row
  fails one field instead of the request.
- `loadMany` does not throw on individual failures; it puts the errors in the result array.
- The per-key cache means two fields asking for the same author in one request hit the database
  once. It also means a mutation inside the same request must `clear(key)` or `clearAll()` or
  later fields read pre-mutation data.
- `maxBatchSize` matters when the backend has a parameter limit (or a URL length limit for an
  HTTP batch endpoint).

## Batching list-valued relationships

A one-to-many relationship batches to one grouped query keyed by the parent id:

```js
async function batchCommentsByPost(postIds) {
  const rows = await db.query(
    'SELECT * FROM comments WHERE post_id = ANY($1) ORDER BY post_id, created_at',
    [postIds],
  );
  const grouped = new Map(postIds.map((id) => [String(id), []]));
  for (const row of rows) grouped.get(String(row.post_id))?.push(row);
  // Every key gets an array, empty where there are no rows.
  return postIds.map((id) => grouped.get(String(id)) ?? []);
}
```

If the relationship is paginated, the key is the parent id **plus** the page arguments, and the
batched query needs a per-parent window (a lateral join or a window function). Do not fetch every
child and slice in memory: that is the unbounded fetch the pagination existed to prevent.

## Batching counts and aggregates

`likeCount` resolved per post is one statement per row. Batch it:

```sql
SELECT post_id, count(*) AS n FROM likes WHERE post_id = ANY($1) GROUP BY post_id
```

Fill zero for keys absent from the result — `GROUP BY` returns no row for a post with no likes,
and a missing key becomes `null` on a field usually declared Int!, which then propagates
(`references/errors.md`). If the count is on a hot path and the table is large, a maintained
counter column beats any amount of batching.

## Batching outbound service calls

The same loader pattern applies to HTTP and RPC, and the win is larger because the per-call
overhead is larger:

```js
new DataLoader(
  (postIds) => ranking.scoreMany({ postIds, userId }),
  { maxBatchSize: 100 },  // the ranking API's documented cap
);
```

If the service has no batch endpoint, a loader still helps by deduplicating repeated keys within
one request, and the absent batch endpoint is worth raising with its owners.

## What batching does not fix

Batching reduces the number of round trips per level of the selection set. It does not bound the
selection set. `Post.author.posts.author.posts…` is cyclical: with perfect batching, each level
is one query, but the result set grows multiplicatively and so does the serialisation work. [official]

So batching is necessary and insufficient; the limits below are the other half. Apply them in
this order, because each one is cheaper to enforce than the next:

1. Paginate every growable list (`references/pagination.md`).
2. Depth limit.
3. Breadth, alias and HTTP-batch limits.
4. Complexity budget.
5. Rate limiting denominated in cost.

Everything from 2 onward is enforced **at validation time**, before any resolver runs, so a
rejected operation costs parsing rather than database load. [community]

## Depth limiting

Set a maximum operation depth — around 8–10 for a public API, higher for a first-party-only
graph where you know the deepest legitimate query. Reject beyond it before execution.

Then set a **separate, smaller limit on how deeply list fields nest**, because nested lists
multiply while nested single objects only add: `products(first:100) { reviews(first:100) }` is
10 000 nodes at depth 2. graphql.org calls this out specifically as a limit to configure apart
from overall depth. [official]

If a legitimate client genuinely needs a deep query, that client is a candidate for trusted
documents (which bypass the question entirely) rather than a reason to raise the global limit.

## Breadth, alias and batch limiting

Depth is not the only multiplier:

```graphql
query {
  viewer {
    a1: friends(first: 100) { name }
    a2: friends(first: 100) { name }
    # … a100
  }
}
```

Depth 3, one hundred expensive resolutions. Aliases let a client repeat the same expensive field
arbitrarily, so cap the number of root fields, the total selections and the alias count per
field. Cap the number of operations in an HTTP batch too, and note Apollo Server disables HTTP
batching entirely by default (`allowBatchedHttpRequests: false`) — leaving it off is the simplest
correct answer unless a client needs it. [verified]

Fragment recursion is a related multiplier: Apollo Server's `maxRecursiveSelections` computes the
selection count with named fragments recursively inlined and is **off** by default.

## Complexity analysis

Assign a cost to each field and reject operations over a budget:

```
scalar field            1
object field            2
list field              child cost × requested page size
expensive named field   explicit weight (search, aggregate, export)
```

The multiplication by page size is the point: it is what makes a nested connection expensive in
the model rather than only in production. Calibrate the budget so the heaviest legitimate client
operation passes with roughly 2× headroom, and log rejections so you find out when a real client
outgrows it. [community]

The GraphQL specification provides no cost model; a community draft cost specification exists,
and most servers offer a plugin. Whichever you use, the weights are yours to calibrate — a
default cost model that has never rejected anything is not demand control.

## Rate limiting

Per-request counting is nearly meaningless for GraphQL, because one request can be one field or
five hundred. Denominate the budget in cost points from the complexity model and deduct the
actual cost of each executed operation. Enforce it in the business-logic layer, where the
identity and the plan live, rather than in the network layer, which cannot see the cost. [official]

## Caching

- **`GET` for queries plus a document id** is the highest-leverage caching change available: the
  response becomes cacheable by a CDN. Servers following the GraphQL-over-HTTP specification
  support `GET` for queries; combine it with persisted documents so the URL stays short
  (`references/operations.md`). Watch Apollo Server's default CSRF prevention, which blocks
  `GET` requests without specific headers.
- **Response caching** on the server, keyed on the document id plus variables plus the
  authorisation scope. The scope is mandatory: a cache keyed on document and variables alone
  serves one user's data to another.
- **Client-side normalised caching** needs stable per-object identity, which is why cacheable
  types select `id` and why global object identification exists
  (`references/schema-design.md`).
- Enable gzip or brotli. GraphQL responses are repetitive JSON and compress unusually well. [official]

## Measuring

Do not assert a fix; count it.

- Instrument the data layer to log every statement with the operation name, and count statements
  per operation. A 50-post feed should be single-digit statements, not 51.
- Check the per-field timing your server exposes (a tracing plugin, or OpenTelemetry
  instrumentation) to find which resolver actually dominates before optimising it.
- Verify the limits with a hostile query: a deep cyclical selection, an alias-heavy selection and
  an oversized `first` should each be rejected before execution, and the rejection message should
  name the limit.
- Re-run the same operation after the change and report both numbers. "Added DataLoader" is not
  a result; "51 statements → 3" is.

<!-- sources: dataloader, graphql-org-learn, skillmedev-graphql-schema, apollo-server-defaults, apollo-skills-graphql, graphql-js -->
