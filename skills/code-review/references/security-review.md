# Security-aware review of a change

Read when a high-risk trigger fires on the diff. This reviews a delta against its base; it is
not a whole-codebase audit.

## Contents

- [The standing security lens](#the-standing-security-lens)
- [Risk classification](#risk-classification)
- [Depth by codebase size](#depth-by-codebase-size)
- [History of what was removed](#history-of-what-was-removed)
- [Blast radius](#blast-radius)
- [Coverage of the changed code](#coverage-of-the-changed-code)
- [Attack scenarios](#attack-scenarios)
- [Escalation triggers](#escalation-triggers)
- [The report](#the-report)

## The standing security lens

Every review, however small, answers these. They are cheap and they catch most of what matters:

- Is every request field the change reads validated at the boundary, before it reaches storage
  or business logic?
- Are queries parameterized, with no value concatenated or interpolated into a statement?
- Is output encoded for its sink, so injected markup or control characters cannot escape?
- Is authorization checked on the path the change added or modified — not only authentication?
- Do secrets stay out of source, logs and version control? Does the change log a token, a raw
  request body, or personal data?
- Is data from outside the process — APIs, webhooks, files, config, other services — treated as
  untrusted at the point it enters?
- Are new dependencies from a maintained source with a compatible licence and no open advisory?

A finding here is a normal Standards finding. What follows is the escalation.

## Risk classification

Classify each changed file, then let the class set the effort. Classify by **what the code
does**, never by how many lines moved: two removed lines have shipped a CVE more than once.

| Class | Triggers |
|---|---|
| HIGH | Authentication, authorization, session handling, cryptography or signature verification, value transfer, calls to external systems, and any removal or weakening of validation |
| MEDIUM | Business logic, state transitions, new public API surface, permission-adjacent configuration |
| LOW | Comments, tests, UI copy, logging that carries no sensitive data, formatting |

A refactor touching HIGH code is HIGH until you have shown the invariants survived it.
Refactors are where invariants quietly die.

## Depth by codebase size

Measure once (`git ls-files | wc -l`) and commit to a depth, so the review finishes:

| Size | Depth |
|---|---|
| Under 20 files | Read the changed code and its dependencies; blame everything the diff removed. |
| 20–200 files | Read the changed code and one hop of callers and callees; blame removals in HIGH files. |
| Over 200 files | Follow only the paths the change can actually reach from an entry point; blame HIGH removals. |

Say in the report which depth you used. A conclusion is only as broad as the reading behind it.

## History of what was removed

The most valuable evidence in a differential review is why the deleted line existed.

```bash
# Who added this guard, and in what kind of commit
git log -S '<removed expression>' --oneline
git blame <base> -- path/to/file

# Was this code removed for safety once and is now coming back
git log -S '<added expression>' --oneline -p
```

Read the commit subjects you land on:

- Removed in a change whose history says fix, security, hardening, or names a CVE or advisory →
  **Critical** until the author explains what replaced it.
- Added recently and removed again within weeks → HIGH; the reason it was added is probably
  still true.
- Previously removed *for* safety and now re-added → a regression, and report it as one, naming
  both commits.

Ask the same question about defence in depth. If the same check appears in several places and
the diff removes one instance, the remaining ones may be the only reason nothing broke in
testing — the layer is thinner than the suite can show.

## Blast radius

For each changed symbol, count who depends on it, and cross that with the risk class:

```bash
grep -rn '<symbol>(' src lib | wc -l      # direct callers
grep -rn "from '.*<module>'" src | wc -l  # importers, for a whole-module change
```

| Callers | Radius |
|---|---|
| 1–5 | Local |
| 6–20 | Moderate |
| 21–50 | Wide |
| Over 50 | Systemic |

A HIGH-risk change with a wide or systemic radius is the first thing you review, and it is the
finding that decides the verdict. Note second entry points explicitly: a replay tool, a cron
job, an admin path or a queue consumer that reaches the same function bypasses whatever guard
sits on the HTTP route.

Counting is not optional because transitive callers are exactly what intuition misses.

## Coverage of the changed code

Split the diff into production changes and test changes, then ask which changed lines no test
executes:

```bash
git diff <base>...HEAD --name-only | grep -v -E '(^|/)(test|tests|spec)/'
git diff <base>...HEAD --name-only | grep -E '(^|/)(test|tests|spec)/'
```

Raise the severity, do not just note it:

- New function with no test → one class higher.
- Validation changed while its tests did not → HIGH, because the tests still describe the old
  contract.
- More than a screenful of new branching with no test → HIGH.
- A test edited so that it can no longer fail → Critical, independent of the code change.

## Attack scenarios

Every HIGH finding needs one concrete path, in this shape. Generic warnings are not findings and
authors correctly ignore them:

```text
Goal:           what the attacker gets
Preconditions:  what they need first — a route, a token, a state, nothing
Steps:          1. concrete request or action
                2. what the changed code does with it
                3. the resulting effect
Why it works:   the changed lines, cited
Impact:         who is affected and how badly
```

Write only what the change enables. Inventing an exotic scenario to justify a severity is the
same failure as rubber-stamping, in the other direction.

## Escalation triggers

Stop the pass and investigate before writing anything else:

- A guard removed with nothing put in its place.
- An access-control modifier loosened, or a visibility widened.
- Signature or token verification removed, skipped conditionally, or made non-fatal.
- An allowlist that became inert (a wildcard entry, an always-true condition, a default of
  "allow").
- A new external call added on a path with no timeout, no error handling and no validation of
  what comes back.
- A HIGH change with a systemic blast radius.
- A dependency bump that also changes code the dependency does not require.

## The report

Write the review to a file, tell the user its path, and keep the artefact — findings that live
only in a chat message are lost by the next turn.

```markdown
# Security review — <branch or PR> (<base>...<head>)

## Summary
Risk: <Critical|High|Medium|Low>   Verdict: <Ready to merge: Yes|No|With fixes>
Depth: <deep|focused|surgical>, chosen for <N> files in the repository.
Counts: <n> Critical, <n> Important, <n> Minor.

## What changed
| File | Risk | Blast radius | Tests cover the change |
|---|---|---|---|

## Findings
### [Critical] <title>
File: <path:line>   History: <commit> "<subject>"
Blast radius: <n> callers   Coverage: none
What changed and why it matters.
Attack scenario: <the block above>
Fix: <the smallest change that restores the invariant>

## Not examined
What the chosen depth excluded, and what would change the conclusion if it were reviewed.
```

The "Not examined" section is mandatory. A review that implies completeness it does not have is
worse than a narrow review that says so.

<!-- sources: trailofbits-diffreview, addyosmani-review, obra-requesting-review -->
