# Commit granularity and messages

Verified against: git 2.55.0

## Contents

- [One commit, one reason](#one-commit-one-reason)
- [Splitting a messy working tree](#splitting-a-messy-working-tree)
- [Splitting a commit that is already made](#splitting-a-commit-that-is-already-made)
- [Message shape](#message-shape)
- [Types](#types)
- [Breaking changes](#breaking-changes)
- [Writing the body: why, not what](#writing-the-body-why-not-what)
- [Trailers and footers](#trailers-and-footers)
- [Creating the commit without an editor](#creating-the-commit-without-an-editor)
- [Fixups instead of amends](#fixups-instead-of-amends)
- [Before every commit](#before-every-commit)

## One commit, one reason

A commit is the unit of revert and of review. Size it so that reverting it is a coherent act.

- Keep formatting out of behaviour changes. A reviewer cannot see three real lines inside a
  400-line reformat, and neither can `git log -S`.
- Keep refactors out of features. Two changes, two commits, and ideally two reviews. A variable
  rename inside a feature commit is fine; extracting a module is not.
- Commit at each point the tests pass, not at the end of the day. The commit is the save point
  that bounds how much work a bad next step can cost.
- Roughly: 100 changed lines reviews easily, 300 is acceptable for one logical change, 1000 needs
  splitting. These are prompts to think, not a gate.

A commit that needs "and" in its subject is two commits.

## Splitting a messy working tree

```bash
git add -p            # hunk by hunk; s splits, e edits the hunk, ? explains the keys
git add -N <path>     # make an untracked file visible to -p without staging its content
git diff --staged     # confirm the group before committing it
git stash push --keep-index    # park everything not staged, so tests run on this commit alone
```

The `--keep-index` step is what makes the split honest: it proves each commit passes on its own
rather than only as part of the pile. Run the project's checks, commit, then `git stash pop` and
repeat.

`git add -p` cannot split two changes that share a line. When it cannot, edit the file back to the
intermediate state by hand, commit, then re-apply. That is not defeat; it is what an atomic
history costs.

## Splitting a commit that is already made

```bash
git rebase -i <sha>~1        # mark the commit 'edit'
git reset HEAD~              # un-commit it, keep the changes in the working tree
git add -p && git commit     # ...as many times as needed
git rebase --continue
```

Only on unpublished commits — a branch nobody else holds, and nothing built from it.

## Message shape

```
<type>(<scope>): <subject>

<body: why this change exists, and what it changes about behaviour>

<footers>
```

- Subject in the imperative present (`add`, not `added`/`adds`), no trailing period, 70 characters
  or fewer. `git log --oneline` and most tooling truncate past that.
- Every line under 100 characters, body wrapped around 72.
- Scope optional but useful; keep it kebab-case and drawn from the repository's own vocabulary.
- Read the repository's last twenty subjects before applying any of this. A project with its own
  convention wins over this one; a project with no convention gets Conventional Commits.
- Never put a customer or organisation name, a user's email, support-ticket text, a secret or any
  other personal data in a message. Describe the technical symptom. A message is public forever and
  cannot be edited after it is published.

## Types

| Type | Use for |
|---|---|
| `feat` | new user-visible capability |
| `fix` | incorrect behaviour now correct |
| `refactor` | structure changes, behaviour does not |
| `perf` | same behaviour, measurably faster |
| `test` | tests only |
| `docs` | documentation only |
| `style` | formatting only, no logic |
| `build` | build system, packaging, dependencies |
| `ci` | CI configuration |
| `chore` | maintenance that fits nothing above |
| `revert` | reverts a previous commit |

Some projects use `ref` for `refactor` and add `meta` for repository metadata. Follow the
repository. Choosing a type is a claim about the change, so check it against the diff: a "fix"
that adds a parameter is a `feat`, and a "refactor" that changes an output is a `fix` or a
breaking change.

## Breaking changes

Two forms, both valid, and they mean the same thing:

```
feat(api)!: drop the v1 refund endpoint

BREAKING CHANGE: POST /v1/refunds returns 410. Callers move to POST /v2/refunds,
which requires an idempotency key.
```

The exclamation mark is what release tooling reads; the footer is what a human reads. Write both
when the change is genuinely breaking, and describe the migration, not the removal.

## Writing the body: why, not what

The diff already says what changed. The body exists for what the diff cannot show: the reason,
the constraint, the rejected alternative, the behaviour a reader would otherwise have to infer.

```
fix(rates): honour the cache TTL when reading

The cache was checked for presence only, so a rate stayed in use
indefinitely once written. Providers repriced hourly, which meant
refunds were computed at a rate up to a day old.

Reading now checks staleness against DEFAULT_TTL_MS. The write path is
unchanged, so nothing else needs to move.
```

Skip the body when the subject is genuinely the whole story (`docs: fix typo in README`). Never
write a body that restates the subject, and never paste test output or a file list into it — the
diff is attached.

## Trailers and footers

```
Fixes #412
Refs #398
Co-authored-by: Name <email>
Reviewed-by: Name <email>
```

Trailers go last, one per line, no blank lines between them. `git interpret-trailers --trailer
'Fixes: #412'` appends one correctly if you are generating messages programmatically;
`git log --format='%(trailers:key=Fixes,valueonly)'` reads them back.

Whether an issue-closing keyword actually closes anything is a property of the forge, not of git —
that belongs to the `github` skill.

## Creating the commit without an editor

Pass one `-m` per paragraph. Git joins them with a blank line, which is exactly the shape wanted:

```bash
git commit -m "fix(rates): honour the cache TTL when reading" \
           -m "The cache was checked for presence only, so a stale rate stayed in use." \
           -m "Fixes #412"
```

Do not put a literal `\n` in an argument — it lands in the message as backslash-n. A heredoc
works too and is easier for long bodies:

```bash
git commit -F - <<'EOF'
fix(rates): honour the cache TTL when reading

The cache was checked for presence only, so a stale rate stayed in use.
EOF
```

Never open an interactive editor from an automated flow; it hangs. If a commit template or hook
would open one, `-m` or `-F -` bypasses it without disabling anything else.

## Fixups instead of amends

```bash
git commit --fixup=<sha>      # message becomes 'fixup! <that commit's subject>'
git commit --squash=<sha>     # same, but keeps your message for the squash editor
git rebase --autosquash <base>
```

`--fixup` is better than `--amend` while a branch is in flight: the intermediate state stays
reviewable, and the folding happens once at the end. `rebase.autosquash` is off by default on
2.55.0 — the flag is required (verified: a plain `git rebase` leaves the `fixup! <subject>`
commit standing).

When a commit fails because of a hook, fix the problem and make a *new* commit rather than
amending, unless the branch is yours alone. An amend changes a SHA that a colleague, a CI run or a
review comment may already reference.

## Before every commit

```bash
git status --short                 # nothing unexpected, no stray files
git diff --staged                  # read what you are about to claim
git diff --staged --check          # no trailing whitespace, no conflict markers
git diff --staged -i -G 'api[_-]?key|secret|password|access[_-]?token|BEGIN [A-Z ]*PRIVATE KEY'
<project typecheck> && <project tests> && <project lint>
```

The `-G` sweep catches the accident that cannot be undone by a rewrite: once a secret is pushed,
it must be rotated regardless of what happens to the history.

Never pass `--no-verify` unless the user asked for it. A hook that is in the way is either
telling you something or is a bug to fix in the hook.

<!-- sources: awesome-copilot-commit, getsentry-commit, addyosmani-git, fvadicamo-commit, awesome-copilot-branch, git-docs -->
