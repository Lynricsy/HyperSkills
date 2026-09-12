# Agent Skills specification reference

Verified against: Agent Skills specification as published at agentskills.io.

## Contents

- Directory layout
- Frontmatter fields and exact constraints
- The `name` field
- The `description` field
- `license`, `compatibility`, `metadata`, `allowed-tools`
- Body content
- Progressive disclosure budgets
- File references
- Validation
- Lenient parsing, and what breaks in practice

## Directory layout

```
skill-name/
├── SKILL.md          # required: frontmatter + instructions
├── scripts/          # optional: executable code
├── references/       # optional: documentation read on demand
├── assets/           # optional: templates and other output resources
└── ...               # any other file the skill needs
```

Only `SKILL.md` is required. The three optional directories are conventions, not
enforced names, but every host and installer documents them, so a different name
costs recognisability for nothing.

The three have different intents, and mixing them wastes context:

| Directory | Intent | Consumed by |
|---|---|---|
| `scripts/` | Deterministic or repeatedly rewritten code | Executed; output enters context, the source need not |
| `references/` | Documentation the agent reads while working | Read into context on demand |
| `assets/` | Files that end up in the produced artifact — templates, fonts, boilerplate | Copied or modified, never read for instruction |

A file placed in `references/` that only ever gets copied into output is an
asset, and an agent will read it once to find out.

## Frontmatter fields and exact constraints

`SKILL.md` opens with a YAML mapping fenced by `---` lines. Six fields are
defined; nothing else is portable.

| Field | Required | Constraint |
|---|---|---|
| `name` | yes | 1–64 characters; lowercase `a-z`, digits `0-9` and `-` only; no leading or trailing `-`; no `--`; must equal the parent directory name; no XML tags; no vendor reserved words |
| `description` | yes | Specification: 1–1024 characters, non-empty; describes what the skill does and when to use it; no XML tags. HyperSkills applies the tighter local policy below |
| `license` | no | Licence name, or the name of a bundled licence file. Keep it short |
| `compatibility` | no | 1–500 characters; environment requirements — intended product, system packages, network access. Most skills do not need it |
| `metadata` | no | A map from string keys to string values. Host-specific extras live here; pick key names unlikely to collide |
| `allowed-tools` | no | Space-separated pre-approved tool list, for example `Bash(git:*) Bash(jq:*) Read`. Experimental; support varies by host |

Minimal valid frontmatter:

```yaml
---
name: pdf-processing
description: Extracts text and tables from PDF files for document processing.
---
```

## The `name` field

The five construction rules exist because the name is an identifier in file
paths, command names and namespaces:

| Invalid | Why |
|---|---|
| `PDF-Processing` | Uppercase not allowed |
| `-pdf` / `pdf-` | Leading or trailing hyphen |
| `pdf--processing` | Consecutive hyphens |
| `pdf_processing` | Underscore is not in the allowed set |
| `pdf-processing` in a directory named `pdf/` | Must equal the parent directory name |

The directory rule is the one that bites hardest: hosts derive a skill's
identity from the directory containing `SKILL.md`, so a mismatch produces a
skill that either loads under a name nobody types or is skipped. Lenient hosts
warn and load it anyway; strict validators fail. Neither outcome is worth the
risk.

Vendor reserved words are rejected because a skill named after the model
provider cannot be distinguished from a first-party one. Names such as
`anthropic-helper` are invalid for that reason.

## The `description` field

The description is the always-loaded routing text. Use it to select the skill,
not to reproduce its capability catalogue or procedure.

- Write one English task-and-key-noun sentence in the third person, usually
  8–16 words: name the task and its identifying technology or artifact.
- HyperSkills requires 1–160 characters, not all whitespace. There is no
  padding minimum; a clear shorter sentence is preferable.
- Put detailed applicability and exclusions in the body's `## Scope`. Do not
  require a "Do not use for" clause; use a brief qualifier only for real
  ambiguity between adjacent scopes.
- Do not enumerate capabilities, versions or steps. A task and its object can
  express what and when without a second sentence.

The specification's 1,024-character ceiling remains a format constraint, not
the repository's authoring budget or a target. HyperSkills' source of truth for
the tighter policy is its repository standard; this reference explains that
policy without changing the upstream specification.

## `license`, `compatibility`, `metadata`, `allowed-tools`

- `license` accepts a short name (`Apache-2.0`) or a pointer to a bundled file
  (`Proprietary. LICENSE.txt has complete terms`). A skill that vendors material
  from elsewhere needs both this field and the bundled file.
- `compatibility` is for genuine environment requirements — a required binary, a
  Python version, network access. It is not a place for a second description.
- `metadata` values are strings. A nested map or a list is out of spec; hosts
  differ on whether they coerce it, ignore the field, or drop the skill.
- `allowed-tools` is experimental, and support is uneven: most hosts honour it,
  at least two ignore it. A skill that only works when its tools are
  pre-approved is a skill that breaks on those hosts. Treat the field as an
  optimisation, never as a precondition.

## Body content

The Markdown after the frontmatter has no required format. What matters is that
the host loads the *whole* body once the skill activates, so its length is a
direct cost on every use.

Sections that reliably earn their place: step-by-step instructions, input and
output examples, edge cases, and a routing table pointing at the bundled files.

## Progressive disclosure budgets

Three tiers, loaded at three different times:

| Tier | Content | Loaded | Budget |
|---|---|---|---|
| 1 | `name` + `description` | At startup, for every installed skill | ~100 tokens each |
| 2 | `SKILL.md` body | When the skill activates | under 500 lines, ~5,000 tokens |
| 3 | `references/`, `scripts/`, `assets/` | On demand, per file | Effectively unbounded |

Tier 1 is a shared budget: every skill on the machine pays into it, which is why
a bloated description harms skills other than its own.

Tier 3 is unbounded only because it is not loaded. A script that gets executed
costs its output; a reference that gets read costs its whole length. Bundling a
1,000-line reference is free until the agent opens it, and then it is not.

## File references

Reference bundled files by relative path from the skill root, and keep every
reference one level deep from `SKILL.md`.

The depth rule has a mechanical cause. An agent that reaches a file directly
from `SKILL.md` reads it. An agent that reaches a file *through* another
reference tends to preview it — a head-of-file read — and then acts on partial
information without knowing it is partial. The fix is never a stronger
instruction; it is promoting the deep file to a sibling and pointing at it from
`SKILL.md`.

Two corollaries:

- A reference file over 100 lines opens with a `## Contents` list, so a preview
  still reveals the full scope of what the file holds.
- Reference files do not link to each other. Cross-links recreate the chain that
  the depth rule exists to prevent.

Paths use forward slashes everywhere, including on Windows. Backslash paths fail
on Unix hosts, and the agent has no way to know which one it is running on.

## Validation

The specification ships a reference validator:

```bash
npx skills-ref validate ./my-skill
```

It checks frontmatter validity and the naming conventions. It does not check
line budgets, reference depth or content quality — add those to whatever check
the repository already runs, because they are the failures that survive a
passing validator.

## Lenient parsing, and what breaks in practice

Host implementations are told to be forgiving, which means a broken skill often
loads in a degraded state rather than reporting an error:

| Defect | Typical host behaviour |
|---|---|
| `name` differs from the directory name | Warn, load anyway |
| `name` longer than 64 characters | Warn, load anyway |
| Missing or empty `description` | Skip the skill, log it |
| Unparseable YAML | Skip the skill, log it |

The single most common real-world breakage is an unquoted `description` value
containing a colon, which turns the line into a nested mapping and makes the
whole block unparseable. Quote the value, or use a block scalar.

When two skills share a name, the near-universal rule is that project scope
overrides user scope. One major host inverts part of this — enterprise beats
personal beats project — so a skill that relies on shadowing is not portable.

<!-- sources: agentskills-spec, anthropic-best-practices, anthropic-skill-creator, vercel-skills-cli, claude-code-skills-docs -->
