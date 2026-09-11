---
name: postgres
description: "Guides self-managed PostgreSQL work: schema and type selection, constraints, index choice and composite column order, reading EXPLAIN (ANALYZE, BUFFERS) and rewriting the query behind it, transactions, isolation and lock levels, MVCC, autovacuum and bloat, plain-SQL row-level security policy syntax and its performance, online schema migrations on a live table, connection limits and PgBouncer pool modes, JSONB, full-text search, pgvector, catalogue diagnostics, and the Postgres-side damage ORMs cause. Use when designing or reviewing a schema or migration, when a query got slow, when a plan shows a sequential scan or bitmap intersection, when writes block on locks or a table bloats, when connections or prepared statements fail under a pooler, or when picking an index type. Do not use for anything on the Supabase platform, including auth.uid() policies, JWT claims, an SDK returning no rows, and the Supabase dashboard or CLI; nor for hosting control planes such as RDS or Cloud SQL; nor for ORM syntax."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# postgres

## Scope

Covers PostgreSQL itself: schema and type selection, constraints, indexes and index
maintenance, plan reading and query rewriting, transactions and locking, MVCC and vacuum,
row-level security, online schema change, connection limits and pooling, JSONB, built-in
full-text search, pgvector, and the catalogue queries that answer "why is it slow".

The body is written against **PostgreSQL 18** (current stable; 18.6 at time of writing).
Rules that need a newer server than 14 carry a gate such as `(PG 15+)`. Nothing here
assumes 19, which is still in beta.

Not covered:

- The Supabase platform — Auth, Storage, Realtime, Edge Functions, the CLI and the
  dashboard. Use the `supabase` skill.
- ORM query-builder and migration-tool syntax. Use the `java-spring`, `laravel`,
  `fastapi` or `nodejs-backend` skill for the framework side; this skill only covers what
  an ORM does *to the database* — prepared statements under a pooler, N+1 round trips,
  migration locks, connection-per-request.
- Managed-hosting control planes: instance sizing, provider backups and PITR, IAM
  authentication, provider parameter APIs, read-replica provisioning on RDS, Cloud SQL or
  Azure Database for PostgreSQL. Use the `aws`, `gcp` or `azure` skill rather than
  improvising provider commands. The SQL-level rules here still apply on a managed server,
  but `ALTER SYSTEM` and anything under `/var/lib/postgresql` usually will not.
- Other databases, and Postgres-compatible products with their own semantics.

RLS policy syntax and its performance are the `postgres` skill's subject; the Supabase auth
context (`auth.uid()`, JWT claims) and the dashboard/CLI workflow around it are the
`supabase` skill's.

Paths below are relative to this skill's directory.

## Core rules

1. Establish the server version before quoting any rule with a gate: `SELECT version();`.
   Half the guidance in circulation is written for PG 11 and the safe migration patterns in
   particular changed in 12, 15 and 18.
2. Read the existing schema and its indexes before proposing either
   (`\d+ table`, or `pg_indexes` filtered by `tablename`). An index you were about to add
   often exists with the columns in the wrong order, which is a different fix.
3. Type choice is a constraint, not a preference: `timestamptz` never `timestamp`,
   `text` with a `CHECK (length(...) <= n)` never `varchar(n)`, `numeric` never `float` for
   money, `bigint generated always as identity` never `serial`. `serial` leaves the sequence
   ownership and grants out of sync and is not SQL-standard.
4. `CHECK` constraints pass on `NULL` — three-valued logic. A `CHECK (status IN (...))`
   without `NOT NULL` on the column enforces nothing for the rows that matter.
5. `UNIQUE` treats every `NULL` as distinct, so `(1, NULL)` can be inserted twice.
   `UNIQUE NULLS NOT DISTINCT (...)` (PG 15+) is what people usually meant.
6. In a multicolumn B-tree, equality predicates come first and the range or `ORDER BY`
   column last. PG 18's skip scan only rescues a *low*-cardinality leading column; with a
   high-cardinality one the index is unusable for a query that does not constrain it —
   measured here as a parallel sequential scan at 6668 buffers against 6 buffers for the
   same query on `(tenant_id, created_at DESC)`.
7. Two single-column indexes are not a substitute for one composite index. The planner
   intersects them with `BitmapAnd`, materialising each side's whole bitmap first; the
   composite index answers the same predicate with an index-only scan and roughly an order
   of magnitude fewer buffers.
8. An index on `(a)` is redundant once `(a, b)` exists — a B-tree serves any leftmost
   prefix. Drop it; every surviving index is write amplification and vacuum work.
9. A partial index is used only when the planner can *prove* the query's predicate implies
   the index's. Write the index predicate to match the query's `WHERE` clause literally.
10. An expression index is matched textually: `lower(email)` does nothing for a query on
    `email`, and a `timestamptz` expression must be timezone-independent
    (`date_trunc('month', created_at AT TIME ZONE 'UTC')`) or it is not immutable.
11. `INCLUDE` columns do not remove heap access. Index-only scans depend on the visibility
    map, so a recently written table still visits the heap — check `Heap Fetches` in the plan
    rather than assuming.
12. In `EXPLAIN ANALYZE`, node times and row counts are **per loop**. Multiply by `loops`
    before deciding what is expensive. PG 18 prints `Buffers` without being asked; on 14–17
    write `EXPLAIN (ANALYZE, BUFFERS)` explicitly.
13. When `rows=` and `actual rows=` differ by an order of magnitude, fix the estimate first —
    `ANALYZE`, or `CREATE STATISTICS` for correlated columns. An index chosen against a wrong
    estimate is the wrong index.
14. `ALTER TABLE` statements batched into one transaction hold the first `ACCESS EXCLUSIVE`
    lock until `COMMIT`. On a live table, commit each step separately and accept that the
    migration is no longer atomic.
15. Set `lock_timeout` on production DDL and retry, because a DDL statement waiting for
    `ACCESS EXCLUSIVE` queues every later query behind it. The statement being instant does
    not help; the wait is what causes the outage.
16. Adding a column with a non-volatile default (`now()`, a literal) is a catalogue change.
    Adding one with a volatile default (`gen_random_uuid()`, `clock_timestamp()`) rewrites the
    table and every index. Check `provolatile` in `pg_proc` when unsure rather than guessing
    from the name.
17. Never backfill a large table in one `UPDATE`. One statement over 180M rows floods WAL,
    doubles the on-disk size with dead tuples, cannot be interrupted cleanly, and holds its
    locks the whole time. Batch by primary key with a commit per batch.
18. `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block, takes two table scans,
    and leaves an invalid index behind when it fails. Follow it with
    `SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;`.
19. Add constraints in two steps: `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT`,
    which scans under a lock that allows concurrent reads and writes. A validated foreign key
    added in one step locks the referenced table too.
20. RLS is off until you enable it, and the table's owner is exempt even then unless
    `FORCE ROW LEVEL SECURITY` is set — which is why a policy suite passes in development
    (running as owner) and leaks in production. A role with `BYPASSRLS` ignores policies
    regardless.
21. `USING` decides which existing rows a statement may see; `WITH CHECK` decides which rows
    it may write. `FOR ALL` with only a `USING` clause reuses it as the `WITH CHECK`, and
    permissive policies for the same command are OR-ed — so one loose policy widens every
    other one. Use `AS RESTRICTIVE` when the intent is AND.
22. Wrap a function call in an RLS predicate as `(SELECT f())` when the predicate lands in a
    `Filter` node: measured 1223 ms unwrapped against 11 ms wrapped over 200k rows, because
    `STABLE` does not mean "cached". Where the predicate becomes an `Index Cond` the planner
    already evaluates it once, so index the policy's columns first and treat the wrap as the
    fix for the rows the index cannot eliminate.
23. Session `SET` does not survive a transaction-mode pooler. Set request context with
    `SET LOCAL` or `set_config('app.tenant_id', $1, true)` inside the transaction, and read it
    with the two-argument `current_setting('app.tenant_id', true)` so an unset value is `NULL`
    instead of an error.
24. Size the pool against the server, not the application: total active connections beyond
    roughly four times the database's CPU count buy contention, not throughput. Stacking an
    application pool on top of PgBouncer means multiplying, so shrink the application's pool
    when you add the pooler.
25. Transaction-mode pooling breaks session state, and the errors never mention pooling:
    `prepared statement "s0" already exists`, a `SET search_path` that vanishes before the next
    query, an unexplained read-only transaction (`SQLSTATE 25006`), a session advisory lock
    that is never held. Run migrations, dumps, `LISTEN`/`NOTIFY` and logical replication over a
    direct connection.
26. Finish with the gate: re-run the affected statement under `EXPLAIN (ANALYZE, BUFFERS)`,
    compare buffers against the before plan, and confirm no new invalid index or unvalidated
    constraint (`pg_index.indisvalid`, `pg_constraint.convalidated`). Report the numbers.

## Workflows

### diagnose-a-slow-query

- [ ] Check whether it is slow or blocked first: `pg_stat_activity` for `wait_event_type`
      and `state`. A query waiting on a lock is a locking problem, not a plan problem
      (`references/diagnostics.md`).
- [ ] Get the plan for the real parameters: `EXPLAIN (ANALYZE, BUFFERS)`, and use
      `SET plan_cache_mode = force_custom_plan` if the application uses prepared statements
      and only some parameter values are slow.
- [ ] Read it bottom-up and per-loop. Note the three signals that name their own fix:
      `Rows Removed by Filter` (missing or wrong index), `read` far exceeding `hit` (cold or
      genuinely scanning), `Sort Method: external merge` (`work_mem`).
- [ ] Compare `rows=` with `actual rows=` at every node. Correct the estimate before touching
      indexes (`references/query-plans.md`).
- [ ] Only then choose an index: the operator picks the access method, the predicate order
      picks the column order, selectivity decides whether an index helps at all
      (`references/indexing.md`).
- [ ] Check whether the query itself is the problem — `OFFSET` pagination, a per-row loop that
      should be `= ANY($1::bigint[])`, a correlated subquery that should be a window function.
- [ ] **Gate — the numbers moved:** re-run `EXPLAIN (ANALYZE, BUFFERS)` and quote both buffer
      counts. If the plan changed but the buffers did not, the index did not help.

### design-or-review-a-schema

- [ ] Fix the types first: `timestamptz`, `text` + `CHECK`, `numeric` for money,
      `bigint generated always as identity` or `uuidv7()` (PG 18+) for keys. Unquoted
      lowercase identifiers throughout (`references/schema-and-types.md`).
- [ ] Make every invariant a constraint, not a convention: `NOT NULL` beside each `CHECK`,
      `UNIQUE` with an explicit `NULLS NOT DISTINCT` decision, `EXCLUDE USING gist` where the
      rule is "these ranges must not overlap".
- [ ] Index every foreign key column on the child side. Postgres indexes the referenced side
      automatically and the referencing side never — so deletes and updates on the parent
      scan the child.
- [ ] Decide the semi-structured boundary explicitly: a column you filter or sort on is a
      column, not a JSONB key. Promote it with a stored generated column if the payload must
      stay JSONB (`references/jsonb-and-search.md`).
- [ ] Consider partitioning only for a table heading past ~100M rows or one whose maintenance
      is really bulk deletion by time. Any `UNIQUE` or `PRIMARY KEY` must then contain every
      partition-key column.
- [ ] Plan for updates: keep hot and cold columns apart, and remember that updating an indexed
      column forfeits the HOT optimisation and writes every index entry again.
- [ ] **Gate — the constraints hold:** apply the DDL to a scratch database, insert one row that
      each constraint should reject, and confirm each rejection by error message.

### make-a-schema-change-on-a-live-table

- [ ] Classify every statement by lock level and whether it rewrites the table, using the
      matrix in `references/migrations.md`. Anything that rewrites needs the
      add-column/backfill/swap treatment instead.
- [ ] Split the file so each statement commits on its own, and move
      `CREATE INDEX CONCURRENTLY` out of any transaction block entirely.
- [ ] Set `lock_timeout` (short) and let the deploy retry, rather than `statement_timeout`,
      which can kill a concurrent index build just before it finishes.
- [ ] Turn every validated constraint into `NOT VALID` plus a later `VALIDATE CONSTRAINT`,
      including the `NOT NULL` path — `ADD CONSTRAINT ... NOT NULL col NOT VALID` on PG 18, a
      `CHECK (col IS NOT NULL) NOT VALID` first on 12–17.
- [ ] Write the backfill as a bounded loop over the primary key with a commit per batch, and
      watch `pg_stat_replication` lag while it runs.
- [ ] Order the deploy around the application: stop reading a column before dropping it, and
      write to both columns while a type swap is in flight.
- [ ] Write the rollback down before running anything, and name the statements that have none
      (`DROP COLUMN`, a lossy type change, `TRUNCATE`).
- [ ] **Gate — rehearsed on real data:** run the whole sequence against a restored copy of
      production, then confirm on the target that no index is invalid and no constraint is
      left unvalidated.

### write-or-fix-rls-policies

- [ ] Enable and force: `ENABLE ROW LEVEL SECURITY` plus `FORCE ROW LEVEL SECURITY`, then list
      the roles that still bypass it (`SELECT rolname FROM pg_roles WHERE rolbypassrls`).
- [ ] Write one policy per command rather than one `FOR ALL`, so the read predicate and the
      write predicate are visible separately, and give every write policy an explicit
      `WITH CHECK` (`references/rls.md`).
- [ ] Audit how the permissive policies combine: they OR together for the same command. Anything
      that must always hold is `AS RESTRICTIVE`.
- [ ] Put the tenant key in transaction-local state (`SET LOCAL` / `set_config(..., true)`) and
      read it with the two-argument `current_setting`.
- [ ] Index every column a policy references, then re-check the plan: the predicate should be
      an `Index Cond`. If it is still a `Filter`, wrap the function call as `(SELECT f())`.
- [ ] Replace correlated `EXISTS` lookups over a membership table with a non-correlated form or
      a `SECURITY DEFINER` helper in a non-exposed schema, `SET search_path = ''`, with
      `EXECUTE` revoked from `PUBLIC`.
- [ ] **Gate — proven from the other side:** `SET ROLE` to the application role and run the
      read, the insert that should be rejected, and the update that tries to move a row out of
      the tenant. All three must behave, and `EXPLAIN` must show the policy predicate as an
      index condition.

### fix-connection-and-pooling-failures

- [ ] Count what is actually connected and in what state: idle, idle in transaction, active,
      and the oldest `state_change` (`references/connections.md`).
- [ ] Distinguish exhaustion from leakage. `idle in transaction` sessions also block vacuum, so
      they cost more than a slot.
- [ ] Work out the real ceiling: pool size per instance times instances, against
      `max_connections` and against roughly four times the CPU count.
- [ ] Match the pool mode to what the application needs. Transaction mode is the default;
      session mode is the escape hatch for `LISTEN`/`NOTIFY`, session advisory locks and
      cross-transaction temporary tables.
- [ ] For prepared statements under transaction pooling, prefer protocol-level prepared
      statements with PgBouncer's `max_prepared_statements` (1.21+) over disabling prepare in
      the driver, and never SQL-level `PREPARE`.
- [ ] Route migrations, dumps and logical replication to a direct connection.
- [ ] **Gate — the failure is reproduced and gone:** re-run the operation that failed over the
      pooled connection and show it succeeding, with the pooler's own counters (`SHOW POOLS`)
      showing no waiting clients.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Types and the ones to avoid, identifiers and case folding, constraints including `EXCLUDE` and deferrable, generated columns, TOAST and fillfactor, enums versus lookup tables, partitioning rules | Designing or reviewing DDL, or deciding how to store something | `references/schema-and-types.md` |
| Access-method selection by operator, composite column order, partial/expression/covering indexes, redundant and unused index detection, index maintenance and partitioned-table index builds | Choosing, auditing or rebuilding indexes | `references/indexing.md` |
| Plan node vocabulary, per-loop arithmetic, estimate errors and extended statistics, `work_mem` and `hash_mem_multiplier`, JIT, plan caching, and the query rewrites that beat an index | Holding an `EXPLAIN` output and deciding what to change | `references/query-plans.md` |
| Isolation levels and the retry contract, the lock conflict matrix, deadlock avoidance, `SKIP LOCKED` queues, advisory locks, MVCC, autovacuum tuning and bloat | Writes block, deadlock, or a table grows without gaining rows | `references/transactions-and-locks.md` |
| Policy syntax, `USING` versus `WITH CHECK`, permissive versus restrictive, `FORCE` and `BYPASSRLS`, tenant context under pooling, policy performance and helper functions | Writing, reviewing or debugging row-level security | `references/rls.md` |
| DDL lock and rewrite matrix, safe rewrite for each operation, batched backfills, concurrent index and constraint patterns, rollback planning | Changing the schema of a table that is in use | `references/migrations.md` |
| `max_connections` and memory, PgBouncer modes and settings, prepared statements across poolers, driver defaults, and the Postgres-side damage ORMs do | Connections exhaust, or an ORM behaves differently through a pooler | `references/connections.md` |
| JSONB operators, indexing and the operator-class limits, full-text search with `tsvector`, pgvector index and distance-operator pairing, recall tuning | Storing documents, searching text, or querying embeddings | `references/jsonb-and-search.md` |
| Catalogue and `pg_stat_*` queries for locks, bloat, index usage, missing FK indexes, buffer cache, statement statistics, plus backup and restore basics | Answering "what is the database doing right now" | `references/diagnostics.md` |

## Output format

When reviewing SQL or DDL, group findings by file and lead each with the location:

```
path/to/file.sql:12 - blocking - ALTER COLUMN amount TYPE bigint rewrites the whole table
  under ACCESS EXCLUSIVE. Add amount_new, backfill in batches, swap, drop.
```

Order findings by blast radius — statements that take `ACCESS EXCLUSIVE` on a live table
first, then correctness, then performance, then style. For a performance finding, quote the
plan evidence (`buffers`, `actual rows`, `Rows Removed by Filter`) rather than asserting that
something is slow, and give the before/after statement.

## Environment

- Reproduce against the same major version as production; `docker run -e POSTGRES_PASSWORD=…
  postgres:18` is enough for lock levels, plan shapes and policy behaviour, and settling a
  version-gated question by running it beats quoting a blog post.
- `pg_stat_statements` needs `shared_preload_libraries` and a restart, so it is either already
  there or not available today. Say which rather than assuming.
- pgvector, `pg_trgm` and `btree_gin` are extensions: check `pg_available_extensions` before
  writing DDL that depends on them, and remember that `CREATE EXTENSION` is a privileged,
  database-altering statement.
- On managed hosting, `ALTER SYSTEM`, configuration files and OS-level commands are usually
  unavailable; parameter changes go through the provider's control plane, which this skill
  does not cover.
