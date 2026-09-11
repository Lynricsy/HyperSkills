---
name: technical-writing
description: "Writes and repairs the documents a project ships to human readers: READMEs, documentation pages, tutorials, how-to guides, reference pages, architecture decision records and changelogs. Classifies a page as tutorial, how-to, reference or explanation first, makes code blocks runnable as pasted, and holds documented defaults and symbols to the source. Also decides how a README looks and reads: first-screen composition, logos and demo recordings, badges and third-party widgets, collapsed sections, alerts, diagrams, anchors that survive npm and PyPI as well as the forge, and prose edited out of an AI register. Applies when docs are written, restructured, made presentable, audited against code, or abandoned by their readers, and when a commit log must become a changelog. Do not use for SKILL.md or AGENTS.md (use the `skill-authoring` skill), GitHub profile READMEs, docs-site generators, OpenAPI generation (use the `api-design` skill), plan documents (use the `planning` skill), or marketing copy."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: task
---

# technical-writing

Paths below are relative to this skill's directory.

## Scope

The documents a project ships to people who did not write it: the README, the
documentation site and its four kinds of page, tutorials, how-to guides,
reference, concept pages and technical articles, architecture decision records,
and the changelog. Also the maintenance of all of it — finding the lines that
have quietly stopped being true, and fixing them without rewriting the page.

Writing here means three things that are not the same: choosing what kind of
document this is and what belongs on it, making the prose and the examples
hold up, and — for the README, which is read before anything else and rendered
by several different engines — composing the page so the answers arrive first
and survive every surface the file is published to. Most documentation defects
are the first kind wearing the second's clothes.

Not covered — do not answer from this skill:

- Writing a skill. `SKILL.md` frontmatter, structure, reference layout and the
  instructions an agent reads are the `skill-authoring` skill. Reader-facing
  documentation about a project is here.
- Generating reference documentation from an API description — OpenAPI
  documents, schema, error contracts: the `api-design` skill. The prose around
  the generated reference is here.
- The structure and acceptance criteria of a plan document: the `planning`
  skill. How the explanatory text in it reads to its reader is here.
- Tagging, publishing and attaching artefacts to a release: the `github` skill
  and the `git-workflow` skill. Writing what the release changed is here.
- Judging whether a code change is correct: the `code-review` skill. Judging
  whether the documentation still describes it is here.
- Docstrings and inline comments as an API surface belong with the language:
  the `python`, `typescript`, `go`, `java-spring` and `csharp-dotnet` skills.
- Marketing and landing-page copy, launch announcements, sales material.
  Nothing here writes to sell.
- The profile README in a repository named after a username. That page is a
  personal home page, not project documentation: it has no reader arriving
  with a task, no quick start to run and no source to check, so every rule
  here would be enforced against the wrong thing.
- Choosing or configuring a documentation-site generator. This skill governs
  what the pages say, not how they build.

## Core rules

Each rule is an invariant; the clause after the dash is what violating it costs.

1. Classify the page — tutorial, how-to, reference or explanation — before
   applying any other rule. Every rule below is conditional on the type, so a
   rule enforced against the wrong type makes the page worse when acted on.
2. One document, one type. A page that answers the classification differently
   in two sections is split, and the foreign sections move to the pages that
   already exist for them — a summary left behind is a second source for the
   same fact, and the two drift.
3. A tutorial offers exactly one path to one stated outcome. A first-time reader
   has no basis for choosing, so every alternative on the page is a place they
   stop.
4. Prerequisites appear before the first code block, with the exact extra, the
   exact environment-variable name the code reads, and the command that starts
   each service. An install line that omits the extra needed twenty lines later
   produces an `ImportError` the reader cannot connect to anything.
5. Every step of a tutorial or how-to guide ends in something the reader can
   observe, quoted. A step with no observable result lets a reader who has
   already gone wrong continue, and discover it three steps later with no way
   to find where it started.
6. Every code block is pasteable and runnable given the prerequisites the page
   has already declared, or it states what is missing; omitted code is marked
   with a comment in the sample's language, never `...` or `…`. There is no
   third state — a block that is neither will be run, and its failure reads as
   a product bug — and an ellipsis is legal syntax in Python and a document
   separator in YAML, so it fails for a reason unrelated to the omission.
7. No sample credential may pattern-match a live one. Use the provider's
   documented test prefix or an explained placeholder: a live-looking key gets
   pasted into real code, and forge push protection rejects the commit that
   carries it.
8. Output shown in a document is captured from a real run. Reconstructed output
   is the one thing on a page nobody rechecks, and a reader whose output differs
   cannot tell whether they broke something.
9. Every symbol, keyword argument, default value, exception name, command and
   environment variable in a document is checked against its definition in the
   current source before the document ships — at the definition, not at a call
   site.
10. Each fact has exactly one home. Install instructions in two places diverge
    within a release, because the second copy gets edited and the first does
    not, and readers act on whichever they scrolled to.
11. A README states its status whenever that status is not plainly "supported",
    and names an owner or a channel. A deprecated package whose README does not
    say so costs its next reader a day.
12. Nothing decorative goes above the line that says what the project is, and
    every badge or widget that survives there is a claim someone has checked by
    reading what it renders. A logo, a badge wall and an animation together push
    that line off the first screen, which is the whole budget a visitor gives
    you; and a mistyped badge URL returns HTTP 200 with the words "not found"
    drawn inside the image, so a link check passes while the reader sees the
    failure.
13. Every construct in a README is chosen for the renderers the file is
    published to, not for the one you are looking at. Alerts, mermaid,
    `<video>`, `<source>`, `open` on `<details>`, hand-written anchors and
    relative paths each behave differently on the forge, on a package registry
    and in an editor preview, and the ones that carry the first impression are
    the ones that differ.
14. Reference is complete, or it says on the page which part is missing, and a
    documented parameter, setting or environment variable that the code does not
    read is a defect ranked above an undocumented one. Readers treat reference
    as exhaustive, so an omitted parameter reads as "does not exist"; and a
    reader who configures something and observes nothing concludes the feature
    is broken.
15. A how-to guide is framed by the reader's problem, not by a control or a
    class name. "To deploy, select the appropriate options and press Deploy"
    restates the screen the reader is already looking at, and a site full of
    those tells readers the product has no answer for their real problem.
16. Explanation carries at its top the *why* question it answers. Nothing else
    bounds an explanation, and an unbounded one grows until someone splits it.
17. The first sentence under a heading does not restate the heading. `## Retries`
    followed by "Retries are an important part of…" spends a line saying what
    the heading said.
18. One name per concept across the document set, with the same capitalisation.
    Readers and translators treat two words as two things, so a synonym invents
    a concept that does not exist.
19. A sentence that asserts importance instead of stating a fact is cut, not
    softened: significance inflation, a trailing `, enabling…` clause, `serves
    as` where `is` would do, three synonyms in a row, "not just X, it's Y", an
    adjective claiming speed or quality with no number beside it. Readers treat
    that register as evidence that nobody has used the thing, and they apply the
    judgement to the code.
20. Changelog entries are grouped under the six standard types and no others,
    and commit history is not changelog material: merge commits, `wip`, `lint`,
    `fix CI`, `bump version` and `update tests` are deleted, not reworded. A
    seventh type costs every reader the convention that lets them read every
    other changelog the same way, and a changelog the reader has to filter is
    one they stop reading.
21. A breaking changelog entry keeps its `**Breaking:**` marker inside the type
    it belongs to, and names which interface breaks — API, command line,
    protocol, file format, configuration, or the install. A separate
    breaking-changes section is the section a reader scanning `Changed` never
    opens.
22. Deprecate in one release and remove in a later one, naming the version that
    removes it. Where a removal shipped with no prior deprecation, the entry
    says so rather than retrofitting a warning into a release that never
    carried one.
23. An audit reports; it edits only when the request was to fix. Rewriting a
    document you were asked to review destroys the evidence of how wrong it was
    and teaches its author nothing, so the next page repeats the defect.
24. Every audit finding cites a line that literally contains the thing it names,
    and every count appears next to the command that produced it. A finding is
    trusted without being rechecked, so a wrong one costs more than a missed
    one.
25. An ADR follows the repository's existing location, numbering and headings,
    or states that the conventions conflict and stops. A second numbering
    scheme means nobody can tell which record is authoritative, and both
    sequences collide at the next number.

## Workflows

### write

Producing a document that does not exist yet.

- [ ] Name the reader and what they will be able to do afterwards. Then classify
      the document with the procedure in `references/document-types.md`. One
      type (rules 1, 2).
- [ ] Check what already exists. A project usually has a getting-started page
      and a reference page, and the request is often for material that belongs
      on one of them (rule 10).
- [ ] Read the source of truth for every fact the document will state:
      signatures and defaults at the definition, declared extras, script names,
      the environment variables the code reads (rule 9).
- [ ] Draft to the shape for this type: `references/readme.md`,
      `references/tutorials.md`, `references/how-to-and-reference.md` or
      `references/explanation-and-articles.md`.
- [ ] Declare prerequisites before the first block, and write each block to be
      pasteable (rules 4, 6). Follow `references/code-examples.md`.
- [ ] Run every block in a clean environment, in order, and paste the captured
      output (rules 6, 8).
- [ ] Apply the sentence-level list in `references/plain-english.md`; it is a
      set of searches, not a judgement call.
- [ ] **Gate — IT RAN AND THE NAMES MATCH:** every block was executed in order
      from the page's own declared prerequisites, every symbol and default in
      the page was found at its definition in the current source, and every link
      resolves. Where the environment could not be created, say which blocks
      were not run.

### readme

Writing a README, or being asked to make an existing one look good. The
content rules are the same; what is added here is the page as an artefact
people look at before they read.

- [ ] Establish where this file is rendered: the forge, and whatever the
      manifest publishes it as. That decides which constructs are available
      (rule 13). `references/readme-portability.md` has the measured matrix.
- [ ] Fix the content first — the minimum set, the order, one home per fact,
      a quick start that runs. `references/readme.md`. A prettier page with
      the wrong content is a worse page.
- [ ] Compose the first screen and choose at most one visual, with
      `references/readme-presentation.md`. Nothing decorative above the line
      that says what this is (rule 12).
- [ ] Choose the badges, and only the badges, that answer a question a reader
      has before reading. `references/badges-and-widgets.md`.
- [ ] Edit the prose out of an AI register with
      `references/human-voice.md`, then run the sentence-level list in
      `references/plain-english.md` (rule 19).
- [ ] **Gate — IT RENDERS AND EVERY CLAIM IS CHECKED:** the file was rendered
      through every surface it is published to and the output inspected, every
      in-page link has a target that exists there, every image resolves from
      outside the repository where it has to, every badge URL was fetched and
      its rendered text read, and the quick start was run.

### restructure

A page — usually a README or a wiki page — has grown into several documents.

- [ ] Mark every section with its type before deciding anything (rule 1).
- [ ] Decide the page's own type from what a reader arriving at this URL needs.
- [ ] For each foreign section, find the existing page for its type. Read that
      page: the material is often already there, and the mixed page duplicated
      it rather than replacing it.
- [ ] Move each section, or drop it and say so. Do not leave a summary behind
      (rule 2).
- [ ] Delete every duplicated fact rather than reconciling both copies
      (rule 10).
- [ ] Check the whole page against the source while you are in it — a page that
      grew this way is usually also stale (rule 9).
- [ ] **Gate — NOTHING LANDS IN A PAGE THAT DOES NOT EXIST:** every destination
      page exists or is created in this change, every fact appears once, every
      link and path named in the result resolves, and no empty quadrant
      directory or placeholder page was created.

### audit

Comparing what the documentation claims against what the code does.

- [ ] Confirm the mode: report only, unless the request said fix (rule 23).
- [ ] Establish the source of truth first — exports, definitions, dependency
      extras, task names, config reads. `references/docs-code-sync.md` lists
      where to look.
- [ ] Settle every claim that has a definite answer, completely: commands that
      exist, links that resolve, symbols, signatures, defaults, exception names,
      environment variables in both directions, whether the documented install
      satisfies the page's own imports.
- [ ] Treat one confirmed rename as a reason to re-check the whole page rather
      than as a single finding.
- [ ] Then judge the claims no check settles: whether an explanation is still
      true, whether a procedure still works in order, whether a warning still
      applies.
- [ ] Separate confirmed drift from inferred gaps, and rank by reader cost, not
      file order (rule 24).
- [ ] **Gate — TWO SIDES AND A LINE FOR EVERY FINDING:** each finding names the
      source of truth and the stale documentation, cites a line that contains
      what it names, states who is misled, and proposes a specific fix. A
      finding you cannot give both sides of is a style preference; drop it.

### changelog

Turning a commit log, or nothing, into a file an upgrader can act on.

- [ ] Delete the non-entries: merge commits, `wip`, `typo`, `lint`, `fix CI`,
      `bump version`, `update tests`, internal refactors nobody can observe
      (rule 20).
- [ ] Group the survivors by version, dating each from the tag list rather than
      guessing, and sort them into the six types (rule 20).
- [ ] Read the source for renames, removed parameters and changed validation
      sets, and confirm each appears. A commit log routinely hides a break as a
      tidy-up — "switch default", "rename for consistency", "remove dead code".
- [ ] Rewrite each entry for the upgrader: old and new name in the entry, the
      observable effect where the name alone does not carry it, the reason where
      it is short.
- [ ] Mark the breaks in place and name the interface each one breaks
      (rule 21). Check whether each removal was ever deprecated (rule 22).
- [ ] Add the frame: heading, preamble naming the conventions, `Unreleased`,
      and reference-style comparison links per version.
      `references/changelog.md` has the exact shapes.
- [ ] **Gate — A READER ON THE OLD VERSION CAN ACT ON EVERY LINE:** for each
      entry you can say what the reader does about it without opening the diff,
      every break is marked with its interface named, every version is dated,
      and nothing you could not determine has been invented.

### Rationalizations

| Excuse | Reality |
|---|---|
| "The code is self-documenting" | Code states what it does. It cannot state what was rejected, or which constraint has since disappeared. |
| "I'll verify the examples later" | Then the page ships with them unverified, and the first reader does the verifying. |
| "It's basically the same as the old name" | Then say both names in the entry and it costs you four words. |
| "The README is the only doc anyone reads" | Because it is the only one anyone maintains. Fix the cause, not by adding to the README. |
| "We'll document it when the API stabilises" | The document is the first test of the design; writing it is how you find out it has not stabilised. |
| "Nobody reads the changelog" | Everybody reads it, once, on the day they upgrade and something breaks. |
| "I'll just fix the doc while I'm reviewing it" | Then no one learns what was wrong, and the next page has the same defect. |
| "`...` is obviously an omission" | It is legal Python and a YAML document separator. The reader's paste fails for a reason that is not the omission. |
| "It only has to look right on GitHub" | The package page is where people land from a dependency list, and it is a different renderer. |
| "The badges prove the project is healthy" | They prove someone pasted them once. A badge URL with a typo renders as a badge that says "not found". |
| "A back-to-top link is standard, the most popular template uses it" | Its rendered HTML has nine links to an anchor that is not there. |

### Red flags

Stop and re-check when you see any of these: a code block you have not run; an
install line that does not satisfy the imports below it; an environment variable
name that appears in the docs and nowhere in the source; a "Next steps" section
on a reference page; a quick start with a choice in it; two install sections; a
step whose result is "notice how it works"; a changelog line beginning `Merge
pull request`; a heading whose first sentence repeats it; a number in an article
with no method beside it; an ADR that edits an accepted decision; four empty
directories named after document types; a `style=` or `class=` attribute in a
README; an `<a name>` anchor or a "back to top" link; a table-of-contents entry
for a heading that carries an emoji; a `<picture>` with no `<img>` inside it;
install or quick start inside `<details>`; a badge row longer than the sentence
it sits above; a paragraph whose adjectives carry no number.

## Topic router

| Topic | Read when | File |
|---|---|---|
| The classification procedure, reader signals, what each type owes its reader, splitting a mixed page, rules that apply to one type only, why not to build empty scaffolding | Before writing or reviewing anything, and whenever a page resists classification | `references/document-types.md` |
| What a README is for and where it lives, the minimum content set, ordering, what moves out, the quick start, one home per fact, monorepo packages | Writing, cutting down or reviewing a README | `references/readme.md` |
| Which surface renders which file, the measured support matrix across the forge and package registries, anchors and slugs, relative paths, the portable subset, forge-only constructs and their fallbacks, size limits, how to render and check | Before choosing any HTML or extended-Markdown construct in a README, and whenever a page renders differently somewhere | `references/readme-portability.md` |
| First-screen composition and ordering, centring, choosing and sizing a visual, alt text, light and dark, when a collapsed section is right, alerts, diagrams, tables of contents, tables, emoji, composition defects | Writing a README, or being asked to make one look good | `references/readme-presentation.md` |
| What a badge is and how stale each kind gets, which badges earn the first screen, how many, style consistency, the HTTP 200 failure mode and how to check for it, static badges, third-party widgets and their real cost, badge markup | Choosing, auditing or cutting badges and widgets | `references/badges-and-widgets.md` |
| Structural tells that outlast any word list, the vocabulary cluster and why it decays, greppable mechanical checks, what is not a tell, what to write instead, the two-pass edit | Prose reads as generated, or before publishing anything written to be read by strangers | `references/human-voice.md` |
| The teaching contract, one outcome and one path, declaring the starting state, observable results, steps that are not steps, credentials and services, verifying, diagnosing a tutorial people abandon | Writing a getting-started page, or readers are giving up partway through one | `references/tutorials.md` |
| Problem-framed how-to guides against control-framed ones, allowed branching, reference entry format, completeness, generated against hand-written reference, labelling unstable surface, the 30-second test | Writing or fixing a how-to guide or a reference page | `references/how-to-and-reference.md` |
| Bounding an explanation with a why-question, page shape, drift into other types, technical articles, the defining constraint, claims and numbers, editing a draft down | Writing a concept page or a technical article, or a draft will not stop growing | `references/explanation-and-articles.md` |
| Matching the repository's existing convention, the field set including Confirmation, writing each field, lifecycle and superseding, when not to write an ADR, review checklist | Recording a decision, or reviewing someone's ADR | `references/adr.md` |
| The file frame, the six types, Fixed against Changed against Security, breaking changes and which interface, deprecation before removal, what is not an entry, version links, changelog against release notes, automation, scale | Writing or repairing a changelog, or deciding what a release note says | `references/changelog.md` |
| Establishing the source of truth, claims with a definite answer, change classes that make docs lie, evidence standards, severity, not writing into the repository while auditing, report shape | Auditing documentation against code, before a release or after a change | `references/docs-code-sync.md` |
| The pasteability bar, declaring what a block needs, omission markers, placeholders and sample credentials, minimality, showing output, introducing a block, formatting, checking a page's examples | Any document that contains code | `references/code-examples.md` |
| Sentence shape, words to replace, modifier placement, words you may not omit, one word per concept, voice and person, abbreviations, what does not translate, the checkable list | Editing prose, and as the last pass before anything ships | `references/plain-english.md` |

## Output format

**Docs audit** — the `audit` workflow. Findings before fixes, two sides each,
ranked by reader cost.

```
**Docs audit: <scope>**

Compared <docs checked> against <source of truth>. <N> confirmed, <M> inferred.
No P0s / P0s: <count>.

1. **P1: <what is false, stated as a fact>.**
   Drift: <what the doc claims> against <what the code does>.
   Impact: <who is misled or blocked, and how it shows up for them>.
   Evidence: docs `<path>:<line>`; source `<path>:<line>`.
   Fix: <the specific change>.

**Checks run**
- `<command>`: <result>

**Not checked**
- <what was not verified, and the residual risk>

**Inferred, not confirmed**
- <finding, and what would settle it>
```

**Restructure plan** — the `restructure` workflow. State the destination of
every section before producing any rewritten file.

```
<page> is currently <N> documents. Proposed split:

| Section | Type | Destination | Exists? |
|---|---|---|---|
| <heading> | reference | docs/reference.md | yes — already lists these; drop this copy |
| <heading> | explanation | docs/<new>.md | no — created in this change |

Staying on the page: <sections, and the page's own type>
Deleted outright: <section, and why nothing needs it>
Also wrong while I was in here: <stale claims found, with the source line>
```

**README review** — the `readme` workflow, when asked to improve an existing
file. Findings before the rewrite, each naming what breaks and where.

```
Rendered on: <surfaces this file is published to>

| Construct | Where it breaks | Fix |
|---|---|---|
| <line or snippet> | <surface, and what the reader sees there> | <the change> |

Claims that are not true: <badge, link, image, or section, with the evidence>
Cut for the fold: <what moved below the first sentence, or out of the file>

Then the rewritten file, followed by the checks you ran on it.
```
