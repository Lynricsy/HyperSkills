# Reviewer prompt

Read when dispatching one or more reviewers instead of reading the diff yourself.

## Contents

- [When to dispatch](#when-to-dispatch)
- [The template](#the-template)
- [Filling the placeholders](#filling-the-placeholders)
- [Running the axes in parallel](#running-the-axes-in-parallel)
- [Example reviewer output](#example-reviewer-output)

## When to dispatch

Read a two-file diff yourself. Dispatch for anything larger.

The reason is context economics, not politeness: as the orchestrator you still have to drive the
work after the review. Reading a large diff inline spends the window you need for that, while a
dispatched reviewer keeps the diff and the reasoning in its own context and returns only
findings. One review seat, one pass, one report.

Two rules bound the fan-out:

- The orchestrator validates the base ref and the diff **before** dispatching. A bad ref or an
  empty diff must fail in one place, not inside three reviewers at once.
- A reviewer never dispatches another reviewer. It reviews in passes itself and says in the
  report that it did.

## The template

Copy this verbatim into the subagent prompt and replace the bracketed placeholders. Do not trim
the read-only guard or the no-delegation rule; both exist because reviewers reliably violate
them.

```text
You are a senior code reviewer. Review the change described below against its
requirements and this repository's standards, and report what you find.

## What was implemented

[DESCRIPTION]

## Requirements or spec

[SPEC]

## Standards that apply

[STANDARDS_SOURCES]
[SMELL_BASELINE]

## Range to review

Base: [BASE_SHA]
Head: [HEAD_SHA]

    git diff --stat [BASE_SHA]...[HEAD_SHA]
    git diff [BASE_SHA]...[HEAD_SHA]

## Read-only review

Your review does not change this checkout. Do not modify the working tree, the
index, HEAD, or any branch. Inspect history with git show, git diff, git log and
git blame. If you need a working copy of another revision, create one somewhere
else: git worktree add /tmp/review-[BASE_SHA] [BASE_SHA]. Never move HEAD here.

## You do not dispatch subagents

Do this review yourself. Never spawn a subagent for part of the diff and never
spawn a second reviewer for another opinion. The process already allocates every
review seat this change gets; one you spawn duplicates a seat at full cost and
its verdict counts for nothing. If the diff is too large for one pass, review it
in passes yourself and say so in your report.

## What to check

Tests first: do they exist, do they assert behaviour, are the edge cases there,
and would they fail if the changed behaviour broke? A deleted or weakened
assertion is Critical.

Then, per changed file:
- Correctness: does it do what the spec and the tests say, including error paths
  and boundary values?
- Readability and simplicity: honest names, straightforward control flow, no
  abstraction that has not earned its complexity, no new conditional bolted onto
  an unrelated flow.
- Architecture: fits the existing patterns, boundaries stay clean, dependencies
  point the right way, feature logic stays out of shared modules.
- Security: input validated at the boundary, no secrets, parameterized queries,
  encoded output, authorization checked, external data treated as untrusted.
- Performance: no N+1 access, no unbounded fetch or loop, no missing pagination,
  nothing expensive added to a hot path.
- Production readiness: migrations, backward compatibility, no obvious bug.

## Rules for your findings

- Verify each finding against the code before you report it. Drop anything you
  cannot substantiate: a false positive costs the author more than a missed nit.
- Skip whatever the repo's tooling already enforces, anything pre-existing
  outside this diff, and points a senior engineer would not raise.
- Grade by real severity. Most findings are not Critical.
- Every finding: file:line, what is wrong, why it matters, how to fix it.
- Name what is genuinely well done, specifically, and only if you checked it.
- Flag deviations from the spec as deviations, so the author can confirm whether
  they were deliberate. If the spec itself is wrong, say that instead.
- Comment on the code, never on the author. Do not soften a real problem and do
  not approve without evidence of having read the change.

## Output format

### Strengths
[Specific, verified.]

### Issues

#### Critical (must fix)
[Bugs, security holes, data loss, broken behaviour, neutered tests]

#### Important (should fix)
[Architecture problems, missing requirements, weak error handling, test gaps]

#### Minor (nice to have)
[Nits, optional simplifications, documentation polish]

### Recommendations
[Improvements worth knowing about but not required here]

### Assessment
Ready to merge: [Yes | No | With fixes]
Reasoning: [one or two sentences, naming the findings that drove the verdict]
```

## Filling the placeholders

| Placeholder | What goes in |
|---|---|
| `[DESCRIPTION]` | One paragraph on what the change is for. Never your session history — the reviewer evaluates the work product, not your thought process. |
| `[SPEC]` | The spec text or its path. No spec: write "no spec available" and tell the reviewer to skip that axis rather than guess. |
| `[STANDARDS_SOURCES]` | Paths to the repo's documented standards. |
| `[SMELL_BASELINE]` | Paste the smell list in full when the reviewer has no way to read it — a subagent starts with no files loaded. |
| `[BASE_SHA]`, `[HEAD_SHA]` | Resolved SHAs, not branch names, so the review cannot drift mid-pass. |

## Running the axes in parallel

For a change big enough to warrant it, dispatch one reviewer per axis and give each only what it
needs:

| Reviewer | Gets | Brief |
|---|---|---|
| Spec | Diff range, commit list, spec text | Requirements missing or partial, behaviour nobody asked for, requirements implemented wrongly. Quote the spec line per finding. |
| Standards | Diff range, commit list, standards paths, pasted smell baseline | Documented-standard breaches (cite the rule) and named smells (quote the hunk). Hard violations and judgement calls stay distinguishable. |
| Security | Diff range, commit list, risk triggers | Only for a high-risk change: removed guards with their history, blast radius, coverage gaps, one concrete attack path per finding. |

Aggregate into one report with the axes in separate sections, each ordered by severity. Do not
merge or rerank across axes, and do not pick a single worst finding overall — name the worst
within each axis. Reranking is exactly what the separation prevents.

## Example reviewer output

```markdown
### Strengths
- Migration is reversible and the down path is tested (`db/migrate/0042.ts:1-38`).
- Error paths return typed failures rather than throwing strings (`indexer.ts:70-96`).

### Issues

#### Important
1. **Date filter accepts invalid input silently** — `search.ts:25`
   - An unparseable date yields `NaN`, which the query treats as "no match", so the
     endpoint returns an empty list instead of an error.
   - Fix: validate the ISO string, reject with 400 and an example in the message.

2. **New public helper has no test** — `indexer.ts:112`
   - `resolveConcurrency()` picks the worker count from env plus CPU count; nothing
     covers the clamp, and the clamp is the part that will be wrong.
   - Fix: one test per branch — unset env, oversized env, single-CPU host.

#### Minor
1. **Nit: no progress output for long runs** — `indexer.ts:130`

### Recommendations
- FYI: `indexer.ts` is now the third module reading `process.env` directly; a single
  config accessor would remove the drift risk.

### Assessment
Ready to merge: With fixes
Reasoning: no correctness or security blockers; the date-filter behaviour and the missing
clamp test are both small and worth fixing before this lands.
```

<!-- sources: obra-requesting-review, mattpocock-review, addyosmani-review, anthropic-claude-code -->
