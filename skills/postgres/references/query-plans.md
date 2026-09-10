# Reading plans and rewriting queries

Verified against: PostgreSQL 18.6

## Contents

- Getting a plan worth reading
- Per-loop arithmetic
- The four signals that name their own fix
- Estimate errors and extended statistics
- Memory: work_mem and hash_mem_multiplier
- Planner settings people reach for too early
- Plan caching and parameter skew
- JIT
- Rewrites that beat an index

## Getting a plan worth reading

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

`ANALYZE` executes the statement — never run it on a mutating statement you do not want
applied (wrap in `BEGIN; ... ROLLBACK;` if you must). From PG 18, `BUFFERS` is included in
`ANALYZE` output automatically; on 14–17 it must be requested, and a plan without it is
missing the most useful column.

Two more options worth knowing: `SETTINGS` prints non-default planner GUCs that are shaping
the plan, and `GENERIC_PLAN` (PG 16+) plans a parameterised statement without executing it,
which is how you inspect a query that only exists as a prepared statement.

Before reading the plan at all, check that the query is slow rather than blocked:

```sql
SELECT pid, state, wait_event_type, wait_event, now() - query_start AS runtime, left(query, 80)
FROM pg_stat_activity
WHERE state <> 'idle' AND backend_type = 'client backend'
ORDER BY runtime DESC;
```

`wait_event_type = 'Lock'` is a locking problem; no amount of indexing fixes it.

## Per-loop arithmetic

Every `actual time` and `actual rows` on a node is **per loop**. A nested loop's inner side
showing `actual time=0.08..0.11 rows=1 loops=45000` is not fast — it is roughly five seconds.
Multiply before judging, and read the plan bottom-up: the leaves are where the rows and the
buffers come from.

`Buffers` is cumulative up the tree, so a parent's count includes its children's. The number
to compare between a before and after plan is the top node's, and the number that localises
the cost is the difference between a node and the sum of its children.

## The four signals that name their own fix

| In the plan | Means | Fix |
|---|---|---|
| `Rows Removed by Filter: <large>` | Rows were read and thrown away | Index the filtered column, or reorder a composite index so the predicate becomes an `Index Cond` |
| `Buffers: shared read=<large> hit=<small>` | Pages came from disk | Cold cache, or the query is genuinely scanning. Do **not** raise `shared_buffers` when the cause is a full scan |
| `Sort Method: external merge  Disk: 84000kB` | The sort spilled | Raise `work_mem` for this statement, or avoid the sort with an index whose order matches |
| `Heap Fetches: <large>` on an index-only scan | The visibility map is cold | `VACUUM` the table; the index is fine |

Two more that are frequently misread. `Recheck Cond` on a bitmap heap scan is normal — it is
how bitmap scans work, and only becomes interesting when accompanied by `Lossy Heap Blocks`,
which means the bitmap outgrew `work_mem` and degraded to page granularity. And `Seq Scan` on
a small table, or on a query returning a large fraction of the rows, is the correct plan.

## Estimate errors and extended statistics

Compare `rows=` (estimate) with `actual rows=` at each node. An order-of-magnitude gap means
the planner is choosing between plans using wrong numbers, and an index added on top of a
wrong estimate is usually the wrong index.

```sql
SELECT relname, n_live_tup, n_mod_since_analyze, last_analyze, last_autoanalyze
FROM pg_stat_user_tables WHERE relname = 'orders';
```

A large `n_mod_since_analyze` relative to `n_live_tup` means the statistics are stale; run
`ANALYZE orders;`.

If statistics are fresh and the estimate is still wrong, the usual cause is correlated
columns — the planner multiplies per-column selectivities and assumes independence, so
`WHERE country = 'JP' AND city = 'Osaka'` is estimated far too low:

```sql
CREATE STATISTICS orders_geo (dependencies, ndistinct) ON country, city FROM orders;
ANALYZE orders;
```

For a skewed column where the default 100 buckets miss the tail, raise the target on that
column only:

```sql
ALTER TABLE orders ALTER COLUMN customer_id SET STATISTICS 1000;
ANALYZE orders;
```

## Memory: work_mem and hash_mem_multiplier

`work_mem` is per sort or hash **operation**, not per query and not per connection. A plan
with three sorts running across two parallel workers can allocate six times `work_mem`. That
is why raising it globally is dangerous and raising it for one statement is not:

```sql
BEGIN;
SET LOCAL work_mem = '256MB';
SELECT ...;
COMMIT;
```

Hash nodes get `work_mem × hash_mem_multiplier` (default 2.0), so a hash join has twice the
budget of a sort by default. If a hash join is spilling (`Batches: 8` rather than 1) that is
the knob to look at before the join order.

`effective_cache_size` reserves nothing — it tells the planner how much of the table it can
expect to find in the OS page cache, which shifts the choice between index and sequential
scans. Setting it to roughly 75% of RAM is standard; it costs no memory.

## Planner settings people reach for too early

`SET enable_seqscan = off` is a diagnostic, not a fix. It does not disable the scan, it adds
a large constant to its cost — a plan node then shows `Disabled: true` (PG 18 labels it
explicitly). Use it to find out whether a usable index exists at all, then fix the real
cause: statistics, `random_page_cost` (1.1 on SSDs is the common correction from the default
4.0), or the index itself.

## Plan caching and parameter skew

A prepared statement reverts to a **generic plan** after five executions if the generic plan
is not estimated to be worse. For a column with a skewed distribution that plan can be right
for most parameter values and catastrophic for one. Test it:

```sql
SET plan_cache_mode = force_custom_plan;   -- always re-plan per parameter
SET plan_cache_mode = force_generic_plan;  -- always the parameter-blind plan
```

If forcing a custom plan fixes the slow case, the fix is either that setting on the session
that runs it or breaking the statement into two with different literals.

## JIT

JIT compilation triggers on estimated cost (`jit_above_cost`, default 100000), not on actual
work. A query whose cost is over-estimated pays milliseconds of compilation for microseconds
of execution, and the plan reports it:

```
 JIT:
   Functions: 42
   Timing: Generation 3.1ms, Inlining 12.4ms, Optimization 88.2ms, Emission 41.0ms, Total 144.7ms
```

If `Total` is a significant fraction of the execution time, raise `jit_above_cost` or
`SET jit = off` for that workload. Fixing the estimate is better where possible.

## Rewrites that beat an index

**`OFFSET` pagination.** `LIMIT 20 OFFSET 40000` reads and discards 40000 rows; the cost grows
with the page number. Use a keyset cursor over a unique-enough ordering:

```sql
-- page 1
SELECT * FROM events WHERE tenant_id = $1
ORDER BY created_at DESC, id DESC LIMIT 20;

-- subsequent pages, carrying the last row's (created_at, id)
SELECT * FROM events
WHERE tenant_id = $1 AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC LIMIT 20;
```

The row-comparison form is what makes this correct when timestamps tie; comparing the two
columns separately with `AND` is a different and wrong predicate. It needs an index on
`(tenant_id, created_at DESC, id DESC)`. The trade-off is no random page access — accept
that, or keep `OFFSET` for a bounded number of pages only.

**N+1 round trips.** A loop issuing one query per identifier is dominated by round-trip
latency, not by the database. Collapse it:

```sql
SELECT * FROM users WHERE id = ANY($1::bigint[]);
```

One statement, one plan, one index scan per identifier inside the server.

**Counting variants in separate queries.** Replace N `count(*)` statements with one pass:

```sql
SELECT count(*) FILTER (WHERE status = 'ok')     AS ok,
       count(*) FILTER (WHERE status = 'failed') AS failed
FROM events WHERE tenant_id = $1;
```

**Correlated subquery per row.** A per-row aggregate over the same table is a window function:

```sql
SELECT id, price, avg(price) OVER (PARTITION BY category_id) AS category_avg
FROM products;
```

**Non-sargable predicates.** Wrapping the column in a function hides it from the index. Move
the transformation to the constant side:

```sql
-- unindexable
WHERE date_trunc('day', created_at) = '2026-09-11'
-- indexable
WHERE created_at >= '2026-09-11' AND created_at < '2026-09-12'
```

Same for `WHERE amount::text LIKE '1%'` and `WHERE upper(email) = $1` against an index on
`email`.

**CTEs.** From PG 12 a `WITH` clause is inlined when it is used once and has no side effects,
so the old "CTEs are an optimisation fence" advice is obsolete — and `MATERIALIZED` is now the
way to *ask* for the fence when you want a subquery computed once. Verify by looking for a
`CTE Scan` node: if it is there, it was materialised.

<!-- sources: postgresql-docs, microsoft-postgres-skills, neon-postgres-skills, supabase-postgres-bp, awesome-copilot-pg -->
