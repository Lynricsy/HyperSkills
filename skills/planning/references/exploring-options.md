# Exploring options and recording the choice

## Contents

- [When a choice deserves options](#when-a-choice-deserves-options)
- [Two or three real options](#two-or-three-real-options)
- [Finding the axis](#finding-the-axis)
- [Cutting with YAGNI](#cutting-with-yagni)
- [Presenting the options](#presenting-the-options)
- [The decision record](#the-decision-record)
- [Rejection reasons that are worth writing](#rejection-reasons-that-are-worth-writing)
- [Superseding a decision](#superseding-a-decision)
- [Where the record lives](#where-the-record-lives)

## When a choice deserves options

Not every choice does. Generating three options for a decision with one
defensible answer is theatre, and it invites the requester to pick the wrong
one out of politeness.

A choice deserves explicit options when at least one holds:

- The options differ in cost by more than the work saved by deciding quickly.
- They are hard to reverse: a schema shape, a wire format, a dependency, a
  boundary between services.
- They trade costs that land on different people — one is cheaper to build and
  more expensive to operate, or cheaper now and more expensive to change.
- Someone will ask "why not X" later, and X is a reasonable question.

Otherwise state the choice, its reason, and move on. A single sentence
(`Using the existing worker rather than a new service: the retry semantics are
already there`) is a complete decision record for a reversible choice.

## Two or three real options

Three is the useful number: one option is a decision presented as a choice,
and four is a survey. Two is enough when the third would be a strawman.

Each option has to be one you would actually implement. The recognisable
failure is the padded set: the recommendation, a deliberately terrible
alternative, and "do nothing". A reviewer learns nothing from it, and the
padding is obvious — which costs the recommendation its credibility too.

Each option needs, in one or two lines each:

- What it is, concretely enough to size.
- What it costs to build — which parts of the codebase it touches.
- What it costs afterwards — operationally, and to change later.
- What it forecloses.

## Finding the axis

Options that differ in many ways at once cannot be compared. Before listing
them, name the single axis that actually separates them, and hold everything
else equal.

Worked example — delivering notifications reliably on a stack whose event bus
is in-process and fire-and-forget:

| | Outbox table | Broker (SQS/Rabbit) | Idempotency key only |
|---|---|---|---|
| Axis: where durability lives | in our database | in infrastructure | nowhere; dedupe on arrival |
| Build cost | one migration, one writer, one poller | new infra, credentials, local dev story | one column, one lookup |
| After | no new operational surface | a queue to monitor and pay for | duplicates still possible on crash between send and record |
| Forecloses | nothing; a broker can read the outbox later | little | reliability; needs redoing when volume grows |

The axis here is *where durability lives*. Once that is explicit, the choice is
a real decision rather than a preference, and the rejection reasons write
themselves.

If you cannot name an axis, the options are probably the same option described
three ways. Collapse them.

## Cutting with YAGNI

Apply the cut to every option before presenting any of them, otherwise you are
comparing padded designs and the padding is what gets built.

Remove anything whose justification is a future requirement nobody has stated:
a plugin point with one implementation, a config flag with one value in use, a
generic interface over a single concrete case, a versioning scheme for an
internal format. Each costs review attention now and constrains the design
later while proving nothing.

The exception is when reversing the omission is expensive and the requirement
is stated: a migration that is hard to run twice, a wire format external
consumers will pin to. Say that explicitly — "including X now because adding it
later needs a second migration over the same table" is a reason; "for
flexibility" is not.

## Presenting the options

Lead with the recommendation, then the alternatives. Burying the
recommendation after three neutral paragraphs makes the reader do your work.

```
Recommended: outbox table.
The durability requirement is non-negotiable and this keeps it in the database
we already operate. One migration, one writer, one poller in the existing
worker.

Rejected — broker: correct at ten times the volume, but it adds infrastructure,
credentials and a local-dev story to a change that is otherwise three files.
Revisit when the outbox poller becomes the bottleneck.

Rejected — idempotency key alone: does not survive a crash between send and
record, which is exactly the case the request names.
```

Present it and stop. A design presented and immediately implemented in the same
breath has not been agreed to; the gate is the agreement, not the presentation,
and its size does not scale with how obvious the choice looks.

## The decision record

Once a structural choice is made, it goes somewhere durable. A decision that
lives only in a chat log is re-litigated, and the second discussion has less
information than the first.

Record the decision next to the code it governs, using the repository's
existing convention. If it has an ADR directory, write an ADR:

```markdown
---
title: "ADR-0010: Durable notification delivery via an outbox table"
status: Accepted
date: 2026-09-11
supersedes: ""
superseded_by: ""
---

## Context
packages/events is an in-process EventEmitter with no persistence; the worker
retries whole jobs at least once. The request requires no duplicate delivery.
Neither property can be met by the current stack.

## Decision
Write notifications to an outbox table inside the same transaction as the
triggering change; a poller in services/worker delivers and marks them,
keyed by event id.

## Consequences
Positive: durability lives in a database we already back up; delivery is
retryable without duplicating; the outbox is readable for the audit trail.
Negative: adds a polling loop and a table that grows; delivery latency is
bounded by the poll interval, not by the event.

## Alternatives considered
- Broker: rejected — new infrastructure and local-dev burden for a change that
  is otherwise three files. Reconsider if poll latency becomes the constraint.
- Idempotency key alone: rejected — does not survive a crash between send and
  record, the exact failure the request names.
```

Numbered sequentially, one decision per file, never renumbered. The sections
that matter are *Context* (what forced a decision), *Decision*, *Consequences*
including the negative ones, and *Alternatives considered* with a reason each.
An ADR with no negative consequences has not been thought about; every real
decision costs something.

## Rejection reasons that are worth writing

A rejection reason is worth writing when it would change a future reader's
mind, or tell them when to change it back.

| Weak | Useful |
|---|---|
| "Too complex" | "Adds a broker, credentials and a local-dev path to a three-file change" |
| "Not a good fit" | "Requires at-least-once delivery, which the in-process bus does not provide" |
| "We prefer X" | "X is already operated here and has the retry semantics we need" |
| "Rejected for now" | "Rejected until the outbox poller is the latency bottleneck — that is the trigger to revisit" |

The last row is the pattern worth copying: a rejection with a re-evaluation
trigger is a decision that ages gracefully. Without a trigger, "for now" means
forever or next week, and nobody can tell which.

## Superseding a decision

Decisions go stale. Do not edit an accepted decision to say something else: the
code written under the old decision still exists, and the old text is how
anyone understands it.

Write a new record, set its `supersedes` to the old one, and set the old one's
`superseded_by` and status to `Superseded`. The new record's *Context* says
what changed — which is the only genuinely new information.

The same applies to the smaller case: a one-line decision recorded in a plan
that turns out wrong is amended with a dated line, not overwritten. See
`execution-tracking.md`.

## Where the record lives

Use what the repository already does, in this order:

1. An existing decisions or ADR directory — extend it, matching its numbering
   and filename convention exactly.
2. No such directory, but a docs tree with plans in it — put the decision in
   the plan document, in a section with the same four headings.
3. Neither — ask where it should go rather than creating a new convention. A
   second convention beside an existing one is worse than either.

The decision record is not the plan. The plan says what to build in what
order; the record says why this shape and not another. A plan that also argues
its own alternatives gets skimmed, and the reasoning is lost either way.

<!-- sources: copilot-plan, obra-brainstorming, addy-planning, speckit-docs -->
