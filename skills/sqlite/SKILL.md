---
name: sqlite
description: "Designs and operates embedded SQLite databases, transactions, WAL and backups."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# sqlite

Paths below are relative to this skill's directory.

## Scope

Embedded SQLite's SQL semantics and database-file lifecycle: application-owned
connections, concurrency, durable state, constraints, migrations and query plans.
Keep the project's binding and migration runner; express the engine contract
without introducing another wrapper or requiring a particular host language.

Not covered:

- Cloudflare D1 bindings, Wrangler targets or remote migrations: use `cloudflare`.
- Turso's engine extensions, replication and hosted service: use its own docs;
  sharing SQL syntax does not establish SQLite's file or locking semantics.
- ORM transaction decorators, pool APIs or language-level resource management:
  use the applicable framework or language skill for those interfaces.
- PostgreSQL administration: use `postgres`. Analysis methodology belongs to
  `data-analysis`, not to a database repair procedure.

## Core rules

1. Inspect `sqlite_version()` and `sqlite_source_id()` on the application's actual connection; a system CLI can link a different engine.
2. Keep every transaction on one exclusively owned connection until commit or rollback; serialized individual calls do not isolate interleaved application transactions.
3. Finish cursors, statements and incremental BLOB handles explicitly; an unfinished operation can keep a transaction or WAL snapshot alive.
4. Treat WAL as concurrent readers plus one writer, not multiple writers; a larger write pool cannot increase simultaneous write ownership.
5. Use atomic conditional SQL for a one-statement state transition, or `BEGIN IMMEDIATE` before reads for a short multi-statement write decision; a process-local mutex cannot protect other processes.
6. Classify the extended error code and transaction phase before retrying; waiting for a lock cannot refresh an obsolete WAL snapshot.
7. On `SQLITE_BUSY_SNAPSHOT`, end the transaction and recompute from a new snapshot; replaying only the failed write preserves a stale decision.
8. Bound retry time and replay only database work whose effects are known; a transaction rollback cannot undo a sent message or completed external request.
9. Enable and read back foreign keys on every connection outside a transaction; an in-transaction PRAGMA change silently does nothing.
10. Separate persistent WAL configuration from connection-local enforcement and durability settings; copying PRAGMA recipes conceals which state survives reopen.
11. Preserve database recovery files and let SQLite manage them; deleting a WAL or hot journal can discard the only committed or recoverable state.
12. Back up a live database through SQLite, not sequential file copies; a structurally valid main file can still omit committed WAL data.
13. Choose durability from the acknowledged-commit contract; WAL with `synchronous=NORMAL` can lose commits after power loss even while retaining consistency.
14. Treat affinity as conversion preference, not validation; STRICT still allows lossless conversion and does not replace NOT NULL or domain checks.
15. Make NULL policy explicit for CHECK, UNIQUE and non-rowid primary keys; those constraints do not all imply rejection of NULL.
16. Rebuild schemas atomically with their dependencies and historical AUTOINCREMENT state; copying present rows alone does not preserve the database's contract.
17. Run foreign-key and integrity checks before committing a rebuild, and consume their results; executing a check does not make returned violations fatal.
18. Use native ALTER syntax supported by every deployed engine; SQLite 3.53.0 adds ALTER COLUMN SET/DROP NOT NULL, not arbitrary type alteration.
19. Compare query behavior and measured work, not just index presence; a scan can be optimal and EXPLAIN QUERY PLAN text is not a stable machine interface.
20. Reproduce destructive operations on an isolated representative copy; investigation permission is not permission to migrate, overwrite or stress a production file.

## Workflows

### diagnose-connection-or-locking

- [ ] Read `references/connections-and-transactions.md` before changing retry or
      connection ownership. Record the binding, engine/source ID, file path,
      journal mode, transaction state and extended error code.
- [ ] Draw the connection timeline: first read, competing commit, attempted
      write, commit and statement finalization. Include background workers,
      cursor consumers and backup/checkpoint connections.
- [ ] Separate an engine lock from application queueing. A blocked event loop,
      pool checkout and an open SQLite transaction need different fixes.
- [ ] Select the recovery boundary from the error and phase. For a stale
      snapshot, roll back the outer transaction and recompute; for writer
      acquisition, wait within the request deadline without holding old reads.
- [ ] Keep external effects outside the retry body. If a request may already
      have committed, resolve its identity instead of blindly replaying it.
- [ ] Exercise the same contention order on a scratch file through independent
      connections; do not change the schedule merely to make an error disappear.
- [ ] **Gate — recovered decision:** observe the final database invariant,
      latest committed competing state, bounded completion and no duplicated
      external effect, not merely absence of a lock exception.

### configure-embedded-storage

- [ ] Inventory every connection entry point, including imports and maintenance.
      Read `references/connections-and-transactions.md` for initialization and
      `references/wal-backup-and-recovery.md` before selecting WAL or durability.
- [ ] Establish the file identity and storage topology. Keep ordinary WAL access
      on one host with a supported local filesystem and locking/VFS behavior.
- [ ] Apply persistent journal configuration in a coordinated bootstrap step;
      inspect the returned mode. Do not race a mode switch on every request.
- [ ] Set connection-local foreign-key enforcement, busy policy and synchronous
      policy outside transactions; read back meaningful settings.
- [ ] Assign a transaction owner and deterministic release paths. Permit
      independent read connections without promising parallel writes.
- [ ] Identify the longest read and write transactions before changing checkpoint
      thresholds or adding a dedicated checkpoint worker.
- [ ] **Gate — reopened contract:** on a scratch database, reopen through each
      real connection path and demonstrate enforcement, expected journal mode
      and complete resource release. State the power-loss durability choice.

### backup-and-restore

- [ ] Read `references/wal-backup-and-recovery.md`. Identify source, destination,
      active writers, recovery files, restore isolation and required freshness.
- [ ] Create a new staging backup using the Online Backup API. Use `VACUUM INTO`
      instead only when a compact rewritten snapshot is the desired artifact.
- [ ] Require successful completion and resource closure before publishing the
      backup. Never publish a partial destination under the latest-backup name.
- [ ] Restore into a separate directory, away from the source's WAL and journals;
      open with a compatible engine and enable foreign keys on the restore reader.
- [ ] Check structural integrity, foreign keys and selected application facts
      known to be committed before the backup began. Document the snapshot's
      freshness boundary rather than promising the last concurrent write.
- [ ] **Gate — usable restore:** consume `PRAGMA integrity_check` and
      `PRAGMA foreign_key_check` results and query required records and schema
      version in the restored file. A lone `ok` does not prove completeness.

### change-schema-or-import

- [ ] Read `references/types-and-migrations.md` before issuing DDL or importing
      values. Record all supported engine versions and the target constraints.
- [ ] Inspect source values with `typeof()` and representative boundary queries;
      distinguish an accepted conversion from forbidden truncation or coercion.
- [ ] Choose a supported native ALTER when sufficient. For a rebuild, enumerate
      incoming foreign keys, indexes, triggers, views, generated columns, table
      options and historical identity state before dropping anything.
- [ ] Keep data copy, dependency recreation, checks and the existing migration
      version marker in one explicit transaction on a dedicated connection.
- [ ] If rebuilding a referenced table requires FK enforcement off, change it
      outside the transaction, restore it afterward on success and failure,
      and never publish with checks failing or enforcement accidentally disabled.
- [ ] Reject bad data with identifying evidence; do not hide it with `OR IGNORE`,
      `OR REPLACE`, casts or silent row deletion unless that policy is requested.
- [ ] **Gate — atomic consumer contract:** on a scratch copy, exercise valid and
      independently invalid writes, dependent views/triggers and identity issuance;
      on failure verify rows, schema, dependencies, sequence and version unchanged.

### tune-query

- [ ] Read `references/query-plans-and-indexes.md`. Capture SQL, bound value types,
      representative cardinalities, schema/index definitions and engine version.
- [ ] Inspect `EXPLAIN QUERY PLAN` for visited loops, search terms, covering access
      and temporary sorting. Time the query separately with equivalent results.
- [ ] Change the smallest relevant index or predicate; retain NULL, collation and
      ordering semantics. Include write and storage cost in the tradeoff.
- [ ] Refresh planner statistics according to the project's policy, then measure
      again with representative selective and unselective bindings.
- [ ] **Gate — useful plan change:** report equivalent results plus measured
      latency or visited work before/after. An index appearing in a plan alone
      does not establish an improvement.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Connection ownership, transaction phases, BUSY recovery | A connection leaks, a write races, or retry/transaction code changes | `references/connections-and-transactions.md` |
| WAL state, checkpoint progress, durability, consistent backup and restore | Selecting journal mode, seeing WAL growth, copying or recovering database files | `references/wal-backup-and-recovery.md` |
| Affinity, STRICT, FK/NULL policy, native ALTER and table rebuilds | Import accepts bad data, constraints change, or migration touches schema dependencies | `references/types-and-migrations.md` |
| Index shape, expression matching, planner statistics and observed work | A query slows down or an index/EXPLAIN plan is being changed | `references/query-plans-and-indexes.md` |

## Output format

For a review or incident report, use this sensible default; adapt to the task.
Group findings by file or connection entry point.

```text
path:line — observed defect and consumer-visible consequence
Engine: runtime version/source ID; journal mode; relevant connection settings
Evidence: error code + transaction phase, violated row, or measured query work
Before -> after: ownership, SQL or operation order being changed
Safety boundary: scratch/source/restore path; rollback and publication conditions
Verification: exact exercised case and resulting invariant; untested limits
```

For a migration or restore, also name the preserved schema objects, identity
state, version marker and the check results that permit publication. Distinguish
observed evidence from a proposed operational procedure.
