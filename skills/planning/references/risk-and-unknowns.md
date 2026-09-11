# Risk and unknowns

## Contents

- [Classify the unknown before scheduling it](#classify-the-unknown-before-scheduling-it)
- [Front-load the one that can invalidate the plan](#front-load-the-one-that-can-invalidate-the-plan)
- [Designing an investigation step](#designing-an-investigation-step)
- [Investigations that are worth a step](#investigations-that-are-worth-a-step)
- [The risk table](#the-risk-table)
- [Assumptions as risk with a blast radius](#assumptions-as-risk-with-a-blast-radius)
- [Markers for unresolved points](#markers-for-unresolved-points)
- [Risks that are not risks](#risks-that-are-not-risks)

## Classify the unknown before scheduling it

Unknowns behave differently and need different steps. Sort each one:

| Kind | Example | What it gets |
|---|---|---|
| Answerable by reading | Does the event bus persist? What does the worker do on throw? | Nothing. Read it now, before planning. |
| Answerable by running | Does the generated client still typecheck in the strict workspace? Does the migration apply cleanly? | An investigation step, first |
| Decision | Immediate or digest? Which events qualify? | A question to the requester |
| External | Do we have store credentials? What does compliance require? | A dependency with an owner and a date, outside the plan |
| Genuinely unknowable now | How will this behave at ten times the volume? | A recorded risk with a trigger, not a step |

The failure mode is filing an *answerable by reading* unknown as a risk. "Risk:
the event bus may not be durable" is not a risk; it is a question with an
answer sitting in the repository, and writing it as a risk means the plan was
built without reading the code it changes.

## Front-load the one that can invalidate the plan

Order unknowns by how much of the plan dies if the answer is bad, not by how
interesting they are. The one that can invalidate the most goes first, as
cheaply as it can be answered.

The reason is arithmetic: everything built before an unknown is settled rests
on a guess. If the guess was wrong, that work is redone — and the later the
unknown is settled, the more work there is to redo.

Worked example. The request says notifications must not double-send. The plan
assumes the event bus supports at-least-once delivery with dedupe. That
assumption underlies every step. Settling it costs twenty minutes of reading
and one scratch script; deferring it until the delivery step means the schema,
the writer and the handler are all built against the wrong model.

The cheapest thing that answers it is rarely the full implementation. Order of
preference:

1. Read the code or the spec. Free.
2. Run the existing tool and observe (`make typecheck` after a regeneration, a
   migration on a scratch database, one command with `--dry-run`).
3. A throwaway script that exercises the one behaviour in question.
4. A prototype that gets deleted. Label it throwaway before starting, and say
   what will be deleted.

Anything beyond that is not an investigation, it is the build step. If the only
way to answer the question is to build the feature, say so and plan the build
with the unknown recorded as a risk.

## Designing an investigation step

An investigation step answers exactly one question and its deliverable is the
answer, written down.

```markdown
## Step 1 — Investigation: can the current stack meet no-double-send?

Question: with packages/events fire-and-forget in-process and services/worker
retrying whole jobs, is there any handler-level arrangement that delivers each
event exactly once?
Do: read packages/events and services/worker. Write a scratch script that
  emits an event, kills the process mid-handler, restarts, and reports whether
  the event was delivered zero, one, or two times.
Accept: a written answer with the observed counts. If the answer is no, step 2
  becomes "outbox table" and steps 4-6 are re-planned before any are started.
Timebox: stop after the counts are observed. Do not start building the outbox
  inside this step.
```

Three properties make it a step rather than a detour:

- **One question.** An investigation with three questions returns three partial
  answers.
- **A stated consequence for each answer.** If both answers lead to the same
  plan, the investigation is not worth doing.
- **A stop condition.** Investigations expand without one: reading turns into
  refactoring, and the answer arrives with a half-built feature attached.

## Investigations that are worth a step

Recurring cases where twenty minutes up front routinely saves a rewrite:

- **A generated artefact with multiple consumers.** Regenerate on a branch and
  run the strictest consumer's typecheck. The answer is a number of errors,
  which is the real size of the "just add an endpoint" task.
- **A migration on a forward-only tool.** Apply it to a scratch database and
  read the resulting shape. The shape has to be right the first time.
- **A dependency upgrade.** Upgrade in isolation, build, run the suite. The
  answer is the list of breakages, which is the actual plan.
- **A third-party behaviour a step depends on.** Rate limits, pagination
  semantics, whether an API is idempotent. Read the official docs, then verify
  the one behaviour with a real call — documented and actual behaviour diverge
  most often exactly here.
- **A performance assumption load-bearing for the design.** One measurement
  beats three paragraphs of reasoning, and it is usually a single command.

## The risk table

Risks that survive investigation get recorded, each with an owner and a
trigger:

```markdown
## Risks
| # | Risk | If it happens | Trigger to act |
|---|---|---|---|
| R1 | Poll interval makes "instant" unacceptable | Move delivery onto a broker; steps 4-5 change | A user-visible latency complaint, or P95 above 60s |
| R2 | Outbox table growth outpaces cleanup | Add a retention job; no step changes | Table above 10M rows |
| R3 | Store credentials never arrive | Push stays a non-goal permanently | Not resolved by the time step 7 would start |
```

The trigger column is what makes the table useful later. A risk without a
trigger is never revisited: nobody can say whether it has happened. With one,
the plan tells its executor when to come back to it.

Risks are not steps. A risk that needs work now is a step; the table is for
things that may need work later.

## Assumptions as risk with a blast radius

Every assumption is a risk whose probability nobody knows. What makes it
manageable is the blast radius, so record that and not a likelihood:

```markdown
## Assumptions
A1. Support's three named event types are the whole of "important".
    — if false: R2 changes, steps 4 and 6 grow one handler each. Cheap.
A2. In-app only for v1. — if false: step 6 is replaced and a channel
    abstraction becomes a prerequisite for steps 4-6. Expensive; this is the
    assumption to confirm first.
A3. Timestamps are UTC, formatted client-side. — if false: step 7 only.
```

Sorting assumptions by blast radius tells you which one to spend a question on.
A2 is worth a round trip; A3 is not, and asking about it dilutes the questions
that matter.

An assumption with no dependents is noise — delete it. An assumption whose
dependents are the whole plan is not an assumption but the decision the plan is
waiting on: move it to the questions.

## Markers for unresolved points

Where an unknown blocks a specific sentence rather than the whole plan, mark it
in place:

```markdown
Do: deliver through `services/mailer` with a per-recipient rate cap of
[NEEDS CLARIFICATION: cap value — support has the complaint data].
```

Two reasons in-place markers beat a separate open-questions list: the unknown
stays attached to the decision it affects, and a draft still containing markers
is visibly not ready. A plan with an open-questions section at the bottom gets
executed from the top.

Resolve every marker before the plan is agreed. A marker that survives into
execution becomes an improvisation by whoever hits it.

## Risks that are not risks

Drop these; they crowd out the real ones:

- **"The requirements may change."** Always true, never actionable.
- **"The estimate may be wrong."** Not a risk about the work.
- **"A dependency may have a vulnerability."** True of every dependency; it
  belongs to whatever process watches for that, not to this plan.
- **Anything whose mitigation is "be careful" or "monitor closely".** If there
  is no action, there is no risk entry — there is an acknowledgement, and it
  belongs in a sentence.
- **A restatement of a step's difficulty.** "Risk: the migration is complex" is
  the step's description, not a risk. The risk would be a specific way it fails.

The test: can you write what happens if it occurs, and what tells you it has
occurred? If not, it is a worry rather than a risk, and worries do not go in
plans.

<!-- sources: copilot-plan, addy-planning, obra-brainstorming, speckit-docs -->
