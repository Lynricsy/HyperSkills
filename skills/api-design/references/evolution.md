# Versioning, compatibility and deprecation

## Contents

- [Three kinds of compatibility](#three-kinds-of-compatibility)
- [The compatibility matrix](#the-compatibility-matrix)
- [The changes tools cannot catch](#the-changes-tools-cannot-catch)
- [Versioning schemes](#versioning-schemes)
- [Deprecation and sunset](#deprecation-and-sunset)
- [Rolling out a breaking change](#rolling-out-a-breaking-change)

## Three kinds of compatibility

A change can be compatible on the wire and still break clients. Check all three axes before
calling a change safe: `[official]`

- **Wire** — old requests still parse and old responses still deserialise.
- **Source** — generated clients still compile. This is why renaming, retyping or moving a
  field breaks even when the JSON would still round-trip, and why adding pagination breaks
  generated clients whose paginated and unpaginated call shapes differ.
- **Semantic** — old code still gets what a reasonable developer would expect. This is the
  axis that catches unit changes, default changes and sort-order changes, and it is the one
  no tool checks.

## The compatibility matrix

| Change | Breaking? | Why |
|---|---|---|
| Add an optional request field | No | Old clients omit it; the default must reproduce the previous behaviour exactly |
| Add a **required** request field | **Yes** | Every existing request becomes invalid. Required fields can only be introduced in an API's first version |
| Make an optional field required, or a required one optional | **Yes** | Both directions change what a valid request is |
| Add a response field | No | Provided clients tolerate unknown fields — state that expectation in the contract |
| Remove or rename a response field | **Yes** | A rename is remove-plus-add; there is no such thing as an in-place rename |
| Remove or rename an endpoint, parameter or enum value | **Yes** | Same reasoning |
| Change a field's type (`integer` → `string`) | **Yes** | Breaks deserialisation and generated code even when values would round-trip; an alias period does not make it compatible |
| Change a field's value format or construction (numeric id → ULID, IPv4 → IPv6) | **Yes** | Clients parse, hash and store these values |
| Change a field's **unit or meaning** with the same type | **Yes**, and the worst kind | No schema check fires, no client fails loudly; all downstream arithmetic silently becomes wrong. Ship a new field name instead |
| Change a static default value | **Yes** | The default is the behaviour old clients rely on |
| Change whether a default-valued field is serialised at all | **Yes** | Clients treat presence and absence as meaningful |
| Add an accepted value to a **request** enum (a new filter value) | No | Old clients simply never send it |
| Add a value to a **response** enum | **Risky** | Clients that switch exhaustively fail on it. Only safe if the enum was documented as open from the start |
| Add pagination to a collection that had none | **Yes** | Behaviourally: a client that received everything now receives one page and does not know to continue. Raising the default limit does not fix it |
| Change a collection response from a bare array to an object | **Yes** | The top-level JSON type changes |
| Change the default sort order or the default page size | **Yes** | Page 1 now contains different items for every existing client |
| Tighten validation (narrower `maxLength`, stricter pattern, lower `maximum`) | **Yes** | Requests that used to succeed now fail |
| Relax validation (`maxLength` 20 → 64) | **Risky** | Servers accept more, but clients sized storage, columns and UI fields on the documented bound. Treat a documented bound as contract |
| Change a success status code (200 → 201) | **Yes** | Clients and gateways match on exact codes |
| Add a new error status or problem type | No | Provided clients were told to treat unknown 4xx/5xx by class |
| Change which status an existing condition returns | **Yes** | Retry logic is written against it |
| Add a new endpoint, a new optional query parameter, a new problem type | No | Nothing existing changes |
| Make a required field's server-side validation stricter without changing the schema | **Yes** | Semantic axis: the documented contract still says it is accepted |

`[official]`

## The changes tools cannot catch

A schema differ sees types and names. It does not see:

- a unit or currency reinterpretation (`weight_kg` now holds grams);
- a default value or default sort change;
- a field that was always populated becoming conditionally absent;
- an id format change behind an unchanged `type: string`;
- an operation that becomes slower than the client's timeout;
- a filter that starts matching a different set of rows.

These are exactly the changes that produce a silent data corruption rather than a loud
failure, so they need a human pass over the diff. Any field previously populated by the
server must keep being populated, even when it has become redundant. `[official]`

## Versioning schemes

**Default: one major version segment in the path**, `/v1/...`, incremented only for breaking
changes. Every resource lives under it, the version is visible in every log and curl command,
and routing two versions side by side is trivial.

- Version the whole API, not the resource. Per-resource versions multiply into a matrix
  nobody can document.
- Only major versions appear in the URI. Compatible additions do not bump anything; if you
  also publish a document version, that is a document version, not an API version.
- Support the current version plus one previous, and keep at most two or three alive. Each
  live version is a full test surface. `[community]`

**Escape hatch: a date-based version parameter.** A required `?api-version=YYYY-MM-DD` on
every operation (with a `-preview` suffix for previews) lets a single-vendor ecosystem ship
fine-grained versions without duplicating routes. It costs more: every client must send it on
every request, including on URIs the server handed back (next-page links, operation
locations, which therefore have to carry it), and the contract must fix the answers for a
missing value and an unknown value — a 400 with a distinguishable problem type for each.
Choose it when you can require all clients to comply, not for a public API. `[official]`

Whatever the scheme, one thing is not negotiable: an unversioned surface plus a versioned one
(some routes bare, some under `/api/v2`) is two APIs, not one API with two versions. Pick the
scheme, route the legacy paths into it, and give the old paths a deprecation date.

## Deprecation and sunset

Deprecation has three layers, and all three are needed:

**1. In the document.** Mark the operation, parameter, schema or property `deprecated: true`
and say in its `description` what replaces it and by when. This is what shows up in generated
documentation and SDKs.

**2. At runtime, on every affected response:** `[official]`

```http
Deprecation: @1758095283
Sunset: Wed, 31 Dec 2026 23:59:59 GMT
Link: <https://developer.example.com/deprecations/shipments-v1>; rel="deprecation"
```

- `Deprecation` (RFC 9745) is a Structured Field **Date** — `@` followed by a Unix
  timestamp. It is the moment the resource is or will be deprecated; a future value means
  "do not onboard anything new".
- `Sunset` (RFC 8594) is an **HTTP-date**, the moment the resource stops answering. The two
  headers use different date formats for historical reasons — this is the detail most
  implementations get wrong.
- `Sunset` must not be earlier than `Deprecation`.
- When several elements of one response are deprecated, use the earliest timestamps, so the
  client sees the shortest window it has to act in.
- Announcing deprecation changes no behaviour. The resource keeps working exactly as before
  until sunset.

**3. Out of band.** A changelog entry and a migration guide, plus direct contact with the
clients you can identify. Announcing a removal only in a changelog is not a deprecation
policy — nobody reads a changelog for an API they already integrated.

Timing that holds up: announce at least a quarter before the sunset date, keep a sunset
roughly two quarters after the announcement, and lengthen both when a client cannot ship on
your schedule (firmware, an app store review cycle, a partner's own release train).
`[community]`

Before the sunset date, monitor usage of the deprecated element. Removing something that
still has traffic is a decision, not an accident, and you can only make it if you measured.
`[official]`

## Rolling out a breaking change

For a change that is unavoidably breaking, in order:

1. **Try to make it compatible first.** Most breaking changes have a compatible sibling: add
   a new field instead of renaming, add a new optional parameter instead of changing a
   default, add a new endpoint instead of changing an existing one's shape.
2. **Additive phase.** Ship the new field, parameter, endpoint or status alongside the old.
   Both work; the document describes both; the old one is marked deprecated.
3. **Announce.** Deprecation and sunset dates in the document, the headers on every affected
   response, the migration guide published, the identified clients contacted.
4. **Measure.** Watch traffic on the deprecated element per client.
5. **Remove at sunset**, or bump the major version if there are too many removals to do
   piecemeal.

For a batch of breaking changes it is usually cheaper to cut `/v2` than to run a dozen
deprecation windows in parallel. The test is whether clients can migrate change by change; if
they cannot, they need one migration, which is a new version.

<!-- sources: google-aip, microsoft-azure-guidelines, zalando-guidelines, rfc9745-deprecation, rfc8594-sunset, orchestkit-api-design, openapi-spec -->
