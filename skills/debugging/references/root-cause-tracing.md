# Root-cause tracing

Bugs surface far from where they are born. A file created in the wrong
directory, a database opened with the wrong path, a string where a number was
expected — the frame that throws is the frame that finally used the bad value,
not the one that made it. Tracing means walking backwards until you reach the
place that created it, then fixing there.

## Contents

- [The backward walk](#the-backward-walk)
- [Reading the stack in the right direction](#reading-the-stack-in-the-right-direction)
- [Stack-capture probes](#stack-capture-probes)
- [Finding which test pollutes shared state](#finding-which-test-pollutes-shared-state)
- [Layering guards after the fix](#layering-guards-after-the-fix)
- [Worked example](#worked-example)

## The backward walk

Five questions, asked in order, each answered from code or from a probe — never
from memory:

1. **What is the observed symptom, precisely?** The exact message, the exact
   wrong value, the exact path that should not exist.
2. **Which line directly caused it?** The operation that used the bad value.
   This is where the instinct to fix is strongest and where fixing is wrong.
3. **What called that, with what value?** Read the argument, do not infer it.
4. **Where did that value come from?** Repeat step 3 until the answer is a
   literal, a parse, a default, a config read or an external input. That is the
   origin.
5. **Why was the wrong value acceptable there?** Usually a missing coercion, a
   missing validation, a default that lies (an empty string that means "not
   set"), or two modules disagreeing about a type.

Stop conditions: you reach a value the program did not create (user input, a
response body, an environment variable) — validate at that boundary; or you
reach a place where the value is created deliberately — the contract is what
is wrong, and both sides need to agree.

If the walk dead-ends because the chain crosses a process, a queue or a network
hop, the trace continues on the other side. Instrument the boundary and carry a
correlation id across it rather than declaring the far side innocent.

## Reading the stack in the right direction

Know which end of the printed trace is the innermost frame in this language
before you draw conclusions: Python and Java print the innermost frame last,
V8 and Go print it first. Naming a "top frame" without knowing the convention
is how the wrong function gets blamed.

Then read the whole trace, not the innermost frame:

- The innermost frame is where the value was **used**.
- The first frame belonging to project code — not to a framework or standard
  library — is usually where the value was **passed in**.
- A frame from a test harness or fixture in the middle of the chain means the
  setup produced the value, which is a different bug from the one the message
  describes.

## Stack-capture probes

When manual reading runs out (dynamic dispatch, callbacks, a framework in the
middle), make the program tell you who called:

```
def git_init(directory):
    # [DEBUG-a4f2] who calls this, and with what?
    log_stderr("[DEBUG-a4f2] git_init", {
        "directory": directory,
        "cwd": os.getcwd(),
        "env": {k: v for k, v in os.environ.items() if k in WATCHED},
        "stack": "".join(traceback.format_stack()),
    })
    run(["git", "init"], cwd=directory)
```

Rules that make the difference between a useful capture and noise:

- Write to standard error, not the application logger. Loggers get suppressed,
  buffered or filtered in tests, and a probe you cannot see reads as "the code
  never ran".
- Probe **before** the dangerous operation, not in its error handler. If the
  operation crashes the process or corrupts state, the handler never runs.
- Include the context that distinguishes hypotheses: the argument, the working
  directory, the resolved config, the relevant environment variables, a
  timestamp. Do not dump whole objects; pick the fields.
- Filter what you keep: run the loop, then grep for the tag rather than reading
  the whole output.
- Then analyse across occurrences: same caller every time, or several? Same
  parameter, or a pattern? One caller means a bug in that path; every caller
  means the contract is wrong.

## Finding which test pollutes shared state

When something appears during a suite run — a stray file, a leaked table row, a
mutated global — and you cannot tell which test did it, bisect over test files
with the artifact as the predicate:

```bash
# Loop over test files one at a time, in a clean state, and stop at the
# first one that creates the artifact.
for f in $(find . -name 'test_*.py' | sort); do
  rm -rf "$ARTIFACT"
  <the project's single-file test command> "$f" >/dev/null 2>&1 || true
  if [ -e "$ARTIFACT" ]; then echo "polluter: $f"; break; fi
done
```

Three details decide whether this works: reset the artifact before every
iteration, ignore the test's own exit code (a failing test can still pollute),
and check for the artifact after every file rather than at the end. If nothing
is found file-by-file but the artifact appears in a full run, the cause is
cross-file ordering — bisect over the file order instead of over single files.

## Layering guards after the fix

Fixing the origin ends this bug. Adding checks along the path the bad value
travelled is what stops the next one from taking the same route — different
call paths bypass a single check, mocks bypass business logic, and platform
differences bypass both.

Add at most one guard per layer, cheapest first:

| Layer | Purpose | Shape |
|---|---|---|
| Entry point | Reject impossible input at the public boundary | Non-empty, exists, right type; raise with the offending value in the message |
| Business logic | Reject input that is valid but meaningless for this operation | Invariant checks close to the decision that depends on them |
| Environment guard | Refuse dangerous operations in the wrong context | For example: in tests, refuse to write outside the temp directory |
| Forensic probe | Keep the next occurrence diagnosable | A permanent, low-volume log line at the boundary with the identifying fields |

Then try to bypass each layer on purpose: reach the business logic without the
entry point and confirm it still refuses. A guard nobody tested is a guard that
compiles.

Two limits keep this from becoming defensive-programming sprawl: guards belong
only on the path this bug actually travelled, and each one raises loudly rather
than substituting a default. A guard that quietly repairs the value recreates
the original bug in a new place — silently.

## Worked example

**Symptom.** A `.git` directory appears inside the package source tree during
a test run, and the run leaves the repository dirty.

**The tempting fix.** Add the path to `.gitignore`, or delete the directory in
a teardown hook. The symptom disappears; the cause is untouched and the next
test that runs earlier will hit it again.

**The walk.** The operation that created it is a `git init` call with a
`cwd` argument. Its caller is the workspace initialiser, which received the
project directory from the session factory, which received it from the test's
setup helper. The helper returns a struct whose temp-directory field is an
empty string until the per-test hook fills it in — and one test reads the
field at module import time, before the hook has run. An empty `cwd` resolves
to the process working directory, which is the source tree. Origin found: a
field read before it was initialised, four frames above the failure and in a
different file.

**Why the teardown fix is wrong.** Every other operation that takes the same
directory — the database file, the config write, the artifact export — also
received the empty string. They did not fail visibly, so nobody noticed, and a
teardown that removes one artifact leaves the rest.

**The fix.** Make the field raise when read before initialisation, so the
mistake fails at the point it is made instead of resolving to a plausible
wrong value. Then guards: the session factory rejects an empty directory, and
in test runs the git wrapper refuses to operate outside the temp directory.

<!-- sources: obra-debugging, mattpocock-diagnosing, pproenca-debug -->
