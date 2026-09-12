# Types, constraints and atomic migrations

Verified against: SQLite 3.53.0 ALTER TABLE documentation; STRICT since 3.37.0.

## Contents

- Separate storage from validation
- Make NULL and foreign-key policy explicit
- Choose native ALTER by runtime capability
- Rebuild the complete schema contract
- Preserve historical identity
- Prove success and failure

## Separate storage from validation

[official] In ordinary tables, INTEGER/NUMERIC affinity can retain nonnumeric
text rather than rejecting it. Inspect `typeof(column)` and the actual stored
values before concluding that the declared type protected an import. A numeric
comparison alone does not establish a numeric storage class.

Use STRICT tables (3.37.0+) when the supported readers and writers permit them.
Allowed declared types are INT, INTEGER, REAL, TEXT, BLOB and ANY; DATE, BOOLEAN
and DECIMAL are not STRICT types. Choose the representation and domain constraint
explicitly rather than substituting another engine's type names.

STRICT attempts lossless affinity conversion before rejecting a value. It does
not mean only host integers can enter INTEGER columns. STRICT ANY preserves the
input's value and type; ordinary-table ANY can convert numeric-looking strings.
Use TEXT when formatting such as leading zeros is part of an identifier contract.

If compatibility requires ordinary tables, pair domain checks with storage-class
checks where needed, for example `CHECK(typeof(amount)='integer' AND amount>=0)`.
Affinity is applied before constraints: if the original input representation is
itself forbidden, validate that at the binding/import boundary as well.

Do not repair an invalid source by adding CAST to a migration until the conversion
policy is approved. A cast can truncate or turn invalid text into a numeric value,
creating syntactically valid but false data. Report affected record identities
and original values; keep the failed migration rollbackable.

## Make NULL and foreign-key policy explicit

[official] `CHECK(amount>=0)` accepts NULL because NULL is not a false CHECK result.
Add NOT NULL when absence is invalid. UNIQUE allows multiple NULL values.
Ordinary rowid-table primary keys can also allow NULL unless explicitly NOT NULL;
STRICT and WITHOUT ROWID primary keys reject it, while INTEGER PRIMARY KEY on a
rowid table generates an integer when INSERT supplies NULL.

`INT PRIMARY KEY` is not the rowid alias `INTEGER PRIMARY KEY`. The inline
`INTEGER PRIMARY KEY DESC` declaration is a historical exception that is not
an alias. Preserve the actual DDL rather than inferring identity from a type prefix.

Enable FK enforcement on each connection before transactions, then read it back.
No result row means the build lacks support; a `0` means enforcement is off.
Do not silently proceed when the application's data contract requires it.

A foreign key with any NULL child component is satisfied without a parent match;
use NOT NULL when the relationship is mandatory. Parent keys must match a primary
or unique key with suitable declared collations. Some cross-table schema defects
surface at DML preparation as "foreign key mismatch", not at CREATE TABLE.
Index child key columns when parent deletes/updates would otherwise scan children.

`PRAGMA foreign_key_check` returns violations even when enforcement was disabled.
It does not throw merely because rows were returned. `integrity_check` is not a
substitute for FK checking. Test each invalid contract independently so that an
FK rejection does not hide a missing type or NULL constraint.

## Choose native ALTER by runtime capability

[official] Read https://www.sqlite.org/lang_altertable.html when the runtime differs
from the verified version or a new ALTER form is requested. Use the operation
supported by the oldest engine that will open the migrated database.

| Requested change | Decision |
|---|---|
| Rename table or column | Prefer native ALTER; inspect its dependency rewrites and ambiguity errors |
| Add column | Check restrictions: no PRIMARY KEY/UNIQUE, restricted defaults, NOT NULL needs non-NULL default, no STORED generated column |
| Drop column (3.35.0+) | Native DROP COLUMN exists but fails for indexed, key, generated-expression or other schema references; resolve dependencies deliberately |
| Set/drop column NOT NULL (3.53.0+) | Use `ALTER TABLE t ALTER COLUMN c SET NOT NULL` or `DROP NOT NULL` when it is the needed change; check data and resulting definition |
| Change affinity/type, table options, arbitrary key or relationship structure | Use the generalized transactional rebuild |

SET NOT NULL on an already nonnullable column is a no-op. If legacy DDL contains
redundant NOT NULL clauses, DROP NOT NULL is guaranteed to remove one or more,
not necessarily all; inspect the resulting constraint and behavior.

Do not use `writable_schema=ON` to force malformed dependency text past ALTER.
It suppresses parsing errors and can leave an unusable database. Native ALTER or
a reviewed rebuild is the default, not ad hoc editing of sqlite_schema text.

## Rebuild the complete schema contract

[official plus application preservation requirements] Use a dedicated migration
connection that owns no caller transaction. Use the existing migration marker
convention; if it is `user_version`, update it in the same transaction as the DDL.
A host script helper that implicitly commits can defeat this sequence; inspect
that helper before using it for a multi-statement migration.

Follow this order for a general rebuild of a referenced ordinary table:

1. Rehearse on a consistent copy; record the source schema/version, data policy,
   disk-space requirement and a recovery artifact. Coordinate migration ownership
   so competing application writers do not observe a half-configured connection.
2. Outside any transaction, record `foreign_keys`, disable it for the rebuild
   and require readback `0`. Abort without DDL if already inside a caller-owned
   transaction; changing the PRAGMA there would silently fail.
3. Begin an explicit write transaction, normally IMMEDIATE. Recheck the expected
   migration version inside it to prevent a stale migration decision.
4. Capture exact table DDL, explicit indexes, triggers and affected views; inspect
   incoming FK definitions on other tables. Capture historical identity state.
   `sqlite_schema WHERE tbl_name=?` finds attached objects, not every view or
   trigger on another table that references this one. Inspect the wider schema
   and application migrations rather than trusting that filter as a dependency graph.
5. Create a noncolliding new table with the intended full definition, including
   constraints, collations, defaults, generated columns and table options.
   Copy with explicit source/target column lists; preserve row identity when the
   application depends on it and omit generated targets as required.
6. Before the old table disappears, transactionally drop affected views and
   external triggers that would otherwise be invalid during rename. Retain their
   DDL and dependency order. Drop dependent views before their prerequisites;
   rebuild prerequisites first. Do not drop incoming child data.
7. Drop the old table, then rename the new table into the original name. Do not
   rename the old table first: SQLite may rewrite foreign keys/views to the
   temporary old name and leave dependencies pointing at the wrong object.
8. Recreate explicit indexes, triggers and affected views with reviewed definitions.
   Automatic indexes derive from table constraints; do not execute NULL SQL from
   sqlite_schema as if it were a missing CREATE INDEX statement.
9. Restore AUTOINCREMENT state as described below, then consume FK and integrity
   checks and validate preserved row/dependency facts. Any violation or failed
   schema statement means rollback, not publication with a warning.
10. Advance the migration marker and commit only after those gates pass. After
    commit or rollback, restore the original FK setting outside the transaction
    and verify it. If normal application policy requires ON, enforce it before
    returning this connection to any caller, or close the connection instead.

If an unexpected error prevents confirming transaction state or restoring the
connection contract, retire that dedicated connection. Preserve the first error;
do not report migration success solely because final cleanup did not raise.

## Preserve historical identity

[official] AUTOINCREMENT prevents reuse of previously committed generated rowids,
not just duplicates among surviving rows, and does not promise gapless numbering.
Its high-water mark lives in `sqlite_sequence`, which can exceed `MAX(id)` after
deletions. Copying current rows into a new table cannot reconstruct that history.

Before dropping an AUTOINCREMENT table, capture whether its sequence row exists
and its `seq`. After the replacement takes the final name, preserve a high-water
mark at least as large as both the captured history and the value established by
the copied rows. Update the replacement's existing sequence row, or insert it if
history must be restored and no row exists. Keep this inside the DDL transaction.
Do not assume `sqlite_sequence.name` has a UNIQUE constraint suitable for UPSERT.

Do not reset unrelated sequence rows or lower the saved value to current MAX(id).
Handle an empty table with deleted historical rows, and preserve exhaustion at
the maximum signed rowid rather than issuing reused IDs. If there was no sequence
row and no copied row creates one, do not invent historical issuance.

## Prove success and failure

Exercise the migrated copy through real consumers: read dependent views, perform
an update that fires a preserved trigger, test independent constraint failures,
and generate an ID after a deleted high ID. Verify incoming child rows remain.
Use a disposable copy or rollbackable probe, not production test inserts.

For invalid source data, require complete failure invariance: table definitions,
rows, child data, indexes/triggers/views, sequence, migration marker and connection
FK setting. Compare logical state rather than database byte identity; journal and
page layout can change without altering the transaction contract.

<!-- sources: moollm-sqlite, sqlite-types, sqlite-strict, sqlite-foreignkeys, sqlite-create-table, sqlite-alter, sqlite-autoincrement, sqlite-pragma -->
