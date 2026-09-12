---
name: git-workflow
description: "Manages local Git branches, worktrees, commits, merges, conflicts and history recovery."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

Paths below are relative to this skill's directory.

## Scope

Git as a local tool: branches and worktrees, rebase and merge, conflicts, commit granularity and
messages, history rewriting and its guardrails, recovering work that appears to be gone, bisect
and history archaeology, hooks and signing, submodules and subtrees, and the mechanics of
finishing a branch.

The line against the `github` skill matters enough to state from both sides. That skill says:

> Anything git alone can do offline is out of scope here; this skill starts where GitHub does.

The pairing sentence for this one: anything that needs GitHub the platform is out of scope here;
this skill ends where GitHub begins. Pull requests, issues, Actions, rulesets and branch
protection, releases, and every `gh` invocation belong to `github`. Pushing and fetching appear
here only where the local consequences are the point — what a lease actually protects, what a
rewrite does to collaborators.

Not covered: whether a change is correct, well designed or safe. Reviewing a diff is the
`code-review` skill's job, and auditing a codebase for vulnerabilities is `security-review`'s.
This skill covers getting the change committed, integrated and recoverable, not its content.

Not covered: the test-writing loop (`test-driven-development`), CI configuration (`github`),
semantic versioning and changelogs — release mechanics live with the forge, and changelog prose
has no skill in this library yet, so say so rather than improvising one.

## Core rules

1. **A `git fetch` disarms a bare `--force-with-lease`.** The lease compares the remote against
   your local `refs/remotes/<remote>/<branch>`, so any fetch — including an informational one —
   refreshes the value being compared and the push then succeeds over commits your history does
   not contain. Add `--force-if-includes` (git 2.30+), or set
   `push.useForceIfIncludes true`. Details and the verified transcript:
   `references/history-rewrite-guardrails.md`.
2. **Never plain `git push --force`.** It has no lease and no includes check; it overwrites
   whatever is on the remote. Treat any alias wrapping it as a finding.
3. **Rewrite only unpublished history.** The default branch, release branches, pushed tags, and
   any branch someone else has checked out or built from are off the table. Public history that is
   wrong gets `git revert`, which is a new commit rather than a replacement.
4. **Take a backup ref before any rewrite and verify with `git range-diff`.**
   `git branch backup/pre-rewrite <tip>`, then
   `git range-diff <upstream> backup/pre-rewrite HEAD`. `git log` cannot distinguish a clean
   rebase from one that dropped a hunk during conflict resolution; `range-diff` can.
5. **After rewriting a pushed branch, tell collaborators to `git fetch` then
   `git reset --hard origin/<branch>`** — explicitly not `pull` or `merge`, either of which
   resurrects the commits the rewrite removed.
6. **A rewrite drops signatures and resets committer dates.** Author dates survive; every SHA is
   new; a rebase with signing configured re-signs the commits with the rewriter's key rather than
   the author's. Say which of those the repository cares about before starting.
7. **A pushed secret is compromised.** Rotate it first; the rewrite only limits future exposure.
   `git filter-repo` is the tool. With `git filter-branch` the old blob stays readable until
   `refs/original/*` is deleted, all reflogs expired, and `git gc --prune=now` has run — verified,
   and skipping any one of the three leaves the secret in place.
8. **`git gc --prune=now` does not delete what a reflog still references.** Verified: a commit
   orphaned by `reset --hard` survives it. Only
   `git reflog expire --expire-unreachable=now --all` followed by `gc --prune=now` destroys it,
   which is why that pair is never suggested while a recovery is open.
9. **Start every recovery at the reflog, and never at `fsck`.** `git fsck --unreachable` reports
   nothing while a reflog entry holds the object, because reflogs count as reachable; `--no-reflogs`
   is what makes it useful. The 30-day default (`gc.reflogExpireUnreachable`) bounds the window.
10. **`git branch -D` deletes that branch's own reflog.** `git reflog show <branch>` then fails and
    only the HEAD reflog of the worktree where the work happened remembers. Record the SHA before
    deleting anything you are not certain about.
11. **Uncommitted work is the one thing git cannot recover.** `git checkout -- <path>`,
    `git restore`, `reset --hard` and `clean -fd` discard state no object records. A single
    `git add` hashes it and makes it recoverable — do that before running anything destructive on
    a dirty tree.
12. **Resolve a conflict between two intents, not two blocks of text.** Read the commits behind
    both sides first, using the operation's own ref (`MERGE_HEAD`, `REBASE_HEAD`,
    `CHERRY_PICK_HEAD`, `REVERT_HEAD`). `-X ours` / `-X theirs` and `git checkout --ours` are bulk
    deletion of one side's work, not resolution.
13. **`ours` and `theirs` invert during a rebase or cherry-pick**: `ours` is the upstream being
    replayed onto and `theirs` is your own commit. Reading the labels the same way in both
    operations is how the wrong side gets kept.
14. **Prefer `merge.conflictstyle zdiff3` (git 2.35+).** The default two-way style hides the merge
    base, so "which side changed what" is unanswerable from the file. Changing the config does not
    re-render files already conflicted — `git checkout --merge <path>` does.
15. **With `rerere` enabled, always diff what it produced before committing.** Verified: a replayed
    resolution leaves the path unmerged with no conflict markers in it, and with
    `rerere.autoupdate` it is staged outright, so `git commit` seals a resolution nobody read.
    `git rerere forget <path>` clears the cache but does *not* restore the markers;
    `git checkout --merge <path>` does.
16. **"Successfully rebased" is a statement about commits only.** With `rebase.autoStash`, the
    rebase can report success while the autostash application conflicted — verified: `UU` in the
    tree, the entry still in `git stash list`, and nothing left to `--abort`. Check `git status`
    after every rebase.
17. **Rebase your own topic branch; merge into the trunk and merge anything others have.** A
    rebase hands collaborators a history that no longer contains their commits. Merge also wins
    when one conflict would otherwise be replayed through every commit in the series.
18. **`git rebase` orphans the branches under a stack.** Use `--update-refs` (git 2.38+) or set
    `rebase.updateRefs true`; verified, without it the intermediate branch stays on its
    pre-rebase commit.
19. **`rebase.autosquash` is off by default.** Verified on 2.55.0: a plain rebase leaves
    `fixup! <subject>` commits standing. Pass `--autosquash`, which works non-interactively.
20. **`git branch --merged` misses squash-merged and cherry-picked work.** Verified: a
    squash-merged branch lists under `--no-merged`. Use `git cherry -v <base> <branch>`, where `-`
    means the patch is already upstream, before deleting any branch.
21. **`refs/stash` is shared across every worktree.** Verified. Parallel agents that stash pop each
    other's entries; in a parallel setup, commit instead. Per-worktree state is only HEAD, the
    index, the working tree, in-progress operation state, and that worktree's reflog.
22. **Remove a worktree with `git worktree remove`, before deleting its branch.** A branch checked
    out in a worktree cannot be deleted, and `rm -rf` of the directory keeps the lock until
    `git worktree prune` — verified. A refused removal means files exist nowhere else, so `--force`
    is the user's call and never the agent's.
23. **A worktree starts with no untracked or ignored files.** No `.env`, no `node_modules`, no
    build cache. Bootstrap it and run the suite once, or every later failure is ambiguous.
24. **`git bisect run` treats 125 as skip and, on 2.55.0, rejects 126 and 127 as `bogus exit
    code` while continuing.** Those are exactly what a mistyped script path returns, so run the
    script by hand on a known-good and a known-bad commit first. An out-of-range code stops the
    run but leaves the session open — `git bisect reset` is always the last step.
25. **A plain `git push` will publish a submodule gitlink that exists on no remote.** Verified.
    Set `push.recurseSubmodules check` (or `on-demand`); the default lets the broken state out and
    everyone else's `git submodule update` fails.

## Workflows

### start-parallel-work

Detail in `references/branching-and-worktrees.md`.

- [ ] Detect existing isolation before creating anything: compare `git rev-parse --git-dir` with
      `--git-common-dir`, and rule out a submodule with
      `git rev-parse --show-superproject-working-tree`, which produces the same inequality.
- [ ] If the harness has its own worktree mechanism, use it. A worktree git created is invisible to
      a harness that tracks its own.
- [ ] Detect the default branch through `git symbolic-ref refs/remotes/<remote>/HEAD`; fall back
      `main`, `master`, current branch. Name each branch `<type>/<slug>`, and validate a derived
      name with `git check-ref-format --branch`.
- [ ] One `git worktree add <path> -b <branch> origin/<base>` per task. A project-local worktree
      directory is confirmed ignored (`git check-ignore -q .worktrees`) before it is used.
- [ ] Bootstrap each worktree — dependencies, local env file — then run the suite once to
      establish a clean baseline. Report failures rather than building on them.
- [ ] Tell the agents: commit, never stash (`refs/stash` is shared); stay inside their own
      directory; land the large mechanical change first if one is planned.
- [ ] **Gate — isolation is real:** `git worktree list` shows one row per task, each on its own
      branch, and each baseline suite is green or its failures are reported.

### integrate-upstream-changes

Detail in `references/rebase-vs-merge.md`.

- [ ] `git fetch origin`, then state the divergence with
      `git log --oneline --left-right --boundary HEAD...origin/<base>`. Never use `git pull` for
      this — it hides the choice.
- [ ] Choose and say why: rebase a topic branch only you have; merge a branch anyone else has, a
      branch that carries meaningful merges, or a sync where one conflict would otherwise be
      replayed through every commit.
- [ ] Commit or stash first. With `rebase.autoStash` the rebase can report success while the
      autostash conflicted.
- [ ] Pass the base explicitly (`git rebase origin/main`), not a bare `git rebase` — the implicit
      `--fork-point` reads a local reflog, so the same command behaves differently in CI.
- [ ] For a stack, `--update-refs`. For a branch with real merges, decide between flattening a
      sync merge and `--rebase-merges`.
- [ ] **Gate — nothing lost, nothing left over:** `git status` is clean, `git stash list` has no
      orphaned autostash entry, and `git range-diff <base> <old-tip> HEAD` shows only the expected
      differences.

### resolve-conflicts

Detail in `references/conflict-resolution.md`.

- [ ] Identify the operation from the `git status` header and enumerate every unmerged path with
      `git diff --name-only --diff-filter=U` plus `git ls-files -u`. Each one gets a recorded
      decision.
- [ ] If `rerere` is enabled, run `git rerere status` and `git rerere diff` before reading any
      file: a markerless unmerged path is a replayed resolution nobody has reviewed.
- [ ] Switch to `zdiff3` and re-render with `git checkout --merge <path>`, or read stage 1 directly
      (`git show :1:<path>`), so the merge base is visible.
- [ ] For each path, read both sides' history — `git log -p <merge-base>..HEAD -- <path>` and the
      same against the operation's counterpart ref — and state each intent in one sentence.
      `git show <op-head> -- <path>` is silently empty when an earlier commit on the branch touched
      the path.
- [ ] Compose both changes where compatible; where not, keep the side matching the integration's
      stated goal and record what was dropped. Invent no third behaviour.
- [ ] Sweep for semantic conflicts: grep the merged tree for every identifier either side added or
      removed, then run the project's typecheck, tests and formatter.
- [ ] **Gate — the index agrees with the tree:** `git status --short` shows no `UU`,
      `git diff --check` finds no marker, the project's checks pass, and the operation is carried
      to completion (including every remaining commit of a rebase) rather than aborted.

### tidy-a-branch-before-review

Detail in `references/commits-and-messages.md` and `references/rebase-vs-merge.md`.

- [ ] Confirm the branch is unpublished or topic-only. If it is published, say what the rewrite
      costs its holders and get agreement first.
- [ ] `git branch backup/pre-rewrite HEAD` before touching anything.
- [ ] Read the repository's own last twenty commit subjects before applying any message
      convention; the project's style wins over the default.
- [ ] Fold fixups with `git rebase --autosquash <base>` (the flag is required), squash noise
      commits, and reword subjects to the imperative present with a body that says why.
- [ ] Split anything that mixes concerns: `git rebase -i`, mark `edit`, `git reset HEAD~`, then
      `git add -p` and commit in groups, testing each with `git stash push --keep-index`.
- [ ] Decide what happens to sync merges in the range — flatten, or `--rebase-merges` — rather than
      letting the rebase silently drop them.
- [ ] **Gate — same work, better shape:**
      `git range-diff <base> backup/pre-rewrite HEAD` accounts for every difference,
      the suite is green, and the push uses `--force-with-lease --force-if-includes`.

### remove-something-from-history

Detail in `references/history-rewrite-guardrails.md`.

- [ ] If the content is a credential, say plainly that it is compromised and must be rotated
      first. The rewrite is containment, not repair.
- [ ] Establish reach: `git log --all --oneline -- <path>`, and whether the commits have been
      pushed, forked, or built. That determines who has to be told.
- [ ] Back up (`git branch backup/pre-rewrite`), then rewrite with `git filter-repo`. If only
      `git filter-branch` is available, the cleanup is `refs/original/*` deleted, all reflogs
      expired, `gc --prune=now` — all three.
- [ ] Confirm removal against the content, not the log: `git log --all --oneline -- <path>` empty,
      and `git cat-file -p <old-sha>:<path>` failing.
- [ ] Add the path to `.gitignore` and a secret-scanning `pre-commit` hook in the same change.
- [ ] **Gate — removal is complete and honest:** the old object is unreadable locally, the
      collaborator instruction is `fetch` + `reset --hard` and is stated explicitly, and the fact
      that forks, caches and the forge's own storage may retain copies is stated rather than
      implied away.

### recover-lost-work

Detail in `references/recovering-lost-work.md`.

- [ ] Stop writing to the repository. Do not run `gc`, `reflog expire`, `reset` or `checkout`
      until the target is anchored to a ref.
- [ ] `git reflog --date=iso` in the worktree where the work happened, and `git reflog show
      <branch>` if the branch still exists. `ORIG_HEAD` covers the most recent rebase, merge,
      reset or pull.
- [ ] Anchor first, adopt later: `git branch recover/<slug> <sha>`. Never `reset --hard` onto a
      candidate before confirming what it contains.
- [ ] If no reflog covers it — a dropped stash, a branch deleted with `-D`, a removed worktree —
      use `git fsck --unreachable --no-reflogs`, then `git show --stat` each candidate.
      `git stash apply <sha>` works on a raw stash commit.
- [ ] For uncommitted work, say so plainly: nothing in git recorded it, and the editor's local
      history is the only remaining place to look.
- [ ] **Gate — recovered and referenced:** the commits are on a named branch, `git log` shows the
      expected subjects, and the user is told which of their expectations could not be met.

### find-the-commit-that-broke-it

Detail in `references/bisect-and-archaeology.md`.

- [ ] Try the cheap route first: `git log -S'<symbol>'` or `-G'<pattern>'` on the affected paths,
      `git log -L`, `git blame -w -C`. A textual question does not need a bisect.
- [ ] For a behavioural regression, establish a reproducing check and a known-good commit, and
      confirm the good commit is an ancestor of the bad one.
- [ ] Write the test script outside the repository. Exit 0 for good, 1 for bad, 125 for a commit
      that cannot be built or installed. Run it by hand on both endpoints before automating.
- [ ] `git bisect start <bad> <good>` then `git bisect run <script>`. Treat any `bogus exit code`
      line as a broken script, reset, and fix it. Consider a worktree so the bisect does not
      occupy the main checkout.
- [ ] Save `git bisect log` before `git bisect reset`, and report the culprit with its diff — or,
      under `--first-parent`, say that what you found is the merge that brought it in.
- [ ] **Gate — the session is closed and the answer is checked:** `git bisect reset` has run, and
      the named commit's diff plausibly explains the symptom rather than merely being where the
      search stopped.

### finish-and-clean-up

Detail in `references/finishing-a-branch.md`.

- [ ] Run the project's full suite on the tree about to be integrated. A green run from earlier in
      the session proves something about a tree that no longer exists.
- [ ] Confirm the base — `@{upstream}`, then `git log --oneline --left-right --boundary
      HEAD...origin/<candidate>` — rather than assuming the default branch.
- [ ] Present the integration choice (merge locally / push and open a pull request / keep as is)
      and wait. Merge locally, then re-run the suite on the merged result.
- [ ] Establish the work has landed before deleting anything: `git cherry -v <base> <branch>`, or
      an empty `git diff --stat <base> <branch>`. Record the SHA with `git rev-parse` first.
- [ ] Remove the worktree with `git worktree remove` **before** deleting its branch, from outside
      the worktree. If the directory was already deleted by hand, `git worktree prune` first — the
      branch stays locked until then. A refused removal is reported to the user, never forced.
- [ ] `git branch -d` from the base branch, `-D` only with the `git cherry` result to back it, then
      `git fetch --prune`.
- [ ] **Gate — nothing deleted while it was the only copy:** the work is on the base branch or
      pushed, `git worktree list` and `git branch -vv` show the expected remainder, and every
      deleted branch's SHA was recorded first.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Trunk-based defaults, branch naming rules, worktree internals, per-worktree vs shared state, layout, bootstrapping, removal and pruning, parallel agents | Creating branches or worktrees, or setting up parallel work | `references/branching-and-worktrees.md` |
| Rebase/merge trade-offs, `--update-refs`, `--rebase-merges`, `--fork-point` in CI, autostash, `--autosquash`, `range-diff`, squash-merge costs, aborting and `ORIG_HEAD` | Deciding how to integrate, or a rebase behaved unexpectedly | `references/rebase-vs-merge.md` |
| Unmerged inventory, ours/theirs inversion, intent recovery per operation, conflict styles, index stages, rerere's two misleading states, rename conflicts, semantic conflicts | Conflict markers or unmerged paths are in the tree | `references/conflict-resolution.md` |
| Atomic commits, splitting a messy tree or an existing commit, message shape and types, breaking changes, trailers, non-interactive commit forms, fixups, pre-commit sweep | Writing commits, or a branch's history is unreviewable | `references/commits-and-messages.md` |
| What a rewrite changes, the lease's failure mode, `--force-if-includes`, collaborator instructions, removing a file from all history, filter-branch leftovers, the rewrite checklist | Any rewrite of published or shared history, or a secret in history | `references/history-rewrite-guardrails.md` |
| Reflog semantics and expiry defaults, gc/prune interaction, deleted branches, `fsck --no-reflogs`, dropped stashes, the limits on uncommitted work, worktree reflogs | Anything appears to be lost | `references/recovering-lost-work.md` |
| Bisect loop and exit-code contract, skip, custom terms, merges in range, bisect in a worktree, log/replay, `log -S`/`-G`/`-L`, blame across moves, `git cherry` | Finding which commit changed behaviour or touched a line | `references/bisect-and-archaeology.md` |
| Hook locations, the global `core.hooksPath` override, which hook for which job, `--no-verify`, a secret-scanning hook, ssh vs gpg signing, verification, signatures under rewrites | Adding or diagnosing hooks, or working in a signed repository | `references/hooks-and-signing.md` |
| Submodule vs subtree, gitlinks and detached HEAD, the unpushed-gitlink accident, `submodule.recurse`, subtree commands, sparse checkout, partial vs shallow clones, maintenance | The repository vendors another, or is large enough to be slow | `references/submodules-and-large-repos.md` |
| Verify-then-integrate order, base detection, the integration choice, landed-or-not checks, branch deletion, worktree cleanup order, pruning tracking refs, discarding work | The work is complete and needs integrating or cleaning up | `references/finishing-a-branch.md` |

## Output format

Before running anything that can destroy work — a force-push, a rewrite, a branch or worktree
deletion, a `reset --hard`, a `gc` — present a plan in this shape and wait:

```markdown
### Plan
1. `git branch backup/pre-rewrite feat/x`      # escape hatch
2. `git rebase --autosquash origin/main`
3. `git range-diff origin/main backup/pre-rewrite HEAD`
4. `git push --force-with-lease --force-if-includes origin feat/x`

### Irreversible
- Step 4 replaces origin/feat/x. Anyone holding it must `git fetch` then
  `git reset --hard origin/feat/x` — not `pull`.
- Commits dropped in step 2 stay in the reflog for 30 days, then go.

### Not touched
- `main`, `feat/currency`, the credentials in deploy/creds.env (rotation is separate).
```

Report a recovery as the anchoring ref plus what it contains: `recover/<slug> -> <sha>`, the
subjects it holds, and an explicit statement of anything that could not be recovered. For a
bisect, report the culprit SHA, its subject, its diff, and the endpoints and skips that produced
it.

## Environment

Requires git. Rules marked with a version gate need at least that version; everything else was
verified against git 2.55.0. `git --version` before relying on `zdiff3` (2.35+),
`--force-if-includes` (2.30+), `--update-refs` (2.38+), or a non-interactive `--autosquash`.

`git filter-repo` is a separate install and is not present by default;
`git filter-branch` ships with git but is deprecated and leaves the cleanup to you. `git subtree`
ships with git, though its man page is packaged separately on some distributions, so
`git subtree --help` can fail while the command works.
