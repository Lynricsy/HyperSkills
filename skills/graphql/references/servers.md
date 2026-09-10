# Server implementations

Verified against: graphql-js 17.0.2, GraphQL Yoga 5.22, Apollo Server 5.5, Pothos 4.13.

## Contents

- [What is common and what is not](#what-is-common-and-what-is-not)
- [Defaults that differ](#defaults-that-differ)
- [graphql-js](#graphql-js)
- [GraphQL Yoga](#graphql-yoga)
- [Apollo Server](#apollo-server)
- [Pothos](#pothos)
- [SDL-first versus code-first](#sdl-first-versus-code-first)
- [Resolver signature and context](#resolver-signature-and-context)
- [Subscription transports](#subscription-transports)
- [Non-JavaScript servers](#non-javascript-servers)
- [What to assert in tests](#what-to-assert-in-tests)

## What is common and what is not

Every JavaScript GraphQL server in common use executes through **graphql-js**. So the type
system, validation rules, execution order, coercion and error propagation are identical
everywhere, and any rule about *those* is a GraphQL rule.

What differs is the layer around execution: the HTTP handling, the defaults for what reaches a
client, the plugin or middleware model, and how the schema is constructed. Rules about *those*
are product rules and must name the product.

The practical consequence when reviewing: a claim like "GraphQL masks internal errors" is false
as stated. Masking is a Yoga default and an Apollo Server opt-in.

## Defaults that differ

| Behaviour | graphql-js 17 | Yoga 5 | Apollo Server 5 |
|---|---|---|---|
| Plain `Error` from a resolver | message passed through | masked to `Unexpected error.` | message passed through, `extensions.code: INTERNAL_SERVER_ERROR` |
| Stack traces in responses | not added | only when `NODE_ENV=development`, under `extensions.originalError` | `includeStacktraceInErrorResponses` defaults **true** unless `NODE_ENV` is `production` or `test` |
| Introspection | not its concern | enabled; disable with a plugin | `introspection` defaults **true**, and **false** when `NODE_ENV=production` |
| "Did you mean …" validation hints | `hideSuggestions` execution option | passed through | `hideSchemaDetailsFromClientErrors` defaults **false**; Apollo's docs recommend enabling in production |
| HTTP request batching | not its concern | plugin | `allowBatchedHttpRequests` defaults **false** |
| CSRF protection on `GET` | not its concern | not enabled by default | `csrfPrevention` **enabled** by default; blocks `GET` without specific headers |
| Recursive-fragment selection cap | none | none | `maxRecursiveSelections` defaults **false** (10 000 000 when `true`) |
| Parsed-document cache | caller's job | built in | `documentStore`, ~30 MiB LRU by default |
| Automatic persisted queries | not its concern | plugin | `persistedQueries` supported; **not** an allowlist |

Two takeaways worth carrying into any review:

- On Apollo Server the security posture depends on `NODE_ENV` being set correctly in the deployed
  environment. An unset `NODE_ENV` in production means introspection on and stack traces in
  responses. Assert it, or set `nodeEnv` explicitly on the constructor.
- On Yoga the risk runs the other way: masking is on, so an intended user-facing message
  disappears unless it is thrown as a `GraphQLError`.

## graphql-js

The reference implementation and the semantics everything else inherits.

- Version 17 is current (`graphql@17.0.2`). Notable for review purposes: `@oneOf` is a specified
  directive; `@defer`/`@stream` directives exist though incremental delivery is not in the
  current specification edition; and the operation-level
  `@experimental_disableErrorPropagation` directive turns null-bubbling off for one operation.
  The last is experimental — recognise it, do not adopt it in place of correct nullability
  (`references/schema-design.md`).
- `hideSuggestions` is an execution option, so a server built directly on graphql-js has to pass
  it; there is no framework doing it for you.
- Building a schema with `buildSchema(sdl)` gives you no resolvers — it is for tooling and tests.
  A real SDL-first server uses `makeExecutableSchema` from graphql-tools or its framework's
  equivalent.

## GraphQL Yoga

Batteries-included server on the WHATWG Fetch API, so the same code runs on Node, Bun, Deno,
Cloudflare Workers and other Fetch-based runtimes.

- Schema from `createSchema({ typeDefs, resolvers })`, or any executable schema built elsewhere.
- Error masking is the default, and the escape hatch is throwing `GraphQLError` with
  `extensions`. `maskedErrors: { isDev: false }` keeps `originalError` out of extensions even
  under `NODE_ENV=development`; disabling masking altogether is not recommended, because it makes
  development behaviour diverge from production. [official]
- Plugins come from the envelop ecosystem, which is where depth limiting, complexity analysis,
  response caching, persisted operations and disabled introspection live. Yoga ships fewer
  opinions than Apollo Server, so the demand-control checklist is work you do explicitly.
- Subscriptions default to Server-Sent Events, which needs no extra protocol on the client.

## Apollo Server

- Version 5 (`@apollo/server@5.5.1`). `new ApolloServer({ typeDefs, resolvers })` plus a
  framework integration (`startStandaloneServer`, `expressMiddleware`, …).
- The defaults table above is the part to internalise; the rest of the API is product surface
  best read from its own documentation when you need it.
- `formatError` is the single place to normalise the error shape: map internal errors to a
  generic message plus a correlation id, keep the `extensions.code` you intend to publish, and
  drop everything else.
- Subgraph schemas use `buildSubgraphSchema` rather than `makeExecutableSchema`
  (`references/federation.md`).
- `maxCoercionErrors` (default 50) bounds how many variable-coercion errors are collected before
  execution stops — relevant when a client sends a large malformed input array.

## Pothos

Code-first schema builder for TypeScript. The schema is TypeScript that produces a graphql-js
schema; the SDL is an output, not the source.

- The payoff is that resolver argument and return types are checked against the schema by the
  compiler, so a renamed field is a type error rather than a runtime null. The cost is that the
  schema is not readable as a document — generate and commit the SDL so reviewers and schema
  diffs have something to look at.
- `@pothos/plugin-relay` generates Connection types and the `Node` interface, which is the
  fastest correct route to the pagination shape in `references/pagination.md`.
- Field nullability is explicit per field (`nullable: true`); the builder's default is non-null,
  which is the opposite of SDL's default. That makes the nullability audit *more* important in a
  Pothos codebase, not less, because the safe choice needs a keystroke.
- Version 4 is current (`@pothos/core@4.13.1`).

## SDL-first versus code-first

| | SDL-first | Code-first |
|---|---|---|
| Source of truth | `.graphql` files | builder code |
| Review artefact | the SDL diff | generated SDL, if you commit it |
| Resolver/schema drift | possible; needs codegen or tests to catch | impossible for shapes the compiler sees |
| Non-developer readability | good | poor without generated SDL |
| Dynamic schemas (per-tenant fields) | awkward | natural |

Pick per project and do not mix. If the project is code-first, add generated-SDL output to the
build so schema diff gates still work (`references/evolution.md`).

## Resolver signature and context

`(parent, args, context, info)` in every JavaScript server.

- `context` is built per request and is the only correct home for request-scoped state: the
  authenticated user, the DataLoaders, a request id, an abort signal. Anything on module scope is
  process-scoped and leaks across requests (`references/performance.md`).
- `parent` is whatever the parent resolver returned, not the GraphQL type. This is why returning a
  database row works — and why a field resolver reading `parent.author_id` after someone renames
  a column fails at runtime rather than at build time in an SDL-first server.
- `info` carries the field's AST and path. Using it to inspect the client's selection set (to
  build a narrower database query) is legitimate and effective, but it couples the resolver to
  query shape — keep that logic in one place rather than sprinkling `info` inspection around.
- Only top-level `Mutation` fields execute serially; everything else may execute in parallel.
  Resolvers must therefore be side-effect free except for mutation roots.

## Subscription transports

The specification does not define a transport. Two live choices:

- **Server-Sent Events** — plain HTTP, works through most proxies, one-directional, no extra
  client protocol. Yoga's default; the simplest thing that works.
- **`graphql-transport-ws` over WebSocket** — bidirectional, supports connection-level
  initialisation payloads for auth. Needed if the client library expects it.

The deprecated `subscriptions-transport-ws` protocol is a different, incompatible wire format;
a client and server disagreeing about which one they speak fails at connection time with an
unhelpful error. Check both ends when subscriptions "just do not connect".

## Non-JavaScript servers

The type system and execution semantics are the same; the ecosystem names change. Strawberry and
Graphene in Python, graphql-java and DGS in Java, gqlgen in Go, Absinthe in Elixir, async-graphql
in Rust. When working in one of those, everything in `references/schema-design.md`,
`references/pagination.md`, `references/errors.md`, `references/operations.md` and
`references/evolution.md` still applies verbatim; only the wiring in this file and the DataLoader
package name change. Check that language's DataLoader equivalent for the same two contracts —
per-request lifetime and key-ordered results.

## What to assert in tests

Test through the schema, executing real documents against a real schema, rather than calling
resolver functions directly. A resolver unit test cannot observe coercion, validation,
nullability propagation or the response shape, which is where the interesting bugs are.

Worth asserting:

- The nullability contract: make a fallible dependency fail and assert the response has the
  sibling data plus one `errors` entry with the right `path`, **not** `data: null`. This is the
  only way to catch an accidental ` ! `.
- The error contract: a domain failure returns a payload with populated `userErrors` and a null
  entity, and an infrastructure failure returns a masked message.
- Pagination: two consecutive pages over a list that received a write in between contain no
  duplicated and no skipped node.
- Demand control: the hostile deep query, the alias-heavy query and an oversized `first` are each
  rejected before execution.
- Authorisation: the same document as two different users returns different fields, exercised
  through the schema.

Not worth asserting: that a field exists, that a resolver returns what the stub returned, or a
snapshot of the whole introspection result. Schema shape is what the schema diff gate is for
(`references/evolution.md`).

<!-- sources: graphql-js, graphql-yoga, apollo-server-defaults, pothos, apollo-skills-graphql, graphql-org-learn, dataloader -->
