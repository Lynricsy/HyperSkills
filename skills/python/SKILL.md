---
name: python
description: "Guides modern Python work: uv for projects, tools and PEP 723 single-file scripts; ruff as the single linter and formatter; pyproject.toml, dependency groups, build backends and PyPI publishing; pytest fixtures, parametrization, isolation and plugins; typing with Protocol, TypedDict, PEP 695 generics and gradual mypy/pyright strictness; asyncio task lifetime, cancellation and blocking-call detection; and the language-level traps that survive review. Use when creating, migrating, typing, testing, packaging or debugging Python code, when reading pyproject.toml to decide how dependencies and tooling are declared, or when a test suite passes alone but fails as part of the whole run. Do not use for Django, FastAPI, data analysis with pandas or notebooks, or model training and fine-tuning."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# python

## Scope

Covers the Python language and its standard toolchain: uv for environments,
dependencies and scripts; ruff for lint and format; `pyproject.toml` for project
metadata, dependency groups, build backend and packaging; pytest for tests;
static typing with mypy or pyright; asyncio; and the runtime traps that a type
checker and a linter both miss.

Not covered: web frameworks — FastAPI request handling, dependency injection and
response models are the `fastapi` skill's job; Django request handling, ORM
models and migrations are the framework's own concern. Also not covered: data
analysis and notebooks (pandas, numpy, Jupyter). Model training and fine-tuning:
use the `ml-training` skill; calling a hosted model: the `ai-engineering` skill.
For the discipline of driving code with tests rather than the pytest API, use the
`test-driven-development` skill. For diagnosing a specific observed failure, use
the `debugging` skill. For reviewing a diff, use the `code-review` skill.

Paths below are relative to this skill's directory.

## Core rules

1. Read `pyproject.toml` before changing anything. On an existing project its
   declared Python version, line length, type checker, test layout and rule set
   are the truth; the defaults here apply only when a field is absent or the
   project is new. Nothing annoys a maintainer faster than a tool swap nobody asked for.
2. uv is the environment manager. Mutate dependencies with `uv add` / `uv remove`
   and run everything through `uv run`. Hand-editing the dependency tables skips
   resolution and leaves `uv.lock` stale; `source .venv/bin/activate` leaves the
   agent and CI in different environments.
3. `uv pip install` is an escape hatch for a non-project virtualenv, never a way
   to add a project dependency — it writes nothing to `pyproject.toml`.
4. Development tooling goes in `[dependency-groups]`, not
   `[project.optional-dependencies]`. Groups are local-only; extras are published
   with the wheel, so an extra makes your linter part of your public API.
5. Commit `uv.lock` for applications and for anything deployed. Libraries may
   leave it uncommitted, but then CI has no reproducible run — decide once and say which.
6. A single file that needs third-party packages gets PEP 723 inline metadata
   (`uv init --script`, then `uv add --script`), not a requirements file and not a
   README telling people to `pip install` first. The `dependencies` key must be
   present even when empty, and inline metadata makes `uv run` ignore any
   surrounding project.
7. ruff replaces flake8, black, isort, pydocstyle and pyupgrade — all of them, not
   some. `ruff check` and `ruff format` are two separate commands; running only
   the first leaves the file unformatted.
8. Select ruff rules explicitly (`E`, `F`, `UP`, `B`, `SIM`, `I` is a good start)
   and widen a group at a time. `select = ["ALL"]` silently adopts every rule
   added in the next release, which turns a version bump into a lint failure.
9. Fix only the diagnostics on lines this change touched. Pre-existing violations
   elsewhere get reported to the user, not swept up — "while I was here" is how a
   two-line fix becomes an unreviewable diff.
10. Never let `ruff check --fix` and `--unsafe-fixes` run unattended in the same
    pass. Apply safe fixes, read the diff, then consider unsafe ones; unsafe fixes
    may change behaviour by design.
11. Every `# noqa` and every `# type: ignore` names its code and its reason
    (`# noqa: E501 — URL in docstring`). A bare suppression is invisible to the
    next reader and to `--extend-select RUF100`.
12. Type the boundaries first: public function signatures, class attributes, and
    anything crossing a process or module edge. Local variables the checker can
    infer do not need annotations.
13. A dependency that several unrelated classes satisfy is a `typing.Protocol`, not
    a base class. Inheritance forces every implementation — including test stubs —
    to import your module.
14. Structured payloads get a `TypedDict`, dataclass or Pydantic model.
    `dict[str, Any]` disables checking for everything downstream of it, which is
    worse than no annotation because it looks done.
15. Turn strictness up per module, in batches, and keep the suite green between
    batches (`references/typing.md`). Flipping `--strict` on a large repo produces
    thousands of errors and one giant unreviewable commit.
16. In `pyproject.toml`, `[tool.pytest]` needs pytest 9.0+; `[tool.pytest.ini_options]`
    works from 6.0. Put the table under the wrong name for your pinned version and
    pytest ignores the whole thing — markers, `filterwarnings` and `asyncio_mode`
    included — without warning.
17. Fixture scope above `function` must be immutable or reset. A `session`-scoped
    object that tests mutate makes the suite order-dependent, which is why a file
    passes alone and fails in the full run.
18. `unittest.mock.patch` replaces a name in the namespace that resolves it, so the
    target follows the import style of the module under test: `from httpx import get`
    means patching `mymodule.get`, while `import httpx` means `httpx.get` is the
    same object either way. Mocks for awaited callables are `AsyncMock`, not `Mock`;
    and a patch whose context exits before a background task runs asserts nothing.
19. Keep a strong reference to every `asyncio.create_task` result, or create it
    inside `asyncio.TaskGroup`. The loop holds only weak references, so a
    fire-and-forget task can be garbage collected mid-flight.
20. Prefer `asyncio.TaskGroup` over `asyncio.gather`. When a child fails, the group
    cancels its siblings; `gather` propagates the first exception and leaves the
    rest running. Use `gather` only when you need positional results or
    `return_exceptions=True`.
21. No blocking call inside `async def` — not `time.sleep`, not `requests`, not a
    synchronous DB driver, not `open().read()` on a slow mount. One blocking call
    stalls every other task on the loop. Wrap unavoidable ones in
    `asyncio.to_thread`.
22. If you catch `asyncio.CancelledError`, re-raise it after cleanup.
    Swallowing it breaks `TaskGroup` and `asyncio.timeout`, which are built on
    cancellation.
23. Finish every change with the gate: `uv run ruff format`, `uv run ruff check`,
    the project's type checker on the touched paths, then `uv run pytest`. Report
    the commands and their output, not "should be fine".

## Workflows

### start-or-migrate-a-project

- [ ] Classify the work: single file with dependencies → PEP 723 script; multi-file
      but not distributed → `uv init`; installable package → `uv init --package`
      with a `src/` layout. The rest of this list is the package case.
- [ ] Existing project? Inventory what is being replaced first: `requirements*.txt`,
      `setup.py` / `setup.cfg`, `Pipfile`, `poetry.lock`, `.flake8`,
      `[tool.black]`, `[tool.isort]`, `mypy.ini`, `tox.ini`. Migration steps per
      source are in `references/uv-projects.md`.
- [ ] Bring runtime dependencies over with `uv add -r requirements.txt` (or
      `uv add` per package, reviewing each pin — an `==` from 2023 is a decision
      nobody re-made), then dev tooling with `uv add --group dev ruff mypy` and
      `uv add --group test pytest pytest-cov`.
- [ ] Set `requires-python` to the oldest version you actually support. ruff infers
      `target-version` from it, so this one field decides which pyupgrade rewrites fire.
- [ ] Configure ruff and the type checker (`references/ruff.md`,
      `references/typing.md`), and pytest under the table name your pinned pytest
      version reads (rule 16, detail in `references/pytest.md`).
- [ ] Delete the replaced files in the same change. Two dependency sources in one
      tree is the failure mode: CI installs one, the developer installs the other.
- [ ] Distributable? Choose the build backend and fill in packaging metadata via
      `references/packaging.md`.
- [ ] **Gate — reproducible from a clean checkout:** `uv sync --all-groups`, then
      `uv run ruff format --check`, `uv run ruff check`, the type checker, and
      `uv run pytest`, all from a fresh clone with no pre-existing `.venv`.

### add-types

- [ ] Read the current state: which checker the project configures, whether this
      module is excluded, and how strict the surrounding modules already are.
- [ ] Annotate the boundaries — public signatures and class attributes — and let
      inference handle locals.
- [ ] Replace duck-typed parameters with a `Protocol`, and untyped mappings with a
      `TypedDict` or dataclass (rules 13–14, patterns in `references/typing.md`).
- [ ] Pick the syntax for your floor: PEP 695 (`def f[T](...)`, `class C[T]`,
      `type Alias = ...`) needs Python 3.12+; below that use `TypeVar`. Say which
      you chose and why.
- [ ] Remove this module from the exclusion list and raise strictness for it alone
      — a per-module override, not a global flag.
- [ ] Run the checker on the touched paths first for fast feedback, fix, then widen
      the run to the package.
- [ ] Any suppression left behind is `# type: ignore[<code>] — <reason>`. If the
      count is growing rather than shrinking, the batch is too big: stop and split it.
- [ ] **Gate — narrower than before, and green:** the checker passes on the touched
      paths at the new strictness, the exclusion entry is gone, `uv run pytest`
      still passes, and every remaining ignore has a code and a reason.

### write-or-fix-tests

- [ ] Confirm pytest is reading your config at all: `uv run pytest --help` lists
      registered settings, and the startup header names the `configfile` it picked.
      A silently ignored table is the first thing to rule out (rule 16).
- [ ] Put shared setup in a fixture in the nearest `conftest.py`, and default to
      `function` scope. Widen scope only for genuinely immutable or externally
      managed resources, and say what makes it safe.
- [ ] Order-dependent failure? Run `uv run pytest -p no:randomly` versus the plain
      run, and `uv run pytest --lf`. Then look for shared mutable state: a
      non-function-scoped fixture, a module-level singleton, a mutable default
      argument, or a class attribute (`references/runtime-traps.md`).
- [ ] Cover the same behaviour across inputs with `@pytest.mark.parametrize` and
      `pytest.param(..., id=...)`; a failing case should name itself in the output.
- [ ] Patch at the lookup site, use `AsyncMock` for awaited dependencies, and assert
      on calls (`assert_called_once_with`) rather than on the mock's existence
      (rule 18, detail in `references/pytest.md`).
- [ ] Async tests need an async plugin and a declared mode; mixing
      `asyncio_mode = "auto"` with explicit `@pytest.mark.asyncio` is fine, missing
      both silently skips or errors the coroutine.
- [ ] **Gate — the failure is reproduced and then gone:** the previously failing
      invocation now passes, the full `uv run pytest` passes, and if the bug was
      isolation you show the ordering that used to break it.

### debug-async

- [ ] Map the call path: is it fully async, or does an `async def` reach a
      synchronous library? Mixed paths are where the loop stalls.
- [ ] Grep the async functions for blocking calls — `time.sleep`, `requests.`,
      `subprocess.run`, sync DB drivers, plain file IO on network mounts — and move
      them behind `asyncio.to_thread` or an async client.
- [ ] Audit task lifetime: every `create_task` result is stored or created inside a
      `TaskGroup`; nothing awaits a coroutine it never scheduled; no coroutine is
      left un-awaited (ruff `RUF006`, `ASYNC` and `B` rules catch several of these).
- [ ] Audit cancellation: `except asyncio.CancelledError` re-raises, `except
      Exception` does not accidentally cover it (it derives from `BaseException`),
      and cleanup lives in `finally`.
- [ ] Replace ad-hoc timeout logic with `asyncio.timeout`, and expect
      `TimeoutError` rather than `CancelledError` at the boundary.
- [ ] Turn on `asyncio` debug mode (`PYTHONASYNCIODEBUG=1` or
      `asyncio.run(main(), debug=True)`) to get slow-callback warnings that point at
      the blocking frame. Details in `references/asyncio.md`.
- [ ] **Gate — the symptom is explained, not just gone:** name the task, the
      blocking frame or the swallowed cancellation, and show the run where the
      symptom no longer appears.

### publish

- [ ] Confirm the metadata contract in `references/packaging.md`: `[project]`
      fields, PyPI name versus import name, `readme`, `license`, classifiers, and
      `py.typed` if the package ships types.
- [ ] Decide the version source — static in `pyproject.toml`, or derived from git
      tags — and make sure exactly one place owns it.
- [ ] Build and inspect before uploading: `uv build`, then check the wheel actually
      contains the package (a missing `src/` mapping produces an empty wheel that
      installs cleanly and imports nothing).
- [ ] Rehearse on TestPyPI, install from there into a throwaway environment, and
      import the package.
- [ ] Publish from CI with Trusted Publishing (OIDC) rather than a long-lived API
      token stored in secrets.
- [ ] **Gate — installable and typed:**
      `uv run --isolated --no-project --with dist/<pkg>-<ver>-py3-none-any.whl python -c
      "import <pkg>"` succeeds against the built artifact [verified], and the type
      checker sees the annotations the wheel actually ships.

## Topic router

| Topic | Read when | File |
|---|---|---|
| uv projects, groups, lockfile, tools, workspaces, PEP 723 scripts, migration from pip/Poetry | Creating or migrating a project, or making a script self-contained | `references/uv-projects.md` |
| ruff rule selection, per-file ignores, formatter settings, the fix loop, noqa discipline | Configuring lint/format or working through a backlog of diagnostics | `references/ruff.md` |
| Protocol, TypedDict, PEP 695 generics, narrowing, `Self`, `override`, mypy and pyright config, strictness ratchet | Adding or tightening annotations | `references/typing.md` |
| pytest config table versions, fixtures and scope, parametrization, isolation, mocking, async tests, plugins | Writing tests or chasing an order-dependent failure | `references/pytest.md` |
| Task lifetime, TaskGroup, cancellation, timeouts, blocking-call detection, debug mode | Anything with `async def` in it | `references/asyncio.md` |
| `pyproject.toml` metadata, src layout, build backends, versioning, `py.typed`, publishing | Making a package installable or releasing it | `references/packaging.md` |
| Mutable defaults, late-binding closures, class-attribute sharing, exception chaining, resource leaks, equality and caching traps | Reviewing or debugging code that passes lint and the type checker but misbehaves | `references/runtime-traps.md` |

## Environment

- `uv` is the only required tool; it provisions Python itself
  (`uv python install 3.13`), so no system interpreter or `pyenv` is needed.
  Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- ruff, mypy or pyright, and pytest are project dependencies, declared in
  `[dependency-groups]` and invoked as `uv run ruff`, `uv run mypy`,
  `uv run pytest`. Do not rely on globally installed copies: their versions differ
  from the project's and their diagnostics will not match CI.
- `uvx <tool>` runs a tool without adding it to the project — useful for a one-off
  check, wrong for anything CI depends on.
- When a command here does not exist in the project, say so and name the command
  the project does use, rather than substituting a global tool.
