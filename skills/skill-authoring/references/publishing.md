# Packaging, distribution and provenance

How a skill gets from a repository into an agent, and what has to be recorded on
the way.

## Contents

- Repository layout
- Why flat
- Self-contained skills
- The installer
- Repository scan rules
- Plugin manifests
- Installation scope and method
- Validation in continuous integration
- Licensing the skill
- Licensing vendored material
- Recording provenance
- Generated attribution
- Checking upstreams for drift
- Release checklist

## Repository layout

```
repo/
├── skills/
│   ├── <skill-a>/
│   │   ├── SKILL.md
│   │   ├── SOURCES.yaml        # provenance, if the skill adapts upstream work
│   │   ├── NOTICE.md           # generated attribution
│   │   ├── references/
│   │   ├── scripts/
│   │   ├── assets/
│   │   └── evals/
│   │       ├── evals.json
│   │       └── files/
│   └── <skill-b>/              # identical internal structure
├── .claude-plugin/
│   └── marketplace.json        # generated distribution manifest
├── LICENSE
└── THIRD_PARTY_NOTICES.md      # generated aggregate of every NOTICE.md
```

Every skill has the same internal shape. The uniformity is not tidiness: it is
what lets a validator, a catalogue generator and an evaluation runner treat all
skills identically instead of special-casing each one.

## Why flat

One directory per skill, directly under the container directory. No category
subdirectories.

Two reasons, both mechanical. A skill's identity is the directory holding
`SKILL.md`, so a category directory contributes nothing to it. And selecting a
skill by name at install time is unambiguous only when names are unique in one
flat namespace.

Categorisation still works — as a frontmatter `metadata` field and a generated
index table. That gives the same grouping without putting it in a path that
installers, hosts and users all have to agree about.

## Self-contained skills

No file inside a skill may reference a path outside it. Installers copy or
symlink one skill at a time into an agent directory, so a relative path that
climbs out of the skill root resolves to nothing once installed.

When two skills need the same helper, duplicate the small helper rather than
introducing a shared tree. Duplication costs a file; a broken relative path
costs the whole skill, silently, only for the users who installed it alone.

## The installer

The de facto installer is `npx skills`. Source formats it accepts:

```bash
npx skills add owner/repo                                   # GitHub shorthand
npx skills add https://github.com/owner/repo                # full URL
npx skills add https://github.com/owner/repo/tree/main/skills/name   # one skill
npx skills add https://gitlab.com/org/repo                  # any git host
npx skills add git@github.com:owner/repo.git                # SSH
npx skills add ./my-local-skills                            # local path
```

Useful flags: `--list` to enumerate without installing, `--skill <name>` (repeatable,
`'*'` for all), `--agent <agent>` (`'*'` for all, `universal` for the shared
directory), `-g` for user scope, `--copy` instead of symlinking, `-y` for
non-interactive use.

Other subcommands: `use` (generate a prompt for one skill without installing),
`list`, `find [query] [--owner org]`, `update`, `remove`, `init`.

Direct download URLs also work, pointing at a single `SKILL.md` or an archive.
Limits apply: 10 MiB download, 25 MiB extracted, 1000 files, each overridable by
an environment variable.

## Repository scan rules

Worth knowing exactly, because they determine whether a layout is discoverable
at all:

- The installer walks a fixed list of container directories, which includes the
  repository root (if it holds `SKILL.md`), `skills/`, its `.curated`,
  `.experimental` and `.system` subdirectories, `.agents/skills/`,
  `.claude/skills/` and roughly fifty other host directories.
- Each container is walked **up to three levels deep**, so a flat layout and a
  one- or two-level catalogue layout both resolve.
- A `SKILL.md` found at a shallower level **shadows** anything nested beneath it.
  A stray `SKILL.md` at a container root hides every skill under it.
- `--full-depth` additionally finds skills outside the container directories.
- If nothing is found in the standard locations, a recursive search runs as a
  fallback — convenient, and not something to rely on.

Only the skill root may contain a `SKILL.md`. Shadowing protects the installer,
but it does not protect every host: Cursor scans recursively and treats any
directory holding a `SKILL.md` as a skill in its own right. A test fixture at
`evals/files/SKILL.md` therefore ships a second, broken skill named `files`,
carrying whatever `name` the fixture declares. Name such fixtures for what they
are — `widget-builder-SKILL.md` — and assert the count after installing:

```bash
find .agents/skills -name SKILL.md | wc -l   # must equal the number of skills
```

## Plugin manifests

A `.claude-plugin/marketplace.json` (or `plugin.json`) declares skills
explicitly, and the installer reads it too. Paths declared there are searched at
their declared depth and are exempt from the three-level walk.

```json
{
  "name": "example",
  "owner": {"name": "org"},
  "plugins": [
    {
      "name": "<skill>",
      "description": "<short description>",
      "source": "./",
      "skills": ["./skills/<skill>"]
    }
  ]
}
```

Generate this file from the skills on disk rather than maintaining it by hand.
A manifest that drifts out of sync with the tree is worse than no manifest,
because it silently publishes a stale set.

## Installation scope and method

| Scope | Location | When |
|---|---|---|
| Project | `./<agent-dir>/skills/` | Committed with the project, shared with the team |
| User | `~/<agent-dir>/skills/` | Available across all of one person's projects |

Symlinking is the default and gives one canonical copy that updates in place.
Copying is for environments where symlinks do not work, and for verifying that a
skill really is self-contained — a copy exposes every path that reached outside
the skill directory.

## Validation in continuous integration

Run the checks on every change, not once before publishing. Mechanical checks
worth wiring up:

- The reference validator, for frontmatter and naming.
- Line-count gates for the body and for each reference file.
- The frontmatter `name` equals the directory name.
- Every bundled file is referenced from `SKILL.md`, and nothing referenced is
  missing.
- No reference-to-reference link, and no reference more than one level deep.
- No host-specific runtime construct in the body.
- Scripts compile, and their declared dependencies resolve.
- `evals/evals.json` parses, has at least three scenarios, and at least one
  negative.
- Generated files — attribution, manifest, index — match what the generator
  would produce now.

Two of these are worth the extra effort because they fail silently otherwise:
the generated-file check, which catches a hand edit to a generated file, and the
unreferenced-file check, which catches the dead weight that accumulates as a
skill is revised.

## Licensing the skill

Own content gets a licence, and the frontmatter `license` field says which. A
short value is enough (`MIT`), or a pointer to a bundled file when the terms are
not a standard identifier.

A skill that vendors material from elsewhere needs both: the field for its own
terms, and an attribution file for everything it adapted.

## Licensing vendored material

Determine the licence **per skill directory**, not per repository. Large
collections routinely publish a permissive licence at the root and a different
one — sometimes proprietary — inside individual skill directories, and the
repository-level metadata will not show it.

| Upstream status | What is permitted |
|---|---|
| Permissive open source (MIT, Apache-2.0, BSD, MPL) | Adapt and merge, with attribution. MPL keeps file-level obligations on the files that carry its header |
| Share-alike (CC-BY-SA) | Take the structure and the checklist semantics, rewrite every word, record the licence. Do not copy text |
| No licence at all, publicly available | Judgement call under the project's own policy; if merged, record that no grant exists and attribute prominently |
| Proprietary or source-available with a no-derivatives clause | Read it for coverage only. It contributes a topic list, never text, never a script, never a data file |

The proprietary case is the one that needs discipline, because such skills are
often the highest quality in their area. Use them to answer "what must a skill
in this area cover", then write the coverage independently. Record the
relationship as reference-only, so a later reader does not assume the content
was adapted.

Facts are not copyrightable, and the gotchas that make a good skill are mostly
facts. Their wording and their organisation are not. Independent phrasing from
the vendor's own documentation plus local verification produces a skill that
owes nothing to a restrictively licensed upstream.

## Recording provenance

One machine-readable record per skill, so a future maintainer can answer three
questions: where did this come from, at what version, and under what terms.

```yaml
skill: <name>
version: "YYYY.MM.DD"
upstreams:
  - id: <stable-slug>
    kind: repo                 # repo | docs
    repo: owner/name
    url: https://github.com/owner/name
    paths: [path/inside/repo]
    ref: main
    commit: <40-hex sha at the time the content was read>
    license: <SPDX id, or NONE, or Proprietary>
    relation: merged           # merged = rewritten in; reference = read only
    synced_at: "YYYY-MM-DD"
    contributes: "<what this upstream gave the skill>"
    notes: "<licence caveats, conflict rulings>"
```

The `commit` field is what makes the record useful. A reference to a branch
answers "where from" but not "which version", so it cannot support a diff later.
Pin the commit at the moment the content is read, mechanically, not by hand.

`relation` carries the licence decision: `merged` means text was adapted,
`reference` means nothing was copied. A proprietary upstream can only ever be
`reference`.

Per-reference-file attribution is worth adding too — a trailing comment naming
the upstream ids that fed that file. It makes an upstream change traceable to
the specific files that need re-reading, instead of the whole skill.

## Generated attribution

Generate the human-readable attribution from the provenance record; never
maintain both by hand.

```
# NOTICE — <skill>

This skill is a curated rewrite. It adapts material from:

- <repo> (<licence>) — <url> @ <commit> — paths: <paths> — <contributes>

Reference-only sources (no content copied):
- <repo> (<licence>) — <url>
```

Note the second section. Separating reference-only sources from adapted ones is
what keeps the attribution honest in both directions: it credits the influence
without claiming a licence relationship that does not exist.

## Checking upstreams for drift

A vendored skill decays. Automate the check:

1. For each upstream, fetch the current head of the tracked ref.
2. Compare with the pinned commit; equal means nothing to do.
3. Otherwise list the commits since the pin that touched the recorded paths, and
   print a comparison link.
4. Re-read the changed files, apply the same conflict rules that were used
   originally, then re-pin and re-date.
5. Re-run the evaluations. An upstream change that alters a rule invalidates the
   evidence, not just the text.

Re-check the **licence** on every sync, not only the content. A skill directory
whose licence changed from permissive to proprietary has to be downgraded to
reference-only and its affected sections rewritten — and nothing will announce
that this happened.

## Release checklist

- [ ] Every skill validates mechanically, and the check runs in CI
- [ ] Generated files regenerated and committed
- [ ] Every upstream pinned to a commit, with its licence recorded
- [ ] Proprietary upstreams recorded as reference-only, with no adapted text
- [ ] Smoke-install into a scratch directory with the real installer, using
      `--copy` so path escapes surface
- [ ] The installed copy loads and its references resolve from the install path
- [ ] Version stamped, in the frontmatter and in the provenance record

<!-- sources: vercel-skills-cli, hyperskills-self, agentskills-spec, anthropic-skill-creator, claude-code-skills-docs -->
