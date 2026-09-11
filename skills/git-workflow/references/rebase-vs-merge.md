# Rebase, merge, and keeping a branch current

Verified against: git 2.55.0

## Contents

- [Choosing between them](#choosing-between-them)
- [Keeping a topic branch current](#keeping-a-topic-branch-current)
- [Stacked branches and `--update-refs`](#stacked-branches-and---update-refs)
- [Rebasing a branch that contains merges](#rebasing-a-branch-that-contains-merges)
- [`--fork-point` and why it is unreliable](#--fork-point-and-why-it-is-unreliable)
- [autostash: the failure that looks like success](#autostash-the-failure-that-looks-like-success)
- [`--autosquash` and fixup commits](#--autosquash-and-fixup-commits)
- [Proving a rebase changed nothing](#proving-a-rebase-changed-nothing)
- [Squash merge and what it costs](#squash-merge-and-what-it-costs)
- [Aborting and resuming](#aborting-and-resuming)

## Choosing between them

The decision is about who pays, not about which history looks nicer.

| | `git merge` | `git rebase` |
|---|---|---|
| Commit identity | preserved | every replayed commit gets a new SHA |
| Conflicts | resolved once, against the combined tree | potentially once per replayed commit |
| Signatures | preserved | dropped unless re-signed |
| Safe on a branch others have | yes | only if nobody else has it |
| Bisect quality | merge commits can hide which side broke | linear, one change per step |
| Result | records that integration happened, and when | records the work as if it were written after the upstream |

Defaults worth applying without discussion:

- **Rebase your own unpushed or topic-only branch** onto the updated trunk. It keeps review focused
  on the change rather than on sync noise.
- **Merge into the trunk**, never rebase the trunk. The trunk is published by definition.
- **Merge, do not rebase, a branch that anyone else has checked out.** A rebase hands them a
  history that no longer contains the commits they have, and their next `git pull` either creates a
  duplicate-commit mess or a merge of two versions of the same work.
- **Merge when the conflict is the same in every commit.** Replaying twelve commits through one
  conflict twelve times is not discipline, it is waste; `git merge` resolves it once.

## Keeping a topic branch current

```bash
git fetch origin
git rebase origin/<default>          # own topic branch
git merge origin/<default>           # shared branch, or conflict-heavy sync
```

Do not use `git pull` to do this. With `pull.rebase=false` (the default) it produces a merge commit
whose message nobody wrote, and with `pull.rebase=true` it rebases whatever happens to be local
including commits you had not looked at. `git fetch` followed by an explicit `rebase` or `merge` is
the same work with the decision visible.

`git merge --ff-only origin/<default>` is the right way to say "advance if you can, tell me if you
cannot" — it fails instead of inventing a merge.

## Stacked branches and `--update-refs`

Rebasing the tip of a stack silently orphans the branches underneath it. Verified on a chain
`main -> featA -> featB`, rebasing `featB` onto a moved `main`:

```
$ git rebase main            # from featB
73ca66f (HEAD -> featB) B
eb40025 A                    <- featA is NOT here
6ec085b (main) main moves
$ git log -1 --pretty='%h %s' featA
5287d1c A                    <- still on the old, pre-rebase commit
```

With `--update-refs` (git 2.38+) the intermediate branch is carried along:

```
$ git rebase --update-refs main
73ca66f (HEAD -> featB) B
eb40025 (featA) A
6ec085b (main) main moves
```

Set `rebase.updateRefs=true` in a repository where stacking is the working style. Without it, every
stack rebase needs a manual `git branch -f` pass, and the branch that gets forgotten is the one
someone else is reviewing.

## Rebasing a branch that contains merges

A plain rebase flattens merge commits out of existence. `git rebase --rebase-merges` recreates
them. Decide which you want before running anything:

- The merge was a *sync* from the trunk (`Merge branch 'main' into feat/x`): flatten it. Rebasing
  onto the new trunk makes the sync meaningless, and keeping it produces a merge of a commit into
  its own descendant.
- The merge joined two real lines of development whose separation carries meaning: `--rebase-merges`,
  and check the result with `git log --graph` before pushing.

## `--fork-point` and why it is unreliable

`git merge-base --fork-point <upstream> <branch>` consults the *reflog* of the upstream ref to find
where the branch actually forked, which lets it tolerate an upstream that was itself rewritten.
Verified: after amending `main`, plain `merge-base` finds nothing while `--fork-point` still answers:

```
$ git merge-base main topic
                       (empty)
$ git merge-base --fork-point main topic
9357ea56
```

The catch is in the mechanism. A reflog is local and per-clone, so `--fork-point` returns nothing in
a fresh clone and nothing in CI. `git rebase` applies fork-point logic by default when no explicit
`<upstream>` is given, which is why the same rebase can behave differently on your machine and on a
build agent. Pass the base explicitly — `git rebase origin/main` or `git rebase --onto` — whenever
the result has to be reproducible.

## autostash: the failure that looks like success

`rebase.autoStash=true` stashes a dirty tree, rebases, and re-applies. When the re-application
conflicts, the rebase still reports success. Verified transcript:

```
$ git -c rebase.autoStash=true rebase main
Rebasing (1/1)
Your local changes are stashed, however applying them
resulted in conflicts. ...
Successfully rebased and updated refs/heads/topic.
$ git status --porcelain
UU a
$ git stash list
stash@{0}: autostash
```

The rebase is finished, so `git rebase --abort` has nothing to abort; the conflict markers in the
tree come from the stash application, and the autostash entry is still on the stack. Treat
"Successfully rebased" as a statement about the commits only — check `git status` afterwards, and
either resolve and `git stash drop`, or `git reset --hard` and `git stash pop` later. Committing a
clean tree before a rebase avoids the whole situation.

## `--autosquash` and fixup commits

`git commit --fixup=<sha>` and `--squash=<sha>` write messages (`fixup! <subject>`) that
`--autosquash` reorders onto their target. It works non-interactively; there is no need to open an
editor. Verified:

```
$ git log --oneline
9676cb0 fixup! feat: thing
9552af8 other
b900865 feat: thing
$ git rebase --autosquash --root
Successfully rebased and updated refs/heads/main.
$ git log --oneline
6fe88de other
fb929ed feat: thing            <- fixup folded in, across the intervening commit
```

`rebase.autosquash` is off by default on git 2.55.0 — a plain `git rebase --root` on the same repo
leaves `fixup! feat: thing` standing as its own commit. So the flag (or the config) is required;
assuming the default cleans up fixups is how they reach review.

## Proving a rebase changed nothing

`git range-diff` compares two versions of the same series and is the only cheap way to show a
rewrite preserved the work. Tag the old tip first (`git branch topic-old`), rebase, then:

```
$ git range-diff main topic-old topic
1:  65ac435 = 1:  33b89e3 t1
2:  cf41e59 = 2:  4799bd9 t2
```

`=` on every row means the patches are identical and only the parents moved. Anything else is
flagged; after amending one message the same command reports:

```
2:  cf41e59 ! 2:  fb86441 t2
    @@ Metadata
     ## Commit message ##
    -    t2
    +    t2 (message changed)
```

Make this the gate on every rewrite you hand back. `git log` cannot tell the difference between a
clean rebase and one that dropped a hunk during conflict resolution; `range-diff` can.

## Squash merge and what it costs

`git merge --squash <branch>` stages the combined change and leaves the commit to you; the result
has no parent link to the branch. Two consequences to state out loud before using it:

- `git branch --merged` will never report that branch as merged, because none of its SHAs appear in
  the trunk. Verified: a squash-merged branch shows up under `git branch --no-merged main`. Use
  `git cherry -v main <branch>` instead — it compares patch-ids, and prints `-` for a patch that is
  already upstream.
- Bisect resolution collapses to the whole branch. If the branch is large, the squash is the reason
  a future bisect lands on a 900-line commit.

Squash a branch whose internal history is noise (`wip`, `asdf`, `fix lint`). Keep the history of a
branch whose commits were built to be read one at a time.

## Aborting and resuming

| State | Continue | Give up |
|---|---|---|
| rebase | `git rebase --continue` | `git rebase --abort` |
| merge | `git commit` | `git merge --abort` |
| cherry-pick | `git cherry-pick --continue` | `git cherry-pick --abort` |
| revert | `git revert --continue` | `git revert --abort` |

`--abort` restores the pre-operation state including the working tree, so it is safe — but it also
discards every resolution decision made so far, and the same conflict returns next time. Abort
because the integration itself is the wrong move, not because the resolution got hard.

`ORIG_HEAD` is set by rebase, merge, reset and pull to the pre-operation tip. `git reset --hard
ORIG_HEAD` is the undo for an operation that already completed — but only for the most recent one,
since the next operation overwrites it. For anything older, use the reflog.

<!-- sources: addyosmani-git, mattpocock-conflicts, obra-finishing, git-docs -->
