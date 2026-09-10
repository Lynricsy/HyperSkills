# Three worked examples

Three skill shapes that work, each with the version that does not. Use them to
pick a shape for a new skill, and to calibrate a review.

## Contents

- Choosing a shape
- Example 1 — the gotcha skill
- Example 2 — the calibration skill
- Example 3 — the router skill
- What all three have in common

## Choosing a shape

| The model's problem | Shape | Body carries |
|---|---|---|
| It knows the library and gets the details wrong | Gotcha skill | A decision table, then the failures |
| It produces something competent and generic | Calibration skill | Named characteristics to avoid, and a two-pass process |
| The domain is far too large for one body | Router skill | Detection, invariants, and a table of read-when conditions |

Most skills are one of the three. A skill that seems to need all three is
usually two skills.

## Example 1 — the gotcha skill

For a mature library the model already knows. The value is entirely in what
fails silently.

**Body shape:** a routing table for the three or four things a user asks for,
then a flat list of failure modes.

```markdown
## Task routing

| Goal | Approach |
|---|---|
| Create a new document | Build it with the document library |
| Edit an existing one | Unpack the archive, edit the body XML, repack |
| Read one | Convert to markdown with the converter |

## Gotchas

- Page size defaults to A4. Set it explicitly for letter-size output.
- Table widths are specified twice, in different units. Set both or the
  column widths are ignored.
- The shading type constant is CLEAR, not SOLID. SOLID silently renders black.
- An image run requires an explicit type field. Without it the image is
  dropped, with no error.
- A page break must live inside a paragraph. At the top level it is ignored.
- Newline characters in a text run do not break the line. Use separate runs.
- A generated table of contents only picks up the built-in heading styles.
```

Why it works: every line is a fact the model does not have and cannot derive,
and each one describes a *silent* failure — the kind that produces a plausible
wrong file rather than an error. Nothing explains what a document is.

**The version that fails:**

```markdown
## Introduction

Word documents are a common file format for text documents. To create one
programmatically you need a library. There are several libraries available,
each with trade-offs. First install your chosen library with your package
manager...

## Creating a document

A document consists of sections, which contain paragraphs, which contain runs.
A run is a span of text with consistent formatting...
```

Four defects: it explains a format the model knows; it names no default, so the
choice comes back to the reader; it teaches the object model instead of the
failures; and it will be identical in usefulness to an empty file while costing
several hundred lines.

## Example 2 — the calibration skill

For work where the model produces something competent and recognisably generic
— visual design, prose style, naming. The value is a named list of the defaults
to avoid, plus a process that forces a decision before production.

**Body shape:** the characteristics to avoid, stated concretely enough to be
checkable, then a two-pass process.

```markdown
## Recognisable defaults

Work that lands in one of these clusters reads as generated. Name the cluster
you are in, then leave it deliberately.

1. Warm off-white background, one serif display face, a single terracotta
   accent.
2. Near-black background with one saturated accent, everything else grey.
3. Broadsheet pastiche: hairline rules, small caps, centred masthead.
4. The card kit: three columns of equal cards, each an icon, a bold line and
   two lines of grey text.
5. Template chrome: all-caps eyebrow labels, middle dots between metadata,
   arrows suffixed to link text.

## Process

Pass 1 — decide, before writing any code:
- Four to six named colours, each with the role it plays.
- Two type roles, and the reason each was chosen.
- The layout, as an ASCII wireframe.
- Then check the plan against the brief. Anything that does not serve the
  brief comes out now, not later.

Pass 2 — build, then critique your own output against the five clusters above
and name which one it drifted towards.
```

Why it works: "avoid generic design" is unactionable, and five named clusters
are checkable. The two passes separate deciding from producing, which is what
stops the default from arriving by accident. The self-critique names a cluster
rather than asking "is this good", so it has an answer.

**The version that fails:**

```markdown
## Design principles

- Use good typography and appropriate spacing.
- Choose a colour palette that fits the brand.
- Make sure the design is modern and clean.
- Avoid generic-looking interfaces.
- Ensure good visual hierarchy.
```

Every line is agreeable and none is checkable. An agent that reads this produces
exactly what it would have produced without it, and the evaluation would have
shown that in one baseline comparison.

## Example 3 — the router skill

For a domain too large for one body: a platform, a framework, a broad review
task. The body is detection, invariants and navigation; the depth lives in
reference files.

**Body shape:**

```markdown
## Scope

<what is covered, then an explicit list of what is not>

## Core rules

<the invariants that apply regardless of which reference gets read>

## Workflows

### review

- [ ] Deprecated API usage: `references/deprecations.md`
- [ ] Data flow and ownership: `references/data-flow.md`
- [ ] Concurrency, if the code is concurrent: `references/concurrency.md`
- [ ] **Gate — every finding is actionable:** each carries a file, a line, the
      rule it breaks, and a before/after.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Deprecated and soft-deprecated API | Always, first | `references/deprecations.md` |
| State, observation, bindings | Data enters or leaves a view | `references/data-flow.md` |
| Isolation, sendability, task structure | Concurrency code, or a migration | `references/concurrency.md` |
```

Why it works: the read-when column is a *condition an agent can evaluate*
against the code in front of it, so files get opened at the right moment and not
otherwise. The workflow is a checklist, so no step is silently skipped. The gate
is decidable. And the body remains useful with zero reference files read — the
invariants and the detection step are already there.

**The version that fails:**

```markdown
## References

See the `references/` directory for more information on the various topics
covered by this skill.
```

Three defects, and the third is the fatal one. There is no per-file trigger, so
nothing is ever read at the right moment. There is no invariant in the body, so
a run that reads nothing gets nothing. And a bare pointer at a directory
requires the agent to list it, guess from the filenames, and preview — which is
how a skill ends up "half-read".

The opposite failure is a body that is *only* a router: a table of forty files
and no content. It scores badly with an automated reviewer, it tempts an
optimiser into inlining the whole bundle, and it fails outright on any run that
opens no reference. Keep the body independently able to complete a routine task,
with the references carrying depth rather than substance.

## What all three have in common

- The body states what the skill will not answer.
- Nothing explains something the model already knows.
- Every rule carries its reason, and the reason is a failure that actually
  happens.
- One default with one escape hatch; never a menu.
- Bundled files have observable read-when conditions, one level deep.
- Each workflow ends in a gate that can be evaluated.

<!-- sources: anthropic-skill-creator, anthropic-best-practices, obra-writing-skills, getsentry-skill-writer, grafana-skill-authoring, ronifue-skill-authoring -->
