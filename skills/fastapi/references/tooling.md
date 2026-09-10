# Tooling in a FastAPI project

Verified against: FastAPI 0.141, ruff (FAST rule group).

## Contents

- [Which extra to install](#which-extra-to-install)
- [Running the app](#running-the-app)
- [The FAST ruff rules](#the-fast-ruff-rules)
- [Type checking](#type-checking)
- [Layout](#layout)
- [Libraries the official skill picks](#libraries-the-official-skill-picks)
- [Generating clients](#generating-clients)

The generic Python toolchain — uv projects, `[dependency-groups]`, ruff rule selection, pytest
configuration, packaging — is not repeated here. Only what differs inside a FastAPI project is.

## Which extra to install

```bash
uv add 'fastapi[standard]'
uv add --group test httpx2 pytest
```

`fastapi[standard]` brings the `fastapi` CLI, uvicorn with `uvloop` and `httptools`, and the extras
the tutorial assumes (`jinja2`, `python-multipart`, `email-validator`). Plain `fastapi` is the
minimal install for a service that brings its own server; there is no separate slim package to hunt
for any more.

`httpx2` is a test dependency, not a runtime one, and it is needed because Starlette's test client
prefers it over httpx v1.

## Running the app

Declare the app once so no command needs a path:

```toml
[tool.fastapi]
entrypoint = "my_app.main:app"
```

```bash
fastapi dev     # reload, localhost only
fastapi run     # production mode
```

[verified against 0.141: `fastapi run` reads the entrypoint and logs
`Using import string: my_app.main:app`.]

Pass an explicit path (`fastapi dev my_app/main.py`) only when the config cannot be added — a
monorepo with several apps, or a user who asked you not to touch `pyproject.toml`.

`uvicorn my_app.main:app` still works and is what a container image or a process manager typically
runs. Keep the two in agreement: a `[tool.fastapi] entrypoint` that names a different module from
the container `CMD` is a deployment that behaves differently from every local run.

## The `FAST` ruff rules

The `FAST` group is FastAPI-specific and off by default. Turn it on:

```toml
[tool.ruff.lint]
extend-select = ["FAST"]
```

| Rule | Catches | Fixable |
|---|---|---|
| `FAST001` | `response_model=` that duplicates the return annotation | always |
| `FAST002` | `x: T = Depends(...)` instead of `Annotated[T, Depends(...)]` | usually |
| `FAST003` | a path parameter in the route string with no matching function parameter | usually |

`FAST002` is the one worth adopting first: it mechanically converts a legacy codebase to the
`Annotated` style, which is the prerequisite for every other convention in this skill. `FAST003`
catches a genuine 500 — the parameter is undeclared, so the route never matches the way the author
intended.

## Type checking

The rest of the toolchain is generic, with two FastAPI-specific notes:

- `response_model=` and the return annotation can legally disagree (that is the point of
  `response_model`). Annotate such handlers `-> Any` so the checker is not asserting a type FastAPI
  will override.
- Decorated path operations lose nothing type-wise, but `Depends` in a default value defeats the
  checker entirely — another reason for `Annotated`.

## Layout

Do not restructure an existing project to match a template. Two layouts are in wide use and both
work:

- **By feature** — `src/orders/{router,schemas,service,dependencies}.py`. Scales with team size,
  keeps a change in one directory.
- **By layer** — `app/{api,schemas,services,repositories}/`. Familiar, and what most generated
  projects use.

Pick the one the repository already uses. For a new project, by feature, with `main.py` doing
nothing but creating the app, wiring lifespan and including routers — one router per feature module,
`prefix` and `tags` declared on the `APIRouter`.

The one hard rule: no module-level side effects on import. A `create_engine` at import time makes
the app impossible to import in a test without a database, and makes `--reload` slow.

## Libraries the official skill picks

One default, one escape hatch, so a codebase does not accumulate three HTTP clients:

| Job | Use | Instead of |
|---|---|---|
| HTTP calls out | `httpx` (async and sync) | `requests`, `aiohttp` |
| SQL with Pydantic models | `SQLModel` | plain SQLAlchemy, unless the project already uses it |
| crossing the async/blocking boundary | `asyncer` | hand-rolled `to_thread` wrappers |
| settings | `pydantic-settings` | `os.environ` reads scattered around |

These are FastAPI's own recommendations, not the only workable choices. Do not migrate a working
SQLAlchemy or `aiohttp` codebase to satisfy this table; apply it to new code.

Database schema design, query tuning and migration tooling are outside this skill entirely.

## Generating clients

`/openapi.json` is the artefact clients are generated from, so treat it as output you own:

- Set `operation_id` explicitly on any operation a client generator consumes. The generated default
  includes the function name and route, so renaming a Python function renames a method in every
  downstream SDK.
- Use one `generate_unique_id_function` (or consistent `operation_id`s) if you want stable, readable
  names across the whole app rather than per-route decisions.
- Commit a snapshot of `openapi.json` and diff it in CI when SDKs are published from it; that turns
  an accidental contract change into a review comment instead of a client bug.

<!-- sources: fastapi-official-skill, fastapi-docs, ruff-fast-rules, zhanymkanov-best-practices, microsoft-skills-py -->
