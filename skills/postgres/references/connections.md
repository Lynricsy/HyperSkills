# Connections, pooling and ORM side effects

Verified against: PostgreSQL 18.6, PgBouncer 1.21+

## Contents

- What a connection costs
- Sizing
- Pool modes and what each breaks
- Prepared statements across a pooler
- The errors that never mention pooling
- Direct connections are still required for some work
- Timeouts that reclaim slots
- What ORMs do to the database

## What a connection costs

Every connection is a separate backend process. Baseline memory is single-digit megabytes,
but a backend running a complex query allocates `work_mem` per sort or hash operation per
parallel worker on top of that, so the realistic figure under load is tens of megabytes.
Beyond a few hundred active backends, context switching and lock-manager contention cost
more than the extra concurrency buys.

Defaults on 18.6: `max_connections = 100`, `shared_buffers = 128MB`, `work_mem = 4MB`.
`max_connections` is a postmaster-scope setting — `ALTER SYSTEM SET` it and nothing happens
until a restart.

```sql
SELECT count(*) FILTER (WHERE state = 'active')              AS active,
       count(*) FILTER (WHERE state = 'idle')                AS idle,
       count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn,
       count(*)                                              AS total,
       current_setting('max_connections')::int               AS max_conn
FROM pg_stat_activity WHERE backend_type = 'client backend';
```

`idle in transaction` is the number to react to: those sessions hold locks and block vacuum,
so they cost far more than a slot.

## Sizing

Two numbers, in this order:

1. **Server-side ceiling.** Total *active* connections beyond roughly four times the
   database's CPU count adds contention, not throughput. That is the number the pool exists
   to hold down.
2. **Client-side total.** The real load is `pool_size_per_instance × instances`, not the
   per-instance number that appears in the config file. Ten instances with a pool of 20 is
   200 connections.

When PgBouncer sits in front, the application pool and the pooler multiply — so **shrink the
application pool when you add a pooler**, otherwise you have added a hop and no reduction.
Serverless runtimes are the extreme case: one connection per invocation with no pool at all
is what exhausts `max_connections`, and a pooler is mandatory rather than an optimisation.

## Pool modes and what each breaks

| Mode | Server connection held for | Use when |
|---|---|---|
| `session` | the whole client session | `LISTEN`/`NOTIFY`, session advisory locks, cross-transaction temp tables, `SET` that must persist |
| `transaction` | one transaction | the default for web applications and APIs |
| `statement` | one statement | autocommit-only workloads; multi-statement transactions are rejected |

Transaction mode is the default recommendation because it is where the multiplexing gain is.
What it breaks, all of it session state that silently moves to another backend:

- SQL-level `PREPARE` / `EXECUTE` / `DEALLOCATE`
- session `SET` / `RESET` — use `SET LOCAL` inside the transaction
- `LISTEN` / `NOTIFY`
- session advisory locks (`pg_advisory_lock`) — use `pg_advisory_xact_lock`
- temporary tables that must outlive the transaction
- `WITH HOLD` cursors

Configure the pooler to scrub state between clients, or one client inherits another's:

```ini
pool_mode = transaction
server_reset_query = DEALLOCATE ALL; DISCARD ALL; RESET ALL;
max_client_conn = 1000
default_pool_size = 20            ; ≈ 2-4x database CPU cores
max_db_connections = 50           ; hard cap per database
max_prepared_statements = 100     ; PgBouncer 1.21+; see below
server_idle_timeout = 60
query_wait_timeout = 120
```

## Prepared statements across a pooler

Most drivers use **protocol-level** prepared statements (the `Parse`/`Bind`/`Execute`
messages), not SQL `PREPARE`. PgBouncer 1.21+ tracks those per server connection and
re-prepares transparently when `max_prepared_statements` is non-zero. That is the fix:
set it, and leave the driver alone.

The alternatives are worse and appear in older guidance: turning off prepare in the driver
(`prepare: false` in node-postgres, `prepareThreshold=0` in JDBC, which otherwise promotes a
statement after five executions) gives up plan reuse everywhere to work around one hop;
switching the whole application to session mode gives up the multiplexing that justified the
pooler. Keep both as escape hatches, not defaults.

SQL-level `PREPARE` never works in transaction mode. There is no configuration for that.

## The errors that never mention pooling

Every one of these is "you are on a transaction-mode pooler and something assumed a session":

| Error | Cause |
|---|---|
| `prepared statement "s0" already exists` / `... does not exist` | The driver's statement cache disagrees with the backend it landed on |
| `relation "mytable" does not exist` right after a successful `SET search_path` | The `SET` applied to a backend the next query did not get |
| `cannot execute UPDATE in a read-only transaction` (`SQLSTATE 25006`) | The backend inherited `default_transaction_read_only` from a previous client — missing `server_reset_query` |
| An advisory lock that is never held, or never released | Session-scoped lock on a rotating backend |
| `LISTEN` never fires | Same |

When one of these appears intermittently and only in production, check the pool mode before
reading the application code.

## Direct connections are still required for some work

Route these past the pooler, to the database's own port:

- schema migrations (they use session state, sometimes advisory locks, and must not be
  interrupted mid-transaction by a pool reset)
- `pg_dump` / `pg_restore`
- logical replication and CDC
- `LISTEN` / `NOTIFY` consumers
- long analytical sessions using temporary tables

Most migration tools accept a second URL for exactly this. Keep the pooled URL as the
application's default and pass the direct one to the tool, rather than switching the
application to direct and losing pooling.

## Timeouts that reclaim slots

```sql
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';  -- kills lock/vacuum blockers
ALTER SYSTEM SET idle_session_timeout = '10min';               -- PG 14+, idle outside a txn
ALTER SYSTEM SET statement_timeout = '30s';                    -- per statement, not per connection
```

`statement_timeout` is a per-statement budget and does nothing about a connection storm; set
it per role or per transaction rather than globally, and never on a session that is going to
run `CREATE INDEX CONCURRENTLY` or `VALIDATE CONSTRAINT`.

The emergency reap, when the pool is exhausted and something has to give:

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '10 minutes';
```

Prefer `pg_cancel_backend` (cancels the statement) over `pg_terminate_backend` (kills the
connection) when the goal is just to unblock, and never target `pg_backend_pid()`.

## What ORMs do to the database

The ORM's own API is out of scope here; these are the four things ORMs do that show up as
database problems.

**Connection per request.** A framework that opens a connection per HTTP request and 500
concurrent users is 500 backends. This is the most common `FATAL: sorry, too many clients
already` in existence. The fix is a pool in the application plus, at scale, a pooler.

**Prepared statements under a pooler.** Any ORM layer that names its prepared statements —
Drizzle's `.prepare()`, some Prisma paths, JDBC after its fifth execution — hits the
transaction-mode failure above. Configure `max_prepared_statements` on the pooler rather
than pushing `prepare: false` into every call site.

**N+1.** A lazily-loaded relation inside a loop is one round trip per row, and the database
sees N trivially fast queries while the endpoint takes seconds. The signature is a high
`calls` count with a low `mean_exec_time` in `pg_stat_statements`. Collapse it to one
statement:

```sql
SELECT * FROM order_items WHERE order_id = ANY($1::bigint[]);
```

**Schema push against a live database.** Tools with a "sync the schema to match the models"
mode (`drizzle-kit push`, `prisma db push`) generate and apply DDL directly, bypassing the
reviewed migration file, with no control over lock levels — and they will happily emit a
table rewrite. Use them on development databases only; production changes go through
generated migration files reviewed against `migrations.md`.

Two smaller ones worth checking in any ORM configuration: it should emit unquoted snake_case
identifiers rather than quoted `"camelCase"`, and its connection URL must be
percent-encoded — a `#` or `@` in a password produces a connection error that names the
wrong host.

<!-- sources: postgresql-docs, neon-postgres-skills, neon-agent-skills, microsoft-postgres-skills, supabase-postgres-bp, drizzle-best-practices, prisma-skills -->
