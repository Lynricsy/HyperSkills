# How-to guides and reference

## Contents

- [The two are not neighbours](#the-two-are-not-neighbours)
- [How-to guides](#how-to-guides)
  - [Address a problem, not a control](#address-a-problem-not-a-control)
  - [Shape](#shape)
  - [Branching is allowed here](#branching-is-allowed-here)
  - [Titles](#titles)
- [Reference](#reference)
  - [Led by the product](#led-by-the-product)
  - [The entry format](#the-entry-format)
  - [Completeness is the point](#completeness-is-the-point)
  - [Hand-written against generated](#hand-written-against-generated)
  - [Labelling unstable surface](#labelling-unstable-surface)
- [The 30-second test](#the-30-second-test)

## The two are not neighbours

They share an audience — a practitioner at work — and nothing else. A how-to
guide is led by what the reader is trying to do; reference is led by what
exists. Mixing them produces the two worst pages in a docs site: a how-to
guide that stops to enumerate every option at the moment the reader needs one,
and a reference page with a narrative in it that cannot be scanned.

The test when a page resists classification: delete the reader's goal from your
mind and ask whether the page still has an obvious shape. If it does, it is
reference (the product's shape). If it collapses, it is a how-to guide.

## How-to guides

### Address a problem, not a control

A how-to guide answers a human project. "How to configure reconnection back-off",
"how to serve the same rate limit from two processes", "how to migrate from
2.4 to 3.0". Each is something someone actually needs done. [official]

The common failure is a guide defined by an operation the machinery can
perform. Two examples of this, both real shapes:

- "To shut off the flow of water, turn the tap clockwise."
- "To deploy the desired configuration, select the appropriate options and
  press **Deploy**."

They look like guidance and carry none: they restate the interface the reader
is already looking at, and answer no need. Any competent practitioner knows
that a power switch turns the device on. The cost is not merely wasted words —
a docs site full of these tells the reader the product has no answers for
their real problems, because the list of how-to guides is how readers judge
what a product can do.

Build the list from questions people have asked: support threads, issues filed
twice, the same question in chat. A guide written from an invented question
answers nobody, and there is no way to tell from the inside which kind you
wrote.

### Shape

```
# How to <do the thing>

<one or two sentences: the problem this solves, and the state it leaves you in>

Assumes: <the baseline this guide does not teach; link it>

1. <step, with the command>
2. <step>
   ...

Result: <how the reader confirms it worked>

See also: <the reference page for the options used here>
```

Assume the practitioner's baseline. A how-to guide that re-explains what a
connection pool is has become an explanation with steps in it, and the reader
who came for the answer has to scroll past teaching they do not need.

### Branching is allowed here

Unlike a tutorial, a how-to guide may branch, because real problems have
variants: a different platform, a version boundary, a managed service instead
of a local one. Keep branches shallow and put the condition first, so the
reader can skip the branches that are not theirs:

```
- On Linux, ...
- On macOS, ...
```

A branch whose condition is not stated up front forces the reader to read all
of it to find out which half applies.

### Titles

Start with the task, not with the machinery. "How to share a rate limit across
processes" beats "Using RedisLimiter" — the reader searching does not yet know
the class name. Where the mechanism has a name readers do search for, put it in
the body, not in place of the task.

## Reference

### Led by the product

Reference describes the machinery: every parameter, every default, every error,
in the structure the machinery has. It takes no view on what the reader is
trying to achieve, and it does not teach. Readers come for certainty — a firm
platform to stand on while they work — so the tone is flat and the facts are
exact. [official]

Two consequences:

- The order is the product's order (alphabetical, or by module, or by route),
  not the order a newcomer would learn them in.
- A worked example is allowed per entry, at minimum usage scale. A lesson is
  not.

### The entry format

Pick one shape and hold it for every entry on the page. The tenth entry must
read like the first, because readers navigate by position after the second one:

```
### `name`

`signature`

<one sentence: what it does>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int` | `3` | ... |

Raises: `ErrorName` when <condition>.
```

For a settings or environment-variable page, the four columns are name, type,
default, and effect — with the default being the value that applies when the
key is absent, not the value in the example config.

### Completeness is the point

A reference page with a subset of the parameters is a trap: readers treat
reference as exhaustive, so an omitted parameter reads as "does not exist" and
an omitted error reads as "cannot happen". If a surface is not fully documented,
say which part is missing on the page rather than leaving the gap silent.

The same applies in reverse. A documented parameter the code does not have, or
a documented environment variable nothing reads, is worse than an undocumented
one: readers configure it, observe no effect, and conclude the feature is
broken. Finding those is the docs-against-code audit.

### Hand-written against generated

Where reference can be generated from the source of truth — docstrings, a type
definition, an OpenAPI document — generate it, and edit the source rather than
the output. A hand-maintained copy of a generated surface is guaranteed to
diverge, and the divergence is invisible because both files look authoritative.

When you find a generated file that is stale, fix the generator input and note
that the committed output was not rebuilt here, rather than editing the output
and leaving the next build to revert your fix.

Designing and generating the API description itself — OpenAPI documents,
schema, error contracts — is the `api-design` skill. This page is about the
prose around it.

### Labelling unstable surface

Anything experimental, deprecated or unreleased carries a label at the entry,
not only in a release note. A reader who lands on the entry from a search never
saw the release note. State what the label means for them: may change without
a major version, will be removed in the next major, not yet available.

Deprecations on a reference entry say the replacement and the version that
removes it. "Deprecated" with no successor leaves the reader nowhere to go.

## The 30-second test

Reference passes when a reader can find one fact in under 30 seconds without
reading the page around it. That requires: headings that are the names of
things, a uniform entry shape, and defaults in a column rather than in a
sentence. If finding the default timeout means reading a paragraph, the page has
failed the only test that matters for its type. [community]

<!-- sources: diataxis, mcollina-skills, mblode-docs-writing, google-devdocs-style -->
