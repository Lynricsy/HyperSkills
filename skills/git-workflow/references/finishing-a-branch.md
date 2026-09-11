# Finishing a branch

Verified against: git 2.55.0

## Contents

- [Order of operations](#order-of-operations)
- [Verify before integrating](#verify-before-integrating)
- [Establish the base](#establish-the-base)
- [Present the integration choice](#present-the-integration-choice)
- [Merging locally](#merging-locally)
- [Has it landed?](#has-it-landed)
- [Deleting the branch](#deleting-the-branch)
- [Cleaning up the worktree](#cleaning-up-the-worktree)
- [Pruning remote-tracking refs](#pruning-remote-tracking-refs)
- [Discarding work](#discarding-work)

## Order of operations

Cleanup happens last, and only after the work is demonstrably somewhere else. Every step below is
ordered so that nothing is deleted while it is still the only copy.

```
tests green -> base confirmed -> integration chosen -> integrated & re-verified
            -> worktree removed -> branch deleted -> tracking refs pruned
```

## Verify before integrating

Run the project's full suite on the tree that is about to be integrated. A green run from earlier
in the session proves something about a tree that no longer exists.

If it fails, report the failures and stop. The integration menu comes after a green suite, not
alongside it — and "probably flaky" is a claim that needs the second run to back it.

## Establish the base

The base is whatever this work forked from, which is not always the default branch. It is usually
named in the branch's upstream, the plan, or the conversation:

```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'   # fails if none is set
git merge-base HEAD origin/<candidate>
git log --oneline --left-right --boundary HEAD...origin/<candidate>
```

Confirm it before merging. Merging into the wrong base is expensive to undo and, once pushed, is
not undoable at all without a rewrite.

## Present the integration choice

Integration is the user's decision, not an inference from "the work looks done". Offer exactly:

1. Merge back into `<base>` locally.
2. Push the branch and open a pull request (the mechanics of that belong to the `github` skill).
3. Keep the branch as it is.

On a detached HEAD in an externally managed workspace, option 1 is not available — there is no
branch to merge — so offer the push (`git push origin HEAD:refs/heads/<name>`) and the keep-as-is.

Discarding the work is not on this menu. It happens only in response to an explicit request; see
the last section.

## Merging locally

```bash
main_root=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$main_root"                       # worktree removal later must run from outside it
git switch <base>
git merge --ff-only origin/<base>     # fail loudly rather than invent a merge
git merge <branch>
<project tests>                       # on the merged result, not on the branch
```

A failure on the merged result stops everything: nothing has been pushed, the merge is local and
recoverable with `git reset --hard ORIG_HEAD`, and the branch and worktree stay where they are
while you investigate.

Capture the worktree path *before* changing directory — `git rev-parse --show-toplevel` answers
differently once you have moved.

## Has it landed?

Before deleting anything, establish that the work exists somewhere else. Ancestry is not the only
way work lands, and `git branch --merged` only understands ancestry:

```bash
git branch --merged <base>            # true merges only
git cherry -v <base> <branch>         # patch-id comparison: '-' already upstream, '+' not
git diff --stat <base> <branch>       # empty => the trees agree, whatever the history says
git log --oneline <base>..<branch>    # what is still unique to the branch
```

Verified on a squash-merged branch: it appears under `git branch --no-merged main`, while
`git cherry -v main <branch>` prints `-` for its commit. So in any repository that squash-merges,
`--merged` will never authorise a deletion and `git branch -d` will always refuse. Use `git cherry`
or the tree comparison, then delete with `-D` and say why the check passed.

The inverse case matters too: a branch whose upstream is gone has usually been merged and deleted
on the forge.

```bash
git fetch --prune
git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads   # look for [gone]
```

`[gone]` means the remote branch no longer exists — strong evidence the work landed, but confirm
with `git cherry` before deleting local commits.

## Deleting the branch

```bash
git branch -d <branch>     # refuses unless merged into the current branch
git branch -D <branch>     # unconditional
```

`-d` checks against the branch you are *on*, not against the default branch. Standing on a topic
branch and running `git branch -d other` gives an answer about the wrong base. Switch to the base
first, or pass `--merged <base>` to the listing and decide from that.

`git branch -D` deletes the branch's own reflog along with the ref. Verified:

```
$ git branch -D doomed
Deleted branch doomed (was 1d1c007).
$ git reflog show doomed
fatal: ambiguous argument 'doomed': unknown revision or path not in the working tree.
```

The commit is still recoverable from the *HEAD* reflog of the worktree where the work was done —
but only from there. Note the SHA before deleting anything you are not certain about; a one-line
`git rev-parse <branch>` beforehand costs nothing.

## Cleaning up the worktree

Clean up only worktrees this workflow created; anything else belongs to the host environment or
another agent and gets left alone.

```bash
cd "$main_root"                        # removal must run from outside the worktree
git worktree remove "$worktree_path"
git worktree prune                     # clears any stale registration
```

A refusal is information:

```
fatal: '<path>' contains modified or untracked files, use --force to delete it
```

Show what is at stake and let the user choose:

```bash
git -C "$worktree_path" status --porcelain -uall
```

Commit them to the branch, move them into the main checkout, or delete them — the third being
unrecoverable. `--force` on your own initiative destroys files that exist in no other place.

Order: remove the worktree **before** deleting the branch. A branch checked out in a worktree
cannot be deleted, and if the worktree directory was removed by hand the lock survives until
`git worktree prune` (verified: `error: cannot delete branch 'feat' used by worktree at ...`).
And because a worktree's reflog is deleted with its administrative directory, deleting the branch
after the worktree is gone leaves no local recovery path at all.

## Pruning remote-tracking refs

```bash
git fetch --prune                          # drop refs/remotes/* whose remote branch is gone
git config --global fetch.prune true       # make it the default
git remote prune origin --dry-run          # see what would go, without fetching
```

Stale remote-tracking refs are also what make a `--force-with-lease` judgement wrong, so keeping
them pruned is a safety measure and not just tidiness.

## Discarding work

Only in response to an explicit request to throw the work away. Show exactly what will be lost and
require an unambiguous confirmation before running anything:

```
This will permanently delete:
- branch <name>
- commits: <the list from git log --oneline <base>..<branch>>
- worktree at <path>, including <n> uncommitted files

Confirm by replying: discard
```

Then, and only then, remove the worktree and `git branch -D`. Mention that the commits remain in
the reflog for 30 days by default (`gc.reflogExpireUnreachable`), so the deletion is reversible for
a while — and that uncommitted files in the worktree are not, which is why they are listed
separately.

<!-- sources: obra-finishing, obra-worktrees, parham-worktree, getsentry-commit, git-docs -->
