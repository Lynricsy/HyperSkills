---
name: linux-ops
description: "Operates Linux hosts with systemd, permissions, networking, storage and backup recovery."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# linux-ops

Paths below are relative to this skill's directory.

## Scope

Operate at the Linux host boundary: identify which process, mount, listener,
manager or persistence layer owns the failure; change that layer without losing
management access, evidence or recoverable data. Cover systemd-based bare-metal
and VPS hosts, including distribution differences in service names and managers.

Keep these boundaries:

- Cloud IAM, provider networking and VM control planes belong to aws, azure or
  gcp. A provider console may be a recovery prerequisite, not a deployment task.
- Container images and Kubernetes resources belong to containers. Do not apply
  host firewall or namespace recipes inside a container as though it were a host.
- Application logic belongs to its language/framework skill; Linux merely being
  the runtime is not a reason to diagnose it here.
- Database-consistent capture and replay require the database's supported
  procedure. Own the host cutover, not an invented database backup protocol.
- Production telemetry pipelines belong to observability; shell program design
  is not this skill's purpose.

A request to analyze supplied evidence authorizes analysis, not connecting to
machines or applying repairs. Write an executable plan only after its target
values and access boundary are known; do not silently execute that plan.

## Core rules

1. Bind every observation to host identity, time, boot, process and namespace where relevant; identical paths can name different objects.
2. Separate observation, proposed mutation and authorized execution; a diagnostic request does not authorize a restart or remote login.
3. Record the owner of runtime and persistent configuration before editing; two independent managers can immediately undo each other.
4. Require an external recovery path for changes that can remove access or destroy data, plus a tested rollback independent of the connection being changed; a second shell alone is not recovery.
5. Preserve volatile evidence before restarting, rotating, deleting or resetting failure state; the repair may erase the only explanation.
6. Distinguish disk configuration, manager-loaded configuration and live process state; daemon-reload does not retrofit namespaces, credentials or resource limits into MainPID.
7. Match readiness and reload claims to the daemon's actual protocol; active state and a successful signal helper are not proof that clients see the new configuration.
8. Keep non-root identity and isolation while fixing the specific denied operation; chmod 777, broad capabilities and disabling MAC or sandboxing are not diagnostic fixes.
9. Treat capability bounding as a ceiling, not a grant; inspect effective and ambient sets and exec-time privilege restrictions before changing them.
10. Count storage by filesystem and object identity, not path strings or FD rows; blocks, inodes and per-process descriptors exhaust independently.
11. Recheck PID identity and device/inode immediately before a signal or file action; process and descriptor numbers can be reused.
12. Verify new connections on every relevant address family after an access change; established sessions and IPv4 success can conceal a broken IPv6 or new-SSH path.
13. Validate TLS with the intended hostname, SNI, trust chain and endpoint; bypassing verification proves connectivity, not certificate correctness.
14. Select a recoverable point by explicit identity and consistency evidence, not unqualified latest; mirrors and successful backup jobs do not establish RPO or RTO.
15. Restore into an isolated target before cutover and coordinate all writers; an intact repository can still restore an unusable application state.
16. State exactly what each check proves and leaves untested; do not promote syntax checks, samples or repository checks into end-to-end recovery evidence.

## Workflows

### Diagnose a host incident

- [ ] Confirm the supplied or authorized host identity, boot/time interval,
      distribution, kernel, relevant tool version and impact. Record whether the
      evidence is live, a snapshot, or a synthetic incident.
- [ ] Choose the reference matching the observed boundary in the topic router;
      do not run a full-host inventory to answer a single-service question.
- [ ] Collect the smallest discriminating evidence: effective unit and journal
      for service failure; mount plus block/inode figures for storage; listener,
      route, resolver and endpoint identity for network failure.
- [ ] Mark access-denied or unavailable observations as unknown, not empty.
      Begin unprivileged; request only the privilege necessary to read the
      missing evidence, excluding private keys and secret environment values.
- [ ] Write a causal hypothesis and the observation that would falsify it.
      Compare the actual daemon context with a successful shell context rather
      than treating a root-shell success as an application health test.
- [ ] Before an action that loses evidence, identify its owner, retention duty
      and a protected off-host or unaffected-volume evidence destination.
- [ ] **Gate — localized cause:** cite evidence for the failing layer and one
      discriminating check. If the check cannot be performed, label the proposed
      cause as a hypothesis and provide the exact missing observation.

### Change a service or its execution environment

- [ ] Identify the exact unit instance, drop-ins, activation sockets/timers,
      MainPID and worker processes. Read `references/service-privileges-and-limits.md`.
- [ ] Capture the current effective settings and rollback copies with ownership,
      permissions and secrets protected. Specify availability budget, drain
      method, health probe and external recovery access before disruption.
- [ ] Determine whether the change is daemon configuration, unit configuration,
      socket configuration or live cgroup state. Specify the activation required
      for each; do not use reload-or-restart to conceal that decision.
- [ ] Check syntax with the installed daemon's validator and, for unit changes,
      `systemd-analyze verify` against the candidate unit. Treat unknown settings
      as a compatibility problem, not a harmless warning.
- [ ] For denied access, resolve identity, ancestor traversal, ACL/MAC,
      capability, filesystem and namespace evidence before changing one policy.
- [ ] For a namespace or execution-context change, drain and replace the affected
      process under an approved window; retain the non-root and read-only design.
- [ ] Activate only the authorized change, then read the live process state.
      Watch readiness, worker turnover and restart counters over a meaningful
      interval, not only the instant after the command returns.
- [ ] **Gate — live activation:** the intended process observes the new object
      or setting, a fresh client exercises it, isolation remains effective, and
      the documented rollback remains available until acceptance.

### Recover capacity without erasing the incident

- [ ] Identify the filesystem behind the failing path and classify the failure
      as blocks, inodes, quota, read-only/I/O, or descriptors. Read
      `references/storage-and-processes.md`.
- [ ] Compare like-for-like `df` and scoped `du` observations; retain collection
      times, traversal errors and mount boundaries.
- [ ] For deleted-open files, group holders by device/inode, estimate allocated
      space once per object, and preserve required evidence before the last close.
- [ ] Identify the producer responsible for continuing growth. Propose its
      supported reopen, retention or bounded shutdown mechanism rather than a
      generic truncate, kill or package-cache cleanup.
- [ ] State exact targets, authorization, recovery copies and capacity required
      for evidence preservation. If preservation is impossible, escalate the
      loss tradeoff explicitly rather than silently deleting.
- [ ] **Gate — sustainable headroom:** remeasure blocks and inodes separately,
      confirm the intended holders released the object, and demonstrate that a
      representative write works without a continuing exhaustion trend.

### Change remote access, routing or filtering

- [ ] Read `references/network-and-remote-changes.md`; identify the real SSH
      port, source network, destination addresses, jump path, firewall manager,
      routing manager and persistence loader for both IP families.
- [ ] Record current runtime and persistent state, and test the independent
      console/rescue path before touching the management path.
- [ ] Prepare the complete candidate and rollback transaction. Arm rollback
      outside the SSH process tree and prove its status, deadline and privileges.
      If reboot is in scope, account for how recovery survives reboot too.
- [ ] Validate configuration without activation; preserve management access and
      required network control traffic in the candidate before restrictive policy.
- [ ] Apply one boundary at a time under explicit authorization; keep the old
      session and do not remove the previous access path yet.
- [ ] **Gate — fresh remote access:** establish a non-multiplexed new SSH session
      from the expected client path, exercise required IPv4/IPv6 business traffic
      and TLS, inspect persistence, then cancel rollback and retire old access.

### Prove a backup and perform a recovery

- [ ] Read `references/backup-and-restore.md`; state the recovery point objective
      (maximum data loss) and recovery time objective (maximum service outage).
- [ ] Select repository and snapshot ID by host, paths, time and application
      consistency evidence. Compute recoverable age at the incident time; do not
      substitute backup schedule frequency for observed recovery-point age.
- [ ] Establish isolated target identity, free blocks/inodes, metadata support,
      restricted access and network containment before restoring untrusted data.
- [ ] Restore the selected scope, check content and metadata, then exercise the
      recovered service without contacting production dependencies or writers.
- [ ] Time retrieval, provisioning, restore, replay, validation and switch-over.
      Mark RTO unproven if only download speed or a small sample was timed.
- [ ] For cutover, stop or fence every writer, complete the approved final delta
      or replay, retain the pre-cutover state, and allow one authoritative writer.
- [ ] **Gate — usable recovery:** the recovered application passes its own
      integrity and client checks at the selected point, measured outage meets
      RTO, observed data loss meets RPO, and rollback handles post-cutover writes.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Service lifecycle, permissions, capabilities, namespaces and limits | A unit fails only under systemd, a reload does not activate data, or execution policy changes | `references/service-privileges-and-limits.md` |
| Storage and process ownership | A write fails, df and du disagree, deleted files retain space, or a process exhausts FDs | `references/storage-and-processes.md` |
| DNS, TLS, routes, SSH and host firewall | Reachability differs by client/address family, or a change may disrupt remote management | `references/network-and-remote-changes.md` |
| Consistent backup and controlled restoration | Evaluating recoverability, copying metadata-sensitive data, or planning a restore/cutover | `references/backup-and-restore.md` |

## Output format

Use this template for an incident or change review; omit inapplicable rows rather
than claiming they passed.

```text
Target: host / unit or filesystem / relevant version / observation time
Authority: analysis only | authorized observations | authorized mutation scope
Impact and invariants: availability, evidence retention, identity and isolation
Evidence: observed facts with source; hypotheses and missing observations separate
Cause: mechanism and falsifying check
Change: exact target, current -> proposed state, owner, activation and disruption
Recovery: external access, saved state, executor/deadline, rollback trigger
Verification: check -> expected result -> observed result -> limitation
Status: proposed | applied and verified | rolled back | blocked
```

For configuration findings, add `path:line - finding` and a minimal before/after
fragment. Separate a suggested command from one actually run. Never include
private keys, passwords or raw secret-bearing environment dumps in the report.

## Environment

Use the target's existing tools and managers. Common observations use systemd,
procfs, util-linux, coreutils, iproute2 and the installed OpenSSH; storage details
may require lsof, ACL/xattr tooling or the filesystem's native utilities.

Do not install diagnostic packages during an incident without approval: package
installation changes disk pressure and state. Request existing evidence instead.
Consult installed manuals (`man systemd.exec`, `man sshd`, `man rsync`) and
`restic help restore`/`restic help check` before using version-sensitive flags.
