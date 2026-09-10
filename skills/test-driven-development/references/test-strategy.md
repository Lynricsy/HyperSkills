# Test strategy

Read this when choosing where a test goes, what kind of test a behaviour needs,
or how to find a repository's real test commands.

## Contents

- [Discover the stack](#discover-the-stack)
- [Choosing the seam](#choosing-the-seam)
- [Kinds of test](#kinds-of-test)
- [Test sizes](#test-sizes)
- [How many tests](#how-many-tests)
- [DAMP over DRY](#damp-over-dry)
- [Arrange, act, assert](#arrange-act-assert)
- [Naming](#naming)

## Discover the stack

The loop is universal; the commands never are. Before the first test, find the
commands this repository actually uses, and use them for every red, green and
completion step.

- [ ] Language and build system: `package.json`, `pyproject.toml`, `go.mod`,
      `Cargo.toml`, `Gemfile`, `pom.xml`, `build.gradle`, `Makefile`,
      `justfile`.
- [ ] Checked-in wrappers first: `./gradlew`, `./mvnw`, `make test`, a script
      under `scripts/` or `bin/`. They pin the version the project expects.
- [ ] The runner and its config, and specifically how it runs one focused file
      versus the whole suite. The focused command is what you use in the loop.
- [ ] Existing conventions: where test files live, how they are named, what a
      neighbouring test file does for setup. Match them; a test in the wrong
      place may not run at all.
- [ ] Documented commands: README, CONTRIBUTING, and the CI workflow. CI is
      authoritative — those are the commands that gate merges.
- [ ] Package manager: use the one the repository declares (a lockfile, a
      `packageManager` field, a wrapper), not the one you know best.

Never assume a default. `npm test` may be missing, may be aliased to a linter,
or may run a full end-to-end suite that takes ten minutes; a Gradle, Cargo or
pytest project has an entirely different command. Record the two commands you
found before writing the first test, and quote them in the completion report.

## Choosing the seam

A seam is a place where behaviour can be substituted without editing the code
under test. Candidates, from most to least useful:

| Seam | Observes | Good for |
|---|---|---|
| Exported function or method | Return value, thrown error | Pure logic, transforms, validation |
| Module public interface | Behaviour across several calls (write then read back) | State, persistence, caches |
| Process boundary (HTTP handler, CLI entry) | Status, payload, exit code, stdout | Contracts other systems depend on |
| Injected collaborator | Calls the unit makes outward | External effects that are the contract itself |

Pick the shallowest seam that can observe the behaviour. A deeper seam sees more
but couples the test to structure that has no reason to be stable.

Two signals that the seam is wrong: the test needs enormous setup to reach the
behaviour, or it needs to substitute collaborators you own. Both say the
behaviour is not reachable from a real boundary — move it, or inject the
dependency, before writing the test.

The seam is ambiguous — and worth one question — when the module's depth is
undecided, or when two boundaries are equally plausible and they would observe
different things. Everything else is a decision you can make and state.

## Kinds of test

```
        /\        end-to-end: real browser or real deployment, whole flows
       /  \       few; only the paths whose failure is unacceptable
      /----\
     /      \     integration: several units, a real database or filesystem
    /        \    some; boundary contracts and wiring
   /----------\
  /            \  unit: one seam, no I/O, milliseconds
 /              \ most; logic, branches, boundaries, error paths
/----------------\
```

Decision guide:

- Pure logic with no side effects, or a branch and its boundaries → unit.
- Crosses a boundary you own (interface plus storage, handler plus service) →
  integration.
- A user-visible flow whose breakage would be unacceptable → end-to-end, and
  keep the count small; they are slow and they fail for environmental reasons.

If a behaviour is already covered at a lower level, do not re-cover it higher up
"for safety". Duplicated coverage doubles the maintenance and halves the signal
of the higher test.

## Test sizes

Classify by the resources a test consumes, independently of what it covers.
This is what determines whether it can run in the loop.

| Size | Constraints | Speed | Example |
|---|---|---|---|
| Small | Single process, no I/O, no network, no database | Milliseconds | Pure functions, data transforms, validation |
| Medium | Multiple processes, localhost only, no external services | Seconds | Handler plus test database, component render |
| Large | Multiple machines, external services permitted | Minutes | End-to-end flows, performance runs |

Keep the loop on small tests. A medium test in the inner loop turns the red-green
cycle into a coffee break, and a large one turns it into a different task.

## How many tests

Ship the tests the behaviour needs and only those. Trivial code and human prose
earn none. A test written to satisfy a rule costs maintenance forever and
protects nothing, and it is indistinguishable — to the next reader — from a test
that matters.

The pyramid above is a shape, not a quota. There is no coverage number to
defend: a coverage target is satisfied most cheaply by padding, which is the
opposite of what tests are for. The real question per behaviour is the mutation
question — which realistic wrong version of this code would go undetected — and
that is the only budget worth tracking.

## DAMP over DRY

In production code, remove duplication. In tests, prefer descriptive and
meaningful phrases: each test should read as a complete specification without
the reader tracing through shared helpers.

```typescript
// Each test tells its whole story
it('rejects an empty title', () => {
  expect(() => createTask({ title: '', assignee: 'user-1' }))
    .toThrow('Title is required');
});

it('trims surrounding whitespace from the title', () => {
  expect(createTask({ title: '  Buy groceries  ', assignee: 'user-1' }).title)
    .toBe('Buy groceries');
});
```

Extract a helper when it hides irrelevant construction (a factory returning a
complete fixture), not when it hides the values the test is about. The line to
hold: the reader must see the input and the expected output in the test body.

## Arrange, act, assert

Three visible phases, one action:

```typescript
it('marks a task overdue once the deadline has passed', () => {
  const task = createTask({ title: 'Test', deadline: new Date('2026-01-01') });

  const result = checkOverdue(task, new Date('2026-01-02'));

  expect(result.isOverdue).toBe(true);
});
```

Two actions in one test means two tests. One assertion per concept: several
assertions about the same outcome are fine (status and timestamp of one
completion); assertions about three different behaviours hide each other,
because the first failure stops the test.

## Naming

Name the behaviour and its condition, in the project's domain vocabulary — read
project context docs if present (CONTEXT.md, ADRs, CONTRIBUTING) so test names
use the same words as the code and the tickets.

```
sets status to completed and records the completion time
throws NotFoundError for an unknown task id
is idempotent: completing an already-completed task changes nothing
```

Not: `works`, `handles errors`, `test 3`, or `calls repository.save`. The first
three say nothing; the last documents the implementation, so it stops being true
the moment the method is renamed. An `and` in a name that joins two behaviours
is a request to split the test.

<!-- sources: addy-tdd, mattpocock-tdd, obra-tdd -->
