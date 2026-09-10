# Pagination

Verified against: Relay Cursor Connections Specification, graphql.org/learn/pagination.

## Contents

- [What is a specification here and what is not](#what-is-a-specification-here-and-what-is-not)
- [The Connection shape](#the-connection-shape)
- [What a cursor contains](#what-a-cursor-contains)
- [Page-size caps](#page-size-caps)
- [Forward and backward paging](#forward-and-backward-paging)
- [`totalCount` and other connection fields](#totalcount-and-other-connection-fields)
- [Filtering and ordering alongside pagination](#filtering-and-ordering-alongside-pagination)
- [Connections on relationships](#connections-on-relationships)
- [When offset paging is the right answer](#when-offset-paging-is-the-right-answer)
- [Reviewing existing pagination](#reviewing-existing-pagination)

## What is a specification here and what is not

The GraphQL specification says nothing about pagination. The `edges`/`node`/`cursor`/`pageInfo`
shape comes from the **Relay Cursor Connections Specification**, which the GraphQL Foundation's
own learning material points to as the formal pattern to follow "whether or not you use Relay".
[official]

That distinction matters in practice: because it is a convention rather than a spec requirement,
every client's generated pagination helper matches it *by name*. Rename `pageInfo` to `page`, or
drop `hasPreviousPage`, and the shape still validates but the tooling stops working. Match it
exactly or do not claim to be a connection.

## The Connection shape

```graphql
type Query {
  products(
    first: Int
    after: String
    last: Int
    before: String
    filter: ProductFilter
    orderBy: ProductOrder = { field: CREATED_AT, direction: DESC }
  ): ProductConnection!
}

type ProductConnection {
  edges: [ProductEdge!]!
  pageInfo: PageInfo!
  """Exact count of matching products. Omit unless the UI needs it: this is a
  second, unindexed-in-the-worst-case query on every page."""
  totalCount: Int
}

type ProductEdge {
  node: Product!
  """Opaque. Position of this node in this ordering; not stable across orderings."""
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

Notes on the non-null choices, which are not arbitrary:

- The connection itself is non-null — the field always returns a page object, even an empty one.
- `edges` is a non-null list of non-null edges and `node` is non-null here because a product that
  exists in the page cannot fail on its own. If your nodes are hydrated from a separate service
  that can fail per item, `node: Product` and nullable edge elements are the honest shape —
  otherwise one missing node nulls the whole page (`references/schema-design.md`).
- `pageInfo` is non-null; `startCursor`/`endCursor` are nullable because an empty page has none.
- `totalCount` is nullable so you can decline to compute it.

Exposing a convenience `nodes` list alongside `edges` is allowed and common: clients that
need no edge metadata skip a level of indirection, and the cursors they need are already in
`pageInfo`. [official]

## What a cursor contains

A cursor is an opaque string. The client's only contract is: pass back what the server gave.
Server-side it must encode enough to build a seek predicate:

```
cursor = base64( "<sort key value>|<unique tiebreaker>" )
       e.g. base64("2026-02-11T09:31:00Z|prd_8fa21c")
```

- **The sort key**, so the next page starts where this one ended.
- **A unique tiebreaker** (usually the primary key), because sort keys collide — ten products
  created in the same millisecond will otherwise repeat or skip at the page boundary.
- Nothing else. No user id, no filter state, no signature: a cursor is a position, and stuffing
  authorisation context into it makes it a token you now have to validate.

The resulting query is a seek, not an offset:

```sql
-- forward page after (created_at, id)
WHERE (created_at, id) < ($cursor_created_at, $cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT $first + 1     -- the extra row is how you know hasNextPage
```

Base64 is there to signal opacity, not to provide security — it is trivially decodable, so never
put anything secret in it. Encoding an offset (`base64("offset:40")`) is legal but keeps every
offset problem; it is a migration step, not a destination.

`hasNextPage` comes from fetching `first + 1` rows and discarding the extra, which is why it is
cheap and `totalCount` is not.

## Page-size caps

Three numbers, all decided in the schema or the resolver rather than left to the caller:

- **Default** when the client omits `first`/`last`: 20–25 is a normal choice. Declare it in the
  SDL (`first: Int = 20`) so it shows up in introspection.
- **Maximum**: 100 is the conventional ceiling for a public API. Enforce it server-side.
- **Behaviour on excess**: return a request error naming the limit. Silently clamping to the
  maximum makes a client's paging loop silently wrong, and honouring `first: 100000` is a
  self-service denial of service. [community]

An unpaginated list field on a growable collection is the same problem with no dial at all,
which is why demand control starts with pagination rather than with rate limits
(`references/performance.md`).

## Forward and backward paging

- Forward: `first` + `after`.
- Backward: `last` + `before`.
- Do not mix them in one request. `first` with `before`, or `first` and `last` together, has no
  well-defined meaning; reject it as a request error rather than picking one.
- Backward paging is genuinely more work: you seek in the opposite direction, take `last` rows,
  and reverse them before building edges. Skip `last`/`before` entirely if no client needs it —
  but then say so in the field's description rather than declaring arguments you ignore.

## `totalCount` and other connection fields

`totalCount` is the field that quietly doubles the cost of every page: it cannot be derived from
the page you just fetched, so it is a second query, and on a filtered collection it is often the
expensive one. Options, in order of preference:

1. Leave it out. Most infinite-scroll and "load more" interfaces never render a total.
2. Expose it nullable and return null when it would be too expensive (a large filtered set),
   documenting that in the description.
3. Return an approximation from statistics, and name the field for what it is
   (`approximateTotalCount`).

The connection type is also the right place for aggregates that describe the whole matching
set rather than the page — `priceRange`, `facets`. Edge-specific data (when a membership was
created, who added the item) goes on the edge, which is the reason the edge layer exists at all.

## Filtering and ordering alongside pagination

```graphql
input ProductFilter {
  category: ID
  inStock: Boolean
  priceCentsMin: Int
  priceCentsMax: Int
}

enum ProductOrderField { CREATED_AT, PRICE, TITLE }
enum OrderDirection { ASC, DESC }

input ProductOrder {
  field: ProductOrderField!
  direction: OrderDirection!
}
```

- Ordering must be **total** for cursors to work: every `ProductOrderField` gets the same
  tiebreaker appended. An ordering by a non-unique column with no tiebreaker will duplicate rows
  at page boundaries no matter how good the cursor encoding is.
- A cursor is only valid within one ordering and one filter. Changing `orderBy` mid-pagination
  invalidates the cursor; either reject the request or document that the client must restart.
  Never silently reinterpret the cursor against the new ordering.
- Use an enum for sortable fields, not a free string. The set of columns you are willing to sort
  by is a closed set, and an index has to exist for each one.

## Connections on relationships

Every growable relationship field gets the same treatment as a root field:

```graphql
type Product {
  reviews(first: Int = 20, after: String): ReviewConnection!
  variants: [Variant!]!   # bounded by the product's own configuration
}
```

A list is only safe unpaginated when its size is bounded by something structural — enum-derived
permissions, size/colour variants, a user's roles. Say which bound in a comment or description;
"it is small today" is how a 40 000-review product happens.

Nested connections multiply: `products(first: 100) { reviews(first: 100) }` is 10 000 nodes from
a legal query. That is what nested-list depth limits and complexity budgets are for
(`references/performance.md`).

## Reviewing existing pagination

Symptoms and their causes:

| Symptom | Cause |
|---|---|
| Users see duplicate or missing items while scrolling | Offset paging over a list that receives writes, or a cursor with no unique tiebreaker. |
| Deep pages time out | Offset paging: the database counts and discards every skipped row. |
| Page boundaries repeat a few rows | Sort key collisions — the ordering is not total. |
| `hasNextPage` is wrong on the last page | Computed from `edges.length === first` instead of from an extra fetched row. |
| One page is fine, the report endpoint is not | A caller loops the connection with no server-side cap; cap `first` and consider a separate export path instead of paging a report. |
| Cursors stop working after a deploy | The cursor encodes something that changed (an offset, a table-local id, a version prefix). Cursors must survive deploys or be documented as ephemeral. |

<!-- sources: relay-connections, graphql-org-learn, apollo-skills-graphql, skillmedev-graphql-schema -->
