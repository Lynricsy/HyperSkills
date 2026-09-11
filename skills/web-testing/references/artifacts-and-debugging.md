# Artifacts and debugging

Verified against: Playwright 1.63.0.

## Contents

- [Pick the artifact by the question](#pick-the-artifact-by-the-question)
- [What is actually inside a trace](#what-is-actually-inside-a-trace)
- [`error-context.md`](#error-contextmd)
- [Trace modes](#trace-modes)
- [Reading a trace](#reading-a-trace)
- [Screenshots and videos](#screenshots-and-videos)
- [Console and network without a trace](#console-and-network-without-a-trace)
- [Interactive tools: `--ui` and `--debug`](#interactive-tools---ui-and---debug)
- [Driving a paused test](#driving-a-paused-test)
- [Keeping an automated run from hanging](#keeping-an-automated-run-from-hanging)
- [Narrowing the run while iterating](#narrowing-the-run-while-iterating)
- [The diagnosis order](#the-diagnosis-order)

## Pick the artifact by the question

| Question | Artifact |
|---|---|
| What did the test do, and what was the page at each step? | trace |
| What did the page look like at the moment of failure? | screenshot (`only-on-failure`) |
| What happened over time, for a human to watch? | video |
| Which request failed, with what body? | trace's network tab |
| What did the app log? | trace's console tab, or a `page.on('console')` handler |
| Which assertion failed, and against what accessibility tree? | the reporter output plus `error-context.md` |

The trace subsumes most of the others. A screenshot is one frame with no context; a video shows
motion but nothing you can inspect; a trace carries the DOM at each step, so you can hover an
element in the recorded snapshot and see what the selector would have matched.

## What is actually inside a trace

Verified by listing a `trace.zip` produced by a failing test:

```
        0  0-trace.network
       93  0-trace.stacks
      273  0-trace.trace
     2065  1-trace.network
       93  1-trace.stacks
     7136  1-trace.trace
     2989  attachments/3973238c4eeb066b9fa95505347c98384e126d87
      869  resources/0f8151927668e1f6b743230503adf6f018bcaec2.html
     2459  screencast/page@…-1789103333313.jpeg
     4509  screencast/page@…-1789103333330.jpeg
     4509  screencast/page@…-1789103333346.jpeg
     1573  src/1d3b1c6e1b232fa5ff69ba2573f69063cf6bafd2.ts
     6431  test.trace
```

Six kinds of content: action events (`*.trace`), call stacks (`*.stacks`), the network log
(`*.network`), DOM snapshot resources (`resources/`), a per-step screencast (`screencast/*.jpeg`),
the test source (`src/`), and attachments. That inventory is the reason a trace is enough to
diagnose a CI failure without rerunning it — which matters, because a flake often refuses to
reproduce.

The cost is real: tracing slows the run and the archives are large, which is why `trace: 'on'`
everywhere is the wrong default in CI.

## `error-context.md`

Alongside the trace, a failed test writes a Markdown file intended to be read by an agent:

```
# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: exp.spec.ts >> strict mode: two Submit buttons
- Location: tests/exp.spec.ts:18:5

# Error details

Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Submit' }) resolved to 2 elements:
    1) <button class="btn" id="nav-submit">Submit</button> aka locator('#nav-submit')
    2) <button class="btn" type="button" id="form-submit">Submit</button> aka locator('#form-submit')

Call log:
  - waiting for getByRole('button', { name: 'Submit' })

# Page snapshot
```

The `# Page snapshot` section carries the accessibility tree at the moment the matcher failed,
which is usually the fastest route to the answer: it shows what the locator *should* have been.
Read this file before opening the trace viewer — it is text, it is small, and it often contains the
whole diagnosis. Attach it in `afterEach` if the reporter in use does not surface it.

## Trace modes

The `--trace` choices in 1.63.0, read from `--help`:

```
--trace <mode>   Force tracing mode (choices: "on", "off", "on-first-retry", "on-all-retries",
                 "retain-on-failure", "retain-on-first-failure", ...)
```

| Mode | Behaviour | Use |
|---|---|---|
| `off` | never | never in CI — this is why failures are unreproducible |
| `on` | always, kept always | local debugging of one file |
| `on-first-retry` | recorded on the first retry only | **the CI default.** Costs nothing on passing runs |
| `retain-on-failure` | recorded always, kept only for failures | when `retries: 0` and you still need traces |
| `on-all-retries` | every retry | a flake that only appears on the third attempt |
| `retain-on-failure-and-retries` | keeps the failing attempt *and* its retries | **while hunting a specific flake** |

Two gotchas. `on-first-retry` produces nothing when `retries` is 0, which is the usual reason a
"we have tracing on" config yields no traces — pair it with retries, or use `retain-on-failure`.
And `retain-on-failure-and-retries` is the mode that matters for flake triage specifically, because
`on-first-retry` discards the original failing attempt, leaving nothing to compare the passing
retry against.

## Reading a trace

```bash
npx playwright show-trace test-results/<dir>/trace.zip
```

An order that gets to the answer faster than clicking around:

1. Go to the failing action in the timeline. Read its **call log** — it lists what Playwright was
   waiting for, which distinguishes "element never appeared" from "element appeared but was
   covered" from "two elements matched".
2. Look at the **before** DOM snapshot for that action, not the after. The before state is what the
   locator was evaluated against.
3. Hover the elements in the snapshot. The recorded snapshot is interactive; you can see which node
   the selector would have matched and what its computed state was.
4. Open the **network** tab and filter to the window around the failure. A 401, a 500 or a request
   that never fired explains most "element never appeared" failures.
5. Open the **console** tab. An unhandled exception in the app at that moment turns a puzzling test
   failure into an application bug report.
6. Only then look at the source tab and consider changing the test.

Step 4 and 5 are the ones people skip, and they are where the test turns out to be right and the
application wrong.

## Screenshots and videos

```ts
use: {
  screenshot: 'only-on-failure',        // cheap, always worth it
  video: 'retain-on-failure',           // recorded always, kept only for failures
}
```

`screenshot: 'on'` on every step bloats the report for little gain over the trace's screencast.
`video: 'on'` records every passing test too, which is the single biggest cause of a slow artifact
upload step.

Comparison screenshots are a different thing: `toHaveScreenshot` is an assertion with a stored
baseline, and it needs `animations: 'disabled'`, masked dynamic regions and a pinned viewport to be
stable:

```ts
await expect(page).toHaveScreenshot('dashboard.png', {
  animations: 'disabled',
  mask: [page.getByTestId('last-updated')],
  maxDiffPixelRatio: 0.01,
});
```

Baselines are platform-specific: a baseline generated on macOS will not match a Linux CI runner.
Generate them in the same image CI uses, or the assertion becomes a permanent false failure.

## Console and network without a trace

For an exploratory run, or where tracing is off, attach listeners:

```ts
page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
page.on('pageerror', e => console.log('PAGEERROR', e.message));
page.on('requestfailed', r => console.log('REQFAILED', r.url(), r.failure()?.errorText));
```

A page with console errors is a finding in its own right, even when the test passes: an unhandled
rejection during a flow usually means a code path that "works" only because nothing depended on
the value.

## Interactive tools: `--ui` and `--debug`

`npx playwright test --ui` opens a watch-mode UI with the trace viewer attached to every run,
time-travel over steps, and a locator picker. It is the fastest loop for a human writing tests.

`npx playwright test --debug` opens the Inspector and steps the test. The `--help` output states
its equivalent flags: `--timeout=0 --max-failures=1 --headed --workers=1`. Note `--timeout=0`: the
test will not time out while you are looking at it, and this is also why `--debug` is unusable in
CI.

Both need a display. In a headless environment they will not open, which is a reason to prefer the
trace viewer on a recorded archive plus `show-trace`.

## Driving a paused test

For a test that fails for reasons the trace does not settle, the productive loop is to pause it and
drive the live page. Playwright's CLI supports attaching to a paused run:

1. Start the test in the background with `--debug=cli` and wait until the output prints its
   debugging instructions, which include a session name.
2. Attach to that session from a second process. The test stays paused; you drive the same page.
3. Step to the point where the problem is likely, then interact. Every action taken this way is
   echoed back as Playwright TypeScript, which can be pasted into the test.
4. The fix is usually a locator or an expectation — but it can equally be an application bug. Decide
   which before editing the test.
5. Stop the background run and re-run the test normally to confirm.

`await page.pause()` in the test body is the inline equivalent when you already know where to stop.

## Keeping an automated run from hanging

Set `PLAYWRIGHT_HTML_OPEN=never`:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test
```

The HTML reporter otherwise starts a local server to show the report and does not exit, so a
non-interactive run hangs rather than failing — the most common way an automated Playwright
invocation appears to "take forever". `reporter: [['html', { open: 'never' }]]` does the same in
config; the environment variable is the one that also covers a project's own npm script.

`npx playwright show-report` has the same property: it is a server, and it must not be part of an
automated sequence.

## Narrowing the run while iterating

```bash
npx playwright test tests/checkout.spec.ts:42    # one test by line
npx playwright test -g "applies a promo code"    # by title
npx playwright test --project=chromium           # one project
npx playwright test --last-failed                # only the previous failures
npx playwright test --only-changed=origin/main   # only specs changed vs a ref
npx playwright test --max-failures=1             # stop at the first failure
```

`--headed` shows the browser; `--slow-mo` is not a test flag but a launch option
(`use: { launchOptions: { slowMo: 250 } }`) and is for watching, never for fixing a race.

## The diagnosis order

- [ ] Read the reporter's error text and call log. Half of all failures are named there.
- [ ] Read `error-context.md`, especially its page snapshot.
- [ ] Open the trace; check the before-snapshot, then network, then console.
- [ ] Decide whether the test or the application is wrong, and say which.
- [ ] If it will not reproduce, run `--repeat-each` before assuming it was infrastructure.
- [ ] Only then consider driving the page interactively.

<!-- sources: ms-playwright-cli, playwright-runtime, playwright-docs, currents-best-practices, testdino-playwright, awesome-copilot, lambdatest-playwright -->
