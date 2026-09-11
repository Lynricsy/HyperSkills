# Prose that a reader believes

## Contents

- [What this page is for](#what-this-page-is-for)
- [Two honest caveats](#two-honest-caveats)
- [Structural tells](#structural-tells)
- [Lexical tells, and why a word list rots](#lexical-tells-and-why-a-word-list-rots)
- [Mechanical checks](#mechanical-checks)
- [What is not a tell](#what-is-not-a-tell)
- [What to write instead](#what-to-write-instead)
- [The two-pass edit](#the-two-pass-edit)
- [The checkable list](#the-checkable-list)

## What this page is for

There is a second reading of every README, running alongside the first: is
there a person behind this, and do they know what they are talking about. A
page can be correct, complete and perfectly clear and still lose that reading
in its first paragraph, because the prose has the shape of text generated to
fill a space rather than written by someone who built the thing.

This is a different problem from making sentences easy to parse, which is what
the plain-English pass covers. "Driftwood serves as a robust solution,
empowering teams to streamline their workflows" is short, active, present
tense and free of jargon. It passes every plain-English check and tells the
reader nothing, and the reader knows it.

The failure is concrete and it is fixable: the prose asserts importance
instead of stating facts. Every fix below replaces an assertion with something
checkable.

## Two honest caveats

**Do not accuse.** Automated detectors have non-trivial error rates, and
studies find that people who do not use these tools heavily distinguish
generated from human text at about chance. [official] The point of this page is
to stop writing that way, not to identify who did.

**These are patterns, not sins.** Human marketing copy has every one of them.
A single instance is nothing; a page where six of them co-occur is the
problem, and the problem is usually that the page has no facts in it.

## Structural tells

These do not depend on vocabulary, so they stay true as models change. Each
one is a shape you can find by reading a paragraph aloud.

**Significance inflation.** The text explains that the subject matters, or
locates it inside a larger trend, instead of saying what it does.

> In today's fast-paced development environment, managing schema change has
> become increasingly crucial, and Driftwood represents a significant step
> forward in the evolution of database tooling.

> Driftwood diffs your database against the SQL files in a directory and
> prints the statements that reconcile them.

**Copula avoidance.** `is`, `are` and `has` get replaced by `serves as`,
`stands as`, `represents`, `functions as`, `boasts`, `features`, `offers`,
`delivers`, `provides`. The replacements are marketing verbs and they all
mean `is`. [official]

> The CLI serves as a lightweight alternative and boasts zero dependencies.

> The CLI has no dependencies.

**The trailing participle.** A sentence ends with `, enabling…`, `,
ensuring…`, `, empowering…`, `, highlighting…`, `, underscoring…`, `,
showcasing…`, `, reflecting…`. The clause looks like analysis and restates the
main clause in warmer words. [official] Cut it; the sentence is finished
without it.

**Rule of three.** Three adjectives or three short phrases in a row, where the
third is a synonym of the first two: "speed, reliability, and performance".
Fine once in a page. Three times is a rhythm, and it means the author had one
idea and needed three slots. In a bulleted feature list the structure is the
list, not the padding — the tell is three-in-a-row inside flowing prose.

**Negative parallelism.** "It's not just a migration runner, it's a
philosophy." "Not a framework, but a toolkit." "Fast, rather than merely
convenient." The construction manufactures a misconception so it can correct
it. Delete the first half. [official]

**Vague attribution.** "Widely regarded as", "many teams find", "developers
increasingly choose". Either name who, with a link, or delete the claim. An
unsourced consensus is the easiest sentence in the world to write and carries
no information.

**The challenges-and-future ending.** A section that begins "Despite its
strengths, X faces challenges…" and ends with a positive outlook, or a
Roadmap that says the future is bright without naming a version. [official]
Replace with the actual next thing: an issue number, a milestone, or nothing.

**The summary that summarises nothing.** "In summary", "In conclusion",
"Overall, Driftwood offers a compelling solution." A README section does not
need a conclusion; the reader is going to the next heading.

**Adjectives with no measurement.** `blazing-fast`, `robust`, `scalable`,
`seamless`, `intuitive`, `powerful`, `elegant`, `enterprise-ready`,
`production-grade`, `battle-tested`. Each is a claim the author has not
checked and the reader cannot. Replace with the measurement or delete the
word. "Fast" becomes "plans a 412-table schema in 1.9 s".

**Uniform rhythm.** Six sentences of twenty words each, all subject-verb-
object, all one clause. Humans write a long sentence and then a short one.
This is the hardest tell to fix by rule and the easiest to hear by reading the
paragraph out loud.

**Chatbot residue.** "Here's a breakdown", "Let's dive in", "Feel free to",
"I hope this helps", "Let me know if you need clarification", "Certainly!".
These are addressed to the person who typed the prompt, not to the reader of
the README. So are template placeholders left in place, and sentences that
explain what the document is about to do.

## Lexical tells, and why a word list rots

Some words became statistically overused after 2022 and are a real signal in
quantity. One or two mean nothing; a dozen in one page is the strongest single
indicator there is. [official]

The cluster worth searching a README for: `delve`, `underscore`, `showcase`,
`leverage`, `harness`, `pivotal`, `crucial`, `vital`, `testament`, `landscape`,
`ecosystem`, `journey`, `realm`, `tapestry`, `vibrant`, `seamless`,
`foster`, `robust`, `comprehensive`, `holistic`, `paradigm`, `transformative`,
`cutting-edge`, `state-of-the-art`, `game-changing`.

But the list decays. `delve` was the notorious marker in 2023 and early 2024
and had dropped off sharply by 2025; models are tuned against whatever becomes
famous. [official] A README audited only against a frozen blacklist will pass
while reading exactly as badly as before.

So use the list as a cheap first pass and the structural section as the real
one. A durable substitute for the list: compare the page against prose the
same project wrote before, in its issues or its commit messages. A sudden
change in register inside one project is more informative than any word.

(`utilize`, `leverage` as a verb, `in order to` and `prior to` are also on the
plain-English replacement list, for a different reason: they are harder to
read. They fail both tests.)

## Mechanical checks

These are greppable and they are specific.

- **Spaced em dashes.** Generated text tends to write ` — ` with spaces
  around it, against the usual typographic convention. [official] The count of
  em dashes is a weak signal on its own — one study found that among current
  models only one used them more than professional writers — but the spacing
  is a habit, and a page where every em dash is spaced was probably pasted.
- **Curly quotes and apostrophes** in a file whose other text uses straight
  ones. Mixed `"` and `“` in one document is the giveaway. [official]
- **Title Case In Section Headings**, when the rest of the project uses
  sentence case. [official]
- **A thematic break (`---`) between every section.** [official]
- **A duplicated title**: an `# H1` repeating the repository name immediately
  above the same name in the first sentence.
- **Assistant markup leftovers**: `:contentReference`, `oaicite`, `[cite: 1]`,
  `turn0search0`, or `utm_source=openai` / `utm_source=chatgpt.com` /
  `referrer=grok.com` inside a link. These are unambiguous. [official]
- **Links that 404.** Several dead links in a page that was written in one
  sitting means the URLs were produced rather than visited. [official]

## What is not a tell

Flagging these wastes the author's time and teaches nothing.

- **Bulleted lists with a bold lead-in** — `- **Retries:** three by default`.
  This is native README formatting; generated text picked the habit up *from*
  READMEs. [official] It is only a problem when the bold word adds nothing.
- **Em dashes as such.** See above: count is weak, spacing is the signal.
- **One or two vocabulary words.** `Comprehensive` is the right word for a
  reference page that is comprehensive.
- **Clean grammar and consistent structure.** Those are the goal.
- **Emoji in headings.** A style choice with its own costs, not evidence of
  anything.
- **A confident tone.** Confidence backed by a number is what you want.

## What to write instead

The replacement for a removed adjective is usually a fact you already have.

- **A number with its method.** "1.9 s to plan a 412-table schema, against
  26 s for the tool it replaced, same machine, same schema." The method is
  what makes it credible; the number alone is another claim.
- **A named comparison.** "Smaller than `X` because it does not bundle a
  parser" beats "lightweight".
- **A boundary.** "PostgreSQL 14 and later. MySQL is not supported and is not
  planned." Saying what a thing does not do is the most reliable signal that
  someone has actually used it.
- **The origin.** "Written because a 40 MB response kept timing out in the
  tool we had." One sentence of real history is worth a paragraph of
  positioning.
- **Visible uncertainty.** "We have not decided whether `plan` should emit SQL
  or a machine-readable format — see issue #87." Generated prose almost never
  admits an open question, and a reader who finds one believes the rest of the
  page more.
- **First person, where there is a person.** A solo project may say "I wrote
  this because…". A team may say "we". Committee voice on a two-person project
  is its own tell.
- **The caveat that costs you something.** "`CREATE INDEX CONCURRENTLY` cannot
  run inside the transaction, so those statements are not rolled back." No
  marketing copy contains a sentence like that.

## The two-pass edit

Editing prose for this in one pass does not work, because the second draft
inherits the first draft's frame. Two passes:

1. **Name the tells.** Go through the draft and list every instance, by
   pattern, with the line. No rewriting yet. If the list is short and the page
   still reads badly, the problem is not the prose — the page has no content,
   and the fix is to go and get the facts.
2. **Cut before rewording.** Most of these sentences have nothing under them,
   so deleting is the correct edit and rewording just relocates the problem. A
   section that shrinks by half and keeps every fact was mostly filler.

Then check that nothing true was lost: every version number, measurement,
limitation and name that survived the first draft should survive the second.

## The checkable list

- [ ] No sentence ending in `, enabling/ensuring/empowering/highlighting/
      underscoring/showcasing …`.
- [ ] No `serves as`, `stands as`, `boasts`, `represents a`, `delivers`,
      `offers` where `is` or `has` would do.
- [ ] No `not just X, it's Y`, `not X, but Y`, `Y rather than X`.
- [ ] No adjective claiming speed, quality or scale without a number beside
      it.
- [ ] No `testament`, `pivotal`, `landscape`, `journey`, `tapestry`, `delve`,
      `showcase`, `foster`, `paradigm`, `cutting-edge`.
- [ ] No "In summary", no "the future is bright", no "Despite its strengths".
- [ ] No `Here's a breakdown`, `Let me know`, `Feel free to`, `I hope this
      helps`.
- [ ] No claim attributed to unnamed developers, teams or the community.
- [ ] Em dashes unspaced; quotes and apostrophes all straight or all curly.
- [ ] No `utm_source=openai`, `oaicite`, `contentReference` or `[cite:` in any
      URL.
- [ ] Every link opened at least once.
- [ ] At least one number with its method, one stated limitation, and one
      thing the project deliberately does not do.

<!-- sources: wikipedia-ai-signs, awesome-readme-skill, mattpocock-skills, google-devdocs-style -->
