# Collections: pagination, filtering, sorting, field selection

## Contents

- [Pick the pagination scheme from the write pattern](#pick-the-pagination-scheme-from-the-write-pattern)
- [Offset and page numbers](#offset-and-page-numbers)
- [Keyset](#keyset)
- [Opaque cursors](#opaque-cursors)
- [Total counts](#total-counts)
- [Filtering](#filtering)
- [Sorting](#sorting)
- [Sparse fieldsets and expansion](#sparse-fieldsets-and-expansion)

## Pick the pagination scheme from the write pattern

Every collection is paginated from its first release. Adding pagination later is a breaking
change even though it only adds fields: a client that used to receive all 75 items now
receives the first 50 and does not know to ask for more. Raising the default does not fix it,
because the collection grows. `[official]`

| Scheme | Correct when | Fails when |
|---|---|---|
| Offset / page number | The collection is stable while a client walks it, or jump-to-page is a real requirement | Rows are inserted or deleted between page requests: the window shifts, so items repeat or vanish |
| Keyset | There is a total order on immutable columns, and clients walk forwards or backwards | Jump-to-page; sort keys that are not unique; the row a cursor points at is deleted |
| Opaque cursor (usually keyset inside) | Anything client-facing — it is keyset plus the freedom to change the implementation | Same as keyset; additionally needs a decision about cursor lifetime |

Default to an opaque cursor for client-facing listings. Keep offset only for the specific
screen that needs numbered pages, and document that it can repeat or skip rows under
concurrent writes rather than pretending it cannot.

Two schemes on one endpoint is a valid design (`page=` for the admin screen, `cursor=` for
the feed) as long as they are mutually exclusive and the response says which one produced it.
Silently accepting both and mixing them produces pages that no client can reconcile.

## Offset and page numbers

`LIMIT 50 OFFSET 100` asks the database for the 101st through 150th row *of the query as it
is right now*. Between the client's page 3 and page 4:

- 50 rows inserted before the window → every row in the old window has shifted 50 places
  down, so page 4 re-serves what page 3 already showed.
- 50 rows deleted before the window → the window jumps forward, so 50 rows are never served.

That is the whole mechanism behind "I saw the same item twice" and "the export missed rows".
It reproduces only under concurrent writes, which is why a staging environment with no write
traffic never sees it, and why the bug is usually blamed on the client.

Offset also degrades: the database must count and discard every skipped row, so page 1000
costs a thousand pages of work.

Cap the page size in the contract (a documented default and a documented maximum) and coerce
a larger request down rather than erroring. A collection endpoint with no maximum is an
outage waiting for one client to ask for everything. `[official]`

## Keyset

Page forward by asking for rows after the last one seen, in a total order:

```
GET /activities?page[size]=50
GET /activities?page[after]=<cursor>&page[size]=50
```

```sql
SELECT * FROM activities
WHERE org_id = $1 AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

The two rules that decide whether this works:

1. **The sort key must be a total order.** `created_at` alone is not, if two rows can share a
   timestamp — and a bulk import guarantees they do. Append a unique tiebreaker (`id`) to
   both the `ORDER BY` and the comparison, and put both values in the cursor. Sorting on a
   non-unique key without a tiebreaker reintroduces exactly the duplicate-and-skip behaviour
   the switch away from offset was meant to fix.
2. **The cursor's row can disappear.** If a retention job deletes the row a cursor names, a
   naive `WHERE id > $cursor_id` lookup that first fetches that row fails. Comparing against
   the *values* carried in the cursor rather than re-reading the row makes deletion harmless.

Backwards paging is the mirrored comparison plus a reversed sort, re-reversed before
returning. Say in the contract whether `before` is supported; clients cannot infer it.

An absent next-page link or cursor is the only signal that the walk is finished. Do not use
an empty item array for it — a page can legitimately be empty and still have more behind it
— and never require the client to compare a count against a total. `[official]`

## Opaque cursors

A cursor is a token the server issues and the client only echoes back.

- **Opaque means unparseable, not encoded.** Base64 of `created_at=...&id=...` is not
  obfuscation: clients will decode it, then construct their own, and the encoding becomes
  part of your public contract. Sign it, encrypt it, or store it server-side. `[official]`
- Put everything needed to recreate the query in the cursor — position, direction, and the
  filters (or a hash of them). Then either reject a cursor whose filter hash does not match
  the request, or document that filters must stay identical while paging. A cursor reused
  under different filters silently returns nonsense.
- A cursor carries position only. It is not a capability: authorise the request exactly as
  you would without it.
- Cursors may expire. If they do, say so and answer a stale cursor with a 4xx that tells the
  client to restart, not with an empty page that looks like the end of the collection.
- Return cursors as links (`links.next` holding a full URI) rather than as bare tokens the
  client must splice into a URI. Clients follow links; they get string concatenation wrong.

## Total counts

Do not return a total by default. Counting the matches for a filtered query usually means
scanning the whole index, so the count costs more than the page and shows up in the p99 of
every listing. `[official]`

If a client genuinely needs one:

- Make it opt-in — a query parameter or `Prefer: return=total-count` — and document that the
  server may ignore the request.
- Say whether it is exact or an estimate. An estimate is usually enough for "about 4.8M
  results" and costs nothing.
- Never make `total_pages` part of a keyset response. There is no page count without offsets,
  and clients that compute one will loop forever.

## Filtering

- Filters are query parameters named after the field: `?status=booked&created_after=2026-01-01`.
- Enumerate the operators you support and reject the rest. A grammar you did not design
  (`?filter=status eq 'booked' and total gt 100`) is a query language you now have to
  implement, secure and version.
- Combining values: repeat the parameter (`?status=booked&status=in_transit`) or use a
  documented separator — one of the two, applied everywhere.
- A filter parameter you accept and silently ignore is worse than a 400. The client believes
  it filtered.
- Adding an accepted value to a request-side filter enum is compatible. Removing one, or
  narrowing what an existing value matches, is breaking.

## Sorting

- One parameter, a documented field allow-list, `-` for descending:
  `?sort=-created_at,id`. An open sort field means an unindexed sort on request.
- Every sortable listing needs a deterministic total order, so append the tiebreaker even
  when the client did not ask for one. Without it, two requests with the same sort can return
  the same row twice across pages.
- The default sort is part of the contract. Changing it changes what page 1 contains for
  every existing client, which is a breaking change even though no schema moved.

## Sparse fieldsets and expansion

- `?fields=id,status,total` lets a client trim a large representation. Always return the
  identifier whether or not it was asked for, and reject unknown field names instead of
  ignoring them.
- `?expand=customer` inlines a related resource to save a round trip. Cap the depth and the
  number of expansions in the contract; unbounded expansion is a query amplifier a single
  client can point at your database.
- Both are optional optimisations. If neither is implemented, the default representation must
  still be small enough to serve — sparse fieldsets are not a licence for a 400-field object.

<!-- sources: zalando-guidelines, google-aip, microsoft-azure-guidelines, asyrafhussin-patterns, jeffallan-api-designer -->
