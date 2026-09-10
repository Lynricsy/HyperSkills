# Transactions, locks, MVCC and vacuum

Verified against: PostgreSQL 18.6

## Contents

- Isolation levels and the retry contract
- Keeping transactions short
- The lock conflict matrix
- Deadlocks
- Queue tables with SKIP LOCKED
- Advisory locks
- MVCC and what dead tuples cost
- Autovacuum tuning
- Bloat and when VACUUM FULL is justified
- Transaction ID wraparound

## Isolation levels and the retry contract

`read committed` is the default. Each statement sees a snapshot taken at statement start, so
two statements in one transaction can see different data, and a lost update between a read
and a later write is possible.

`repeatable read` gives the whole transaction one snapshot. It does not queue conflicting
writes — it aborts:

```
ERROR:  could not serialize access due to concurrent update
```

`serializable` adds predicate locking and can additionally raise
`could not serialize access due to read/write dependencies among transactions`.

The contract for both is that **the application must retry**, from the beginning of the
transaction, with backoff. There is no server-side retry. If a codebase uses anything above
`read committed` without a retry wrapper, that is the finding — the isolation level is
providing a correctness guarantee the application then throws away as a 500.

Where `read committed` is fine and a lost update is the concern, make the write conditional
instead of raising the isolation level:

```sql
UPDATE orders SET status = 'shipped'
WHERE id = $1 AND status = 'pending'
RETURNING *;
```

Zero rows returned means someone else got there first, which the application can handle
without a retry loop. `SELECT ... FOR UPDATE` is the other tool: it takes a row lock so the
subsequent write is serialised, at the cost of blocking.

## Keeping transactions short

A transaction holds its locks and pins its snapshot until it ends. Two rules follow:

- **Never call an external service inside a transaction.** Validate, call the API, then open
  a transaction to record the result. A payment provider timing out should not hold a row
  lock for 30 seconds.
- Bound what a transaction may do: `SET LOCAL statement_timeout = '5s'` and
  `SET LOCAL lock_timeout = '2s'` inside it, rather than a session-wide setting that a
  pooled connection then carries to the next client.

`idle in transaction` is the pathological state: it holds locks, holds a snapshot, and blocks
vacuum from cleaning anything newer than it, on every table in the database. Cap it:

```sql
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
```

## The lock conflict matrix

Table-level modes, weakest to strongest. Each conflicts with every mode marked below it and
to the right of the diagonal:

| Mode | Taken by | Conflicts with |
|---|---|---|
| `ACCESS SHARE` | `SELECT` | `ACCESS EXCLUSIVE` |
| `ROW SHARE` | `SELECT ... FOR UPDATE/SHARE` | `EXCLUSIVE`, `ACCESS EXCLUSIVE` |
| `ROW EXCLUSIVE` | `INSERT`, `UPDATE`, `DELETE` | `SHARE` and above |
| `SHARE UPDATE EXCLUSIVE` | `VACUUM`, `ANALYZE`, `CREATE INDEX CONCURRENTLY`, `VALIDATE CONSTRAINT` | itself and above |
| `SHARE` | `CREATE INDEX` | `ROW EXCLUSIVE` and above — blocks writes, allows reads |
| `SHARE ROW EXCLUSIVE` | `CREATE TRIGGER`, `ADD FOREIGN KEY` | `ROW EXCLUSIVE` and above |
| `EXCLUSIVE` | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | everything but `ACCESS SHARE` |
| `ACCESS EXCLUSIVE` | most `ALTER TABLE`, `DROP`, `TRUNCATE`, `VACUUM FULL`, `CLUSTER` | everything |

The operational consequence matters more than the table: **lock requests queue in order**. A
long `SELECT` holding `ACCESS SHARE`, followed by an `ALTER TABLE` waiting for
`ACCESS EXCLUSIVE`, means every subsequent `SELECT` — which would not have conflicted with
the first one — now waits behind the `ALTER`. One slow reporting query plus one instant DDL
is a full outage. That is why `lock_timeout` on DDL is not optional (`migrations.md`).

Two useful sanity checks: `SHARE UPDATE EXCLUSIVE` self-conflicts, so a `VACUUM` and a
`CREATE INDEX CONCURRENTLY` on the same table serialise; and `SHARE` (plain `CREATE INDEX`)
allows concurrent reads, which is why the blocking index build is survivable on a read-heavy
table and fatal on a write-heavy one.

## Deadlocks

A deadlock is always two transactions taking the same locks in different orders. Postgres
detects it after `deadlock_timeout` (default 1s) and kills one:

```
ERROR:  deadlock detected
DETAIL:  Process 123 waits for ShareLock on transaction 456; blocked by process 789.
```

Two structural fixes:

```sql
-- 1. acquire in a deterministic order
SELECT * FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;

-- 2. or make it one statement, which locks in a single pass
UPDATE accounts
SET balance = balance + CASE id WHEN 1 THEN -100 WHEN 2 THEN 100 END
WHERE id IN (1, 2);
```

To see them at all, turn on the logging — deadlocks are otherwise only a counter:

```sql
ALTER SYSTEM SET log_lock_waits = on;      -- logs any wait beyond deadlock_timeout
SELECT datname, deadlocks FROM pg_stat_database WHERE datname = current_database();
```

## Queue tables with SKIP LOCKED

Workers polling a jobs table will otherwise all block on the same oldest row:

```sql
UPDATE jobs
SET    status = 'processing', worker_id = $1, started_at = now()
WHERE  id = (
    SELECT id FROM jobs
    WHERE status = 'pending'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;
```

`SKIP LOCKED` makes each worker take the oldest row nobody else holds, so N workers claim N
different jobs in one round. It is only correct for exactly this shape — a work queue where
skipping a contended row is desirable. Never use it for a read that must see all matching
rows.

Index `(status, created_at)`, ideally partial on `WHERE status = 'pending'`, or the claim
scans the whole completed history.

## Advisory locks

Application-defined locks keyed by a `bigint`, for mutual exclusion that has no row to attach
to — a cron job that must not run twice, a migration guard.

```sql
SELECT pg_advisory_xact_lock(hashtext('nightly-rollup'));   -- released at COMMIT/ROLLBACK
SELECT pg_try_advisory_xact_lock(hashtext('nightly-rollup'));  -- false instead of waiting
```

Prefer the `_xact_` variants. Session-level `pg_advisory_lock` must be released once per
acquisition, leaks if the code path throws, and — critically — does not survive a
transaction-mode connection pooler, which may hand the backend to another client between
statements.

## MVCC and what dead tuples cost

An `UPDATE` writes a new row version and marks the old one dead; a `DELETE` marks it dead.
Nothing is reclaimed until vacuum runs and no snapshot older than the deletion remains. Dead
tuples cost on every read: an index entry points at them, a scan visits and discards them,
and they inflate the table on disk.

```sql
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;
```

The single most common reason this number will not fall is one `idle in transaction` session
somewhere holding an old snapshot. Check that before tuning anything.

`VACUUM` also refreshes the visibility map, which is what index-only scans need — a table
that is never vacuumed produces index-only scans with large `Heap Fetches`.

## Autovacuum tuning

Defaults on 18.6 (`pg_settings`): `autovacuum_vacuum_scale_factor = 0.2`,
`autovacuum_analyze_scale_factor = 0.1`, `autovacuum_vacuum_cost_delay = 2ms`,
`autovacuum_worker_slots = 16`, `autovacuum_vacuum_max_threshold = 100000000`.

The scale factor is a fraction of the table, so on a 100M-row table the default means 20M
dead rows before autovacuum starts — far too late. `autovacuum_vacuum_max_threshold` (PG 18)
caps that in absolute terms; on 14–17, lower the scale factor per table instead:

```sql
ALTER TABLE hot_table SET (
    autovacuum_vacuum_scale_factor  = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);
```

Tune the tables that need it, not the cluster. Watch a running vacuum with
`pg_stat_progress_vacuum` (`phase`, `heap_blks_scanned`, `heap_blks_total`), and on PG 18
compare cumulative cost across tables with `total_vacuum_time` / `total_autovacuum_time` in
`pg_stat_user_tables`.

`VACUUM (BUFFER_USAGE_LIMIT '256kB')` (PG 16+) keeps a manual vacuum from evicting the
working set out of shared buffers.

## Bloat and when VACUUM FULL is justified

Ordinary `VACUUM` makes space reusable; it does not return it to the filesystem. A table that
grew during an incident stays large and mostly empty, which is fine — the space will be
reused — unless the bloat is extreme or the growth was one-off.

`VACUUM FULL` rewrites the table under `ACCESS EXCLUSIVE`: no reads, no writes, for as long
as the rewrite takes, and it needs room for a second copy. It is an outage, not maintenance.
The non-blocking alternatives are `REINDEX INDEX CONCURRENTLY` when the bloat is in an index
(often the case), or an external online-repack tool for the heap.

Bloat estimates from catalogue statistics are estimates. Confirm against
`pg_total_relation_size` trends before scheduling downtime.

## Transaction ID wraparound

Every row version carries the transaction ID that created it, and the counter is 32-bit.
Vacuum "freezes" old rows to keep the visible range from wrapping; if it cannot keep up,
Postgres warns, then refuses new transactions.

```sql
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database ORDER BY xid_age DESC;
```

`autovacuum_freeze_max_age` (default 200 million) triggers an anti-wraparound autovacuum that
runs **even on tables with autovacuum disabled** and does not yield to a conflicting lock
request the way an ordinary autovacuum does. Do not cancel one to unblock a migration — it
will come straight back, and cancelling repeatedly is how databases reach the read-only
state. PG 18 additionally freezes eagerly during normal vacuums, governed by
`vacuum_max_eager_freeze_failure_rate` (default 0.03), which spreads the cost.

<!-- sources: postgresql-docs, neon-postgres-skills, supabase-postgres-bp, microsoft-postgres-skills, timescale-pg-aiguide -->
