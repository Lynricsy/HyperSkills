# Writing and optimising a description

The description is the only text always in context and the only text a host
matches a request against. A skill with an excellent body and a weak description
is never used, and nothing reports the failure.

## Contents

- The two description types
- The formula for a capability skill
- The formula for a workflow skill
- Voice, length and ordering
- The negative boundary
- Undertriggering
- Building a trigger query set
- Why near-miss negatives are the only useful negatives
- Train and held-out split
- Running the loop
- What triggering does not fix
- Worked before and after

## The two description types

The one genuine disagreement between the authoritative sources, and it resolves
by asking what the skill's value actually *is*.

| Type | Description contains | Reason |
|---|---|---|
| Workflow skill — the value is an ordered procedure, especially one with branches or repeated stages | Triggering conditions only | A procedure summary in the description becomes the shortcut the agent takes *instead of* reading the body. Documented case: a description mentioning "code review between tasks" produced one review, while the body's flow required two. Removing the summary fixed it |
| Capability skill — the value is knowledge: gotchas, invariants, a reference surface, a review checklist | What it does, when to use it, trigger keywords | There is no procedure to short-circuit, and the extra specificity improves selection among competing skills |

Both types end with a negative boundary. Both are third person.

The deciding test is not whether the body contains a checklist — plenty of
knowledge skills do. It is this: **could an agent produce a plausible imitation
of the body's procedure from the description alone?** If yes, the description is
too procedural and has to come back to triggering conditions, because a
plausible imitation is exactly what gets executed instead of the real thing.

A coverage list — the topics the skill knows about — does not pass that test and
is safe in a capability description. An ordered summary — "detects the stack,
then audits, then reports" — does, and is not.

## The formula for a capability skill

```
<Third-person verb phrase: what it does, most important use first>.
<Use when ...: the situations, phrased as a user would recognise them>.
<Do not use for ...: the adjacent things it must lose to>.
```

Fill the middle clause with the concrete nouns a request contains — file
extensions, library and product names, error strings, command names, the
synonyms of the task. A host matches text; give it text to match.

## The formula for a workflow skill

```
Use when <situation>, <situation>, or <symptom>. Do not use for <adjacent thing>.
```

No verbs describing the procedure. No step counts. No "then" clauses.

## Voice, length and ordering

- **Third person.** The description is injected into a system prompt, where
  "I can help you..." reads as a different speaker. Selection degrades measurably.
- **Front-load.** Hosts shorten long listings and cut from the end — one caps
  the whole list at 2% of the context window, another truncates each entry at
  1,536 characters. The last sentence of a long description may never be seen,
  so the most important use case and the strongest keywords go first.
- **Length.** The ceiling is 1,024 characters. Aim for the shortest text that
  carries what, when, keywords and the boundary; do not pad to the limit.
- **No XML tags**, in either the name or the description. They are rejected.

## The negative boundary

The boundary is what resolves competition between adjacent skills, and it is the
clause authors skip most often. Without it the host has no basis to prefer a
neighbouring skill, so both trigger, or the wrong one does.

Write the boundary as the thing that should win instead, not as an abstraction:

```
Do not use for visual design decisions, Vue or Svelte, or React Native.
```

is decidable. "Do not use for unrelated tasks" is not.

## Undertriggering

Models under-select skills rather than over-select them, for a structural
reason: a skill is consulted only for tasks the model cannot obviously handle
alone. A one-step request — "read this PDF" — often will not trigger a matching
skill at all, because the model can just do it.

Two consequences:

1. A slightly pushy capability description is correct. Naming the situations
   explicitly, including cases where the user does not say the skill's own
   vocabulary, closes real misses.
2. Trivial queries are worthless as trigger tests. A test query must be
   substantive enough that consulting a skill is plainly the better route.

## Building a trigger query set

Twenty queries, 8–10 that should trigger and 8–10 that should not.

Make them look like real requests. Real requests carry file paths, job context,
column names, company names, URLs, a little backstory, sometimes lower case,
abbreviations, typos and casual speech. Abstract stubs test nothing.

Too abstract:

```
"Format this data"
"Extract text from PDF"
"Create a chart"
```

Realistic:

```
"ok so my boss just sent me this xlsx file (its in my downloads, called
something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column
showing profit margin as a percentage. revenue is in column C and costs are in
D i think"
```

For the should-trigger half, aim for coverage rather than volume: different
phrasings of the same intent, formal and casual, cases where the user never
names the file type or the skill's own vocabulary, a couple of uncommon uses,
and at least one case where this skill competes with another and should win.

## Why near-miss negatives are the only useful negatives

An obviously unrelated query passes every description, including a terrible one,
so it measures nothing. "Write a fibonacci function" as a negative for a PDF
skill is not a test.

A useful negative shares vocabulary or concepts with the skill and still needs
something else:

- an adjacent domain the skill must lose to
- phrasing where a naive keyword match would fire
- a request that touches what the skill does, in a context where another tool
  is the right answer

For a skill about authoring skills, the sharp negatives are "write an MCP
server", "turn this into a slash command", "write the README for this tool" —
all of them about authoring something for an agent, none of them an Agent Skill.

## Train and held-out split

Split the query set, roughly 60% for the editing loop and 40% held back. Edit
against the first part, score candidates on the second, and pick the winner by
the held-out score.

Without the split, the loop converges on wording fitted to the exact queries
used to write it, which is indistinguishable from improvement until the skill
meets a real request.

## Running the loop

1. Score the current description on the whole set, running each query several
   times. Triggering is stochastic; a single run cannot separate a better
   description from noise.
2. Read the failures. A miss on a should-trigger query names a missing keyword
   or situation; a hit on a near-miss names a boundary that is too wide.
3. Propose a candidate that addresses the specific failures. Do not rewrite from
   scratch — that discards what already worked.
4. Re-score on train and held-out. Keep the candidate with the better held-out
   rate, not the better train rate.
5. Stop after a few iterations, or when the held-out rate stops moving.
6. Report both rates for the old and the new description. "It reads better" is
   not a result.

Use the model that will actually run the skill. A description tuned on one model
is not guaranteed to transfer, and the point is the user's experience.

## What triggering does not fix

If the skill triggers and the work is still wrong, the description is not the
problem and editing it will not help. Two distinct failures with distinct fixes:

| Symptom | Fault | Fix |
|---|---|---|
| The skill is never loaded | Description | This file |
| The skill is loaded and half-read | Body length and reference structure | Budgets and reference depth |
| The skill is loaded, read, and ignored | Guidance form, or a rule the model disagrees with | Match the form to the failure |

## Worked before and after

```yaml
# Before — nothing to match, no boundary, first person
description: I can help you with release notes.
```

```yaml
# After — capability skill: what, when, keywords, boundary; key use first
description: Writes release notes and changelog entries from merged pull
  requests and commit history, grouping changes by user-visible impact and
  flagging breaking changes and migrations. Use when preparing a release,
  drafting or editing a CHANGELOG entry, summarising what shipped since a tag,
  or writing upgrade notes for a version bump. Do not use for commit messages,
  pull request descriptions, or marketing announcements.
```

What changed, and why each change is load-bearing: third person; the first
clause names the artifact so the most likely request matches on the first words;
`changelog`, `CHANGELOG`, `since a tag`, `breaking changes`, `upgrade notes` are
the terms real requests contain; the boundary names the three neighbours that
were previously stealing the request.

<!-- sources: anthropic-skill-creator, obra-writing-skills, anthropic-best-practices, agentskills-spec, codex-skills-docs, claude-code-skills-docs, grafana-skill-authoring -->
