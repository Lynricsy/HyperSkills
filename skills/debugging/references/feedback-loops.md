# Feedback loops

The loop is the whole game. A tight, red-capable loop turns a hard bug into a
mechanical exercise; without one, hypothesis testing is guesswork and the fix
cannot be verified.

## Contents

- [The ten constructions](#the-ten-constructions)
- [Tightening a loop](#tightening-a-loop)
- [Raising the reproduction rate](#raising-the-reproduction-rate)
- [Condition-based waiting](#condition-based-waiting)
- [Driving a human inside the loop](#driving-a-human-inside-the-loop)
- [When no loop can be built](#when-no-loop-can-be-built)

## The ten constructions

Ordered by how often they are the right answer. Stop at the first one that can
go red on this bug.

### 1. Failing test at the seam that reaches the bug

The default when a suite exists. Pick the shallowest seam that still exercises
the real path: a unit test that stubs the thing which is broken proves
nothing. Run the project's own focused-test command; find it in the `Makefile`,
`package.json` scripts, `pyproject.toml`, `justfile` or the CI workflow rather
than assuming a runner.

### 2. HTTP request script against a running dev server

For endpoint symptoms. Keep the request in a file so it is re-runnable and
diffable, and assert on the response rather than eyeballing it — a script that
prints 200 and exits 0 is not red-capable. Put credentials in environment
variables so the script can be shown without redaction work.

### 3. CLI invocation on a fixture input, diffed against known-good output

For commands and code generators. Commit the fixture and the expected output;
the loop becomes `run | diff -u expected -`, which exits non-zero exactly when
the symptom is present.

### 4. Headless browser script asserting DOM, console or network

For symptoms that only exist in a page. Assert the specific broken thing (this
element's text, this console error, this request's status). Screenshot-only
scripts are not loops: nothing fails.

### 5. Replay of a captured artifact

The answer when production reproduces it and your machine does not. Capture
the real input — request body, event payload, message, log window, data export
— save it to disk, and feed it through the code path in isolation. This is the
cheapest way to convert "it happens in prod" into a local red signal. Strip
secrets from the artifact as you save it, not later.

### 6. Throwaway harness calling the suspect path directly

When booting the system costs more than the bug is worth. Construct the minimum
object graph the suspect function needs, with the rest stubbed, and call it in
one function. Expect to delete this at the end; note it in the cleanup list so
you do.

### 7. Property or fuzz loop over generated inputs

For "sometimes the output is wrong". Generate several hundred inputs, run them
all, and assert the invariant rather than specific values. This also produces a
minimal counterexample for free if the generator shrinks.

### 8. Bisection harness

When it worked at a known earlier point. Automate "put the system into state X,
check, repeat" so the check is a single exit code, then let `git bisect run`
drive it. State can be a commit, a dependency version, a dataset revision or a
config file — the harness is the same shape.

### 9. Differential run

When one environment is fine and another is not. Run the same input through
both (old version and new, two configs, two hosts) and diff the outputs. The
first diverging line localises the bug without any hypothesis at all.

### 10. Human-driven loop

Last resort, for a symptom that only a person can trigger. Do not ask the user
for freeform reports; drive them with a script so each round returns the same
structured observations. See the section below.

## Tightening a loop

Treat the loop as a product with three properties, and improve each one:

| Property | Ask | Typical wins |
|---|---|---|
| Fast | Can it run in seconds? | Cache or skip unrelated setup, narrow the test selection, drop fixture data the symptom does not need, reuse a warm server |
| Sharp | Does it fail only on this symptom? | Assert the exact wrong value, not "did not throw"; assert the error type and message, not just failure |
| Deterministic | Same verdict every run? | Pin the clock, seed the RNG, isolate the filesystem in a temp dir, block or record the network, fix the locale and timezone, run single-threaded |

A thirty-second flaky loop will make you distrust your own results. A
two-second deterministic one lets you test ten hypotheses in the time the first
one used to take.

## Raising the reproduction rate

For a bug that does not reproduce on demand, the goal is not a clean repro; it
is a **higher rate**. A symptom that appears in half of runs is debuggable; one
in a thousand is not. Escalate in this order:

1. **Loop the trigger.** Run the failing case in a shell loop hundreds of
   times, counting failures. This alone converts most "cannot reproduce" into
   a rate. Report the rate — it is the baseline the fix has to beat.
2. **Run in parallel.** Several copies at once contend for the same resource,
   which is where order- and lock-dependent bugs live.
3. **Add load.** Saturate CPU, shrink available memory, throttle IO. Timing
   bugs surface when the machine is slow, which is why CI finds them and your
   laptop does not.
4. **Widen the window.** Insert a sleep, a yield or a breakpoint at the
   suspected race point. Widening the window turns a one-in-a-thousand
   interleaving into a reliable one. This is instrumentation, so tag it.
5. **Remove the accidental protection.** Fast paths, caches and retries often
   mask the failure; disable them while hunting.
6. **Isolate versus sequence.** Run the failing case alone, then after the
   suite. If it only fails after other work, the bug is shared state, not the
   case itself.

Only after all six fail is "not reproducible on this hardware" an honest
statement — and then it needs an artifact or environment access, not a theory.

## Condition-based waiting

Arbitrary delays are the single most common cause of a flaky loop. A test that
sleeps for 50 ms is asserting a guess about machine speed, so it passes on a
laptop and fails under CI load.

Wait for the condition you actually care about:

```
# guessing at timing — flaky by construction
sleep 0.05
assert result is not None

# waiting for the condition — deterministic
wait_for(lambda: result is not None, "result to arrive", timeout=5)
assert result is not None
```

A polling helper needs three things and no more: a predicate called fresh on
every iteration, a poll interval around 10 ms (1 ms burns CPU, 100 ms adds
latency to every test), and a timeout that raises with the description of what
never happened. Never poll a value captured before the loop — it cannot change.

Common shapes: wait for an event to appear in a list, for a state machine to
reach a state, for a count to reach N, for a file to exist, for a compound
predicate.

An arbitrary delay is correct in exactly one situation: you are testing timed
behaviour itself (a debounce, a throttle interval, a poll cadence). Then wait
for the triggering condition first, sleep a duration derived from the known
interval second, and write the arithmetic in a comment — "200 ms is two 100 ms
ticks" is justified; "200 ms seems enough" is a future flake.

## Driving a human inside the loop

When only a person can trigger the symptom, keep the loop structured anyway:
`scripts/hitl_loop_template.sh` prints numbered instructions, collects
answers, and prints them back as `KEY=value` lines you can parse. Copy it, edit
the block between the markers, and run it with `bash`.

Two calls are available. `step` shows an instruction and waits for the person
to press Enter — use it for actions with no observation attached, such as
signing in. `capture` asks a question and reads the answer into a variable —
use it for every observation you need back. Ask for one observation per
`capture`, phrased so the answer is a word or a pasted line, and never ask a
person to interpret ("did it look wrong?"); ask what they saw.

Each round of the human loop is expensive, so batch: ask for everything the
current hypothesis set needs in one script run rather than one question per
round.

## When no loop can be built

Stop and say so explicitly. Do not proceed to hypotheses — an untestable
hypothesis followed by a plausible edit is how a session ends with a changed
codebase and an unfixed bug.

List what you tried (each construction above and why it failed), then ask for
exactly one of:

- access to an environment where the symptom occurs;
- a redacted captured artifact: request or event dump, log window around the
  failure, core dump, database snapshot, screen recording with timestamps;
- permission to add temporary, tagged instrumentation to the failing
  environment and wait for the next occurrence.

Name the command you would run the moment the artifact exists. That converts
the ask from "I need more information" into a concrete next step.

<!-- sources: mattpocock-diagnosing, obra-debugging, addy-debugging -->
