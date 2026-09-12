# Service privileges, activation and process limits

Verified against: systemd 261.2 manuals; Linux man-pages 6.19.

## Contents

- Three states and an activation protocol
- Denied operations without abandoning isolation
- Mount namespaces and atomic renewal
- Resource limits and process identity
- Acceptance evidence

## Three states and an activation protocol

[official] Keep three separate records:

| State | Observation | What it does not prove |
|---|---|---|
| Files on disk | `systemctl cat UNIT` plus application configuration | The manager loaded the edited files |
| Manager model | `systemctl show UNIT` with selected properties | MainPID inherited those settings |
| Live invocation | MainPID, worker identities, procfs and a fresh client | That a subsequent boot uses the same configuration |

`systemctl daemon-reload` reloads unit definitions and dependencies. It does not
reload application configuration or recreate an existing process's mount
namespace, UID, ambient capabilities or inherited limits. `systemctl reload`
invokes the service's supported reload mechanism, not daemon-reload.
`enable` arranges activation dependencies; it does not start a service without
an explicit start action. `disable` does not stop a running invocation.

Choose activation from the actual changed object:

- Application config: validate it, then use the documented synchronous reload
  protocol. A signal-only `ExecReload` can return before loading finishes.
- Execution policy or mount bindings: load the unit definition, then replace the
  affected invocation through an approved drain/restart. Do not assume a reload
  helper modifies the main process's namespace or credentials.
- Socket listener: inspect the `.socket` unit and inherited descriptors as well
  as the service. Restarting only the daemon may retain a manager-owned listener.
- Runtime cgroup controls: supported properties may be changed live, but inspect
  persistence separately; do not confuse them with per-process rlimits.

Match `Type=` to the program, not a generic template. `Type=exec` (systemd 240+)
reports execution setup failures but not application readiness. `notify` requires
actual READY notifications; selecting it without application support times out.
Use `notify-reload` (253+) only with its reload notification protocol. Preserve a
packaged unit's supported startup contract rather than converting blindly.

For long-running daemons, consider `Restart=on-failure` only after identifying
expected exits and the existing recovery policy. `always` also restarts clean
exits and is not a universal production setting. A restart loop needs its first
failure captured; `reset-failed` resets useful state and is not a repair.
`OOMPolicy=continue` governs handling after an OOM kill; it does not disable the
kernel OOM killer. Distinguish kernel/global OOM, cgroup OOM and userspace oomd.

## Denied operations without abandoning isolation

[official] Begin with the exact syscall/error, path and process identity.
`EACCES`, `EROFS`, `ENOENT` and bind-address errors imply different checks.
Inspect the service's effective UID/GID and supplementary groups, each ancestor
component's search permission, leaf permissions and ACL mask, then MAC denials.
A root shell reading a key neither proves the service can read it nor proves the
path exists inside `RootDirectory`, `ProtectHome` or its mount namespace.

Use `namei -l PATH`, scoped `getfacl`, relevant SELinux/AppArmor audit events and
`/proc/PID/status` as observations where available. Avoid indiscriminate process
environment dumps and private-key reads. Readability probes must run with the
service identity and relevant namespace; a standalone `sudo -u` test establishes
only the host identity view, not the complete service sandbox.

`CapabilityBoundingSet` restricts the available set; listing
`CAP_NET_BIND_SERVICE` there alone does not give a non-root process that effective
capability. `NoNewPrivileges=yes` blocks privilege acquisition through exec,
including file-capability elevation; adding a file capability is not a reliable
fix under that invariant. Ambient capabilities (systemd 229+) can convey a
specific capability to a non-root service while retaining no-new-privileges.
Check effective, permitted, inheritable, bounding and ambient sets after exec,
and account for executable file capabilities, set-ID bits and user namespaces.

Default to the minimal service-scoped grant if the operation truly needs it;
for a daemon already supporting socket activation, keep the manager-owned socket
instead. Do not introduce a new activation protocol just to avoid analysis.
Do not grant CAP_SYS_ADMIN, CAP_DAC_OVERRIDE or root to fix an unexplained denial.
A writable-path exception does not create DAC permission and cannot make an
underlying read-only filesystem writable.

## Mount namespaces and atomic renewal

[official] `BindPaths`/`BindReadOnlyPaths` (233+) imply mount namespacing.
`PrivateMounts` is explicitly available from 239. Each command forked by the
manager receives its own configured mount namespace; an `ExecReload` helper's
fresh view is not the long-running `ExecStart` process's view. Children forked
by that main process normally inherit its existing namespace.

A single-file bind holds the original object. Publishing a replacement by
rename changes which inode the host pathname resolves to, not the bind already
held by MainPID. Thus all these observations can simultaneously be true:

- Host path and a newly spawned reload helper read the new certificate.
- MainPID's bound path still resolves to the old inode.
- Sending the reload signal succeeds, but new client handshakes serve the old
  certificate because the daemon rereads its old bound object.

Compare device/inode identities and `/proc/PID/mountinfo` for host, MainPID and
helper. Reading `/proc/PID/root/...` with permission is observational evidence;
do not write through it to bypass a read-only binding or overwrite the old key.
It also does not prove which certificate workers have already loaded in memory.

Use a narrowly scoped, stable parent directory bound read-only, with renewal
publishing children within it. Keep that parent inode stable; replacing the
bound directory itself recreates the problem. For a certificate/key pair,
serialize publishing and reload, verify the pair, and ensure the daemon resolves
one coherent generation. Two separate file renames are not an atomic pair;
use a generation directory plus a single pointer switch only if the daemon's
path-resolution/reload contract makes the pair coherent.

Bind lists append across assignments. An empty assignment resets both writable
and read-only bindings collected earlier, so enumerate required existing binds
before replacing the list. A drop-in that merely adds the parent can leave the
old file mount overlaid underneath it. Reset the list, restate all required
bindings, and omit obsolete single-file bindings; do not accidentally remove
unrelated state or logging mounts.

Migration requires one controlled process replacement: confirm target unit and
recovery copies, validate the candidate, hold external recovery access, drain
connections, then activate the new namespace. Retain User, NoNewPrivileges,
ProtectSystem and narrowly scoped read-only access. Afterward, rehearse a second
renewal through the supported reload path without another restart, observing
MainPID/worker behavior and fresh non-resumed client handshakes.

## Resource limits and process identity

[official] Capture `/proc/PID/limits`, descriptor count and highest descriptor,
not the administrator shell's `ulimit`. An `EMFILE` process limit differs from
system-wide `ENFILE`; a socket leak differs from legitimate concurrency growth.
List descriptor types and change over time before raising a ceiling.

A process using `select` with the usual Linux fd_set cannot safely handle FDs
above 1023. Raising the soft `LimitNOFILE` beyond 1024 can convert a clean capacity
failure into memory corruption or incorrect readiness handling. Confirm the
program and dependencies use a safe polling implementation first. A high hard
limit with a conservative soft limit is not the same as making both high.

Rlimits are inherited at process creation; a unit edit is not live evidence.
Per-user managers cannot raise a service's hard limit beyond their own inherited
ceiling. `LimitNPROC` is per real UID, not per unit; `TasksMax` counts tasks for
the unit's cgroup. `LimitRSS` is ineffective on Linux; use supported cgroup memory
controls for service-wide memory policy rather than pretending it enforces RSS.

Before a signal or restart, refresh MainPID, start time and cgroup membership.
Use the daemon's documented reopen/drain mechanism; arbitrary signals may kill
it. A PID from a stale log is not a safe action target.

## Acceptance evidence

Show the candidate passed its installed-version validators, then separately
show the running invocation has the intended identity, groups, capabilities,
limits and mount objects. Preserve failed startup evidence if activation fails.
Exercise the original failed operation and a client request, including new TLS
handshakes when applicable. Record the exact rollback activation and effects on
active connections; restoring the old file alone does not restore live state.

<!-- sources: terminal-systemd, systemd-exec, systemd-service, systemctl-manual, linux-path -->
