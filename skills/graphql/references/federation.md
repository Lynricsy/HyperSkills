# Federation

Verified against: Apollo Federation 2.x directive set; graphql.org/learn/federation.

## Contents

- [Federation is a pattern, not a specification](#federation-is-a-pattern-not-a-specification)
- [The pieces](#the-pieces)
- [Opting a subgraph in](#opting-a-subgraph-in)
- [Entities and `@key`](#entities-and-key)
- [Reference resolvers](#reference-resolvers)
- [Who owns a field](#who-owns-a-field)
- [`@external`, `@requires`, `@provides`](#external-requires-provides)
- [Authorisation directives](#authorisation-directives)
- [Composition failures](#composition-failures)
- [What belongs in a subgraph and what does not](#what-belongs-in-a-subgraph-and-what-does-not)
- [Reviewing a subgraph change](#reviewing-a-subgraph-change)

## Federation is a pattern, not a specification

Federation composes several independently deployed GraphQL services (subgraphs) into one schema
that clients query through a gateway. It is an **architectural pattern**. Apollo introduced
Apollo Federation in 2019 and that implementation became the community reference point, but the
GraphQL specification says nothing about it; the standardisation work is happening in the GraphQL
Foundation's Composite Schemas working group, with participants from several vendors. [official]

So everything below — `@key`, `@shareable`, `@external`, the `_entities` resolution mechanism —
is Apollo Federation 2 vocabulary. Other implementations exist and use overlapping but not
identical directive sets. Before writing directives, establish which implementation and which
version the gateway actually composes, and read that version's directive list rather than
copying one from an example, including this one.

Also worth saying out loud when someone asks for federation: it is infrastructure. It needs a
gateway, a schema registry, composition in CI and someone who owns all three. A single graph
that a few teams contribute to through one repository is a legitimate destination, not a
transitional state — Meta has run a monolithic GraphQL API since 2012. Start there and federate
when team boundaries, not fashion, force it. [official]

## The pieces

```
        client
          │  one schema, one endpoint
      ┌───▼────┐
      │gateway │  parses, plans, fans out, stitches the response
      └─┬──┬──┬┘
   ┌────┘  │  └────┐
┌──▼──┐ ┌──▼──┐ ┌──▼──┐
│users│ │order│ │catal│   subgraphs: ordinary GraphQL servers
└─────┘ └─────┘ └─────┘   plus federation directives and an entity resolver
```

- **Subgraph** — a normal GraphQL server that additionally declares which of its types are
  entities and how to resolve them from a key.
- **Composition** — a build step that merges the subgraph schemas into one supergraph schema,
  failing when they contradict each other. This is where most federation work actually happens.
- **Gateway (or router)** — plans a client operation into subgraph requests, executes them, and
  assembles the response. Its configuration, deployment and telemetry are that product's
  concern, not this skill's.
- **Schema registry** — stores the composed schema and runs checks before a subgraph deploys.

## Opting a subgraph in

Federation 2 subgraphs opt in explicitly and import only the directives they use:

```graphql
extend schema
  @link(
    url: "https://specs.apollo.dev/federation/v2.x"
    import: ["@key", "@shareable", "@external", "@requires", "@provides"]
  )
```

The version in the `url` is the **floor** the subgraph requires, not the version composition
runs at. Take the value from your graph's current supported set; a version copied from a blog
post either fails to compose or silently forgoes directives you meant to use. [official]

In Apollo Server, the executable schema for a subgraph comes from `buildSubgraphSchema` rather
than `makeExecutableSchema` — that is what adds `_service` and `_entities` to the schema
(`references/servers.md`).

## Entities and `@key`

An entity is a type more than one subgraph can talk about, identified by a key the whole graph
agrees on:

```graphql
type Product @key(fields: "id") {
  id: ID!
  title: String!
  priceCents: Int!
}
```

Rules that come up in review:

- The key must uniquely identify the entity. Key fields cannot include union or interface
  fields, cannot include fields that take arguments, and should be non-null.
- Compound keys are a field set: `@key(fields: "username domain")`. Nested selections are
  allowed: `@key(fields: "id organization { id }")`.
- `@key` is repeatable. A type may have several keys, and different subgraphs may use different
  keys as long as they share at least one.
- `@key(fields: "id", resolvable: false)` declares "I reference this entity but cannot resolve
  it" — the right shape for a subgraph that only holds a foreign key.
- Key fields are implicitly shareable; you do not mark them `@shareable`.

Choose the key from identity the domain already shares — the id every system uses. A key that is
one subgraph's internal primary key forces every other subgraph to store and migrate it.

## Reference resolvers

Each subgraph that resolves an entity implements a resolver that hydrates the object from the
key alone:

```js
const resolvers = {
  Product: {
    // Called with exactly the key fields, nothing else.
    __resolveReference: (ref, ctx) => ctx.loaders.product.load(ref.id),
  },
};
```

Two things go wrong here reliably:

- **It is called once per key.** The gateway asks for many products in one `_entities` request,
  and a reference resolver that queries per key is N+1 across a service boundary — the most
  expensive kind. Route it through a DataLoader like any other boundary crossing
  (`references/performance.md`).
- **It receives only the key.** Code that reads `ref.title` works in local tests, where the
  parent object happens to be complete, and returns undefined in the composed graph.

## Who owns a field

Every field in the supergraph is resolved by exactly one subgraph unless you say otherwise:

| Situation | Directive |
|---|---|
| One subgraph owns this field | nothing; the default |
| Two subgraphs can genuinely resolve the same value identically | `@shareable` on the field or the type |
| Moving a field from one subgraph to another | `@override(from: "OtherSubgraph")` on the new owner |
| Composed but not published to clients | `@inaccessible` |
| Adding fields to every implementation of an entity interface | `@interfaceObject` |

Notes:

- `@shareable` must agree across subgraphs: a field marked shareable in one must be `@shareable`
  or `@external` in the others. Type-level `@shareable` applies only to fields in that same
  declaration, not to later `extend type` blocks.
- `@shareable` on a field two subgraphs compute *differently* is a bug that composition cannot
  catch — the client gets whichever the query planner picked. Use it for values that are
  genuinely the same, not to end a composition error.
- `@override` cannot target `@external` fields, fields carrying `@provides`/`@requires`, or the
  subgraph itself, and `from` must match the subgraph name exactly.
- `@inaccessible` is the tool for landing a shared field in stages: add it everywhere marked
  inaccessible, then remove the directive once every subgraph has it. It is also how a key field
  or a `@requires` dependency stays private (`references/evolution.md`).

## `@external`, `@requires`, `@provides`

```graphql
type Product @key(fields: "id") {
  id: ID!
  weightGrams: Int @external          # owned by the catalogue subgraph
  shippingCents: Int @requires(fields: "weightGrams")
}
```

- `@external` marks a field this subgraph does not own but needs to reference.
- `@requires` declares that resolving this field needs those external fields, so the gateway
  fetches them first. Every `@requires` is an extra hop in the query plan — a field with a large
  `@requires` selection is usually a sign the field is on the wrong subgraph.
- `@provides` says "when you reach this entity through *this* field, I can already supply these
  fields", letting the planner skip a hop. It is an optimisation and it must be true: promising
  a field you sometimes cannot supply produces nulls the schema says are impossible.

## Authorisation directives

Federation 2.5+ adds `@authenticated`, `@requiresScopes(scopes: [[...]])` and (2.6+)
`@policy(policies: [[...]])`, evaluated by the router before it plans. The nested array is a
disjunction of conjunctions: the inner array is AND, the outer is OR.

These enforce coarse gates at the edge. They do not replace authorisation in the business-logic
layer — the subgraph is still reachable by anything inside the network, and per-object rules
("the author may see their own draft") are not expressible in scopes
(`references/schema-design.md`).

## Composition failures

Composition fails when subgraphs disagree, and the error names the rule. The recurring causes:

- The same type defined in two subgraphs with fields that are not marked `@shareable`.
- A field with the same name and different types across subgraphs — including a nullability
  difference, which is a type difference.
- An entity referenced with a key no subgraph declares `resolvable`.
- An enum used in both input and output positions whose value sets differ between subgraphs.
- A `@requires` or `@provides` naming a field that is not `@external` in this subgraph.
- Two subgraphs contributing the same root field name.

Fix the disagreement rather than silencing it. Adding `@shareable` to make an error go away is
how two subgraphs end up returning different values for the same field.

## What belongs in a subgraph and what does not

Everything in `references/schema-design.md`, `references/pagination.md`, `references/errors.md`
and `references/evolution.md` applies unchanged inside a subgraph — a subgraph is an ordinary
GraphQL schema. Federation adds ownership, not different design rules.

Two things get harder and are worth planning for:

- **Pagination across subgraphs.** A connection whose nodes come from another subgraph resolves
  page by page through `_entities`; the cursor and the ordering must be owned by the subgraph
  that owns the list, not reconstructed by the gateway.
- **Errors.** A subgraph failure surfaces as an error at the client's path, and non-null
  propagation applies across the join too — a non-null field owned by a down subgraph nulls its
  parent in the composed response exactly as it would locally.

## Reviewing a subgraph change

- A `@key` on fields that are nullable, argument-taking, or not stable identity.
- `__resolveReference` reading fields other than the key.
- `__resolveReference` not batched.
- `@shareable` added to resolve a composition error rather than because both subgraphs compute
  the same value.
- `@requires` pulling a large selection — the field is probably on the wrong subgraph.
- A `@link` version copied from an example rather than taken from the graph.
- A change checked only with local composition, not against the current registry: composition
  succeeding with your two subgraphs says nothing about the other eleven.

<!-- sources: apollo-skills-graphql, graphql-org-learn, apollo-server-defaults, skillmedev-graphql-schema -->
