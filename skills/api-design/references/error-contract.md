# The error contract (RFC 9457 problem details)

## Contents

- [One shape for every failure](#one-shape-for-every-failure)
- [The members](#the-members)
- [Defining a problem type](#defining-a-problem-type)
- [Validation failures](#validation-failures)
- [Telling retryable from terminal](#telling-retryable-from-terminal)
- [What never goes in an error body](#what-never-goes-in-an-error-body)
- [Migrating an API that has several error shapes](#migrating-an-api-that-has-several-error-shapes)

## One shape for every failure

Use problem details (RFC 9457) with the `application/problem+json` media type for every 4xx
and 5xx response the API can produce. RFC 9457 obsoletes RFC 7807: the format is unchanged in
substance, but material citing 7807 predates the registry and the `about:blank` guidance, so
write 9457. `[official]`

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json
Content-Language: en

{
  "type": "https://api.example.com/problems/insufficient-stock",
  "title": "Not enough stock to reserve",
  "status": 422,
  "detail": "Requested 40 units of SKU-8891; 12 are available in warehouse 12.",
  "instance": "/reservations/01JQ8Z3T6K",
  "available": 12,
  "warehouse_id": 12
}
```

A bespoke envelope — `{"error": {"code": ..., "message": ..., "details": [...]}}` — carries
the same information and costs every client a hand-written parser plus a guess at which of
your endpoints uses which variant. That is the situation the RFC exists to end.

Two shape decisions that are not optional:

- **The HTTP status and the `status` member agree.** They are the same fact stated twice, and
  a proxy that rewrites the status while the body keeps the old number is a real failure mode
  worth designing against.
- **A failure never ships under a 2xx status.** `200` with `{"ok": false}` breaks every
  retry policy, gateway rule and error-rate dashboard, and forces clients to parse before
  they know whether they succeeded.

Problem details fit naturally on 4xx and 5xx and are not the only option: if the response is
still a representation of the resource, describing the condition in the API's own format can
be better. Do not invent a "batch" problem type for several unrelated failures — return the
most relevant or most urgent one. `[official]`

## The members

| Member | Type | Meaning |
|---|---|---|
| `type` | URI reference | The problem type's primary identifier. Absent means `about:blank`. |
| `status` | integer | The HTTP status, restated. |
| `title` | string | Short, human-readable summary of the *type*, stable across occurrences. |
| `detail` | string | Human-readable explanation of *this* occurrence. |
| `instance` | URI reference | Identifies this occurrence, for support and forensics. |

Rules that clients and servers both depend on:

- **Consumers identify a problem by `type`, never by `title` or `detail`.** Those two are
  human-readable prose that may be localised via `Accept-Language` or reworded at any time.
  A client that branches on the message string breaks on the next copy edit — which is
  exactly what happens to an API whose only machine-readable signal is a `msg` field.
- **A consumer must ignore a member whose value has the wrong type** and continue as if it
  were absent. So a server must never overload a member with a different type in some cases.
- **Consumers should not automatically dereference `type`.** It is an identifier; making it
  an `https` URL that serves documentation is good practice for humans, but nothing fetches
  it at runtime, and it does not need to resolve for the contract to work.
- Use absolute URIs in `type`. A relative reference resolves against the response's base URI,
  so the same relative value means different things under different paths.
- Anything else you need is an **extension member** at the top level of the object
  (`available`, `warehouse_id`, `balance`). Extensions are how a problem type carries the
  data a client needs to recover. `[official]`

## Defining a problem type

One type per condition a client can meaningfully act on differently. Fewer types than that
and clients string-match; many more and nobody documents them.

For each type, fix:

- the `type` URI, under a path you control (`https://api.example.com/problems/<slug>`);
- the HTTP status it always uses;
- the `title`;
- which extension members it always carries, with their types.

Keep them in a registry — a page, a table in the OpenAPI document, one schema per type — and
treat that registry as contract surface: adding a type is compatible, changing what an
existing type means is not.

`about:blank` is the type for "nothing more to say than the status code": `type` omitted or
`about:blank`, and `title` is then the status phrase. Use it rather than inventing
`https://example.com/problems/bad-request`. `[official]`

Do not reuse HTTP status numbers as your error codes. `{"code": 402}` adds nothing the status
line did not already say; a code is only worth having when it is finer-grained than the
status.

## Validation failures

Field-level failures belong in one extension member, not in a second envelope:

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Request body failed validation",
  "status": 422,
  "instance": "/invoices/req-01JQ8Z",
  "errors": [
    { "pointer": "#/amount", "detail": "must be greater than 0" },
    { "pointer": "#/currency", "detail": "must be one of EUR, USD" }
  ]
}
```

- Locate each failure with a JSON Pointer for a body field, and name the parameter and its
  location for a query or header failure. "Invalid input" with no location is not actionable.
- Report all the failures you found, not the first. A client that has to round-trip once per
  bad field will round-trip once per bad field.
- 400 when the request could not be parsed or a parameter has the wrong type; 422 when it
  parsed and the values are unacceptable. Pick one for each case and keep it stable — the
  distinction is what tells a client whether to fix its serialisation or its data.
- Never echo back a rejected value that might be a credential or PII.

## Telling retryable from terminal

A caller that cannot tell "try again in a minute" from "this will never work" either retries
forever or gives up on transient failures. Give it a machine-readable answer:

- `Retry-After` on 429 and 503 — seconds or an HTTP-date. This is the signal clients should
  back off on, and it is standard, so libraries already honour it. Explaining the throttle in
  `detail` is fine; making the client parse `detail` to find the delay is not. `[official]`
- Retryable-by-status is the baseline contract: 408, 429, 502, 503 and 504 are worth
  retrying; 400, 401, 403, 404, 409, 412 and 422 are not, until the client changes something.
- If a condition breaks that pattern — a 409 that resolves itself once a background job
  finishes — say so in that problem type's documentation, or carry an extension member for
  it. Do not leave it implicit.
- Retries need idempotency to be safe. A retryable write with no idempotency mechanism is a
  duplicate charge with extra steps.

Rate-limit quota headers (remaining, reset) have no stable RFC yet, so treat them as an
addition on top of `Retry-After` rather than a replacement, and avoid the `X-` prefixed
spellings — that convention was deprecated by RFC 6648. `[community]`

## What never goes in an error body

- Stack traces, driver messages, SQL, constraint names, internal hostnames, file paths.
  `psycopg2.errors.UniqueViolation: duplicate key ... "idx_charges_idem"` tells an attacker
  the schema and tells the client nothing it can act on. Log it with a correlation id and
  return an opaque problem.
- Anything the caller is not authorised to know. A 404 that becomes a 403 for resources that
  exist is an existence oracle.
- Credentials, tokens, or the offending field value when it may be one.

Every error carries a correlation identifier — in `instance`, in an extension member, or in a
response header that is also in the log line. Without it, "the API returned 500 at some point
this morning" is unactionable.

## Migrating an API that has several error shapes

Changing an error body is a breaking change for anyone parsing it. Sequence it:

1. Write down the target problem types and their statuses first. The migration is
   mechanical once the registry exists.
2. Fix the status codes that are wrong (2xx-with-error first — those are the ones breaking
   client retry logic today) and keep the old body for now.
3. Serve problem details alongside the old shape by content negotiation: clients sending
   `Accept: application/problem+json` get the new body, everyone else keeps the old one.
   Where negotiation is not available, add the problem members to the existing body as extra
   fields, which is compatible, and remove the old ones only after clients have moved.
4. Announce the old shape as deprecated with a date, then remove it — the same deprecation
   discipline as any other breaking change.

<!-- sources: rfc9457, rfc9110-http, zalando-guidelines, orchestkit-api-design, jeffallan-api-designer, asyrafhussin-patterns -->
