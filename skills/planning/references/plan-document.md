# The plan document

## Contents

- [What the document is for](#what-the-document-is-for)
- [Where it lives](#where-it-lives)
- [Header and global constraints](#header-and-global-constraints)
- [Non-goals](#non-goals)
- [The rollback point](#the-rollback-point)
- [The step block](#the-step-block)
- [Consumes and produces](#consumes-and-produces)
- [The acceptance line](#the-acceptance-line)
- [Identifiers, and when they help](#identifiers-and-when-they-help)
- [No placeholders](#no-placeholders)
- [Self-review](#self-review)

## What the document is for

The plan is read by someone with none of your context, out of order, often one
step at a time, sometimes in a fresh session. Every property below follows from
that: repetition over cross-reference, exact paths, exact signatures, exact
commands.

It is not a design document. The design argument — options, trade-offs,
rejections — belongs in the decision record (`exploring-options.md`). A plan
that re-argues its own approach gets skimmed, and the steps get skimmed with it.

## Where it lives

Look for an existing convention before inventing one: a plans or design
directory in `docs/`, a `specs/` tree, a `tasks/` directory. Match its
naming exactly.

Before writing, check whether a plan already there has unchecked steps.

- Same work, being revised or extended → amend that file in place.
- Different work → stop and ask. Those unchecked boxes may be the only record
  of what another session is mid-way through, and a plan file is usually not
  recoverable from anywhere else.

No convention exists → ask where it should go. Creating a second convention
beside an existing one costs more than the question.

## Header and global constraints

```markdown
# Notifications v1 — plan

Goal: users see an in-app notification for three qualifying events within 60s.
Approach: outbox table written in the triggering transaction; poller in
services/worker delivers; web reads through the generated client.
Requirements: docs/plans/2026-09-notifications-requirements.md
Decision record: docs/adr/adr-0010-notification-outbox.md
Rollback point: after step 3. See below.

## Global constraints
- Node 22 (the worker's runtime floor; the repo's CI matrix pins it).
- No new infrastructure this cycle.
- `openapi.yaml` is the only source of API shape; never hand-write a request.
- Enterprise sends must remain retrievable — do not delete outbox rows.
```

Global constraints are the project-wide bounds every step inherits: version
floors, dependency limits, platform requirements, naming rules. Copy exact
values from the requirements rather than paraphrasing — a version floor
paraphrased as "recent Node" stops being a constraint.

Link the requirements rather than restating them. The plan argues from them, so
they travel together; a plan whose requirements have been lost cannot be
reviewed, only obeyed.

## Non-goals

```markdown
## Non-goals
- Push notifications. Needs store credentials nobody has; deferred, not dropped.
- Email delivery. services/mailer stays as it is; no step touches it.
- The 7-year retention send log. Separate capability, its own plan.
- Digest/batching. Requires a scheduler; revisit if "too spammy" is reported.
```

Each non-goal says where the thing went: deferred, separate plan, or dropped
with a reason. A bare exclusion list reads like an oversight, and the excluded
item gets added back by the first person who notices it missing.

Non-goals are what makes scope creep detectable during execution: without
them, every adjacent improvement is arguably in scope, and nothing can be
called out as outside it.

## The rollback point

State where work can stop, and what state stopping leaves behind. Two things
make this non-obvious and both are common:

- **Forward-only migrations.** Reverting the deploy does not revert the schema.
  If the plan applies a migration in step 2, then from step 2 onward the
  rollback is "a new forward migration", not "revert".
- **Anything already released or applied to a shared environment.** Once the
  generated client has landed in a consumer, rolling back the producer breaks
  the consumer.

```markdown
Rollback point: after step 3 the outbox exists but nothing reads it, which is
inert and safe to leave. From step 4 on, rollback means a forward migration
dropping the table (db/migrations is forward-only; adr-0009) plus reverting the
poller. Do not stop between steps 5 and 6: web would call an endpoint that has
been removed from openapi.yaml.
```

## The step block

One block per step, in dependency order.

```markdown
## Step 4 — Outbox poller in the worker

Depends on: step 3 (the table and its writer must exist).
Files:
  create services/worker/jobs/deliver-notifications.ts
  create services/worker/jobs/deliver-notifications.test.ts
  modify services/worker/index.ts  (register the job)
Consumes: `claimOutboxBatch(limit: number): Promise<OutboxRow[]>` and
  `markDelivered(id: string): Promise<void>` from step 3.
Produces: nothing other steps import.
Do: claim a batch, deliver each row, mark it delivered in the same
  transaction as the delivery record. On throw, leave the row unclaimed so the
  next tick retries it; never mark a row delivered before the write succeeds.
Accept: `make test-one FILE=services/worker/jobs/deliver-notifications.test.ts`
  → passes, including the case where delivery throws and the row stays
  claimable. Then `make test` → full suite green.
```

Sizing: a step is the smallest unit that carries its own acceptance check and
is worth a reviewer's separate yes or no. Fold setup, config and scaffolding
into the step whose deliverable needs them — a step that only creates a
directory cannot be accepted or rejected on its own.

Every step leaves the system working. A step that requires the next step to
land before anything runs is half a step; merge them or move the boundary.

## Consumes and produces

The single highest-value block in a plan whose steps will be executed
separately, and the one most often omitted.

- **Consumes** — exact signatures this step relies on from earlier steps.
- **Produces** — exact signatures later steps will import, with parameter and
  return types.

The executor of step 6 sees step 6. Without *produces* on step 3 they invent a
name, and the integration fails on a rename rather than on anything real. This
is also where a plan's internal contradictions become visible: if step 3
produces `markDelivered(id)` and step 6 consumes `markSent(row)`, writing both
blocks makes the mismatch impossible to miss.

Keep the types identical across blocks, character for character. `clearLayers()`
in one step and `clearFullLayers()` in another is a bug the plan caused.

## The acceptance line

A step without one is not a step. The line has two halves and both are
required:

- the repository's own command, exactly as it would be typed;
- the output that counts as passing.

Read the command from the repository — its Makefile, `package.json` scripts,
`pyproject.toml`, `Cargo.toml`, `build.gradle`, or the CI workflow, which is
the one that actually gates merges. Prefer a checked-in wrapper over a global
tool. Never write a default like `npm test` on the assumption it exists; in
most repositories it is wrong, and a plan that fails on its own first command
loses the executor's trust for every later one.

Some steps are not test-shaped. They still get a command:

| Step kind | Acceptance |
|---|---|
| Schema change | `make migrate` on a scratch database, then a query showing the new shape |
| Interface change | `make client && make typecheck` → 0 errors across all workspaces |
| Dependency upgrade | build and full suite green, plus the specific behaviour the upgrade was for |
| Config or CI change | the pipeline run, or the tool's own validate/dry-run subcommand |
| Deletion | full suite green plus a search proving no remaining references |
| Investigation | the question answered in writing, with the command or code that answered it |

"Run tests" is not an acceptance line: no command, no expected output, no way
to be wrong. Neither is "verify it works".

## Identifiers, and when they help

For a plan with cross-references — a requirement cited by three steps, a risk
that gates one of them — prefixed identifiers (`REQ-001`, `TASK-004`,
`RISK-002`, `ASSUMPTION-001`) make the citations checkable. Each identifier is
**declared exactly once**, at the row or bullet that introduces it, and may be
referenced anywhere.

A declared-twice identifier means two different things share a name, and every
citation of it is now ambiguous. This is mechanically checkable:

```bash
# Declarations in table rows must be unique.
grep -oE '\| (TASK|GOAL)-[0-9]+ \|' "$PLAN" \
  | sed -E 's/.*((TASK|GOAL)-[0-9]+).*/\1/' | sort | uniq -d

# Declarations in bullet lines must be unique.
grep -oE '^- \*\*(REQ|CON|RISK|ASSUMPTION|DEP|TEST)-[0-9]+\*\*:' "$PLAN" \
  | sed -E 's/^- \*\*([A-Z]+-[0-9]+)\*\*:.*/\1/' | sort | uniq -d
```

Both must print nothing. [verified] against a POSIX shell with GNU-compatible
`grep`, `sed`, `sort` and `uniq`.

For a plan of six steps with no cross-references, identifiers are overhead.
Add them when something is cited, not by default.

## No placeholders

Each of these is a decision deferred onto the executor at the moment they have
the least context. In a finished plan they are defects, not shorthand:

- `TBD`, `TODO`, "details to follow", "fill in during implementation"
- "Add appropriate error handling", "add validation", "handle edge cases" —
  which cases, and what happens in each
- "Write tests for the above" — which behaviour, at which seam, asserting what
- "Similar to step N" — repeat it; steps are read out of order
- A step that says what to do without saying how, where the how is the
  difficult part
- A reference to a type, function or table that no step creates
- A command with a placeholder argument (`make test-one FILE=<...>`) left
  unfilled

## Self-review

Once, with fresh eyes, after the plan is complete. Three checks:

1. **Requirement coverage.** Walk each requirement and name the step that
   implements it. Anything unmatched is either a missing step or a requirement
   that should have been a non-goal; decide which and write it down.
2. **Placeholder scan.** Search the plan for the patterns above, plus any
   remaining `[NEEDS CLARIFICATION]`.
3. **Name and type consistency.** Every *consumes* matches a *produces*,
   character for character. Every path named exists, or is created by an
   earlier step in this plan.

Fix what you find inline; there is no second pass. Then run the gate: for every
step you can quote its command, its expected output, and either its
dependencies or the argument that it has none.

<!-- sources: obra-writing-plans, copilot-plan, addy-planning, mattpocock-spec -->
