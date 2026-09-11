# Browsers in CI

Verified against: Playwright 1.63.0. Container and GitHub Actions behaviour marked `[official]` was
taken from vendor documentation rather than reproduced on a real runner.

## Contents

- [Version lockstep is the whole problem](#version-lockstep-is-the-whole-problem)
- [`--with-deps` and non-Debian hosts](#--with-deps-and-non-debian-hosts)
- [The container image](#the-container-image)
- [Caching browsers, if you must](#caching-browsers-if-you-must)
- [Starting the application: `webServer`](#starting-the-application-webserver)
- [Workers and `fullyParallel`](#workers-and-fullyparallel)
- [Sharding, and the granularity trap](#sharding-and-the-granularity-trap)
- [Blob reports and `merge-reports`](#blob-reports-and-merge-reports)
- [Artifacts that survive the runner](#artifacts-that-survive-the-runner)
- [Making the job fail when it should](#making-the-job-fail-when-it-should)
- [Which browsers, how often](#which-browsers-how-often)
- [Secrets and supply chain](#secrets-and-supply-chain)
- [The job skeleton](#the-job-skeleton)
- [Review checklist](#review-checklist)

## Version lockstep is the whole problem

Playwright ships a browser build per release. The npm package and the browser binaries are a
matched pair, and the runner must have the pair that the package expects. Almost every "works on my
machine" CI failure in a Playwright job is a violation of that.

The canonical symptom:

```
browserType.launch: Executable doesn't exist at
/root/.cache/ms-playwright/chromium_headless_shell-1200/chrome-linux/headless_shell
```

The number in the path is the browser revision the installed `@playwright/test` wants. The message
means the cache contains some other revision. The usual cause is an unversioned cache key: the
cache restores the browsers from whenever the key was first written, `playwright install` sees a
populated directory and does nothing, and launch then looks for a revision that was never
downloaded. [official]

Two ways to keep the pair together, in order of preference:

1. Run in the official image tagged with the same version as the dependency.
2. Install the browsers on every run and, if caching, put the resolved version in the key.

Whichever you choose, bump the image tag or the version in the same commit as the npm dependency.
A Dependabot bump of `@playwright/test` that does not touch the workflow is exactly the change that
produces the error above the next morning.

## `--with-deps` and non-Debian hosts

Verified locally on Arch:

```
$ npx playwright install --with-deps chromium
BEWARE: your OS is not officially supported by Playwright; installing dependencies for ubuntu24.04-x64 as a fallback.
Installing dependencies...
sh: line 1: apt-get: command not found
Failed to install browsers
Error: Installation process exited with code: 127
```

`--with-deps` shells out to `apt-get`. On any host without it — Arch, Fedora, Alpine, a slim image
built from something other than Debian — it exits 127 and installs nothing. Dropping the flag
downloads the browser successfully:

```
$ npx playwright install chromium
BEWARE: your OS is not officially supported by Playwright; downloading fallback build for ubuntu24.04-x64.
$ npx playwright --version
Version 1.63.0
```

The browser then runs against whatever shared libraries the host happens to have, which worked here
(`chromium.launch()` reported `153.0.8010.12`) but is not something to depend on in CI. In CI, use
the image.

## The container image

```yaml
jobs:
  e2e:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.63.0-noble
```

The image ships the browsers and the OS libraries already matched to that Playwright version, which
removes the install step, the cache and the whole class of failure above. [official]

Three notes:

- Pin the full version, not `:latest` or a floating major. A floating tag reintroduces the mismatch
  from the other direction.
- The image runs as root; a step that writes into the workspace may need ownership fixed depending
  on the runner.
- Screenshot baselines generated elsewhere will not match this image. Generate `toHaveScreenshot`
  baselines inside the same image, or the comparison fails permanently.

## Caching browsers, if you must

If the image is not an option, the cache key must carry the version:

```yaml
- name: Resolve Playwright version
  id: pw
  run: echo "version=$(node -p "require('@playwright/test/package.json').version")" >> "$GITHUB_OUTPUT"

- uses: actions/cache@v4
  id: pw-cache
  with:
    path: ~/.cache/ms-playwright
    key: ms-playwright-${{ runner.os }}-${{ steps.pw.outputs.version }}

- if: steps.pw-cache.outputs.cache-hit != 'true'
  run: npx playwright install --with-deps chromium

- if: steps.pw-cache.outputs.cache-hit == 'true'
  run: npx playwright install-deps chromium
```

The second branch matters: a cache hit restores the browser binaries but not the apt packages they
link against, so the system dependencies still have to be installed. [official]

Reading the version from the resolved `package.json` rather than hardcoding it means the key moves
automatically with a dependency bump.

## Starting the application: `webServer`

Replace "start it in the background and sleep" with the runner's own supervision:

```ts
webServer: {
  command: 'npm run start',
  url: 'http://localhost:3000/api/health',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
},
```

Why this is better than `npm run start & sleep 45`:

- it polls the URL until it answers, so a fast start is not padded and a slow one is not truncated;
- if the server exits or never answers, the run fails with the server's own output instead of 200
  test failures;
- `reuseExistingServer: !process.env.CI` means a local developer's already-running dev server is
  used, while CI always starts a clean one.

Point `url` at a health endpoint that returns only when the app is actually ready, not at the root
route that a proxy answers before the app is up.

## Workers and `fullyParallel`

```ts
fullyParallel: true,
workers: process.env.CI ? '50%' : undefined,
forbidOnly: !!process.env.CI,
retries: process.env.CI ? 2 : 0,
failOnFlakyTests: true,
```

`workers: 1` in CI is a common setting and a mistake. It does not fix inter-test coupling; it
arranges for the coupling not to be observed, while multiplying wall time by the worker count. It
also contradicts every per-worker isolation mechanism the suite might use. Use a percentage so the
count follows the runner size, and keep `--workers=1` as a diagnostic only.

`forbidOnly` makes a stray `test.only` fail the build instead of silently reducing the suite to one
test — a green run that executed 1 of 400 tests is the worst possible outcome.

## Sharding, and the granularity trap

Verified on a 10-test suite spread over 4 files:

```
# default (fullyParallel off) — shards split by FILE
  shard 1/3 = 7
  shard 2/3 = 0
  shard 3/3 = 3

# --fully-parallel — shards split by TEST
  shard 1/3 = 4
  shard 2/3 = 3
  shard 3/3 = 3
```

Without `fullyParallel`, `--shard` distributes *files*. A suite whose tests are unevenly
distributed across files therefore gets unevenly distributed shards — in the measured case one
shard received **zero** tests, finished green in seconds, and proved nothing, while another took
70% of the work. The job's wall time does not improve, which is usually the reason sharding was
added in the first place.

So the order of operations is: make the tests isolated, turn on `fullyParallel`, then shard. Adding
shards to a file-serial suite is the step that appears to do nothing.

Do not shard a suite that finishes in a few minutes — the fixed cost of a runner, a checkout, an
install and a report merge per shard exceeds the saving.

## Blob reports and `merge-reports`

Each shard produces its own report, so a sharded run cannot emit one HTML report directly. Use the
`blob` reporter and merge:

```ts
reporter: process.env.CI ? [['blob'], ['github']] : [['html', { open: 'never' }], ['list']],
```

```yaml
  e2e:
    strategy:
      fail-fast: false
      matrix: { shard: [1, 2, 3, 4] }
    steps:
      - run: npx playwright test --shard=${{ matrix.shard }}/4
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: blob-${{ matrix.shard }}
          path: blob-report/
          retention-days: 7

  report:
    needs: e2e
    if: always()
    steps:
      - uses: actions/download-artifact@v4
        with: { pattern: blob-*, path: all-blob-reports, merge-multiple: true }
      - run: npx playwright merge-reports --reporter=html,github ./all-blob-reports
      - uses: actions/upload-artifact@v4
        with: { name: playwright-report, path: playwright-report/ }
```

`merge-reports` is a top-level Playwright command (`merge multiple blob reports (for sharded tests)
into a single report`, from `npx playwright --help`). `fail-fast: false` on the matrix matters: with
the default, one failing shard cancels the others and the merged report is missing most of the
suite.

## Artifacts that survive the runner

Three defects recur in review:

- **Upload only on success.** `actions/upload-artifact` does not run after a failed step unless
  `if: always()`. The artifacts you need are exactly the ones a failure produces.
- **One artifact name across a matrix.** Four shards uploading `playwright-report` collide. Include
  the shard index in the name.
- **Report without `test-results/`.** The HTML report links to traces, screenshots and videos that
  live in `test-results/`; uploading only `playwright-report/` gives you a report whose links are
  dead. Upload both, or merge blobs (which carry the attachments).

Set `retention-days` deliberately — traces are large and the default retention on a busy repository
is a real cost.

## Making the job fail when it should

- `failOnFlakyTests: true` (or `--fail-on-flaky-tests`). Verified: without it a run with a non-zero
  flaky count exits **0**; with it, exit **1**.
- `forbidOnly: !!process.env.CI`.
- `globalTimeout` as a circuit breaker, so a hung suite fails rather than burning the job limit.
- `--max-failures` on a pre-merge job if you want fast feedback — but not on the nightly run, where
  the full picture matters.

## Which browsers, how often

Running Chromium, Firefox, WebKit and a mobile emulation on every push multiplies the suite by four
for a marginal increase in signal — most defects a second engine catches are CSS, and those are
caught by the engine your users actually use plus a visual check.

A defensible split: Chromium on every push; the full matrix nightly and before a release. State the
trade-off explicitly rather than quietly deleting projects — a team that supports Safari needs
WebKit somewhere in the pipeline.

## Secrets and supply chain

- No credential literal in the workflow file. A password or API key written inline is in version
  control and in every fork's history; move it to repository secrets and reference it.
- Pin third-party actions to a commit SHA rather than a tag. A tag is mutable.
- Pin the container image by version, and consider a digest for a release pipeline.
- Do not upload the authentication state file as an artifact — it is a live session.
- A trace records network bodies and DOM snapshots. A trace of a form that received a real
  credential is a recording of that credential; use throwaway test accounts.

GitHub Actions hardening beyond this — `permissions`, `pull_request_target`, script injection, OIDC
— is the `github` skill's territory.

## The job skeleton

Combining the above, the parts that are specific to a browser suite:

```yaml
jobs:
  e2e:
    runs-on: ubuntu-latest
    container: { image: mcr.microsoft.com/playwright:v1.63.0-noble }
    strategy:
      fail-fast: false
      matrix: { shard: [1, 2, 3, 4] }
    env:
      PLAYWRIGHT_HTML_OPEN: never
      BASE_URL: http://localhost:3000
      TEST_USER_PASSWORD: ${{ secrets.TEST_USER_PASSWORD }}
    steps:
      - uses: actions/checkout@v5
      - run: npm ci
      - run: npx playwright test --shard=${{ matrix.shard }}/4
      # then the blob upload and merge job shown above
```

`PLAYWRIGHT_HTML_OPEN: never` is set at job level so nothing in the repository's own npm scripts
can start a report server and hang the job.

## Review checklist

- [ ] Image tag or cache key moves with the `@playwright/test` version.
- [ ] No `--with-deps` on a non-Debian base; the image carries the libraries instead.
- [ ] `webServer` with a health URL, not a background process plus `sleep`.
- [ ] `fullyParallel: true` before any sharding; `workers` a percentage, not 1.
- [ ] Shard counts come back roughly equal; no empty shard.
- [ ] `blob` reporter per shard, `merge-reports` in a dependent job, `fail-fast: false`.
- [ ] Artifacts uploaded with `if: always()`, distinct names per shard, including `test-results/`.
- [ ] `forbidOnly` and `failOnFlakyTests` on; traces `on-first-retry`.
- [ ] No credential literal; actions pinned to SHAs; state files not uploaded.

<!-- sources: playwright-docs, playwright-runtime, testdino-playwright, currents-best-practices, ms-playwright-cli, lambdatest-playwright, anthropics-webapp-testing -->
