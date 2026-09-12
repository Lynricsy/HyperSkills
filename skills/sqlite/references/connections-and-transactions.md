# Connections and transactions

Verified against: SQLite 3.53.0 transaction and isolation documentation.

## Contents

- Connection ownership
- Select the smallest atomic unit
- Recover by phase and extended result code
- Stale-snapshot retry protocol

## Connection ownership

[official] Keep one logical transaction on one connection. SQLite serializing
calls does not prevent two coroutines from mixing statements inside the same
transaction. Lease the connection for the whole unit of work or serialize whole
units, not individual statements. Do not infer a thread change or connection
change merely from an `await`; inspect the binding's actual ownership model.

Read the application's runtime identity, not just `sqlite3 --version`:

```sql
SELECT sqlite_version(), sqlite_source_id();
PRAGMA database_list;
PRAGMA journal_mode;
PRAGMA foreign_keys;
PRAGMA synchronous;
PRAGMA busy_timeout;
```

Use existing connection instrumentation for transaction state; where available,
`sqlite3_get_autocommit()` and `sqlite3_txn_state()` expose engine state. A host's
"autocommit" option can mean something different from the engine state.

For each fresh connection, before beginning work:

1. Enable `PRAGMA foreign_keys=ON` and require the readback to be `1`.
2. Install the application's bounded busy handler or timeout. Installing a
   timeout replaces the existing busy handler; do not accidentally discard one.
3. Set the chosen connection-local synchronous policy and read it back.
4. Leave file-wide WAL switching to coordinated bootstrap, outside transactions.
5. Establish who rolls back and who closes on every exceptional exit.

A connection context manager is not proof of close. Inspect the binding contract.
Finish result cursors, reset/finalize statements and close incremental BLOB
handles promptly. In an implicit transaction, the last unfinished statement can
retain transaction state. In an explicit transaction, finishing statements does
not substitute for COMMIT or ROLLBACK.

## Select the smallest atomic unit

[community, official] Prefer `UPDATE counters SET value=value+1 WHERE key=?`
over a read/compute/write sequence. Put an eligibility predicate in the update
and inspect the affected-row result when the transition fits one statement.

For a decision across multiple rows, acquire write ownership with
`BEGIN IMMEDIATE` before the reads, keep database work short, then commit.
Perform network calls, user interaction and slow computation outside this window.
Do not add `SELECT ... FOR UPDATE`: SQLite does not offer that row-locking syntax.

- `BEGIN` is deferred. The first read establishes a read transaction; a later
  write may fail to upgrade it.
- `BEGIN IMMEDIATE` requests write ownership immediately and can itself be busy.
- `BEGIN EXCLUSIVE` is equivalent to IMMEDIATE in WAL; in rollback modes it also
  excludes other readers. It is not a stronger WAL consistency setting.
- Nested units use SAVEPOINT, not another BEGIN. Releasing an inner savepoint
  does not durably commit the enclosing transaction.

Do not scan a table and mutate it on the same connection while assuming later
cursor rows form an unchanged snapshot; visibility during that scan is undefined.
Use a set-based statement or finish the read before mutation when that matters.

## Recover by phase and extended result code

[official] Preserve the extended code, not merely the text "database is locked".
A binding may expose only the primary BUSY code unless configured otherwise.

| Observable state | Recovery boundary |
|---|---|
| BUSY acquiring write ownership before reads | Wait/back off within a deadline, then retry acquisition; no prior database decision to preserve |
| BUSY upgrading a deferred read, or BUSY_SNAPSHOT after a competing WAL commit | End the outer transaction, discard derived decisions, acquire a fresh transaction and read again |
| BUSY at COMMIT because another reader blocks rollback-mode commit | Transaction remains active; finish pending local writes and retry COMMIT within a bound, or explicitly roll back; do not replay its writes while it remains active |
| LOCKED or LOCKED_SHAREDCACHE | Find a conflicting statement/shared-cache use; a larger busy timeout is not a general remedy |
| Constraint failure | Report violated data/contract; retrying unchanged data is not recovery |
| IOERR, FULL, NOMEM or interruption | Inspect whether SQLite rolled back; normalize cleanup without hiding the original error and address the underlying condition |

A busy handler need not be invoked when waiting would deadlock. Its timeout is
not a guarantee that every lock failure waits that long. Capture the phase and
connection owners instead of concluding that an immediate error is a broken timer.

## Stale-snapshot retry protocol

Use this conditional sequence when the application permits transaction replay:

1. On a stale snapshot or failed read-to-write upgrade, finalize dependent
   statements and roll back the enclosing transaction, not only a savepoint.
2. Discard cached reads, totals and eligibility decisions from that transaction.
3. If the operation's deadline/attempt allowance is exhausted, return contention
   without reporting success. Avoid nested driver and application retry loops.
4. Begin a fresh transaction, preferably IMMEDIATE for a known write decision,
   and re-read all data on which the decision depends.
5. Apply only the newly justified mutation; a competing commit may mean refusal
   is now the correct result. Commit before acknowledging success.

A retry callback contains database work only. Do not repeat a competing writer,
a charge or a sent notification just because the database transaction restarted.
Where the request's outcome is ambiguous, reconcile its stable operation identity
before replay. If external delivery is part of the contract, use the project's
existing durable delivery/idempotency design rather than treating COMMIT as a
transaction spanning external systems.

<!-- sources: terminalskills-sqlite, harness-sqlite, openfang-sqlite, sqlite-transactions, sqlite-isolation, sqlite-pragma, sqlite-busy-handler -->
