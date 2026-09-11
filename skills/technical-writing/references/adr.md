# Architecture decision records

## Contents

- [What an ADR is](#what-an-adr-is)
- [Match the repository's existing convention first](#match-the-repositorys-existing-convention-first)
- [Fields](#fields)
- [Writing each field](#writing-each-field)
- [Lifecycle and superseding](#lifecycle-and-superseding)
- [When not to write an ADR](#when-not-to-write-an-adr)
- [Reviewing an ADR](#reviewing-an-adr)

## What an ADR is

A short, dated, numbered record of one decision: the constraints that forced it,
what was chosen, what was rejected and why, and what the project now has to live
with. Its audience is a maintainer six months out who is about to change the
thing, or propose the rejected option again.

The code records what was built. It cannot record what was considered and
rejected, or which constraint has since disappeared. That is the whole value of
the artefact, and the reason an ADR that only describes the chosen design is
barely worth its file.

## Match the repository's existing convention first

Before creating anything, look for an established convention and follow it. This
is the first step, not a courtesy: a second numbering scheme in a repository that
already has one means nobody can tell which record is authoritative, and both
sequences collide at the next number. [official]

Look for, in this order:

1. **Existing records.** `docs/adr/`, `docs/decisions/`, `doc/arch/`,
   `Documentation/Decisions/`, `adr/`. Any extension — `.md`, `.rst`.
2. **Tooling configuration.** An `.adr-dir` file (written by `adr-tools`), a
   MADR layout, a template file in the directory, a docs-site nav entry.
3. **Contributor instructions** that name a location or a template.

Match all three of: location and file extension, the numbering and filename
pattern (`0004-title.md`, `ADR-004-Title.rst`, `004-title.md` — continue the
sequence, never restart at 1), and the heading set already in use.

Where the evidence conflicts — two directories, or a template that does not
match the records beside it — say so and ask, rather than silently introducing a
third scheme. Only when no convention can be established do you pick one:
`docs/adr/NNNN-kebab-title.md`, four-digit sequence, the headings below.

## Fields

```markdown
# ADR-0007: Share the rate limit through Redis

- Status: Accepted
- Date: 2026-05-19
- Supersedes: ADR-0004
- Deciders: platform team

## Context and problem statement

## Decision drivers

## Considered options

## Decision

## Consequences

## Confirmation
```

`Supersedes` / `Superseded by` appear only when they apply. `Confirmation` is
the field most templates omit and the one that keeps the record honest: how
anyone will later verify this decision is being followed. [official]

## Writing each field

**Context and problem statement.** The situation and the constraint that forces
a decision — not the decision restated as a problem. "We need to use Redis" is
not a context. "Eight workers each limit themselves to the upstream's full
budget, so we send eight times the allowed rate, and the worker count changes on
every deploy" is. Include the numbers and the deadlines that bound the choice;
those are exactly what a reader six months later cannot reconstruct.

**Decision drivers.** The criteria, ranked. If two drivers conflict, say which
wins. A list of every desirable property is not a set of drivers; drivers are
the ones you were willing to trade against each other.

**Considered options.** At least two real ones, each with what it costs. An
option that nobody could have chosen is not an option — listing "do nothing"
when doing nothing was never acceptable inflates the record without informing
it. For each rejected option, state the reason it was rejected in terms of the
drivers above, because that is the sentence the next person needs when they
propose it again.

**Decision.** One sentence naming what was chosen, in the present tense.
Followed by the reasoning only where it is not already implied by the drivers.

**Consequences.** Both directions, and only the ones that are actually
consequences of this decision: what becomes easier, what becomes harder, what
new operational burden the project has acquired (a Redis instance to run and
monitor, a new failure mode when it is unreachable), and what this now
precludes.

**Confirmation.** How compliance is checked: a test, a lint rule, a review
checklist item, a metric. "Code review" is the weakest acceptable answer; a
named test is the strongest. A decision with no confirmation drifts out of
force without anyone noticing, and the ADR then documents a state of the world
that has not existed for a year.

## Lifecycle and superseding

```
Proposed -> Accepted -> Deprecated | Superseded by ADR-NNNN
```

- **Never delete or rewrite an accepted ADR** to reflect a new decision. The
  record of what was believed, and when, is the artefact. Editing it to match
  the present destroys the only account of why the code looks the way it does.
- Reversing a decision means a **new** ADR that names the one it supersedes,
  and an edit to the old one's Status line pointing forward. Both directions, or
  a reader arriving at the old record by search will act on retired guidance.
- Correcting a typo or adding a missing consequence is fine. Changing the
  decision is not.
- When the constraint that drove a decision disappears, that is worth its own
  short ADR even if the decision stands: it tells the next reader the record is
  still current for a different reason.

## When not to write an ADR

An ADR has a maintenance cost and a reading cost. Write one only for a decision
that is expensive to reverse **and** has a defensible alternative. Skip it for:

- **Reversible choices with an obvious answer.** Which formatter, which
  assertion library. Record those in the contributing guide as conventions.
- **Decisions the code already states unambiguously.** An ADR that says "we use
  PostgreSQL" next to a `postgres://` connection string and a schema directory
  adds nothing the reader could not see.
- **Implementation detail inside one module.** If changing it touches one file
  and no interface, a comment explaining the non-obvious intent is the right
  artefact.
- **A plan.** Plans have steps, owners and acceptance criteria; an ADR has a
  decision and its consequences. Writing the plan as an ADR loses the steps —
  use the `planning` skill for the plan and reference the ADR from it.
- **A decision nobody has made yet.** A Proposed ADR is legitimate; an ADR
  written to make a decision look settled is not.

The failure mode in both directions is real. No ADRs in a project with
significant architectural choices means every such choice gets re-litigated;
an ADR per commit means nobody reads any of them.

## Reviewing an ADR

- [ ] It follows the repository's existing location, numbering and headings.
- [ ] The context states a constraint, with numbers where there are numbers, and
      does not restate the decision.
- [ ] At least two options anyone could have chosen, each with its cost.
- [ ] Every rejection has a reason expressed in the stated drivers.
- [ ] Consequences include what got harder and what the project now has to
      operate.
- [ ] Confirmation names something checkable.
- [ ] Status and date are set; supersede links point both ways where they exist.
- [ ] Nothing in it will need editing when the decision is later reversed.

<!-- sources: addyosmani-skills, madr, jph-adr, mattpocock-skills -->
