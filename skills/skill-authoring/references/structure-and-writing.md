# Structure, voice and bundling

How to shape a body that gets read, and what to leave out of it.

## Contents

- Section skeleton
- Naming
- Budgets, and what to do at the limit
- Write only what the model lacks
- Degrees of freedom
- Match the form of the guidance to the failure
- Progressive disclosure patterns
- Splitting references, and the index pattern
- Workflow checklists and feedback loops
- Templates, examples and conditional workflows
- Rationalisation tables and red flags
- Guessing points
- Anti-patterns
- When a bundled script earns its place
- Script rules

## Section skeleton

A body that agents navigate well has the same shape in the same order. Omit a
section that has no content; do not reorder them.

| Section | Holds | Omit when |
|---|---|---|
| `## Scope` | What is covered, and an explicit list of what is not | Never — the negative list is what stops the skill inventing |
| `## Read first` | The one file that must be read at the start of every task | There is no such file |
| `## Core rules` | Invariants, one line each with its reason | The skill has no invariants, only a procedure |
| `## Workflows` | A checklist per task shape, each ending in a named gate | The skill is pure reference |
| `## Topic router` | A table of topic, read-when condition, file | Nothing is bundled |
| `## Output format` | The exact shape of a report or artifact | The skill produces no structured output |
| `## Environment` | Required binaries, packages, platform limits | Nothing external is needed |

Two things this skeleton deliberately excludes. There is no duplicate "when to
use" section: the description routes to the skill, while `## Scope` retains
the detailed applicability and exclusions needed after loading. And there is
no narrative — "in one session we found that..." is a story about one
occasion, not a reusable technique.

## Naming

The name says what the skill *does*. Beyond that, two conventions coexist and
both are acceptable:

- Gerund or verb-first for task and process skills: `creating-skills`,
  `analyzing-spreadsheets`, `root-cause-tracing`. Active, and it names the
  action the agent is taking.
- Domain noun for ecosystem and platform skills: `postgres`, `react`, `apple`.
  The domain *is* the trigger, and a verb adds nothing.

Avoid: vague names (`helper`, `utils`, `tools`), over-general ones (`documents`,
`data`, `files`), vendor reserved words, and — worst — a naming pattern that
differs from the rest of the collection it ships in.

## Budgets, and what to do at the limit

| File | Target | Hard limit |
|---|---|---|
| `SKILL.md` body | 150–400 lines | 500 lines |
| A reference file | under 400 lines | 600 lines |
| A reference file needing `## Contents` | over 100 lines | — |

Word counts scale with load frequency: a skill that loads in every session
should be under a couple of hundred words, and `wc -w` is the check.

At the limit, the failure mode is deleting the wrong thing. The parts that
survive a length cut must be the project-specific invariants and the gotchas —
the content that only this skill has. What moves out is bulk: catalogues,
schemas, API surfaces, per-variant detail. What gets deleted outright is
whatever the model already knew.

## Write only what the model lacks

The context window is a shared resource. Challenge every paragraph: does the
model already know this, and does this paragraph justify its tokens?

Concise, roughly 50 tokens:

````markdown
## Extract PDF text

Use pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

Bloated, roughly 150 tokens for the same information: a paragraph explaining
what PDF files are, that libraries exist, that several libraries exist, that
this one is recommended because it is easy to use, and that it must be installed
with a package manager first.

What is worth writing, in order of value: the silent failure, the soft
deprecation that still compiles, the version difference, the project's own
invariant, the counter-intuitive fact. Teach the failure, not the API.

## Degrees of freedom

Match specificity to how fragile the task is.

| Freedom | Form | Use when |
|---|---|---|
| High | Prose heuristics | Several approaches are valid and context decides |
| Medium | A template or pseudocode with parameters | A preferred pattern exists, variation is acceptable |
| Low | An exact command, marked "do not change the flags" | The operation is fragile, order matters, consistency is critical |

The picture: a robot on a narrow bridge with cliffs on both sides needs exact
guardrails; the same robot in an open field needs a direction and the freedom to
find its own route. Over-constraining the open field wastes the model's
judgement; under-constraining the bridge is a failed migration.

## Match the form of the guidance to the failure

Classify the baseline failure *before* choosing wording. The form that fixes one
class measurably backfires on another.

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Knows the rule, breaks it under pressure | Prohibition, plus a rationalisation table and a red-flag list | Soft guidance: "prefer", "consider" |
| Complies, but the output has the wrong shape — bloated, verdict buried, spec restated | A positive recipe or contract: state what the output *is*, its parts, in order | A prohibition list: "don't restate", "never narrate" |
| Omits a required element from something it already produces | A required slot in the template it fills in | Prose reminders near the template |
| Behaviour should depend on a condition | A conditional keyed to an observable predicate: "if the brief exists, reference it" | An unconditional rule plus exemption clauses |

Why prohibitions backfire on shaping problems: under a competing incentive the
agent negotiates with "don't X". In head-to-head wording tests on
dispatch-prompt guidance, the prohibition arm produced clearly more of the
unwanted content than the recipe arm, and trended worse than the no-guidance
control. A recipe leaves nothing to negotiate — the output matches the stated
shape or it does not.

Two rules for whichever form is chosen:

- **No nuance clauses.** "Don't X unless it matters" reopens the negotiation;
  appending one nuance clause to a winning recipe degraded it from consistent to
  noisy in the same tests. Express a real exception as its own conditional on an
  observable predicate.
- **Exemption clauses do not scope.** "This limit does not apply to code blocks"
  still suppresses code blocks. If part of the output must be exempt,
  restructure so the rule cannot reach it.

## Progressive disclosure patterns

Three patterns cover almost every skill.

**High-level guide with references.** The body holds the quick start and points
at bundled files for depth. Best when there is one main path and several
occasional needs.

**Organisation by variant.** One reference per framework, platform, cloud or
domain, with the selection logic in the body. A request about one variant reads
one file, so the other variants cost nothing. Best when the axis of variation is
obvious to the reader.

**Conditional detail.** Basic content inline, advanced content behind a
condition: simple edits here, tracked changes in one file, the underlying format
in another. Best when the advanced path is rare but heavy.

## Splitting references, and the index pattern

Split by topic or variant, not by size. A file created purely because the body
got long has no read-when condition, and a file with no read-when condition is
never opened.

Every reference gets an entry in the router with an *observable* trigger. "Read
when working on advanced topics" is not observable — the agent cannot tell
whether its task is advanced. "Read before changing anything under
`src/registry/`" is.

Past roughly ten reference files, add an index file that the router points at
first. A working shape for that index: a short "start here" list of ordered
reading paths for the two or three common task types, then one or two tables of
file and open-when, then a reading strategy paragraph — open one variant file at
a time, prefer the built-in abstraction, check the version file before using a
new API. The index replaces a router that has grown too big to scan, and it is
the one legitimate exception to a flat router, because it is still exactly one
level from the body.

## Workflow checklists and feedback loops

For a multi-step task, give a checklist the agent can copy and tick off. It
prevents silent step-skipping and makes progress visible.

Every workflow ends in a **gate**: a named condition that must hold before the
work counts as done. A gate is a command with an expected result, or a check
whose outcome is observable. "Make sure the code is good" is not a gate.

The most valuable gate shape is a loop: run the validator, read the error, fix,
run again, and only proceed when it passes. This works without any code — the
"validator" can be a checklist in a reference file that the agent compares the
draft against.

## Templates, examples and conditional workflows

- **Template.** Supply the output structure. Match the strictness to the need:
  "use exactly this template" where the format is contractual, "here is a
  sensible default, adapt it" where judgement helps.
- **Examples.** Where quality depends on style rather than rules, two or three
  input-output pairs convey more than any description. Commit message formats,
  review comment tone, report phrasing.
- **Conditional workflow.** Where the procedure forks, state the decision first
  and give each branch its own steps. When the branches get long, each becomes
  its own reference file and the body keeps only the decision.

## Rationalisation tables and red flags

For discipline skills only — where the agent knows the rule and skips it anyway.
Both artifacts come out of baseline observation, not imagination: record the
excuses verbatim while watching the failure, then answer each one.

```markdown
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | A test written after passes immediately and proves nothing. |
```

Then a red-flag list of the phrases that signal the agent is mid-rationalisation,
so it can catch itself. Close loopholes explicitly: "delete it, start over" plus
"do not keep it as reference, do not adapt it, do not look at it" — because each
of those is a workaround somebody actually took.

State once, early, that violating the letter of a rule violates its spirit. That
one sentence closes an entire class of "I'm following the spirit" arguments.

## Guessing points

Before calling a draft finished, read it looking for the places where it forces
the agent to invent something: a path that is never given, a threshold that is
never stated, a naming convention that is implied and never written, a "the
usual way" with no referent.

Each one is a defect, and each has the same fix: supply the fact, or supply the
command that retrieves the fact. Where the fact genuinely cannot be known ahead
of time, say so and name the command that discovers it — a skill that says
"fetch the component's documentation with this command, never recall it from
memory" is complete; one that assumes the API is remembered is not.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Narrative case study | Describes one occasion; not reusable |
| The same example in five languages | Five mediocre examples instead of one good one, and five things to maintain |
| Fill-in-the-blank template instead of a real example | Nothing to pattern-match against |
| Generic labels — `step1`, `helper2`, `pattern4` | Labels should carry meaning |
| Diagram source in a graph language | Cannot be read or copied; a table or ASCII does the job |
| Code inside a flowchart node | Not copyable, hard to read |
| A menu of libraries | Hands the decision back; give one default and one escape hatch |
| Capitalised ALWAYS and NEVER throughout | Signals a missing reason; a model that knows why handles the unanticipated case |
| Time-anchored instructions | The agent cannot tell how old the file in front of it is; use a collapsed old-patterns block |
| Mixed synonyms for one concept | Breaks the pattern matching the instructions rely on |
| Backslash paths | Fail on Unix hosts, and the skill cannot know which host it is on |
| Unqualified MCP tool names | Fail to resolve when several servers are connected; write `Server:tool` |
| README, changelog or install guide in the skill directory | Written for humans; the agent has to read past it |
| A reference file nothing points at | Dead weight that still ships |

## When a bundled script earns its place

The signal is empirical, not aesthetic: read the transcripts of the evaluation
runs. If every run independently wrote the same helper — the same document
builder, the same chart generator, the same parser — that code belongs in
`scripts/`, written once.

Beyond removing repeated work, a pre-written script is more reliable than
generated code, spends no tokens on its own source, and produces consistent
output across runs.

Reasons that are *not* sufficient: the task involves code; a script would be
tidier; the author enjoys writing scripts. A bundled script is permanent
maintenance, and an unused one is worse than none.

Use the plan-validate-execute shape for batch or destructive work: the agent
writes a structured plan file, a script validates the plan and reports specific
errors, and only then does the execution step run. It catches the error before
the damage, and the validation is machine-checkable rather than a judgement.

## Script rules

- **Self-contained**, with dependencies declared inline where the language
  supports it, so it runs without a separate setup step.
- **Solve, do not defer.** Handle the missing file, the bad permission, the
  absent dependency, and emit a message that names the fix. `Field 'x' not
  found. Available: a, b, c` lets the agent recover; a raw traceback makes it
  guess.
- **No unexplained constant.** Every threshold, timeout and retry count carries
  a comment saying why that value. If the author cannot justify it, the agent
  certainly cannot.
- **Labelled in the body** as **Run** (execute it) or as **See** (read it as
  reference). Execution is the default and the cheaper one; reading is for
  algorithms the agent has to adapt.
- **Referenced at least once** from the body. A script the body never mentions
  does not exist.
- **No host runtime dependency.** Relative paths, no provider template
  variables.

<!-- sources: anthropic-best-practices, obra-writing-skills, anthropic-skill-creator, getsentry-skill-writer, grafana-skill-authoring, mgechev-skill-creator, openai-aspnet-core, agentskills-spec -->
