# One README, several renderers

Verified against: GitHub's rendered-README pipeline, PyPI's `readme_renderer`,
and the npm package page.

## Contents

- [The premise](#the-premise)
- [Which file each surface renders](#which-file-each-surface-renders)
- [The support matrix](#the-support-matrix)
- [Anchors: the one mechanism that travels](#anchors-the-one-mechanism-that-travels)
- [Relative paths](#relative-paths)
- [The portable subset](#the-portable-subset)
- [GitHub-only constructs and their fallbacks](#github-only-constructs-and-their-fallbacks)
- [What is always stripped](#what-is-always-stripped)
- [Limits worth knowing](#limits-worth-knowing)
- [How to check instead of guessing](#how-to-check-instead-of-guessing)
- [Review checklist](#review-checklist)

## The premise

A README is usually written while looking at one renderer and read on several.
The same file becomes the repository landing page, the PyPI project page, the
npm package page, the Go or Rust doc page, whatever a mirror or an internal
portal shows, and a Markdown preview in an editor. Each of those runs its own
parser and its own HTML sanitiser, and they disagree.

The disagreement is not cosmetic. Constructs that carry the reader's first
impression — the table of contents, the dark-mode logo, the alert that says
"version 3 changed the default" — are exactly the constructs that differ. A
README that only ever got looked at on the forge can be quietly broken on the
page where most of its readers actually land.

So the first question about any piece of README markup is not "does this look
good", it is "where is this file rendered, and what happens to this construct
there".

## Which file each surface renders

Forges and registries do not pick the same file, and they do not pick it the
same way.

- GitHub surfaces a README from the `.github` directory first, then the
  repository root, then `docs`. A repository with both `.github/README.md` and
  `README.md` shows only the first; the root file becomes the one nobody
  sees. [official]
- Package registries render the file the manifest names, not the file GitHub
  chose: `readme` in `pyproject.toml`, the README that the npm tarball
  contains. A repository whose real README moved into `.github` publishes an
  empty or stale description.
- Nothing outside the forge knows about the repository at all. The renderer
  receives Markdown text and a base URL that is not your repository.

## The support matrix

Measured, not assumed. "stripped" means the tag or attribute is removed and its
content is either dropped or flattened into surrounding text.

| Construct | GitHub | PyPI | npm |
|---|---|---|---|
| `align="center"` on `div`, `p`, `h1`–`h6`, `td`, `img` | kept | kept | kept |
| `style=`, `class=` attributes | stripped | stripped | — |
| `<style>`, `<script>`, `<iframe>` | stripped | stripped | — |
| `<center>`, `<font>`, `<marquee>` | stripped | stripped | — |
| `<img width= height= align= alt= title=>` | kept | `width`/`align` kept | kept |
| `<img loading="lazy">` | attribute stripped | attribute stripped | — |
| `<details>` / `<summary>`, including the `open` attribute | element kept, `open` kept | element kept, **`open` stripped — a block you meant to ship expanded arrives collapsed** | element kept |
| `<picture>` with `<source>` | kept | **`<source>` stripped** | kept |
| `<video>` | kept | **stripped entirely** | — |
| `<kbd>`, `<sub>`, `<sup>`, `<br>`, `<hr>`, tables | kept | kept | kept |
| Task lists `- [x]` | kept | kept | — |
| Footnotes `[^1]` | kept | — | — |
| Alerts `> [!NOTE]` | styled callout | styled admonition | **literal `[!NOTE]` in a plain blockquote** |
| ` ```mermaid ` | rendered diagram | **source-code block** | **not a diagram** |
| Heading anchors | generated, but the `id` is `user-content-` prefixed while the permalink `href` is bare | generated, `id` and `href` both prefixed, so they match | **not generated: every `#` link is dead** |
| Images from other hosts | proxied through `camo.githubusercontent.com` | proxied through `pypi-camo` | proxied through camo |

`—` means not measured on that renderer; treat it as unknown rather than
supported. [verified]

The single most damaging row is the alert. On npm, `> [!WARNING]` renders as an
ordinary blockquote whose first line is the literal text `[!WARNING]`, so the
one construct authors reach for to flag a breaking change reads as a typo on
the page where upgraders see it. [verified]

## Anchors: the one mechanism that travels

Three renderers, three different treatments of in-page links.

GitHub rewrites every author-supplied `id`/`name` to a `user-content-` prefix
and leaves `href="#..."` alone. Its own generated heading permalinks are built
the same way: on a live repository page the anchor elements carry
`id="user-content-<slug>"` while every permalink `href` is the bare `#<slug>`.
The rendered HTML therefore never resolves a fragment by `id` on its own, on
github.com or anywhere else. [verified] How github.com itself reconciles the
two at click time was not measured here; do not build a rule on the mechanism,
only on the markup.

PyPI rewrites the other end: `href="#x"` becomes `href="#user-content-x"`, a
heading's generated `id` is prefixed to match — but an author's own
`<a id="x">` keeps its original `id`, and `<a name="x">` loses the attribute
outright. Hand-written anchors therefore break there, silently.

npm generates no heading anchors at all, so every `#` link in the file is dead.

What survives: a link to a Markdown heading, on the renderers that generate
heading anchors at all. What does not survive: `<a name="readme-top"></a>`
paired with "back to top" links. That construct is officially documented for
GitHub, and it is also what the most-copied README template in existence uses —
its live page serves nine `href="#readme-top"` against one element with
`id="user-content-readme-top"` and none with `id="readme-top"`, and on PyPI the
same construct is measurably broken: an author's `id` is left unprefixed while
the link pointing at it is prefixed. Popularity is not portability. [verified]

Slugs are generated by a rule that surprises people: letters lower-cased,
spaces replaced by hyphens, everything else removed. An emoji is "everything
else", but the space after it is a space, so `## 🚀 Quick Start` produces
`#-quick-start` with a leading hyphen — not `#quick-start`. [official] An emoji
heading plus a hand-written table of contents is one of the commonest sources
of dead links in a README.

Two ways out, both fine: keep the emoji and write the hyphen, or keep the table
of contents and drop the emoji. GitHub already generates an outline from the
headings, so on that surface a hand-written table of contents is a second copy
of something the reader already has. [official]

## Relative paths

GitHub's documentation recommends relative links and relative image paths,
because they survive forks and clones and GitHub rewrites them against the
current branch. [official] Registries do no such rewriting: the link is emitted
as written and resolves against the registry's own URL, so
`![diagram](docs/arch.png)` on a PyPI page asks pypi.org for a file it does not
have. [verified]

Both sources are right about their own surface, so the rule is conditional on
where the file is published:

- README read only on the forge — relative paths.
- README also published as a package description — absolute URLs into the
  repository for every image and every link, or no images and no cross-file
  links at all.

Pin absolute URLs to a tag or a commit rather than to a moving branch: a
description published with a release keeps pointing at the tree that release
shipped with.

## The portable subset

Use these without thinking about the renderer: Markdown headings, paragraphs,
lists, tables, fenced code blocks with a language tag, links, images,
blockquotes, `<br>`, `<hr>`, `<kbd>`, `<sub>`, `<sup>`, `<details>` with
`<summary>`, `<div align>` / `<p align>` for centring, `<img>` with `alt`,
`width` and `align`, and links to Markdown headings.

Centring is the whole of the layout toolkit. `style=` and `class=` are stripped
everywhere, `<center>` is stripped everywhere, so `align` is the only way to
move anything off the left margin. Any advice that implies otherwise — custom
fonts, column layouts, colour — is describing something no renderer will
show. [verified]

## GitHub-only constructs and their fallbacks

Each of these is worth using on GitHub. None may carry information that the
reader loses when it disappears.

| Construct | Elsewhere | Fallback to write alongside it |
|---|---|---|
| `> [!NOTE]` / `> [!WARNING]` | plain blockquote, and on npm the marker text shows | Put the meaning in the first words: `> **Breaking in 3.0.** …`. It reads correctly everywhere and degrades to bold text. |
| ` ```mermaid ` | a block of diagram source | Export the diagram and commit it; embed the image. Keep the mermaid source in `docs/` if you want it diffable, not in the README. |
| `<video>` | stripped | An animated GIF, or a poster image linking to the video. |
| `<picture>` + `<source media="(prefers-color-scheme: dark)">` | `<source>` may be dropped | The `<img>` inside is not optional: it is what everyone else sees. Make it the light-mode asset with real `alt` text. [official] |
| `<details open>` | collapses anyway | Do not put anything a first-time reader needs inside `<details>` at all. |
| Footnotes, task lists, `geojson`/`topojson`/`stl` blocks | unpredictable | Keep them out of the README; they belong in issues and docs pages. |
| GitHub's generated outline | absent | If navigation matters off the forge, write the table of contents by hand with heading-slug links and accept that it is plain text on npm. |

## What is always stripped

`<style>`, `<script>`, `<iframe>`, `style=`, `class=`, `<center>`, `<font>`,
`<marquee>`, and `loading="lazy"`. Writing them is not a risk, it is a no-op:
the page renders as if the markup were absent, which is how a "carefully
designed" README ends up left-aligned and unstyled everywhere. [verified]

## Limits worth knowing

- GitHub truncates the rendered README past 500 KiB. [official]
- Images and GIFs uploaded to GitHub are capped at 10 MB; video at 10 MB on
  free plans and 100 MB on paid ones. Supported media are PNG, GIF, JPEG, SVG
  and `.mp4`/`.mov`/`.webm`, with H.264 recommended for browser
  compatibility. [official]
- Images from other hosts are fetched by the surface's own proxy, not by the
  reader's browser, on GitHub, PyPI and npm alike. The third-party host sees
  the proxy, not your readers. Do not justify inlining a badge as a privacy
  measure on those three surfaces; justify it by the proxy's cache and by what
  happens when the host is down. [verified]

## How to check instead of guessing

Do not preview a README in one place and call it verified.

```sh
# GitHub, in repository context: the same pipeline the repo page uses.
gh api repos/OWNER/REPO/readme -H 'Accept: application/vnd.github.html+json' > rendered.html

# GitHub, for a file not yet committed.
gh api /markdown -f mode=gfm -f text="$(cat README.md)"

# PyPI, using the library PyPI itself renders with.
uv run --with 'readme_renderer[md]' python -c \
  "from readme_renderer.markdown import render; print(render(open('README.md').read()))"

# PyPI, as part of the upload check.
twine check dist/*
```

Then grep the output rather than reading it: every `href="#..."` in the
rendered HTML should have a matching `id=`, and every `<img src=` should be a
URL that resolves from outside the repository.

## Review checklist

- [ ] The file the registry publishes is the file you edited.
- [ ] No `style=`, `class=`, `<style>`, `<center>`, `<font>` or `<marquee>`.
- [ ] Centring uses `align` only.
- [ ] No `<a name>`/`<a id>` anchor scheme and no "back to top" links.
- [ ] Every in-page link targets a Markdown heading, with the slug the heading
      actually generates, emoji included.
- [ ] Every `<picture>` contains an `<img>` with `alt` text.
- [ ] Every mermaid diagram, alert and `<video>` still makes sense when it
      degrades.
- [ ] Relative paths only if the file is never published to a registry;
      otherwise absolute URLs pinned to a tag.
- [ ] Nothing a first-time reader needs is inside `<details>`.
- [ ] Rendered through at least the two renderers that matter for this project,
      and the output was checked, not eyeballed.

<!-- sources: github-writing-docs, pypa-readme, standard-readme, awesome-readme-skill -->
