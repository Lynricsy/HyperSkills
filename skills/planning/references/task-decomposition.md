# Task decomposition

## Contents

- [Map the dependencies before cutting](#map-the-dependencies-before-cutting)
- [Slice vertically, along the dependency order](#slice-vertically-along-the-dependency-order)
- [Right-sizing a step](#right-sizing-a-step)
- [Split triggers](#split-triggers)
- [One subsystem per step](#one-subsystem-per-step)
- [Checkpoints](#checkpoints)
- [When one request is several capabilities](#when-one-request-is-several-capabilities)
- [Decomposing work in an existing codebase](#decomposing-work-in-an-existing-codebase)
- [Ordering heuristics](#ordering-heuristics)

## Map the dependencies before cutting

Decomposition starts from what depends on what, not from a list of things to
do. A list produced without the graph will be in the author's order of
thought, which is roughly the reverse of the executable order.

Write the graph down. ASCII is enough:

```
outbox table + writer
   |
   +-- poller (delivers, marks delivered)
   |      |
   |      +-- send log  (reads outbox rows)
   |
   +-- openapi.yaml: GET /notifications   <-- frozen contract
          |
          +-- regenerated api-client
                 |
                 +-- web: bell + list
                 +-- mobile: call-site updates
```

Two things fall out of the graph immediately: the build order (bottom-up from
whatever has no dependencies) and the parallelism (siblings, once their shared
parent is frozen — see `parallelism.md`).

Dependencies to look for specifically, because they are the ones people miss:

- **Generated artefacts.** A generated client, generated types, a compiled
  schema. Every consumer depends on the generator's input, not on the output.
- **Shared schema.** Two features touching the same table serialise on the
  migration even when they look unrelated.
- **Contracts with a consumer outside this plan.** Another service, another
  team's app, a published package.
- **Anything that has to be true at runtime before something else works.** A
  feature flag, a credential, a queue, a seeded row.

## Slice vertically, along the dependency order

Once the graph exists, cut slices that each deliver something observable,
rather than layers that deliver nothing until the last one lands.

```
Horizontal (avoid)                Vertical (prefer)
1. all the schema                 1. one event type end to end: outbox row
2. all the endpoints                 written, delivered, visible in web
3. all the UI                     2. second event type (handler only)
4. wire it together               3. third event type (handler only)
                                  4. read-state and the unread badge
```

Horizontal slicing hides integration risk in the last step, which is also the
step with the least time left. Vertical slicing pays the integration cost
first, on the smallest possible case, where fixing it is cheap.

Vertical does not mean ignoring the graph: the first slice still needs the
outbox before the poller. It means the slice is cut through the layers rather
than along them.

Two honest exceptions:

- **A migration is its own step.** It is not part of a vertical slice because
  it cannot be half-applied, and with forward-only tooling it cannot be undone.
- **Freezing a contract is its own step.** Its deliverable is agreement plus a
  committed artefact, not behaviour.

## Right-sizing a step

A step is the smallest unit that carries its own acceptance check and is worth
a reviewer's separate yes or no.

That definition does the work that time estimates cannot. "About two hours"
means nothing for a step whose difficulty is unknown, and nothing at all for an
executor that is not a person. "Could a reviewer accept this while rejecting
its neighbour" is answerable now, from the plan.

Consequences of the definition:

- Setup, configuration, scaffolding and documentation fold into the step whose
  deliverable needs them. A step that only creates a directory cannot be
  accepted or rejected on its own.
- A step that cannot be accepted without the next one landing is half a step.
  Merge them, or move the boundary so both sides stand alone.
- A step that would be reviewed by two different people for two different
  reasons is two steps.

## Split triggers

Split when any of these is true. Each is observable from the plan, not from
how the work feels:

- **The title contains "and".** `Add the outbox and the poller` is two steps
  with two acceptance checks.
- **The acceptance check needs more than about three assertions to describe**,
  or needs two different commands to be complete.
- **It touches two independent subsystems.** See below.
- **The *files* list has an inner boundary**: a migration plus application
  code, or a generated file plus its consumers.
- **Part of it is blocked and part is not.** Split at the blockage so the
  unblocked half can proceed.
- **You cannot write its *produces* block** because it produces several
  unrelated things.

Do not split on file count alone. A step that edits nine call sites after a
rename is one step with one acceptance check; a step that edits two files in
two subsystems is two steps.

## One subsystem per step

A step spanning two independent subsystems is split, or the plan says why it
cannot be. Two reasons:

- A review of it cannot be partially approved. The reviewer either accepts
  both halves or blocks both.
- A failure in it cannot be localised. When the acceptance check fails, the
  cause is in one of two places with different owners.

The legitimate exception is a change that is only correct when applied
atomically — a rename that crosses a package boundary, a schema field and its
single writer. Say so in the step:

```
Cannot be split: the generated client and mobile's call sites must land
together or mobile's strict build is red on main between the two steps.
```

That sentence is what turns an unsplittable step from an oversight into a
decision.

## Checkpoints

After every two or three steps, insert a checkpoint whose acceptance is the
whole system rather than one step:

```markdown
## Checkpoint — after step 4
- `make test` → full suite green
- `make typecheck` → 0 errors including mobile strict mode
- One real event produces exactly one delivery, verified by replaying it twice
```

Checkpoints catch the class of error individual steps cannot: an interaction
between two steps that each pass in isolation. They are also the natural place
to stop — a plan abandoned at a checkpoint leaves a working system, which is
what makes the rollback point meaningful.

## When one request is several capabilities

Some requests bundle capabilities that could each ship alone. Detecting this
early is worth more than any amount of detail on the wrong scope.

Decompose first when:

- the request names capabilities with their own consumers or data (identity,
  billing, notifications, reporting);
- its acceptance criteria cluster into groups that could be verified
  separately;
- one capability could be cut or replaced without rewriting the others'
  requirements.

Then propose a capability map — a table and a build order, not a project plan:

```markdown
# Capability map — notifications initiative

| Module | Responsibility | Depends on |
|---|---|---|
| outbox | Durable event capture and delivery | — |
| notifications | User-facing list, read state | outbox |
| send-log | Retention and retrieval for compliance | outbox |

Build order: outbox → notifications, send-log
```

Three rules make the map useful rather than decorative:

- **Stable ids**, chosen once and never renamed. Plans and steps select work by
  id; renaming breaks every reference.
- **One-way dependencies, no cycles.** If two modules each need the other, they
  are one module — splitting them creates two plans that cannot be executed in
  either order.
- **Interfaces live at the boundary.** The map records that `notifications`
  depends on `outbox`; the contract between them belongs in the provider's
  own plan.

Get the map agreed before writing any module's requirements. Reviewing ten
lines is cheap; discovering the boundaries were wrong after two plans are
written is not.

Then recurse: each module gets its own clarify → plan cycle, in build order.

## Decomposing work in an existing codebase

Read the structure before proposing changes to it, and follow what is there.
Three specific adjustments:

- **Follow existing patterns even when you would have chosen differently.**
  A plan that unilaterally restructures while delivering a feature produces a
  diff nobody can review.
- **Include targeted improvements where existing code blocks the work.** A file
  that has to be split for the change to fit is part of the change; say so as
  its own step with its own acceptance.
- **Do not include unrelated refactoring.** It is a second plan. Write it down
  somewhere and leave it.

Where a plan touches code that is wrong but works, note it as a finding rather
than a step. Findings do not need a rollback point.

## Ordering heuristics

Within the dependency order, several sequences are valid. Prefer, in order:

1. **Riskiest unknown first**, as an investigation rather than a build step.
   Everything built before the unknown is settled rests on a guess. See
   `risk-and-unknowns.md`.
2. **Contracts before consumers.** Freeze the interface, then let both sides
   build against it.
3. **Irreversible things late**, unless something depends on them. A migration
   applied on day one constrains every later decision about the schema.
4. **Thinnest end-to-end path first.** One event type all the way through beats
   three event types with no delivery.
5. **Then whatever unblocks the most parallel work**, if any real parallelism
   exists.

Where two heuristics conflict — the riskiest unknown is also the irreversible
migration — resolve it by splitting: investigate cheaply first (a migration on
a scratch database proves the shape), apply for real later.

<!-- sources: addy-planning, obra-writing-plans, mattpocock-spec, neolab-sdd -->
