# Deciding what kind of document this is

## Contents

- [Why the classification comes first](#why-the-classification-comes-first)
- [The decision procedure](#the-decision-procedure)
- [Reader signals](#reader-signals)
- [What each type owes its reader](#what-each-type-owes-its-reader)
- [Splitting a mixed page](#splitting-a-mixed-page)
- [Rules that apply to one type only](#rules-that-apply-to-one-type-only)
- [Do not build empty scaffolding](#do-not-build-empty-scaffolding)
- [Naming the sections on disk](#naming-the-sections-on-disk)

## Why the classification comes first

Every writing and review rule below this line is conditional on the type. A
"Next steps" section is required at the end of a tutorial and is noise on a
reference page. A quick start belongs on a getting-started page and does not
belong on a concept page. Reviewing a page without first deciding its type
produces findings that, if acted on, make the page worse.

The type is also what decides the biggest single failure in software docs:
**a tutorial written as reference**. The reader needs one path that works; a
complete table of every option gives them a choice they have no basis to make,
and they stop at the first one. Conversely a reference written as a tutorial
cannot be scanned, so the reader who knows exactly what they want has to read
prose to find a default value.

## The decision procedure

Two questions, asked about the reader, not about the subject: [official]

| Does the content inform… | …serving the reader's… | Then it is |
|---|---|---|
| action (doing) | acquisition of skill (study) | a tutorial |
| action (doing) | application of skill (work) | a how-to guide |
| cognition (knowing) | application of skill (work) | reference |
| cognition (knowing) | acquisition of skill (study) | explanation |

Classify by what the reader is doing, never by the filename. A README can
orient or it can be reference. A page called `getting-started.md` may be a
tutorial (a first lesson) or a how-to (an experienced reader setting the thing
up); which one it is changes whether alternatives are allowed on the page.

## Reader signals

The sentence the reader would have typed, and what it asks for:

| They said | They want |
|---|---|
| "I'm new to this, walk me through it" | tutorial |
| "How do I add auth to an existing app?" | how-to guide |
| "What's the default timeout?" / "what are the flags?" | reference |
| "Why does it work this way?" / "should I use A or B?" | explanation |

When a request contains two of these, it is two documents. Answering both on
one page is how a page ends up mixed, and every rule below then applies to
half of it.

## What each type owes its reader

**Tutorial.** One path, chosen by the author, to one stated outcome. No
alternatives, no "you could also". Prerequisites declared before the first
command. Every step has a result the reader can see. The contract is
asymmetric: the reader's only obligation is to follow along, so every failure
mode on the path is the author's to remove. [official]

**How-to guide.** Addressed to a problem the reader already has, stated in
their words and not the machinery's. "How to calibrate the radar array" is a
how-to; "how to use the Calibrate button" is a description of a control, and
tells the reader nothing they did not already see on screen. Assumes the
baseline knowledge a practitioner in this domain has. May branch, because real
problems have variants. [official]

**Reference.** Led by the product, not by the reader's goal: it describes what
is there, in the shape it is there. Uniform entry format so the tenth entry
reads like the first. Facts only — a usage line is fine, a lesson is not. The
test is a stopwatch: can a reader find one fact in under 30 seconds without
reading the surrounding page. [official]

**Explanation.** Bounded by a real or imagined *why* question, because nothing
else bounds it. Higher and wider than the reader's eye-level view: it joins
things together, discusses alternatives and the reasons behind the design. It
is the one type that makes sense to read away from the keyboard. If it contains
steps, they belong in a how-to. [official]

## Splitting a mixed page

A page answers the classification question differently in different sections.
That is the common state of a README or a wiki page that grew.

1. Mark each section with its type. Do this before deciding anything else.
2. Find the page's own type: the one the reader arriving at this URL needs. For
   a README that is orientation plus a quick start; for `docs/index.md` it is
   navigation.
3. Move each foreign section to the page that already exists for its type.
   Check first — projects usually already have a `docs/reference.md` and a
   getting-started page, and the mixed page duplicated them rather than
   replacing them. Two sources for one fact is worse than one badly placed one,
   because they drift and nobody knows which is current.
4. Where no destination exists, either create it or drop the material and say
   so. Leaving it in place because there is nowhere to put it keeps the defect.
5. Link from the page to each destination, one line each. Do not leave a
   summary of the moved material behind as well; a summary of reference data is
   reference data that will go stale on its own schedule.

## Rules that apply to one type only

Applying these outside their type tells the author to break the structure, and
is the largest source of false findings in a docs review. [community]

| Rule | Applies to |
|---|---|
| Quick start near the top | READMEs, getting-started pages |
| Numbered procedure, "Next steps" at the end | tutorials, how-to guides |
| One path with no alternatives | tutorials only |
| Uniform per-entry format (name, type, default, description) | reference |
| Every parameter, flag and field present | reference |
| A bounding *why* question | explanation |
| Signature block before prose | reference |
| Experimental / unstable labels | reference and how-to pages for unstable features |

## Do not build empty scaffolding

Do not create four directories, or a page per type, and fill them later. Empty
sections advertise absence, and a docs tree of stubs is harder to fix than the
mess it replaced. [official]

The structure is an outcome, not a first step: classify and fix pages one at a
time, and the top-level shape appears once enough material has moved that it
has to live somewhere. Work at page scale or smaller, and publish each step.

## Naming the sections on disk

The four words are the author's vocabulary and need not be the reader's.
Common substitutions that stay unambiguous: *Guides* for how-to guides,
*Concepts*, *Background*, *Topics* or *Discussion* for explanation. Keep the
names stable once chosen and use one word per concept throughout the site; two
names for one section make readers believe there are two sections.

<!-- sources: diataxis, mblode-docs-writing, mcollina-skills -->
