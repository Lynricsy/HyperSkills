# Conflict resolution

Verified against: git 2.55.0

## Contents

- [Inventory before editing](#inventory-before-editing)
- [Which side is which](#which-side-is-which)
- [Recovering both intents](#recovering-both-intents)
- [Conflict presentation: merge, diff3, zdiff3](#conflict-presentation-merge-diff3-zdiff3)
- [Reading the three stages directly](#reading-the-three-stages-directly)
- [Resolving a hunk](#resolving-a-hunk)
- [rerere: what it does and how it misleads](#rerere-what-it-does-and-how-it-misleads)
- [Rename and move conflicts](#rename-and-move-conflicts)
- [Semantic conflicts the markers never show](#semantic-conflicts-the-markers-never-show)
- [Finishing](#finishing)

## Inventory before editing

Enumerate every unmerged path first, and identify which operation stopped. They need different
commands, and guessing produces silently empty output.

```bash
git status --short --branch          # the in-progress banner is in the header
git diff --name-only --diff-filter=U # the complete unmerged list
git ls-files -u                      # the same list with all three stages and their blob SHAs
```

| Operation | Counterpart ref |
|---|---|
| merge | `MERGE_HEAD` |
| rebase | `REBASE_HEAD` |
| cherry-pick | `CHERRY_PICK_HEAD` |
| revert | `REVERT_HEAD` |

Every path on the unmerged list gets a recorded decision. A path that stopped showing markers
because a tool touched it is still unmerged until the index says otherwise.

## Which side is which

The labels invert, and reading them the same way in both operations is how the wrong side gets
kept.

| | `ours` / stage 2 / `<<<<<<< HEAD` | `theirs` / stage 3 |
|---|---|---|
| merge | your branch | the branch being merged in |
| rebase | the upstream you are replaying onto | **your own commit being replayed** |
| cherry-pick | the branch you are on | the commit being picked |
| revert | the branch you are on | the inverse of the reverted commit |

During a rebase, `git checkout --ours <path>` throws away your own work. That is the single most
expensive misreading in this document.

## Recovering both intents

Resolve between two intents, not two blocks of text. Before touching a hunk, read why each side
exists — the commit, and whatever it references.

```bash
base=$(git merge-base HEAD MERGE_HEAD)            # substitute the right counterpart ref
git log --oneline "$base"..HEAD       -- <path>   # what this side did, and why
git log -p        "$base"..MERGE_HEAD -- <path>   # the incoming side, all of it
```

`git show MERGE_HEAD -- <path>` looks like a shortcut and is a trap: it shows only the tip commit,
so it prints nothing at all when an earlier commit on the incoming branch is the one that touched
the path. For rebase, cherry-pick and revert, the counterpart ref *is* the single commit in
question, so `git show REBASE_HEAD -- <path>` is correct there.

If `git merge-base` returns nothing, do not interpolate the empty value into a range. Inspect the
counterpart ref plus `git log --all --oneline -- <path>`, and ask rather than guess.

## Conflict presentation: merge, diff3, zdiff3

The default `merge` style shows two sides and hides the merge base, so "which side changed what"
is unanswerable from the file alone. Verified on one three-way conflict:

```
merge                    diff3                      zdiff3
-------------------      --------------------       --------------------
header                   header                     header
SHARED                   <<<<<<< HEAD               SHARED
<<<<<<< HEAD             SHARED                     <<<<<<< HEAD
main-only                main-only                  main-only
=======                  SHARED-TAIL                ||||||| 848a9a9
side-only                ||||||| 848a9a9            OLD
>>>>>>> side             OLD                        =======
SHARED-TAIL              =======                    side-only
footer                   SHARED                     >>>>>>> side
                         side-only                  SHARED-TAIL
                         SHARED-TAIL                footer
                         >>>>>>> side
                         footer
```

`diff3` adds the base but pulls the lines both sides share back inside the markers, duplicating
them. `zdiff3` (git 2.35+) keeps the base *and* hoists the shared lines out, so the region between
the markers is only what actually differs. Prefer it:

```bash
git config --global merge.conflictstyle zdiff3
```

Changing the config does not rewrite files already conflicted. `git checkout --merge <path>`
regenerates the markers for that path under the current style.

## Reading the three stages directly

The index holds all three inputs while a path is unmerged, which is the reliable way to see the
base even under the two-way style:

```bash
git show :1:<path>   # merge base
git show :2:<path>   # ours
git show :3:<path>   # theirs
git diff --base  <path>   # both sides against the base
git diff --ours  <path>
git diff --theirs <path>
```

`git ls-files -u <path>` prints the stage numbers and blob SHAs; a path with only stages 1 and 2,
or 1 and 3, is a delete/modify conflict, not a content conflict, and needs a decision about
whether the file should exist at all.

## Resolving a hunk

1. State each side's intent in one sentence. If you cannot, you have not read enough history.
2. Compose both where they are compatible. Two independent improvements to the same function are
   the common case, and keeping both is the correct answer, not a compromise.
3. Where they are genuinely incompatible, keep the side matching the stated goal of the
   integration and say in the commit message what was dropped and why.
4. Invent nothing. A third behaviour that was on neither branch is a new change smuggled in under
   a merge, and it will not be reviewed.
5. `git add <path>` only after the file is in its final state. The index is the record of what you
   decided.

`-X ours` / `-X theirs` on the merge command, and `git checkout --ours/--theirs`, are not
resolution. They are a bulk instruction to delete one side's work without reading it. Use them
only for a file whose content is genuinely generated (a lockfile you will regenerate, a compiled
asset), and regenerate it immediately afterwards.

## rerere: what it does and how it misleads

`rerere.enabled=true` records how you resolved a conflict and replays it when the same conflict
text appears again. It is genuinely useful across a repeated rebase. It also produces two states
that look like nothing else in git.

**Replayed but unstaged.** Verified: after re-running the same merge, git says
`Resolved 'f.txt' using previous resolution.`, the file has no conflict markers, and:

```
$ git status --porcelain
UU f.txt
```

An agent that greps for `<<<<<<<` concludes the tree is clean; the index says the path is unmerged.
Both are right. The resolution came from cache and nobody has reviewed it.

**Replayed and staged.** With `rerere.autoupdate=true` the same run reports `Staged 'f.txt' using
previous resolution.` and `git status --porcelain` shows `M  f.txt` — no conflict at all. A
`git commit` at that point seals a resolution that was never read, on a conflict that may only
*look* like the one recorded. Verified: a resolution recorded on one merge was replayed onto a
different branch's conflict with the same marker text, unchanged and unremarked.

So: when `rerere` is enabled, always diff what it produced before committing.

```bash
git rerere status        # paths rerere is tracking in this operation
git rerere diff          # the resolution it applied, as a diff
git rerere forget <path> # drop the recorded resolution for this conflict
```

`git rerere forget` clears the cache but does **not** restore the conflict. Verified: after
`Forgot resolution for 'f'`, the working file still held the cached (wrong) content. The command
that brings the markers back is:

```
$ git checkout --merge f
Recreated 1 merge conflict
```

## Rename and move conflicts

A large rename landing on one side and edits landing on the other is the expensive case. Two
knobs matter:

- **Rename detection is capped.** `merge.renameLimit` (and `diff.renameLimit`) bound how many
  candidate pairs git will consider; past the cap it stops detecting renames and reports the
  conflict as "deleted on one side, added on the other", which loses the edits on the other side
  unless you notice. Git prints a warning when it gives up — read it. Raise the limit for that
  one merge rather than globally.
- **Find the counterpart yourself** when detection failed: `git log --follow -- <old-path>`, and
  `git diff -M --find-copies-harder <base> <side> -- <dir>` to see what moved where. Then apply
  the other side's edits to the new path by hand.

Prefer sequencing over cleverness: land the rename first, on its own commit, and rebase the
outstanding branches immediately. A rename that sits unmerged while ten branches fork off the old
layout is the one conflict that does not get cheaper with better tooling.

## Semantic conflicts the markers never show

A merge can be textually clean and still broken, because each side changed something the other
side depends on: a renamed function whose new callers arrived on the other branch, a changed
default, a narrowed type, a migration that now runs in the wrong order, two independent additions
to the same enum or dependency list.

After every resolution, sweep for them: search the merged tree for the identifiers each side
introduced or removed, and run the project's checks. A merge is the easiest place in git to
produce code that satisfies both branches and passes neither's tests.

## Finishing

```bash
git add <each resolved path>
git status --short          # no UU, no leftover stages
git diff --check            # no stray conflict markers committed
<project typecheck> && <project tests> && <project formatter>
git commit                  # keeps the generated merge message; add what was dropped and why
git rebase --continue       # rebase instead: repeat for every remaining commit
```

Do not stop at the first resolved commit of a multi-commit rebase — the operation is unfinished
until `git status` says so. And do not reach for `--abort` because the resolution got hard: that
throws away the decisions and hands the same conflict back next time. Abort only when the
integration itself is the wrong move.

<!-- sources: mattpocock-conflicts, melodic-resolve, git-docs -->
