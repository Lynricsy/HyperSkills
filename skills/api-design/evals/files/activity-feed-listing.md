# `GET /v1/activities` — listing design note

## Current contract

```
GET /v1/activities?page=3&per_page=50
```

```json
{
  "data": [{ "id": 91823, "kind": "comment", "created_at": "2026-02-11T09:03:12Z" }],
  "meta": { "page": 3, "per_page": 50, "total_count": 4820113, "total_pages": 96403 }
}
```

Backing query:

```sql
SELECT * FROM activities
WHERE org_id = $1
ORDER BY created_at DESC
LIMIT 50 OFFSET 100;
```

## What we know

- The table takes roughly 400 inserts/second during business hours; rows are
  never updated but are hard-deleted after 90 days by a nightly job.
- `created_at` is not unique: bulk imports write thousands of rows with an
  identical timestamp.
- Clients are: a mobile app that scrolls infinitely, an export worker that walks
  the entire org history once a night, and an admin screen with numbered pages.
- Support keeps filing "I saw the same activity twice" and "an activity was
  missing from the export" tickets. Nobody can reproduce them on staging, which
  has no write traffic.
- `total_count` shows up in the p99 latency profile; the count query scans the
  whole org partition.
