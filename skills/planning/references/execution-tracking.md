# Execution tracking and plan revision

## Contents

- [Before the first step](#before-the-first-step)
- [What counts as done](#what-counts-as-done)
- [The progress report](#the-progress-report)
- [Divergences](#divergences)
- [Stop triggers](#stop-triggers)
- [Amend, do not regenerate](#amend-do-not-regenerate)
- [Which artefact to change first](#which-artefact-to-change-first)
- [The consistency check before resuming](#the-consistency-check-before-resuming)
- [Closing out a plan](#closing-out-a-plan)

## Before the first step

Read the whole plan critically once, against the current code, before executing
anything. A plan is a claim about a codebase at a moment; both the code and
the understanding have moved since.

Record the concerns rather than working around them. Raise them if any of the
following holds — these are the ones that get worse with every step executed:

- A path, service or command the plan names does not exist.
- A step's acceptance cannot be run as written.
- A step depends on something no earlier step produces.
- Two steps declare incompatible signatures for the same thing.

Then execute. Re-read each step immediately before doing it; the previous step
may have changed what this one assumes.

## What counts as done

A step is done when its acceptance command has been run and its output matches
what the step said would count as passing. Not before, and not on the strength
of any report.

| Claim | What is required | What is not enough |
|---|---|---|
| Step passes | Its acceptance command, run now, output read | A run from before the last edit |
| Suite is green | The full-suite command's output with counts | The focused test passing |
| Types are clean | The typecheck command across all workspaces | One workspace, or the editor showing no squiggles |
| Migration applied | The migration command's output and the resulting shape | The file being committed |
| Delegated step complete | The diff, plus the acceptance command run by you | The delegate's report, however detailed |
| Requirements met | Each requirement walked against the built behaviour | The suite passing |

The last row is the one that catches whole plans. A plan can be fully executed
with every step green and still fail acceptance because one requirement had no
step. Walk the requirements, not the checkboxes.

## The progress report

A report exists so someone else can tell what is true. That means commands and
outputs, not adjectives.

```markdown
## Step 4 — Outbox poller — done
Command: make test-one FILE=services/worker/jobs/deliver-notifications.test.ts
Output: 7 passed, 0 failed
Full suite: make test → 214 passed, 0 failed
Diverged: the claim query needed SKIP LOCKED, which the step did not mention.
  Recorded as an amendment to step 4; no other step affected.

## Step 5 — Freeze GET /notifications — in progress
Command: make client && make typecheck
Output: make client clean; make typecheck FAILS with 14 errors in mobile/
Status: not done. The 14 errors are the step's remaining work, not a separate
  task.
```

"In progress" with the failing output is a useful report. "Done, tests pass"
with no output is not a report, it is a mood — and it is the most common way a
plan drifts from reality, because everything downstream now assumes a step
that did not land.

Two specific habits:

- Quote the output. Paraphrasing loses the counts, and the counts are the
  information.
- Say when you last ran the full suite. "Tests pass" from a session whose last
  full run was two days and four steps ago is not about the current state.

## Divergences

Note every divergence between what a step said and what happened, including
the ones that turned out fine. A divergence that worked is still information
about the plan's accuracy, and the next step may depend on it.

Three kinds, with different handling:

| Kind | Example | Handling |
|---|---|---|
| Detail | The query needed a lock hint the step did not mention | Amend the step; continue |
| Shape | The table shipped with different columns than planned | Amend the step *and* every step that consumes it; check the consistency of the whole plan before continuing |
| Premise | The event bus turned out not to be durable | Stop. The plan's foundation changed; see below |

The dangerous one is a shape divergence handled as a detail. If a step
delivered `(user_id, kind, payload_json, seen_at)` where the plan said
something else, every later step's *consumes* block is now wrong, and each
will be discovered separately by whoever executes it.

## Stop triggers

Stop executing and revise the plan — do not patch inside a step — on any of
these:

1. **A premise turned out false.** Something the plan assumed about the code,
   the platform or a dependency is not true. Continuing produces work that is
   correct against a model of the system that does not exist.
2. **A step's acceptance cannot be met as written.** Not "is failing" — cannot
   be met. Either the acceptance was wrong or the step was.
3. **The same step has failed three times.** The cause is not where you think
   it is. Further attempts are guesses; switch to diagnosis, come back with a
   reproduction.
4. **Work has appeared that no step covers.** A prerequisite nobody planned, a
   consumer nobody listed, a migration the plan does not contain.
5. **A step can only pass by violating a constraint or a non-goal.** Bypassing
   a frozen contract, hand-writing a request against a generated client,
   deleting a failing test, touching a file the step's non-goals excluded.
6. **A blocker outside the plan.** A missing credential, an unavailable
   environment, an unanswered decision. Split the plan at the blockage so the
   unblocked part can proceed, and record the blocker with an owner.

Trigger 5 is the one most often rationalised. A local workaround that violates
a constraint converts a blocked step into a silent debt: the work looks done,
the contract is broken, and the breakage surfaces in whatever consumes it
next. When a step cannot pass honestly, the plan is what is wrong.

What "stop" means concretely: finish nothing new, write down the state,
name the trigger, propose the revision. It does not mean reverting work that
is correct.

## Amend, do not regenerate

Revising a plan means amending the document. Completed steps stay, with the
reason each change was made.

```markdown
## Step 4 — Hook into events — SUPERSEDED 2026-09-13
Delivered a handler plus a 30s setTimeout re-run. This does not satisfy the
no-double-send requirement: the timer dies with the process and the re-run
duplicates sends. Replaced by steps 4a-4c below. The handler is kept; the
timer is removed in 4a.

## Step 4a — Remove the setTimeout re-run
...
```

Regenerating the document destroys the only account of why the code looks the
way it does. It also destroys the checkbox state, which for a plan being
executed in more than one session is the only record of what is in flight.

Two related rules:

- Before replacing any derived artefact, carry forward the rationale still
  worth keeping. A regenerated task list that drops the reason a task existed
  produces a second round of the same discussion.
- Never repurpose a plan file with unchecked steps for different work. Those
  boxes may belong to another session. Ask.

## Which artefact to change first

When requirements, plan and code disagree, the order of repair is a decision
to make once and then follow.

**Default — requirements are the contract.** Change the requirements first,
then bring the plan into line, then the code. Use this when intended behaviour
is what changed: a requirement was wrong, missing, or the requester changed
their mind. The discipline it buys: nothing in the plan or the code
contradicts the requirements for longer than one revision.

**Escape hatch — the discovery lands where the work is.** When implementation
reveals something nobody could have known, capture it in the artefact closest
to the work — the step, or the code — then decide what it changes: intended
behaviour, approach, decomposition, or nothing beyond this step. Then update
every artefact that now disagrees.

Flow-back is flexible and needs discipline. The rule that makes it safe: never
leave a lower-level change in place while the requirements still say something
different. A requirements document that no longer describes the system is worse
than none, because it is still trusted.

## The consistency check before resuming

After any revision, before resuming execution, check the set:

- [ ] Every requirement maps to a step, or is explicitly a non-goal.
- [ ] Every step's *consumes* matches some step's *produces*, character for
      character, including the ones that changed.
- [ ] Every path and command in the remaining steps still exists.
- [ ] Every assumption that was invalidated has had its dependents revisited.
- [ ] The rollback point is still accurate given what has already been applied.
- [ ] Completed steps still describe what was actually built.

Resuming without this check is how a revision produces a second round of the
same divergence: the amended step is right and the three steps that consume it
are still describing the old shape.

## Closing out a plan

A plan is finished when every step has quoted passing output, every
requirement has been walked against the built behaviour, and every divergence
is either amended into the plan or open as a recorded finding.

State what was not done and why: deferred non-goals, risks that fired, the
steps that were superseded. A plan that ends with every box ticked and no
account of what changed along the way is a plan that was rewritten to match
the outcome.

<!-- sources: speckit-docs, obra-executing, copilot-plan, addy-planning -->
