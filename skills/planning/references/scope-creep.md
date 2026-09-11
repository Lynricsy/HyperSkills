# Scope creep

## Contents

- [Why non-goals are the only defence](#why-non-goals-are-the-only-defence)
- [Where creep enters](#where-creep-enters)
- [The definition-drift test](#the-definition-drift-test)
- [Creep that arrives in a comment](#creep-that-arrives-in-a-comment)
- [Creep that arrives as a shortcut](#creep-that-arrives-as-a-shortcut)
- [What to do with a good idea that is out of scope](#what-to-do-with-a-good-idea-that-is-out-of-scope)
- [Scope reduction needs the same ceremony](#scope-reduction-needs-the-same-ceremony)
- [Creep in the other direction](#creep-in-the-other-direction)

## Why non-goals are the only defence

Without stated non-goals, every adjacent improvement is arguably in scope. The
argument is always locally reasonable — it is nearby, it is quick, it makes the
main change cleaner — and each one is accepted on its own merits until the plan
is twice its original size and the original request is still unfinished.

Non-goals convert that argument into a check: is this in the non-goals list? A
plan with non-goals can be defended by anyone, including the person who wrote
the creep. A plan without them can only be defended by whoever remembers what
was agreed.

## Where creep enters

Each entry point has a recognisable phrase and a specific response.

| Entry | Phrase | Response |
|---|---|---|
| Adjacent refactor | "While I'm in there…" | Out, unless the change does not fit without it. Then it is its own step with its own acceptance. |
| Migration by opportunity | "…and migrate the existing callers over" | Out. Migrating existing users of a new mechanism is a second project with its own risk. |
| Generalisation | "Let's make it configurable while we're at it" | Out unless a stated requirement needs the second configuration. One implementation does not need a plugin point. |
| Gold-plating acceptance | "Also add metrics/tracing/admin UI" | Out unless a requirement asks for it. Record as a follow-up. |
| Blocked-task substitution | "Task 5 is blocked so I picked up something else" | Out. Unplanned work while blocked is unreviewed work. Report the blockage. |
| Requirement inflation | "Obviously it should also handle…" | Back to clarification. This is a new requirement, not a detail. |
| Fixing what you noticed | "This other bug is right there" | Record it as a finding. Fixing it inside this plan makes the diff unreviewable. |

The riskiest is migration by opportunity, because it looks like completion. A
plan that builds a new notification pipeline and *also* moves four existing
billing receipt templates onto it has doubled its blast radius: the new
pipeline is unproven, and the thing now riding on it is transactional money
mail. The correct sequencing is obvious once stated — prove the pipeline on the
new low-stakes traffic, migrate the high-stakes traffic later, as its own
plan with its own rollback.

## The definition-drift test

Creep also enters by widening a word rather than adding a step. Nothing is
added to the plan; the meaning of an existing term grows.

Ask, for each key term: is it being used with exactly the meaning it had when
the requirements were agreed?

- "Notify users" agreed as in-app, now being built as in-app plus email plus
  push. Same sentence, three times the work.
- "Important events" agreed as three named types, now "any domain event".
- "Retrievable" agreed as a list of what was sent, now an immutable audit log
  with a retention policy.
- "Works on mobile" agreed as the list renders, now push notifications with
  device-token lifecycle and store review.

The tell is that the requirement text has not changed while the estimate has.
When a term's meaning has drifted, pin it in the requirements with an explicit
definition and a non-goal for the excluded readings:

```markdown
R2. "Important event" means exactly: plan changed, invoice failed, member
    invited. Any other event type is a non-goal for this round.
```

## Creep that arrives in a comment

A request with three comments from three people is four requests. Each
commenter will review the result against their own comment, so silently
dropping one is not a saving — it is a rejection deferred to review.

Handle each explicitly, in one of three ways:

- **Accepted** into this round, with its own requirement.
- **Deferred**, named in the non-goals, with where it goes instead.
- **Declined**, with a reason, visible to the person who asked.

What does not work is treating a comment as context. "This should work for the
mobile app too" either changes the plan or is a non-goal; there is no third
state in which it has been dealt with.

Where two comments conflict — one asking for an extra channel, another asking
to keep it small — surface the conflict rather than averaging it. Averaging
produces a plan that satisfies neither and that both reviewers will reject.

## Creep that arrives as a shortcut

Some creep is created by taking a shortcut rather than by adding a feature. It
does not look like extra scope; it looks like less work.

- Hand-writing a request against a generated client because regenerating breaks
  a consumer. The regeneration is still owed, the consumer's errors are still
  owed, and now there is a second source of truth to remove as well.
- Adding a table column with a shape that differs from the plan because it was
  faster, on a forward-only migration tool. Every consumer is now planned
  against the wrong shape and the schema cannot be reverted.
- Wrapping a handler in a retry instead of making delivery durable. The
  original requirement is unmet and a duplicate-delivery bug has been added.

Each converts a blocked step into a silent debt plus a new defect. The response
is the same: the shortcut is recorded as a divergence, the owed work is added
back as a step, and if that changes the plan's premise, execution stops (see
`execution-tracking.md`).

## What to do with a good idea that is out of scope

Out of scope is not the same as wrong. Most creep is genuinely good work in the
wrong plan. Losing it is a real cost, so:

1. Write it down where the project keeps such things — a follow-up section in
   the plan, a findings list, the issue tracker.
2. Say what triggers it: "after the pipeline has run for a cycle without
   duplicate reports", "when a second channel is actually requested".
3. Leave it.

A findings list at the end of a plan is the cheapest version of this and
usually enough:

```markdown
## Findings — not in this plan
- services/mailer has no send log. Blocks any retry or audit story; needed if
  email becomes a channel. No step here depends on it.
- packages/events has no dead-letter path. Every consumer will hit this;
  worth its own decision record.
```

Findings do not need acceptance criteria or a rollback point. That is the point
of them: they cost a line to record and nothing to carry.

## Scope reduction needs the same ceremony

Silently dropping a requirement is the mirror image of creep and is treated the
same way: it is a change to what was agreed.

A step that cannot be finished, a requirement that turns out too expensive, a
capability deferred to make a deadline — each moves to the non-goals with a
reason, and the requester is told. Reducing scope quietly produces a plan that
reports complete while failing acceptance, which is discovered by whoever
depended on the dropped part.

## Creep in the other direction

Planning itself creeps. A plan that grows past the work it describes is its own
failure mode:

- Steps with three paragraphs of prose and one line of action.
- A plan for a one-file change with a rollback section, a risk table and a
  capability map.
- An investigation step for something answerable by reading one file.
- Identifiers and cross-references in a six-step plan where nothing is cited.

The test is the same as for the code: would a reader use this? A plan longer
than the diff it produces was written for the wrong audience. Match the
ceremony to the work — a bounded change to a flow already in the repository
needs a stated intent and agreement, not a document.

<!-- sources: obra-writing-plans, addy-planning, mattpocock-spec, obra-brainstorming -->
