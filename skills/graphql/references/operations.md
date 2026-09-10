# Writing operations

Verified against: GraphQL specification (October 2025 edition), graphql-js 17,
`@graphql-eslint/eslint-plugin` 4.

## Contents

- [Document hygiene](#document-hygiene)
- [Variables](#variables)
- [Fragments](#fragments)
- [Abstract types and `__typename`](#abstract-types-and-__typename)
- [`@skip` and `@include`](#skip-and-include)
- [Mutations](#mutations)
- [Subscriptions](#subscriptions)
- [Incremental delivery: `@defer` and `@stream`](#incremental-delivery-defer-and-stream)
- [Persisted and trusted documents](#persisted-and-trusted-documents)
- [Code generation](#code-generation)
- [Reviewing an operation](#reviewing-an-operation)

## Document hygiene

```graphql
query OrderDetail($id: ID!) {
  order(id: $id) {
    id
    status
    totalCents
    lineItems {
      id
      sku
      quantity
    }
  }
}
```

- **Name every operation.** The name is what appears in server logs, traces, per-operation
  metrics, allowlists and persisted-document registries. An anonymous `query { … }` is invisible
  in all of them.
- Give the name a shape you can grep for and that says what it is for: `OrderDetail`,
  `HomeFeedPage`, `PlaceOrder`, `OnOrderStatusChanged`. Prefixing with the operation type
  (`GetOrder`) is redundant with the keyword but harmless; be consistent either way.
- Operation names must be unique across the whole set of documents a client sends, because
  codegen and registries key on them. Two files with `query Order` collide.
- Select only the fields the caller uses. Over-selection costs resolver work on the server and,
  with a normalising client cache, keeps stale data alive.
- Do not select `id` "just in case" — but do select it on every type the client caches, because a
  normalising cache with no identity for a type will overwrite entries.

## Variables

Every dynamic value is a variable. Inline literals defeat operation registries (each distinct
value is a distinct document), defeat query-plan and document caches, and make the value
invisible to per-operation instrumentation.

```graphql
query Products($first: Int = 20, $after: String, $filter: ProductFilter) {
  products(first: $first, after: $after, filter: $filter) { … }
}
```

- The variable's declared type must match the argument's type, non-nullness included. A
  nullable variable cannot be passed to a non-null argument unless the variable has a default.
- Default values belong on the variable definition when the client owns the default, and on the
  schema argument when the server does. Do not duplicate them in both places with different
  values.
- An omitted variable and a variable explicitly set to `null` are different at the protocol
  level. If the server distinguishes "not provided" from "set to null", omit the key rather than
  sending `null`.
- Never build the document string by interpolation. It is a registry-buster, and with
  user-controlled input it is an injection into the document.

## Fragments

Define a fragment on the type whose fields it selects, and keep it next to the code that reads
those fields:

```graphql
fragment ProductCard on Product {
  id
  title
  priceCents
}

query Catalogue($first: Int = 20) {
  products(first: $first) {
    edges { node { ...ProductCard } }
  }
}
```

- Co-locating the fragment with the component that consumes it means the component declares its
  own data requirement; adding a field to the card is a one-file change and no screen silently
  loses data.
- Name fragments for the consumer, not the type: `ProductCard`, `OrderSummaryRow`. Fragment
  names must be unique across all documents, so a bare `ProductFields` in two features collides.
- Fragments can spread other fragments. Deep nesting is what makes a recursive fragment
  explosion possible, which is why some servers cap the recursive selection count — Apollo
  Server's `maxRecursiveSelections` is off by default.
- Prefer a fragment to a repeated field list, but do not create a fragment used once to hide a
  three-field selection.

## Abstract types and `__typename`

Any selection on a union or interface field selects `__typename` and gives the consuming code a
branch for a type it does not know:

```graphql
query Search($term: String!) {
  search(term: $term) {
    __typename
    ... on Post { id title }
    ... on Author { id handle }
  }
}
```

Unions and interfaces gain members. A client that renders nothing for an unrecognised
`__typename` degrades; a client that crashes on it takes the screen down when the server ships a
new type. This matters most in long-lived native apps, where old versions keep running against
an evolved schema. [official]

## `@skip` and `@include`

```graphql
query Order($id: ID!, $withInvoice: Boolean!) {
  order(id: $id) {
    id
    invoice @include(if: $withInvoice) { pdfUrl }
  }
}
```

- One document, two shapes. Useful when the same screen has a permission-gated section.
- The variable must be Boolean!, and both directives apply to fields, fragment spreads and
  inline fragments.
- With a normalising client cache, a conditionally excluded field is absent from the cached
  object, which can look identical to "null" in consuming code. Handle both.
- Do not use them to build a single mega-query with a dozen flags. Two named operations are
  easier to instrument, cache and reason about.

## Mutations

```graphql
mutation PlaceOrder($input: PlaceOrderInput!) {
  placeOrder(input: $input) {
    order { id status totalCents }
    userErrors { __typename message path
      ... on InsufficientStock { sku available }
    }
  }
}
```

- Always select `userErrors` (or every union member) — a mutation whose selection omits the error
  branch reports success on failure.
- Select the fields the UI needs to update from the returned entity so the client can refresh
  without a follow-up query.
- Top-level mutation fields execute **serially**, in the order written, while everything else may
  execute in parallel. Two mutations in one document are therefore ordered, but any error
  handling between them is yours: there is no transaction. If two writes must be atomic, that is
  one mutation on the server.

## Subscriptions

```graphql
subscription OnOrderStatusChanged($orderId: ID!) {
  orderStatusChanged(orderId: $orderId) { id status trackingNumber }
}
```

- One root field per subscription operation — the specification allows exactly one.
- The event payload is a normal type, so the same nullability reasoning applies; a subscription
  that pushes a non-null object which occasionally cannot be built will terminate rather than
  degrade.
- Transport is not specified by GraphQL. Server-Sent Events and the `graphql-transport-ws`
  WebSocket protocol are the two live options and clients must match the server
  (`references/servers.md`).
- Subscriptions are for events the client cannot poll for cheaply. A status that changes twice a
  day is a query on focus.

## Incremental delivery: `@defer` and `@stream`

`@defer` (on fragment spreads and inline fragments) and `@stream` (on list fields) let a server
send a fast first payload and fill in slow parts afterwards. graphql-js 17 ships both directives,
but incremental delivery is **not** part of the current specification edition and support varies
by server and client. [verified]

Treat it as opt-in and check three things before using it: the server executes it, the client
understands the multipart response, and any gateway or CDN in between does not buffer the
response into one chunk. If any is missing, split the screen into two operations instead.

## Persisted and trusted documents

For first-party clients, extract the documents at build time, register them, and have the client
send an identifier instead of the document text.

- **Trusted documents** are that registry used as an allowlist: the server executes only known
  ids. This is the strongest demand control available, because an attacker cannot express a new
  query at all. It is impossible for a public API, where clients' documents are unknown in
  advance. [official]
- **Automatic persisted queries** are a different thing with a similar name: the client sends a
  hash, the server asks for the full document when it does not recognise it, then caches it. That
  saves bytes and enables `GET` caching but is *not* an allowlist — anything can register.
- Either way, sending the id in a `GET` request makes the response cacheable by a CDN, which is
  the largest single performance win available to a read-heavy GraphQL API. Note that Apollo
  Server enables CSRF prevention by default, which blocks `GET` requests lacking specific
  headers; configure the client accordingly rather than disabling the protection.

Standardisation of persisted documents is in progress in the GraphQL-over-HTTP specification, so
the wire format is still implementation-specific. Read your server's documentation for the exact
parameter names.

## Code generation

Generate types from the schema plus the documents; do not hand-write response types.

- Generated types encode nullability. If the generated type says `string | null` and the code
  uses a non-null assertion to get past it, the code is wrong, not the type
  (`references/schema-design.md`).
- Run generation in CI against the deployed schema. A generated type that is only regenerated
  locally diverges silently, and the failure surfaces as a runtime undefined.
- Regenerate after every schema change and commit the output, or generate in the build — pick
  one and enforce it. Half-committed generated files are worse than either.
- Lint the documents: `@graphql-eslint/eslint-plugin` catches unnamed operations, unused
  variables, unused fragments, duplicate names, deprecated field usage and selections that do not
  validate against the schema. Run it on the operations, not only on the schema.

## Reviewing an operation

- Anonymous operation, or a name duplicated in another file.
- Inline literals where variables belong.
- Missing `__typename` on a union or interface selection, or no unrecognised-type branch.
- Non-null assertions in the consuming code on fields the schema declares nullable.
- A mutation selection with no error branch.
- Over-selection: fields nothing renders, or a whole fragment pulled in for one field.
- Paging that reconstructs cursors instead of passing back `pageInfo.endCursor`, or mixes
  `first`/`after` with `last`/`before`.
- Deprecated fields still selected — the lint rule reports these, and they are the reason the
  server cannot remove them.

<!-- sources: apollo-skills-graphql, graphql-org-learn, graphql-js, graphql-spec, apollo-server-defaults, graphql-hive-tooling -->
