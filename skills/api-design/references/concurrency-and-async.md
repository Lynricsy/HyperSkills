# Concurrency, caching, idempotency and long operations

## Contents

- [Optimistic concurrency with ETag and If-Match](#optimistic-concurrency-with-etag-and-if-match)
- [Which status code for which precondition](#which-status-code-for-which-precondition)
- [Caching headers as contract](#caching-headers-as-contract)
- [Idempotency: three patterns](#idempotency-three-patterns)
- [Long-running operations](#long-running-operations)

## Optimistic concurrency with ETag and If-Match

Without a precondition, two clients that both read a resource and both write it produce a
lost update: the second write silently overwrites the first, and neither client learns
anything. The contract fix:

1. Every `GET` of a mutable resource returns `ETag` — an opaque quoted validator whose value
   changes whenever the representation changes. A hash of the body, a hash of the
   modification timestamp, or a stored version number all work; which one you use is an
   implementation detail, but that it is opaque to clients is contract.
2. `PUT`, `PATCH` and `DELETE` accept `If-Match: "<etag>"`. The server executes only if the
   current validator matches, and answers 412 otherwise.
3. Document whether `If-Match` is required or optional. If it is required, mark the header
   `required: true` in the document; that is clearer to clients than documenting a 428
   response they have to discover.

`If-None-Match: *` on a create makes "create only if it does not exist yet" explicit, which
is how you get a safe `PUT`-as-create.

For collections, an `ETag` over the whole collection plus `HEAD` or a conditional `GET` lets
a client cheaply ask "has anything changed" without transferring the list.

Embedded sub-resources can carry their own `etag` field in the body so a client can write
back one item of a list it fetched, without re-reading the parent. `[official]`

## Which status code for which precondition

| Situation | Code |
|---|---|
| `If-Match` did not match on a write | 412 |
| `If-None-Match` matched on a `GET`/`HEAD` (client's copy is current) | **304**, not 412 |
| Server requires the request to be conditional and it was not | 428 |
| Concurrent request conflicts with state but no precondition was involved | 409 |

The 304-versus-412 split is the one that gets implemented wrong: returning 412 on a
conditional read breaks HTTP caching for every intermediary. `[official]`

## Caching headers as contract

Cacheability is part of the contract, not a deployment setting. For each read operation
declare:

- `Cache-Control` — the freshness policy (`no-store` for anything user-specific by default,
  `max-age` plus `private` where a client cache is safe).
- `Vary` — every request header that changes the response. Omitting `Vary: Accept-Language`
  or `Vary: Authorization` on a cached response is how one tenant's data reaches another.
- `ETag`, so a client can revalidate cheaply instead of refetching.

Do not declare `Expires` alongside `Cache-Control`; two sources of truth for lifetime is one
too many. `[official]`

## Idempotency: three patterns

Idempotency is what makes a retry safe, and a retry after a timeout — where the client does
not know whether the first attempt landed — is the case that duplicates orders and charges.
`GET`, `PUT` and `DELETE` are idempotent by definition; `POST` and `PATCH` are not, and have
to be made so deliberately. Three patterns, in the order to reach for them: `[official]`

**1. Conditional key (`If-Match`).** The client sends the validator it read. Standard HTTP,
no server-side storage, and it also surfaces conflicts. Applies to updates. This is the
default choice for `PATCH` and `PUT`.

**2. Secondary key in the request body.** A business-unique key the client owns
(`external_order_ref`, an invoice number) is stored permanently on the resource. A repeat
create with the same key answers 409, or 200 with `Location` if you can prove the returned
representation is the original one. This is the strongest fix for duplicate creates —
"zombie resources" — because the guarantee lives in a unique constraint rather than in a
cache.

**3. Idempotency key header.** `Idempotency-Key: <client-generated unique value>`, stored
temporarily (24 hours is a common documented window) together with the first response, and
replayed verbatim on a repeat. This is stronger than HTTP idempotency: it promises the *same
response*, not just the same effect. Note two things in the contract:

- The header is **not standardised in any RFC**; the de-facto shape follows Stripe's. Document
  the name, the expected value format, the retention window, and what happens when the same
  key arrives with a different body (409 is the usual answer). `[community]`
- Correct implementation needs the resource write and the key-cache write to be atomic.
  Ship it only if that is true; a best-effort key cache is worse than none, because clients
  will trust it.

The three compose. `Idempotency-Key` plus a secondary key is the belt-and-braces
configuration for payments.

Status codes make a safe repeat distinguishable from a first create: 201 when this request
created the resource, 200 or 204 when it was already there. A client can then tell a
successful retry from a fresh side effect. `[official]`

## Long-running operations

An operation that cannot finish inside a request needs a contract of its own. Make it
asynchronous when the 99th-percentile duration exceeds about a second, or when the client
should poll before doing anything else. Holding the connection open instead means the load
balancer decides your timeout, and the client cannot tell a timeout from a failure.
`[official]`

The shape:

```http
POST /inventory-exports HTTP/1.1
Content-Type: application/json

{ "warehouse_id": 12, "format": "csv" }
```

```http
HTTP/1.1 202 Accepted
Operation-Location: https://api.example.com/v1/operations/01JQ8Z3T6K
Retry-After: 5

{
  "id": "01JQ8Z3T6K",
  "status": "running",
  "created_at": "2026-02-11T09:03:12Z"
}
```

- 202 plus an absolute URI naming a **status-monitor resource** the client polls. Return it
  in `Operation-Location`, and put the operation in the body too so a client that reads only
  the body still works.
- The status monitor is a resource: `GET` returns at least `status` (a documented enum with
  terminal values), and on failure the reason as problem details — the poll itself succeeded,
  so the poll response is 200 with a failed status inside, not a 4xx.
- On success, either return the result inline or link to the resource that was created. Say
  which; a status monitor that goes `succeeded` with no pointer to the output is unusable.
- `Retry-After` on the 202 and on each in-progress poll tells the client how often to come
  back, instead of leaving it to hammer or to sleep too long.
- If the client may supply the operation id (so it can retry the *submission* safely),
  answer 409 when that id already names a different request, and replay the original for an
  identical one.
- Give the status monitor a lifetime and document it — how long after completion it stays
  readable, and what a `GET` returns after that.
- **Do not model `PATCH` as a long-running operation.** Where an update genuinely takes
  minutes, expose it as an action that creates an operation resource instead. `[official]`

Cancellation, if supported, is `DELETE` on the operation or a `cancel` action on it; a
cancelled operation is a terminal status, not a 404.

<!-- sources: zalando-guidelines, microsoft-azure-guidelines, rfc9110-http, rfc9111-caching, rfc9457 -->
