# Explanation pages and technical articles

## Contents

- [What explanation is for](#what-explanation-is-for)
- [Bound it with a why-question](#bound-it-with-a-why-question)
- [Shape of an explanation page](#shape-of-an-explanation-page)
- [Signs it has drifted into another type](#signs-it-has-drifted-into-another-type)
- [Technical articles and blog posts](#technical-articles-and-blog-posts)
- [The defining constraint](#the-defining-constraint)
- [Claims, numbers and benchmarks](#claims-numbers-and-benchmarks)
- [Editing a draft down](#editing-a-draft-down)

## What explanation is for

Explanation joins things together. It answers "can you tell me about …", takes
the wider view rather than the reader's eye-level one, discusses alternatives
and says why the design is what it is. It is the only one of the four types
that makes sense to read away from the keyboard. [official]

It is less urgent than the other three and no less important: without it a
practitioner's knowledge of a system stays fragmentary, and their use of it
stays anxious — every unexplained behaviour is a possible landmine. The usual
symptom of a docs site with no explanation section is that the same question
gets asked every few weeks and answered in chat each time.

## Bound it with a why-question

Tutorials are bounded by what the reader must learn, how-to guides by the task,
reference by the machinery. Explanation has no external boundary, which is why
explanation drafts sprawl. Supply one: write the question the page answers
before writing the page, and keep it visible at the top. [official]

Good bounding questions are specific enough to end:

- "Why does a shared rate limit need a shared store?"
- "Why are retries and rate limiting in one library instead of two?"
- "What breaks if the token bucket refills on read instead of on a timer?"

A page whose question is "How does the limiter work?" has no end condition and
will grow until someone splits it. If you cannot write the question, the page
is probably reference material that has been narrated.

## Shape of an explanation page

```
# <topic>

<the question this page answers, as a question or as a claim about it>

<context: what exists, what constraint forces the discussion>

<the core idea, in the reader's terms>

<alternatives, and the trade-off that separates them>

<consequences: what this means for someone using the system>
```

Two things to keep out: steps (they belong in a how-to) and exhaustive tables
(reference). An explanation may quote a default to make a point; it must not
become the place readers look up defaults, or it acquires a second job and
drifts against the reference page.

Where the page discusses a choice the project made and still lives with, an
architecture decision record may be the better artefact. Explanation is for
readers of the system; an ADR is for maintainers of it.

## Signs it has drifted into another type

| Symptom | It is now |
|---|---|
| Numbered steps with commands | a how-to guide |
| A complete table of options | reference |
| "First, install…" | a tutorial |
| A list of every error the system raises | reference |
| Advice on what the reader should do next week | a how-to guide |

Drift is usually additive: someone answered a support question by appending to
the concept page. Move the answer to its proper type and leave a link.

## Technical articles and blog posts

An article is explanation addressed to someone who did not come looking for it.
That changes two things and nothing else: it must earn attention in its first
paragraph, and it cannot assume the product is installed.

- **Lead with the finding, not the journey.** "Our p99 fell from 1.8s to 240ms
  when we stopped retrying inside the connection pool" is a first line. "In this
  post we will explore retries" is a table of contents.
- **One claim per article.** An article with three claims gets remembered for
  none of them.
- **Ground every general statement in the specific case you actually have.**
  The specific case is the only part a reader cannot get elsewhere.
- **Say what you are not claiming.** The sentence that names the limits of the
  result is what separates an article from a pitch, and it is usually the
  sentence that gets cut.
- **No product pitch.** Marketing copy is out of scope here; an article that
  ends in a call to action has changed genre and will be read as advertising,
  including the technical parts.

## The defining constraint

Whether it is a concept page or an article, the most valuable sentence states
the single fact that makes this thing behave differently from the obvious
default. For a shared limiter: it holds the total below the upstream's limit
without knowing how many workers exist. For an ADR: it records the options that
were rejected, which the code cannot. [community]

Write it as a plain declarative sentence. Not "The key insight is that…" and
not "The defining constraint is…" — the label reads as filler and pushes the
actual content into a subordinate clause. If you cannot state it, you do not yet
know what the page is about, and no amount of structure will hide that.

## Claims, numbers and benchmarks

Every number in an article needs its method next to it: what was measured, on
what, how many times, against what baseline. A number without a method is not
evidence, and a reader who spots one unmethodded number discounts the rest of
the page.

If the measurement cannot be reproduced from what the article contains, say so
in the article rather than letting the reader discover it. "Measured on one
production cluster, not a controlled benchmark" costs a clause and buys the
reader's trust for everything else.

## Editing a draft down

Explanation is where padding hides, because prose sounds finished. Passes that
find real cuts:

1. **Delete the first paragraph.** In most drafts it announces the subject. The
   second paragraph is usually the real opening.
2. **Check each heading's first sentence.** If it restates the heading, the
   sentence is filler: `## Retries` followed by "Retries are an important part
   of…" says nothing the heading did not.
3. **Find sentences with no falsifiable content.** "It is important to consider
   the trade-offs" survives any edit because it asserts nothing. Cut it or
   replace it with the trade-off.
4. **Cut every intensifier and hedge that changes nothing** — *very*, *quite*,
   *really*, *simply*, *just*, *of course*, *it should be noted that*. "Simply
   run" tells a reader whose run failed that they are stupid.
5. **One concept, one word, throughout.** Alternating between *bucket*,
   *limiter* and *throttle* for one thing makes readers look for three things.
6. **Read the document once with only the headings and first sentences.** If
   that skim does not convey the argument, the structure is wrong and no
   sentence-level edit will fix it.

A finished draft gets shorter as it gets better. If it is growing, the argument
is not settled yet.

<!-- sources: diataxis, mattpocock-skills, neolab-write-concisely, google-devdocs-style -->
