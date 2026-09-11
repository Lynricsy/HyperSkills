---
name: planning
description: "Turns a vague request into a plan that can be executed and verified: clarifying requirements into acceptance criteria that are either true or false, recording assumptions and rejected options, and producing a plan whose every step names the command that proves it done, its dependencies, its rollback point and its explicit non-goals. Covers task decomposition, honest parallelism, front-loading unknowns, catching scope creep, and the triggers that force a stop-and-replan when execution contradicts the plan. Applies when a request is too vague to start, when work must be broken into tasks, when reviewing a draft plan, or when a progress report disagrees with its plan. Do not use for writing SKILL.md files (use the `skill-authoring` skill), the red-green test loop (use the `test-driven-development` skill), the mechanical creation of GitHub issues or pull requests (use the `github` skill), technical writing itself, or product roadmaps and sprint scheduling."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: task
---

# planning

Paths below are relative to this skill's directory.

## Scope

Getting from "someone asked for a thing" to "a plan an executor can follow and
a reviewer can check": clarification, option selection and its record,
decomposition, the shape of the plan document, and keeping the plan honest
while it is executed.

The cheapest plan is often no document. A change whose flow already exists here
and can be read end to end needs a stated intent and agreement, not a file.
Reach for a document when the work spans subsystems, outlives one session, or
will be executed by someone other than its author.

Not covered — do not answer from this skill:

- Writing a skill. Planning its content is planning; frontmatter, structure
  and reference layout are the `skill-authoring` skill.
- The red-green-refactor loop. A plan says which command proves a step done;
  restating the test cycle is the `test-driven-development` skill.
- Creating issues, pull requests, milestones or labels, and anything `gh`
  does: the `github` skill. Deciding what the work is belongs here.
- Branch strategy, commit granularity and history: the `git-workflow` skill.
- Reviewing a diff: the `code-review` skill. Judging whether a plan is
  executable belongs here; judging the code it produced does not.
- Diagnosing a failure whose cause is unknown: the `debugging` skill.
- Designing the interface once the plan says one is needed: the `api-design`
  skill.
- Writing the prose — user docs, release notes, a guide. No skill in this
  library covers technical writing yet; say so rather than improvising.
- Product roadmaps, cross-team prioritisation, sprint scheduling and delivery
  estimates. Nothing here predicts dates.

## Core rules

Each rule is an invariant; the clause after the dash is what violating it costs.

1. A requirement is finished only when a third party can judge it true or
   false — "instant but not spammy" cannot be, so it is built, then rejected.
2. Every requirement not stated by the requester is written down as an
   assumption, before decomposition — an unrecorded assumption is
   indistinguishable from a requirement until it proves wrong, and then the
   work resting on it is rewritten rather than adjusted.
3. Each assumption names the steps that die with it. An assumption with no
   dependents is noise; one with dependents is a rollback plan you already have.
4. Facts are looked up, decisions are asked. Anything discoverable from the
   repository, a `--help` or a changelog is looked up — asking for it tells
   the requester you have not read their code. Anything that trades one cost
   against another is asked — deciding it silently commits them to a cost
   they never agreed to.
5. Before clarifying anything, check whether the behaviour already exists and
   whether this request was already rejected, and say where you looked — every
   project has a feature built twice and a request re-litigated a third time.
6. A step is not a step until it names the command that proves it done and the
   output that counts as passing — "run tests" and "wire up the frontend"
   cannot be finished, only abandoned, so they are reported done on the day
   someone stops looking.
7. Commands in a plan are the repository's own, read from its Makefile,
   `package.json`, `pyproject.toml` or CI workflow — a plan that says
   `npm test` in a repository that has no `test` script fails at its first
   step and takes its credibility with it.
8. Every step names what it depends on. A dependency that is obvious to the
   author is invisible to the executor, who will build the consumer first and
   then discover it has nothing to call.
9. Two steps are parallel only after an argument that they are; otherwise they
   are sequential. "Independent unless stated" inverts the burden of proof and
   the undeclared dependency surfaces as a merge conflict or a broken build in
   someone else's workspace.
10. Work that two parties will consume in parallel is preceded by a step that
    freezes the contract between them — parallelising against an unfrozen
    interface means both sides land, disagree, and one is rewritten.
11. A plan states its non-goals. Without them every adjacent good idea is
    arguably in scope, and the plan ends larger than the request while the
    request stays unfinished.
12. A plan states where the work can be abandoned and the state it leaves.
    With forward-only migrations or an applied deploy, "revert the commit" is
    not a rollback, and mid-incident is the worst time to learn that.
13. No placeholders in a finished plan: no TBD, no "add appropriate error
    handling", no "write tests for the above", no "similar to step N", no
    reference to a type no step defines — each defers a decision onto the
    executor at the moment they have the least context.
14. Each step is self-contained: its own paths, signatures and expected output,
    repeated rather than cross-referenced. Executors read one step, out of
    order, often in a fresh session with none of the author's context.
15. Paths and code belong in the plan, not in the requirements. Requirements
    outlive the file layout; a requirement written as `src/foo.ts:42` is stale
    at the next refactor and was a design decision in disguise.
16. Rejected options are recorded with the reason they were rejected, next to
    the decision — otherwise the same option is re-proposed in three months,
    and no one can tell whether it was considered or overlooked.
17. A step spanning two independent subsystems is split, or the plan says why
    not — an unsplittable step cannot be partially approved or localised.
18. The riskiest unknown is settled first, by the cheapest thing that answers
    it. Deferring it means everything built meanwhile rests on a guess.
19. Execution stops and the plan is revised — not patched in place — when a
    premise turns out to be false, when a step's acceptance cannot be met as
    written, when the same step has failed three times, or when work appears
    that no step covers. Pressing on produces a codebase that matches neither
    the plan nor the requirements, and no one can tell which is authoritative.
20. Revising a plan amends it: completed steps and the reason each changed stay
    on the record. Regenerating the document destroys the only account of why
    the code looks the way it does.
21. A step counts as done on quoted command output, never on a report that it
    is done — including a delegate's own report, which is checked against the
    diff. "Tests pass" from a session that has not run them is the most common
    false completion.
22. An existing plan with unchecked steps is never overwritten or repurposed
    for different work without asking. Those unchecked boxes may be the only
    record of what another session is mid-way through.

## Workflows

### clarify

From a vague request to requirements someone can build against.

- [ ] Read the request and every comment on it. Comments are where scope
      arrives unannounced; list each one as its own candidate requirement.
- [ ] Read the code the request is about, and the repository's conventions
      (`docs/plans/`, `docs/adr/`, CONTRIBUTING, the Makefile or script
      targets). Note the real commands; they become the plan's acceptance
      commands.
- [ ] Run the two pre-checks from `references/clarifying-requirements.md`:
      already implemented, previously rejected. Report where you looked.
- [ ] Sort every open point into looked-up, must-be-asked, or assumed
      (rule 4). Look up the first group now.
- [ ] Ask the second group in one round, numbered, each with your recommended
      answer. Use the format below.
- [ ] Write the third group as an explicit assumption block, each assumption
      naming what depends on it (rules 2, 3).
- [ ] Restate the requirements as criteria that can be judged true or false,
      and state the non-goals for this round (rules 1, 11).
- [ ] **Gate — DECIDABLE AND BOUNDED:** every requirement can be judged by a
      third party, every assumption is written down with its dependents, and
      the non-goals are stated. A requirement you cannot phrase as a check is
      still a wish.

### plan

From agreed requirements to a document an executor can follow.

- [ ] Confirm the requirements are decidable. If not, run `clarify` first —
      decomposing a wish produces steps that cannot be finished.
- [ ] Choose where the plan lives: the repository's existing convention if it
      has one, otherwise ask. Never overwrite a plan with unchecked steps
      (rule 22).
- [ ] Settle the approach: two or three real options, the trade-off that
      separates them, your recommendation, and the reason each rejected option
      was rejected (rule 16). Read `references/exploring-options.md`.
- [ ] Map the dependency order, then cut vertical slices along it. Read
      `references/task-decomposition.md`.
- [ ] Write the steps in the shape given by
      `references/plan-document.md`: files, interfaces consumed and produced,
      acceptance command with expected output, dependencies.
- [ ] Decide parallelism per pair of steps, and add the contract-freezing step
      that any real parallelism needs (rules 9, 10). Read
      `references/parallelism.md`.
- [ ] Front-load the riskiest unknown as an investigation, not a build step
      (rule 18). Read `references/risk-and-unknowns.md`.
- [ ] State non-goals and the rollback point (rules 11, 12).
- [ ] Self-review, once, with fresh eyes: requirement coverage, placeholder
      scan, name and type consistency across steps. The checklist is in
      `references/plan-document.md`.
- [ ] **Gate — EVERY STEP HAS A COMMAND AND A PREDECESSOR:** for each step you
      can quote the command that proves it, the output that counts as passing,
      and either its dependencies or the argument that it has none. A step
      missing any of these is not a step.

### review-plan

Judging someone else's plan — or your own, a day later — before execution.

- [ ] Read the plan and the actual repository state side by side, checking that
      every path, service and command it names exists. Most plan defects are
      disagreements with reality, not internal ones.
- [ ] Walk the defect catalogue in `references/plan-review.md` and record a
      finding per defect with the step it lands on. Check each parallelism
      claim against the code rather than the plan's assertion (rule 9), and
      check for scope the request never asked for using
      `references/scope-creep.md`.
- [ ] Give a verdict: executable, executable after the listed fixes, or not
      executable. Name the defects before proposing a rewrite — a silently
      repaired plan teaches its author nothing and hides how wrong it was.
- [ ] **Gate — EVERY FINDING NAMES ITS FAILURE:** each finding says what will
      happen during execution if it is left alone. A finding you cannot
      complete that sentence for is a style preference; drop it.

### track

Keeping a plan honest while it is executed, and knowing when to stop.

- [ ] Before each step, re-read it. Plans go stale against the code from the
      moment they are written.
- [ ] After each step, record the command and its actual output. A step with no
      quoted output is in progress, whatever the checkbox says (rule 21).
- [ ] Compare what happened with what the step said would happen. Note every
      divergence, including the ones that worked out.
- [ ] Check the stop triggers in `references/execution-tracking.md` against
      each divergence. On any trigger, stop and revise; do not improvise a
      patch inside a step (rule 19).
- [ ] When revising, amend: keep completed steps and record why each change was
      made (rule 20).
- [ ] **Gate — STATE MATCHES EVIDENCE:** the checked steps are exactly those
      with quoted passing output, every divergence is either accepted in
      writing or open as a finding, and no claim rests on a report you did not
      verify.

### Rationalizations

| Excuse | Reality |
|---|---|
| "I'll figure out the details as I go" | The details are the plan. What you had was a title. |
| "The dependencies are obvious" | To you, today. The executor sees one step and no context. |
| "Everything can run in parallel" | Say it per pair, with the reason. The claim survives about two pairs. |
| "I'll write the acceptance criteria once it works" | Then they will describe what you built, and can never disagree with it. |
| "While I'm in there I'll also…" | That is a second plan. Write it down and leave it for later. |
| "The old plan is stale, I'll regenerate it" | Its unchecked steps may be in flight, and its history is the only record of why. Amend it. |
| "The premise changed but I'm nearly done" | Nearly done on a false premise is further from done than starting over knowingly. |

### Red flags

Stop and re-plan when you catch any of these: a step whose completion you
cannot describe as a command; a plan that names a directory that does not
exist; "and" in a step title; a requirement quoted from the request verbatim
because it resisted rephrasing; an assumption you noticed and did not write
down; a parallel claim with no argument; a rollback described as "revert the
commit" over a forward-only migration; a progress report with no command
output in it; a definition of done that mentions how the team feels.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Decidable acceptance criteria, the already-built and already-rejected pre-checks, the look-up/ask/assume split, one-round questions, keeping clarification results | Turning a vague request into requirements | `references/clarifying-requirements.md` |
| Two or three real options, the trade-off axis, YAGNI cuts, recording the rejected ones, ADR shape and supersede chains | A choice with more than one defensible answer | `references/exploring-options.md` |
| Plan header, global constraints, the step block, interfaces consumed and produced, acceptance command and expected output, identifiers, no-placeholder list, self-review | Writing or fixing the plan document itself | `references/plan-document.md` |
| Dependency mapping, vertical slices, right-sizing and split triggers, capability maps for multi-subsystem work, one-subsystem-per-step | Cutting work into steps, or a step feels too big to start | `references/task-decomposition.md` |
| Parallel / sequential / needs-coordination, freezing a contract first, serialisation boundaries, what a delegated step must carry | Deciding what can run at the same time, or handing steps out | `references/parallelism.md` |
| Classifying unknowns, designing a spike that answers exactly one question, front-loading risk, `[NEEDS CLARIFICATION]` markers, assumption-to-step mapping | The plan contains something nobody knows yet | `references/risk-and-unknowns.md` |
| Progress reporting shape, evidence rules, the stop-and-replan triggers, amend-not-regenerate, living and flow-back revision models | A plan is being executed, or a report disagrees with it | `references/execution-tracking.md` |
| Creep patterns and where each one enters, the definition-drift test, what to do with a good idea that is out of scope | The work is growing, or a plan contains steps the request never asked for | `references/scope-creep.md` |
| Defect catalogue with the execution failure each one causes, per-defect verdicts | Reviewing a plan before execution | `references/plan-review.md` |

## Output format

**Clarification** — the `clarify` workflow. Facts first, then the one round of
questions, then what you assumed.

```
## What I checked
<where you looked for an existing implementation or a prior rejection, and what you found>
<facts you established from the code, one line each, with path:line>

## Requirements (decidable)
R1. Given <context>, when <trigger>, then <observable outcome>.
R2. ...

## Non-goals this round
- <thing deliberately excluded, and where it goes instead>

## Assumptions
A1. <assumption> — if false: <the steps or requirements that change>

## Decisions I need
❓ Q1 — <title>
<question>
➡️ Recommended: <answer and why>
```

**Plan** — the `plan` workflow. One step block per step; repeat, never
cross-reference.

```
# <feature> — plan

Goal: <one sentence>
Approach: <two or three sentences; the rejected options live in the decision record>
Requirements: <path to the decidable requirements this plan implements>
Rollback point: <where work can stop, and the state it leaves behind>

## Global constraints
- <project-wide constraint, exact values copied from the requirements>

## Non-goals
- <excluded, and where it goes instead>

## Assumptions
A1. <assumption> — affected steps: <N, M>

## Step N — <title>
Depends on: <step numbers, or "nothing, because …">
Files: create <path> / modify <path> / test <path>
Consumes: <exact signatures this step relies on from earlier steps>
Produces: <exact signatures later steps rely on>
Do: <what changes, concretely>
Accept: `<the repository's own command>` → <the output that counts as passing>
```

**Plan review** — the `review-plan` workflow, worst first.

```
## <plan path>

Verdict: executable | executable after the fixes below | not executable

<plan path>:<line> - <step or section>: <defect>
  Fails as: <what happens during execution if this is left alone>
  Fix: <the smallest change that removes the defect>

## Missing
<requirement, dependency or risk that no step covers>
```

Worked example:

```
## docs/plans/2026-08-notifications.md

Verdict: not executable

docs/plans/2026-08-notifications.md:9 - Task 1: targets services/notifier/,
which does not exist in this repository.
  Fails as: the first step's executor stops to invent a service boundary the
  plan never decided, and every later step's paths are guesses.
  Fix: state whether the notifier is a new service or lives inside
  services/mailer/, and name the files either way.

docs/plans/2026-08-notifications.md:5 - "All tasks are independent and can be
worked in parallel": false.
  Fails as: Task 2 calls GET /notifications, which Task 3 creates. Whoever
  takes Task 2 first writes against an endpoint that does not exist.
  Fix: make the OpenAPI change its own step, freeze it, and mark Tasks 2 and 3
  as its dependents.

## Missing
Nothing covers the retrievability requirement from the request, so the plan
can be fully executed and still fail acceptance.
```
