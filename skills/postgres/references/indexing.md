# Indexing

Verified against: PostgreSQL 18.6

## Contents

- Choosing an access method
- When no index helps
- Composite indexes and column order
- Partial indexes
- Expression indexes
- Covering indexes and index-only scans
- Redundant, duplicate and unused indexes
- Building and rebuilding without blocking
- Indexes on partitioned tables

## Choosing an access method

The operator in the `WHERE` clause picks the access method, not the column's type.

| Predicate | Method | Note |
|---|---|---|
| `=`, `<`, `>`, `BETWEEN`, `IN`, `ORDER BY` | B-tree | The default and almost always right |
| `@>`, `<@`, `?`, `?|`, `?&` on JSONB or arrays | GIN | Containment and key existence |
| `@@` against `tsvector` | GIN | Full-text search |
| `LIKE '%x%'`, `ILIKE '%x%'`, similarity | GIN + `pg_trgm` | A leading wildcard is unindexable by B-tree |
| Range overlap `&&`, geometric, nearest-neighbour | GiST | Also the method behind `EXCLUDE` constraints |
| Very large append-only table scanned by a correlated column | BRIN | See the correlation caveat below |
| `<=>`, `<->`, `<#>` on `vector` | HNSW (pgvector) | See `jsonb-and-search.md` |

Two traps in that table:

- **GIN is not for scalar equality.** A GIN index on a JSONB column does not accelerate
  `data->>'status' = 'shipped'`; that needs a B-tree on the expression or on a stored
  generated column.
- **BRIN needs physical correlation.** It stores per-block-range minima and maxima, so it is
  only small *and* useful when rows arrive in key order. Check before creating one:

  ```sql
  SELECT attname, correlation
  FROM pg_stats
  WHERE tablename = 'events' AND attname = 'created_at';
  ```

  A correlation near 1.0 (or -1.0) is the precondition. Random `UPDATE`s move rows to new
  pages and silently destroy it, after which the index still exists and still returns correct
  answers, just uselessly.

Hash indexes exist and are crash-safe since PG 10, but they support only `=`, cannot be
unique, cannot be multicolumn, and cannot serve `ORDER BY`. Use B-tree unless you have
measured a specific win on very wide keys.

For text, the index's collation must match the query's. A `text_pattern_ops` index serves
`LIKE 'prefix%'` under a non-C collation; a default-collation index does not. Mismatched
collation means the index is simply never chosen, with no error.

## When no index helps

If a predicate matches more than roughly 10–20% of the table, a sequential scan is usually
cheaper than an index scan plus random heap access, and the planner is right to choose it.
`Seq Scan` in a plan is not automatically a finding. Before adding an index, check what
fraction of rows the predicate actually selects, and check whether the estimate is even
correct (`query-plans.md`).

## Composite indexes and column order

Equality columns first, then the range or `ORDER BY` column. A B-tree can use a leading run
of equality predicates plus one range predicate; anything after the range column is only a
filter.

```sql
-- WHERE tenant_id = $1 AND created_at >= $2 ORDER BY created_at DESC
CREATE INDEX events_tenant_created ON events (tenant_id, created_at DESC);
```

That index serves the filter and the ordering, so the plan has no `Sort` node. Reverse the
columns and the same query, on a 500k-row table with 50 tenants, falls back to a parallel
sequential scan:

```
-- only (created_at DESC, tenant_id) exists
 Parallel Seq Scan on events   Rows Removed by Filter: 166667   Buffers: shared hit=6668
-- only (tenant_id, created_at DESC) exists
 Index Only Scan using events_tenant_created   Heap Fetches: 100   Buffers: shared hit=6
```

PG 18's B-tree **skip scan** lets the planner use an index whose leading column is
unconstrained by generating one search per distinct leading value. That rescues a leading
column with a handful of distinct values; it does nothing for a near-unique one such as a
timestamp, as the plan above shows.

**Two single-column indexes are not one composite index.** The planner combines them with
`BitmapAnd`, which builds each side's bitmap in full before intersecting:

```
-- events_tenant(tenant_id) + events_status(status)
 BitmapAnd   Buffers: shared read=36
   ->  Bitmap Index Scan on events_tenant   (actual rows=10000.00)  read=12
   ->  Bitmap Index Scan on events_status   (actual rows=25000.00)  read=24
-- events_tenant_status(tenant_id, status)
 Index Only Scan using events_tenant_status   Heap Fetches: 0   Buffers: shared read=3
```

Bitmap intersection is the planner making the best of what it has, not a design goal.

## Partial indexes

A partial index is only considered when the planner can prove the query's predicate implies
the index's. `WHERE status = 'failed'` matches an index declared `WHERE status = 'failed'`;
it does not match one declared `WHERE status <> 'ok'`, even though the sets may coincide in
practice. Write the index predicate to match the query literally, and use only immutable
expressions — `WHERE created_at > now() - interval '30 days'` is rejected, because the index
would decay.

The payoff is size. On the same 500k-row table:

| Index | Size |
|---|---|
| `(tenant_id, created_at DESC)` | 15 MB |
| `(tenant_id, created_at DESC) WHERE status = 'failed'` | 784 kB |

The other standard use is a unique constraint over a subset:

```sql
CREATE UNIQUE INDEX users_one_primary_email
  ON user_emails (user_id) WHERE is_primary;
```

Note that `INSERT ... ON CONFLICT` needs a conflict target backed by an exact matching unique
index; a partial index qualifies only if the statement repeats the same predicate in
`ON CONFLICT (user_id) WHERE is_primary`.

## Expression indexes

Matched textually against the query, so the expression has to be identical:

```sql
CREATE INDEX users_lower_email ON users (lower(email));
-- used:     WHERE lower(email) = lower($1)
-- not used: WHERE email = $1
-- not used: WHERE upper(email) = upper($1)
```

The expression must be immutable. `date_trunc('month', created_at)` on a `timestamptz` is
stable, not immutable, because the result depends on `TimeZone`; pin it:

```sql
CREATE INDEX orders_month
  ON orders (date_trunc('month', created_at AT TIME ZONE 'UTC'));
```

For case-insensitive comparison, prefer the expression index over the `citext` type; reach
for `citext` only when the case-insensitivity has to be part of a key or foreign key so that
every comparison inherits it.

## Covering indexes and index-only scans

`INCLUDE` (PG 11+) appends non-key payload columns to the leaf entries:

```sql
CREATE INDEX orders_customer_inc ON orders (customer_id) INCLUDE (status, total);
```

Two things this does *not* do. It does not make writes cheaper — the payload is still
maintained. And it does not eliminate heap access: an index-only scan may still visit the
heap to check tuple visibility whenever the visibility map does not mark the page all-visible,
which on a recently written table is most pages. The plan tells you which happened:

```
Index Only Scan using orders_customer_inc on orders
  Heap Fetches: 0        -- genuinely index-only
  Heap Fetches: 48213    -- the visibility map is cold; vacuum the table
```

`INCLUDE` columns cannot be used as search or ordering keys. If you need to filter on the
column, it belongs in the key list.

## Redundant, duplicate and unused indexes

`(a)` is redundant once `(a, b)` exists. `(a, b)` is not redundant beside `(a, b, c)` if you
depend on index-only scans over just `a` and `b`, because the narrower index is smaller and
more of it stays cached — but that is a deliberate trade, not a default.

```sql
-- exact duplicates
SELECT indrelid::regclass AS table_name,
       array_agg(indexrelid::regclass) AS duplicates
FROM pg_index
GROUP BY indrelid, indkey
HAVING count(*) > 1;

-- never-scanned indexes, excluding constraint-backing ones
SELECT s.relname AS table_name, s.indexrelname AS index_name,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0
  AND NOT i.indisunique
  AND NOT i.indisprimary
ORDER BY pg_relation_size(s.indexrelid) DESC;
```

`idx_scan` counts since the last statistics reset and is per-node on a replica, so a zero
here means "not used in this window on this server". Confirm the window covers a monthly
report before dropping anything, and drop with `DROP INDEX CONCURRENTLY`.

## Building and rebuilding without blocking

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer ON orders (customer_id);
```

- Cannot run inside a transaction block — `ERROR: CREATE INDEX CONCURRENTLY cannot run
  inside a transaction block`. It therefore cannot live in a migration file that the tool
  wraps in `BEGIN`/`COMMIT`.
- Takes two table scans and waits for concurrent transactions, so it is slower in wall-clock
  terms than the blocking form. That is the trade.
- Leaves an invalid index behind on failure, which costs write overhead while serving no
  reads:

  ```sql
  SELECT indexrelid::regclass AS index_name, indrelid::regclass AS table_name
  FROM pg_index WHERE NOT indisvalid;
  ```

  Drop it with `DROP INDEX CONCURRENTLY` and retry.
- Do not put a `statement_timeout` on it. Being killed just before completion wastes the
  whole build.

`REINDEX INDEX CONCURRENTLY` (PG 12+) is the non-blocking rebuild for a bloated index. The
blocking `REINDEX` takes `ACCESS EXCLUSIVE`.

## Indexes on partitioned tables

There are no global indexes. An index on the partitioned parent is a template: creating it
propagates to existing and future partitions, and dropping the parent index drops the
children. But `CREATE INDEX CONCURRENTLY` is not supported on a partitioned parent, so the
non-blocking build is a three-step dance:

```sql
-- 1. invalid parent index, no data touched
CREATE INDEX events_customer ON ONLY events (customer_id);

-- 2. one concurrent build per partition
CREATE INDEX CONCURRENTLY events_2026q1_customer ON events_2026q1 (customer_id);
CREATE INDEX CONCURRENTLY events_2026q2_customer ON events_2026q2 (customer_id);

-- 3. attach; the parent becomes valid once every partition is attached
ALTER INDEX events_customer ATTACH PARTITION events_2026q1_customer;
ALTER INDEX events_customer ATTACH PARTITION events_2026q2_customer;
```

Any `UNIQUE` or `PRIMARY KEY` on a partitioned table must include every partition-key column,
because uniqueness can only be enforced within a partition. That constraint shapes the key
design, so decide the partition key before the primary key.

<!-- sources: postgresql-docs, neon-postgres-skills, supabase-postgres-bp, microsoft-postgres-skills, awesome-copilot-pg -->
