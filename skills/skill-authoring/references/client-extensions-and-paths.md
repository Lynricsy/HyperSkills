# Host extensions, discovery paths and listing truncation

Everything in this file is **non-standard**. The specification defines six
frontmatter fields; every field below belongs to one host and is ignored — or
occasionally rejected — everywhere else. A skill meant to be portable uses none
of them.

Verified against: the Claude Code, Cursor and Codex skill documentation, and the
`npx skills` installer README, as published at the time of writing.

## Contents

- Why extensions are a trap
- Claude Code extensions
- Cursor extensions
- Codex extensions
- Installer-reserved metadata
- Body-level extensions
- Discovery paths per host
- Collision precedence
- Listing truncation budgets
- Capability differences worth knowing

## Why extensions are a trap

An extension field does not fail loudly. It sits in the frontmatter looking
authoritative while the host that is actually running ignores it. The damage is
not the wasted line — it is that the author believes activation is handled.

A frontmatter block containing a path-scoping field and a custom signals map,
on a host that supports neither, has *no* triggering logic at all: the
description was never written, because the fields appeared to cover it.

When a skill genuinely targets one host, keep the extension and say so in the
`compatibility` field, so the next reader knows why the skill is not portable.

## Claude Code extensions

Accepts every specification field (`license` and `compatibility` are accepted
but not acted on) plus the following. None of these work anywhere else.

| Field | Effect |
|---|---|
| `name` | Optional there; defaults to the directory name |
| `when_to_use` | Extra triggering context, appended to the description in the listing |
| `argument-hint` | Autocomplete hint for expected arguments |
| `arguments` | Named positional arguments for placeholder substitution in the body |
| `disable-model-invocation` | `true` keeps the skill out of automatic selection; user invocation still works |
| `user-invocable` | `false` hides it from the command menu; only the model may invoke it |
| `disallowed-tools` | Tools removed from the pool while the skill is active |
| `model` | Model override for the turn that invoked the skill |
| `effort` | Reasoning-effort override for that turn |
| `context: fork` | Runs the skill in a forked subagent context |
| `agent` | Which subagent type to use when forking |
| `background` | Whether a forked run is awaited or backgrounded |
| `hooks` | Hooks registered when the skill is invoked |
| `paths` | Glob patterns limiting automatic activation to matching files |
| `shell` | Shell used for inline command execution in the body |

The vendor's own documentation states plainly that outside its product only the
specification fields may be used. Take that at face value.

## Cursor extensions

| Field | Effect |
|---|---|
| `paths` | Glob patterns (comma-separated string or list) scoping the skill to matching files; legacy name `globs` still accepted |
| `disable-model-invocation` | `true` makes the skill explicit-invocation only |
| `icon` | Badge icon when the skill backs a custom mode |
| `color` | Badge colour, from a fixed palette |

Note the collision: `paths` and `disable-model-invocation` exist in both this
host and Claude Code with compatible meanings, which makes them the least
dangerous extensions — and still not portable to the rest.

## Codex extensions

Codex adds no frontmatter keys. Host-specific configuration goes in a sibling
file, `agents/openai.yaml`:

```yaml
interface:
  display_name: "User-facing name"
  short_description: "User-facing description"
  icon_small: "./assets/small-logo.svg"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt"

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: "mcp"
      value: "someServer"
      transport: "streamable_http"
      url: "https://example.com/mcp"
```

`allow_implicit_invocation` defaults to `true`; setting it `false` restricts the
skill to explicit invocation. Because this lives outside `SKILL.md`, it is the
least invasive form of host-specific configuration: other hosts simply never
read the file.

## Installer-reserved metadata

The `npx skills` installer reserves exactly one repository-declarable value:

```yaml
metadata:
  internal: true
```

An internal skill is hidden from listing and installation unless an environment
variable opts in. Useful for work in progress; there is no other repository-level
manifest, because the layout *is* the manifest.

## Body-level extensions

These are host-specific mechanics in the Markdown body, not the frontmatter, and
they are the ones that most often make a vendored skill unusable:

- **Template variables** — a family of upper-case, provider-prefixed
  placeholders for the skill directory, the project directory, the session id,
  the effort level and the plugin root. Substituted by one host, delivered as
  literal text by everything else. Replace them with relative paths.
- **Dynamic shell injection** — a line whose command is executed and replaced by
  its output before the model sees the body. One host runs it, one replaces it
  with a placeholder, the rest pass it through as literal text. Replace it with
  an instruction to read the file or run the command at task time.
- **Forced file attachment** — an at-prefixed path reference that loads a file
  immediately. Even where it works it defeats progressive disclosure: the file
  enters context before anything establishes that it is needed.
- **Argument placeholders** — positional and named substitution tokens. Only
  meaningful for explicitly invoked skills on hosts that implement them.

A skill that must run a bundled script writes the relative path and lets the
agent execute it. That works everywhere and costs nothing.

## Discovery paths per host

Two paths carry most of the ecosystem: a vendor-specific directory and the
shared `.agents/skills/` convention. The shared one is the portable target.

| Host | Project | User |
|---|---|---|
| Claude Code | `.claude/skills/`, plus every parent up to the repository root, plus nested subdirectory copies loaded lazily | `~/.claude/skills/` |
| Codex / ChatGPT | `.agents/skills/` in the working directory, its parent, and the repository root | `~/.agents/skills/`; admin `/etc/codex/skills` |
| Cursor | `.agents/skills/`, `.cursor/skills/`, recursively including nested project directories, auto-scoped to their directory; also reads the Claude Code and Codex directories | `~/.cursor/skills/`, `~/.agents/skills/` |
| Gemini CLI, GitHub Copilot, OpenCode, Amp, Cline, Zed, Warp, Droid, Kilo, Antigravity | `.agents/skills/` | Vendor-specific, e.g. `~/.gemini/skills/`, `~/.copilot/skills/`, `~/.config/opencode/skills/` |
| Goose, Windsurf, Crush, OpenHands, Pi, Kiro CLI, Devin | Vendor-specific, e.g. `.goose/skills/`, `.windsurf/skills/`, `.kiro/skills/` | Vendor-specific |

For a new host, the specification recommends supporting both
`<project>/.<client>/skills/` and `<project>/.agents/skills/`, and the user-level
equivalents.

One host requires extra wiring: a custom agent configuration there must list
skills in its resources array, or the directory is not read at all.

## Collision precedence

The near-universal rule is **project overrides user**. Claude Code inverts part
of it — enterprise, then personal, then project — and it also reserves the
directory name `synced` for skills downloaded from its web product. A skill that
depends on shadowing another skill is not portable; give it a distinct name
instead.

## Listing truncation budgets

Tier-1 metadata is a shared budget, and hosts enforce it differently:

| Host | Budget | Behaviour when exceeded |
|---|---|---|
| Codex | 2% of the context window, or 8,000 characters when the window is unknown | Shortens descriptions first; may omit skills entirely and warn |
| Claude Code | 1,536 characters for the description plus its extra triggering field, per skill | Truncates the entry |

Both cut from the end. This is the entire justification for front-loading the
key use case and the trigger words — text at the tail of a long description may
never reach the model that has to choose.

## Capability differences worth knowing

The installer publishes a compatibility matrix. Three rows matter when deciding
whether a feature is safe to depend on:

- `allowed-tools` — supported by most hosts, ignored by at least two.
- Forked subagent context — one host only.
- Hooks — three hosts, with differing semantics.

A skill whose workflow depends on any of these needs a documented fallback, or a
`compatibility` field that says which product it is for.

<!-- sources: claude-code-skills-docs, cursor-skills-docs, codex-skills-docs, vercel-skills-cli, agentskills-spec -->
