# Leaked credentials: finding, scoping, rotating

## Contents

- [The one rule that orders everything else](#the-one-rule-that-orders-everything-else)
- [Finding them](#finding-them)
- [What counts as a secret](#what-counts-as-a-secret)
- [Scoping the blast radius](#scoping-the-blast-radius)
- [The exposure window](#the-exposure-window)
- [The response, in order](#the-response-in-order)
- [History rewriting and what it does not do](#history-rewriting-and-what-it-does-not-do)
- [Secondary locations](#secondary-locations)
- [Preventing recurrence](#preventing-recurrence)
- [Secrets that are not in the repository](#secrets-that-are-not-in-the-repository)
- [Severity](#severity)

## The one rule that orders everything else

**Revocation is the only step that makes the credential stop working.** Everything else —
deleting the line, rewriting history, rotating config, adding a scanner — changes who can
conveniently find it. Until the credential is revoked at the provider, every clone, fork,
mirror, CI cache, container layer and screenshot still holds a working one.

This is why the response order is revoke, then rotate, then history. Teams invert it because
the history rewrite feels like the fix, and spend the rewrite window with a live credential
still out.

## Finding them

Sweep every file, not just source. The places a code-focused scan misses:

- Config and IaC: `*.tf`, `*.tfvars`, Helm values, Kubernetes manifests and `Secret` objects
  with base64 (which is encoding, not encryption), Ansible vars.
- CI definitions and the scripts they call.
- Dockerfiles (`ENV`, `ARG`, `RUN` with a token) and committed image layers.
- Committed `.env`, `.env.local`, `.npmrc`, `.pypirc`, `.netrc`, `.dockercfg`,
  `kubeconfig`, `.pem` / `.p12` / `id_*` key files.
- Test fixtures, seed data, notebooks and their saved output cells.
- Documentation and comments — a "temporary" token in a README outlives the README.
- Lockfiles and package manifests with credentials in a registry URL.
- Anything named `*example*` or `*sample*` that was filled in with real values.

Signals beyond known prefixes: high-entropy string literals assigned to a name containing
`key`, `token`, `secret`, `password`, `credential`, `passwd`, `auth`; `-----BEGIN` blocks;
connection strings with an embedded password; base64 blobs long enough to hold a key.

## What counts as a secret

Not everything that looks like one is one, and saying so keeps the report credible:

| Value | Verdict |
|---|---|
| A live provider key, token, password or private key | Secret. Revoke. |
| A test-mode or sandbox key | Lower severity, still rotate — it often shares an account and reveals identifiers |
| A public identifier: client id, publishable key, project id, bucket name | Not a secret. Do not report as one. |
| A placeholder (`REDACTED`, `changeme`, `xxx`, an obvious dummy) | Not a secret, but a hardcoded-credential pattern is still a finding if production reads it |
| A key committed and already revoked | Report as history hygiene, not an incident |
| An encrypted value with the key elsewhere (SOPS, sealed-secrets, `git-crypt`) | Not a leak; check where the decryption key lives |

A default or fallback secret is the dangerous middle case: `SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")`
is a live credential in every deployment that forgets the variable, and it fails open silently.
Report the fallback, not just the literal.

## Scoping the blast radius

Per credential, not as one lump. "Rotate the secrets" is not a plan, because the four in one
file usually need four different responses:

| Kind | What it reaches | First question |
|---|---|---|
| Payment provider live key | Money movement, customer payment data | Were charges, refunds or payouts created? |
| Repository / package token | Code, releases, CI, possibly the org | Were new commits, workflows, releases or tokens created? |
| Cloud access key | Whatever its IAM policy allows | What is the attached policy, and was `sts:AssumeRole` used? |
| Database or warehouse credential | Customer data, at the privilege of that role | Were there connections from outside the expected network? |
| Deploy key or SSH private key | Shell or push access to hosts | Were there logins in the window? |
| Signing key | Every artifact consumers trust | Was anything signed that the team did not sign? |
| Session or JWT signing secret | Forgeable identity for every user | Must be rotated with a plan for invalidating live sessions |
| Third-party API key | The data and actions of that integration | Provider-side usage logs |

For each: what identity it grants, what that identity can reach, whether provider-side logs can
show use, and whether rotation breaks callers (which decides whether you need overlapping keys).

## The exposure window

From the commit that introduced the value to the moment it is revoked — not to the moment it was
noticed. `git log --diff-filter=A -- <path>` gives the introduction; `git log -S '<fragment>'`
finds it if it moved between files. Treat every credential exposed in a public repository as
compromised from its commit date and work backwards from evidence, not forwards from optimism.

The audit-log question is decisive for whether this is a rotation or an incident: pull
provider-side logs for the window and look for use from unexpected addresses, unusual times, or
actions the team cannot account for. A clean log is weak evidence — many providers do not log
reads, and retention is often shorter than the window — so say "no evidence of use in the
retained logs" rather than "it was not used".

## The response, in order

1. **Revoke at the provider.** Every credential, before anything else. If revoking breaks
   production, issue the replacement first and revoke immediately after — do not defer it to a
   maintenance window.
2. **Issue replacements into a secret store** and redeploy from there. If the replacement lands
   in the same file, the incident recurs on the next commit.
3. **Check for damage** using the provider logs and the questions above. Whatever cannot be
   determined goes in the report as an open item with the check that would settle it.
4. **Remove from the working tree** and make the path unreadable going forward.
5. **Purge the secondary locations** below. This is where most responses stop too early.
6. **Rewrite history if it is still warranted**, knowing what that does and does not achieve.
7. **Add the recurrence control**, and verify it fires on a test commit.

## History rewriting and what it does not do

`git filter-repo` (or BFG) rewrites the objects, and then:

- Every collaborator must re-clone or hard-reset; a stale clone will push the blob back.
- Forks keep their own copy. The fork network is outside your control entirely.
- On GitHub, an unreachable object can stay retrievable by SHA — including through pull-request
  refs — until support purges the cache. Ask for the purge explicitly if the removal has to be
  real. `[official]`
- Every commit SHA after the touched commit changes, breaking tags, references in issues,
  deployment records and anything pinned by SHA.
- Mirrors, backups, CI artifact caches and package tarballs are unaffected.

Given all that: rewrite history when the secret is still sensitive after revocation — a private
key, a customer data extract, personal data — and skip it when a revoked API key is simply
embarrassing. Either way it is never the first step.

## Secondary locations

The same value is usually in more than one place:

- **CI logs.** A script that echoes the token puts it in every job log; those logs need
  deleting, and the delete is separate from the code fix.
- **Container images** on every registry tag built from the commit.
- **Issues, pull requests and chat**, where it was pasted during debugging.
- **Error trackers and APM**, if a request or environment dump was captured.
- **Developer machines**: shell history, editor recents, local `.env`.
- **Backups and database snapshots** if the secret was stored in a row.

## Preventing recurrence

- Push protection or a pre-commit / pre-receive secret scan, verified by attempting a test
  commit with a dummy pattern. An unverified hook is a hope.
- Read secrets from the environment or a secret manager, with **no fallback default**. A missing
  variable should crash at startup, loudly.
- Short-lived credentials where the provider supports them: OIDC federation for CI instead of
  long-lived cloud keys, per-environment scoped tokens instead of one org token.
- `.gitignore` does nothing for a file already tracked. Say this explicitly — it is the most
  common wrong answer. `git rm --cached` plus the ignore rule is the actual change.
- A `SECURITY.md` with the revocation contacts, so the next response starts at step 1 instead of
  at "who owns the Stripe account".

## Secrets that are not in the repository

The same audit covers credentials handled badly at runtime, which produce leaks without anyone
committing anything: secrets logged (`log_request_bodies: true` next to an endpoint that
receives tokens), secrets in URLs (they reach access logs, referrers and browser history),
secrets in error responses or stack traces, secrets passed as command-line arguments (visible
in the process table), and secrets written to a world-readable path or a temp file.

## Severity

| Situation | Typical severity |
|---|---|
| Live production credential in a public repository | Critical |
| Live production credential in a private repository | High — the contributor set is still wider than the secret's intended audience |
| Session or token signing secret, any visibility | Critical — it forges identities |
| Fallback default secret used by any deployed environment | High |
| Test or sandbox credential | Medium |
| Revoked credential still in history | Low, reported as hygiene |
| Secret written to logs with a demonstrated reader | High |

<!-- sources: copilot-secrets, cloudflare-audit, tob-insecure-defaults, openai-secbase, copilot-secreview -->
