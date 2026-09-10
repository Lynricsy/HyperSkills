# Error modelling

Verified against: GraphQL specification (October 2025 edition), GraphQL Yoga 5, Apollo Server 5.

## Contents

- [Two channels, two purposes](#two-channels-two-purposes)
- [The response shape](#the-response-shape)
- [Request errors versus execution errors](#request-errors-versus-execution-errors)
- [Errors-as-data: the payload pattern](#errors-as-data-the-payload-pattern)
- [When a result union is the better shape](#when-a-result-union-is-the-better-shape)
- [Error codes in `extensions`](#error-codes-in-extensions)
- [Interaction with non-null propagation](#interaction-with-non-null-propagation)
- [Masking: what each server does by default](#masking-what-each-server-does-by-default)
- [Partial success across a batch](#partial-success-across-a-batch)
- [Reviewing error handling](#reviewing-error-handling)

## Two channels, two purposes

| Failure | Channel | Example |
|---|---|---|
| Infrastructure fault | top-level `errors` | database timeout, downstream 503, unhandled exception |
| Invalid document | top-level `errors` (request error) | syntax error, unknown field, variable coercion failure |
| Authentication missing or invalid | top-level `errors` | no token, expired token |
| Business rule violation | errors-as-data | coupon expired, stock short, name already taken |
| Input validation | errors-as-data | password too short, invalid country for shipping |
| Domain constraint | errors-as-data | order already shipped, cannot cancel |

The dividing line is *expectedness*, not severity. If the product has a designed response to the
failure — a message next to a form field, a retry with a different coupon — it is a domain
outcome and belongs in the schema, where it is typed, introspectable and impossible for a client
to forget. If nobody designed a response because the failure means something is broken, it
belongs in `errors`. [official]

Authorisation sits on the line and the choice is a product decision. "You may not see this
field" is often best expressed as a null on a nullable field plus an entry in `errors`; "you may
not perform this action" is usually a typed error in the mutation's payload, because the UI has
something specific to say.

## The response shape

```json
{
  "data": { "placeOrder": { "order": null, "userErrors": [ … ] } },
  "errors": [
    {
      "message": "Ranking service unavailable",
      "path": ["viewer", "recommendations"],
      "locations": [{ "line": 4, "column": 5 }],
      "extensions": { "code": "DOWNSTREAM_UNAVAILABLE" }
    }
  ]
}
```

`data` and `errors` coexist: a response with both is the normal outcome of a partial failure,
not a contradiction. Clients that treat any non-empty `errors` as total failure throw away the
data they were given — a client-side bug that a well-designed schema makes visible.

`extensions` is the only place a server may add its own keys to an error. Do not invent
top-level keys next to `message`/`path`/`locations`.

## Request errors versus execution errors

- A **request error** happens before execution: parse failure, validation failure, variable
  coercion failure. The response has `errors` and **no `data` key at all** (not `data: null`).
  Nothing was executed, so nothing is partially correct.
- An **execution error** happens while resolving a field. The response has `data` (possibly with
  nulls) and `errors`, and each affected position contributes at most one error.

The distinction shows up in client code: a request error means the document or variables are
wrong and retrying is pointless; an execution error may be transient.

## Errors-as-data: the payload pattern

The default shape for a mutation. One argument, one payload, a nullable entity and a non-null
list of typed errors:

```graphql
type Mutation {
  placeOrder(input: PlaceOrderInput!): PlaceOrderPayload!
}

type PlaceOrderPayload {
  """Null when userErrors is non-empty."""
  order: Order
  userErrors: [PlaceOrderError!]!
}

interface PlaceOrderError {
  message: String!
  """Path into the input that caused this, e.g. ["lineItems", "0", "sku"]."""
  path: [String!]
}

type CouponRejected implements PlaceOrderError {
  message: String!
  path: [String!]
  code: CouponRejectionCode!
}

type InsufficientStock implements PlaceOrderError {
  message: String!
  path: [String!]
  sku: String!
  requested: Int!
  available: Int!
}
```

Why this and not thrown errors:

- The client can render `InsufficientStock.available` — a top-level error string cannot carry it
  without clients parsing prose.
- The failure modes are visible in introspection, so a client author discovers them without
  reading server code.
- `userErrors` is non-null and can be empty, so success and failure have one shape and the
  client has one code path.
- The payload can gain fields later without breaking anyone.

The `message` field is for humans, so localise it or keep it in English and let the client
localise from `code`. Never make the client match on `message` text.

## When a result union is the better shape

Use a union when the outcomes return structurally different data, not merely different error
detail:

```graphql
union CheckoutResult = CheckoutCompleted | PaymentRedirectRequired | CheckoutRejected
```

`PaymentRedirectRequired` carries a URL and no order; `CheckoutCompleted` carries an order. A
payload with three mostly-null fields would be worse.

The trade-off is evolution: adding a member to a union is a breaking change for clients that do
not have an unrecognised-`__typename` branch, whereas adding a field to a payload is always safe.
So default to the payload and reach for the union when the shapes genuinely differ
(`references/evolution.md`).

Queries can use the same technique — `union OrderResult = Order | NotFound | Forbidden` — but the
cost is that *every* client selection on that field needs inline fragments. Reserve it for fields
where "not found" is a first-class, actionable outcome rather than reaching for it everywhere.

## Error codes in `extensions`

For top-level errors, put a machine-readable code in `extensions.code` and keep the set small
and stable, because clients will branch on it:

```
UNAUTHENTICATED  FORBIDDEN  BAD_USER_INPUT  NOT_FOUND
RATE_LIMITED  DOWNSTREAM_UNAVAILABLE  INTERNAL_SERVER_ERROR
```

For errors-as-data, the code is a schema enum on the error type, which is strictly better: it is
introspectable, and removing a value is a detectable breaking change.

## Interaction with non-null propagation

Error modelling and nullability are the same decision viewed twice. An error raised at a
non-null position does not stay where it happened: it propagates upward until it reaches a
nullable position, potentially nulling `data` entirely
(`references/schema-design.md`).

Consequences to check when reviewing:

- A mutation returning PlaceOrderPayload! from a resolver that *throws* on a rejected coupon
  produces `data: null` and loses any other field in the same request. The payload only helps if
  the resolver returns it.
- Putting `userErrors` in the payload but leaving the entity non-null (order: Order!) recreates
  the problem: on failure you have nothing to put there, so you throw, so `data` is null.
- Two failing fields in one selection set produce two entries in `errors`, each with its own
  `path`. Clients should key error display off `path`, not off array position.

## Masking: what each server does by default

Never let an unknown error reach a client verbatim: messages carry connection strings, table
names and internal hostnames. How much work that is depends entirely on the server. [verified]

| | GraphQL Yoga 5 | Apollo Server 5 | graphql-js 17 |
|---|---|---|---|
| Plain `Error` thrown in a resolver | masked to `Unexpected error.` | message passed through, `extensions.code: INTERNAL_SERVER_ERROR` | passed through; the library does not mask |
| Stack trace in the response | only when `NODE_ENV=development`, under `extensions.originalError` | `includeStacktraceInErrorResponses` defaults to **true** unless `NODE_ENV` is `production` or `test` | not added |
| How to expose an intended message | throw `GraphQLError` — its message is not masked | any error; use `formatError` to normalise | throw `GraphQLError` |
| "Did you mean …" suggestions on validation errors | passed through | `hideSchemaDetailsFromClientErrors` defaults to **false**; Apollo's own docs recommend enabling it in production | `hideSuggestions` execution option |

Two consequences:

- On Apollo Server, masking is something you must implement (`formatError` plus a check that
  `NODE_ENV` is set correctly in the deployed environment). On Yoga it is the default and the
  thing you must do deliberately is *unmask* the errors you meant to show, by throwing
  `GraphQLError`.
- Leaving suggestion hints on defeats the point of disabling introspection: an attacker
  recovers field names by sending wrong ones (`references/performance.md`).

Whatever the server, log the original error with the operation name, the field `path` and a
correlation id, and return that id to the client. A masked error the client can quote is
supportable; an anonymous "Unexpected error." is not.

## Partial success across a batch

For an operation that acts on many items, model per-item outcomes instead of failing the whole
call:

```graphql
type BulkCancelPayload {
  results: [BulkCancelResult!]!
}

type BulkCancelResult {
  """Echoes the input id so the client can correlate regardless of ordering."""
  orderId: ID!
  cancelled: Boolean!
  error: CancelError
}
```

Echo the input identifier rather than relying on index correlation — a server is free to reorder,
and index-based correlation breaks silently when it does.

## Reviewing error handling

- Business failures thrown as top-level errors — the client cannot branch on them safely.
- A payload with a non-null entity, which forces a throw on failure.
- `userErrors` declared nullable, so clients need a null check that never triggers until it does.
- `message` used as the branching key on the client.
- Unmasked errors on Apollo Server, or `NODE_ENV` unset in production.
- Clients treating any `errors` entry as total failure and discarding valid `data`.
- Error codes as free strings on both sides instead of a schema enum where the schema can hold
  them.

<!-- sources: graphql-org-learn, graphql-spec, graphql-yoga, apollo-server-defaults, apollo-skills-graphql, skillmedev-graphql-schema -->
