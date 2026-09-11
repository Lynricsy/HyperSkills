# History rewrite guardrails

Verified against: git 2.55.0

## Contents

- [When a rewrite is off the table](#when-a-rewrite-is-off-the-table)
- [What a rewrite changes that people do not expect](#what-a-rewrite-changes-that-people-do-not-expect)
- [The lease is weaker than it looks](#the-lease-is-weaker-than-it-looks)
- [`--force-if-includes`](#--force-if-includes)
- [Pinning the lease by hand](#pinning-the-lease-by-hand)
- [After the rewrite: what collaborators must do](#after-the-rewrite-what-collaborators-must-do)
- [Removing a file from all of history](#removing-a-file-from-all-of-history)
- [filter-branch leftovers](#filter-branch-leftovers)
- [The rewrite checklist](#the-rewrite-checklist)

## When a rewrite is off the table

Rewriting means replacing commits with new SHAs. That is fine for work only you have and
catastrophic for work other people or systems reference.

Never rewrite:

- the default branch, a release branch, or any branch a ruleset protects;
- a tag that has been pushed — a tag is a promise about an exact commit, and moving one gives two
  people different code under the same name;
- a branch someone else has checked out, is reviewing, or has built from, unless they have agreed
  and are standing by to reset;
- anything a deploy, a lockfile, a submodule gitlink or an external build pins by SHA.

A topic branch that only you have is fair game, and cleaning it up before review is good
practice. "Only you have it" includes CI: a rewrite invalidates every in-flight run on that ref.

Public history that is wrong gets `git revert`, not a rewrite. A revert is a new commit that
undoes the change and leaves the record of both.

## What a rewrite changes that people do not expect

Verified by rebasing two commits authored on 2020-01-01:

```
before:  c133243 a=2020-01-01 00:00:00 +0000 c=2020-01-01 00:00:00 +0000 second
after:   d7bc9e3 a=2020-01-01 00:00:00 +0000 c=2026-09-11 13:10:04 +0800 second
```

- **Author date survives; committer date resets to now.** Any report built on `%cd` — "commits per
  week", "time to merge" — is wrong after a rewrite, and everything looks like it happened today.
- **Every SHA is new**, including for commits whose content did not change, because the parent
  changed. Review comments, deploy pins and issue references that named the old SHA now point at
  nothing.
- **Signatures are dropped.** Verified with ssh signing:

  ```
  $ git log -1 --pretty='%G? %GS'        # before
  G lab@example.invalid
  $ git rebase --force-rebase HEAD~1 && git log -1 --pretty='%G? %GS'
  N                                      # unsigned
  $ git -c commit.gpgsign=true rebase --force-rebase HEAD~1 && git log -1 --pretty='%G?'
  G                                      # re-signed — by whoever ran the rebase
  ```

  `git cherry-pick` drops the signature too. So a rewrite either unsigns the history or reattributes
  the signature to the rewriter; in a repository that requires signed commits, the second is the
  only option and it means the original author's attestation is gone.
- **`git commit --amend --no-edit` is not always a rewrite.** Verified: with nothing changed and
  inside the same second, the SHA is identical; one second later the committer date differs and the
  SHA changes. Do not use an amend as a way to "touch" a commit.

## The lease is weaker than it looks

`--force-with-lease` with no value compares the remote's ref against your local
`refs/remotes/<remote>/<branch>`. That ref is updated by *any* fetch, including one you ran just to
look around — and once it matches the remote, the lease passes even though your history still does
not contain the other person's commit. Verified end to end:

```
$ git commit --amend -m "base (amended by A)"
$ git push --force-with-lease origin main
 ! [rejected]  main -> main (stale info)          <- the lease working
$ git fetch origin                                 <- informational fetch, nothing else
$ git push --force-with-lease origin main
 + e53d4da...8420192 main -> main (forced update)  <- accepted
$ git -C ../remote.git log --oneline main
8420192 base (amended by A)                        <- B's commit is gone
```

So `--force-with-lease` protects against a remote that moved *since your last fetch*, not against
a remote that moved *since you built your history*. Any `git fetch`, `git pull`, an IDE's
background fetch, or `git remote update` closes the protection window.

Also verified: with no remote-tracking ref at all the push is rejected as `stale info` rather than
waved through, so a deleted or never-fetched tracking ref fails safe.

## `--force-if-includes`

`--force-if-includes` (git 2.30+) adds the missing condition: the history being pushed must
actually contain the commit the remote-tracking ref points at. Same setup, same fetch:

```
$ git push --force-with-lease --force-if-includes origin main
 ! [rejected]  main -> main (remote ref updated since checkout)
$ git -C ../remote.git log --oneline main
e53d4da B: important work
06f5038 base                                       <- nothing lost
```

`--force-if-includes` is only meaningful together with `--force-with-lease`. Make it the default
for the whole machine, so no force-push ever relies on remembering the flag:

```bash
git config --global push.useForceIfIncludes true
```

Plain `git push --force` and any alias wrapping it (`fp = push --force`) has no lease and no
includes check at all. It overwrites whatever is on the remote. There is no situation in normal
work that needs it.

## Pinning the lease by hand

When the expected remote state is known — the SHA you fetched before you started — say so
explicitly. This is immune to later fetches:

```bash
expected=$(git rev-parse refs/remotes/origin/feat/x)   # captured before any rewriting
# ... rewrite ...
git push --force-with-lease=refs/heads/feat/x:"$expected" origin feat/x
```

## After the rewrite: what collaborators must do

State this every time a pushed branch is rewritten, because the default reaction makes it worse:

```bash
git fetch origin
git reset --hard origin/<branch>     # discards local commits on that branch
```

Not `git pull`, and not `git merge`. Either of those grafts the old and the new history together
and resurrects exactly the commits the rewrite removed, usually as duplicates. Anyone with local
work on the branch cherry-picks it onto the new tip first, or saves it with
`git branch backup/<name>` before resetting.

Verify the rewrite dropped nothing before announcing it:

```bash
git branch backup/pre-rewrite <old-tip>          # do this first, always
git range-diff <upstream> backup/pre-rewrite <new-tip>
```

Every row `=` means only the parents moved. `git log` cannot tell a clean rewrite from one that
lost a hunk during conflict resolution.

## Removing a file from all of history

A secret that has been pushed is compromised. **Rotate it first.** The rewrite limits future
exposure; it does not undo the past, because clones, forks, CI caches, backups and the forge's own
unreachable-object storage keep copies you cannot reach.

Then use `git filter-repo` (a separate install; not shipped with git):

```bash
git filter-repo --invert-paths --path deploy/creds.env
```

`filter-repo` removes the original refs and expires the reflog itself, which is most of why it is
the recommended tool `[official]` — that self-cleanup is documented rather than verified here, so
check the result against the content either way (below). `git filter-branch` still exists, prints
a deprecation warning, and leaves the old history reachable `[verified]`. `BFG Repo-Cleaner` is
the other accepted option for very large histories.

Either way, add the path to `.gitignore` in the same change, and add a secret-scanning pre-commit
hook so it cannot recur.

## filter-branch leftovers

Verified: after `git filter-branch --index-filter 'git rm --cached --ignore-unmatch secret.env'`,
the blob is still readable at the *old* commit, because `refs/original/refs/heads/main` still
points at the pre-rewrite history:

```
$ git for-each-ref refs/original --format='%(refname)'
refs/original/refs/heads/main
$ git cat-file -p "$OLD_SHA:secret.env"
token=sk_live_REDACTED
```

The cleanup is three steps, all required:

```bash
git for-each-ref --format='%(refname)' refs/original | xargs -r -n1 git update-ref -d
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now
```

Verified: after all three, `git cat-file -p "$OLD_SHA:secret.env"` fails. Skipping any one of them
leaves the secret readable to anyone with a copy of the repository. And on the forge side, the
object usually remains reachable through cached views until support prunes it — say so rather than
implying the removal is complete.

## The rewrite checklist

- [ ] The branch is unpublished, or every holder has agreed and will reset.
- [ ] `git branch backup/pre-rewrite <tip>` exists before anything else runs.
- [ ] The rewrite is done with an explicit base (`git rebase origin/main`, not a bare
      `git rebase`), so it is reproducible.
- [ ] `git range-diff <upstream> backup/pre-rewrite HEAD` shows only expected differences.
- [ ] The push uses `--force-with-lease --force-if-includes`, never bare `--force`.
- [ ] Signing status of the result is what the repository requires.
- [ ] Collaborators got the `fetch` + `reset --hard` instruction, explicitly not `pull`.
- [ ] For a secret: rotated first, path gitignored, hook added, forge asked to prune.

<!-- sources: mattpocock-guardrails, awesome-copilot-commit, addyosmani-git, git-docs -->
