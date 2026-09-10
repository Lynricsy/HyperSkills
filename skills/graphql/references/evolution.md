# Schema evolution

Verified against: GraphQL specification (October 2025 edition), `@graphql-inspector/cli` 7,
graphql.org/learn/robust-applications.

## Contents

- [Why there is no version number](#why-there-is-no-version-number)
- [Change classification](#change-classification)
- [Nullability changes](#nullability-changes)
- [Enum evolution](#enum-evolution)
- [Abstract type evolution](#abstract-type-evolution)
- [Input evolution](#input-evolution)
- [Replacing a field: the additive procedure](#replacing-a-field-the-additive-procedure)
- [`@deprecated`](#deprecated)
- [Retiring a field on measured usage](#retiring-a-field-on-measured-usage)
- [Replacing a mutation](#replacing-a-mutation)
- [What clients must do to make this work](#what-clients-must-do-to-make-this-work)
- [The gate](#the-gate)

## Why there is no version number

Most APIs version because the server decides what comes back, so any change to the payload can
break somebody. GraphQL inverts that: a client receives exactly the fields it asked for, so
adding types and fields cannot affect a client that did not ask for them. That is the whole
argument for a versionless, continuously evolving schema, and it is the official position. [official]

The corollary is the discipline: since there is no version to break compatibly in, you may not
retype, rename or remove in place. Every change is either additive or a migration you run with
both shapes served at once.

`/graphql/v2` is not the escape hatch it looks like. It doubles the schema you operate, the
resolvers you maintain and the registry entries you check, and it throws away the property that
made additive evolution work. Reach for it only when the domain model itself changed beyond
recognition, and then treat it as a new API with its own deprecation of the old one.

## Change classification

Do this classification before designing anything, because it decides the shape of the work.

**Safe (additive):**

| Change | Note |
|---|---|
| New type | Unreferenced types are invisible to clients. |
| New field on an existing type | The core additive move. |
| New optional argument on an existing field | Must have a default or be nullable. |
| New optional (nullable) field on an input object | Existing documents stay valid. |
| New enum value | Safe **only** in output positions — see below. |
| New interface implementation by a new type | Existing selections still validate. |
| Making a nullable output field non-null | Safe for clients; a new promise for the server. |
| Making a non-null argument or input field nullable | Loosens a requirement. |
| Adding `@deprecated` | Metadata only. |

**Breaking:**

| Change | Why |
|---|---|
| Remove or rename a type, field, argument, enum value | Existing documents stop validating. |
| Change a field's type | Even `Int` → `Float`; generated client types and parsers differ. |
| Make an output field nullable | Clients built against ` ! ` do not handle null. |
| Add a required argument or a non-null input field | Existing documents become invalid. |
| Remove an enum value, or add one in an input position | See below. |
| Add a member to a union, or a new implementation clients must handle | Only breaking for clients without a fallback branch — which is most of them. |
| Remove an interface from a type | Selections through the interface stop resolving to it. |
| Change a default value | Changes behaviour for every client relying on the old one. |
| Change what a field means without changing its type | Undetectable by any tool; the worst kind. |

Renaming is the trap worth stating explicitly: a rename is a removal plus an addition, and it
costs the same as any removal. If the only motivation is a better name, deprecate and wait.

## Nullability changes

Nullability moves in exactly one safe direction per side, and they are opposites:

- **Output positions:** nullable → non-null is safe (the client already handles null and now
  never sees it). Non-null → nullable is breaking, because clients written against ` ! ` — and
  their generated types — do not have a null branch.
- **Input positions:** non-null → nullable is safe (fewer requirements). Nullable → non-null is
  breaking, because documents that omit the value stop validating.

Tightening an output field to ` ! ` is safe for clients but is a promise the server now has to
keep, with the propagation consequences in `references/schema-design.md`. Do not tighten a field
that crosses a service boundary just because a tool says it is a safe change.

## Enum evolution

Adding a value is the change teams get wrong most often, because it is only half safe:

- **Output position:** safe on the wire. But a client that switches exhaustively with no default
  branch will crash or silently drop the case, and long-lived native apps keep old versions
  running for months. graphql.org treats this as an application-robustness requirement:
  always have a default branch. [official]
- **Input position:** breaking. An older client's generated types and validation do not include
  the value, and any peer that receives it may not handle it.

So: an enum used only in output positions can grow with a client-side announcement; an enum used
in an input position needs a new input enum, or the value gated behind a new argument.

Removing or renaming a value is breaking either way. To rename `PENDING` to `AWAITING_PAYMENT`:

1. Add `AWAITING_PAYMENT` to the enum.
2. Have the server return the new value **only** once clients handle it; until then keep
   returning `PENDING`. There is no way to return both.
3. Deprecate `PENDING` (`@deprecated` works on enum values).
4. Switch the server to emit the new value; watch for client errors.
5. Remove `PENDING` when no client sends it as input and every client tolerates unknown values.

Steps 2 and 4 are the real cost, and they are why "just rename it" is never just a rename.

## Abstract type evolution

Adding a member to a union, or a new type implementing an interface, is safe on the wire and
breaking in practice, because a client that does not recognise the `__typename` has nothing to
render — or throws. The mitigation lives on the client, so it has to be established *before* you
need it: every selection on an abstract type selects `__typename` and has an unrecognised-type
branch (`references/operations.md`).

Removing a member is unambiguously breaking.

## Input evolution

Input objects evolve under the same rules as arguments:

- Adding a nullable field is safe; adding a non-null field (with or without a default) is
  breaking for documents already sending that input, because the input's shape is validated.
- Removing a field is breaking.
- `@oneOf` cannot be added to an existing input object: it changes what a valid input is.

When an input genuinely needs a required new field, add a new input type and a new field or
mutation that takes it, and deprecate the old one.

## Replacing a field: the additive procedure

The general recipe, using "shippingCountry: String! should become an ISO code enum":

1. **Add** the new field beside the old one, with the new type and a name that does not collide:
   `shippingCountryCode: CountryCode`. Nullable, because it may be underivable for historical
   rows.
2. **Backfill** so the new field answers for existing data, or document exactly when it is null.
3. **Deprecate** the old field with a reason naming the replacement.
4. **Serve both** for as long as the deprecation window requires. Resolvers derive one from the
   other so they cannot diverge.
5. **Measure** who still selects the old field.
6. **Remove** when that number is zero.

Do not skip step 1 by changing the type in place, even when "only our own apps use it" — mobile
clients you shipped are still out there.

## `@deprecated`

```graphql
type Order {
  shippingCountry: String!
    @deprecated(reason: "Use shippingCountryCode. Removal once usage reaches zero.")
  shippingCountryCode: CountryCode
  status: OrderStatus!
}

enum OrderStatus {
  AWAITING_PAYMENT
  PENDING @deprecated(reason: "Renamed to AWAITING_PAYMENT.")
  PAID
}
```

- Applies to fields, arguments, input fields and enum values.
- The `reason` is read by humans deciding what to migrate to, and by lint rules that flag
  deprecated usage in client documents. "Deprecated" as a reason is useless; name the
  replacement.
- A deprecated field is still fully functional and still served. Deprecation is a signal, not a
  behaviour change, and a field that starts returning null when deprecated is a breaking change
  wearing a label.
- Deprecated fields are hidden from most introspection tooling by default, so a new client will
  not discover them — which is the mechanism that makes usage decay.

## Retiring a field on measured usage

Deprecation without measurement never ends: the field is still there three years later because
nobody could prove it was safe to remove.

- Instrument per-field usage. Servers and registries can report which operations and which
  clients selected each field.
- Set the removal condition on the data — zero selections over a window longer than your slowest
  client's release cycle — not on a number of releases.
- Identify the remaining callers by client and contact them; "someone is still using it" is not
  actionable, "the Android app at version 4.2" is.
- Only for a field with no instrumentation available, fall back to a stated window in the
  deprecation reason, and announce the date.
- Removal itself is a schema change like any other: it goes through the same diff gate, which
  will correctly report it as breaking. That report is the record that it was intended.

## Replacing a mutation

Mutations replace as a unit rather than field by field, because their input and their result
change together. To move `placeOrder` from throwing on business failures to errors-as-data:

1. Add placeOrderV2(input: PlaceOrderInput!): PlaceOrderPayload! returning the payload with
   `userErrors` (`references/errors.md`). Reuse the input type if it is unchanged.
2. Implement the old mutation in terms of the new one — call the new path, throw where the old
   contract threw — so behaviour cannot drift while both exist.
3. Deprecate the old mutation naming the new one.
4. Migrate clients, measure, remove.

Version suffixes on field names are ugly and they are still the least-bad option; the
alternative is a name that describes the mechanism (`placeOrderWithResult`) which ages worse.

## What clients must do to make this work

Additive evolution only works if clients are written to survive it. State these when you publish
a deprecation, because they are the client's half of the contract: [official]

- Default branch on every enum switch; do not treat the value set as closed.
- `__typename` selected on every union and interface field, with a branch for the unrecognised
  case.
- No force-unwrapping of nullable fields (` ! ` in Swift, ` !! ` in Kotlin, non-null assertions in
  TypeScript). A nullable field is the schema saying "this may be absent", and the field may
  become absent the day a downstream service degrades.
- Regenerate types against the current schema in CI, so a deprecation or a new value shows up as
  a lint warning rather than a production surprise.

## The gate

Every schema change runs through a mechanical diff before it merges:

```bash
npx @graphql-inspector/cli diff <old-schema> <new-schema>
```

Both arguments take a file, a URL or a `git:` reference, so the deployed schema can be the
baseline directly. The command exits non-zero on breaking changes, which is what makes it a CI
gate rather than a report.

- Intended breaking changes are approved explicitly (an allow-list entry, a label on the pull
  request) so the record says a human decided.
- On a federated graph, the plain diff is not enough: run the registry's subgraph check, which
  composes against the other subgraphs and evaluates usage across the whole graph
  (`references/federation.md`).
- `@graphql-eslint/eslint-plugin` complements the diff on the client side, flagging documents
  that still select deprecated fields — which is how you find the callers to migrate.

<!-- sources: graphql-org-learn, graphql-spec, apollo-skills-graphql, graphql-hive-tooling, skillmedev-graphql-schema -->
