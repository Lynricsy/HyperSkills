# ruff: lint and format

Verified against: ruff 0.16.x.

## Contents

- [Two commands, not one](#two-commands-not-one)
- [Defaults you inherit](#defaults-you-inherit)
- [Rule selection](#rule-selection)
- [Rule groups worth enabling deliberately](#rule-groups-worth-enabling-deliberately)
- [Per-file ignores](#per-file-ignores)
- [Formatter settings](#formatter-settings)
- [The fix loop](#the-fix-loop)
- [Suppression discipline](#suppression-discipline)
- [Preview rules](#preview-rules)
- [Config resolution](#config-resolution)

## Two commands, not one

```bash
uv run ruff check .            # lint
uv run ruff check --fix .      # lint, applying safe fixes
uv run ruff format .           # format
uv run ruff format --check .   # verify formatting without writing (CI)
```

`ruff check` does not format and `ruff format` does not lint. A change that ran
only `check` leaves formatting violations that CI's `format --check` will reject.

Formatting-adjacent lint rules exist (`E501` line length, `COM812` trailing
comma, `ISC001` implicit concatenation) and fight the formatter when both are
active. Turn those specific rules off rather than the formatter.

## Defaults you inherit

When no setting is given:

- `line-length = 88`, `indent-width = 4`
- `quote-style = "double"`, magic trailing commas respected
- default rule set is a subset of `E` and `F` — not "everything"
- `target-version` is inferred from `project.requires-python` in a nearby
  `pyproject.toml`; only when neither is present does it fall back to `py310`

That inference matters: `requires-python = ">=3.9"` makes ruff refuse to rewrite
`Optional[int]` to `int | None`, and raising the floor to `>=3.10` makes the same
rewrite appear without any lint config change. If the pyupgrade rewrites you
expect are missing, check `requires-python` before touching `select`.

## Rule selection

`select` **replaces** the enabled set; `extend-select` **adds** to whatever was
resolved. Mixing them across an inherited config is how a rule you thought you
enabled silently disappears — the highest-priority `select` wins outright, then
`extend-select` and `ignore` are applied on top.

A deliberate starting point, per ruff's own guidance:

```toml
[tool.ruff.lint]
select = [
  "E",    # pycodestyle errors
  "F",    # pyflakes
  "I",    # isort — import ordering, replaces isort entirely
  "UP",   # pyupgrade — rewrites to the syntax your requires-python allows
  "B",    # flake8-bugbear — real bugs, not style
  "SIM",  # flake8-simplify
]
ignore = [
  "E501",  # line length is the formatter's job
]
```

Widen one group at a time and fix the fallout before adding the next. `select =
["ALL"]` is available but adopts every rule added in future releases, so a ruff
upgrade becomes a lint failure in unrelated files; use it only where the ruff
version is pinned exactly and someone owns the upgrade.

## Rule groups worth enabling deliberately

These earn their keep beyond the starter set, in rough order of value:

| Prefix | What it catches |
|---|---|
| `RUF` | ruff's own rules, including `RUF006` (dangling `asyncio.create_task`) and `RUF100` (unused `noqa`) |
| `ASYNC` | blocking calls inside `async def`, un-awaited coroutines |
| `PT` | pytest anti-patterns: bare `assert` on exception, misused fixtures, `parametrize` shape |
| `ANN` | missing annotations — enable when the typing ratchet reaches this module, not before |
| `S` | bandit security rules; noisy in tests, so pair with a per-file ignore |
| `PTH` | `os.path` → `pathlib` |
| `TC` | imports that belong under `if TYPE_CHECKING:` |
| `D` | docstring style; pick one convention (`[tool.ruff.lint.pydocstyle] convention = "google"`) or the D203/D211-style conflicts appear |

`RUF100` deserves a specific mention: it flags `noqa` comments that no longer
suppress anything, which is the only automated defence against suppression
comments outliving their cause.

## Per-file ignores

Rules that are right for source and wrong for tests or `__init__.py`:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = [
  "S101",    # assert is the point of a test
  "ANN",     # test signatures carry no API contract
  "PLR2004", # magic values in assertions are the expected value
]
"__init__.py" = ["F401"]  # re-exports look unused
"scripts/**" = ["T201"]   # print is the output channel for a script
```

Prefer this over scattering `# noqa` through the files: it states the policy in
one place and survives refactors.

## Formatter settings

Deliberately few knobs. The two worth setting:

```toml
[tool.ruff.format]
docstring-code-format = true      # format code blocks inside docstrings
skip-magic-trailing-comma = false # keep exploded literals exploded
```

`line-length` is shared with the linter and lives under `[tool.ruff]`. Do not set
a different value per tool; a mismatch means the formatter produces lines the
linter rejects.

## The fix loop

Working through a backlog of diagnostics without producing an unreviewable diff:

1. Scope it. `ruff check src/acme/orders` beats a whole-repo run: the diff stays
   reviewable and the failures stay attributable.
2. `ruff format` first. Formatting changes shift line numbers, so doing it after
   the lint fixes invalidates every location you just reported.
3. `ruff check --fix`. Safe fixes only; read the diff before continuing.
4. Consider `--unsafe-fixes` explicitly, never in the same pass. Unsafe fixes may
   change behaviour by design (removing a "useless" expression that had a side
   effect, for one), so they get their own diff and their own read.
5. Fix the remainder by hand, from the highest-signal rule down. `F` and `B`
   findings are usually bugs; `E` and `SIM` are usually not.
6. Re-run and stop. If a file still fails after one honest attempt, report it with
   the diagnostic rather than looping: repeated auto-fix attempts on one file mean
   the rule and the code genuinely disagree, and that is a decision for the user.

Only the lines this change touches are in scope. Pre-existing diagnostics in
untouched code get listed in your report so the user can decide; dragging them in
turns a small fix into a large diff nobody asked to review.

## Suppression discipline

```python
# noqa: E501 — URL cannot be wrapped
# noqa: S603 — argv is a fixed literal list, no shell
```

Rules:

- Always a code, never bare `# noqa`. A bare one suppresses everything on the
  line, including the bug that appears there next year.
- Always a reason. "The linter complained" is not a reason.
- Enable `RUF100` so dead suppressions get removed instead of accumulating.
- A rule suppressed in more than a handful of places is a configuration decision,
  not a per-line one: move it to `ignore` or `per-file-ignores` and say why.

## Preview rules

`preview = true` enables unstable rules and unstable formatter behaviour. It is
useful for evaluating what is coming and a poor default: rules can change or
disappear between patch releases, so CI reproducibility depends on the exact ruff
version. If you turn it on, pin ruff exactly.

## Config resolution

ruff reads `pyproject.toml` (`[tool.ruff]`), `ruff.toml` or `.ruff.toml`, and
uses the nearest one to each file — a subdirectory config wins for files under
it. `extend = "../ruff.toml"` inherits and overrides.

Passing `--config` explicitly disables `target-version` inference from
`requires-python`, so an explicitly-passed config must state `target-version`
itself or silently target py310.

<!-- sources: awesome-copilot-python, trailofbits-modern-python, laurigates-python, probabl-python-style, ruff-docs -->
