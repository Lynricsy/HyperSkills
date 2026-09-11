# Parallelism and delegation

## Contents

- [The burden of proof](#the-burden-of-proof)
- [Three categories](#three-categories)
- [Freezing a contract](#freezing-a-contract)
- [Things that must be serialised](#things-that-must-be-serialised)
- [Recording the parallelism decision](#recording-the-parallelism-decision)
- [What a delegated step must carry](#what-a-delegated-step-must-carry)
- [Integrating parallel work](#integrating-parallel-work)
- [Verifying a delegated step](#verifying-a-delegated-step)
- [When parallelism is not worth it](#when-parallelism-is-not-worth-it)

## The burden of proof

Two steps are parallel only after an argument that they are. The default is
sequential.

The common convention — "tasks within a phase are parallel unless a dependency
is declared" — inverts the burden and fails in the only case that matters. An
undeclared dependency does not stop existing because nobody wrote it down; it
surfaces later as a merge conflict, a broken build on someone else's machine,
or two implementations of the same interface that disagree. The dependencies
that go undeclared are exactly the ones the author did not notice, which are
exactly the ones that cause damage.

So: state parallelism per pair, with the reason. A blanket "all tasks are
independent" is a claim about every pair simultaneously, which almost never
survives contact with the dependency graph.

## Three categories

Every pair of steps lands in one.

**Safe to parallelise.** Different files, no shared schema, no shared
generated artefact, no shared runtime state, and neither consumes what the
other produces.

- Two independent event handlers writing through an existing interface.
- Tests for behaviour already implemented and merged.
- Two unrelated pages in the same app, if they do not touch shared routing or
  layout.

**Must be serialised.** One of them changes something the other depends on
existing, or the change itself cannot be interleaved.

- Schema migrations — one at a time, in a defined order, especially with
  forward-only tooling where a wrong order is not undoable.
- Anything touching shared module state or a shared config file.
- A rename and any work inside its blast radius.
- Two steps that both edit a generated file's input.

**Needs coordination.** They could run at the same time, but only after
something is settled first. This is the category people collapse into "safe",
and it is where the expensive failures are.

- Producer and consumer of an interface: freeze the interface, then both.
- Two consumers of a generated client: regenerate once, then both.
- Two features whose acceptance depends on the same new configuration.

## Freezing a contract

Freezing means the interface exists as a committed artefact both sides read,
and neither side changes it without telling the other. Not "we agreed on a
shape in chat".

A freeze step's deliverable is the artefact, and its acceptance is that
consumers can build against it:

```markdown
## Step 5 — Freeze GET /notifications in openapi.yaml

Depends on: step 4 (the poller defines what a delivered notification contains).
Files: modify openapi.yaml; commit the regenerated packages/api-client.
Produces: `listNotifications(params: {cursor?: string}): Promise<{items:
  Notification[]; nextCursor?: string}>` and the `Notification` type with
  fields id, kind, createdAt, seenAt.
Do: add the path and schema, then `make client`. Do not change either again
  without updating steps 6 and 7.
Accept: `make client` leaves no diff on a second run, and `make typecheck`
  → 0 errors across all workspaces, including mobile's strict build.
```

That last clause is the part usually skipped. On a generated client shared by
two apps, regeneration is source-breaking for the stricter consumer: widening a
union type makes existing call sites fail to compile. So the freeze step is not
done when the file is committed — it is done when every consumer still
typechecks. Leaving those errors for "whoever picks up the mobile task" means
the contract was never frozen; it was published and abandoned.

Without the freeze, both sides land, disagree, and one is rewritten. The
rewrite costs more than the serialisation would have.

## Things that must be serialised

Some boundaries are irreducible regardless of how the work is split. Name one
owner for each and let that step run alone:

| Boundary | Why |
|---|---|
| Migrations | Order is part of the meaning; forward-only tooling makes a wrong order permanent |
| Generated artefacts | Two regenerations from different inputs produce a file nobody can merge |
| Lockfiles and dependency manifests | Concurrent edits conflict textually and semantically |
| Shared config, CI workflow, feature-flag definitions | Last write wins, silently |
| A rename or move | Every concurrent edit inside its radius conflicts |
| The plan document itself | Two agents amending it produce a plan with two states |

## Recording the parallelism decision

Put the conclusion in the plan where the executor will see it, per step:

```markdown
## Step 6 — web: bell and list
Depends on: step 5 (frozen client).
Parallel with: step 7 (mobile call sites) — different workspaces, no shared
  files, both read the client from step 5 and neither changes it.

## Step 7 — mobile: update call sites for the regenerated client
Depends on: step 5.
Parallel with: step 6. Not parallel with step 5: regeneration is what breaks
  these call sites.
```

"Not parallel with X because Y" is worth as much as the positive claim. It is
the sentence that stops someone from starting X early.

## What a delegated step must carry

A delegated executor sees one step and has none of the plan's context. The step
is either self-contained or it is a guess. Required:

- Exact paths to create, modify and test.
- *Consumes*: exact signatures it may rely on, because it cannot read the code
  that provides them if that code is being written concurrently.
- *Produces*: exact signatures others will import — so a sibling does not have
  to guess the name.
- The acceptance command and its expected output.
- Explicit non-goals for this step: which adjacent files it must not touch.
  Without this, two delegates independently "fix" the same shared file.
- The global constraints it inherits.

Repeat rather than cross-reference. "Similar to step 3" is unusable to someone
who is not reading step 3, and cross-references between steps are how two
delegates end up reading two different versions of the same decision.

When several steps run concurrently, tell each one not to run project-wide
validation mid-flight. A full suite run against a half-landed sibling reports
failures that belong to nobody, and the delegate spends its time on them. Full
validation happens once, at the checkpoint, by whoever integrates.

## Integrating parallel work

Name one integrator per checkpoint. The integrator, not the delegates:

- resolves conflicts in the serialised boundaries above;
- runs the checkpoint's full-system acceptance;
- amends the plan with what actually happened.

Concurrent work that also amends the plan produces a plan document with two
inconsistent states, which is worse than no plan because it looks authoritative.

## Verifying a delegated step

A delegate's report that it finished is not evidence, however detailed. Check:

1. The diff. It shows what changed; the report shows what the delegate
   believes changed. When they disagree, the diff is right.
2. The acceptance command, run by you, with its output. "Completed" without an
   output you have seen is the most common false completion there is.
3. The step's non-goals. A delegate that also improved three other files has
   produced work nobody planned and nobody reviewed.

This is not distrust of the delegate specifically — the same rule applies to
your own earlier session, whose claims you also cannot re-derive.

## When parallelism is not worth it

Parallelism costs a freeze step, a coordination boundary, and an integration
pass. Below a certain size that exceeds the time saved.

Skip it when:

- The dependency chain is nearly linear anyway. Two workers on a five-step
  chain with four real dependencies means one worker and one spectator.
- The steps are small relative to the freeze they would need. A contract that
  takes as long to settle as the two steps take to write is not worth freezing.
- The riskiest unknown is not settled. Parallel work on an unproven premise
  multiplies the rework rather than the throughput.
- Only one person or session will actually execute. Marking steps parallel
  changes nothing and removes the ordering information the executor wanted.

Say this out loud when asked to parallelise something that does not divide:
"steps 1–4 are a chain; the second worker has nothing to do until step 5" is a
more useful answer than a fabricated split.

<!-- sources: addy-planning, obra-executing, copilot-plan, obra-writing-plans -->
