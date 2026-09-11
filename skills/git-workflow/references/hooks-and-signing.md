# Hooks and commit signing

Verified against: git 2.55.0

## Contents

- [Where hooks live](#where-hooks-live)
- [`core.hooksPath` is a global override](#corehookspath-is-a-global-override)
- [Which hook for which job](#which-hook-for-which-job)
- [Writing a hook that does not get bypassed](#writing-a-hook-that-does-not-get-bypassed)
- [`--no-verify` and what it skips](#--no-verify-and-what-it-skips)
- [A secret-scanning pre-commit hook](#a-secret-scanning-pre-commit-hook)
- [Signing: ssh vs gpg](#signing-ssh-vs-gpg)
- [Verifying signatures locally](#verifying-signatures-locally)
- [Signatures and rewrites](#signatures-and-rewrites)

## Where hooks live

`.git/hooks/` by default — inside the git directory, therefore **not** version-controlled and not
cloned. That is the whole reason hook managers exist: a hook nobody receives enforces nothing.

The version-controlled pattern is a directory in the repository plus a one-time opt-in:

```bash
git config core.hooksPath .githooks     # per repository, run once after clone
```

Anything that has to hold for everyone belongs on the server or in CI, not in a hook. A hook is a
fast local warning; it is not a gate.

## `core.hooksPath` is a global override

Set globally, `core.hooksPath` replaces hook lookup for **every** repository on the machine —
including repositories that ship their own `.githooks` or rely on a hook manager. Their hooks
silently stop running. A global `core.hooksPath = ~/.config/git/hooks` is therefore a repo-wide
opt-out disguised as a personal preference.

If you find it set globally while diagnosing "the pre-commit hook is not running", that is the
answer. Move personal hooks to per-repository config, or have the global hook directory chain to
the repository's own.

In a worktree, hooks come from the *shared* git directory: every linked worktree runs the same
hooks, and there is no per-worktree hook path.

## Which hook for which job

| Hook | Runs | Use for | Can block? |
|---|---|---|---|
| `pre-commit` | before the message editor | format, lint and test **staged** content | yes |
| `prepare-commit-msg` | before the editor opens | insert a template, a ticket id, a trailer | no |
| `commit-msg` | after the message is written | validate message shape | yes |
| `pre-rebase` | before a rebase starts | refuse to rebase a protected branch | yes |
| `post-checkout`, `post-merge` | after the tree changes | reinstall dependencies | no |
| `pre-push` | after the remote is chosen, before transfer | run the test suite, refuse force-push to protected refs | yes |
| `post-commit`, `post-rewrite` | after the fact | notifications, bookkeeping | no |

`pre-push` receives the ref updates on stdin (`<local-ref> <local-sha> <remote-ref> <remote-sha>`),
which is what makes a local "never force-push main" guard possible. A deleted remote ref arrives
as an all-zero local SHA.

## Writing a hook that does not get bypassed

- Check the **staged** content, not the working tree. `git stash push --keep-index` before running
  the tests, and restore afterwards — otherwise the hook passes on code that is not being committed.
- Exit non-zero with a message that says what to do. `Error` with no remedy trains people to use
  `--no-verify`.
- Keep it under a couple of seconds. A slow `pre-commit` is the single biggest cause of
  `--no-verify` habits.
- Make it idempotent and non-interactive: hooks run under editors, IDEs and automation that have
  no terminal.
- Hooks are executables, not necessarily shell scripts — any interpreter with a shebang works, and
  the file must be executable (`chmod +x`). A non-executable hook is skipped silently.

## `--no-verify` and what it skips

`git commit --no-verify` skips `pre-commit` **and** `commit-msg`. `git push --no-verify` skips
`pre-push`. Nothing warns anyone afterwards that it happened.

Do not pass it unless the user asked. A hook in the way is either telling you something true or is
a bug to fix in the hook; skipping it commits the problem and hides the evidence. When a commit
fails because of a hook, fix the cause and make a new commit rather than amending — the failed
attempt never became a commit, so there is nothing to amend on a shared branch anyway.

## A secret-scanning pre-commit hook

The one hook worth adding to any repository, because it guards the mistake a history rewrite
cannot undo:

```sh
#!/bin/sh
# .githooks/pre-commit — refuse staged content that looks like a credential.
# Patterns cover the common literal forms; a real scanner (gitleaks, trufflehog)
# belongs in CI, where it can see the whole history.
# `-G` takes POSIX extended regex: `(?i)` is rejected as an invalid regex, so
# case-insensitivity comes from `-i` and not from an inline flag.
if git diff --cached -U0 -i -G 'secret|passwd|password|api[_-]?key|access[_-]?token|BEGIN [A-Z ]*PRIVATE KEY' --name-only | grep -q .; then
	echo "pre-commit: staged change looks like it contains a credential." >&2
	echo "Review with: git diff --cached -U0" >&2
	echo "If this is a false positive, commit with --no-verify and say so in the message." >&2
	exit 1
fi
```

Pair it with `.gitignore` entries for `.env*`, `*.pem`, `*.p12` and whatever the project's
credential files are called. A `.gitignore` entry does not help for a file already tracked — for
that, `git rm --cached <path>` in its own commit.

## Signing: ssh vs gpg

ssh signing is the lower-friction option and needs no key server:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519_signing.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

For gpg, drop `gpg.format` (the default) and set `user.signingkey` to a key id.

`commit.gpgsign true` signs every commit, including ones created by `rebase` and `cherry-pick`,
which is usually what a repository requiring signatures wants. It also means every commit needs
the key available: in an automated flow, an ssh key with a passphrase and no loaded agent makes
`git commit` fail or hang. Use an unencrypted signing key held by the agent, or turn signing off
for that context deliberately — never by passing `--no-verify`, which does not affect signing at
all.

## Verifying signatures locally

Verification needs an allowed-signers file; without one git reports every ssh signature as
unverifiable rather than as bad:

```
error: gpg.ssh.allowedSignersFile needs to be configured and exist for ssh signature verification
```

```bash
# one line per signer: <principal> <key-type> <key>
printf '%s %s\n' "sam@example.com" "$(cat ~/.ssh/id_ed25519_signing.pub)" >> ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
```

Then:

```bash
git log --pretty='%h %G? %GS %s'    # G good, B bad, U good-but-untrusted, N none, E cannot check
git verify-commit <sha>
git log --show-signature -1
```

`%G?` of `N` means *unsigned*, not *invalid*. Do not report an unsigned commit as a signature
failure; the two have different causes and different fixes.

## Signatures and rewrites

Rewriting history destroys signatures, and this is the part that surprises people in a repository
with a signature requirement. Verified:

```
$ git log -1 --pretty='%G? %GS'
G lab@example.invalid
$ git rebase --force-rebase HEAD~1 && git log -1 --pretty='%G? %GS'
N                                      <- unsigned
$ git -c commit.gpgsign=true rebase --force-rebase HEAD~1 && git log -1 --pretty='%G?'
G                                      <- signed again, with the rewriter's key
```

`git cherry-pick` behaves the same way. So a rebase of someone else's signed commits either
unsigns them or replaces their attestation with yours; there is no third option, and the original
signature cannot be carried across because the commit object it covered no longer exists.

Consequences to state before rewriting a signed branch:

- Under a ruleset requiring signed commits, an unsigned rewrite is rejected at push time — after
  the local history is already rewritten.
- `git rebase -x 'git commit --amend --no-edit -S'` re-signs every commit, but every commit is then
  attributed to the rewriter. If authorship attestation matters, do not rewrite; merge instead.
- Signed tags do not survive at all: a tag signs a specific commit, so a rewrite orphans it. Re-tag
  the new commit and say the old tag is dead.

<!-- sources: awesome-copilot-commit, addyosmani-git, mattpocock-guardrails, git-docs -->
