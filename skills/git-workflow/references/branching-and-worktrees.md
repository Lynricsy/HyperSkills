# Branching and worktrees

Verified against: git 2.55.0

## Contents

- [Branching model](#branching-model)
- [Branch names](#branch-names)
- [Creating a branch from the right base](#creating-a-branch-from-the-right-base)
- [What a worktree actually is](#what-a-worktree-actually-is)
- [Per-worktree vs shared state](#per-worktree-vs-shared-state)
- [When a worktree beats a stash](#when-a-worktree-beats-a-stash)
- [Creating and bootstrapping a worktree](#creating-and-bootstrapping-a-worktree)
- [Detecting existing isolation](#detecting-existing-isolation)
- [Removing a worktree](#removing-a-worktree)
- [Parallel agents in one repository](#parallel-agents-in-one-repository)

## Branching model

Default to trunk-based work: one always-deployable integration branch, topic branches that live
one to three days, merged and deleted. Every extra day a branch lives is extra divergence to
reconcile later, and the cost is paid by whoever integrates, not by whoever delayed.

Incomplete work goes behind a feature flag on the trunk, not on a branch that waits for
completeness. A release branch to stabilise a shipping version while the trunk moves on is a
legitimate long-lived branch; a `develop` branch that accumulates months of work is the pattern
this advice exists to prevent.

If the repository already runs git-flow or a release-train model, keep it. The commit-level
discipline — atomic commits, small changes, messages that explain intent — carries over unchanged
and matters more than the branch topology.

## Branch names

`<type>/<short-description>`, where `<type>` is drawn from the same vocabulary as commit types
(`feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `perf`, `ci`, plus `hotfix` and `release`
where the project uses them). Keep the description kebab-case, three to six words.

Constraints that are worth knowing because they fail late rather than at creation time:

- Lowercase only, and `a-z0-9-.` only. No underscores, no spaces, no capitals.
- Dots are reserved for release versions (`release/v1.2.0`); avoid them elsewhere, and never
  produce `..`, `-.`, `.-`, `--`, or a leading/trailing `-` or `.`.
- `main`, `master` and `develop` are trunk names. Branch *off* them; never create a topic branch
  that reuses one of those names.
- `git check-ref-format --branch <name>` rejects a name git itself will not accept. Use it when
  the name is derived from a ticket title rather than typed by hand.

## Creating a branch from the right base

Detect the default branch rather than assuming `main`:

```bash
remote=$(git remote | grep -qx origin && echo origin || git remote | head -1)
base=$(git symbolic-ref "refs/remotes/$remote/HEAD" 2>/dev/null | sed "s|refs/remotes/$remote/||")
```

If that is empty — a fresh clone of some hosts never sets it — fall back in a fixed order:
`main`, then `master`, then the current branch. Do not silently switch the user off a branch they
are on: if the current branch is not the default, branch from where they are; only move to the
default branch when they asked for it.

On collision, suffix (`-2`, `-3`) rather than reusing a name that already exists locally or on the
remote. `git rev-parse --verify -q refs/heads/<name>` and `git ls-remote --exit-code --heads
origin <name>` answer both questions without a network round trip you cannot explain.

## What a worktree actually is

`git worktree add` creates a second checkout backed by the same object store. The new directory's
`.git` is a *file* pointing into `<main>/.git/worktrees/<name>`. Measured in a throwaway repo:

```
$ git -C ../wt-feat rev-parse --absolute-git-dir
/tmp/lab/main-repo/.git/worktrees/wt-feat
$ git -C ../wt-feat rev-parse --git-common-dir      # resolved to an absolute path
/tmp/lab/main-repo/.git
```

A commit made in the worktree is immediately readable from the main checkout — same objects, same
`refs/heads/*`. It costs working-tree bytes, not a second copy of history. The main checkout is
just the first row of `git worktree list`; nothing else about it is special.

## Per-worktree vs shared state

| Per worktree | Shared across all worktrees |
|---|---|
| `HEAD`, the index, the working tree | objects and packs |
| in-progress merge / rebase / cherry-pick / revert state | `refs/heads/*`, `refs/remotes/*`, tags |
| bisect state and `refs/bisect/*` | **`refs/stash`** |
| `refs/worktree/*` | hooks (`core.hooksPath` / `.git/hooks`) |
| that worktree's own reflog | the repository `config` (unless `extensions.worktreeConfig=true`) |

`refs/stash` being shared is the one that bites. Verified: a `git stash` run inside a linked
worktree appears in `git stash list` in the main checkout at the same SHA. Two agents stashing in
two worktrees are pushing onto one stack and will pop each other's work. In a parallel setup,
commit instead of stashing.

A branch can be checked out in exactly one worktree at a time:

```
$ git checkout feat
fatal: 'feat' is already used by worktree at '/tmp/lab/wt-feat'
```

That is a feature, not an obstacle — it makes "which directory is that branch in?" answerable by
`git worktree list`.

## When a worktree beats a stash

| Situation | Do this |
|---|---|
| Second unrelated task arrives while the tree is dirty | new worktree — the in-progress change keeps its exact state |
| Urgent fix on the trunk mid-feature | new worktree off `origin/<default>` |
| Reviewing someone else's branch while yours stays running | new worktree |
| A long test run or dev server is pinning the checkout | new worktree for the edits |
| Bisecting while continuing to work | new worktree — bisect state is per-worktree |
| Several agents editing in parallel | one worktree per agent |
| Same branch, one small fix, clean tree | just commit; a worktree is pure overhead |
| Read-only peek at another branch | `git show <branch>:<path>`, no checkout at all |
| A stack of dependent commits on one topic | one branch, one worktree — dependent work is not parallel work |

Rule of thumb: work that would land in two separate reviews deserves two worktrees; work that
would land in one does not.

## Creating and bootstrapping a worktree

```bash
git worktree add ../<repo>-<slug> -b <type>/<slug>      # siblings of the repo
git worktree add .worktrees/<slug>  -b <type>/<slug>    # nested, must be ignored
```

Pick one layout per repository and keep it. If the worktree directory lives inside the repository,
confirm it is ignored *before* creating anything — an unignored `.worktrees/` commits an entire
second checkout into the repository:

```bash
git check-ignore -q .worktrees || echo "add .worktrees/ to .gitignore first"
```

Untracked and ignored files do not come along. A fresh worktree has no `.env`, no `node_modules`,
no `.venv`, no `target/`, no build cache. Budget one setup step per worktree — install
dependencies, copy the local env file, then run the test suite once to establish a clean baseline.
A test failure discovered after three commits is ambiguous; the same failure on a fresh baseline
is information.

If the harness provides its own worktree mechanism, use that instead of `git worktree add`: a
worktree git created is invisible to a harness that tracks its own, and the divergence shows up
later as a workspace nobody owns. If `git worktree add` fails with a permission error under a
sandbox, say so and work in place rather than retrying variations.

## Detecting existing isolation

Before creating anything, find out whether you are already in a linked worktree:

```bash
git_dir=$(cd "$(git rev-parse --git-dir)" && pwd -P)
common=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
```

`git_dir != common` means a linked worktree — *or* a submodule, which produces the same
inequality. Rule that out before concluding anything:

```bash
git rev-parse --show-superproject-working-tree   # non-empty => submodule, treat as a normal repo
```

A detached HEAD inside a linked worktree usually means the workspace is externally managed: work
there, but leave its lifecycle alone and name a branch at finish time.

## Removing a worktree

Always `git worktree remove <path>`. Deleting the directory by hand leaves the administrative
directory and the branch lock behind — verified:

```
$ rm -rf ../wt-feat
$ git worktree list
/tmp/lab/main-repo  14fd24d [main]
/tmp/lab/wt-feat    dfa7ecd [feat] prunable
$ git branch -d feat
error: cannot delete branch 'feat' used by worktree at '/tmp/lab/wt-feat'
$ git worktree prune && git branch -d feat      # now it works
```

A refused removal is information, not an obstacle:

```
fatal: '../wt-feat' contains modified or untracked files, use --force to delete it
```

It means files exist in that directory and nowhere else. Show `git -C <path> status --porcelain
-uall`, and let the user choose between committing them, moving them out, and deleting them.
`--force` on your own initiative destroys work that has no other copy.

One more asymmetry: the worktree's reflog dies with its administrative directory. Delete the
worktree and then the branch, and there is no local record of where the branch pointed — the
commits are unreachable and the usual `HEAD@{n}` recovery route is gone. Delete the branch first,
while the worktree still exists, or note the SHA.

## Parallel agents in one repository

- One branch and one worktree per agent, created up front with `-b` so no two agents contend for
  a branch.
- No stashing. `refs/stash` is shared; a commit is per-branch and therefore safe.
- Do the large mechanical change first — a rename that lands after ten branches have forked off it
  is the conflict that stays expensive no matter how good the conflict handling is.
- The merge back is best done by whoever wrote the change, because reconstructing intent is the
  expensive half of conflict resolution and that agent still has it.
- `git worktree list --porcelain` is the inventory; `git worktree prune` after any manual cleanup.

<!-- sources: obra-worktrees, obra-finishing, parham-worktree, addyosmani-git, awesome-copilot-branch, getsentry-commit, mattpocock-conflicts, git-docs -->
