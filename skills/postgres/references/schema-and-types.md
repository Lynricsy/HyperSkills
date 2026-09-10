# Schema and data types

Verified against: PostgreSQL 18.6

## Contents

- Types: the short list of decisions
- Types to avoid and what to use instead
- Keys and identity
- Identifiers and case folding
- Constraints beyond NOT NULL
- Enums versus lookup tables
- Arrays and semi-structured data
- Generated columns
- Storage: TOAST, fillfactor and HOT
- Partitioning

## Types: the short list of decisions

| Need | Use | Not |
|---|---|---|
| A point in time | `timestamptz` | `timestamp`, `timetz` |
| A calendar date with no time | `date` | a `timestamptz` at midnight |
| Text | `text`, plus `CHECK (length(col) <= n)` if a limit is real | `varchar(n)`, `char(n)` |
| Money | `numeric(12, 2)` | `float`, `real`, `money` |
| Surrogate key | `bigint generated always as identity`, or `uuid` with `uuidv7()` (PG 18+) | `serial`, `bigserial` |
| Boolean-ish state | `boolean`, or `text` + `CHECK` for more than two states | integer flags |
| An interval of time | `tstzrange` with an `EXCLUDE` constraint where overlaps matter | two nullable columns |

`timestamptz` does not store a timezone. It stores an absolute instant and renders it in the
session's `TimeZone`; `timestamp` stores wall-clock digits with no instant attached, which is
almost never what an application means. Do not add a precision specifier
(`timestamptz(0)`) — it silently rounds, and rounding *up* can move an event into the next
second.

`varchar(n)` and `text` have identical performance in Postgres; the only difference is that
changing `n` later is a schema migration while changing a `CHECK` is not (and widening
`varchar(n)` happens to be one of the few non-rewriting type changes). `char(n)` pads with
spaces and has no upside.

Postgres does not silently coerce on overflow the way some engines do: inserting `999` into
`numeric(2,0)` raises an error rather than truncating. Rely on that.

## Types to avoid and what to use instead

- `serial` / `bigserial` — a macro that creates a sequence whose ownership and privileges are
  easy to desynchronise from the column. `generated always as identity` is SQL-standard, and
  `always` also blocks an application from writing the column by accident.
- `money` — locale-dependent and fixed-precision in the wrong way.
- `char(n)` — blank-padded comparison surprises.
- The built-in geometric types (`point`, `line`, `polygon`, `circle`) — no projections, no
  geography, no serious indexing story. If real spatial work is needed, that is PostGIS
  territory, which this skill does not cover.
- Nothing wrong with `uuid` as a key, but random UUIDv4 primary keys fragment B-tree inserts
  across the whole index. `uuidv7()` (PG 18+) is time-ordered and does not, and on older
  servers a `bigint` identity is the low-friction choice.

Sequence and identity gaps are normal: a rolled-back transaction, a crash, or caching in a
concurrent session all consume values. Do not build anything that assumes contiguity, and do
not "repair" them.

## Keys and identity

```sql
CREATE TABLE orders (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    public_ref  uuid   NOT NULL DEFAULT uuidv7(),   -- PG 18+
    customer_id bigint NOT NULL REFERENCES customers (id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (public_ref)
);
CREATE INDEX orders_customer_id ON orders (customer_id);
```

Two things that are easy to forget. Postgres indexes the **referenced** side of a foreign key
automatically (it must be unique) and never the **referencing** side, so every child table
needs its own index on the FK column or deletes on the parent scan the child. And an
externally visible identifier is a separate column from the primary key — exposing a
sequential `id` leaks volume and invites enumeration.

Postgres tables are heaps: there is no clustered index, and physical order is not maintained.
`CLUSTER` reorders once, takes `ACCESS EXCLUSIVE`, and decays immediately afterwards.

## Identifiers and case folding

Unquoted identifiers fold to lower case; quoted ones preserve it and must then be quoted
everywhere, forever. Use `snake_case` unquoted and configure the ORM to match. When a legacy
schema already has `"userId"`, a view is the cheap compatibility layer rather than a rename:

```sql
CREATE VIEW users AS
  SELECT "userId" AS user_id, "createdAt" AS created_at FROM "Users";
```

## Constraints beyond NOT NULL

```sql
-- three-valued logic: a CHECK passes on NULL
status text NOT NULL CHECK (status IN ('pending', 'shipped', 'cancelled'))

-- one NULL is distinct from another, so this permits duplicate (1, NULL) pairs
UNIQUE (tenant_id, external_id)
-- PG 15+: treat NULLs as equal
UNIQUE NULLS NOT DISTINCT (tenant_id, external_id)

-- no two bookings for one room may overlap
EXCLUDE USING gist (room_id WITH =, during WITH &&)

-- two tables that reference each other; defer until COMMIT
FOREIGN KEY (head_id) REFERENCES employees (id) DEFERRABLE INITIALLY DEFERRED
```

`EXCLUDE USING gist` needs `btree_gist` when a scalar column such as `room_id` participates.

A reusable validated type is a domain:

```sql
CREATE DOMAIN email AS text CHECK (VALUE ~ '^[^@[:space:]]+@[^@[:space:]]+$');
```

Postgres has no `ADD CONSTRAINT IF NOT EXISTS`; the idempotent form is a `DO` block checking
`pg_constraint` (see `migrations.md`).

## Enums versus lookup tables

`CREATE TYPE ... AS ENUM` is right for a small, genuinely stable set — weekdays, a two- or
three-state flag that is part of the domain model. It is wrong for business values that
evolve, because adding a value is a DDL statement, **removing** one is not supported at all,
and reordering requires recreating the type and every column that uses it.

For anything with a lifecycle — order status, subscription tier, feature flag — use `text`
with a `CHECK`, or a lookup table with a foreign key when the set needs its own attributes.

## Arrays and semi-structured data

SQL arrays are **1-indexed** (`tags[1]`, slice `tags[1:3]`); JSONB arrays are **0-indexed**
(`doc->'items'->0`). Both appear in the same query often enough for this to bite.

Use an array for a small, unordered bag with no attributes of its own — tags, permission
strings — indexed with GIN for `@>` and `&&`. Do not use one to model a relationship: no
foreign keys, no per-element constraints, no efficient join.

Choose JSONB when the shape is genuinely open or supplied by a third party. Anything you
filter, sort or join on is a column, not a key — see `jsonb-and-search.md` for promoting one
without abandoning the payload. Plain `json` is only for the rare case where key order and
whitespace must be preserved byte-for-byte.

## Generated columns

```sql
-- STORED: computed on write, occupies space, indexable
ALTER TABLE products
  ADD COLUMN price_cents bigint GENERATED ALWAYS AS ((payload->>'price')::bigint) STORED;

-- VIRTUAL (PG 18+): computed on read, no storage, not indexable
ALTER TABLE orders
  ADD COLUMN total_with_tax numeric GENERATED ALWAYS AS (total * 1.2) VIRTUAL;
```

`STORED` is the one that makes a JSONB scalar or a `tsvector` indexable. `VIRTUAL` is the
default in PG 18 when the keyword is omitted, so write the keyword you mean. The expression
must be immutable in both cases, so `now()` is not allowed.

## Storage: TOAST, fillfactor and HOT

Values over roughly 2 kB are compressed and moved out of line into the table's TOAST
relation. That is usually invisible, but it means a wide `text` or `jsonb` column is a second
lookup whenever it is actually selected — which is one more reason `SELECT *` costs more than
it looks on document-heavy tables. Per-column control:

```sql
ALTER TABLE docs ALTER COLUMN body SET STORAGE EXTERNAL;    -- out of line, uncompressed
ALTER TABLE docs SET (toast_tuple_target = 4096);           -- push out of line sooner
```

An `UPDATE` writes a whole new row version. If no **indexed** column changed and the new
version fits on the same page, Postgres uses a HOT update: no index entry is written and
cleanup is cheap. Two design consequences:

- Do not index columns that are updated constantly (a `last_seen_at` heartbeat, a counter)
  unless a query really needs it — measured here, 200k updates of a non-indexed column gave
  93334 HOT updates; adding an index on the updated column pushed the same workload onto new
  pages instead.
- Leave room on the page for the new version on update-heavy tables:
  `ALTER TABLE sessions SET (fillfactor = 90);` — it only affects pages written after the
  change, so pair it with a rewrite if the table already exists.

Splitting a hot, narrow, frequently-updated set of columns out of a wide, cold table is the
structural version of the same fix.

## Partitioning

Declarative partitioning (never table inheritance) pays off when a table is heading past
~100M rows, or — more often the real reason — when maintenance is bulk removal by time, where
`DROP TABLE events_2025_01` replaces a `DELETE` that would run for hours and leave the space
behind.

```sql
CREATE TABLE events (
    id         bigint GENERATED ALWAYS AS IDENTITY,
    tenant_id  bigint NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (id, created_at)          -- must contain the partition key
) PARTITION BY RANGE (created_at);
```

The rules that shape the design:

- Every `UNIQUE` or `PRIMARY KEY` must include all partition-key columns, because uniqueness
  is only enforced per partition. Decide the partition key before the primary key.
- Partition pruning needs the partition key in the `WHERE` clause. A query that filters only
  on `tenant_id` touches every partition.
- Foreign keys **from** a partitioned table work (PG 12+); indexes are per-partition, with a
  parent index acting as a template — see `indexing.md` for the concurrent build recipe.
- `DETACH PARTITION CONCURRENTLY` (PG 14+) avoids the exclusive lock when retiring one.
- On PG 18, `VACUUM t` and `ANALYZE t` recurse into partitions by default; `VACUUM ONLY t`
  restores the old parent-only behaviour.

Do not partition a table that is merely large-ish. Every query pays planning cost across
partitions, and the constraints above are permanent.

<!-- sources: postgresql-docs, timescale-pg-aiguide, supabase-postgres-bp, neon-postgres-skills, microsoft-postgres-skills, awesome-copilot-pg, wshobson-table-design -->
