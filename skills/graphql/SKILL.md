---
name: graphql
description: "Guides GraphQL schema and operation work: nullability and the non-null error propagation that turns one failing field into a null response, type and field naming, interfaces, unions, input objects and enum evolution, cursor Connection pagination and opaque cursors, error modelling (top-level errors versus a payload with userErrors), writing operations with named documents, variables and fragments, DataLoader batching for N+1, demand control through depth, breadth and complexity limits, trusted documents, server differences across graphql-js, Yoga, Apollo Server and Pothos, federated subgraphs with entities and @key, authorisation placement, introspection, and deprecating a field without breaking clients. Use when designing, reviewing, evolving or debugging a GraphQL schema, when a query returns null data or fires hundreds of database statements, or when writing queries, mutations and subscriptions. Do not use for REST and HTTP contract design or OpenAPI, nor for Apollo Client's React bindings and cache."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# graphql

## Scope

Covers the GraphQL API surface itself: schema design (types, field naming, nullability,
interfaces and unions, input objects, enums, custom scalars, global object identification),
pagination, error modelling, writing and reviewing operations, execution performance and
demand control, the differences between server implementations, federated subgraphs,
authorisation placement, introspection, and evolving a schema without breaking clients.

Facts here are checked against the GraphQL specification and graphql.org, then against
**graphql-js 17**, **GraphQL Yoga 5**, **Apollo Server 5** and **Pothos 4** where behaviour
differs by implementation. Rules that hold only for one server say so in the same sentence.

Not covered:

- REST and HTTP contract design — resource modelling, URI and status-code policy, RFC 9457
  error bodies, OpenAPI documents. Use the `api-design` skill. There is no "GraphQL version"
  of those decisions; a question about status codes is a question about HTTP.
- Apollo Client's React bindings and its normalised cache — hooks, `useSuspenseQuery`,
  `cache.modify`, optimistic UI. Use the `react` skill. This skill covers the operation
  documents such a client sends, not how a component subscribes to them.
- The Node process around a GraphQL server — HTTP framework wiring, configuration, logging,
  graceful shutdown, health checks. Use the `nodejs-backend` skill.
- Database schema and query tuning behind the resolvers — indexes, `EXPLAIN`, keyset
  predicates as SQL. Use the `postgres` skill; this skill only says which shape of query a
  batched resolver must ask for.
- Type-level modelling in TypeScript around generated operation types — use the `typescript`
  skill.
- Deciding what deserves a test — use the `test-driven-development` skill; the GraphQL-specific
  question of *what to assert* is in `references/servers.md`.
- Gateway and router operations (deployment topology, YAML configuration, traffic shaping,
  telemetry pipelines) are a product concern of whichever router you run, not part of this
  skill. Read that product's own documentation.

Paths below are relative to this skill's directory.

## Core rules

1. Read the SDL and the server setup before proposing anything. Which implementation is running,
   whether the schema is SDL-first or code-first, and whether this is a single graph or a
   subgraph decide which of these rules have a mechanism behind them in this codebase.
2. Fields are nullable by default deliberately: a networked service can lose a database, a
   downstream call or a field-level authorisation check, and a nullable field lets that one
   position degrade to null instead of failing the request. ` ! ` is a promise the server must
   keep, not a convenience for the client's generated types.
3. An execution error at a non-null response position propagates to its parent position. If the
   parent is nullable it becomes null; if it is also non-null the error keeps climbing. When
   every position from the root to the failure is non-null, the whole `data` entry is null —
   this is how a schema decorated with ` ! ` everywhere produces blank screens.
4. So add ` ! ` only where the position cannot fail independently of its parent: an `id` that came
   with the row, yes; a score from a ranking service, a URL from a CDN, a field one role cannot
   see, no.
5. `[T!]` means one failing element nulls the *entire* list, and a non-null list of those then
   nulls the list's parent. If partial results matter, the element type is what has to be
   nullable.
6. Non-null on the input side is the opposite trade: a required argument or input field costs
   nothing at runtime and removes a whole class of validation. The cost is later — adding a
   required argument or a non-null input field to a shipped schema is a breaking change.
7. Model the domain the clients render, not the tables behind it. A type that mirrors a table
   freezes today's storage layout into a contract you cannot version out of.
8. Return object types rather than scalar foreign keys. A field `author` typed as the `Author`
   object lets a client fetch what it needs; an `authorId` scalar forces a second round trip and
   never grows.
9. Use enums for closed sets instead of free strings, and treat the set as append-only:
   removing or renaming a value is breaking, and adding one breaks input positions and clients
   that switch exhaustively (`references/evolution.md`).
10. Give each mutation a single input object argument named after the operation
    (`placeOrder(input: PlaceOrderInput!)`), and name the mutation after the business operation
    rather than the CRUD verb.
11. A mutation returns a payload type: the affected entity, nullable, plus a non-null list of
    typed errors (userErrors: [UserError!]!). Use a result union instead only when the
    outcomes return genuinely different shapes — a payload can gain fields without breaking
    clients, a union cannot gain members safely.
12. The top-level `errors` array is for exceptional failures — infrastructure, an invalid
    document, missing authentication. Expected domain outcomes (coupon rejected, stock short,
    name taken) belong in the schema where they are discoverable and typed.
13. Never let an unknown error reach a client verbatim. Whether you have to do anything for
    that differs: Yoga masks by default, Apollo Server does not and ships stack traces unless
    `NODE_ENV` is `production` or `test` (`references/errors.md`).
14. Every list field that can grow gets a cursor Connection. This shape comes from the Relay
    cursor connections specification, not from the GraphQL specification, so match it exactly
    or clients' generated helpers will not work (`references/pagination.md`).
15. Give paginated fields a default page size and a server-enforced maximum, and make an
    out-of-range `first`/`last` a request error rather than silently clamping. An uncapped list
    argument is a self-service denial of service.
16. Cursors are opaque to clients and encode the sort key plus a unique tiebreaker, so the
    query behind them is a seek predicate. An offset dressed up as a cursor still duplicates and
    skips rows when the underlying list shifts between requests.
17. Keep exact counts off the hot path: `totalCount` is a separate, expensive query, so leave it
    nullable or off the connection instead of paying for it on every page.
18. Put authorisation in the business-logic layer and have resolvers call into it. Field
    resolvers are one entry point among several; duplicated rules drift, and the graph reaches
    every type it connects, so entry-point-only checks are not checks.
19. Construct DataLoaders per request and hand them to resolvers on the context. A loader
    shared across requests caches rows for the process lifetime, which serves stale data and
    leaks one user's authorised rows into another user's response.
20. A DataLoader batch function must return exactly `keys.length` values in the same order as
    `keys`, using `null` or an `Error` for misses. Returning whatever the database gave back
    silently attaches the wrong parent to the wrong child.
21. Bound the operation, not just the resolvers. Batching removes round trips but a cyclical
    selection set still multiplies work: set a depth limit, a separate smaller limit on nested
    list fields, caps on breadth, aliases and HTTP batching, and a complexity budget rejected at
    validation time — before the first resolver runs (`references/performance.md`).
22. For first-party clients, register the operations at build time and let the client send a
    document id (trusted documents). That is an allowlist, a smaller request, and — over `GET` —
    something a CDN can cache. It does not work for public APIs, where the demand-control limits
    above are the whole defence.
23. Evolve additively: add the new field, deprecate the old one with a reason that names the
    replacement, and remove it only after measured per-field usage reaches zero. Retyping or
    renaming in place is the one change GraphQL gives you no way to survive.
24. Apollo Federation is one implementation of federation, not a specification; the standards
    work is in the GraphQL Foundation's Composite Schemas working group. Write subgraphs against
    the federation version your gateway composes, and check the current directive set rather
    than copying a `@link` version from an example (`references/federation.md`).
25. Finish with the gate for the task you were doing — schema lint, a breaking-change diff, a
    statement count, or composition — and report the command and its output. "It should be
    fine now" is not a result.

## Workflows

### design-or-review-a-schema

- [ ] Start from what clients render, not from the tables: list the screens or use cases, the
      nouns they need, and the largest list each one can return.
- [ ] Name types and fields from the client's vocabulary, and check the mechanical rules
      (PascalCase types, camelCase fields, no `_tbl`/`_id`-scalar smells, enums instead of
      status integers) — `references/schema-design.md`.
- [ ] Audit nullability position by position: for each ` ! `, say what makes that position unable
      to fail independently. Anything crossing a network, a service or a field-level permission
      loses its ` ! `. Do the same for list element types.
- [ ] Give every growable list a Connection with a default and a maximum page size, and decide
      what the cursor encodes (`references/pagination.md`).
- [ ] Model the failures: which outcomes are exceptional (top-level `errors`) and which are
      domain results that belong in a payload's `userErrors` — `references/errors.md`.
- [ ] Decide whether clients need refetch-by-id or cache normalisation; if so, implement global
      object identification with `Node` rather than type-local integer ids.
- [ ] Write descriptions on every type, field and argument, including what a null means for the
      nullable ones.
- [ ] **Gate — the schema survives a hostile client:** `graphql-eslint` passes on the schema, a
      deliberately deep and alias-heavy query is rejected by the configured limits, and killing a
      downstream dependency degrades one field to null instead of nulling `data`.

### write-or-review-an-operation

- [ ] Read the schema first, not the client code: which fields are nullable, which lists are
      connections, which abstract types need `__typename`.
- [ ] Name the operation, pass every dynamic value as a variable, and select only the fields the
      caller uses (`references/operations.md`).
- [ ] Put reusable selections in fragments defined on the type they select from, co-located with
      the component or module that consumes them, rather than repeating field lists.
- [ ] Select `__typename` on every union and interface field, and give the consuming code a
      branch for a type it does not recognise — schemas gain members.
- [ ] Handle the nullable fields as nullable. A non-null assertion on the client side converts a
      graceful partial response into a crash.
- [ ] For paginated fields, take the cursors from `pageInfo`, keep them opaque, and do not mix
      `first`/`after` with `last`/`before` in one request.
- [ ] **Gate — the document is valid and typed:** `graphql-eslint` passes on the operation
      documents, code generation succeeds against the current schema, and the generated types
      show the nullability the code actually handles.

### fix-n-plus-1-or-an-expensive-query

- [ ] Measure before changing: log the statements and outbound calls one representative
      operation issues, so you know the number you are trying to move.
- [ ] Map each resolver that crosses a database or service boundary. Every one that runs once
      per parent row is an N+1, including the ones that look cheap (`count(*)` per row).
- [ ] Add a DataLoader per boundary, constructed per request on the context, with a batch
      function that returns `keys.length` results in key order — `references/performance.md`.
- [ ] For list-valued relationships, batch to one grouped query keyed by the parent id; for
      counts, one grouped aggregate or a counter column, not one statement per parent.
- [ ] Batch outbound service calls the same way rather than per item.
- [ ] Then bound the operation itself: depth, nested-list depth, breadth and alias caps, and a
      complexity budget enforced at validation. Batching a cyclical query only makes it cheaper
      per level, not bounded.
- [ ] Paginate the list fields the expensive selection reached, if they are not paginated already.
- [ ] **Gate — the number moved and stays moved:** re-run the same operation and report statement
      and call counts before and after, and show that the hostile deep query is now rejected
      before execution.

### evolve-a-schema-without-breaking-clients

- [ ] Classify every requested change first: additive (new type, new field, new optional
      argument, new output enum value) or breaking (retype, rename, remove, new required
      argument or non-null input field, new union member, removed enum value) —
      `references/evolution.md`.
- [ ] For each breaking change, design the additive equivalent: a new field beside the old one,
      a new mutation beside the old one, a new enum value served alongside the old one.
- [ ] Mark the superseded element `@deprecated(reason: "...")` with a reason that names the
      replacement, and keep serving it.
- [ ] Find out who still uses it — per-field usage from your own instrumentation or registry —
      and set removal on measured traffic reaching zero, not on a release count.
- [ ] Tell the clients what to do to be safe next time: default branches on enums, `__typename`
      plus an unknown-type branch on abstract types, no force-unwrapping of nullable fields.
- [ ] Resist versioning the endpoint. A `/graphql/v2` doubles the surface you operate and throws
      away the one property that makes additive evolution work: clients only receive the fields
      they asked for.
- [ ] **Gate — the diff says what you think it says:** run a schema diff against the deployed
      schema (`npx @graphql-inspector/cli diff <old> <new>`, or your registry's check) and show
      that every reported breaking change is one you intended.

### add-or-change-a-federated-subgraph

- [ ] Establish the mechanics of the graph you are joining: which federation version the gateway
      composes, which directives that version provides, and which subgraph currently owns each
      type you are touching.
- [ ] Opt this subgraph in with `extend schema @link(...)`, importing only the directives it
      uses, and take the version from the graph's current one rather than from an example
      (`references/federation.md`).
- [ ] Define entities from the identity the whole graph shares: `@key(fields: "...")` on fields
      that are stable, non-null and resolvable in this subgraph, plus a reference resolver that
      can hydrate an object from that key alone.
- [ ] Decide ownership per field, deliberately: one owning subgraph, `@shareable` where two can
      genuinely resolve the same value, `@override` for a migration in progress, `@inaccessible`
      for something composed but not public.
- [ ] Make sure the reference resolver is batched — it is called once per key the gateway needs,
      which is the federated form of N+1.
- [ ] **Gate — it composes and nothing else breaks:** run composition and the subgraph check
      against the current graph, and confirm no other subgraph's fields changed shape.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Type and field naming, nullability reasoning, interfaces versus unions, input objects and `@oneOf`, enums, custom scalars, global object identification, descriptions | Designing or reviewing any part of the type system | `references/schema-design.md` |
| Relay Connection shape, `pageInfo`, cursor contents and encoding, page-size caps, offset and keyset trade-offs, connections on relationships, `totalCount` | A list field can grow, or paging duplicates and skips rows | `references/pagination.md` |
| Top-level `errors` versus errors-as-data, payload `userErrors`, result unions, error codes and `extensions`, interaction with non-null propagation, masking defaults per server | Choosing how a failure reaches the client, or an error leaks or disappears | `references/errors.md` |
| Operation naming, variables, fragments and co-location, `__typename`, `@skip`/`@include`, `@defer`/`@stream` status, persisted and trusted documents, code generation | Writing or reviewing query, mutation and subscription documents | `references/operations.md` |
| N+1 and DataLoader (per-request lifetime, the batch-function contract), aggregate batching, depth and nested-list limits, breadth and alias caps, complexity analysis, `GET` and CDN caching | An operation is slow or chatty, or the API has no demand control | `references/performance.md` |
| graphql-js, Yoga, Apollo Server and Pothos differences, security-relevant defaults, subscription transports, resolver and context conventions, what to assert in tests | Wiring or hardening a server, or a rule behaves differently than documented | `references/servers.md` |
| Entities and `@key`, reference resolvers, `@external`/`@requires`/`@provides`/`@override`/`@shareable`/`@inaccessible`, composition failures, gateway behaviour | Working in a subgraph or debugging composition | `references/federation.md` |
| Breaking versus additive change classification, `@deprecated`, removal on measured usage, enum and abstract-type evolution, client-side robustness, schema diff gates | Changing anything already served to a client | `references/evolution.md` |

## Output format

When reviewing a schema or an operation, group findings by file and lead each with the location:

```
schema/order.graphql
  L14 Order.trackingNumber: String!  — non-null on a field the carrier populates later.
    A parcel not yet accepted makes Order null, and Query.order is non-null, so data is null.
    -> trackingNumber: String
  L31 Order.lineItems: [LineItem!]!  — unbounded list.
    -> lineItems(first: Int = 20, after: String): LineItemConnection!
```

Then one **Verdict** line naming the single change with the largest effect, and a **Gate** line
with the command that proves it. Order findings by consequence — a nullability chain that can
blank a screen, an unbounded list, a shared loader — not by line number.

## Environment

- Schema and operation linting: `npx @graphql-eslint/eslint-plugin` through an ESLint config, or
  the project's existing lint task. It needs to know where the schema and the documents are; if
  the project has no `graphql-config`, say so rather than guessing paths.
- Breaking-change diff: `npx @graphql-inspector/cli diff <old-schema> <new-schema>`. Both
  arguments accept a file, a URL or a `git:` reference, so the deployed schema can be the
  baseline directly.
- Federated graphs use their gateway's own composition and subgraph checks instead of the plain
  diff; the plain diff cannot see the other subgraphs.
- Verifying `data: null` behaviour needs no tooling: run the operation with the failing
  dependency actually failing and read the response. A unit test that stubs the resolver to
  return a value proves nothing about propagation.
- When a command named here is not the one this project uses, name the project's command instead
  of substituting your own.
