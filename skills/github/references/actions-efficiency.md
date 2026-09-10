# Workflow efficiency and structure

## Contents

- [Measure first](#measure-first)
- [Guardrails on every proposed fix](#guardrails-on-every-proposed-fix)
- [The six fixes worth ranking](#the-six-fixes-worth-ranking)
- [Caching](#caching)
- [Concurrency](#concurrency)
- [Trigger and job scoping](#trigger-and-job-scoping)
- [Matrices](#matrices)
- [Reusable workflows and composite actions](#reusable-workflows-and-composite-actions)
- [Baseline shape for a new workflow](#baseline-shape-for-a-new-workflow)
- [Reporting the result](#reporting-the-result)

## Measure first

```bash
gh run list --limit 20 --json databaseId,name,conclusion,event,createdAt,updatedAt
run_id=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
gh run view "$run_id"                 # per-job durations
gh run view "$run_id" --log-failed    # only the failing steps' logs
gh cache list                         # what is actually being cached, and its size
```

Then read the YAML for the five usual waste sources: no dependency cache, no `concurrency`
cancellation, triggers broader than the code they guard, two workflows covering the same ground,
and an expensive job that runs on every change regardless of scope.

Without shell or `gh` access, ask for `.github/workflows/` and `gh run list --limit 10` output,
and label the answer as static-only analysis rather than implying the numbers were observed.

## Guardrails on every proposed fix

Check a candidate against all five before it is even ranked:

1. It does not hide required validation. Anything that removes a release, schema, migration or
   shared-library check is dropped, not weighed.
2. It does not reduce parallelism unless the user chose cost over latency *and* the new critical
   path stays close to the original.
3. It keeps every matrix leg the project actually promises (a supported runtime, a supported OS).
   Only undocumented legs are candidates for removal.
4. Jobs that write back to the branch — formatters, generated-code committers — move to an
   opt-in trigger rather than being deleted or left to run on every push.
5. Repository YAML changes stay separate from organisation or account settings. A fix that needs
   both becomes two recommendations, because one of them the user may not be able to apply.

## The six fixes worth ranking

Rank by estimated minutes saved per day (per-run saving × runs per day) and propose at most
three:

1. Dependency cache with a lockfile-hashed key.
2. `concurrency` with `cancel-in-progress`.
3. Remove duplicate coverage between workflows before merging jobs together.
4. Narrow triggers, or gate jobs on changed paths.
5. Reduce matrix breadth to match the risk of the event.
6. Parallelise independent jobs on the critical path.

## Caching

```yaml
- uses: actions/cache@<sha>
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

- Key on the lockfile, not on `package.json`; and never on `github.run_id`, which guarantees a
  miss on every run while still paying the upload cost.
- `restore-keys` is what makes a partial hit useful. Without it, one dependency change throws
  away the whole cache.
- Cache the package manager's store (`~/.npm`, `~/.cache/pip`, `~/.m2`), not `node_modules`,
  unless the install step is the thing being skipped.
- `setup-node`, `setup-python`, `setup-java` and friends have a `cache:` input that wires this up
  correctly; prefer it over hand-rolling `actions/cache` for dependencies.
- To debug a miss without disturbing the run, use `actions/cache/restore` with
  `lookup-only: true` and read which keys were tried.
- Caches are scoped by branch, with fallback to the default branch. A cache written on a feature
  branch is invisible to a sibling branch — that is why "it works on main" is a common report.

## Concurrency

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This is the single cheapest fix on a busy repository: every force-push to a PR otherwise starts
a run that nobody will read. Do not set `cancel-in-progress: true` on deployment or release
workflows — a cancelled deploy leaves partial state. Group those by environment with
`cancel-in-progress: false` so they queue instead.

## Trigger and job scoping

```yaml
on:
  push:
    branches: [main]
  pull_request:
    paths:
      - "src/**"
      - "tests/**"
      - "package-lock.json"
```

`paths` filters apply to `push` and `pull_request` only. Two consequences:

- A required status check on a path-filtered workflow blocks merges forever when the filter does
  not match, because the check never reports. Either make the check non-required, or add a job
  that reports success for the skipped case.
- For `workflow_run`, `schedule` and manual events there is no path filter; gate inside the
  workflow with a change-detection step that emits explicit boolean outputs
  (`run_tests`, `docs_only`, …) and `if:` on those.

`paths-ignore` is the better choice when the exclusion list is shorter and more stable than the
inclusion list.

## Matrices

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, windows-latest]
    node: [20, 22]
    include:
      - os: macos-latest
        node: 22
```

- Size the matrix to the decision the event needs: one representative leg for an ordinary code
  change, a compatibility matrix on sensitive runtime surfaces, the full matrix on release.
- `fail-fast: true` (the default) gives the fastest signal; `fail-fast: false` gives a complete
  report. Choose deliberately — a matrix that cancels on first failure hides whether the problem
  is one leg or all of them.
- `include` adds a single combination without multiplying the whole product; `exclude` removes
  one. Reaching for a second matrix key to express one extra case is the usual mistake.
- `max-parallel` throttles a matrix that would otherwise saturate the runner quota and starve
  other workflows.

## Reusable workflows and composite actions

Two different tools:

- A **reusable workflow** (`on: workflow_call`) is called as a whole job with
  `uses: owner/repo/.github/workflows/build.yml@<sha>`. It has its own `jobs:`, receives `inputs`
  and `secrets`, and returns `outputs`. Use it when entire jobs repeat. Secrets are not
  inherited by default — pass them explicitly or use `secrets: inherit`, and be aware that
  `inherit` hands the called workflow everything.
- A **composite action** (`action.yml` with `runs.using: composite`) is called as a step and
  bundles a step sequence. Use it when the repetition is inside a job. It cannot use `strategy:`
  or `services:`, and its `if:` handling differs from a normal step's.

Both are third-party references when they come from another repository: pin them by SHA. A local
composite action under `./.github/actions/` is your own code, but note that under a privileged
trigger it comes from whatever ref is checked out.

## Baseline shape for a new workflow

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@<sha>          # v4.3.1
        with:
          fetch-depth: 1
          persist-credentials: false
      - uses: actions/setup-node@<sha>        # v4.0.4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm test
```

`timeout-minutes` matters more than it looks: without it a hung job holds a runner for six
hours. `fetch-depth: 1` is the default and is right unless something needs history — a tool that
diffs against the base branch, or a changelog generator, needs `fetch-depth: 0`.

## Reporting the result

Report four things: the waste sources found with their evidence, the fixes proposed with the
measurement that motivated each, what was validated live versus statically, and the impact —
expected versus measured, with PR wall-clock time and total runner minutes kept apart. A matrix
split shortens the first and lengthens the second; collapsing them into one "faster" claim
misrepresents the trade the user is making.

Treat unexpected live behaviour as a real bug even when the YAML looks correct: path filters and
`concurrency` groups are both easy to get subtly wrong, and a test push on a non-protected
branch settles it in one run.

<!-- sources: awesome-copilot, github-docs, starter-workflows -->
