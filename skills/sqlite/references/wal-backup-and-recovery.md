# WAL, backup and recovery

Verified against: SQLite 3.53.0 documentation; WAL-reset fixes in 3.51.3,
3.50.7 and 3.44.6.

## Contents

- Establish the operating boundary
- Read checkpoint progress correctly
- Back up through the engine
- Restore without mixing histories
- Handle suspected damage

## Establish the operating boundary

[official] WAL allows concurrent readers and a writer, not concurrent writers.
Ordinary multi-connection WAL requires shared-memory coordination on one host;
do not place a shared active WAL database on a network filesystem. Validate a
custom VFS against its own locking and shared-memory contract.

Choose WAL for local concurrent read/write workloads when its operational costs
fit. Retain rollback journaling when the deployment requires it; consistency is
not exclusive to WAL. WAL transactions across ATTACHed databases are atomic per
file, not across the attached set. Do not promise a multi-file atomic restore.

During coordinated bootstrap, outside a transaction, execute
`PRAGMA journal_mode=WAL` and inspect the returned mode. WAL persists across
reopen. Foreign-key enforcement, busy timeout and synchronous policy belong to
connection setup, not to an assumption that the file remembers all PRAGMAs.

[official] For WAL commits that must survive power loss, choose `synchronous=FULL`
subject to the filesystem/device honoring synchronization. NORMAL preserves WAL
consistency but can lose acknowledged transactions after an OS crash or power
loss. Do not change durability to cure lock contention. Do not claim a process
restart smoke test demonstrates power-loss durability.

### WAL-reset version boundary

The documented race concerns two or more connections to the same WAL database,
in separate threads or processes, writing or checkpointing at coincident times.
The affected lineage is 3.7.0 through 3.51.2, with fixes in 3.51.3 and later and
backports in 3.50.7 and 3.44.6. Evaluate release branches explicitly: "version
below 3.51.3" alone incorrectly rejects those patched backports. For a vendor
build, obtain its source ID and backport evidence; do not infer patches from a
package's unrelated version. Upgrade the engine actually loaded by the app.

## Read checkpoint progress correctly

[official] The WAL contains committed pages not necessarily in the main file.
The `-shm` file is the reconstructible coordination/index structure, not a
substitute for the WAL. Do not delete either while connections are using them.
A retained WAL after a crash is recovery state, not disposable scratch data.

When growth or commit latency is reported:

1. Identify long read transactions, unfinished cursors and large write batches.
   A reader's end mark can prevent checkpoint completion and WAL reuse.
2. Record auto-checkpoint policy and page size; byte size alone does not show
   how many frames remain uncheckpointed. A recycled WAL can retain its size.
3. If authorized to perform maintenance, use
   `PRAGMA main.wal_checkpoint(PASSIVE)` for non-waiting progress, not as a
   purely read-only probe. It copies pages and may sync the database.
4. Read all three result fields: busy indication, WAL frames, checkpointed frames.
   PASSIVE can report first field `0` while the last two differ. Values `-1` for
   frame counts mean no applicable WAL, not a successfully drained log.
5. Fix snapshot lifetime first. Use RESTART/TRUNCATE only in a suitable maintenance
   window with a bounded wait and inspect completion; TRUNCATE shrinks the WAL
   on success. Do not put forced truncation on every request.

Automatic checkpoint thresholds are workload choices, not correctness limits.
The historical warning against WAL transactions above 100 MB does not apply to
SQLite 3.11.0 and later. Still provision free space for a large transaction and
for a reader that delays reuse.

## Back up through the engine

[community, official] Default to the Online Backup API exposed by the existing
binding, or the CLI `.backup` command where that is the established tool.
A source connection can read committed WAL content while the live writer remains
open. Sequentially copying the main file, then WAL, then SHM is not a snapshot.

1. Choose a fresh staging destination distinct from the live file and any good
   previous backup. Resolve paths before opening with create/overwrite flags.
2. Open a dedicated source connection without a pending application write.
   Start and finish the backup through the binding's supported API.
3. For incremental backup, handle transient contention within a deadline and
   require terminal success; interruption or an existing destination file does
   not establish completion. Release the backup handle on every exit.
4. Close the destination and validate it in isolation before publishing. If a
   single-file artifact is required, ensure SQLite has completed the destination's
   own recovery-file lifecycle rather than manually unlinking sidecars.
5. Publish only a completed artifact. Use the filesystem's appropriate durable
   publication sequence when surviving a crash during publication is required;
   a rename alone is not a universal power-loss guarantee.

Use `VACUUM INTO` instead when a compact rewritten snapshot is desired. It needs
its own supported runtime and space allowance, and can change implicit rowids
of tables without an explicit INTEGER PRIMARY KEY. Do not substitute it when
bitwise identity or implicit rowid identity is a requirement.

An incremental backup can restart as other connections modify the source.
Promise a consistent completed snapshot, not an exact wall-clock start instant
unless the application deliberately established and retained that read snapshot.
Specify a freshness boundary using application markers or a coordinated snapshot.

## Restore without mixing histories

1. Restore to a new directory with no unrelated WAL or journal bearing the same
   basename. Preserve the original source and recovery files untouched.
2. Open the restored database through a compatible engine, enable FK enforcement,
   and consume both `PRAGMA integrity_check` and `PRAGMA foreign_key_check`.
   Require `ok` and no FK violations, not just successful command execution.
3. Query required application facts known to predate the backup, schema version,
   and relevant identity state. An empty but valid database can pass integrity.
4. For replacement of a live path, stop all users of that path, retain a rollback
   copy and publish the validated file set according to the deployment procedure.
   Never replace underneath open connections or pair it with the old live WAL.
5. Reopen via the real application path and verify a representative read before
   restoring write traffic. State whether this was rehearsed or executed.

## Handle suspected damage

Stop avoidable writes and preserve a consistent forensic copy of the database
and its recovery state before attempting salvage. Let a compatible SQLite engine
perform normal journal/WAL recovery on a working copy. Do not use `immutable=1`
as a shortcut around active-writer locking: it asserts the file cannot change.
If normal opening fails, treat salvage as lossy recovery into a separate output;
compare business records and report omissions. Integrity checks cannot restore
missing commits, establish backup freshness or prove that all business data exists.

<!-- sources: terminalskills-sqlite, moollm-sqlite, sqlite-wal, sqlite-backup, sqlite-pragma, sqlite-vacuum -->
