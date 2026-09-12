# Storage capacity and process-held objects

Verified against: Linux man-pages 6.19; systemd 261.2 execution limits.

## Identify the exhausted resource

Use observations scoped to the failing path and its actual mount. Begin with
`findmnt -T PATH`, `df -hT PATH` and `df -i PATH`. Record filesystem, source device,
mount options and collection time. If the application has a private namespace,
the host path may not select its filesystem; compare the process's mountinfo.

| Evidence | Next distinction | Unsafe shortcut |
|---|---|---|
| Blocks full, visible tree smaller | Deleted-open files, hidden mounted-over data, snapshots, reserved space, incomplete traversal | Recursively delete the largest directory |
| Inodes full, blocks available | Many small objects and the producer/retention policy | Remove one large file and call the incident fixed |
| `EDQUOT` | User/group/project quota on that filesystem | Trust host-wide free bytes |
| `EROFS` or I/O errors | Read-only mount or protective remount; storage fault evidence | Force read-write before preserving data |
| `EMFILE` | This process's soft FD limit and descriptor ownership | Raise all system limits |
| `ENFILE` | System-wide file table pressure | Treat one service's restart as the whole diagnosis |

For a visible-tree measurement, use a scoped `du -x` traversal on the same
filesystem and capture permission errors. Apparent file sizes differ from
allocated blocks for sparse/compressed/shared data. Snapshots and filesystem
metadata require the filesystem's native accounting; do not subtract arbitrary
`du` output from `df` and label the entire difference a leak.

Do not unmount a live filesystem just to inspect files hidden beneath it. Obtain
an approved maintenance or isolated inspection path that does not disturb
writers, mount propagation or management access. Filesystem repair, format,
resize, snapshot deletion and forced remount require verified device identity,
external rescue access, recoverable data and the filesystem's own procedure.

## Deleted names still consume storage

[official] Removing the last directory entry does not release a file still open
by a process. The last relevant holder must release the object before its space
can be reclaimed. Check `lsof +L1` when available, scoped by filesystem/process,
and use procfs to resolve uncertain holders. Permission-limited output cannot
prove the absence of other holders.

Build an object table, not a list of candidate PIDs to kill:

```text
filesystem/device | inode | allocated bytes | link count | PID/start time/FD
owner/service | retention requirement | supported release action
```

Group duplicate FDs, workers and processes by device plus inode. Two rows with
the same inode on the same device do not mean twice the reclaimable capacity.
Inode numbers alone are not globally unique. Logical size is not necessarily
allocated bytes; label estimates accordingly. Refresh object identity before
acting because both PID and FD numbers are reusable.

A safe release sequence is:

1. Confirm the affected object, holders, service owner and retention obligation.
2. Preserve required logs/evidence to protected storage on another unaffected
   filesystem or host, with authorization and sufficient space. Record hashes,
   provenance and timestamps. A live writer makes a copy non-atomic; coordinate
   capture or document the missing interval rather than claiming completeness.
3. Prefer the application's documented reopen mechanism after preservation.
   If unsupported, agree a controlled drain/stop/start with external access and
   rollback of configuration/data. Do not guess that SIGHUP means reopen.
4. Observe every holder release the original object and the service write to
   the intended new file. Recheck blocks and inodes independently.

Do not truncate `/proc/PID/fd/N`, overwrite the open object or kill arbitrary
holders to make the numbers smaller. Truncation destroys evidence, affects all
holders of that inode and may leave a writer's offset beyond EOF, creating a
sparse hole on subsequent writes. Renaming or deleting the visible replacement
file does not release the old deleted-open object.

## Stop recurrence and prove headroom

Correct the producer or retention mechanism responsible for growth. Select a
bounded retention policy with the owner; file age alone does not prove data is
unneeded. Mail spools, temporary files and package caches are not automatically
safe deletion targets. Confirm exact paths and an independently recoverable copy
before any approved deletion; if no recovery is possible, record that irreversible
loss explicitly before seeking authorization.

For descriptor growth, compare descriptor types and counts over a bounded
interval alongside traffic. Separate legitimate load from leaked sockets/files.
Read `/proc/PID/limits`; changing a shell limit or a unit file cannot demonstrate
that an existing daemon inherited the new value. Preserve select compatibility
and choose a bounded restart only after capturing leak evidence and impact.

Report reclaimed allocated space, remaining inode headroom, verified new writes
and the producer's subsequent growth rate. If a deleted large file frees blocks
but inode exhaustion remains, the incident is not closed. If storage faults are
present, prioritize evidence-preserving recovery rather than a cosmetic free-space
success.

<!-- sources: linux-unlink, linux-path, systemd-exec -->
