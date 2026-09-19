# Deck narrative: how many slides, what each one owes you

Content rhythm only. Visual scale, palette and grid numbers live in the
layout reference; this file decides how many slides exist, what each type is
allowed to carry, and which slides never should have been built.

## Contents

- [Before any slide exists](#before-any-slide-exists)
- [Page budget](#page-budget)
- [Slide types and their limits](#slide-types-and-their-limits)
- [Sequence rules](#sequence-rules)
- [Titles carry the claim](#titles-carry-the-claim)
- [Cut list](#cut-list)
- [Numbers and sources](#numbers-and-sources)

## Before any slide exists

A fixed stage does not reflow. Text that no longer fits does not push the
page taller — it overflows, gets clipped, or forces a rebuild of the layout
that held it. So every answer below changes slide count or slide type, and
every one of them discovered late is markup surgery rather than an edit.

Ask these before writing a single element. Each row names the failure you buy
by skipping it.

| Ask | What breaks if you skip it |
|---|---|
| Presented live, or read alone? | A read-alone deck must carry the sentence the speaker would have said; a live deck must not. Guess wrong and you ship either a deck nobody can follow without you, or a script you read aloud. This also decides whether presenter notes are load-bearing or decoration. |
| Who is in the room, and what do they already know? | Sets how much definition each term needs. Discovered during the talk instead, it shows up as slide 3 either insulting or losing the audience, with no way to re-level mid-deck. |
| How long is the slot, and does it include Q&A? | The slot is the only hard cap on slide count. Without it you build to the length of the material, and the material is always longer than the slot. |
| Does the material exist, and do the numbers exist? | If a number is still "we'll get it", a placeholder chart gets drawn, looks finished, and ships. Knowing up front lets you reserve a visible hole instead. |
| Hard constraints: projector or laptop, network available, will the file be emailed, is an org template mandatory? | Each is a rebuild when found late. An emailed deck has to be one self-contained file; a room with no network kills anything fetched at runtime; a mandatory template fixes the layout family you were about to invent. |
| What single sentence should the audience repeat afterwards? | Without it a deck becomes a list of topics. This sentence is also the cut test: any slide that does not move it is a candidate for deletion. |

Then hold this order:

1. Write the outline as plain text: one line per slide, each line the claim
   that slide makes, plus its type from the table below.
2. Confirm the outline — with the requester if there is one, otherwise by
   reading the claim lines back to back and checking they form an argument.
3. Only then write HTML.

The reason is cost asymmetry, not ceremony. Reordering lines in a text outline
is free. Reordering slides in a built deck means moving markup between layout
containers, re-checking geometry on every moved slide, and re-running the deck
QA script over the whole file. Text rework is minutes; layout rework is a
rebuild. [community] The outline is also the only cheap moment to discover
that the deck wants to be 30 slides in a 15-minute slot.

## Page budget

Budget slides before writing them, because the slot is fixed and the material
is not.

- About one slide per minute of speaking time for a live technical talk. A
  15-minute slot lands at 12–15 slides. [community]
- Most decks land at 8–15 slides total. Past roughly 20, either the slot is a
  workshop-length one or the artifact is a document wearing slide markup.
  [community]
- Read-alone decks are paced by reading, not speaking: budget roughly 20–30
  seconds per slide and expect more slides with less on each.
- Q&A comes out of the slot. A "30-minute talk" with 10 minutes of questions is
  a 20-minute deck, so about 20 slides maximum, not 30.
- A live demo costs full wall-clock minutes and contributes zero slides. A
  5-minute demo inside a 15-minute slot leaves room for about 10 slides.
- Appendix slides sit after the closing slide, are excluded from the budget,
  and are reached only by jumping. "Someone might ask" is the main cause of
  overrun; an appendix is where that instinct goes.

When the draft exceeds budget, work in this order. The order matters because
each step changes what the next step has to do.

1. **Cut whole slides.** Delete anything that does not change what the
   audience believes or does. This is the only step that reduces both slide
   count and minutes, and it costs nothing downstream — when titles carry
   claims, no other slide references a deleted one.
2. **Split over-full slides.** A slide over its type's limit becomes two
   slides. This raises the count, which is why it only works after cutting;
   splitting first just makes the overrun worse.
3. **Compress content.** Shorten sentences, drop a chart series, merge two
   captions. Last, because it is the step with the worst failure mode: a deck
   of 22 individually "fixed" slides is still 22 minutes of material in a
   15-minute slot.

What never counts as budget work: keeping the slide count by shrinking type or
tightening spacing. On a fixed stage that fails silently — it looks fine at
authoring zoom and is unreadable from the back of the room. The deck QA script
catches a type floor violation; nothing catches "this deck has too much
material in it". That judgement is yours, and it has to happen at the outline.

## Slide types and their limits

Pick a type per slide at outline time and keep it in the markup as a data
attribute, so the sequence rules below stay countable without parsing prose.
Every limit here is a number on purpose: "≤3 bullets" is checkable, "not too
dense" is not.

| Type | Use it when | Hard limit |
|---|---|---|
| Cover | Always the first slide | Title, one subtitle line, speaker and occasion. Exactly one per deck. No agenda, no logo wall. |
| Single claim | The argument turns here | One sentence. No bullets, no chart, no supporting art. Needs a second sentence? It is a content slide, not a claim slide. |
| Content / bullets | The material genuinely is a list | 3 bullets maximum, each under about 12 words, no nesting. A 4th bullet means split into two slides, never a 4th line. [community] |
| Big number | One metric is the entire point | One number, one caption line naming the measurement window. Two numbers means neither is the headline — use a chart or split. |
| Chart | Any quantitative claim | One chart, one conclusion, and the conclusion is the title. Axis units and a source line are mandatory. Never a second chart. |
| Code | Showing an API, diff, or config | 10 lines visible maximum, with the 2–3 lines under discussion highlighted. Continuation slides move the highlight down; they do not add lines. A 30-line function becomes three slides or a diagram. [community] |
| Diagram | Structure, flow, or sequence | One diagram, about 7 labelled nodes maximum. If labels need abbreviating to fit, the diagram is too big for one slide. SVG text does not wrap, so an outgrown label overflows its shape silently instead of reflowing. [official] |
| Comparison | Two options, or before and after | Exactly two columns with identical row structure, 4 rows maximum. Three columns is a table, and tables on a projector are not read. |
| Section divider | Only in decks over 12 slides | Each divider introduces a run of 4–6 slides. [official] In a 10-slide deck a divider is pure overhead. |
| Quote / testimonial | The source's exact words are the evidence | One quote, under about 25 words, with an attributed speaker and role. Unattributed quotes are decoration. |
| Recap / closing | Always the last slide | 3 takeaways maximum, each echoing a claim already made. New information on the closing slide is a bug — nobody is still taking notes. |
| Appendix | Answers you expect to be asked for | Unlimited count, excluded from the visible numbering, reachable only by direct jump. Never in the linear flow. |

## Sequence rules

These are deck-level invariants. Each is countable from the per-slide type
attribute, which is why they are written as counts rather than advice.

- **First slide is a cover, last slide is a recap or closing.** [official]
  Someone who opens a shared deck reads slide 1 and skims to the end; those
  two are the only slides guaranteed to be seen, so they have to stand alone.
- **A deck over 8 slides contains at least one structure slide** — a roadmap,
  a claims-based overview, or the first section divider. [official] Past 8
  slides an audience loses its place, and a map that exists nowhere cannot be
  recovered from.
- **Section dividers only in decks over 12 slides, each introducing 4–6
  slides.** [official] A divider every second slide is chrome; a divider
  introducing nine slides divided nothing.
- **A callout or emphasis layout repeats at most twice in a row.** [official]
  Emphasis is relative. Three consecutive "this is the important one" slides
  mean none of them is.
- **Density bands must be mixed.** A deck where every slide sits in the same
  density band has no rhythm, and upstream lints treat single-band decks as a
  failure. [official] In practice: put a single-claim slide next to every
  dense chart or table slide, so the audience gets a recovery beat.
- **Eyebrow labels appear on at most `ceil(total slides / 3)` slides.**
  [official] Eyebrows mark a change of section. On every slide they are
  decoration, and the uniform repetition is one of the clearest tells of a
  machine-generated deck.
- **At most 3 consecutive slides of the same type.** [community] After the
  third bullet slide in a row the audience stops reading; a chart, diagram or
  claim slide between them restores attention.
- **One idea per slide, and that idea is the title.** On a fixed stage there
  is no scrolling and no reflow — a slide holding two ideas cannot be split at
  reading time, so the second idea is simply the one that gets lost.

## Titles carry the claim

A title states the conclusion. A noun phrase states a topic, and a deck of
topics argues nothing — the audience has to reconstruct your point from the
body text of every slide.

- **Detection for topic titles:** a title with no verb is a topic label.
  Upstream deck lints flag exactly this shape. [official]
- **Detection for restated titles:** take the word set of the title and the
  word set of the body text; a Jaccard overlap of 0.6 or higher means the body
  is paraphrasing the title instead of supporting it. [official] Replace the
  body with the cause, the mechanism, or the evidence.
- **Read the titles alone, in order.** That sequence should read as the
  argument you intend to make. If it reads as a table of contents, rewrite the
  titles, not the bodies.
- **Titles that wrap to three lines are not titles.** The stage will not shrink
  them for you, and a title that long is almost always two claims.

Before and after:

| Topic title (before) | Claim title (after) |
|---|---|
| CI metrics | Queue time fell 92% in one quarter |
| Migration plan | Two weeks of dual writes, then one afternoon of cutover |
| Caching results | Cache hits absorb 80% of read traffic, halving p99 |
| About the architecture | Every write goes through one queue, and that queue is the bottleneck |

The restatement failure looks like this. Title: "Queue time fell 92% in one
quarter." Body bullet: "Queue time dropped by 92% this quarter." That pair is
the Jaccard case above — the slide spends its only body line saying the title
again. The fix is to make the body carry the part the title cannot: "Parallel
runners went from 4 to 32 in March; the queue never re-formed."

## Cut list

Cut these by default. Each one occupies minutes of a fixed slot while adding
nothing the audience could not have inferred.

- **"About us" / speaker bio.** The audience already accepted the talk. The
  introduction is the host's job, or one line on the cover.
- **"Agenda" / "What we'll cover" in a deck under 12 slides.** It spends a
  minute narrating minutes the audience is about to experience anyway. Over 12
  slides, replace it with a structure slide whose lines are claims, not nouns.
- **A separate "Thank you" or "Questions?" slide.** It holds the screen for the
  entire Q&A with zero content. Leave the recap up instead, so the takeaways
  stay visible while people ask about them.
- **Data that does not support that slide's claim.** A chart the audience has
  to interpret before learning it was context costs attention and returns
  nothing. If it supports a different claim, it belongs on that slide.
- **Screenshot stacks — three or more consecutive UI captures.** Each one costs
  a re-orientation and delivers one fact. Crop a single screenshot to the
  region under discussion and say the rest.
- **The whole-system architecture diagram when two boxes are relevant.** The
  audience spends the slide finding the two boxes instead of hearing the point.
- **"Why choose us" / "Why we are the right team".** An assertion, not
  evidence. The evidence slides already make the case or they do not.
- **Roadmaps with no dates and no owners.** Unfalsifiable, so they carry no
  information, and they reliably invite the questions that consume the slot.
- **Quote slides from famous people unrelated to the work.** Borrowed
  authority, zero own evidence, and one minute of the slot.
- **"Just in case someone asks" detail.** Move it behind the closing slide as
  appendix. In the linear flow it charges the whole room for one hypothetical
  question.
- **Any slide you would skip while presenting.** If the plan is to say "I'll
  skip this one", delete it now — the skip costs a transition, a distraction,
  and the audience's trust in the rest of the ordering.

The general test, applied slide by slide: what does the audience believe or do
differently because this slide exists? No answer means cut. Honestly applied,
this removes roughly 20–30% of a first draft. [community]

## Numbers and sources

- **Never invent a figure to fill a chart.** On a fixed stage a fabricated
  number renders exactly as well as a real one, and nothing downstream catches
  it — the QA gate measures geometry, not truth. The only defence is not
  writing it.
- **Missing data keeps its slot.** Leave the space on the slide and state what
  is missing and who owns it: "p99 latency, EU region — pending, platform
  team". A visible hole gets filled before delivery; a deleted slot is
  forgotten; a plausible placeholder gets presented as fact.
- **Every number carries its basis in visible caption text**: measurement
  window, source system, as-of date. "92%" cannot survive a question. "92%
  (p50 queue time, CI runs, Jan–Mar, n=14k)" can.
- **Put the basis on the slide, not only in presenter notes.** Exported PDFs
  and forwarded files travel without notes, and a number outlives the talk that
  introduced it.
- **Percentages need denominators.** "Errors down 40%" from 5 to 3 is noise.
  The denominator is what turns a ratio into a claim.
- **State rounding when it changes the conclusion.** Calling a 1.6x
  improvement "2x" is a rewrite of the claim, not a rounding.
- **One metric, one window, across the whole deck.** If two slides cite the
  same metric over different periods, that is the inconsistency an audience
  spots first and the fastest way to lose the room.
- **Placeholder strings must not reach delivery.** They are prose, so a
  geometry check passes them. Scan the file before the QA gate:
  `grep -nE 'TBD|Lorem ipsum|XX%|\[placeholder\]|FIXME' deck.html` — any hit is
  a blocker, not a warning.

<!-- sources: flabs-slideshow-deck, event4u-html-deck, zarazhangrui-frontend-slides, slidespeak-design -->
