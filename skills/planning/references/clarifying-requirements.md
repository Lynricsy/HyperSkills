# Clarifying requirements

## Contents

- [The two pre-checks](#the-two-pre-checks)
- [Look up, ask, or assume](#look-up-ask-or-assume)
- [Making a requirement decidable](#making-a-requirement-decidable)
- [Requirements, constraints, guidelines](#requirements-constraints-guidelines)
- [Finding the constraint nobody stated](#finding-the-constraint-nobody-stated)
- [The assumption block](#the-assumption-block)
- [Asking in one round](#asking-in-one-round)
- [Keeping what clarification produced](#keeping-what-clarification-produced)
- [How much process this request needs](#how-much-process-this-request-needs)
- [Self-review before handing requirements on](#self-review-before-handing-requirements-on)

## The two pre-checks

Run both before asking the requester anything. Both are cheap, both routinely
end the conversation, and both are skipped almost always.

**Already built.** Search for the behaviour by domain concept, not by the
request's wording. A request for "notify users" will not match a module called
`digest` or `announcements`. Search the schema and the route table too, not only
identifiers. Then say where you looked:

```
Checked for an existing implementation: grepped services/ and packages/ for
notify|alert|digest|announce, read the route table in api/routes.ts, and
listed db/migrations for a notifications table. Nothing exists. The closest
thing is services/mailer, which sends but records nothing.
```

Reporting the search matters as much as running it. Without it, a reviewer who
knows the codebase cannot tell whether you missed something or there is nothing
to miss — and re-runs the search themselves.

**Already rejected.** Look for the request's history: closed issues, an
out-of-scope or decisions directory, ADRs, a FAQ in the README. A request that
was declined once is usually declined for a reason that still holds, and
re-deciding it without that reason wastes the decision that was already made.
If a prior rejection exists, surface it with its reason before proposing
anything: the requester may have new information that overturns it, which is a
different conversation from one that ignores it.

## Look up, ask, or assume

Every open point goes in exactly one bucket. Misfiling is the main way
clarification wastes everyone's time.

| Bucket | Test | Consequence of misfiling |
|---|---|---|
| Look up | The answer exists in the repository, a `--help`, a changelog, a schema, or an official doc | Asking for it burns a round trip and signals you have not read their code |
| Ask | Two defensible answers with different costs, and the cost lands on the requester | Deciding it yourself commits them to a cost they never agreed to |
| Assume | Neither discoverable nor decision-shaped, and does not change this round's decomposition | Leaving it unwritten means nobody knows the plan rested on it |

Concretely, in a request to add notifications:

- *Which test command does this repo use?* — look up (Makefile, CI workflow).
- *Does the event bus guarantee delivery?* — look up (read the bus).
- *Immediate or digest?* — ask. It changes the design and the user experience.
- *Email, in-app, or push for v1?* — ask. It changes the scope by weeks.
- *Do we notify on every event type or the three support named?* — ask.
- *Timestamps in UTC* — assume, and write it down.

## Making a requirement decidable

A requirement is decidable when someone who did not write it can look at the
running system and say yes or no. The test is not "is this specific" but "could
two honest people disagree about whether it is met".

| Not decidable | Decidable |
|---|---|
| "Feels instant but not spammy" | "A notification appears within 60s of the event. At most one per user per event." |
| "Must not double-send on retry" | "Replaying the same event id after a worker retry produces no second delivery." |
| "Handles errors gracefully" | "A send failure leaves the notification unsent and retryable, and surfaces in the worker's error output." |
| "Works on mobile too" | "The same list renders in `mobile/` against the generated client with no hand-written request code." |
| "Enterprise can retrieve what we sent" | "For any account, every message sent in the last N days can be listed with its body and timestamp." |

Given-When-Then is a reliable forcing function because each slot has to be
filled with something observable:

```
AC-1. Given a user with notifications enabled,
      when an event they subscribe to is committed,
      then exactly one notification row exists for that user and event id.
```

The value is not the format. It is that "then feels instant" cannot be written
in the *then* slot without noticing it is not an outcome.

## Requirements, constraints, guidelines

Label them separately. They behave differently under pressure, and a list that
mixes them gets negotiated as one block.

- **Requirement** — the thing being asked for. Dropping one means not shipping
  the request.
- **Constraint** — a bound the solution must respect, usually external:
  a compliance rule, a version floor, a platform limit, an interface the caller
  already depends on. Dropping one means shipping something unusable.
- **Guideline** — a preference. Dropping one costs consistency and nothing else.

The common failure is a constraint filed as a guideline. "Enterprise accounts
must be able to retrieve anything we sent them" is a compliance constraint; once
it reads like a nice-to-have it is the first thing cut, and the cut is
discovered during an audit.

## Finding the constraint nobody stated

Constraints arrive buried in prose, in comments from third parties, or not at
all. Sweep for these:

- **Words like "obviously" and "of course".** They mark a requirement the writer
  believes is too evident to specify. It is usually the hardest one in the
  request.
- **A deadline attached to something unrelated.** "before the audit window"
  is a constraint on scope and on what evidence must exist, not just on timing.
- **Comments by people other than the reporter.** Each is a candidate
  requirement from someone who will review the result. List them separately;
  do not silently merge them into the reporter's request, and do not silently
  drop them either.
- **"Just like <product> does it."** An analogy, not a requirement. Ask which
  property of that product matters — the immediacy, the grouping, the badge, the
  mute controls. They are four different features.
- **"Nothing fancy" / "keep it small".** A constraint on scope. It gives you
  authority to declare non-goals, and it conflicts with any comment asking for
  an extra channel. Surface the conflict rather than resolving it quietly.
- **An existing asset cited as a shortcut.** "We already have the templates"
  is a claim to verify, not a fact. Verify it and report what is actually
  reusable.

## The assumption block

Everything in the assume bucket goes into the artifact, each with its
dependents. The dependents turn the block from a disclaimer into a tool:
when an assumption falls, you already know the blast radius.

```
## Assumptions
A1. "Important" means the three event types support named, not every domain
    event. — if false: R2 changes, and steps 3 and 5 grow by one handler each.
A2. In-app only for v1; no email, no push. — if false: step 6 is replaced and
    a delivery-channel abstraction becomes a prerequisite.
A3. Timestamps are UTC and formatted client-side. — if false: step 4 only.
```

An assumption with no dependents is noise: delete it. An assumption whose
dependents are "everything" is not an assumption, it is the decision the plan
is waiting on — move it to the ask bucket.

Use an inline `[NEEDS CLARIFICATION: <question>]` marker in the draft where an
unresolved point blocks a specific sentence. It keeps the unknown attached to
the place it matters instead of in a separate list nobody re-reads, and a draft
still containing markers is visibly not ready.

## Asking in one round

Ask everything in the ask bucket at once, numbered, each carrying your
recommended answer. One question per message doubles the number of round trips
and gives the requester no view of the whole decision surface; a recommendation
turns a quiz into a review, which is faster to answer and easier to correct.

```
❓ Q1 — Immediate or digest
Send each notification as its event lands, or batch them?
➡️ Recommended: immediate for v1. Batching needs a scheduler we do not have,
   and "not spammy" is achievable by limiting which events qualify.
```

Do not ask more than about five; more than that usually means the request needs
decomposing rather than clarifying. Never include a question whose answer is in
the repository.

## Keeping what clarification produced

Multiple rounds lose their own results. Before ending a round, write down what
is now settled, not only what is still open:

```
## Established
- Three qualifying events: plan changed, invoice failed, member invited.
- In-app only for v1. Push is deferred (see non-goals).
- Retrievability is a separate capability, tracked on its own.

## Still open
- Q2 (retention window) — blocks the send-log schema only.
```

Without the *established* half, the next session re-asks questions that already
have answers, and the requester loses confidence faster than from any technical
mistake.

## How much process this request needs

Classify before deciding what to produce, and say the classification out loud so
it can be overridden.

- **Probe** — a feasibility question whose output is an answer, not code you
  keep. State the question and what you will try, get a nod, find out as
  cheaply as correctness allows. Whatever gets built is labelled throwaway.
- **Bounded** — a change to a flow that already exists in this repository and
  can be read end to end. Ask the questions that matter, state the intent in a
  few sentences, get agreement, implement. No document.
- **Structural** — new subsystems, new interfaces, or changes to interfaces
  others depend on. Full path: questions, options, decidable requirements,
  written plan.

Bounded measures the repository, not your familiarity: if the flow being
changed is not here to read, the work is structural no matter how ordinary it
sounds. The classification only ratchets upward — complexity discovered
mid-task upgrades the path, and nothing downgrades it. When two
classifications are defensible, take the heavier one; the cost of an extra
page of writing is bounded, and the cost of a structural change made as a
bounded one is not.

## Self-review before handing requirements on

Four checks, once, on the finished requirements:

1. **Placeholders.** Any TBD, any unresolved `[NEEDS CLARIFICATION]`, any
   section that says what it will say.
2. **Contradictions.** Does any requirement conflict with another, or with a
   constraint? "Keep it small" against "web, mobile, and push" is a
   contradiction to surface, not average out.
3. **Ambiguity.** Could any requirement be read two ways? Pick one reading and
   make it explicit; an ambiguity that survives into a plan becomes two
   incompatible implementations.
4. **Size.** Does this describe several independently shippable capabilities?
   Then it needs decomposing before it needs detailing — see
   `task-decomposition.md` for the capability map.

Fix what you find inline. There is no second review pass.

<!-- sources: mattpocock-spec, addy-planning, obra-brainstorming, copilot-plan, obra-writing-plans -->
