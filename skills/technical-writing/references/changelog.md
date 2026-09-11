# Changelogs

Verified against: Keep a Changelog 2.0.0.

## Contents

- [Who it is for](#who-it-is-for)
- [File frame](#file-frame)
- [The six types](#the-six-types)
- [Choosing between Fixed, Changed and Security](#choosing-between-fixed-changed-and-security)
- [Breaking changes](#breaking-changes)
- [Deprecation before removal](#deprecation-before-removal)
- [Writing an entry](#writing-an-entry)
- [What is not an entry](#what-is-not-an-entry)
- [Version links](#version-links)
- [Changelog against release notes](#changelog-against-release-notes)
- [Turning a commit log into a changelog](#turning-a-commit-log-into-a-changelog)
- [Automation](#automation)
- [Scale](#scale)

## Who it is for

A changelog is written for the person deciding whether and how to upgrade. Not
for the maintainers, not for the tooling, and not as a record of work done. The
test for every line: can a reader on the previous version act on it without
opening the diff. [official]

That single test decides most of the questions below. A merge commit fails it. A
line that says "switch default backoff" fails it, because the reader cannot tell
whether their code still runs. "Default `backoff` is now `full_jitter`; the old
`exponential` and `linear` values are rejected with `ValueError`" passes.

## File frame

Name it `CHANGELOG.md` at the repository root — a predictable name is why anyone
finds it. Open with a fixed preamble stating what the file is and which
conventions it follows, so both readers and tools know what to expect:
[official]

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-08-27

### Added
...
```

- Latest version first.
- Every version has an entry, and a date in `YYYY-MM-DD`. Not a regional
  format: `03/02/2026` is two different days depending on the reader.
- Keep an `Unreleased` section at the top permanently. At release time rename it
  and open a fresh empty one.
- Pin the Keep a Changelog link to the version you follow, so it stays true as
  that page changes.
- Semantic Versioning is not required. Calendar versioning, a plain counter or
  dates all work — but say which scheme you use, or readers cannot read your
  version numbers.
- A version may open with one or two sentences introducing the release. Optional;
  use it when there is a theme, skip it otherwise.
- A pulled release stays in the file, marked: `## [3.0.1] - 2026-06-02 [YANKED]`.

## The six types

`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Group entries
under the types that apply and omit the empty ones. [official]

Do not add types. `Improved` and `New` duplicate `Changed` and `Added`;
`Performance` is a `Changed`; `Internal` and `Housekeeping` are usually not
notable and should not be in the file at all. Six types means every changelog
in the ecosystem reads the same way and parses with the same tools; a seventh
buys one project a nuance and costs every reader the convention.

Two frequent requests that are not types:

- **Dependencies.** A dependency bump is harmless, a fix, or a break. If it
  affects users, describe its effect under the right type. If it does not, leave
  it out.
- **Known issues.** They are discovered, not changed. Note them on the affected
  version or in the tracker; when one is fixed it appears under `Fixed`.

## Choosing between Fixed, Changed and Security

The question that resolves it: **was the old behaviour a bug?** [official]

- Yes → `Fixed`. The behaviour was wrong and is now correct.
- No → `Changed`. It worked as intended and now works differently.
- It addressed a vulnerability → `Security`, regardless of which of the two it
  technically was, because the urgency and the audience differ.

Lead a `Security` entry with its identifier when it has one, so readers and
scanners can match it to the advisory:

```markdown
- CVE-2026-12345: out-of-bounds read when parsing a malformed Retry-After header.
```

## Breaking changes

Mark them. The version number already signals a major release, but the number is
easy to miss and a reader scanning `Changed` will not go looking. [official]

- A breaking change stays **inside the type it belongs to** — usually `Changed`
  or `Removed` — with a short `**Breaking:**` marker at the front of the entry.
  Do not collect breaks into a separate section: that is precisely the section a
  reader skimming `Changed` never opens, and it separates each break from the
  description of what replaced it.
- **Say which interface breaks.** "Breaking" means nothing until the reader
  knows which surface you keep stable: a library API, a command line, a network
  protocol, a file format, a configuration or environment surface, or the
  install itself. One release often breaks several, and a reader only cares
  about the ones they touch.

```markdown
### Changed

- **Breaking** (Python API): `Client.fetch(path)` is now
  `Client.request(method, path)`; the HTTP method is no longer implicit.
- **Breaking** (Python API): `max_retries` is now `max_attempts` and counts the
  first attempt. `max_retries=3` sent four requests; `max_attempts=3` sends three.
- **Breaking** (environment): the token is read from `CORRAL_TOKEN`, not
  `CORRAL_API_KEY`.

### Removed

- **Breaking** (Python API): `retry_on`. Retries now key off the status class
  and the `Retry-After` header.
- **Breaking** (install): the Redis limiter moved to an extra. Install
  `corral[redis]`.
```

A short upgrade action belongs in the entry itself — "rename the `color` option
to `theme`". When the procedure is substantial, link a migration guide instead.
A long procedure inside the changelog buries what changed and turns a scannable
record into a how-to guide for a narrower audience.

## Deprecation before removal

Announce in one release, act in a later one: `Deprecated` first, `Removed`
afterwards, naming the version that will remove it. Then anyone upgrading meets
the warning before the break. [official]

If a removal shipped with no prior deprecation, say so in the entry rather than
retrofitting a `Deprecated` line into a past release — the past release did not
warn anyone, and a changelog that claims otherwise is the one thing a changelog
cannot afford to be. Of everything in this file, deprecations, removals and
breaking changes are the entries that must never be omitted.

## Writing an entry

- One line, present tense, the user's vocabulary.
- Both names when something is renamed, in the entry, so the reader can search
  their own code for the old one.
- The observable effect where the name alone does not convey it (see the
  `max_attempts` example above).
- The reason, when it is short and not obvious.
- No issue-number soup. Prose with an occasional reference beats a list of bare
  `(#1234)`; pull-request numbers belong to one forge, tags and commits travel
  with the repository. Collect such links as reference-style links at the bottom
  of the file.

## What is not an entry

Delete these on sight — each one costs a reader a line and tells them nothing:

| Line | Why |
|---|---|
| `Merge pull request #214 from acme/limiter-tidy` | A branch operation, not a change. |
| `wip`, `typo`, `lint`, `fix CI`, `update tests`, `bump version` | Not user-visible. |
| `address review comments` | Records the process, not the product. |
| `remove dead code in limiter.py` | Internal; nothing a user can observe changed. |
| `refactor Client.__init__` | Internal unless behaviour changed — and if it did, the entry should say what. |
| `README tweaks` | Documentation-only changes are notable when they correct a documented behaviour; otherwise they are noise. |

Curation is the work. A changelog records *notable* changes, which means
deciding what is not notable, and that judgement is the part no tool does.
[official]

## Version links

Make every version a Markdown reference link resolving to a comparison with the
one before it, collected at the bottom of the file:

```markdown
[Unreleased]: https://github.com/acme/corral/compare/v3.1.0...HEAD
[3.1.0]: https://github.com/acme/corral/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/acme/corral/compare/v2.4.1...v3.0.0
[2.4.0]: https://github.com/acme/corral/releases/tag/v2.4.0
```

`Unreleased` compares the last tag to `HEAD`; the oldest version points at its
own tag, since there is nothing earlier to compare with. Every forge exposes tag
and comparison URLs, so the pattern is portable, and keeping the URL out of the
heading keeps the file readable as plain text.

## Changelog against release notes

They are not the same document and they draw on the same material. The changelog
is the complete ongoing record, in the repository, written plainly for anyone.
Release notes are an announcement for one version: a selection of its headline
changes, often with upgrade steps and a promotional voice, published when that
version ships. [official]

Derive the notes from the changelog, not the other way round, and do not
maintain both by hand: at release time that version's section is already the
draft. Because every version sits under a predictable `## [x.y.z]` heading, a
few lines of scripting can extract it.

Keep `CHANGELOG.md` canonical even when the forge offers to generate notes for
you. What a forge generates lives in its database, not in your repository: it
does not travel when the project moves, and it is gone the day you leave. Use
the forge for reach — notifications, a visible page, attached artefacts — and
keep the record in a file you own.

The mechanics of cutting the release itself — tagging, publishing, attaching
artefacts — are the `github` skill and the `git-workflow` skill.

## Turning a commit log into a changelog

When handed a file that is a commit dump, work in this order:

1. **Drop the non-entries** from the table above. Usually half the lines.
2. **Group the survivors by version**, keeping the versions the file already
   has; get their dates from the tag list rather than guessing.
3. **Sort each version's entries into the six types.** Anything that resists is
   usually internal — check whether a user can observe it at all.
4. **Rewrite each line for the upgrader**: old and new names, observable effect,
   reason where short.
5. **Mark the breaks** and name the interface each one breaks.
6. **Check for undeclared breaks**: read the source for renames and removed
   parameters and confirm each one appears. A commit log's own wording routinely
   hides a break as a tidy-up — "remove dead code", "switch default", "rename
   for consistency".
7. **Add the frame**: heading, preamble, `Unreleased`, comparison links.
8. **State what you could not determine** rather than inventing it: an exact
   date, whether something was ever deprecated, whether a change was
   user-visible.

## Automation

A model can draft a changelog from a diff in seconds, and that is a legitimate
first draft. It cannot decide what is notable for your readers. Machines draft;
humans curate. [official]

Generating entries from commit messages assumes every commit belongs in the
changelog and that the right entry is a reworded commit message. Usually it is
neither: most commits do not matter to readers, and the changes that do often
span several commits and need describing from the reader's point of view.
Conventional Commits and the tools that read them give you raw material, not a
changelog.

Keep CI in a supporting role: move `Unreleased` into a dated section at release
time, check the file's shape, optionally remind a contributor that a change may
need an entry. Do not make a changelog edit a required check on every pull
request — that teaches people to add a line to pass the check, and fills the
file with the noise this page is about removing.

## Scale

One file is usually fine, however long. If it becomes unmanageable, move old
history into archive files and link the main file and the archives in both
directions, or readers will not find the older entries. Archive only versions
old enough that they will not need editing, and never delete old entries:
someone is still upgrading from one of them.

In a monorepo of unrelated projects, each keeps its own changelog. For one
product split into components, keep a changelog per component **and** a central
one — readers should not have to read a dozen component files to learn what a
release means.

<!-- sources: keep-a-changelog, copilot-docs, google-devdocs-style -->
