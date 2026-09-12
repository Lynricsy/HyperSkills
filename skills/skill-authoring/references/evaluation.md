# Evaluating a skill

A skill is a claim: "with this text, the agent does better". The claim is either
measured or it is decoration.

## Contents

- Evaluation-driven development
- The evaluation file
- Writing an expectation
- The negative scenario
- Baseline and with-skill runs
- Grading
- Non-discriminating expectations
- Variance, and the LLM judge
- Multiple models
- The two-agent loop
- Observing navigation
- Iterating without overfitting
- Blind comparison
- Artifact schemas
- Pre-release checklist

## Evaluation-driven development

Five steps, in this order. The order is the point: it is what stops a skill from
documenting problems that never occurred.

1. **Identify gaps.** Run the agent on representative tasks with no skill.
   Record the specific failures — the wrong API, the invented convention, the
   missing project rule, the excuse it gave.
2. **Create evaluations.** Build at least three scenarios that test those gaps.
3. **Establish the baseline.** Measure the no-skill performance against those
   expectations, so the starting point is a number and not an impression.
4. **Write minimal instructions.** Just enough to close the recorded gaps.
5. **Iterate.** Re-run, compare against the baseline, refine.

The failure this prevents is the most common one in practice: a well-written
skill full of rules the model already followed, which measures identical to no
skill at all while consuming context in every session.

## The evaluation file

One scenario per entry. The shape that works across runners:

```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF and save it to output.txt",
  "files": ["evals/files/document.pdf"],
  "expected_behavior": [
    "Reads the PDF with an appropriate library or command-line tool",
    "Extracts text from every page without skipping any",
    "Writes the result to output.txt in readable form"
  ]
}
```

- `skills` names what should be loaded; an empty list marks a negative scenario.
- `query` is what a real user would type, with the texture of a real request.
- `files` are small fixtures, kept with the evaluations, not fetched at run time.
- `expected_behavior` items are observable, one claim each.

Fixtures stay small — a runner copies them for every scenario, every
configuration and every model, so a large fixture multiplies.

## Writing an expectation

An expectation is graded from a transcript, so it has to be decidable from one.

| Weak | Strong |
|---|---|
| "Handles the PDF correctly" | "Extracts text from every page without skipping any" |
| "Good output" | "Writes output.txt containing the string 'Invoice total'" |
| "Uses the skill" | "Applies the deprecation table: replaces the soft-deprecated call at line 12" |

Two traps:

- **An expectation a hallucination would satisfy.** "The output mentions John
  Smith" passes for a fabricated document. Pin it to something the fabrication
  would get wrong.
- **An expectation about the implementation.** "Reads reference file X" measures
  navigation, not outcome. It is a useful *diagnostic*, but it is not evidence
  the skill helped.

Where an expectation can be checked programmatically, check it with a script
rather than by eye. It is faster, it does not drift between runs, and it is
reusable next iteration.

Skills with subjective output — writing voice, visual design — are graded
qualitatively. Forcing assertions onto them produces expectations that measure
the wrong thing precisely.

## The negative scenario

At least one scenario must be a near miss that should *not* load the skill, with
an expectation that says so.

A negative that shares no vocabulary with the skill passes any description,
including a broken one, so it tests nothing. The useful negative is the adjacent
request the skill has to lose: for a skill about authoring skills, "write an MCP
server" or "write the README for this tool".

If the negative loads the skill, the fault is in the description's boundary, not
in the body.

## Baseline and with-skill runs

Launch both configurations for a scenario together, not the with-skill runs
first and the baselines later. Anything that changes between the two batches —
model routing, tool availability, a rate limit — becomes indistinguishable from
the skill's effect.

For a new skill, the baseline is no skill at all. For an improvement to an
existing skill, snapshot the current version first and make the snapshot the
baseline; otherwise the comparison is against a version nobody has.

Capture the per-run cost — tokens and wall-clock — at the moment the run
reports it. It is usually not persisted anywhere else, and it is what tells you
a skill that improved a pass rate by 5% tripled the tokens.

## Grading

Judge each expectation separately as met or unmet, and cite the transcript line
that decides it. An unmet expectation with no citation cannot be acted on; a met
one with no citation cannot be trusted.

Record, per run: the expectation text, the verdict, and the evidence. Aggregate
into a pass rate per configuration and a delta.

The pass condition for a skill is not a high pass rate. It is a **closed gap**:
at least one expectation that the baseline missed and the skill meets. A skill
with 100% in both configurations has proven only that the model was already
capable.

## Non-discriminating expectations

An expectation that passes in every configuration is non-discriminating. It is
still worth keeping as a regression guard, but it cannot justify any text in the
skill, and it must not be counted as evidence the skill works.

When most expectations are non-discriminating, the evaluations are testing the
model rather than the skill. Rewrite them against the recorded baseline
failures — the ones that actually happened.

## Variance, and the LLM judge

Both the runs and the grading are stochastic.

- A single run per configuration cannot separate a real effect from noise.
  Repeat, and report the spread alongside the mean.
- An expectation whose verdict swings between repeats is flaky. Either the
  expectation is ambiguous or the behaviour genuinely is unreliable; find out
  which before touching the skill.
- When a model grades quality on a scale, the score moves by a wide margin
  between runs on identical input — a swing of several points out of a hundred
  is normal, and a local score commonly lands lower in a different environment.
  Treat a single high score as noise; require the threshold to hold across
  several consecutive runs before shipping.

Variance is itself a signal. When guidance lands, repeats converge on the same
shape. Five different interpretations across five repeats means the wording is
not binding: tighten the form before adding words.

## Multiple models

A skill is an addition to a model, so its effect depends on the model. Test
every model the skill is meant for.

| Model class | Question to ask |
|---|---|
| Small and fast | Is there enough guidance? |
| Mid-range | Is it clear and efficient? |
| Large reasoning | Is it over-explaining what the model already handles? |

The tension is real: text that a strong model reads as noise can be the minimum
a small one needs. When one skill must serve both, keep the invariant list tight
and push the explanation into references, where the strong model can skip it.

## The two-agent loop

The most effective loop uses two agents in different roles.

One agent holds the author role: it sees the whole skill, the observations and
the history, and it proposes changes. A second, fresh agent does real work with
the skill loaded and nothing else — no briefing, no history, no explanation of
what the author intended.

The author agent cannot evaluate the skill, because it knows what the skill
meant to say. The working agent cannot improve it, because it only sees the
result. Keep the roles separate and the loop works:

1. Give the working agent a real task, not a test scenario.
2. Observe where it struggles, and what it never used.
3. Bring the specific observation back to the author agent — "it forgot to
   filter test accounts even though the skill mentions it" — not a general
   complaint.
4. Apply the change, and repeat on a similar task.

## Observing navigation

Watch the working agent's file access, not only its answer. Four signals, each
with a structural reading:

| Signal | What it means | Fix |
|---|---|---|
| Reads files in an unexpected order | The structure is not as intuitive as it looked | Reorder sections; move the thing it needed first, first |
| Never follows a reference | The read-when condition is not observable, or not prominent | Rewrite the condition against something the agent can check |
| Reads the same file repeatedly | That content belongs in the body | Promote it |
| Never opens a bundled file | Dead weight, or unsignalled | Delete it, or give it a real trigger |

Every one of these is a structure defect. Adding emphasis to text that was never
reached changes nothing.

## Iterating without overfitting

The loop runs on a handful of scenarios because that is what is affordable. The
skill will run on thousands. That gap is where iteration goes wrong.

- **Generalise from feedback.** A fiddly fix aimed at one scenario, or a rigid
  prohibition bolted on to force one outcome, buys the scenario and loses the
  population. When a problem is stubborn, try a different framing or a different
  recommended pattern rather than a harder rule.
- **Keep it lean.** Read the transcripts, not just the outputs. Text that makes
  the agent do unproductive work is a candidate for deletion, and deletion is a
  legitimate iteration.
- **Explain why.** Terse or frustrated feedback still has a reason behind it.
  Transmit the reason into the skill; capitalised absolutes are a sign the reason
  was not found.
- **Look for repeated work.** If several runs independently wrote the same
  helper, that is the signal to bundle a script.

## Blind comparison

For "is the new version actually better", give both outputs to an independent
agent without saying which is which, and have it judge quality; then analyse
*why* the winner won. It is more rigorous than a side-by-side read, and more
expensive. The measured expectations plus human review are usually enough.

## Artifact schemas

Runners differ, but the field names below are the ones the widely used tooling
expects. Matching them means existing viewers and aggregators work on the
output; inventing new ones means they do not.

Grading result, per run:

```json
{
  "expectations": [
    {"text": "...", "passed": true, "evidence": "Transcript step 3: ..."}
  ],
  "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67}
}
```

The three keys in `expectations` are `text`, `passed`, `evidence` — not `name`,
`met` or `details`.

Aggregate, across runs:

```json
{
  "run_summary": {
    "with_skill":    {"pass_rate": {"mean": 0.85, "stddev": 0.05}},
    "without_skill": {"pass_rate": {"mean": 0.35, "stddev": 0.08}},
    "delta":         {"pass_rate": "+0.50"}
  },
  "notes": [
    "Expectation 'Output is a PDF file' passes in both configurations — non-discriminating",
    "Scenario 3 swings 50% +/- 40% — flaky or model-dependent"
  ]
}
```

The `notes` array is where the analysis goes, and it is the part people skip.
Two things belong there every time: which expectations were non-discriminating,
and which scenarios had variance wide enough to distrust.

## Pre-release checklist

**Core quality**

- [ ] The description is one third-person task-and-key-noun routing sentence,
      usually 8–16 words, 1–160 characters and not all whitespace in HyperSkills
- [ ] Capability lists, procedures and detailed exclusions remain in the body,
      with scope boundaries in `## Scope`, not a mandatory negative sentence
- [ ] The body is under 500 lines
- [ ] Detail lives in separate files, one level deep
- [ ] No time-sensitive statement outside a collapsed old-patterns block
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] Progressive disclosure used, and each bundled file has a read-when trigger
- [ ] Workflows have clear steps and end in a gate

**Code and scripts**

- [ ] Scripts solve rather than defer
- [ ] Error handling is explicit and its messages name the fix
- [ ] No unexplained constant
- [ ] Required packages listed and verified available
- [ ] Scripts documented, and labelled Run or See
- [ ] Forward slashes everywhere
- [ ] Validation steps for anything destructive
- [ ] A feedback loop where output quality matters

**Testing**

- [ ] At least three evaluations exist, one of them a near-miss negative
- [ ] A no-skill baseline was measured, and at least one gap is closed
- [ ] Tested on every model class the skill targets
- [ ] Tested on real usage, not only the scenarios

<!-- sources: anthropic-best-practices, anthropic-skill-creator, obra-writing-skills, grafana-skill-authoring, hyperskills-self -->
