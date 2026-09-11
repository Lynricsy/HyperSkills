# Sentences that survive a non-native reader

Verified against: Google developer documentation style guide.

## Contents

- [Why these and not "write clearly"](#why-these-and-not-write-clearly)
- [Sentence shape](#sentence-shape)
- [Words to replace](#words-to-replace)
- [Modifiers](#modifiers)
- [Words you may not omit](#words-you-may-not-omit)
- [One word per concept](#one-word-per-concept)
- [Voice, person and tense](#voice-person-and-tense)
- [Abbreviations and pronouns](#abbreviations-and-pronouns)
- [What not to reach for](#what-not-to-reach-for)
- [Things that do not translate at all](#things-that-do-not-translate-at-all)
- [The checkable list](#the-checkable-list)

## Why these and not "write clearly"

Most of the documentation a project ships in English is read by people whose
first language is not English, and some of it is machine-translated before
anyone reads it. "Write clearly" cannot be checked and so cannot be reviewed.
Every item on this page can be checked against a specific sentence, which is the
only reason it is here.

The rules below are Google's developer-documentation guidance, which is written
for exactly this audience. [official]

## Sentence shape

- **Subject, verb, object.** Standard English word order, with the main subject
  and verb as near the start as you can get them.
- **One idea per sentence.** A sentence with two clauses joined by "and" that
  could be two sentences should be two sentences. English sentences often
  lengthen considerably when translated; a long one can also break page layout.
- **Condition first.** When the instruction applies only in a circumstance,
  state the circumstance before the instruction: "If the key is absent, then the
  default is returned" — not the reverse.
- **Lists are parallel.** Every item in a list starts with the same part of
  speech and is punctuated the same way. Mixed list items read as two lists
  interleaved.

## Words to replace

Prefer the plain word. These are not stylistic preferences; the longer forms are
the ones translation memory and non-native readers stumble on. [official]

| Instead of | Write |
|---|---|
| commence | start, begin |
| consequently | so |
| utilize, leverage | use |
| a number of | some, many |
| prior to | before |
| in order to | to |
| make use of | use |
| is able to | can |

Use one word where a phrase says the same thing. The exception is a word used
in its precise technical sense — "the client utilizes up to 100% of available
CPU" is a claim about utilization, and stands.

**Avoid phrasal verbs** where a single verb exists: "this document uses the
following terms", not "this document makes use of the following terms". Some
phrasal verbs are the only names for the thing — *set up*, *log in*, *sign in* —
and stay. [official]

## Modifiers

- **No more than two nouns modifying another noun.** "A cloud-native DevSecOps
  pipeline in a hybrid environment", not "a hybrid cloud-native DevSecOps
  pipeline". Beyond two, readers cannot tell which noun modifies which.
- **Place `only` immediately before what it limits.** "Request only one token"
  means one token. "Only request one token" says the request is the only action.
  The two sentences give different instructions, and the second is almost never
  the intended one.
- **Avoid gerunds where a clause reads plainer.** "You must configure the
  firewall rules before you deploy the instance", not "configuring the firewall
  rules is required before deploying the instance". [official]

## Words you may not omit

Conversational English drops these; documentation keeps them, because the reader
may be parsing the sentence one clause at a time. [official]

| Keep | Instead of |
|---|---|
| If the key is not found, **then** the default is returned. | If the key is not found, the default is returned. |
| assumes **that** you have the following knowledge | assumes you have the following knowledge |
| Identify all **of** the datasets. | Identify all the datasets. |
| Start the profiler, **and then** run the app. | Start the profiler, then run the app. |
| the rules **that** you defined | the rules you defined |

Repeat a word where the repetition removes ambiguity: "an egress rule whose
action is `allow`, **whose** destination is `0.0.0.0/0`, and **whose** priority
is the lowest" — the shorter version makes the reader guess where the possessive
stops applying.

## One word per concept

One name per thing, everywhere, with the same capitalisation. Not *bucket* here,
*limiter* there and *throttle* in the third paragraph. Readers — and translators
— treat different words as different things, so synonyms invent concepts that do
not exist. This is the single highest-value rule on the page and the one most
often broken by multiple authors on one site.

Use the same word for the same UI element, the same file, the same role. Where
the project has a glossary, it wins over your preference.

## Voice, person and tense

- **Active voice.** With the passive, the reader often cannot tell who is
  supposed to act: "the configuration is loaded" leaves open whether they must
  load it.
- **Second person.** Address the reader as *you*, not *the user* or *they* —
  unless you are genuinely talking about someone using the software the reader
  is building. A tutorial may use *we* for the shared walkthrough; every other
  document type uses *you*.
- **Present tense.** "The request fails", not "the request will fail".
- **Positive form.** Prefer telling the reader what to do over what not to do.
  Where a prohibition is the point, keep it — but a page mostly made of
  negatives is hard to act on.

## Abbreviations and pronouns

- Expand an abbreviation on first use on each page. Readers arrive from search,
  mid-page, and the expansion three pages back does not help them.
- Replace an ambiguous pronoun with the noun. "If you use the term *green beer*
  in an ad, make sure that **the ad** is targeted" — not "make sure that it's
  targeted", where *it* could be the term or the ad.
- Avoid directional language in procedures. "See the table below" breaks when
  the page reflows, when it is translated into a different layout, or when a
  screen reader reaches it out of order; name the thing instead.

## What not to reach for

- **Colloquialisms and idioms.** *Ballpark figure*, *back burner*, *hang in
  there*: each is a phrase a competent reader can fail to parse entirely.
- **Humour.** Most of it is culturally specific and most of what survives
  translation is not funny. A joke in a procedure is one more thing the reader
  has to decide whether to take literally.
- **Culturally specific references.** Holidays, sports, local practices.
- **Seasons as dates.** "Ships in the summer" is six months wrong in the
  southern hemisphere. Give the quarter or the month.
- **"Simply", "just", "obviously", "of course".** They assert the step is easy.
  A reader whose step failed now also believes it was their fault.
- **Ambiguous dates and times.** `03/02/2026` is two different days. Use
  `YYYY-MM-DD`, name the month, and state the time zone.

## Things that do not translate at all

Images are not translated. Any information that exists only inside a screenshot
or a diagram is unavailable to a translated reader, and to a reader using a
screen reader. New information goes in text; images illustrate what the text
already said. [official]

The same holds for text baked into a diagram, a table rendered as a picture, and
a code sample delivered as a screenshot — the last is also uncopyable, which is
reason enough.

## The checkable list

Run these against a draft. Each is a search, not a judgement:

- [ ] No sentence over about 25 words that could be two.
- [ ] No `utilize`, `leverage`, `commence`, `prior to`, `in order to`,
      `make use of`, `a number of`.
- [ ] No `simply`, `just`, `obviously`, `of course`, `easy`.
- [ ] Every `only` sits immediately before what it limits.
- [ ] No noun stack longer than two modifiers.
- [ ] No dropped `that`, `then` or `of` where the list above keeps them.
- [ ] One name per concept, checked by searching for the synonyms you might
      have used.
- [ ] Every abbreviation expanded once on this page.
- [ ] No `above`, `below`, `left`, `right` used to locate content.
- [ ] Every date `YYYY-MM-DD` or with a named month; every time with a zone.
- [ ] No information that exists only inside an image.
- [ ] Second person throughout, except a tutorial's shared `we`.

<!-- sources: google-devdocs-style, neolab-write-concisely, mblode-docs-writing -->
