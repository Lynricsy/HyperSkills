# Interface copy

Words in a design exist to make it easier to understand and use. They are content, not decoration,
and they deserve the same intentionality as spacing and color. Copy can make a design feel as
templated as the design itself.

## Contents

- [Before writing anything](#before-writing-anything)
- [Naming](#naming)
- [Voice](#voice)
- [Buttons and actions](#buttons-and-actions)
- [Errors, empty states and loading](#errors-empty-states-and-loading)
- [Typographic conventions](#typographic-conventions)
- [Locale](#locale)
- [The copy self-audit](#the-copy-self-audit)
- [Checkable rules](#checkable-rules)

## Before writing anything

Ask what the design needs to say, and how it can best be said to help the person navigate. Then let
each written element do exactly one job. Two elements saying the same thing means one is unnecessary,
which is why "Introducing Acme" above an `h1` that already names the product is always cuttable.

## Naming

- Name things by what the person will understand, not by how the system is built. Somebody manages
  notifications, not webhook configuration.
- Describe what something is or does in plain terms rather than selling it.
- Being specific and legible to a new user beats being clever, every time.
- One concept, one word, everywhere. The vocabulary of an interface is the signposting people use to
  learn their way around, and a synonym is a new concept as far as the reader knows.

## Voice

- Active voice by default: "Install the CLI", not "The CLI will be installed".
- Second person. Avoid first person; the interface is not a character.
- Sentence case for prose, plain verbs, no filler.
- Tone matched to the brand and the audience, and conversational rather than formal by default.
- No filler verbs: `Elevate`, `Seamless`, `Unleash`, `Next-Gen`, `Revolutionize`. They say nothing
  and they are a generated-copy tell.

## Buttons and actions

- A call to action says exactly what happens: "Save changes", not "Submit". "Save API key", not
  "Continue".
- The verb persists through the flow: "Publish" produces "Published".
- Title Case for headings and buttons where the product's style is Title Case; whatever the choice,
  it is consistent across the product.
- Numerals for counts: "8 deployments", not "eight deployments".
- No `→` appended to button and link text. The arrow is template chrome, and where direction genuinely
  matters an icon element carries it (hidden from assistive technology).
- `&` in place of "and" only where space is genuinely constrained.

## Errors, empty states and loading

- Failure and emptiness are moments for direction, not mood.
- An error explains what went wrong and how to fix it, in the interface's voice. It does not
  apologize, and it is never vague about what happened.
- An empty screen is an invitation to act: say what belongs here, and give the action that puts it
  there.
- Loading text ends with an ellipsis: `Loading…`, `Saving…`. And it must be true; a status line
  permanently reading `Loading…` because nothing ever updates it is worse than no status line.

## Typographic conventions

- `…` not `...`.
- Curly quotes in prose, not straight quotes. Straight quotes stay in code samples.
- Zero em dash (U+2014) and zero en dash (U+2013) in visible copy. Restructure with a period, comma,
  parentheses, colon, line break, or a separate column. Ranges use a hyphen.
- Non-breaking spaces where a break would be wrong: `10&nbsp;MB`, `⌘&nbsp;K`, multi-word brand names.
- One middle dot per metadata line at most, and never as the universal separator.
- No tracked ALL-CAPS eyebrow labels as a default treatment.

## Locale

- Dates and times through `Intl.DateTimeFormat`. `03/04/2026` is ambiguous between two large
  markets; a machine-readable `<time datetime="2026-03-04">` plus a formatted label is unambiguous.
- Numbers and currency through `Intl.NumberFormat`.
- Detect language from `Accept-Language` or `navigator.languages`, never from IP geolocation.
- Wrap brand names, code tokens and identifiers in `translate="no"`.
- Write copy that survives translation: German and Finnish strings run considerably longer than
  English, so a button sized to its English label will break.

## The copy self-audit

Before shipping, re-read every visible string and flag:

- Anything grammatically broken or with an unclear referent.
- Anything that reads like the writer trying to sound thoughtful: forced wordplay, mock-humble
  craftsman labels, aphorisms.
- Placeholder residue: `John Doe`, `Acme`, `lorem`, `Lorem ipsum`, `TODO`, `99.99%`.
- Two strings saying the same thing.

Replace each with a plain functional sentence. Boring but correct beats cute but wrong.

## Checkable rules

- `...` instead of `…`; straight quotes in prose.
- Em dash or en dash in visible copy.
- Generic button label ("Submit", "Continue", "Click here").
- `→` inside button or link text.
- Passive voice in a call to action.
- Error message with no fix or next step.
- Hardcoded date or number format.
- Placeholder name, brand or number left in place.
- Loading text without a trailing ellipsis.
- Inconsistent casing across headings or buttons.
- Two adjacent elements carrying the same message.

<!-- sources: anthropic-frontend-design, vercel-wig, antfu-design, uiux-pro-max -->
