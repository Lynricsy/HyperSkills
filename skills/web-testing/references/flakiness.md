# Flakiness

Verified against: Playwright 1.63.0.

## Contents

- [Reproduce before theorising](#reproduce-before-theorising)
- [The four shapes](#the-four-shapes)
- [Default execution is file-serial, and that hides coupling](#default-execution-is-file-serial-and-that-hides-coupling)
- [Retries are a diagnosis budget, and the exit code lies](#retries-are-a-diagnosis-budget-and-the-exit-code-lies)
- [Isolation without serializing the suite](#isolation-without-serializing-the-suite)
- [`test.lock` — verified](#testlock--verified)
- [Timing flakes inside one test](#timing-flakes-inside-one-test)
- [Environment flakes](#environment-flakes)
- [Infrastructure flakes](#infrastructure-flakes)
- [Quarantine, honestly](#quarantine-honestly)
- [Burn-in before merge](#burn-in-before-merge)
- [Measuring whether it worked](#measuring-whether-it-worked)

## Reproduce before theorising

A flake that has not been reproduced on demand cannot be fixed, only guessed at. Three commands,
each answering a different question:

```bash
npx playwright test <file> --repeat-each=20                  # is it a race inside the test?
npx playwright test <file> --repeat-each=20 --fully-parallel  # is it coupling between tests?
npx playwright test <file> --workers=1                       # does serializing make it go away?
```

Verified on a test whose page delay was randomised between 50 ms and 900 ms behind a
`waitForTimeout(400)`:

```
$ npx playwright test -g "genuinely racy" --repeat-each=10 --reporter=line
  5 failed
  5 passed (1.1s)
```

That is the goal state: a 50% failure rate under repetition is a deterministic bug, not a mystery.
All three commands are diagnostics. `--workers=1` in particular is not a fix — see below.

## The four shapes

| Shape | Signature | Remedy |
|---|---|---|
| **Timing** inside one test | reproduces under `--repeat-each` at any worker count | replace the wait with a retrying assertion; fix the actual race if the app has one |
| **Isolation** between tests | passes alone or with `--workers=1`, fails in the suite or under `--fully-parallel` | remove shared state; per-worker accounts; `lock` for contended resources |
| **Environment** | CI only, or one machine only | pin viewport and device scale, stub third parties, freeze time, pin the image |
| **Infrastructure** | no pattern; browser-internal errors, `Target page, context or browser has been closed` | version lockstep, memory headroom, read the trace for the step that actually died |

The classification matters because the remedies do not transfer. Adding retries to an isolation
flake makes the suite slower and still wrong; adding `--workers=1` to a timing flake makes it
slower and hides nothing at all.

## Default execution is file-serial, and that hides coupling

Playwright's default (`fullyParallel: false`) runs *files* in parallel and *tests within a file*
serially in one worker, in declaration order. So a module-level variable written by one test and
read by the next works — as a scheduling accident.

Verified. A file where test A writes `token` and test B reads it, plus a genuinely racy test C:

```
$ npx playwright test flaky.spec.ts --reporter=line
  3 passed (1.0s)

$ npx playwright test flaky.spec.ts --reporter=line --fully-parallel
  2 failed
    tests/flaky.spec.ts:12:5 › B: depends on A having run
    tests/flaky.spec.ts:17:5 › C: genuinely racy
  1 passed (890ms)
```

Consequences for review: a green suite is not evidence of isolation, and the first person to turn
on `fullyParallel` (usually so that sharding splits by test rather than by file) inherits
every latent coupling at once. The coupling patterns to grep for:

- module-level `let` written by one test and read by another;
- `beforeAll` that logs in, stores a token, and closes its page;
- ordinal test titles (`01 - adds an item`, `02 - cart shows the item added by 01`);
- a fixed record id, email or slug that two tests both write;
- an assertion on a count or a total that only holds if no other test has touched the data.

Each has the same fix: the test creates what it needs and cleans up, ideally through an API fixture
rather than the UI.

## Retries are a diagnosis budget, and the exit code lies

`retries: 2` in CI, `0` locally is the right setting — but it is a budget for *learning* that a
test is unreliable, not a repair. The trap is the exit code. Verified:

```
$ npx playwright test -g "genuinely racy" --repeat-each=8 --retries=3 --reporter=line ; echo $?
  2 flaky
  6 passed (2.7s)
no-flag exit=0

$ npx playwright test -g "genuinely racy" --repeat-each=8 --retries=3 --fail-on-flaky-tests ; echo $?
  3 flaky
  5 passed (3.6s)
with-flag exit=1
```

A run with a non-zero flaky count exits **0**. So "CI has been green for weeks" is compatible with
a third of the suite being racy, and nobody finds out until a flake's probability drifts past the
retry budget. `--fail-on-flaky-tests` (or `failOnFlakyTests: true`) makes the flaky count fail the
job, which is the only way the number becomes visible.

Two further consequences:

- `retries: 3` outside a quarantine project is an admission that 2 was not enough, which means the
  failure rate is high enough to be a bug. Fix it or quarantine it.
- Surface the count even if you are not yet ready to fail on it:

```ts
test.afterEach(async ({}, testInfo) => {
  if (testInfo.retry > 0 && testInfo.status === 'passed') {
    console.log(`FLAKY ${testInfo.titlePath.join(' > ')} (passed on retry ${testInfo.retry})`);
  }
});
```

## Isolation without serializing the suite

`workers: 1` is the reflex fix and the wrong one. It does not remove the coupling; it arranges for
the coupling not to be observed, while multiplying CI wall time by the worker count. It also
contradicts everything else a suite needs — per-worker accounts, sharding, `workerInfo.workerIndex`
— all of which presuppose more than one worker.

The ladder, narrowest first:

1. **Make the test self-sufficient.** Create its data, act, assert, clean up. This removes the
   problem rather than scheduling around it.
2. **Per-worker resources.** A worker-scoped fixture keyed on `workerInfo.workerIndex` gives each
   worker its own account, tenant or record namespace.
3. **`{ lock: 'name' }`** (Playwright 1.63+) for a genuinely shared resource that cannot be
   partitioned. Only tests naming the same lock queue; everything else stays parallel.
4. **A single-worker project** for a small set of tests whose writes are globally visible —
   organisation settings, feature flags, tax rules. `projects: [{ name: 'admin', workers: 1, ... }]`.
5. **`test.describe.configure({ mode: 'serial' })`** when a file genuinely models a sequence of
   steps and a failure should skip the rest. Note the tension: a serial block *is* an ordering
   dependency, so prefer 3 or 4 when the real reason is contention rather than sequence.

`mode: 'parallel'` is the inverse escape hatch: it opts one file into full parallelism while the
project default stays file-serial.

## `test.lock` — verified

Four tests entering the same critical section, four workers, full parallelism. The only difference
between the two files is the `lock` key:

```ts
for (const n of ['a', 'b', 'c', 'd']) {
  test(`locked ${n}`, { lock: 'shared-resource' }, async () => {
    await criticalSection(n);     // throws if another test is already inside
  });
}
```

```
$ npx playwright test tests/lock.spec.ts --fully-parallel --workers=4 --reporter=line
Running 4 tests using 4 workers
  4 passed (1.9s)

$ npx playwright test tests/nolock.spec.ts --fully-parallel --workers=4 --reporter=line
Running 4 tests using 4 workers
    Error: OVERLAP: a entered while b held it
    Error: OVERLAP: d entered while b held it
    Error: OVERLAP: c entered while b held it
  3 failed
  1 passed (704ms)
```

Locks are named and cross-file: tests in different files and different projects that declare the
same lock name never run concurrently. That makes it the right tool for "these six tests fight over
one staging tenant" without touching the other 174.

## Timing flakes inside one test

Almost all of them are one of:

- a fixed wait in front of an assertion;
- an assertion on an awaited value rather than on the locator;
- a navigation-triggering click followed immediately by an assertion on the new page — assert
  `toHaveURL` first, or assert on an element that only exists after the navigation;
- an event waiter created after the action that triggers it;
- a dialog handler registered after the click that opens the dialog;
- an animation moving the target, so a click lands on the previous position. `stable` covers the
  common case; for CSS that animates indefinitely, `page.emulateMedia({ reducedMotion: 'reduce' })`
  if the app honours it, and `toHaveScreenshot(..., { animations: 'disabled' })` for screenshots.

Do not reach for `contextOptions.reducedMotion` — `reducedMotion` is a top-level `use` option, and
in any case it sets a media feature rather than stopping unconditional animations.

## Environment flakes

CI-only failures usually come from the environment differing in a way the test depends on:

- **Viewport and device scale.** Pin them (`viewport: { width: 1280, height: 720 }`,
  `deviceScaleFactor: 1`) so a different default does not change what is on screen or in a
  screenshot.
- **Third parties.** Analytics, chat widgets, ad tags, font CDNs and maps all fail differently in
  CI. Stub them at the route level: `await page.route('**/*.analytics.com/**', r => r.abort())`.
- **Time.** A test that depends on the date, a countdown, or a "today" filter needs `page.clock`
  rather than tolerance.
- **Locale and timezone.** Set `locale` and `timezoneId` in `use`; a CI runner in UTC formats
  currency and dates differently from a laptop.
- **Machine speed.** A shared runner is slower and noisier. This should not matter if no test
  contains a fixed wait — if it does matter, that is the finding.

Reproduce locally with `CI=true npx playwright test --repeat-each=10`, which picks up the
CI-conditional branches of the config.

## Infrastructure flakes

`Target page, context or browser has been closed`, `browserType.launch` failures, crashes with no
stack. The first move is not to raise a timeout — it is to read the trace and find the last step
that actually ran.

- A missing executable after a cache restore is a version mismatch, not a flake.
- A crash under parallel load is often memory: the container has fewer resources than the laptop,
  and each worker is a browser. Reduce workers to a percentage of CPU rather than a constant, and
  check the runner's memory limit.
- A context closing mid-test usually means the test's own teardown ran early — a fixture that
  closed the context while an assertion was still pending, or a `use()` that returned before the
  awaited work finished.

## Quarantine, honestly

Quarantine is a config decision with a visible name, not a `try/catch` and not `retries: 5`:

```ts
projects: [
  { name: 'stable', testIgnore: ['**/*.flaky.spec.ts'] },
  { name: 'quarantine', testMatch: ['**/*.flaky.spec.ts'], retries: 3 },
]
```

Run `stable` as the merge gate and `quarantine` as a non-blocking job. Two rules keep it from
becoming a landfill: every quarantined test carries an issue link, and the quarantine project's
size is reported, so it is visible when it grows. `test.fixme` with a link is the right marker for
a test that is currently wrong; `test.skip` with no explanation is how tests die quietly.

## Burn-in before merge

A new end-to-end test should be proven stable before it becomes everyone's problem:

```bash
npx playwright test <new-file> --repeat-each=50                     # is it deterministic?
npx playwright test <new-file> --repeat-each=20 --fully-parallel     # does it survive neighbours?
```

For a suite already in place, `--only-changed` restricts the run to specs touched relative to a
ref, and `--last-failed` re-runs only the previous failures — both useful in the iteration loop,
neither a substitute for the full run in CI.

## Measuring whether it worked

A flake is fixed when the measurement that exposed it no longer does:

- [ ] The formerly failing test passes `--repeat-each=50`.
- [ ] The file passes `--repeat-each=20 --fully-parallel`.
- [ ] The full suite's flaky count is zero with `--fail-on-flaky-tests` enabled.
- [ ] The fix names a mechanism (a race, a shared record, an unstubbed third party), not "added a
      wait" or "reduced workers".

If the fix was to raise a timeout, reduce workers, or add a retry, the flake was not fixed. It was
rescheduled.

<!-- sources: playwright-runtime, playwright-docs, currents-best-practices, testdino-playwright, lambdatest-playwright, vercel-agent-browser -->
