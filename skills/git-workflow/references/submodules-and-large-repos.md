# Submodules, subtrees and large repositories

Verified against: git 2.55.0

## Contents

- [Submodule or subtree](#submodule-or-subtree)
- [What a submodule actually stores](#what-a-submodule-actually-stores)
- [The unpushed-gitlink accident](#the-unpushed-gitlink-accident)
- [Everyday submodule commands](#everyday-submodule-commands)
- [Submodules and branch switching](#submodules-and-branch-switching)
- [Subtree](#subtree)
- [Sparse checkout](#sparse-checkout)
- [Partial and shallow clones](#partial-and-shallow-clones)
- [Keeping a large repository fast](#keeping-a-large-repository-fast)

## Submodule or subtree

| | submodule | subtree |
|---|---|---|
| What the superproject stores | a pointer (gitlink) to one commit | the files themselves |
| Clone | needs `--recurse-submodules` or a follow-up command | just works |
| Consumers need to know | yes | no |
| Upstream history | stays separate | merged in, or squashed |
| Sending a change upstream | commit in the submodule, push it, then bump | `git subtree push` |
| Repository size | small | grows by the vendored history |

Choose a submodule when the dependency has its own release cycle and the people using the
superproject are expected to know it exists. Choose a subtree when consumers should be able to
clone and build with no extra steps. Neither is a substitute for a package manager: if the
dependency has a registry, use the registry.

## What a submodule actually stores

One tree entry of mode `160000`:

```
$ git ls-tree HEAD libs/sub
160000 commit c51ceab794e5a7681a21446df36f04aec76cce9a	libs/sub
```

That is a commit SHA and nothing else — no branch, no remote, no version range. `.gitmodules`
records the URL and the path, but the *version* is only ever that SHA.

Consequently `git submodule update` checks out a detached HEAD inside the submodule. Work done
there without first creating a branch is one `git submodule update` away from being unreachable.

## The unpushed-gitlink accident

This is the failure that costs a team an afternoon. Commit in the submodule, bump the gitlink in
the superproject, push the superproject, forget to push the submodule — everyone else's
`git submodule update` fails on an object that exists on exactly one machine. Verified:

```
$ git -C libs/sub log -1 --oneline
c5b1a36 sub: local only
$ git -C libs/sub branch -r --contains HEAD
                                        <- on no remote branch
$ git push origin main                  <- plain push: accepted
   0ac24f4..b751f37  main -> main       <- superproject now points at a private commit
```

`--recurse-submodules=check` catches it:

```
$ git push --recurse-submodules=check origin main
The following submodule paths contain changes that can
not be found on any remote:
  libs/sub
...
fatal: Aborting.
```

Make it the default in any repository with submodules — the check costs nothing and the failure it
prevents is remote:

```bash
git config push.recurseSubmodules check       # or on-demand, to push them for you
```

`on-demand` pushes the submodule first and then the superproject. `check` refuses and tells you.
Both are fine; the default (`no`) is what lets the broken state out.

## Everyday submodule commands

```bash
git clone --recurse-submodules <url>                # clone and populate in one step
git submodule update --init --recursive             # after a clone that forgot
git submodule update --init --recursive --depth 1   # CI: skip the submodule's history

git -C <path> switch -c <branch>                    # before working in a submodule
git -C <path> commit -am '...' && git -C <path> push
git add <path> && git commit -m 'chore: bump <path>' # record the new gitlink

git submodule status --recursive                    # '+' = checked out ≠ recorded gitlink
git diff --submodule=log                            # what the bump actually contains
git submodule foreach 'git status --short'          # sweep every submodule
```

`git submodule update --remote` moves the gitlink to the tip of the *tracked branch* rather than to
the recorded commit. That is an upgrade, not a sync — it changes what the superproject points at
and needs a commit and a reason.

`git submodule status` showing `+` means the working tree has a different commit checked out than
the superproject records. Reading that as "dirty" and running `git submodule update` silently
discards whatever was done in there.

## Submodules and branch switching

`git checkout` does not update submodule contents unless told to:

```bash
git config --global submodule.recurse true    # make checkout/pull/switch follow submodules
```

Without it, switching between two branches that record different gitlinks leaves the submodule at
the old commit while the superproject says otherwise — and the resulting build failure looks like
a code problem. With it, `git checkout` updates submodules the same way it updates files.

Removing a submodule takes three steps, and skipping any one leaves debris:

```bash
git submodule deinit -f <path>      # clear it from .git/config and empty the directory
git rm <path>                       # remove the gitlink and the .gitmodules entry
rm -rf .git/modules/<path>          # the submodule's own git directory, kept for reuse
```

## Subtree

`git subtree` ships with git (verified present as `/usr/lib/git-core/git-subtree` on 2.55.0, though
its man page is packaged separately on some distributions, so `git subtree --help` may fail while
the command works).

```bash
git subtree add    --prefix=vendor/lib <url> main --squash
git subtree pull   --prefix=vendor/lib <url> main --squash
git subtree push   --prefix=vendor/lib <url> my-changes
```

Verified result of an `add --squash`:

```
$ git log --graph --oneline
*   98944b2 Merge commit '3a3f675...' as 'vendor/lib'
|\
| * 3a3f675 Squashed 'vendor/lib/' content from commit 89411fd
* 42996bd base
```

`--squash` keeps the vendored project's history out of yours; it is almost always the right choice,
and it must be used consistently — mixing squashed and unsquashed pulls on the same prefix produces
merges git cannot reconcile. The upstream commit named in the squash message is the only record of
which version is vendored, so do not reword it.

## Sparse checkout

Populate part of a large repository's working tree while the index still tracks everything:

```bash
git sparse-checkout init --cone        # cone mode: directory-level, fast
git sparse-checkout set app libs/ui
git sparse-checkout add tools
git sparse-checkout list
git sparse-checkout disable            # back to a full checkout
```

Verified: after `git sparse-checkout set --cone app`, only `app/` exists on disk, the index still
lists `docs/d`, and the excluded paths carry the skip-worktree bit:

```
$ git ls-files -v | grep -v '^H'
S docs/d
```

The `S` flag is the thing to know. Excluded files are still tracked, so:

- a commit still includes them at their existing content — a sparse checkout does not narrow what
  you can accidentally change;
- a tool that writes to an excluded path creates a file git treats as modified-but-skipped, and
  the change is invisible in `git status` until the skip bit is cleared;
- `git grep` and `git log -S` still search the full index, which is usually what you want.

Non-cone mode accepts arbitrary gitignore-style patterns and is much slower on large repositories.
Use cone mode unless a pattern is genuinely required.

## Partial and shallow clones

```bash
git clone --filter=blob:none <url>        # partial: history, no file contents until needed
git clone --depth 1 <url>                 # shallow: one commit, no history
git fetch --unshallow                     # convert a shallow clone to complete
```

A partial clone fetches blobs on demand, so `git log` is fast and `git blame` triggers network
traffic. A shallow clone has no merge base with anything, so `git merge-base`, `git bisect`,
`git blame` and `git describe` are all either wrong or impossible in one. Shallow is for CI; a
partial clone is the better default for a human working in a large repository.

`git rev-parse --is-shallow-repository` answers "why does bisect say the good commit is not an
ancestor" in one command.

## Keeping a large repository fast

```bash
git maintenance run --task=commit-graph   # writes .git/objects/info/commit-graph*
git maintenance start                     # schedule background maintenance
git commit-graph write --reachable
git config core.fsmonitor true            # built-in filesystem monitor
git config feature.manyFiles true         # index v4 + untracked cache
```

Verified: `git maintenance run --task=commit-graph` produced a commit-graph chain in a throwaway
repository. A commit graph is what makes `git log --graph` and merge-base queries fast on a large
history; it is derived data and safe to delete.

`git maintenance start` writes a schedule into the user's global configuration and their system
scheduler `[official]` — not run here, precisely because it would change this machine. That is a
change outside the repository, so mention it before running it, and prefer `git maintenance run`
for a one-off.

Avoid `git gc --aggressive` as routine advice: it repacks everything from scratch, takes a long
time on a large repository, and the ordinary `git gc` (or `git maintenance`) achieves nearly the
same result incrementally.

<!-- sources: addyosmani-git, parham-worktree, git-docs -->
