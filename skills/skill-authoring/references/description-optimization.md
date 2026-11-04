# Writing and optimising a description

The description is the always-loaded text an agent selects a skill on. It is
not a capability catalogue or a substitute for the body: it says what the skill
is about and when to read it.

## Contents

- Two layers
- Why the first sentence must stand alone
- Voice, length and ordering
- Adjacent scopes
- Undertriggering
- Building a trigger query set
- Why near-miss negatives are the only useful negatives
- Train and held-out split
- Running the loop
- What triggering does not fix
- Worked before and after

## Two layers

Use the same shape for knowledge and workflow skills:

```
<What + domain + key technology>. Use when <3–6 concrete triggers>[, including <easily skipped case>]. [Not for <measured near miss>.]
```

- **First sentence — what.** A third-person task verb, the domain and the
  identifying technology or artifact: "Python", "Rust", "AWS", "PDF files",
  "Agent Skills". It must make sense on its own (next section).
- **`Use when` — when.** Concrete situations in which the skill should be
  read: the user's natural phrasings, file names and extensions
  (`pyproject.toml`, `*.tf`, `Dockerfile`), error symptoms, task situations.
  Describe when to read, never what happens after reading.
- **`including …` / `even for …` — optional.** One concrete case the model
  would think it can handle without the skill: a one-line change, a throwaway
  script, a question that looks simple. Only skill-specific cases; the same
  boilerplate on every skill is noise.
- **`Not for …` — optional.** Only for a near miss that routing evaluations
  actually produced (see Adjacent scopes).

Never summarise the workflow. When a description lists steps, agents follow
the summary and skip the body that holds the real procedure (the failure
documented in obra's writing-skills). Capability lists and version lists fail
the same way: they spend the shared budget on text that does not help select.
Detailed coverage and exclusions belong in `## Scope`.

## Why the first sentence must stand alone

Hosts do not all show the whole description:

- **omp** (oh-my-pi 18.16.0) renders a description of 100 characters or less
  unchanged. A longer one is replaced by a preview: the first sentence, if it
  ends with a full stop, exclamation mark or question mark followed by a space
  inside the first 99 characters and is at least 40 characters long;
  otherwise a word-boundary cut with an ellipsis. A fast model later
  compresses the full description into a one-line routing hint (a 12-word
  target, at most 160 characters), cached in `skill-descriptions.db` and used
  by later sessions instead of the original.
- **Claude Code** cuts each entry at 1,536 characters and, when the whole
  listing exceeds about 1% of the context window, drops entire descriptions of
  the least-invoked skills.
- **Codex** spends at most 2% of the context window on the listing and
  shortens descriptions first.

So the first sentence carries the domain and the key nouns, and it must not
break early. `Node.js` and `.NET` are safe (no space after the dot), but
`e.g.`, `i.e.` and `vs.` end the sentence on omp; keep them out of the first
sentence. HyperSkills enforces a 40–99 character first sentence for exactly
this reason.

## Voice, length and ordering

- **Third person.** Use a task verb such as "Writes" or "Reviews", not
  "I can help" or "You can".
- **Front-load.** Domain and identifying nouns in the first sentence, the most
  frequent trigger first in `Use when`. Tails get cut.
- **Length.** HyperSkills policy: first sentence 40–99 characters, whole
  description at most 400 characters. The Agent Skills specification allows
  1,024. Neither is a target; do not pad. Every installed skill spends the
  shared listing budget.
- **No capitalised emphasis.** CRITICAL, MUST, ALWAYS, NEVER and IMPORTANT in a
  description make recent Claude models overtrigger (see Undertriggering).
- **No XML tags**, in either the name or the description. Anthropic's platform
  rejects them (the open specification does not forbid them); leaving them out
  keeps the skill loadable on every host.

## Adjacent scopes

Disambiguate neighbouring skills with precise nouns first: "native Android" and
"React Native", "self-managed PostgreSQL" and "SQLite", "Terraform" and
"Bicep". A precise noun separates the scopes without telling the model to
stay away.

Add `Not for …` only for a near miss that routing evaluations actually
produced, and keep it short. A speculative exclusion list pushes the model
further toward not loading the skill, which is the more common failure. The
full negative boundary stays in `## Scope`, where it acts after loading.

## Undertriggering

Claude tends to undertrigger skills: it skips them when they would help.
Anthropic's skill-creator recommends making descriptions "a little bit pushy",
and notes that simple one-step requests may not trigger a skill however good
the description is, because the model consults skills only for work it cannot
easily do alone.

Push with situations, not tone. Anthropic's Claude prompting guide reports that
Opus 4.5 and 4.6 respond strongly to the system prompt and overtrigger on
aggressive wording such as "CRITICAL: You MUST use this tool when…"; plain "Use
this tool when…" is the fix. In a description that means a concrete
`including …` case — "including one-line config edits" — rather than capitals.

Separate two failures before rewording anything:

| Failure | Observation | Lever |
|---|---|---|
| Selection | The agent checks the skill list and picks the wrong skill, or none fits | The description: nouns, triggers, a measured `Not for` |
| Activation | The agent never checks the list and starts working | Host or context-file rules that force a skill check before acting |

A sandboxed Claude Code evaluation (Scott Spence, Sonnet 4.5, 22 prompts run
twice) found activation, not selection, was the failure: every time the model
invoked a skill it picked the right one; without a hook only about 50–55% of
prompts activated one, and a `UserPromptSubmit` hook forcing an explicit
per-skill yes/no check reached 22/22 in both runs. On a harder set mixing in
prompts that need no skill, the forced check scored 75% overall with no false
positives. A stronger description does not fix a model that never looks.

Use substantive, realistic requests in the evaluation, inspect the actual
selection, and replace weak wording with the nouns and situations the failures
reveal; do not accumulate keywords after each miss.

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
   words over adding clauses; keep the first sentence self-contained and the
   whole description within the repository limit.
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
# Before — vague task, first person, no triggers
description: I can help you with release notes.
```

```yaml
# After — self-contained first sentence, then concrete triggers
description: Writes release notes and changelog entries from merged pull requests and commits. Use when preparing a release, tagging a version, editing CHANGELOG.md, or summarising what changed since the last tag, including a one-line changelog entry.
```

The first sentence (81 characters) still identifies the skill when a host shows
nothing else. The triggers are situations a user is in — a release, a tag, a
file name, a question — not a writing procedure. The `including` case names the
request most likely to be handled without the skill. There is no `Not for`,
because no near miss has been measured yet; adjacent jobs are separated in
`## Scope` and tested with near-miss queries.

<!-- sources: anthropic-skill-creator, obra-writing-skills, anthropic-best-practices, agentskills-spec, codex-skills-docs, claude-code-skills-docs, grafana-skill-authoring, claude-prompting-best-practices, scottspence-skill-activation, oh-my-pi-skill-descriptions -->
