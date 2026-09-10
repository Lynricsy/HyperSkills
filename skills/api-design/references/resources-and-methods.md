# Resources, URIs, methods, status codes

## Contents

- [Finding the resources](#finding-the-resources)
- [URI structure](#uri-structure)
- [Method semantics](#method-semantics)
- [Operations that are not CRUD](#operations-that-are-not-crud)
- [Choosing a status code](#choosing-a-status-code)
- [Representation shape](#representation-shape)

## Finding the resources

Resources come from the domain nouns clients need to address, not from the tables behind
them. An API that mirrors the database schema leaks the storage design into the contract and
freezes it: every normalisation, split or denormalisation later becomes a breaking change.

Work in this order:

1. List the nouns a client needs to name, fetch, create or change on its own.
2. For each, decide whether it is addressable — does a client ever need a URI for just this
   thing? If not, it is a field or a nested object, not a resource.
3. Decide ownership. A resource that only exists inside a parent (`/orders/{id}/lines`) is a
   sub-collection; one that has independent lifetime gets a top-level collection even when
   it is usually reached through a parent.
4. Only then write endpoints. Endpoints fall out of resources plus methods; the reverse
   ordering produces one endpoint per screen and a surface nobody can version.

Identifiers are part of the contract, and their **format** is as frozen as their name. If
`id` is an integer today, clients parse it as one; switching to a ULID is a breaking change
even with an alias. Prefer an opaque string from the start when you might ever renumber,
shard or merge. Sequential integers additionally leak volume and let clients enumerate the
collection. `[official]`

## URI structure

- Plural nouns for collections, an identifier segment for members:
  `/warehouses`, `/warehouses/{warehouseId}`.
- No verbs in paths. `POST /createWarehouse` duplicates what the method already says, and
  the moment a second verb appears (`/updateWarehouseName`) the surface stops being
  addressable — clients can no longer tell which URI names the thing.
- Nest at most one level (`/warehouses/{id}/items`). Deeper nesting encodes a traversal path
  into the URI, so any change in the relationship breaks it. If an item is addressable on its
  own, give it `/items/{itemId}` and keep the nested route as a filtered listing.
- One casing convention for path segments and one for query parameters and JSON fields,
  applied everywhere. Mixed casing in one API is a permanent tax on every client.
- Keep the version segment in front of everything or nowhere — a surface where `/warehouses`
  is v1 and `/api/v2/warehouses` is v2 has no version, it has two APIs.
- Query parameters carry filtering, sorting, pagination and field selection. They never
  carry the resource identity: `/warehouses?id=12` and `/warehouses/12` cannot both be the
  canonical URI, and only the second one caches, permalinks or appears in a `Location`
  header.

## Method semantics

| Method | Safe | Idempotent | Cacheable | Body on request |
|---|---|---|---|---|
| `GET` | yes | yes | yes | no |
| `HEAD` | yes | yes | yes | no |
| `POST` | no | **no** | only if that operation is itself safe | yes |
| `PUT` | no | yes | no | yes |
| `PATCH` | no | **no** | no | yes |
| `DELETE` | no | yes | no | no |
| `OPTIONS` | yes | yes | no | no |

Idempotent means repeating the request has the same intended effect on server state. It does
**not** promise the same response: `DELETE` twice leaves the resource gone both times but may
answer 204 then 404. `[official]`

Consequences that get missed:

- **`PUT` may create.** `PUT /warehouses/{id}` with a client-chosen identifier is a
  create-or-replace and answers 201 the first time, 200 or 204 after. That is the right
  method for an upsert; a `POST /updateX` that silently creates is an upsert wearing the
  wrong method, so no client and no proxy can reason about retrying it.
- **`PATCH` must state its media type.** `application/merge-patch+json` (RFC 7396) treats the
  body as a sparse object where `null` deletes a member — which means it cannot address a
  single array element, and sending `{"tags": ["a"]}` replaces the whole array.
  `application/json-patch+json` (RFC 6902) sends an operation list and can. Declaring
  `application/json` for a PATCH body says nothing, and every client guesses differently.
- **`PATCH` is not idempotent by default** — `{"op":"add","path":"/tags/-"}` appends every
  time. Make it idempotent deliberately (conditional request or an idempotency key) or
  document that it is not.
- **`POST` is the method for anything that does not fit.** Reaching for `GET` with side
  effects breaks caches and prefetchers; reaching for `PUT` on a collection replaces it.
- **Cacheability is a contract decision.** Declare `Cache-Control` and `Vary` per operation
  rather than leaving it to whatever the gateway defaults to; a collection that is
  `no-store` for one client and cached for five minutes for another is a support ticket
  nobody can reproduce. `[official]`

## Operations that are not CRUD

Some operations are genuinely not "create/read/update/delete a thing": reserve stock,
cancel an order, rotate a key, replay a webhook. Two workable shapes:

1. **State sub-resource** — model the outcome as a resource and let the method carry the
   verb: `PUT /orders/{id}/cancellation`. Idempotent for free, addressable afterwards, and
   the state is readable with a `GET`.
2. **Action endpoint** — `POST /orders/{id}/cancel`. Use when there is no meaningful state
   object to address afterwards. Keep it a leaf: nothing nests under an action.

Either way, an action that a client will retry needs an idempotency mechanism, because the
retry after a timeout is the case that double-charges. Prefer the state sub-resource when
you can, because it is idempotent by construction.

Search is not an action. `GET /items?q=bolt` stays a filtered collection so it caches and
paginates like one. A query too large for a URI is the one exception; then `POST /searches`
returning a result resource keeps the semantics honest.

## Choosing a status code

Success:

| Code | Use when |
|---|---|
| 200 | Read, or a write that returns the resulting representation |
| 201 | Something was created — **always with a `Location` header** naming it |
| 202 | Accepted and not finished; the body or `Operation-Location` names the status monitor |
| 204 | Success with nothing to return; deliberately, not because you had no time to design a body |

Client errors:

| Code | Use when |
|---|---|
| 400 | Malformed request — unparseable body, unknown query parameter, wrong type |
| 401 | No credentials or bad credentials (needs `WWW-Authenticate`) |
| 403 | Authenticated and not allowed |
| 404 | No such resource — including hiding a resource the caller may not know exists |
| 405 | The URI exists, this method does not (needs `Allow`) |
| 409 | The request conflicts with current state: duplicate secondary key, already finalised, operation id reused for a different request |
| 412 | A conditional request's precondition failed (`If-Match` did not match) |
| 415 | Unsupported request media type |
| 422 | Syntactically valid, semantically wrong — the field parsed but its value is not acceptable |
| 428 | The server requires this request to be conditional |
| 429 | Rate limited (needs `Retry-After`) |

Server errors: 500 for a bug, 503 for "not now" with `Retry-After`, 504 for a dependency
timeout. `[official]`

The three mistakes worth naming, because they all survive code review:

- **200 with an error body.** `{"ok": false}` at 200 forces every client to parse before it
  knows whether it succeeded, defeats every retry policy and gateway rule, and makes
  monitoring lie about the error rate. Every failure gets a 4xx or 5xx.
- **400 for everything.** The distinction between "I could not parse this" (400) and "I
  parsed it and it is not acceptable" (422), and between "you are not authenticated" (401)
  and "you are not allowed" (403), is what lets a client decide whether to retry, re-auth
  or fix its input.
- **Success on a no-op.** Deleting or releasing something that does not exist answers 404,
  not 200 with `{"ok": false}`. The exception is a genuinely idempotent delete that treats
  "already gone" as the desired state — that is a documented choice, not an accident.

## Representation shape

- **The top-level JSON value is an object, never an array.** An array has nowhere to add
  pagination links, a warning or a total later, so returning one paints the contract into a
  corner: every future addition is a breaking change. This is why `GET /shipments` returning
  a bare array is the expensive mistake in an otherwise fine spec. `[official]`
- Distinguish the write shape from the read shape. Server-owned fields (`id`, timestamps,
  computed totals) are read-only in the document and rejected — or ignored, stated
  explicitly — on write. One schema for both directions forces clients to guess.
- Represent money as a string plus an explicit currency, or as an integer minor unit with the
  unit in the field name. A JSON number for money is a float in most clients.
- Timestamps as RFC 3339 UTC (`2026-02-11T09:03:12Z`). Durations as ISO 8601 or as an
  integer with the unit in the name (`timeout_seconds`), never as a bare number.
- Put the unit in the field name whenever a unit exists (`weight_grams`, not `weight`).
  A field whose unit lives only in the description is one reinterpretation away from silently
  corrupting every client's arithmetic, and no schema check will catch it.
- Enumerations that can grow need documenting as open: clients must tolerate an unknown
  value. Say what a client should do with one (ignore, treat as "other", fail loudly) rather
  than leaving it to be discovered in production.

<!-- sources: zalando-guidelines, rfc9110-http, rfc9111-caching, rfc7396-merge-patch, google-aip, asyrafhussin-patterns, jeffallan-api-designer, wshobson-openapi-spec-generation -->
