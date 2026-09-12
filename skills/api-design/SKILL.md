---
name: api-design
description: "Designs REST API contracts, resource models, pagination and OpenAPI specifications."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

# api-design

## Scope

The contract an HTTP API exposes, and nothing about how it is implemented. Resource
modelling, URIs, methods, status codes, representation shape, collections and their
pagination, the error contract, concurrency and caching headers, long-running operations,
versioning, compatibility judgement, deprecation, and the OpenAPI document that states all
of it.

Applies whether the contract is new, being redesigned, or being reviewed before a release.

Not covered:

- Implementing the contract — routers, handlers, validation wiring, serialisers, dependency
  injection, ORM access, tests of the implementation. Use the `fastapi`,
  `nodejs-backend`, `java-spring`, `csharp-dotnet` or `laravel` skill; this skill decides
  what the wire contract is, those decide how a stack produces it.
- GraphQL schema design, operations, and federation — use the `graphql` skill. The two do
  not overlap: HTTP contracts here, GraphQL there.
- Reviewing a diff or a pull request for general correctness — use the `code-review` skill,
  and come back here for the contract rules a reviewer applies to an API change.
- Authentication and authorisation mechanism design (OAuth flows, token issuance, session
  handling). This skill covers where credentials appear in the contract and which status
  code a failure gets, not how an identity system works.
- Transport and infrastructure — gateways, rate-limiter implementations, TLS, service mesh
  policy, gRPC and message-broker contracts. None of these has a skill in this library yet;
  say so rather than improvising one.

Paths below are relative to this skill's directory.

## Core rules

1. Model resources from the nouns clients need to address, not from the tables behind them.
   An API shaped like the schema freezes the schema: every later normalisation becomes a
   breaking change.
2. No verbs in paths. `POST /createWarehouse` restates the method, and as soon as a second
   verb appears the surface stops being addressable — nothing names the resource any more.
3. Choose the method from its semantics, not from habit: `PUT` replaces and is idempotent
   and may create, `PATCH` is partial and is not idempotent by default, `POST` is for
   everything else. A `POST /updateX` that silently creates is an upsert wearing the wrong
   method, so no client and no proxy can reason about retrying it.
4. A `PATCH` contract names its media type — `application/merge-patch+json` (sparse object,
   `null` deletes, cannot address an array element) or `application/json-patch+json`
   (operation list, can). Declaring `application/json` says nothing and every client guesses.
5. Failure never ships under a 2xx. `200` with `{"ok": false}` defeats every retry policy,
   gateway rule and error-rate dashboard, and forces clients to parse before they know
   whether they succeeded.
6. Distinguish 400 (could not parse) from 422 (parsed, values unacceptable), 401 (no valid
   credentials) from 403 (authenticated, not allowed), and 409 (conflicts with current
   state) from both. That is what tells a client whether to retry, re-auth or fix its input.
7. `201` always carries a `Location` header naming what was created. Without it the client
   has to guess the URI of the thing it just made.
8. Model an operation that does not fit CRUD as a state sub-resource
   (`PUT /orders/{id}/cancellation`) when there is state worth addressing afterwards, and as
   an action endpoint (`POST /orders/{id}/cancel`) when there is not. The sub-resource is
   idempotent by construction; prefer it.
9. The top-level JSON value of a response is an object, never an array. An array has nowhere
   to add a pagination link, a warning or a total later, so returning one makes every future
   addition breaking.
10. Every collection is paginated from its first release, with a documented default and
    maximum page size, and requests above the maximum are coerced down rather than rejected.
    Adding pagination later is a breaking change even though it only adds fields.
11. Default to an opaque cursor over a keyset; keep offset only for a screen that genuinely
    needs numbered pages, and say in the contract that it can repeat or skip rows under
    concurrent writes. Offset names a position, and positions move when rows are inserted or
    deleted before the window.
12. A keyset needs a total order. `created_at` alone is not one if two rows can share a
    timestamp, so put a unique tiebreaker in both the sort and the cursor — otherwise the
    switch away from offset reintroduces the duplicates it was meant to fix.
13. Opaque means unparseable, not encoded. Base64 of the sort values is not obfuscation:
    clients will decode it, then construct their own, and your pagination internals become
    public contract. Sign it, encrypt it, or keep it server-side.
14. Do not return a total count by default. Counting the matches of a filtered query
    generally scans the whole index, so the count costs more than the page; make it opt-in
    and say whether it is exact or an estimate.
15. Errors use RFC 9457 problem details with `application/problem+json`, and the HTTP status
    agrees with the `status` member. RFC 9457 obsoletes RFC 7807 — material citing 7807
    predates the registry and the `about:blank` guidance.
16. The `type` URI is the problem's identifier and the only thing clients branch on.
    `title` and `detail` are human-readable prose that may be localised or reworded, so a
    client matching on the message breaks at the next copy edit. Adding a second
    machine-readable `code` alongside `type` is only worth it when it is finer-grained than
    the type; a `code` that duplicates `type` or the status number is noise.
17. No stack traces, driver messages, SQL, constraint names or internal hostnames in an
    error body. Log them against a correlation identifier that the response also carries,
    and return an opaque problem.
18. Make retryability machine-readable: `Retry-After` on 429 and 503, and documented
    behaviour for any condition that breaks the retryable-by-status default. A caller that
    has to parse prose to decide retries either hammers you or gives up on transient
    failures.
19. Mutable resources return an `ETag` and accept `If-Match` on writes, answering 412 on a
    mismatch. Without a precondition, concurrent writers silently overwrite each other and
    neither client learns anything. On a conditional read, a matching `If-None-Match` is
    304 — never 412.
20. A write a client will retry needs an idempotency mechanism: a conditional key
    (`If-Match`) for updates, a business secondary key for creates, or an `Idempotency-Key`
    header when the same *response* must be replayed. The retry after a timeout, where the
    client cannot know whether the first attempt landed, is the case that double-charges.
21. An operation that cannot finish inside a request answers 202 with an
    `Operation-Location` pointing at a status-monitor resource, plus `Retry-After`. Holding
    the connection open lets the load balancer choose your timeout, and the client cannot
    tell a timeout from a failure. Never model `PATCH` as a long-running operation.
22. Version the whole API with one major segment in the path (`/v1`), bumped only for
    breaking changes, and support the current version plus one. A surface where some routes
    are unversioned and others sit under `/api/v2` is two APIs, not one API with two
    versions.
23. Judge every proposed change on three axes — wire, source and semantic compatibility —
    before calling it safe. Renaming or retyping a field breaks generated clients even when
    the JSON would round-trip, and an unchanged schema whose field now means something else
    (kilograms becoming grams, a changed default, a changed default sort) breaks clients
    with no tool firing at all. That last kind needs a new field name, not a new description.
24. Deprecate in three places or not at all: `deprecated: true` in the document, the
    `Deprecation` and `Sunset` headers on every affected response, and a migration guide the
    affected clients are actually told about. A removal announced only in a changelog is not
    a deprecation policy. `Deprecation` is a Structured Field Date (`@1758095283`) and
    `Sunset` is an HTTP-date; the formats differ, and `Sunset` must not precede
    `Deprecation`.
25. A contract is not finished until a tool has read it: `redocly lint` must exit 0, and a
    `prism mock` must serve the paths that matter. A design nobody validated is a document,
    not a contract.

## Workflows

Each workflow ends with a named gate. Run the gate; do not assert it passed.

### design-contract

For a new API surface, or a redesign of an existing one.

- [ ] Write down the clients and their constraints first: who calls this, which of them can
      you force to upgrade, and on what cadence. That decides how much compatibility the
      design has to buy.
- [ ] Identify the resources — addressable domain nouns — and their ownership. Produce a
      table of resource, URI template, and which operations it supports, before any endpoint
      list. `references/resources-and-methods.md`.
- [ ] Fix identifier format and representation conventions once, globally: id type, casing,
      timestamps, money, units in field names, and the read-versus-write shape split.
- [ ] Assign methods and status codes per operation, including the failure statuses. Name
      the non-CRUD operations explicitly and decide sub-resource versus action for each.
- [ ] Design collections: pagination scheme per listing (justified by the write pattern),
      page-size default and maximum, filter and sort allow-lists, whether a total is
      offered. `references/collections.md`.
- [ ] Design the error contract: the problem-type registry, which status each type uses,
      the validation-failure shape, the correlation identifier, and retryability.
      `references/error-contract.md`.
- [ ] Decide concurrency and caching per resource — `ETag`/`If-Match`, `Cache-Control` and
      `Vary` — and the idempotency mechanism for every retryable write.
      `references/concurrency-and-async.md`.
- [ ] Model anything slower than about a second at p99 as a long-running operation with a
      status monitor, rather than as a request that blocks.
- [ ] Choose the versioning scheme and write the compatibility promise down: what clients
      may rely on, what may change without notice. `references/evolution.md`.
- [ ] Write the OpenAPI 3.1 document: `$ref`-shared problem responses and pagination
      parameters, read and write schemas, every response an operation can return, examples
      everywhere, `operationId` on every operation. `references/openapi.md`.
- [ ] **Gate — lint clean and mock exercised:** `npx @redocly/cli@latest lint <spec>` exits 0
      with no errors, then `npx @stoplight/prism-cli@latest mock <spec> --port 4010` serves
      the happy path, a paginated listing, one validation failure and one auth failure — with
      no response that prism had to synthesise itself.

### review-contract

For an existing surface, a proposed API, or an OpenAPI document under review.

- [ ] Read the document or the endpoint list end to end first and list the resources it
      implies. A surface whose resources cannot be named is the finding.
- [ ] Check each operation against the rules above and record findings as
      `<location> - <what is wrong> - <what it should be>`: verbs in paths, methods that
      contradict their semantics, 2xx failures, missing `Location`, undeclared error
      responses, missing preconditions on writes.
- [ ] Check every collection: is it paginated, is there a maximum, does the scheme match the
      write pattern, is the sort a total order, is a total count being paid for.
- [ ] Check the error contract for consistency across operations. Several shapes in one API
      is one finding, not one per shape.
- [ ] Check consistency across the surface — naming, casing, id format, timestamp format,
      pagination parameter names. Inconsistency is the most expensive category because every
      client pays for it forever.
- [ ] Separate contract findings from implementation findings and hand the latter to the
      relevant ecosystem skill. A review that mixes them gets neither fixed.
- [ ] **Gate — every finding is located and actionable:** each names the operation, schema
      or parameter, why it matters to a client, and the concrete replacement. If a document
      exists, `redocly lint` has been run and its errors are separated from your findings.

### evolve-contract

For a change to a published contract.

- [ ] Classify each change: compatible, breaking, or risky. Use the matrix in
      `references/evolution.md` and do it per change — a list judged as a whole hides the one
      breaking item.
- [ ] Look specifically for the changes no tool catches: unit or meaning reinterpretations,
      default value changes, default sort or page-size changes, id format changes behind an
      unchanged type, a previously always-present field becoming conditional.
- [ ] For each breaking change, look for the compatible sibling first — add a field instead
      of renaming, add a parameter instead of changing a default, add an endpoint instead of
      reshaping one. Most of the list usually converts.
- [ ] Sequence what remains: additive phase first, then announcement with dates, then
      measurement of the deprecated element's traffic, then removal at sunset. Batch the
      irreducible breaks into a major version instead of running many windows in parallel.
- [ ] Set the dates from the slowest client, not from your release calendar. Firmware and
      app-store cadence are hard constraints.
- [ ] Update the document: `deprecated: true` with a replacement named in the description,
      the new elements added, the compatibility promise re-checked.
- [ ] **Gate — the plan is verifiable:** every change carries its classification and its
      reasoning; deprecated elements carry `Deprecation` and `Sunset` values; the revised
      document passes `redocly lint`; and a `prism mock` of the revised document still serves
      an old client's request shape unchanged for everything classified as compatible.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Resource modelling, URI structure, method semantics and idempotency, non-CRUD operations, status-code selection, representation shape | Shaping or reviewing the surface itself | `references/resources-and-methods.md` |
| Pagination scheme choice, offset failure mechanism, keyset construction, opaque cursors, totals, filtering, sorting, sparse fieldsets | Any endpoint that returns a list | `references/collections.md` |
| RFC 9457 members, problem-type registry, validation failures, retryability, what never goes in an error body, migrating several error shapes | Designing or unifying error responses | `references/error-contract.md` |
| ETag and If-Match, 412 versus 304 versus 428, cache headers, the three idempotency patterns, long-running operations and status monitors | Concurrent writers, retryable writes, or an operation that cannot finish in a request | `references/concurrency-and-async.md` |
| Compatibility axes, the breaking-versus-compatible matrix, changes tools cannot catch, versioning schemes, Deprecation and Sunset, rollout sequencing | Changing a published contract, or choosing a versioning scheme | `references/evolution.md` |
| OpenAPI 3.1 versus 3.0 and 3.2, document skeleton, authoring discipline, the lint and mock gates, mistakes lint will not catch | Writing or validating the document | `references/openapi.md` |

## Output format

For a design, deliver the document plus a summary in this order. Skip empty sections.

```markdown
### Resources
| Resource | URI | Operations | Notes |

### Operations
`METHOD /path` — purpose; success status; failure statuses; preconditions; idempotency.

### Collections
Per listing: pagination scheme and why, page size default/max, sort and filter allow-lists,
whether a total is offered.

### Error contract
Problem types: `type` URI, status, title, extension members. Validation shape.
Correlation identifier. Retryable set.

### Evolution
Versioning scheme, compatibility promise, deprecation mechanism and windows.

### Verification
Commands run and their output: `redocly lint` result, the mock requests exercised and their
responses.
```

For a review or a compatibility judgement, lead with the verdict and keep the per-item
classification in a table:

```markdown
### Verdict
<Ship as is / Ship with the listed fixes / Needs a new major version> — one sentence of why.

| # | Change | Compatible? | Why | What to do instead |

### Findings
1. **<what is wrong>** — `<operation, schema or parameter>`
   - Impact on clients: <concrete consequence>
   - Fix: <the replacement>

### Verification
<commands run and output>
```

State plainly what you could not verify. A contract review that claims a document is valid
without having linted it is worth nothing.

## Environment

- `node` with `npx` for both gates. Neither tool needs installing:
  `npx @redocly/cli@latest lint <spec>` and
  `npx @stoplight/prism-cli@latest mock <spec> --port 4010`.
- `redocly lint` exits 0 when there are no errors; **warnings do not change the exit code**,
  so read them and either fix them or disable them explicitly in `redocly.yaml`.
- `curl` is enough to exercise a prism mock. Prism enforces the document's declared
  `security` and synthesises its own 401 when the document declares none — treat any
  synthesised response as a hole in the contract.
- Both gates verified against `@redocly/cli` 2.52.0 and `@stoplight/prism-cli` 5.16.0.
  Where neither tool can be installed, say that the contract is unvalidated rather than
  implying it passed.
