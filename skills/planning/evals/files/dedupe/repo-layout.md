# tabkit repository layout (generated 2026-09-29)

Python 3.12 CLI, packaged with uv. One module per subcommand.

```
tabkit/
  pyproject.toml          # [project.scripts] tabkit = "tabkit.cli:main"
  Makefile
  src/tabkit/
    __init__.py
    cli.py                # argparse; builds subparsers from COMMANDS
    commands/
      __init__.py         # COMMANDS = {"head": head.register, "select": select.register}
      head.py             # register(subparsers) + run(args, stdin, stdout, stderr) -> int
      select.py           # same shape as head.py
    csvio.py              # open_input(path_or_dash, stdin) -> TextIO; reader(fh) -> csv.reader
                          # writer(fh) -> csv.writer (lineterminator="\n")
  tests/
    conftest.py           # fixture run_cli(argv, stdin_text) -> (code, stdout, stderr)
    test_head.py
    test_select.py
  docs/plans/             # empty
```

## Commands (from the Makefile)

- `make test` - `uv run pytest -q`
- `make test-one T=<path or node id>` - `uv run pytest -q $(T)`
- `make lint` - `uv run ruff check src tests`

## Conventions

- Every subcommand module exposes `register(subparsers)` and
  `run(args, stdin, stdout, stderr) -> int` and is added to `COMMANDS`.
- Tests go through `run_cli` only; they never import a command's internals.
- `select.py` is the closest existing example: it already looks up header
  columns by name and exits 2 via `parser.error` when `--columns` is missing.
