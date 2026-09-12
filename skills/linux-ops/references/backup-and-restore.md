# Backup evidence and controlled restoration

Verified against: restic documentation at ba802d42b7294c98b62c16d1157ea3e80820c019;
rsync official manual. Check the installed versions before selecting flags.

## Contents

- Recovery objectives and four different proofs
- Capture a consistent recovery point
- Select and isolate the restore
- Preserve filesystem semantics through rsync
- Coordinate cutover and rollback
- Recovery report

## Recovery objectives and four different proofs

State RPO as the maximum tolerable committed-data loss and RTO as the maximum
tolerable service outage. Compare the incident time to the latest *recoverable
application point*, including completed replay, not merely a snapshot's finish
time. A daily schedule does not prove a 24-hour RPO after a missed or partial job.

[official] Keep these evidence levels separate:

| Evidence | Establishes | Does not establish |
|---|---|---|
| Successful backup exit plus manifest | Reported capture completed for its scope | Every required path or a consistent database state |
| `restic check` | Repository structural checks | Reading every payload pack |
| `restic check --read-data` | Reading and validating all repository packs | Application consistency, restored metadata usability or RTO |
| Isolated restore and application exercise | Usability of the selected recovered scope | Untested snapshots, paths or a faster full disaster recovery |

A subset check proves only the inspected subset. Random percentage sampling does
not guarantee eventual complete coverage; record which strategy, repository
state and intervals were checked. Reading all packs can be expensive and consume
network/I/O capacity: authorize its scope rather than treating it as a free probe.

Measure the full recovery path: obtain keys and infrastructure, retrieve data,
restore metadata, perform application recovery/replay, validate, switch traffic
and resume service. A timed sample or repository check cannot prove full RTO.

## Capture a consistent recovery point

Inventory required data, configuration, keys and external dependencies. Separate
backup credentials from the production host's failure domain; ensure authorized
recovery operators can retrieve them without that host. Do not place secrets in
command arguments, logs or the skill output.

Use the application's supported snapshot/export protocol for live state. A file
copy or filesystem snapshot of a running database may be crash-consistent, not
application-consistent, and may omit required journal/log files. Route its exact
capture and replay contract to the relevant database skill. For a multi-volume
application, coordinate the recovery point across volumes and record its marker.

Track producer and consumer exit status in streamed captures. A successful backup
consumer can store a partial dump from a failed producer. Snapshot existence is
not success; retain the failed status and exclude that point from RPO claims.
A stream transport does not create an atomic multi-file application snapshot.

Keep version history and an independently recoverable copy. A mirror propagates
accidental deletion, corruption and ransomware; an rsync transfer alone is not
retention. Before pruning, repair or unlock operations, confirm repository
identity, other active writers/locks, recovery copy and a supported procedure.
Do not clear a lock solely because a previous client disconnected.

## Select and isolate the restore

[official] List snapshots by the required host and path, inspect their contents,
and choose an explicit snapshot ID. Unqualified `latest` can belong to a different
host or dataset. Restic's `--path` selects a snapshot; it does not restrict which
files in that snapshot are restored. Use supported include/exclude or subtree
selection only after confirming the internal paths with `restic ls`.

Before an authorized restore, confirm these target facts:

- A dedicated empty directory on the intended filesystem, not `/`, a production
  data root, the repository itself or a path resolving into one through symlinks.
- Adequate blocks and inodes for the restored form, including sparse-file
  expansion, temporary staging and the retained rollback copy.
- Restricted directory access and a separate non-root inspection identity.
  Grant narrowly scoped restore privileges only when ownership, device objects
  or security attributes require them; do not run recovered executables as root.
- Contained network and credentials: no production database connections,
  outbound notifications, scheduled jobs or background replication from the
  restored service. Keep it out of production discovery/load balancers.

After those checks, the operation shape is
`restic -r REPOSITORY restore SNAPSHOT_ID --target ISOLATED_TARGET`.
This writes files and, by default, can overwrite existing target files. It is
not an observation command. Inspect the resulting directory layout before
starting anything; do not assume the snapshot root matches the live data root.

Verify required file contents, UID/GID mapping, modes, ACLs, xattrs, symlinks,
hard-link relationships and application-readable paths. Content equality alone
misses a lost ACL or wrong owner. Restore a representative critical dataset and
run the application's own integrity and client checks; expand to the whole
recovery scope before claiming complete recovery or RTO compliance.

## Preserve filesystem semantics through rsync

[community, official] The source trailing slash changes directory placement:
`source/` copies its contents, while `source` copies the directory by name.
Preview the exact approved source, target and options, not a different example.
Use `--dry-run --itemize-changes` before any deletion-capable synchronization.
Review the complete deletion list and reconfirm target mount/identity before
execution. A dry run is not authorization and does not freeze a changing source.

Archive mode `-a` does not include hard links, ACLs or xattrs. Select `-H`, `-A`
and `-X` explicitly when the recovery contract requires them and confirm support
and permissions on both ends. `--numeric-ids` preserves numbers, not semantic
account identity; check target accounts rather than choosing it unconditionally.
Non-root execution may be unable to restore ownership or security namespaces.
For an established non-root archival design, rsync fake-super can encode metadata
in xattrs, but those encoded attributes require a tested restoration procedure;
they are not the final effective permissions on the restored tree.

Hard links are detected within the transfer set. Separate copies of two related
trees can lose cross-tree link relationships; preserve them in one coherent
transfer where required. Restoring data across different filesystems cannot
preserve a hard link spanning those destination filesystems.

Use SSH with verified host identity for remote transfer; `rsync://` and a direct
`host::module` daemon transport are not inherently encrypted. Rsync must be
available at both ends. Treat returned partial-transfer or vanished-file status
as evidence to investigate, not as unconditional backup success.

Do not update a live application tree with `--inplace` to save temporary space;
readers can observe partial content and hard-linked history can be altered.
Stage separately. `--delete` implements a mirror, not historical backup. Keep the
previous recoverable generation outside the deletion scope and confirm an
external recovery location before any approved destructive synchronization.

## Coordinate cutover and rollback

Identify every writer, including timers, queues, maintenance tasks and clients.
Use the application's supported write fence/quiesce procedure, drain in-flight
work, and record the boundary transaction or timestamp. Complete the approved
final delta/replay while writes remain fenced. A first copy made during writes
can reduce downtime but cannot replace the final consistent pass.

Confirm the replacement unit's non-root identity, namespace visibility and
metadata access before switching it into production. Activate one authoritative
writer, switch traffic, then perform read/write checks through the real client
path. Retain the old state, isolated from writers, through the acceptance window.

Define rollback before accepting writes on the new state. After new commits,
pointing traffic back to the old tree silently loses data. Specify write fencing,
reverse replication/export/replay or an explicit data-loss decision with owner
approval. If no such path exists, label rollback as unavailable after the write
boundary; do not promise an instant reversible cutover.

For any overwrite or deletion, require exact target confirmation, protected
pre-change recovery data and tested external rescue access. If validation fails,
leave the recovery copy isolated, preserve errors and keep production unchanged.
Do not repair the only backup repository in place as part of a speculative fix.

## Recovery report

Record repository and snapshot ID, selected paths, application point, incident
clock, RPO calculation, timed stages, metadata/content/application results and
untested scope. Include write-fence evidence, last reversible point, retained
state location and the rollback action after new writes. State separately whether
the backup is structurally intact, payload-checked and operationally restored.

<!-- sources: terminal-rsync, rsync-manual, restic-docs -->
