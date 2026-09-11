# The first screen, and everything that competes with it

## Contents

- [What layout is for](#what-layout-is-for)
- [Composing the first screen](#composing-the-first-screen)
- [Centring](#centring)
- [Choosing a visual](#choosing-a-visual)
- [Writing the image markup](#writing-the-image-markup)
- [Light and dark](#light-and-dark)
- [Collapsed sections](#collapsed-sections)
- [Alerts](#alerts)
- [Diagrams](#diagrams)
- [Navigation](#navigation)
- [Tables](#tables)
- [Emoji](#emoji)
- [Composition defects](#composition-defects)
- [Review checklist](#review-checklist)

## What layout is for

A README answers four questions: what is this, is it alive, can I use it,
where do I go next. Layout exists to get those answers in front of a reader
sooner. Nothing else justifies it.

That gives a single test for every decorative element: does a reader who
scrolls once get an answer they would otherwise have missed? A demo GIF that
shows what the tool does before the prose can say it passes. A logo, a tagline
in a typing animation, a badge wall and a hero banner stacked above the first
sentence all fail the same test, because together they push the answer to
"what is this" off the screen. The most common way to make a README worse is
to make it prettier one element at a time.

Layout is also not a way out of thin content. A page with nothing to say reads
as a page with nothing to say, in a nicer font.

## Composing the first screen

Roughly one screen is what a visitor gives you. The order below is a ranking:
take the items you can justify, in this order, and stop.

1. **The name.** As an `#` heading, or as a logo image with the name in its
   `alt` text. Not both — a wordmark image directly above the same word as
   text is a duplicated fact.
2. **One sentence saying what it is**, in the reader's vocabulary. This is the
   line the whole page exists to deliver. Keep it under about 120 characters,
   on its own line, and make it the same sentence as the repository
   description and the `description` field in the manifest: those three appear
   side by side in search results and a mismatch reads as neglect. [community]
3. **Status**, when it is not plainly "supported".
4. **Badges** — a short row, chosen for facts a reader needs before reading.
5. **One visual**, if the project is one a picture can explain.
6. **Key links** — documentation, live demo, issue tracker — as one line, not
   a nav bar of buttons.

Then install, then the quick start. The first code block should be reachable
with one scroll.

Elements 1, 4 and 5 are the ones that grow. A useful discipline: write the page
with none of them, confirm it reads, then add back only the ones that answer a
question the text left open.

## Centring

`align` on `<div>`, `<p>` or a heading is the only centring mechanism that
works; CSS is stripped by every renderer. Centred text has a ragged left edge,
so it costs reading speed on anything longer than a line or two.

Centre the name, the tagline, the badge row, a logo and a single link line.
Leave everything else — prose, lists, code, tables — left-aligned. A centred
paragraph is a paragraph someone will skip.

An HTML heading keeps its generated section anchor, so `<h1 align="center">`
does not cost you the link to it.

## Choosing a visual

One good visual is worth more than four. Which one depends on what a reader
cannot get from a sentence:

| Project | The visual that earns its place |
|---|---|
| CLI, terminal tool | A recording of one real run, start to finish |
| Library, SDK | Usually none. The code block is the demo. |
| Web or desktop app | One screenshot of the main screen, with real data |
| Visualisation, generator, formatter | Before and after, side by side |
| Service with moving parts | One diagram, only if the parts are not obvious |

A recording should show the core loop once, in under about fifteen seconds,
and end where it began so the loop is not jarring. Script it rather than
screen-record it where you can, and commit the script: a recording nobody can
regenerate is stale from the first release that changes the output.

Budget: GitHub rejects images and GIFs over 10 MB outright, so that is a hard
ceiling, not a target. Aim far below it — a reader on a slow connection sees
the skeleton of the page while a multi-megabyte GIF loads, which is the
opposite of a fast first impression. Prefer a short recording at modest width
over a long one at display resolution.

Screenshots use real data. A screenshot of `Lorem ipsum` rows tells the reader
the project has never been used for anything.

## Writing the image markup

- **`alt` is required, and it is a sentence, not a filename.** Images are not
  translated and are not read aloud; anything that exists only inside the
  picture is lost to part of your audience. The image illustrates what the
  text said — it does not carry new information.
- **Set an explicit `width`.** Without one, a large asset renders at its full
  pixel size and pushes everything else off the screen.
- Purely decorative rules and spacers do not need alt text, and mostly do not
  need to exist.
- Store assets under a committed directory — `docs/` or `.github/assets/` —
  and check the file is actually in the tree. A broken image is read as a
  broken project, and it is the single easiest defect to ship, because the
  author's working copy has the file.

## Light and dark

A diagram or logo with a white background disappears on a dark page. The fix
is `<picture>` with a `prefers-color-scheme` source and an `<img>`
fallback. [official]

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.svg">
  <img alt="Tilekit" src="docs/logo-light.svg" width="120">
</picture>
```

The `<img>` is not a courtesy. It is what renderers that drop `<source>` show,
and what a browser without the media feature shows. Write the light asset
there, with the real alt text.

Two assets to maintain is the cost. A diagram exported with a transparent
background and mid-tone strokes needs only one, and is usually the better
trade.

## Collapsed sections

`<details>` hides bulk from the scroll without deleting it. It is right for:

- a long option or environment-variable table that the README keeps only as a
  convenience, with reference named as authoritative;
- per-platform install variants, where each reader needs exactly one;
- notes about older versions;
- a frequently-asked-questions block at the bottom.

It is wrong for anything a first-time reader needs: install, the quick start,
the status line, the licence. Collapsed content is not searched by the
browser's find-in-page until it is expanded, and `open` is not honoured
everywhere, so "it is open by default" is not a defence.

Wrapping a thin section in `<details>` to make the page look tidy hides that
the section is thin. Delete it instead.

## Alerts

The `> [!NOTE]` family is for information that changes what the reader does,
where they would otherwise miss it: a breaking default, a destructive command,
a prerequisite that fails late. GitHub's own guidance is to use them only when
they are crucial, to keep to one or two per page, and never to place two in a
row or nest one inside another element. [official]

A README with an alert on every section has taught its readers to scroll past
alerts, which costs exactly the one that mattered.

Because the marker degrades badly on some surfaces, put the meaning in the
first words of the quote rather than relying on the label to carry it.

## Diagrams

A diagram earns its place when the reader cannot hold the relationship in
their head from a sentence: four or more components with non-obvious edges, a
state machine, a protocol handshake. Three boxes in a row is a sentence.

Keep the diagram to one screen, label the edges, and put the claim the diagram
supports in text next to it — a reader on a surface that does not render it
still gets the point. Mermaid is the diff-able option and renders on the forge;
an exported SVG or PNG renders everywhere. Pick by where the file is read.

## Navigation

GitHub generates an outline from the headings, so a hand-written table of
contents on a short README is a second copy of navigation the reader already
has, and a second thing to keep in sync. Write one when the file is long
enough that a reader scrolls looking for a section — past roughly a hundred
lines is the usual threshold — and when it is published somewhere with no
outline of its own. [community]

When you write one:

- Link to headings, never to hand-made anchors.
- Include every second-level heading, and stop there unless the page is very
  long.
- Check the slug of any heading containing an emoji or punctuation.
- Collapse it behind `<details>` if it is longer than about a dozen entries —
  a table of contents that fills the first screen defeats its own purpose.

"Back to top" links are not worth their cost. They rely on an anchor scheme
that does not survive off the forge, they repeat at every section, and the
browser already has `Home`.

## Tables

Tables are for a set of things with the same shape: options and their
defaults, platforms and their commands, versions and their support status.
They are not for prose in two columns.

- Keep to three or four columns. A wide table wraps into unreadable stacks on
  a narrow screen, and README tables have no horizontal scroll to escape into.
- Right-align numeric columns with `--:`.
- Put the column the reader scans in the first position.
- One sentence per cell. Anything longer belongs under a heading.
- A table with two rows is a list.

## Emoji

One per heading at most, or none. They are decoration with a cost: they change
the heading's anchor, they render differently across platforms, and a reader
using a screen reader hears the emoji's name read out before the heading.

Emoji inside sentences read as a chat message. In an enterprise or scientific
context, leave them out entirely.

## Composition defects

Ranked by how much they cost the reader:

1. The first sentence sits below a banner, a badge wall, an animation and a
   video, so a visitor scrolls before learning what the project is.
2. A visual that shows nothing: a generic hero image, a screenshot of an empty
   state, a logo at four different sizes.
3. A broken image or a badge for a service that no longer exists — read as
   abandonment faster than any sentence in the prose.
4. Every section wrapped in `<details>`, so the page is a list of closed
   drawers.
5. Template text left in place: `project_title`, `github_username`, "Use this
   space to show useful examples".
6. Sections with a heading and no content, or marked "coming soon". Delete the
   heading; an empty promise is worse than an absence.
7. A wall of unbroken paragraphs with no code block, list or heading for
   thirty lines.
8. Decorative separators between every section, which add length and remove
   nothing.

## Review checklist

- [ ] A reader who does not scroll learns what this is.
- [ ] The tagline matches the repository description and the manifest
      description.
- [ ] At most one visual above the first code block, and it shows real output.
- [ ] Every image has a sentence of `alt` text, an explicit `width`, and a
      file that exists in the tree.
- [ ] Dark-mode pairs have an `<img>` fallback carrying the alt text.
- [ ] Nothing a first-time reader needs is collapsed.
- [ ] At most one or two alerts, none adjacent.
- [ ] Any diagram's claim also appears in text.
- [ ] Table of contents only if the page is long, built from heading links,
      with the slugs checked.
- [ ] No centred prose, no "back to top" links, no empty sections, no
      placeholder text.

<!-- sources: github-writing-docs, standard-readme, awesome-readme-skill, google-devdocs-style, mblode-docs-writing -->
