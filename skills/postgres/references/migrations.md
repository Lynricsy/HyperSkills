# Online schema migrations

Verified against: PostgreSQL 18.6

## Contents

- The two questions to ask about every statement
- Lock and rewrite matrix
- Transaction batching and lock queues
- Adding a column
- Making a column NOT NULL
- Changing a column's type
- Adding indexes and unique constraints
- Adding foreign keys and checks
- Dropping and renaming
- Batched backfills
- Rollback planning
- Rehearsal

## The two questions to ask about every statement

1. **Which lock does it take, and does it wait?** `ACCESS EXCLUSIVE` blocks readers as well
   as writers. Even an instant catalogue update has to wait for every in-flight transaction
   on the table to finish first — and while it waits, every new query queues behind it. A
   statement that takes 2 ms can still cause a five-minute outage if a reporting query is
   holding the table.
2. **Does it rewrite the table?** A rewrite is O(table) plus O(all indexes) and holds its lock
   for the duration.

Everything below follows from those two.

## Lock and rewrite matrix

Lock levels below were read from `pg_locks` on 18.6 during the statement.

| Statement | Lock | Rewrite | Notes |
|---|---|---|---|
| `ADD COLUMN` (no default, or non-volatile default) | `ACCESS EXCLUSIVE` | no | Catalogue only; brief but still queues |
| `ADD COLUMN ... DEFAULT <volatile>` | `ACCESS EXCLUSIVE` | **yes** | `gen_random_uuid()`, `clock_timestamp()`, `random()` |
| `DROP COLUMN` | `ACCESS EXCLUSIVE` | no | Column marked dropped; bytes stay until rows are rewritten |
| `RENAME COLUMN` / `RENAME TABLE` | `ACCESS EXCLUSIVE` | no | Breaks every dependent view, function and client |
| `SET DEFAULT` / `DROP DEFAULT` | `ACCESS EXCLUSIVE` | no | |
| `ALTER COLUMN TYPE` (most) | `ACCESS EXCLUSIVE` | **yes** | Including `integer` → `bigint` |
| `ALTER COLUMN TYPE` (`varchar(n)`→`text`, widening `varchar`/`numeric`) | `ACCESS EXCLUSIVE` | no | Binary-coercible only |
| `SET NOT NULL` (bare) | `ACCESS EXCLUSIVE` | no, but full scan | Blocks reads for the scan |
| `ADD CONSTRAINT ... CHECK ... NOT VALID` | `ACCESS EXCLUSIVE` | no | Brief — it does not scan |
| `ADD CONSTRAINT ... CHECK` (validated) | `ACCESS EXCLUSIVE` | no, but full scan | |
| `ADD CONSTRAINT ... FOREIGN KEY ... NOT VALID` | `SHARE ROW EXCLUSIVE` on **both** tables | no | Blocks writes, not reads |
| `ADD CONSTRAINT ... FOREIGN KEY` (validated) | `SHARE ROW EXCLUSIVE` on both | no, but full scan | |
| `VALIDATE CONSTRAINT` | `SHARE UPDATE EXCLUSIVE` | no, but full scan | Concurrent reads *and* writes allowed |
| `CREATE INDEX` | `SHARE` | n/a | Blocks writes for the whole build |
| `CREATE INDEX CONCURRENTLY` | `SHARE UPDATE EXCLUSIVE` | n/a | Reads and writes allowed; cannot be in a transaction |
| `CREATE TRIGGER` | `SHARE ROW EXCLUSIVE` | no | |
| `CLUSTER`, `VACUUM FULL` | `ACCESS EXCLUSIVE` | **yes** | Not maintenance; a rewrite with an outage |

`SHARE UPDATE EXCLUSIVE` also conflicts with autovacuum. A `VALIDATE CONSTRAINT` can end up
waiting behind an anti-wraparound autovacuum — do not cancel that autovacuum to unblock the
migration; wait for it.

## Transaction batching and lock queues

Migration tools default to wrapping the whole file in one transaction. Every lock taken
inside is held until `COMMIT`, so a file that ends with a slow backfill holds the
`ACCESS EXCLUSIVE` from its first `ALTER TABLE` for the entire run. On a live table, split
the file so each statement commits on its own and accept that the migration is no longer
atomic — that is the price of not taking the table down.

Bound the wait, and retry rather than queue:

```sql
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN tracking_number text;
-- on ERROR 55P03 lock_not_available: sleep, retry
```

Two defensible policies: a short timeout (50–100 ms) with many retries, which never queues
noticeably but may take many attempts on a busy table; or a few seconds with a handful of
retries, which is simpler and fine at moderate write rates. The higher the write throughput,
the shorter the timeout should be. Do the retry loop in the deploy tool rather than a
PL/pgSQL `EXCEPTION` block — each `EXCEPTION` block is a subtransaction, and thousands of
them create their own contention.

`LOCK TABLE orders IN ACCESS EXCLUSIVE MODE NOWAIT;` is the zero-queue variant: it fails
immediately rather than entering the lock queue at all.

Do not use `statement_timeout` as the safety net for DDL. It cannot distinguish waiting for a
lock from doing useful work, so it will happily kill a `CREATE INDEX CONCURRENTLY` at 95%.

## Adding a column

```sql
-- catalogue only, whatever the table size
ALTER TABLE orders ADD COLUMN tracking_number text;
ALTER TABLE orders ADD COLUMN priority integer NOT NULL DEFAULT 0;
ALTER TABLE orders ADD COLUMN billed_at timestamptz NOT NULL DEFAULT now();
```

`now()` is `STABLE`, so the third statement stores one value in the catalogue and does not
touch the heap — measured by `pg_class.relfilenode` staying the same. Guidance that lists
`DEFAULT now()` as a rewrite is wrong; what rewrites is a **volatile** default:

```sql
-- rewrites the table and every index
ALTER TABLE orders ADD COLUMN public_ref uuid NOT NULL DEFAULT gen_random_uuid();
```

Check rather than guess:

```sql
SELECT proname, provolatile   -- i = immutable, s = stable, v = volatile
FROM pg_proc WHERE proname IN ('now', 'clock_timestamp', 'gen_random_uuid', 'uuidv7');
```

The safe form for a volatile default on a large table is: add the column nullable, backfill in
batches, then `SET DEFAULT`, then add the `NOT NULL` constraint as below.

## Making a column NOT NULL

A bare `SET NOT NULL` scans the whole table under `ACCESS EXCLUSIVE`. On PG 18, not-null
constraints are first-class catalogue entries, so they can be added unvalidated:

```sql
-- PG 18+
ALTER TABLE orders ADD CONSTRAINT orders_currency_nn NOT NULL currency NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_currency_nn;
```

After the first statement `pg_attribute.attnotnull` is already true — new and updated rows are
rejected immediately — while `pg_constraint.convalidated` stays false until the second
statement finishes its concurrent-friendly scan.

Note that the syntax is `ADD CONSTRAINT <name> NOT NULL <column> NOT VALID`. The forms
`ALTER COLUMN ... SET NOT NULL NOT VALID` and `VALIDATE NOT NULL ON <column>` appear in some
guides and are syntax errors on 18.6.

On 12–17 the equivalent is to let a validated `CHECK` do the proving:

```sql
ALTER TABLE orders ADD CONSTRAINT orders_currency_nn
  CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_currency_nn;
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;   -- skips its scan
ALTER TABLE orders DROP CONSTRAINT orders_currency_nn;
```

## Changing a column's type

Most type changes rewrite. `integer` → `bigint` does; `varchar(n)` → `text` and widening a
`varchar`/`numeric` do not, because the new type is binary-coercible from the old. When in
doubt, test on a copy and compare `pg_class.relfilenode` before and after.

The non-blocking pattern is add, backfill, swap:

```sql
ALTER TABLE orders ADD COLUMN amount_cents_new bigint;
-- backfill in batches (below), plus a trigger or dual-write so new rows stay in sync
ALTER TABLE orders ALTER COLUMN amount_cents_new SET DEFAULT 0;
-- then, in one short transaction:
BEGIN;
  ALTER TABLE orders DROP COLUMN amount_cents;
  ALTER TABLE orders RENAME COLUMN amount_cents_new TO amount_cents;
COMMIT;
```

The swap still needs `ACCESS EXCLUSIVE`, but only for a catalogue update, so it fits inside a
short `lock_timeout`.

## Adding indexes and unique constraints

Concurrent index creation is covered in `indexing.md`; the migration-specific points are that
it cannot be inside a transaction block and that a failed build leaves an invalid index.

For a unique constraint without a long lock, build the index first and adopt it:

```sql
CREATE UNIQUE INDEX CONCURRENTLY orders_public_ref_key ON orders (public_ref);
ALTER TABLE orders ADD CONSTRAINT orders_public_ref_key
  UNIQUE USING INDEX orders_public_ref_key;      -- instant, reuses the index
```

The same trick promotes an index to a primary key, which additionally needs the columns to be
provably `NOT NULL` first — do that with the `NOT VALID` constraint pattern above so the
`ADD CONSTRAINT ... PRIMARY KEY USING INDEX` step stays instant.

## Adding foreign keys and checks

```sql
ALTER TABLE orders ADD CONSTRAINT orders_customer_fk
  FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;   -- no scan
ALTER TABLE orders VALIDATE CONSTRAINT orders_customer_fk;         -- concurrent-friendly
```

Adding the constraint locks `customers` as well as `orders`, at `SHARE ROW EXCLUSIVE`. And
Postgres indexes the referenced column automatically but never the referencing one, so pair
every new foreign key with `CREATE INDEX CONCURRENTLY ON orders (customer_id)` — otherwise
each delete or key update on `customers` scans `orders`.

Postgres has no `ADD CONSTRAINT IF NOT EXISTS`. For an idempotent migration, test the
catalogue:

```sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'orders_customer_fk') THEN
    ALTER TABLE orders ADD CONSTRAINT orders_customer_fk
      FOREIGN KEY (customer_id) REFERENCES customers (id) NOT VALID;
  END IF;
END $$;
```

## Dropping and renaming

`DROP COLUMN` is a catalogue update: the column is marked dropped and the bytes stay in every
existing row until those rows are rewritten. Two consequences. Space is not returned until
`VACUUM FULL` or a natural rewrite, and the values are still recoverable from the heap — for
sensitive data, rewrite the table or dump and restore.

`RENAME COLUMN` is instant and breaks every view, function and client that names the column.
For a zero-downtime rename, use the same add/dual-write/backfill/switch/drop sequence as a
type change. Drop dependent constraints before dropping the column they reference, or the
`ALTER TABLE` fails on the dependency.

## Batched backfills

One `UPDATE` over a large table is the single most common way to take a database down: it
writes a new version of every row, floods WAL and any replicas, roughly doubles the table's
on-disk size with dead tuples, and cannot be interrupted without losing all of it.

```sql
-- driven from the application, one transaction per batch
UPDATE orders
SET    currency = 'USD'
WHERE  id IN (SELECT id FROM orders
              WHERE currency IS NULL
              ORDER BY id
              LIMIT 10000
              FOR UPDATE SKIP LOCKED);
```

Batch by primary key, keep each batch small enough to finish inside a second or two, sleep
between batches so autovacuum can keep up, and watch replication lag while it runs:

```sql
SELECT application_name, state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;
```

If the backfill is racing live writes, add a trigger or dual-write in the application so new
rows land correct, and make the batch predicate `WHERE new_col IS NULL` so it converges.

## Rollback planning

Write the down path before running the up path, and name the statements that have none:
`DROP COLUMN`, `TRUNCATE`, `DELETE`, `DROP TABLE`, and any lossy `ALTER COLUMN TYPE`. For
those, the rollback is a restore, which means the real prerequisite is a verified backup and a
known restore time.

Reversible steps to prefer while a change is in flight: add the new column rather than
changing the old one; keep dual writes until the read path has been switched and observed;
drop the old column in a later, separate deploy.

## Rehearsal

Restore a copy of production and run the exact sequence against it. That catches constraint
violations, cast failures and duration. It does **not** catch lock contention, deadlocks or
replication lag, because those need concurrent load — so for the locking questions, reason
from the matrix above and keep the `lock_timeout` short.

`BEGIN; ALTER TABLE ...; ROLLBACK;` is a legitimate rehearsal on the real server for anything
that does not rewrite: DDL in Postgres is transactional, so the statement's lock level and
error behaviour can be observed without keeping the change.

<!-- sources: postgresql-docs, timescale-pg-aiguide, neon-postgres-skills, supabase-postgres-bp, microsoft-postgres-skills -->
