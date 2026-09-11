# Bisect and history archaeology

Verified against: git 2.55.0

## Contents

- [Bisect: the manual loop](#bisect-the-manual-loop)
- [`git bisect run` exit codes](#git-bisect-run-exit-codes)
- [Writing the test script](#writing-the-test-script)
- [Skipping untestable commits](#skipping-untestable-commits)
- [Custom terms](#custom-terms)
- [Bisecting with merges in range](#bisecting-with-merges-in-range)
- [Bisect in a worktree](#bisect-in-a-worktree)
- [Recording and replaying a bisect](#recording-and-replaying-a-bisect)
- [Finding a change without bisecting](#finding-a-change-without-bisecting)
- [Blame that survives moves and reformatting](#blame-that-survives-moves-and-reformatting)
- [Has this patch already landed?](#has-this-patch-already-landed)

## Bisect: the manual loop

```bash
git bisect start <known-bad> <known-good>    # order matters: bad first
# git checks out a midpoint
<run the check>
git bisect good        # or: git bisect bad
# ...repeat
git bisect reset       # always, when done — it returns you to where you started
```

`git bisect start` with no arguments then `git bisect bad` / `git bisect good <sha>` is equivalent.
The known-good commit has to be an ancestor of the known-bad one; if it is not, git says so rather
than silently searching the wrong range.

Forgetting `git bisect reset` leaves the repository on a detached HEAD in a bisect session, and
every later command behaves confusingly. Make it the last step, including on failure.

## `git bisect run` exit codes

Automate the loop with a script. The exit-code contract is not the usual one, and the documented
contract and the observed behaviour do not fully agree:

| Exit code | Documented | Observed on git 2.55.0 |
|---|---|---|
| `0` | good | good |
| `1`–`124` | bad | bad |
| `125` | untestable — skip this commit | skip |
| `126`, `127` | bad ("normal errors in the script") | rejected as `bogus exit code`, and the run continues on to another commit |
| `128`–`255`, negative | abort the run | the run stops, but the bisect session stays open |

126 and 127 are what a POSIX shell returns for "found but not executable" and "command not
found" — that is, exactly what a typo in the script path produces. Verified:

```
$ git bisect run /tmp/nope.sh             # shell exits 127
/tmp/nope.sh: No such file or directory
error: bogus exit code 127 for 'good' revision
[e09481c...] c4                           <- bisect KEEPS GOING
$ git bisect log >/dev/null && echo active
active
```

Exit 126 produces the identical message. So a broken test script does not stop the run; it walks
the range printing errors and leaves a session whose conclusion cannot be trusted. Run the script
by hand on a known-good and a known-bad commit before handing it to `git bisect run`, and treat
any `bogus exit code` line as a reason to reset and start over.

An out-of-range code stops the run but does not clean up:

```
$ git bisect run /tmp/exit-128.sh
error: bisect run failed: exit code 128 from '/tmp/exit-128.sh' is < 0 or >= 128
$ git bisect log >/dev/null && echo active
active                                     <- session still open, HEAD still detached
```

`git bisect reset` is required before anything else in the repository will make sense.

## Writing the test script

```bash
#!/bin/sh
# Exit 125 for a commit this test cannot judge, so bisect skips instead of guessing.
command -v node >/dev/null || exit 125
npm ci --silent   || exit 125     # dependency graph broken at this commit: untestable, not bad
node --test test/rates.test.js    # 0 => good, non-zero => bad
```

Rules that keep the result trustworthy:

- Test the *one* symptom, not the suite. A flaky unrelated test turns every commit bad.
- Return 125, never 1, when the commit cannot be built or installed. Marking an unbuildable commit
  bad shifts the answer to the wrong place.
- Keep the script outside the repository (or in `/tmp`), because a checked-out midpoint may not
  contain it.
- Make it deterministic and fast. Bisect runs it about log2(n) times; a 3-minute script over 4000
  commits is 36 minutes of waiting.

## Skipping untestable commits

`git bisect skip` marks the current commit untestable by hand, and `git bisect skip <rev>..<rev>`
a whole range. When the culprit can only be narrowed to a set of skipped commits, git says so
rather than guessing:

```
$ git bisect run ./test-with-skip.sh
There are only 'skip'ped commits left to test.
```

That output is the answer, not a failure — report the candidate range and why those commits could
not be tested.

## Custom terms

`good`/`bad` reads backwards when bisecting a *fix* or a performance improvement. Rename them:

```bash
git bisect start --term-new=fast --term-old=slow
git bisect fast        # or: git bisect slow
```

`git bisect terms` prints the current pair. Stick to one pair per session; mixing the vocabularies
produces an error, not a silent mix.

## Bisecting with merges in range

Bisect walks all reachable commits, including both sides of every merge, so a midpoint can be a
commit from a side branch that was never a state anyone shipped. That is usually what you want —
the bug was introduced somewhere, and that somewhere is on a branch.

If those midpoints genuinely cannot be built, bound the range with `--first-parent` so only trunk
commits are considered:

```bash
git bisect start --first-parent <bad> <good>
```

The result is then "the merge that brought the bug in" rather than the commit that wrote it. Say
which of the two you found, because the follow-up differs: a merge points at a branch to inspect,
a commit points at a diff.

## Bisect in a worktree

Bisect state and `refs/bisect/*` are per-worktree, so a bisect can run in a linked worktree while
you keep working in the main checkout. This is the clean way to bisect a long build: one worktree
bisecting, one worktree for the fix. It is also why a bisect left active in a removed worktree
disappears with it.

## Recording and replaying a bisect

```bash
git bisect log > /tmp/bisect.log     # the full sequence of good/bad/skip decisions
git bisect reset
git bisect replay /tmp/bisect.log    # resume exactly where it left off
```

Save the log before resetting an interesting bisect. It is also the artefact to hand back when
reporting a result: it shows exactly which commits were judged and how.

## Finding a change without bisecting

Bisect answers "which commit changed behaviour". When the question is "which commit touched this
text", these are faster and need no build:

```bash
git log -S'verify_signature' --oneline -- src/          # commits that changed the count of it
git log -G'cache\.set\(' --oneline -- src/              # commits whose diff matches the regex
git log --oneline -L '20,40:src/rates.ts'               # history of one line range
git log --follow --oneline -- src/refunds/policy.ts     # across renames
git log --oneline --diff-filter=D -- path/to/gone.ts    # the commit that deleted a file
git log --merges --oneline <base>..HEAD                 # just the integration points
```

`-S` counts occurrences (a rename shows twice, add and remove); `-G` matches the diff text and
therefore also finds a line that moved. Use `-S` to find where a symbol appeared or vanished, `-G`
to find where a pattern was edited.

## Blame that survives moves and reformatting

Plain `git blame` attributes every line to the reformat or the file move that touched it last.

```bash
git blame -w -C -C -C -- src/rates.ts
```

- `-w` ignores whitespace-only changes.
- `-C` detects lines moved or copied within the file; repeated, it widens to other files in the
  same commit and then to the whole history. Each repetition costs time, so start with one.
- `git blame --ignore-rev <reformat-sha>` skips a single known-noisy commit, and
  `blame.ignoreRevsFile` (conventionally `.git-blame-ignore-revs`) makes that permanent for the
  repository. Adding the big reformat commit to that file is a five-minute change that pays back
  every time anyone runs blame.

`git log --oneline -1 --format='%h %an %ad %s' <sha>` on whatever blame names is the follow-up:
the commit message is the part that explains why.

## Has this patch already landed?

`git branch --merged` only knows about ancestry, so it misses anything that was squash-merged or
cherry-picked. `git cherry` compares patch-ids instead. Verified against a squash-merged branch:

```
$ git branch --no-merged main
  feat/currency                    <- looks unmerged
$ git cherry -v main feat/currency
- 99ad2d7 s                        <- '-' means this patch IS already upstream
$ git cherry -v main open-branch
+ 0f27f1c o                        <- '+' means it is not
```

Use `git cherry` before deleting any branch whose project squash-merges, and
`git range-diff <upstream> <branch> <other>` when the question is not "did it land" but "did it
land unchanged".

<!-- sources: addyosmani-git, git-docs -->
