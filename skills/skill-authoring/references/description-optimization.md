# Writing and optimising a description

The description is the always-loaded routing sentence, not a capability
catalogue or a substitute for the body. Name the task and the key technology or
artifact so the agent can decide whether to load the skill.

## Contents

- One routing sentence
- Voice, length and ordering
- Adjacent scopes
- Undertriggering
- Building a trigger query set
- Why near-miss negatives are the only useful negatives
- Train and held-out split
- Running the loop
- What triggering does not fix
- Worked before and after

## One routing sentence

Use the same shape for knowledge and workflow skills:

```
<Third-person task verb> <task or artifact> <key technology or context>.
```

Usually 8–16 words are enough. Select the nouns that distinguish the job;
do not enumerate every supported API, version, symptom or subtask. The task
and its object express what the skill does and when it is relevant without
a separate "Use when" sentence.

Keep procedures in the body. The workflow-shortcut failure documented by
obra-writing-skills supports omitting procedural summaries; it does not
justify capability lists for other skills. Detailed coverage and exclusions
belong in `## Scope`, whatever shape the body takes.

## Voice, length and ordering

- **Third person.** Use a task verb such as "Writes" or "Reviews", not
  "I can help" or "You can".
- **Front-load.** Put the task and identifying nouns first. Hosts can shorten
  listings, and every installed skill shares the always-loaded context budget.
- **Length.** HyperSkills requires one English sentence of 1–160 characters,
  not all whitespace, usually 8–16 words. This is a repository policy, not the
  Agent Skills specification's 1,024-character ceiling. Neither is a target;
  do not pad a clear shorter sentence.
- **No XML tags**, in either the name or the description. They are rejected.

## Adjacent scopes

Keep detailed exclusions in `## Scope`; a "Do not use for" sentence is not
required in the description. If realistic near-miss queries reveal genuine
ambiguity, replace a broad noun with a precise one or add a brief qualifier,
such as "native Android" or "self-managed PostgreSQL". Stay within the single
routing sentence rather than appending a refusal list.

## Undertriggering

Treat undertriggering as an observation to measure, not a reason to make every
description longer. A missed request can reflect imprecise routing nouns,
competing skills, or a host that chooses not to consult a skill for trivial
work. Inspect the actual selection before changing the sentence.

Use substantive, realistic requests in the evaluation. Replace weak wording
with the task or artifact the failures reveal; do not accumulate keywords or
marketing claims after each miss.

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
2. Read the editing-split failures. A miss suggests checking the task and nouns;
   a hit on a near-miss suggests checking whether the stated scope is too broad.
3. Propose a short candidate addressing that failure. Prefer replacing vague
   words over adding clauses; retain one sentence within the repository limit.
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
# Before — vague task, first person
description: I can help you with release notes.
```

```yaml
# After — one task-and-artifact routing sentence
description: Writes release notes and changelog entries from merged pull requests and commits.
```

The replacement names the task, the two artifacts and their inputs in one
sentence. It does not promise a writing procedure or list every release-related
request. Put detailed coverage and adjacent exclusions in `## Scope`, and use
near-miss queries to measure whether the concise routing sentence distinguishes
those jobs.

<!-- sources: anthropic-skill-creator, obra-writing-skills, anthropic-best-practices, agentskills-spec, codex-skills-docs, claude-code-skills-docs, grafana-skill-authoring -->
