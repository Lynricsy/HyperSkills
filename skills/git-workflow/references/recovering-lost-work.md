# Recovering lost work

Verified against: git 2.55.0

## Contents

- [What is recoverable and what is not](#what-is-recoverable-and-what-is-not)
- [First move: the reflog](#first-move-the-reflog)
- [When gc has already run](#when-gc-has-already-run)
- [Reflog expiry defaults](#reflog-expiry-defaults)
- [Deleted branches](#deleted-branches)
- [Commits no reflog covers](#commits-no-reflog-covers)
- [Dropped stashes](#dropped-stashes)
- [Uncommitted work](#uncommitted-work)
- [Worktrees and lost recovery paths](#worktrees-and-lost-recovery-paths)
- [Recovery playbook by symptom](#recovery-playbook-by-symptom)

## What is recoverable and what is not

Everything that ever became a git object is recoverable until the object is pruned, and pruning
only happens when nothing — including a reflog entry — references it. The boundary is therefore
not "committed vs uncommitted" but "hashed vs never hashed".

| State | Recoverable? |
|---|---|
| committed, branch moved away | yes — reflog |
| committed, branch deleted | yes — HEAD reflog, or `fsck` |
| committed, reflog expired and gc run | no |
| stashed, then dropped | yes — `fsck --unreachable` |
| `git add`ed, then overwritten | yes — the blob exists; `fsck --unreachable` finds it |
| edited in the working tree only | **no** |

## First move: the reflog

```bash
git reflog                       # HEAD's movements in this worktree
git reflog show <branch>         # that branch's own movements
git reflog --date=iso            # with timestamps, for "yesterday"
```

Every reset, checkout, commit, rebase, merge and amend appears there. Verified after a
`git reset --hard HEAD~1`:

```
6c4bad0 HEAD@{0}: reset: moving to HEAD~1
1d634d8 HEAD@{1}: commit: three          <- the lost commit
```

Recover by naming the SHA, not the `@{n}` form, which shifts as new entries arrive:

```bash
git branch recover/three 1d634d8         # safest: a new branch, nothing else moves
git reset --hard 1d634d8                 # only if you are sure the current tip is disposable
git cherry-pick 1d634d8                  # take just that commit onto where you are
```

`ORIG_HEAD` is the one-step shortcut: rebase, merge, reset and pull all set it to the
pre-operation tip, so `git reset --hard ORIG_HEAD` undoes the most recent of those. It is
overwritten by the next such operation, so it is not a substitute for the reflog.

## When gc has already run

`git gc --prune=now` sounds final and is not. Verified: the commit orphaned by a `reset --hard`
survives `git gc --prune=now` untouched, because the reflog entry still references it. What
actually destroys it is expiring the reflog first:

```
$ git gc --prune=now
$ git cat-file -t 1d634d8
commit                                   <- STILL ALIVE

$ git reflog expire --expire=now --expire-unreachable=now --all
$ git gc --prune=now
$ git cat-file -t 1d634d8
fatal: Not a valid object name           <- GONE for good
```

So "I already ran gc" is not a reason to stop looking. Two corollaries:

- `git fsck --unreachable` reports *nothing* while the reflog still holds the commit, because a
  reflog entry counts as reachable. Pass `--no-reflogs` to see what would die if the reflog were
  expired.
- Never suggest `git reflog expire --expire-unreachable=now --all` as a cleanup step while a
  recovery is still open. It is the one command that turns a recoverable loss into a permanent one.

## Reflog expiry defaults

Nothing is set in a default install; these are git's built-in values:

| Setting | Default | Applies to |
|---|---|---|
| `gc.reflogExpire` | 90 days | entries for commits still reachable |
| `gc.reflogExpireUnreachable` | 30 days | entries for commits nothing else reaches |

`git gc` (including the automatic one triggered by `gc.auto`) expires according to those before
pruning. So the practical recovery window for an orphaned commit is 30 days, not forever — and a
repository that sets these lower has a shorter one. Check with `git config --get gc.reflogExpireUnreachable`;
an empty result means the default is in force.

Reflogs are off by default in bare repositories (`core.logAllRefUpdates`), which is why a
force-push to a bare remote has no reflog on the server side to recover from. Recovery in that
case comes from someone's clone.

## Deleted branches

`git branch -D` removes the branch's own reflog file along with the ref. Verified:

```
$ git branch -D doomed
Deleted branch doomed (was 1d1c007).
$ git reflog show doomed
fatal: ambiguous argument 'doomed': unknown revision or path not in the working tree.
$ git reflog                              # HEAD's reflog still has it
1d1c007 HEAD@{1}: commit: work on doomed
$ git branch doomed 1d1c007               # recovered
```

So the route is always the *HEAD* reflog, in the worktree where the work was done. If the commit
was never HEAD in this worktree — pushed from elsewhere, or made in a worktree that has since been
removed — go to `fsck`.

## Commits no reflog covers

```bash
git fsck --unreachable --no-reflogs
git fsck --lost-found            # additionally writes them under .git/lost-found/
```

`--no-reflogs` is the important half: without it, reflog-held objects are reachable and the output
is misleadingly empty. Inspect candidates before adopting them:

```bash
git log --oneline --all --not --all --reflog        # everything not on a branch
git show --stat <candidate-sha>
git branch recover/<slug> <candidate-sha>
```

`fsck` output is unordered and includes trees and blobs. Filter to commits, then read each one's
subject and stat; a repository with a long history can have dozens of unreachable commits from
ordinary rebases, and most of them are not what you want.

## Dropped stashes

`git stash drop` unlinks the entry but leaves the commit. Verified — it appears in no reflog and
only `fsck` finds it:

```
$ git stash drop
$ git reflog --all | grep -c 74f5da8
0
$ git fsck --unreachable
unreachable commit 74f5da80ef40c0aef787637aca67923f372150bb
$ git stash apply 74f5da8
```

`git stash apply <sha>` works on a raw stash commit, not only on a `stash@{n}` name. A stash commit
has two or three parents (HEAD, the index state, and untracked files if `-u` was used), so
`git show --stat <sha>` under-reports it; `git stash show -p <sha>` shows the change properly.

## Uncommitted work

This is the one git cannot help with. Verified:

```
$ echo "hours of uncommitted work" > f
$ git checkout -- f
$ cat f
committed                                 <- the edit is gone
$ git fsck --unreachable --no-reflogs
                                          <- nothing; it was never an object
```

`git checkout -- <path>`, `git restore <path>`, `git reset --hard`, `git clean -fd`, `git stash`
followed by a bad `pop`, and a `git checkout` that overwrites — all discard working-tree state that
no object records.

But a single `git add` is enough to make it survivable, because staging hashes the content:

```
$ git add f && git rev-parse :f
cdb2c0fa8c14521e29cbac55de94f25fceb1ea54
$ git restore --source=HEAD --staged --worktree f     # the edit is "lost"
$ git cat-file -p cdb2c0fa8c14521e29cbac55de94f25fceb1ea54
work again                                             <- still there
```

So: before running anything destructive against a dirty tree, `git add -A` or
`git stash push -u` first. And on an IDE or editor with local history, say so — that is often the
only remaining copy.

## Worktrees and lost recovery paths

A linked worktree has its own reflog, stored in its administrative directory. Remove the worktree
and that reflog is deleted with it. Verified: after removing a worktree and then deleting its
branch, expiring reflogs and running `gc --prune=now`, the commit is unrecoverable — there was
never a HEAD reflog entry for it in the main checkout.

Order matters: delete the branch while the worktree still exists (so the main repository's reflog
or the surviving worktree reflog records it), or note the SHA before removing anything.

## Recovery playbook by symptom

| Symptom | First command |
|---|---|
| "I reset --hard and lost a commit" | `git reflog` |
| "My rebase ate commits" | `git reflog`, then `git range-diff <upstream> <old-tip> HEAD` |
| "I force-pushed over someone's work" | their clone's `git reflog`; or `git fsck` on the remote if you can reach it |
| "I deleted the branch" | `git reflog` (HEAD), then `git branch <name> <sha>` |
| "I dropped a stash" | `git fsck --unreachable`, then `git stash apply <sha>` |
| "I amended and lost the old message" | `git reflog`, then `git show <old-sha>` |
| "A merge went wrong and completed" | `git reset --hard ORIG_HEAD` |
| "I lost uncommitted edits" | nothing in git; check the editor's local history |

<!-- sources: addyosmani-git, mattpocock-guardrails, obra-finishing, git-docs -->
