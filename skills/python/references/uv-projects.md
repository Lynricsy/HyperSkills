# uv: projects, scripts and migration

Verified against: uv 0.12.x.

## Contents

- [The four dependency fields](#the-four-dependency-fields)
- [Project commands worth knowing](#project-commands-worth-knowing)
- [The lockfile](#the-lockfile)
- [PEP 723 single-file scripts](#pep-723-single-file-scripts)
- [Tools: `uvx` versus a dependency group](#tools-uvx-versus-a-dependency-group)
- [Python versions](#python-versions)
- [Workspaces](#workspaces)
- [Migration paths](#migration-paths)
- [Cleanup after a migration](#cleanup-after-a-migration)
- [CI](#ci)

## The four dependency fields

Four tables, four audiences. Putting a requirement in the wrong one is the most
common `pyproject.toml` mistake.

| Table | Who sees it | Use for |
|---|---|---|
| `[project] dependencies` | anyone who installs the wheel | runtime requirements |
| `[project.optional-dependencies]` | installers who ask for the extra (`pkg[postgres]`) | optional runtime features |
| `[dependency-groups]` | only local development and CI | ruff, mypy, pytest, sphinx |
| `[tool.uv.sources]` | only uv, only during development | local paths, git refs, alternative indexes |

```toml
[project]
name = "acme-orders"
version = "1.2.0"
requires-python = ">=3.12"
dependencies = ["httpx>=0.27", "click>=8.1"]

[project.optional-dependencies]
postgres = ["psycopg[binary]>=3.2"]

[dependency-groups]
lint = ["ruff>=0.16", "mypy>=1.14"]
test = ["pytest>=8.3", "pytest-cov>=6", "pytest-asyncio>=0.24"]
dev = [{ include-group = "lint" }, { include-group = "test" }]
```

`dev` is special only by convention plus one shortcut: `uv add --dev x` writes to
it and `uv sync` installs it by default. Every other group needs `--group`.

`tool.uv.sources` is uv-only. Another tool reading the same `pyproject.toml` sees
just the plain requirement, so a source entry is a development convenience, never
part of the published contract.

## Project commands worth knowing

```bash
uv init                     # non-distributed project
uv init --package           # distributable, src/ layout, [project.scripts] stub
uv init --bare              # pyproject.toml only, for an existing tree
uv add httpx                # resolve, write pyproject.toml, update uv.lock, install
uv add --group test pytest  # into a group
uv add -r requirements.txt  # bulk import; review the pins it brings along
uv remove httpx
uv sync                     # make .venv match uv.lock exactly
uv sync --all-groups        # including lint/test/docs
uv sync --frozen            # fail instead of re-locking (use in CI)
uv run pytest               # sync if needed, then run inside the environment
uv run --with ipython python  # one-off extra package, not written to the project
uv tree                     # why is this transitive dependency here
uv build && uv publish
```

`uv run` is not "activate then run": it re-checks the lockfile first, so a
teammate's `uv add` shows up on your next command rather than at your next manual
`pip install`. That is the reason rule 2 forbids activating the venv by hand — an
activated shell drifts silently.

`uv sync` removes packages that are not in the lockfile. If something you rely on
disappears after a sync, it was never declared.

## The lockfile

`uv.lock` is cross-platform: one file resolves for every platform allowed by
`requires-python` and the markers, so it is committed once and used everywhere.

- Applications and services: commit it. Reproducible deploys are the whole point.
- Libraries: the wheel's metadata is what consumers resolve against, so the lock
  only pins *your* CI. Committing it is still the easier choice; the cost is
  Dependabot-style churn.
- CI: `uv sync --frozen` (or `uv run --frozen`) so a stale lockfile fails the build
  instead of being silently updated mid-pipeline.
- `uv lock --upgrade-package httpx` bumps one package; `uv lock --upgrade` bumps
  everything. Prefer the first, one dependency per change, so a regression has one
  suspect.

## PEP 723 single-file scripts

A script with third-party imports declares them in a comment block the standard
calls inline script metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "rich"]
# ///

import httpx
```

```bash
uv init --script report.py --python 3.12   # create with the block
uv add --script report.py httpx rich       # edit the block for you
uv run report.py                           # provisions an env, runs, exits
uv lock --script report.py                 # optional: report.py.lock
```

Four things that bite:

- The `dependencies` key must exist even when empty. A block with only
  `requires-python` is invalid.
- When a script has inline metadata, `uv run` **ignores** the surrounding
  project's dependencies. `--no-project` is unnecessary; a script that needs the
  project should be a module in the project instead.
- `requires-python` here is a real gate: uv downloads a matching interpreter if
  none is installed, so pick the floor deliberately.
- The shebang form is `#!/usr/bin/env -S uv run --script` — the `-S` is what makes
  the multi-word command work, and `chmod +x` is still needed.

This is also the answer for anything shipped inside a repository as tooling: a
`scripts/*.py` with an inline block runs on a clean machine with uv and nothing
else.

## Tools: `uvx` versus a dependency group

`uvx ruff check` (equivalently `uv tool run`) runs a tool in a throwaway
environment at whatever version resolves today. That is right for a one-off
inspection and wrong for anything reproducible: two developers get two versions
and two diagnostic sets. Anything CI runs belongs in `[dependency-groups]` with a
version constraint, invoked as `uv run ruff`.

`uv tool install` puts a tool on `PATH` for interactive use. It has no
relationship to any project and never satisfies a project dependency.

## Python versions

```bash
uv python install 3.13        # uv-managed interpreter, no system Python needed
uv python list                # what is available and what is in use
uv python pin 3.13            # writes .python-version
uv run --python 3.11 pytest   # one-off check against an older floor
```

`.python-version` selects the interpreter for local work; `requires-python` in
`pyproject.toml` declares what the project supports. They answer different
questions and both belong in the repository. Testing only on the pinned version
while claiming support for three is how a `3.11`-incompatible syntax reaches PyPI.

## Workspaces

Several packages in one repository that release together:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
acme-core = { workspace = true }
```

One lockfile and one environment for all members, so a change in `acme-core` is
visible to `acme-api` immediately. Use it for co-released packages. Do not use it
to stitch together projects with independent release cycles — they resolve
against each other's unreleased state, and the first independent release breaks.

## Migration paths

**From `requirements.txt` + pip.** `uv init --bare`, then `uv add -r
requirements.txt` for runtime and `uv add --group dev -r requirements-dev.txt`
for tooling. Read the pins as you go: an `==` pin from an old resolution is a
decision that expired, and carrying it forward silently blocks every future
upgrade. Delete the requirements files and the old virtualenv, commit `uv.lock`.

**From `setup.py` / `setup.cfg`.** Copy the non-dependency metadata (`name`,
`version`, `description`, `readme`, `license`, classifiers, `entry_points` →
`[project.scripts]`) into `[project]` by hand — this is metadata, not
resolution, so hand-editing is correct here. Move `install_requires` with
`uv add`, `extras_require` to `[project.optional-dependencies]`, and dev-only
extras to `[dependency-groups]`. Add a `[build-system]` table; without one,
installers fall back to setuptools and the deleted `setup.py`. Then remove
`setup.py`, `setup.cfg` and `MANIFEST.in`.

**From Poetry.** Poetry 2 already writes a standard `[project]` table, so the
work is replacing `[tool.poetry.group.*.dependencies]` with
`[dependency-groups]`, translating caret constraints (`^1.2` means `>=1.2,<2`),
and deleting `poetry.lock`. Poetry's `packages = [...]` becomes the build
backend's own include configuration.

**From flake8 + black + isort.** `uv remove` all three, delete `.flake8`,
`setup.cfg` lint sections, `[tool.black]` and `[tool.isort]`, add ruff, then run
`ruff check --fix` and `ruff format`. Expect one large formatting commit; keep it
separate from behaviour changes so review stays possible.

**Changing type checker.** Do not, on an existing project, unless asked. If you
must, translate the config and migrate module by module rather than repo-wide;
the two checkers disagree on enough real cases that a whole-repo switch lands as
one unreviewable commit.

## Cleanup after a migration

The step everyone skips. Leftovers keep working just long enough to confuse the
next person.

- Grep for stale pragmas: `# noqa: F401` left from flake8-only rules,
  `# type: ignore` for a checker you no longer run, `# fmt: off` from black.
- Grep for the old commands in `.github/workflows/`, `Makefile`, `tox.ini`,
  `.pre-commit-config.yaml`, `Dockerfile`, `README.md`. A CI job still calling
  `pip install -r requirements.txt` will pass while testing the wrong tree.
- Remove `venv/`, `.venv/` if its layout changed, `*.egg-info/`, `.eggs/`, and
  add `.venv/` to `.gitignore` if it is not there.
- Delete the removed tools' config sections from `pyproject.toml`; an orphaned
  `[tool.isort]` is a claim that isort still runs.

## CI

```yaml
- uses: astral-sh/setup-uv@<sha>   # pin by SHA; tags move
  with:
    enable-cache: true
- run: uv sync --all-groups --frozen
- run: uv run ruff format --check
- run: uv run ruff check
- run: uv run mypy src
- run: uv run pytest
```

`--frozen` is the important flag: without it a stale lockfile is quietly refreshed
and CI stops testing what the developer committed. Keep format, lint, types and
tests as four steps so the failing one names itself.

<!-- sources: trailofbits-modern-python, laurigates-python, wshobson-python, gvre-python, uv-docs, pypa-docs -->
