---
name: skill-authoring
description: "Authors, reviews and evaluates Agent Skills and their SKILL.md files."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: meta
---

# skill-authoring

Paths below are relative to this skill's directory.

## Scope

Agent Skills as defined by the open specification at agentskills.io: a directory
containing `SKILL.md` with YAML frontmatter, optionally plus `references/`,
`scripts/` and `assets/`. Authoring, reviewing, evaluating, packaging and
licensing them, and organising a repository that holds several.

Not covered — do not answer from this skill:

- MCP servers, tools and resources — use the `mcp-server` skill. A skill is
  instructions an agent reads; an MCP server is a process it calls. Wanting
  both does not make them one artifact.
- Slash commands, subagent and agent definitions, output styles, hooks, prompt
  files, memory and rules files. These are host features that happen to live
  near skills; only the skill fields shared with them are in scope.
- Writing the domain content itself. This skill decides what belongs in a skill
  about PostgreSQL; it does not know PostgreSQL.
- Human-facing documentation — use the `technical-writing` skill. A skill
  directory holds no README, changelog or
  installation guide: those add clutter an agent has to read past.

## Read first

`references/spec-reference.md`, before writing or judging any frontmatter. The
field constraints are hard facts with exact limits, and a misremembered one
produces a skill that a host silently skips — the worst failure mode available,
because nothing reports it.

## Core rules

Violations of these are bugs, not preferences.

1. One skill covers one coherent job. A skill spanning two unrelated jobs
   triggers for neither, because the description cannot describe both without
   becoming vague.
2. `name` is 1–64 characters of lowercase letters, digits and single hyphens,
   never leading, trailing or doubled, never containing an XML tag or a vendor
   reserved word, and identical to its directory name. Hosts key a skill's
   identity to the directory holding `SKILL.md`.
3. Write the description as one English routing sentence in the third person:
   task plus key technology or artifact, usually 8–16 words. HyperSkills requires
   1–160 characters, not all whitespace; the specification allows up to 1,024.
   Neither limit is a target, and there is no padding minimum.
4. Put the task and identifying nouns first. Every installed skill spends the
   shared listing budget; hosts may shorten that listing.
5. Keep capability lists, versions and procedures out of the description.
   Detailed applicability and exclusions belong in `## Scope`. A separate
   "Do not use for" sentence is not required; add only a brief qualifier when
   adjacent scopes are genuinely ambiguous.
6. Only specification fields appear in frontmatter: `name`, `description`,
   `license`, `compatibility`, `metadata`, `allowed-tools`. Every other field
   belongs to one host, is ignored everywhere else, and — the real damage —
   convinces the author that something is handling activation when nothing is.
7. Write only what the model lacks. Cut explanations of the language, the
   framework, the package manager and the standard library; keep the edge cases,
   the silent failures, the project's own invariants. Every paragraph answers
   "is this worth its tokens".
8. Keep the body under 500 lines. Past that, move material into `references/`
   and leave a pointer — never shrink by deleting the project-specific parts,
   which are the only parts that were carrying weight.
9. Every reference file is one level deep from `SKILL.md`, is introduced there
   with an observable condition for reading it, and opens with a `## Contents`
   list once it passes 100 lines. A file reached through another reference gets
   previewed rather than read, and a file with no read-when condition never gets
   opened at all.
10. Match the degree of freedom to the fragility of the task: heuristics where
    several routes work, a parameterised template where one pattern is
    preferred, an exact command marked "do not change the flags" where the
    sequence is fragile and consistency matters.
11. Match the *form* of the guidance to the baseline failure. A prohibition plus
    a rationalisation table works only for "knows the rule, breaks it anyway";
    for output of the wrong shape write a positive recipe, for an omitted
    element add a required slot in the template, for state-dependent behaviour
    write a conditional keyed to something observable.
12. Give one default and one escape hatch, never a menu. `Use X. For <case> use
    Y instead.` A list of five interchangeable options hands the decision back.
13. Use one term per concept for the whole skill. Mixed synonyms break the
    pattern matching the instructions rely on.
14. No time-sensitive statements. Deprecated material goes in a collapsed
    `## Old patterns` block; the main line carries only the current way, because
    an agent cannot tell how old the file in front of it is.
15. Imperative mood, and explain why. Capitalised ALWAYS and NEVER are a signal
    that the reason is missing; a model that understands the reason handles the
    case the rule did not anticipate.
16. Refer to another skill by its name alone. Path-reference syntaxes that
    force a file into context spend the whole budget before it is needed, and a
    host-specific namespace prefix breaks the moment the skill is installed
    alone.
17. Nothing in the body may depend on one host's runtime: no template variables
    it substitutes, no dynamic shell injection, no forced file attachment.
    Call bundled scripts by relative path, and name MCP tools fully qualified
    as `Server:tool` so they resolve when several servers are connected.
18. Bundle a script only once transcripts show runs rewriting the same code.
    Then it solves rather than defers (actionable message naming the available
    options, not a raw traceback), carries no unexplained constant, declares
    its dependencies, and is labelled in `SKILL.md` as **Run** or as **See**.
19. Evaluations come before the body: at least three scenarios with observable
    expected behaviour, at least one near-miss negative, and a measured
    no-skill baseline. A rule the model already follows without the skill is
    dead weight; only a measured gap justifies text.
20. The contents match the stated intent, and the skill does nothing the user
    would be surprised by. Author no skill whose purpose is unauthorised access,
    exfiltration or deception.

## Workflows

### scope-and-draft

For a new skill. Do not start with the prose.

- [ ] Name the one job, and name what the skill will refuse to answer. Both go
      into `## Scope`; the refusal list is what stops the skill inventing.
- [ ] Run two or three representative tasks with no skill loaded and record the
      specific failures verbatim — wrong API, missing project rule, invented
      convention, rationalisation used. This is the gap inventory.
- [ ] Classify each failure by form before writing anything
      (`references/structure-and-writing.md`): discipline, wrong-shaped output,
      omitted element, or state-dependent. The classification picks the form of
      the fix, and the wrong form measurably backfires.
- [ ] Write `evals/evals.json` — at least three scenarios, each with observable
      expected behaviour, plus one near-miss that must *not* trigger the skill
      (`references/evaluation.md`).
- [ ] Write the description with the formula in
      `references/description-optimization.md`.
- [ ] Write the minimum body that closes the recorded gaps. Skip anything the
      baseline already got right.
- [ ] Split into `references/` only where the body crosses its budget, one file
      per variant or topic, each with a read-when condition.
- [ ] **Gate — every section traces to a gap:** point at the baseline failure
      each section closes. Sections with no failure behind them are deleted.

### test-with-and-without

The only evidence that a skill works. Full mechanics in
`references/evaluation.md`.

- [ ] Run every scenario with the skill and without it. Launch both
      configurations together, so a change in the environment cannot be
      mistaken for a change in the skill.
- [ ] Repeat on every model the skill is meant for. A body that reads as
      over-explained to a strong model may be the minimum a small one needs.
- [ ] Judge each `expected_behavior` item separately as met or unmet, citing the
      transcript line that decides it.
- [ ] Confirm the near-miss scenario did not load the skill. If it did, the
      description's boundary is too wide, not the body's fault.
- [ ] Mark every expectation that passes in both configurations as
      non-discriminating: it measures the model, not the skill, so it cannot
      justify text.
- [ ] **Gate — a closed gap in both directions:** at least one behaviour that
      the baseline missed is met with the skill, on every model tested. No
      closed gap means no working skill; return to scope-and-draft rather than
      editing prose.

### iterate-with-two-agents

Once the skill passes, the remaining defects are navigational and invisible from
the author's chair.

- [ ] Have one agent hold the author role (it sees the whole skill) and a fresh
      agent do real work with the skill loaded and no other briefing.
- [ ] Watch the working agent's file access, not its answer, for four signals:
      an unexpected reading order, a reference it never followed, a file it read
      repeatedly, and a file it never opened.
- [ ] Read each signal as a structural verdict — unexpected order means the
      sections are misordered, an unfollowed reference means its read-when
      condition is not observable, a repeatedly read file belongs in the body,
      and a never-opened file is either dead weight or unsignalled.
- [ ] Feed the observation back as a structure change, not as more words. Adding
      emphasis to text that was never reached changes nothing.
- [ ] **Gate — the navigation matches the design:** re-run one scenario and
      confirm the working agent now reaches the intended files in the intended
      order.

### optimize-description

Run when a skill is skipped, or fires on the wrong requests. Details and the
worked query set in `references/description-optimization.md`.

- [ ] Write one task-and-key-noun routing sentence under rule 3, regardless of
      the body's shape. Replace vague words rather than accumulating clauses.
- [ ] Build roughly twenty realistic queries, split between should-trigger and
      should-not-trigger, with the concrete texture of real requests — file
      names, job context, column names, typos.
- [ ] Make the negatives near misses that share vocabulary with the skill.
      Obviously unrelated queries pass every description and prove nothing.
- [ ] Hold part of the set back from the editing loop and score candidates on
      the held-out part, or the winning wording is only fitted to the queries
      used to write it.
- [ ] Re-run each query several times per candidate: triggering is stochastic
      and a single run cannot separate a better description from noise.
- [ ] **Gate — measured on unseen queries:** report the trigger rate on the
      held-out split for the old and the new description, not an impression.

### review-existing-skill

Report findings in the output format below.

- [ ] Frontmatter against `references/spec-reference.md`: field set, name
      constraints and directory match, description length, host-specific fields
      that must move out (`references/client-extensions-and-paths.md`).
- [ ] Description as the trigger: one third-person task-and-key-noun sentence,
      1–160 characters and not all whitespace, usually 8–16 words; no capability or procedure
      list. Detailed coverage and exclusions stay in `## Scope`.
- [ ] Budgets: body line count, each reference's line count, `## Contents` on
      the long ones.
- [ ] Content that the model already knows, and content that is specific to the
      project. Cut the first, keep the second.
- [ ] Navigation: reference depth, a read-when condition per reference, no
      reference-to-reference link, no unreferenced file in `references/`.
- [ ] Portability: host-specific template variables, dynamic shell injection,
      forced file attachment, cross-skill path references, namespace prefixes,
      backslash paths, unqualified MCP tool names.
- [ ] Writing: one term per concept, one default plus an escape hatch,
      no time-sensitive statement, reasons present, freedom matched to
      fragility.
- [ ] Scripts, if any: Run or See labelled, referenced at least once, solves
      rather than defers, constants explained, dependencies declared.
- [ ] Guessing points — places where the instructions force the agent to invent
      a value, a path or a convention. Each one is a defect; name the fact that
      is missing.
- [ ] Evidence: does `evals/` exist, are there three scenarios, is one a
      negative, was a baseline measured.
- [ ] **Gate — every finding is actionable:** each carries a location, the rule
      it breaks, and the replacement text or structural change. Findings without
      a fix are deleted.

### package-and-publish

Distribution mechanics and provenance in `references/publishing.md`.

- [ ] Keep the repository layout flat: one directory per skill under a
      container directory, identical internal structure, no category nesting.
      A skill's identity is its directory name, and flat keeps selection by
      name unambiguous.
- [ ] Keep each skill independently installable: no path that reaches outside
      its own directory, since installers copy or symlink one skill at a time.
- [ ] Record the licence of the skill and of every upstream it adapts, with the
      commit that was read. Proprietary upstreams are read for coverage only and
      contribute no text.
- [ ] Validate every skill mechanically before publishing, and keep the check
      in continuous integration so a later edit cannot quietly break it.
- [ ] Smoke-install into a scratch directory with the installer users will run,
      then confirm `SKILL.md` and every bundled file arrived.
- [ ] **Gate — installed and readable:** the skill loads from the installed copy
      and its references resolve there, not only in the source tree.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Frontmatter fields, limits, directories, disclosure budgets, validation | Always, before touching frontmatter | `references/spec-reference.md` |
| Host-specific frontmatter, discovery paths, listing truncation | A skill targets one host, or a field is not in the spec | `references/client-extensions-and-paths.md` |
| Description formula, trigger query sets, held-out scoring | Writing or fixing a description | `references/description-optimization.md` |
| Sections, naming, budgets, freedom, disclosure and guidance patterns, anti-patterns, when a script earns its place | Drafting or restructuring a body | `references/structure-and-writing.md` |
| Evaluation files, baselines, grading, multi-model runs, pre-release checklist | Proving or measuring a skill | `references/evaluation.md` |
| Installers, plugin manifests, repository layout, licensing, provenance | Publishing, or vendoring upstream material | `references/publishing.md` |
| Three annotated skills, good and bad | Choosing a shape for a new skill, or calibrating a review | `references/worked-examples.md` |

## Output format

Use this shape for `review-existing-skill`. Group by file, skip files with no
findings, and end with a prioritised summary. Quote the replacement text rather
than describing it.

### SKILL.md

**Line 3 — the description is first person and leaves the widget task vague.
Name the task and identifying technology in one short routing sentence.**

```yaml
# Before
description: I can help you build widgets with our design system.

# After
description: Builds UI widgets with the acme design system in React and TypeScript.
```

**Line 5 — `paths` and `metadata.promptSignals` are one host's fields; other
hosts ignore them, so activation is unhandled.** Delete both and put the
triggering into the description.

**Lines 152–831 — the component catalogue is 680 lines of body.** Move it to
`references/` as a table of name, purpose, props and file, and point at it from
the body with a read-when condition: read it before writing any component, to
check whether one already exists.

### advanced.md (bundled reference)

**Line 23 — links to a second reference, so the deeper file gets previewed
rather than read.** Promote it to a sibling of `SKILL.md` and point at both
from the body.

### Summary

1. **Triggering (high):** the description cannot match anything; nothing else
   in the file matters until it does.
2. **Navigation (high):** an 842-line body and a two-level reference chain
   together guarantee partial reads.
3. **Portability (medium):** the generator command and the injected registry
   file work in one host only.

When the user asked for changes rather than a review, apply the same checks and
edit the files directly instead of returning a report.

## Environment

- Validate a skill's frontmatter and naming with the reference validator:
  `npx skills-ref validate ./<skill-dir>`, or the equivalent check in the
  repository that holds the skill. Line budgets are a `wc -l` away and belong
  in the same check.
- Install and update skills with `npx skills@latest`; its subcommands and its
  repository scan rules are in `references/publishing.md`.
- This skill bundles no scripts. Evaluation runners are host-specific, so
  `references/evaluation.md` describes the steps and the judging criteria and
  leaves the mechanics to whatever runner the repository already has.
