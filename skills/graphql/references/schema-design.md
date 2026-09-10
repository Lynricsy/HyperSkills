# Schema design

Verified against: GraphQL specification (October 2025 edition), graphql-js 17.

## Contents

- [Nullability: the mechanism, then the rule](#nullability-the-mechanism-then-the-rule)
- [Naming](#naming)
- [Objects, not scalar foreign keys](#objects-not-scalar-foreign-keys)
- [Interfaces versus unions](#interfaces-versus-unions)
- [Input objects, arguments and `@oneOf`](#input-objects-arguments-and-oneof)
- [Enums](#enums)
- [Custom scalars](#custom-scalars)
- [Global object identification](#global-object-identification)
- [Descriptions](#descriptions)
- [Organising the SDL](#organising-the-sdl)

## Nullability: the mechanism, then the rule

Every output position in GraphQL is nullable unless you write ` ! `. That default is deliberate:
a field can fail on its own — a downstream service is unreachable, an async job errored, this
role may not read this field — and a nullable position lets the failure stay local instead of
failing the whole request. [official]

The specification's execution rules are what make that true, and what make ` ! ` expensive:

- An execution error at a response position is handled as if that position resolved to `null`,
  and the error is added to the response's `errors` list. At most one error is recorded per
  position.
- If a position with a `Non-Null` type resolves to `null` — because the resolver returned null
  or because an error was raised — the error propagates to the parent response position. A
  nullable parent becomes `null`; a non-null parent propagates further up.
- If a `List` type wraps a `Non-Null` type and one element resolves to `null`, **the entire
  list position becomes `null`**. A non-null list then propagates that to its own parent.
- If every position from the root of the request down to the failure is non-null, `data`
  itself is `null`.
- Sibling positions that have not executed yet may be cancelled once propagation starts, so a
  single failure can also discard work that would have succeeded.

That is the whole story behind the most common production symptom: a schema where a team added
` ! ` to every field "so the generated TypeScript has no optionals" answers a partial outage with
`{"data": null}` and a blank screen.

**The rule.** Add ` ! ` to an output position only when it cannot fail independently of its
parent. Ask: if the value for this position were unavailable at request time, would returning
the parent object without it still be useful?

| Position | Non-null? | Why |
|---|---|---|
| `id`, and columns that arrived with the same row | yes | The parent could not have been constructed without them. |
| A value computed by another service (score, recommendation, price quote) | no | It fails on its own schedule. |
| A value fetched from a third-party API (image metadata, geocoding) | no | Same. |
| A field only some roles may read | no | Authorisation is a per-field outcome; null is the answer for the others. |
| A list you always return, even when empty | the list may be ` ! ` | Empty list is a value; a non-null list says "I will always give you an array". |
| Elements of a list whose items can fail individually | no | `[T!]` makes one bad element destroy the page. |
| Root fields (`Query.order`, `Query.viewer`) | almost never | A non-null root field puts `data: null` one error away. |
| Arguments and input fields that are genuinely required | yes | See below — the input side is the opposite trade. |

Inputs invert the trade-off. A non-null argument or input field costs nothing at execution time
and eliminates a validation branch, so mark genuinely required inputs ` ! `. The cost arrives
later: adding a required argument, or adding a non-null field to an existing input object, is a
breaking change for every client already sending that input.

graphql-js 17 exposes an operation-level `@experimental_disableErrorPropagation` directive that
turns null-bubbling off for one operation, and the executor reads it into an `errorPropagation`
flag. It is experimental and non-standard: know it exists so you recognise it in a codebase, but
do not reach for it instead of making a fallible field nullable. [verified]

## Naming

- Types, interfaces, unions, enums and scalars in `PascalCase`; fields, arguments and input
  fields in `camelCase`; enum values in `SCREAMING_SNAKE_CASE`.
- Name from the client's vocabulary, not the storage layer's. `OrderRow`, `orders_tbl`,
  `status_code` and `customer_id: Int` all leak the database into a contract you cannot version
  out of.
- Field names carry no type prefix or suffix: `title`, not `titleString`. The type is already
  in the schema.
- Mutations are named after the business operation — `placeOrder`, `cancelSubscription`,
  `publishPost` — not after the CRUD shape (`updateOrder(status:)`). Two different business
  events that both write the same column deserve two mutations, because their authorisation and
  their errors differ.
- Input object per mutation, named `<Mutation>Input`; payload per mutation, named
  `<Mutation>Payload`. One argument called `input` keeps the mutation extensible without
  renaming anything.
- Booleans read as assertions: `isPublished`, `hasUnreadMessages`, `canEdit`.
- Avoid `get`/`fetch` prefixes on query fields. `order(id:)`, not `getOrder(id:)`.

## Objects, not scalar foreign keys

Return the related type, not its id:

```graphql
type Order {
  id: ID!
  customer: Customer      # nullable: separate lookup, separate failure
  lineItems: [LineItem!]!
}
```

customerId: ID! forces every client into a second request and gives you nowhere to add
`customer.displayName` later. The relationship field is also the place a DataLoader attaches
(`references/performance.md`).

## Interfaces versus unions

- **Interface** when the members share fields and clients want to select those fields without
  knowing the concrete type: `Node { id: ID! }`, `Timestamped { createdAt: DateTime! }`,
  `Error { message: String! }`.
- **Union** when the members share nothing structurally and the client's job is to branch:
  `union SearchHit = Post | Author | Collection`.

Both are open sets in practice — you will add members. Every client selection on an abstract
type therefore needs `__typename` and a branch for the unrecognised case, which is a rule you
have to state in the schema's documentation because the schema cannot enforce it
(`references/evolution.md`).

An interface can also be the shared shape of your error types, which makes a "give me the
message whatever went wrong" selection possible alongside the specific branches:

```graphql
interface UserError {
  message: String!
  path: [String!]
}

type CouponRejected implements UserError {
  message: String!
  path: [String!]
  code: CouponRejectionCode!
}
```

## Input objects, arguments and `@oneOf`

- Use a dedicated input type rather than a long argument list; arguments cannot be reused across
  fields and cannot be nested.
- Never reuse an output type as an input. They diverge immediately — the output has server-set
  fields (`id`, `createdAt`), the input has write-only ones — and object types are not valid
  input types anyway.
- Distinguish "absent" from "explicit null" when it matters. A `PATCH`-style update where
  `nickname: null` means *clear it* and an omitted `nickname` means *leave it* needs the server
  to inspect whether the field was provided; several servers make that hard, so the safer design
  is an explicit sentinel or a separate `clearNickname: Boolean` field.
- `@oneOf` on an input object means exactly one of its fields must be supplied and must not be
  null. It is a specified directive in graphql-js 17, so a modern server can enforce
  "identify the record by exactly one of these" without a runtime check: [verified]

```graphql
input ProductLookup @oneOf {
  id: ID
  sku: String
  slug: String
}
```

  Older servers will not know the directive. Check that yours enforces it before relying on it;
  if it does not, keep the fields nullable and validate in the resolver.

- Default values belong on the schema, not in the resolver, so they appear in introspection:
  `products(first: Int = 20, after: String)`.

## Enums

Use an enum for a closed set of values the API controls — order status, sort direction, a
rejection code. Not for anything the data owner can extend at runtime (tags, categories from a
CMS): a value the server returns that is not in the schema is an execution error.

Treat the value set as append-only, and note that "safe to add" depends on where the enum is
used:

| Change | Output positions | Input positions |
|---|---|---|
| Add a value | safe on the wire; breaks clients that switch exhaustively without a default | **breaking**: an old client's validation and generated types do not include it, and a server that starts *accepting* it changes the contract for peers |
| Remove or rename a value | breaking | breaking |
| Reorder values | safe | safe |

## Custom scalars

Define a scalar when the serialised form has a domain meaning the built-ins lose: `DateTime`
(RFC 3339 string), `URL`, `EmailAddress`, `CountryCode`, `Money` as minor units. The payoff is
that validation and coercion happen once, in the scalar, instead of in every resolver.

Two traps:

- A custom scalar is opaque to schema-aware tooling: codegen maps it to `any`/`String` unless
  configured, and no client can validate it. Document the exact serialisation in the scalar's
  description.
- `JSON`-shaped scalars discard the type system for everything inside them. Use one only for
  genuinely open payloads (a webhook body you pass through), never as a shortcut around
  modelling a known object.

## Global object identification

If clients need to refetch a single object by id, or use a normalising cache, implement the
`Node` interface and make the `id` globally unique across types:

```graphql
interface Node {
  id: ID!
}

type Query {
  node(id: ID!): Node
}
```

The id is opaque — typically the type name and the local key, encoded — so `Post:1` and
`Comment:1` cannot collide. Do not implement this speculatively: it constrains every id in the
schema, and an API whose clients always navigate from a root field gains nothing from it.

## Descriptions

Every type, field, argument and enum value gets a description, in triple-quoted SDL blocks.
For nullable fields, say what a null means — "null until the carrier accepts the parcel" is the
difference between a client that renders a placeholder and one that crashes. For arguments, say
the units, the bounds and the default. For deprecated elements, the `reason` names the
replacement.

## Organising the SDL

Split the SDL by domain, one file per aggregate, and let each file extend the root types rather
than concentrating every field in one `type Query`:

```graphql
# order.graphql
extend type Query {
  order(id: ID!): Order
}

extend type Mutation {
  placeOrder(input: PlaceOrderInput!): PlaceOrderPayload!
}
```

Keep resolvers next to the SDL they implement. In a code-first server (Pothos) the same split is
one builder module per domain — the organising principle is identical, only the syntax differs
(`references/servers.md`).

<!-- sources: graphql-org-learn, graphql-spec, graphql-js, apollo-skills-graphql, skillmedev-graphql-schema, wshobson-graphql -->
