# Tokens, secrets and the Actions supply chain

## Contents

- [`permissions:` and the blast radius](#permissions-and-the-blast-radius)
- [Scope reference](#scope-reference)
- [OIDC instead of stored cloud credentials](#oidc-instead-of-stored-cloud-credentials)
- [Secret hygiene](#secret-hygiene)
- [Pinning `uses:` references](#pinning-uses-references)
- [Upgrading action versions](#upgrading-action-versions)
- [Dependabot for actions](#dependabot-for-actions)
- [Artifact and cache trust boundaries](#artifact-and-cache-trust-boundaries)
- [Self-hosted runners](#self-hosted-runners)
- [`zizmor`](#zizmor)
- [Using a scanner's output honestly](#using-a-scanners-output-honestly)

## `permissions:` and the blast radius

Every run receives an automatic `GITHUB_TOKEN`. Its scope is what a compromised step can do, so
it is the single most valuable thing to tighten.

With no `permissions:` block anywhere, the workflow inherits the repository or organisation
default. New repositories default to read-only for contents, but long-lived ones and
organisations that never changed the setting are still read/write across most scopes — which you
cannot see from the YAML. Flag the absence, do not assume the default.

```yaml
permissions: {}            # deny everything by default

jobs:
  build:
    permissions:
      contents: read       # checkout only
    runs-on: ubuntu-latest

  comment:
    permissions:
      contents: read
      pull-requests: write # this job posts a comment; nothing else
    runs-on: ubuntu-latest
```

Findings and their weight:

| Observation | Weight |
|---|---|
| `permissions: write-all` | high — everything a compromise can reach |
| a `write` scope no step in the job uses | high — free capability for an attacker, zero cost to remove |
| top-level `write` that belongs on one job | medium |
| no `permissions:` block at all | medium — inherits an unknown, possibly broad default |

## Scope reference

`actions`, `attestations`, `checks`, `contents`, `deployments`, `discussions`, `id-token`,
`issues`, `models`, `packages`, `pages`, `pull-requests`, `security-events`, `statuses`. Each
takes `read`, `write` or `none`.

The ones that surprise people: `id-token: write` is required to request an OIDC token and grants
nothing else; `security-events: write` is what CodeQL and any SARIF upload need;
`attestations: write` is required to generate build provenance; commenting on a pull request
needs `pull-requests: write`, and commenting on an issue needs `issues: write` — a PR is an issue
for some endpoints but not for this.

A fork `pull_request` run cannot be granted more than read, whatever the block says. Do not
"fix" that by moving to `pull_request_target`.

## OIDC instead of stored cloud credentials

A static cloud key in repository secrets is valid until a human rotates it, so any leak is
permanent until noticed. OIDC mints a token per run, scoped to the repository and expiring in
minutes.

```yaml
permissions:
  id-token: write
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@<sha>   # v5.0.0
        with:
          role-to-assume: arn:aws:iam::123456789012:role/ci-deploy
          aws-region: us-east-1
      # no AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY secret needed
```

The same pattern exists for Azure (`azure/login`), Google Cloud
(`google-github-actions/auth`), HashiCorp Vault and container registries. The workflow half is
the easy half: on the provider side, scope the trust policy to the specific repository and
ideally a specific branch or environment, otherwise a fork or an unrelated repository can assume
the role. What the provider expects in that policy belongs to the provider's own documentation.

When a long-lived secret genuinely cannot be replaced, put it in an environment with required
reviewers so it is only issued after a human approves the deployment.

## Secret hygiene

- Reference a secret only from the job that uses it. A secret named in a workflow is readable by
  every step of the job that receives it, including third-party actions.
- Anyone with write access to the repository can read every repository secret, so the credential
  behind the secret should itself be least-privileged.
- Do not pass secrets to an unpinned or unreviewed third-party action, and do not pass them to
  any job that runs pull-request code.
- Mask non-secret sensitive values you compute with `::add-mask::VALUE`, and register derived
  secrets so they are redacted too.
- `actions/checkout` leaves the token in `.git/config` by default; set
  `persist-credentials: false` on any job that later runs code it did not write.

## Pinning `uses:` references

Pinning to a full-length commit SHA is the only way to reference an action immutably. A tag or a
branch is a movable pointer: whoever gains write access to the action's repository can point `v4`
at new code that runs inside your job with your token and secrets.

```yaml
steps:
  - uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608   # v4.3.1
  - uses: actions/setup-node@60edb5dd545a775178f52524783378180af0d1f8 # v4.0.4
```

Keep the version in a trailing comment — the SHA alone tells a reader nothing about what it is or
whether it is current.

The rule is not uniform across contexts, and saying which one you are applying avoids a
contradiction:

- **Writing or hardening a workflow:** pin everything, first-party included. Enforce it with the
  repository- or organisation-level policy that requires actions to be pinned to a full-length
  commit SHA, rather than with review.
- **Reporting a vulnerability:** an unpinned *third-party* action in a job that holds secrets,
  OIDC rights, a write token, or release/publish/signing power is a finding. `actions/*` and
  `github/*` on a version tag are not, and neither is a vendored `./.github/actions/...` local
  action — it comes from your own repository and belongs to the pwn-request analysis instead.
- `@main` or `@master` on any third-party reference is worse than a tag and should be reported
  regardless: it is "whatever the author pushed most recently".

Reusable workflows referenced with `uses: owner/repo/.github/workflows/x.yml@ref` follow the same
rule.

## Upgrading action versions

When a run warns that an action uses a deprecated runtime:

- Move to the latest stable **major** version compatible with the workflow, then resolve that
  release to a commit SHA and pin the SHA.
- One action (or one tightly related group) per commit, so a failure names its cause.
- Preserve behaviour: same triggers, same permissions, same inputs unless the upgrade requires a
  change.
- Re-run the affected workflows and check the logs for new deprecation warnings, and confirm
  release, signing and artifact steps still produce the same outputs.
- In the PR description, list each action from → to, name any that could not move to a new major
  and why, and say which workflows were re-run.

## Dependabot for actions

All Dependabot configuration lives in a single `.github/dependabot.yml` on the default branch;
GitHub does not read a second file. The `github-actions` ecosystem covers `uses:` references and
keeps SHA pins current, which is what makes pinning maintainable.

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directories:
      - "/"
      - "/.github/actions/*"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns: ["*"]
```

`directory` (singular) does not accept glob patterns — only `directories` (plural) does. Getting
this wrong produces a config that validates and silently monitors nothing.

Group updates so one PR covers a set, rather than one PR per action per week; the review burden
is what makes teams turn Dependabot off.

## Artifact and cache trust boundaries

- An artifact uploaded by a fork's `pull_request` run is untrusted data. A `workflow_run` job may
  read it; it must not execute it, and must validate any value it turns into a command argument.
- Caches are shared per scope, so a job that can write the default branch's cache scope can
  influence unrelated privileged runs. `pull_request_target` runs therefore get read-only access
  to that scope: a save fails with a log warning while the step and job continue.
- `actions/download-artifact` across runs needs `run-id` and a `github-token`; without them it
  looks in the current run and silently finds nothing.

## Self-hosted runners

On a public repository, a self-hosted runner will eventually execute a stranger's code. It must
be ephemeral (destroyed after each job) and network-isolated from anything internal, otherwise
one fork PR becomes a foothold. Persistent runners also leak state between jobs — installed
tools, `$HOME` caches, cloud instance metadata.

A finding here needs runtime context the YAML does not carry, so report the exposure and what to
verify rather than asserting an exploit.

## `zizmor`

`zizmor` is a static analyser for Actions workflows, composite actions, Dependabot configs and
pre-commit configs.

```bash
zizmor .github/workflows                     # audit a directory
zizmor --persona=auditor .github/workflows    # everything, including likely false positives
zizmor --format=sarif . > zizmor.sarif        # for code scanning upload
zizmor --fix .github/workflows                # apply the fixes it can make safely
```

Facts that decide whether your CI gate works:

- **Exit codes 11–14 mean "findings at informational / low / medium / high"; they are not
  errors.** Real failures are 1 (audit error), 2 (bad arguments) and 3 (no inputs collected).
  Use `--no-exit-codes` when you want findings reported without failing the step, and note that
  `--format=sarif` also suppresses 11+.
- Personas: `regular` (default, high-signal), `pedantic` (adds code smells, e.g. any `${{ }}` in
  a `run:` even when it is not attacker-controllable), `auditor` (everything). Some audits such
  as `self-hosted-runner` only produce auditor-level results, so a clean default run does not
  mean they were checked.
- Online mode is selected by the environment: `ZIZMOR_OFFLINE` forces offline, otherwise the
  presence of `GH_TOKEN` / `GITHUB_TOKEN` / `ZIZMOR_GITHUB_TOKEN` enables online audits. Pass
  `--gh-token "$(gh auth token)"` to be explicit; without a token the audits that need the API —
  impostor commits, confusable refs — are skipped silently.
- `--collect=` controls what is picked up from a directory (`workflows`, `actions`,
  `dependabot`, `pre-commit`, `default`, `all`). An explicitly named file is always audited.
- `--format=json-v1` uses 0-based line numbers under the key `row`, while `plain` and `sarif`
  are 1-based.

## Using a scanner's output honestly

Whether `zizmor`, CodeQL for Actions or Scorecard's `Dangerous-Workflow`, `Token-Permissions`
and `Pinned-Dependencies` checks:

- Keep the tool's ids, titles, severities and locations. Do not merge, drop or reclassify them.
- The tool decides *which findings exist*; you decide *whether the chain is real*. Re-read the
  cited YAML plus enough context to see the trigger, permissions, secrets, checkout ref and the
  commands involved, and follow repository-local reusable workflows and composite actions when
  the reported path depends on them.
- State any link you could not resolve instead of assuming it.
- Do not turn hardening advice into an exploit claim. Broad permissions, a mutable tag,
  `pull_request_target`, `workflow_run`, a self-hosted runner or an interpolation alone are not
  exploitation unless the checked-in workflow establishes the untrusted path and a real impact.
- Do not invent cloud trust policies, repository settings, secret values or caller behaviour that
  is not visible in the repository you are reading.

<!-- sources: awesome-copilot, getsentry-skills, github-docs, zizmor, scrutineer, scorecard, secure-repo -->
