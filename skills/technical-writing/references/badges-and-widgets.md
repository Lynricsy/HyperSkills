# Badges and third-party widgets

Verified against: shields.io, GitHub's image proxy, and the `github-readme-stats`
and `contrib.rocks` services.

## Contents

- [What a badge actually is](#what-a-badge-actually-is)
- [How stale a badge is](#how-stale-a-badge-is)
- [Which badges earn the first screen](#which-badges-earn-the-first-screen)
- [How many](#how-many)
- [Style](#style)
- [Failure modes](#failure-modes)
- [Checking badges](#checking-badges)
- [Static badges](#static-badges)
- [Third-party widgets](#third-party-widgets)
- [Writing the markup](#writing-the-markup)
- [Review checklist](#review-checklist)

## What a badge actually is

A badge is an SVG image, generated on request by a service you do not run,
fetched through the hosting surface's own image proxy, and cached at two
levels before a reader sees it. Every badge in a README is therefore a live
dependency on somebody else's uptime, and a claim whose freshness is bounded
by a cache you do not control.

That is the whole basis for judging them. A badge is worth its dependency when
it answers a question a reader has *before* reading the page — is this
maintained, which version will I get, may I use it, does it build — and is not
worth it otherwise.

Both GitHub and PyPI fetch badge images through their own proxy rather than
letting the reader's browser call the badge host, so on those surfaces the
badge host does not see your readers. [verified] The reasons to prefer a
committed image over a hosted badge are the cache and the outage, not
tracking.

## How stale a badge is

Measured from the `Cache-Control` headers the services actually send. The
number is the longest a reader can see the previous value.

| Badge | Time to live |
|---|---|
| GitHub Actions workflow status | 60 s |
| npm version | 5 min |
| GitHub stars | 30 min |
| PyPI version | 3 h |
| GitHub licence | 4 h |
| shields static badge | 5 days |
| `contrib.rocks` contributor image | 3 days |
| GitHub's image proxy, on top of the above | 2 min |

[verified]

Two consequences. A build badge is close to live, so a red one is real and
worth acting on. A licence or version badge is not: after relicensing or
releasing, the badge keeps asserting the old value for hours, and asking the
service to shorten its cache does not work — a `cacheSeconds` parameter below
the service's own minimum is ignored. [verified]

## Which badges earn the first screen

For each candidate, name the question it answers and the decision it changes.
If you cannot, it is decoration.

| Badge | Question it answers | Keep it when |
|---|---|---|
| Build status | Is `main` green right now? | CI exists and runs on `main`. Point it at the real workflow file. |
| Released version | What do I get if I install today? | The package is published. |
| Licence | May I use this at work? | Always, if the project has a licence. |
| Coverage | How much of this is tested? | Coverage is actually measured and reported. |
| Downloads | Is anyone using this? | The number is large enough to mean something. A badge reading 40/month argues against you. |
| Chat, sponsors, social | Where do I get help? | The destination exists and someone answers there. |

A badge for something the project does not do is worse than a missing badge: a
coverage badge on a project with no coverage job renders as an error and tells
the reader the maintainers do not read their own page.

Language and framework badges ("Built with Python", "Built with Redis") are
static images that repeat what the install command and the code already say.
They belong in a "Built with" list if anywhere, never in the first row.

## How many

Any fixed number is arbitrary. Three properties bound the count, and they are
checkable:

- **Fold.** Badges sit above the first sentence. Count the lines the badge
  block occupies on a narrow window; if the sentence explaining the project is
  pushed off the first screen, there are too many.
- **Dependency.** Every dynamic badge is a service that can go down, rate-limit
  you, or shut down. Each one you keep is one you have agreed to check.
- **Discrimination.** Badges are read as a group. A row where every badge is
  green carries one bit: "somebody set these up". The signal comes from badges
  that could plausibly be red.

Applying those three to most projects lands on three to six: build, version,
licence, and whichever of coverage or downloads is true and non-trivial. Say
why each survives rather than quoting a cap.

## Style

shields.io accepts `flat` (the default), `flat-square`, `plastic`,
`for-the-badge` and `social`. `for-the-badge` upper-cases the label and the
message; `social` capitalises the label. An unrecognised `style=` value is
silently ignored and you get the default — so a typo produces a badge in the
wrong style with no error anywhere. [verified]

Pick one value and use it in every badge URL in the file, including the ones
you copied from another project's README. A row mixing `flat`, `plastic` and
`for-the-badge` is the most visible sign in a README that its parts were
pasted rather than chosen.

## Failure modes

A badge service does not return an error page when you get the URL wrong. It
returns HTTP 200 and a perfectly rendered badge containing the error text:

- an unknown path renders `404: badge not found`;
- a real path with a repository that does not exist renders, for example,
  `release: no releases or repo not found`. [verified]

So a link checker that follows every URL and reports non-200 responses passes
a README full of broken badges, and the reader sees the failure text sitting
in the badge row. The same applies to the spelling of the path itself:
`github/licence/...` is not a shields endpoint, and it fails this way.

The other failure modes:

- The upstream service is down, rate-limited, or gone. The badge becomes a
  broken image, and a broken image at the top of a README reads as an
  abandoned project. Services do disappear; the badge outlives them.
- The badge is dynamic but the fact is not. A hand-written
  `version-2.1.0-blue` badge is a version number in a second place, which
  drifts from the manifest exactly the way any duplicated fact does.
- The link behind the badge points somewhere unhelpful, or nowhere. Every
  badge should be a link to the thing it reports on: the workflow run list,
  the package page, the licence file.

## Checking badges

Status codes tell you nothing. Read the rendered text:

```sh
grep -o 'https://img\.shields\.io/[^)"]*' README.md | sort -u | while read -r url; do
  printf '%s -> ' "$url"
  curl -s "$url" | grep -o '<title>[^<]*</title>'
done
```

Anything whose title contains `not found`, `invalid`, `inaccessible` or `error`
is broken. Run this whenever the README changes and before a release.

Also check what the badge asserts. A licence badge that reads `MIT` against an
`Apache-2.0` file is a legal claim that is wrong, and it usually means the
badge was copied from the project the README was copied from.

## Static badges

A static badge — `img.shields.io/badge/LABEL-MESSAGE-COLOR` — is a picture of
a string. It is the right choice for something true and unchanging, such as a
status marker (`status-experimental-orange`) or a standard the project follows.
It is the wrong choice for anything the project can change, because nothing
will update it.

A static badge can also be committed as an SVG in the repository. That removes
the outage and the cache at the cost of never changing. Worth it for a project
whose README is read on surfaces you do not control.

## Third-party widgets

These are images generated by small community services, usually hosted on a
free tier by one person.

| Widget | What it shows | What it costs |
|---|---|---|
| `github-readme-stats` | Commit, star and language cards | The public instance is documented by its own maintainers as best-effort and subject to rate limits and traffic spikes; they recommend self-hosting or generating the card in a workflow. Its default cache is 24 h for the stats card, 6 days for top languages, 10 days for pinned repositories, so the numbers are not current. [official] |
| `contrib.rocks` | A grid of contributor avatars | A single image with a 3-day cache. [verified] The same information is one click away on the contributors page, which is always current. |
| `star-history` | Star count over time | Meaningful only for a project whose growth is the point. On a young project it draws a flat line at the top of the page. |
| Typing-animation SVGs | An animated tagline | Replaces the one line that has to be readable with an animation that is not selectable, not searchable, and empty when the service is down. |
| Visitor counters | A hit count | Several of these services have shut down over the years; the badges remain in thousands of READMEs as broken images. |

None of them answer any of the four questions a README exists to answer. They
are also the elements most likely to sit above the first sentence, so they pay
their cost in the most expensive place on the page.

Where one is genuinely wanted — a contributor wall on a project whose
contributors are the story — put it near the bottom, and know that it may be a
dead image the day the service stops.

## Writing the markup

Badges go directly under the title, with no heading of their own, one per
line in the source. [community] A badge with no link is a dead end: wrap each
one in the link to what it reports.

For more than three or four, reference-style definitions keep the top of the
file readable, with the definitions at the bottom:

```markdown
[![Build][build-badge]][build-url]
[![npm][npm-badge]][npm-url]
[![Licence][licence-badge]][licence-url]

[build-badge]: https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?branch=main
[build-url]: https://github.com/OWNER/REPO/actions/workflows/ci.yml
```

Put the definitions at the end of the file, not the beginning: a reader who
opens the raw Markdown should see the title first, not twenty URLs.

Give each badge `alt` text that reads as a fact — `Build status`, `Licence:
Apache-2.0` — because that is the string a screen reader announces and the
string that remains when the image fails.

## Review checklist

- [ ] Every badge answers a question a reader has before reading.
- [ ] No badge claims something the project does not do.
- [ ] Every badge URL was fetched and its rendered title read, not its status
      code.
- [ ] One shields `style=` value across the whole file.
- [ ] Every badge links to what it reports on.
- [ ] The badge block does not push the first sentence off the screen.
- [ ] No badge for a service that no longer exists.
- [ ] Third-party widgets, if any, are below the content, and their staleness
      is acceptable.
- [ ] Reference-style definitions, if used, are at the bottom of the file.

<!-- sources: shields, github-readme-stats, standard-readme, awesome-readme-skill -->
