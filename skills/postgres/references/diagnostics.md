# Diagnostics

Verified against: PostgreSQL 18.6

Catalogue queries for answering "what is the database doing right now", plus the backup
basics that every other answer depends on. All of these are read-only except where noted.

## Contents

- What is running
- Who is blocking whom
- Statement statistics
- Table and index sizes
- Index usage and missing foreign-key indexes
- Cache behaviour
- I/O by backend type
- Vacuum and bloat
- Replication
- Settings and their sources
- Backup and restore basics

## What is running

```sql
SELECT pid, usename, application_name, state,
       wait_event_type, wait_event,
       now() - xact_start  AS txn_age,
       now() - query_start AS query_age,
       left(query, 120)    AS query
FROM pg_stat_activity
WHERE backend_type = 'client backend' AND state <> 'idle'
ORDER BY xact_start;
```

Read `wait_event_type` first. `Lock` means blocked, not slow. `IO` means the data is not
cached. `Client` means the server is waiting for the application to read the result — the
query finished and something downstream is slow. A `NULL` wait event with `state = 'active'`
is the only case where the query itself is the work.

`state = 'idle in transaction'` with a large `txn_age` is the highest-value finding in this
whole file: it holds locks and blocks vacuum across the database.

## Who is blocking whom

```sql
SELECT blocked.pid          AS blocked_pid,
       left(blocked.query, 60)  AS blocked_query,
       blocking.pid         AS blocking_pid,
       left(blocking.query, 60) AS blocking_query,
       now() - blocked.query_start AS blocked_for
FROM pg_stat_activity blocked
JOIN LATERAL unnest(pg_blocking_pids(blocked.pid)) AS b(pid) ON true
JOIN pg_stat_activity blocking ON blocking.pid = b.pid
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;
```

`pg_blocking_pids()` does the lock-graph walk that used to require a self-join over
`pg_locks`. Use `pg_locks` only when the lock *mode* matters:

```sql
SELECT l.pid, l.locktype, l.mode, l.granted, l.relation::regclass AS relation
FROM pg_locks l
WHERE l.relation = 'orders'::regclass
ORDER BY l.granted, l.pid;
```

To unblock: `pg_cancel_backend(pid)` cancels the statement and is almost always the right
first move; `pg_terminate_backend(pid)` kills the connection and rolls back its transaction.
Never pass `pg_backend_pid()`.

## Statement statistics

`pg_stat_statements` requires `shared_preload_libraries = 'pg_stat_statements'` and a
restart, so it is either already installed or unavailable today — check rather than assume:

```sql
SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements';
```

```sql
-- where the server's time actually goes
SELECT calls, round(total_exec_time::numeric, 1) AS total_ms,
       round(mean_exec_time::numeric, 2)  AS mean_ms,
       rows, left(query, 100) AS query
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
ORDER BY total_exec_time DESC
LIMIT 20;
```

Rank by `total_exec_time`, not `mean_exec_time`. A 3 ms query called two million times is a
bigger problem than a 4-second report run nightly, and it is the shape an ORM N+1 takes —
high `calls`, low `mean_exec_time`, trivial `rows`.

Reset after a deploy so the next window is attributable:
`SELECT pg_stat_statements_reset();`.

## Table and index sizes

```sql
SELECT c.relname,
       pg_size_pretty(pg_total_relation_size(c.oid))                          AS total,
       pg_size_pretty(pg_relation_size(c.oid))                                AS heap,
       pg_size_pretty(pg_indexes_size(c.oid))                                 AS indexes,
       pg_size_pretty(pg_total_relation_size(c.reltoastrelid))                AS toast
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(c.oid) DESC
LIMIT 20;
```

Indexes exceeding the heap is normal on a narrow, heavily-indexed table and a smell on a wide
one. TOAST dominating means large documents — see `jsonb-and-search.md`.

## Index usage and missing foreign-key indexes

Unused and duplicate index queries are in `indexing.md`. The one that belongs here is the
foreign key with no supporting index, because it is invisible until a delete on the parent
takes minutes:

```sql
SELECT c.conrelid::regclass AS child_table,
       c.conname            AS constraint_name,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
        FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum) AS columns
FROM pg_constraint c
WHERE c.contype = 'f'
  AND NOT EXISTS (
      SELECT 1 FROM pg_index i
      WHERE i.indrelid = c.conrelid
        AND i.indisvalid
        AND i.indpred IS NULL                                 -- partial indexes do not count
        AND (i.indkey::smallint[])[0:cardinality(c.conkey)-1] = c.conkey
  )
ORDER BY 1;
```

The prefix comparison matters: an index only supports the constraint if the constrained
columns are its **leading** columns in the same order. Simpler variants that test membership
with `= ANY(indkey)` report false negatives on composite keys.

## Cache behaviour

```sql
SELECT relname,
       heap_blks_hit, heap_blks_read,
       round(100.0 * heap_blks_hit / nullif(heap_blks_hit + heap_blks_read, 0), 2) AS hit_pct
FROM pg_statio_user_tables
ORDER BY heap_blks_read DESC
LIMIT 20;
```

A hit rate below ~99% on an OLTP table is worth explaining, but the explanation is often "a
sequential scan pulled the whole table through the cache", in which case the fix is the index
or the query — not more `shared_buffers`. Establish which before proposing memory.

With `pg_buffercache` installed you can see what is actually resident:

```sql
SELECT c.relname, count(*) AS buffers,
       pg_size_pretty(count(*) * 8192) AS size
FROM pg_buffercache b
JOIN pg_class c ON c.relfilenode = b.relfilenode
GROUP BY c.relname ORDER BY buffers DESC LIMIT 20;
```

## I/O by backend type

`pg_stat_io` (PG 16+) separates client backends from autovacuum and background writers, which
is how you tell "the application is reading from disk" from "autovacuum is":

```sql
SELECT backend_type, object, context, reads, writes, extends, evictions
FROM pg_stat_io
WHERE reads > 0 OR writes > 0
ORDER BY reads DESC;
```

High `evictions` in the `normal` context means the working set does not fit in
`shared_buffers`. High `writes` under `vacuum` means autovacuum is doing real work, not that
it is broken.

## Vacuum and bloat

```sql
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       n_mod_since_analyze, last_autovacuum, last_autoanalyze,
       total_vacuum_time, total_autovacuum_time         -- PG 18+
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;
```

A vacuum in progress:

```sql
SELECT p.pid, c.relname, p.phase, p.heap_blks_scanned, p.heap_blks_total
FROM pg_stat_progress_vacuum p JOIN pg_class c ON c.oid = p.relid;
```

Wraparound headroom:

```sql
SELECT datname, age(datfrozenxid) AS xid_age FROM pg_database ORDER BY 2 DESC;
```

Tuning and the `VACUUM FULL` decision are in `transactions-and-locks.md`.

## Replication

```sql
SELECT application_name, state, sync_state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)   AS pending_bytes,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes,
       replay_lag
FROM pg_stat_replication;

-- slots holding WAL, including inactive ones that will fill the disk
SELECT slot_name, plugin, active, wal_status,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;
```

An **inactive replication slot is a disk-space incident waiting to happen**: the primary
retains WAL for a consumer that is gone. `wal_status` of `extended` or `lost` is the warning.
Watch both of these during any large backfill.

## Settings and their sources

```sql
SELECT name, setting, unit, source, sourcefile, pending_restart
FROM pg_settings
WHERE source NOT IN ('default', 'override')
ORDER BY name;
```

`source` tells you whether a value came from `postgresql.conf`, `ALTER SYSTEM`,
`ALTER DATABASE`, `ALTER ROLE` or the session — which is the difference between "I changed
it" and "I changed it somewhere that does not apply here". `pending_restart` catches the
`max_connections` and `shared_buffers` class of change that silently does nothing until a
restart.

## Backup and restore basics

`pg_dump` is a logical, per-database dump. Use the custom format so `pg_restore` can
parallelise and select objects:

```bash
pg_dump -Fc -d mydb -f mydb.dump
pg_restore -d mydb_restored -j 4 mydb.dump
createdb -T template_db copy_db          # fast local copy, requires no active sessions
```

A logical dump is a consistent snapshot of one database and is the right tool for moving
between major versions or extracting a subset. It is **not** a point-in-time recovery
strategy: restoring it loses everything since the dump, and on a large database the restore
time is measured in hours because every index is rebuilt.

Real PITR is a base backup (`pg_basebackup`) plus continuous WAL archiving, restored with a
recovery target. On managed hosting the provider supplies this and the provider's mechanism
is the one to use — that control plane is outside this skill's scope, so name it rather than
improvising commands.

Whatever the mechanism: the backup is not a backup until a restore has been performed and
timed. Record the restore duration, because it is the number every migration rollback plan
depends on.

<!-- sources: postgresql-docs, neon-postgres-skills, supabase-postgres-bp, microsoft-postgres-skills, timescale-pg-aiguide, google-cloud-sql -->
