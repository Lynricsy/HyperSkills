# Reviewing a plan before execution

## Contents

- [Read the plan against the repository](#read-the-plan-against-the-repository)
- [The verdict](#the-verdict)
- [Defect catalogue](#defect-catalogue)
- [Checking a parallelism claim](#checking-a-parallelism-claim)
- [Checking an acceptance line](#checking-an-acceptance-line)
- [Checking coverage in both directions](#checking-coverage-in-both-directions)
- [Findings that are not defects](#findings-that-are-not-defects)
- [Name the defects before rewriting](#name-the-defects-before-rewriting)

## Read the plan against the repository

Most plan defects are disagreements with reality, not internal
inconsistencies. A plan can be perfectly coherent and still name a service
that does not exist, a command that is not defined, or a parallelism that the
dependency graph forbids.

So the review is a comparison, not a proofread. Have the plan and the actual
code open together, and check every concrete noun: paths, services, tables,
commands, package names, interface names.

When the code is not available, say so and mark the affected findings as
unverified. Inventing the codebase in order to judge a plan produces
confident, wrong findings — and they are indistinguishable from the real ones.

## The verdict

One of three, stated up front:

- **Executable.** Any competent executor can follow it without inventing
  anything.
- **Executable after the fixes below.** The defects are local and listed.
- **Not executable.** A premise is wrong, or so many steps lack acceptance
  that following the plan would produce unverifiable work.

Give the verdict first. A review that lists twelve findings and never says
whether to start is a review the author has to interpret.

## Defect catalogue

For each defect, the execution failure it causes. A finding you cannot write
that column for is a preference, not a defect — drop it.

| Defect | What happens during execution |
|---|---|
| Step names a path, service or directory that does not exist | The executor invents a boundary the plan never decided; every later path is a guess |
| Step has no acceptance command | It can never be finished, only abandoned; it gets reported done when someone stops looking |
| Acceptance command is not the repository's own | The first command fails, and the plan's credibility goes with it |
| Acceptance has a command but no expected output | Any output is accepted, including a skipped suite or a passing run of the wrong file |
| "Run tests" or "write tests for the above" as a step | No behaviour named, no seam, no assertion; whatever gets written is unrelated to the requirement |
| Dependencies not stated | The consumer is built first and has nothing to call |
| Blanket "all tasks are parallel" | The undeclared dependency becomes a merge conflict or a red build in someone else's workspace |
| Parallel consumers of an unfrozen contract | Both sides land, disagree, and one is rewritten |
| No non-goals | Every adjacent good idea is arguably in scope; the plan grows and the request stays unfinished |
| No rollback point, or "revert the commit" over a forward-only migration | Discovered mid-incident, when there is no time to work it out |
| No assumptions recorded | The plan's premises are invisible until one is wrong, and then the blast radius is unknown |
| Placeholder text (TBD, "appropriate error handling", "similar to step N") | The decision lands on the executor at the moment they have the least context |
| A step that consumes a signature no step produces | Integration fails on a name, and nobody can tell which side is wrong |
| Mismatched names between produces and consumes | Same, but later, and it looks like a bug in working code |
| A step spanning two subsystems with no reason given | Cannot be partially approved, and a failure cannot be localised |
| Scope the request never asked for | Unreviewed work, a bigger diff, and risk nobody signed off |
| Riskiest unknown scheduled late | Everything before it rests on a guess and is redone if the guess was wrong |
| Definition of done that cannot be judged | The plan completes by agreement rather than by evidence |
| Plan file overwrites one with unchecked steps | Another session's work state is destroyed and is not recoverable |
| Plan restates the test cycle or the design argument | Steps get skimmed along with the prose |

## Checking a parallelism claim

Take the claim and try to break it with the code, not with the plan:

1. Does either step change a file the other reads? Shared config, a lockfile,
   a generated artefact, the schema.
2. Does either consume something the other produces? Follow the *produces*
   blocks, not the step titles.
3. Do both consume something that does not exist yet? Then they are both
   blocked on a freeze step that the plan may not contain.
4. Does either change a generated artefact's input? Every consumer of the
   output depends on it, including consumers outside the plan.
5. Would running them concurrently make one's acceptance command fail through
   no fault of its own? Then the acceptance is not runnable in parallel even if
   the edits are.

A claim that survives all five is a real claim. Most do not survive (2).

## Checking an acceptance line

Three questions, in order:

1. **Does the command exist?** Look it up in the Makefile, `package.json`,
   `pyproject.toml`, or the CI workflow. A plausible-looking command that is
   not defined is worse than none, because it will be tried.
2. **Does it exercise the step's behaviour?** A full-suite run proves the step
   broke nothing; it does not prove the step did anything. A step whose only
   acceptance is the full suite has no acceptance.
3. **Is the expected output falsifiable?** "Passes" for a command that also
   passes when the step is not done — a typecheck on a workspace the step does
   not touch, a suite with no test for the new behaviour — accepts an empty
   step.

## Checking coverage in both directions

Two sweeps, and both find different things.

**Requirements → steps.** For each requirement, name the step that implements
it. An unmatched requirement means the plan can be fully executed and still
fail acceptance. This is the single most valuable check in a plan review, and
the one most often skipped because the plan reads complete.

**Steps → requirements.** For each step, name the requirement it serves. An
unmatched step is either scope creep or a prerequisite nobody wrote down; both
are worth knowing, and they are handled differently.

Report the first sweep's misses under a `## Missing` heading. They are not
findings against a line, so they have nowhere else to go and otherwise get
lost among the per-step findings.

## Findings that are not defects

Keep these separate from the verdict, clearly labelled, so they do not inflate
the objection count:

- Code the plan touches that is wrong but works. Record it; do not make it a
  step.
- Formatting, ordering and wording preferences about the document.
- Alternative approaches you would have chosen. If the plan's approach works,
  the time to argue it was before the plan; raise it only if the alternative
  removes a defect.
- Things that are missing but deliberately out of scope, if the non-goals say
  so. Non-goals are answers, not gaps.

A review that mixes these with real defects gets read as a matter of taste, and
the real defects are discounted along with them.

## Name the defects before rewriting

When asked to review a plan, the temptation is to produce the good plan
instead. Resist it for one pass.

A silently repaired plan teaches its author nothing, hides how wrong the
original was, and removes the chance to disagree with the repair. The author
may know something the review does not — that a service is being created in
another branch, that a constraint was lifted.

So: findings first, with the failure each one causes. Then, if a rewrite is
wanted, produce it as a separate artefact and say which findings it addresses.

<!-- sources: obra-writing-plans, addy-planning, copilot-plan, obra-executing -->
