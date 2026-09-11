# Sub-agents and parallelism

## Contents

- [What a sub-agent buys, and what it costs](#what-a-sub-agent-buys-and-what-it-costs)
- [Decomposition that survives](#decomposition-that-survives)
- [Context handoff is construction, not inheritance](#context-handoff-is-construction-not-inheritance)
- [Parallelism that is real](#parallelism-that-is-real)
- [Budgets per child](#budgets-per-child)
- [Model tier per role](#model-tier-per-role)
- [Failure isolation](#failure-isolation)
- [Integration is a step, not an afterthought](#integration-is-a-step-not-an-afterthought)
- [Trust inside the fan-out](#trust-inside-the-fan-out)
- [When not to fan out](#when-not-to-fan-out)

## What a sub-agent buys, and what it costs

One thing: a fresh, small context containing exactly what one piece of work
needs. That is worth a lot when the parent's context is large and the child's
task is narrow — the child is cheaper per turn, less distracted, and its
failure does not poison the parent's transcript.

The costs are real and usually underestimated:

- The parent pays to write the brief and to read the result. A child whose
  brief is longer than the work is a net loss.
- The child cannot ask clarifying questions mid-task in most harnesses, so an
  ambiguous brief produces confident wrong work.
- Children do not see each other. Two children editing the same file produce
  a merge conflict or, worse, a plausible file that satisfies neither brief.
- The parent must verify what the child reports. A child's "done" is a claim
  (`agent-loop.md`).

## Decomposition that survives

Fan out one child per **independent problem domain**, where independent means
three specific things:

1. It can be understood without context from the others.
2. It touches files or resources the others do not.
3. Its result does not change the brief of another child.

Failing (1) means you pay for the shared context N times and get N partial
understandings. Failing (2) is a conflict. Failing (3) is the common and most
expensive one: two children implementing both sides of an interface neither
of them has seen, after which one of them is rewritten.

Where (3) would be violated, freeze the contract first as its own step — the
type, the schema, the function signature — then fan out against it. A frozen
contract is what makes the parallelism real rather than asserted.

Batch same-shape work into one child rather than one child per item. Twelve
one-line edits of the same kind is one brief listing twelve files, reviewed
as one diff; twelve children cost twelve briefs and twelve reviews for the
same change.

## Context handoff is construction, not inheritance

A child should never receive the parent's history. Construct exactly what it
needs:

- The goal, in one sentence, stated as an outcome.
- The relevant facts the parent already established — paths, signatures,
  versions, decisions — restated, not referenced. A child cannot follow "as
  discussed above".
- Explicit non-goals, because a child with spare capacity will expand scope.
- The acceptance check: the command that proves the work done and the output
  that counts as passing.
- The output contract: what to return, in what shape. A child returning prose
  where the parent expected a structured result costs a re-run.

Large payloads go by reference to a file the child can read, not inline. An
inline 40 KB document is paid for in the parent's prompt *and* the child's.

## Parallelism that is real

Concurrency is per pair, with an argument. "These are all independent" survives
about two pairs of scrutiny; check each pair against the three conditions
above and write down the ones that share anything.

Also bounded by the outside world:

- **Provider rate limits.** Eight children at full tilt hit the same
  organisation-level token-per-minute ceiling, and every child starts
  retrying. The fan-out then runs slower than sequential execution while
  paying for the retries (`cost-and-reliability.md`). Cap concurrency
  and share one client, so the SDK's own connection pool and backoff apply.
- **Shared mutable state.** One database, one working tree, one index. Either
  give each child its own copy, or serialise the mutation and let only one
  child hold it.
- **Total spend.** Concurrency multiplies burn rate. A per-child budget with
  no aggregate cap means N children each stopping politely at their own limit
  while the total is N times what you authorised.

## Budgets per child

Every child gets its own turn cap, deadline and spend cap, and the parent
enforces an aggregate. Without the aggregate, the parent's own budget is
whatever its children decide to spend.

Give the parent a rule for what to do when a child reports `budget` or
`turn_cap`: resume it with a larger cap, re-scope its brief, or accept the
partial result. Deciding this after a child stalls, mid-run, produces the
"just bump it to 200 turns" reflex that caused the cap to exist.

## Model tier per role

Match the model to the judgement the role requires, and always name the model
explicitly. An omitted model inherits the parent's — usually the most capable
and most expensive — which silently defeats the whole exercise.

| Role | Tier |
|---|---|
| Transcription from a complete spec, single-file mechanical edit | cheapest |
| Implementation from a prose description, review of a small diff | mid |
| Multi-file integration, debugging, subtle review | standard |
| Architecture, final whole-change review | most capable |

One correction to the obvious cost model: turn count beats token price. The
cheapest models routinely take two to three times as many turns on
multi-step work, so they cost more overall and take longer. Use a mid tier as
the floor for anything that is not transcription.

## Failure isolation

A child's failure must be a value in the parent's hands, not an exception
that ends the fan-out:

- Collect results with per-child status, so one failure degrades one subtree
  rather than the batch.
- A child that fails twice on the same brief has a brief problem, not a model
  problem. Re-briefing beats retrying — including escalating a tier when the
  failure was judgement rather than mechanics.
- Time-box the whole fan-out, not only each child. N children each inside
  their deadline can still exceed the parent's.
- Keep each child's trajectory (`agent-loop.md`). A child's summary of
  its own failure is the least reliable account of it.

## Integration is a step, not an afterthought

Name one owner for the merge, and give it work to do:

- Read every child's actual output, not its report. The report is a claim.
- Check the seams: the interfaces children produced against the ones they
  consumed, the naming they each chose, the duplicated helper two of them
  wrote.
- Run the acceptance check for the whole change, once, after integration. Each
  child running the full suite mid-flight blocks on the others' half-finished
  work and reports failures that do not exist.

## Trust inside the fan-out

A child's output is untrusted text to the parent. If a child read a web page,
an instruction from that page can arrive in its report and reach the parent's
prompt — and the parent typically has more capability than the child did.
Two consequences:

- A child's result goes into the parent's context as delimited data, exactly
  like any other third-party content (`prompt-injection.md`).
- A child that handles untrusted content should not be the one holding
  irreversible tools, and its report should be a structured proposal the
  parent validates rather than a free-text instruction the parent follows.

## When not to fan out

- The work is sequential. Children that wait on each other cost more than one
  agent doing the steps, and the handoffs lose context at every boundary.
- The pieces are small. Below roughly a few minutes of work, the brief and
  the review dominate.
- The decomposition is unknown. Spawning a child to figure out the
  decomposition puts the least-informed participant in charge of the plan;
  work out the slices first, then fan out.
- One coherent judgement is required. Splitting a design across four children
  produces four designs.

<!-- sources: obra-superpowers, openai-agents-python, langchain-skills, murat-context-engineering -->
