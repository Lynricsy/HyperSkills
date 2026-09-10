---
name: fastapi
description: "Guides FastAPI service work: APIRouter organisation, Annotated dependency injection including yield-dependency lifetime and exit scope, Pydantic v2 request and response models, response_model filtering and serialisation traps, exception handlers and a single error contract, the async/blocking boundary (async def versus def, the 40-slot threadpool, lifespan and lifespan state), streaming and Server-Sent Events, background tasks versus a real task queue, testing with TestClient or httpx.AsyncClient plus dependency_overrides, security dependencies, and what FastAPI puts into the generated OpenAPI schema. Use when writing, reviewing, debugging or upgrading FastAPI endpoints, when a request path stalls under concurrency, when a response leaks or silently drops fields, or when a test suite still talks to real databases and identity providers. Do not use for the Python language and its general toolchain, nor for designing the REST contract and OpenAPI specification itself."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# fastapi

## Scope

Covers building and reviewing HTTP services with FastAPI: path operations and router
organisation, the dependency-injection system, Pydantic v2 models as the request and
response contract, error handling, the boundary between async and blocking code,
lifespan-managed resources, streaming and Server-Sent Events, background work, security
dependencies, testing, and the FastAPI-specific parts of the toolchain.

The body is written against **FastAPI 0.141**, **Pydantic 2.13** and **Starlette 1.6**.

Not covered:

- The Python language and its general toolchain — uv projects and dependency groups, ruff
  rule selection, pytest fixtures and isolation, packaging, `Protocol`/`TypedDict` typing,
  asyncio task lifetime and cancellation. Use the `python` skill; this skill only covers
  what those tools do differently inside a FastAPI project.
- Deciding what deserves a test and driving code with tests — use the
  `test-driven-development` skill.
- Working a reproducible local failure down to a root cause — use the `debugging` skill.
- Reviewing a diff for general correctness and style — use the `code-review` skill; come
  back here for the FastAPI-specific rules a reviewer applies.
- REST contract and OpenAPI specification design (resource modelling, URI and versioning
  policy, pagination strategy, the error schema itself), database schema design and query
  tuning, ORM and migration tooling, containers and cloud deployment, GraphQL. None of
  these has a skill in this library yet; say so rather than improvising one.

Paths below are relative to this skill's directory.

## Core rules

1. Read `pyproject.toml` and the app factory before changing anything. The FastAPI and
   Pydantic versions decide which of these rules apply, and an existing project's router
   layout and error shape are the truth even where they differ from the defaults here.
2. Declare parameters and dependencies with `Annotated`: `q: Annotated[str | None, Query()]`,
   `user: Annotated[User, Depends(get_current_user)]`. The `= Depends(...)` default form puts
   a sentinel in the default slot, so the function can no longer be called or type-checked
   outside a request. `ruff`'s `FAST002` finds and rewrites them.
3. Name reusable dependencies as type aliases (`CurrentUser = Annotated[User, Depends(...)]`)
   and use the alias everywhere. One place to change when the dependency changes.
4. No `...` as a default. A field or parameter with no default is already required, and
   `Field(...)` is noise that hides real metadata.
5. The body of a path operation decides its keyword: fully awaited → `async def`; contains any
   blocking call → `def`, which FastAPI runs in the threadpool. One `requests.get` inside
   `async def` stalls every other request on that worker, not just its own.
6. The threadpool has 40 slots by default, and `def` dependencies take slots too. If that is
   the real ceiling, raise `anyio.to_thread.current_default_thread_limiter().total_tokens` in
   `lifespan` — deliberately, and in step with the connection pool behind it.
7. When a handler must stay `async def`, push the blocking call out with
   `run_in_threadpool` or `asyncer.asyncify`, not by hoping it is fast enough.
8. Annotate the return type and let FastAPI validate, filter, document and serialise from it.
   Use `response_model=` only when the public schema differs from what the function returns,
   and then annotate the return `-> Any`; declaring both for the same type is what `FAST001`
   flags.
9. Filter secrets structurally. A response model that never declares `password_hash` cannot
   leak it; `response_model_exclude` is a list someone forgets to extend on the next endpoint.
10. Pydantic serialises according to the **declared** type, not the runtime class. Returning a
    subclass where the base is declared silently drops the subclass's fields — no error, no
    warning. Use a discriminated union when both shapes are real.
11. Router-level `prefix`, `tags` and `dependencies` belong on the `APIRouter(...)`
    constructor, not on `include_router()`. What guards a router should be readable in the
    router's own file.
12. One HTTP method per function. `@app.api_route(methods=["GET", "POST"])` with a branch on
    `request.method` produces one OpenAPI operation for two behaviours.
13. Declare the success status code on the decorator: `201` for create, `202` for accepted and
    queued, `204` (with `response_model=None`) for no body. A `204` handler that returns data
    does not fail — Starlette drops the body and the client gets nothing.
14. Raise `ValueError` from a validator, not `HTTPException`: FastAPI turns it into the standard
    422 with the field path. And never `assert` in a validator — assertions vanish under
    `python -O`, so validation silently stops.
15. Register exception handlers against **Starlette's** `HTTPException`, not FastAPI's
    subclass. Otherwise the 404s and 405s Starlette itself raises bypass your handler and your
    API answers in two different error shapes.
16. One error contract for the whole API, applied to `HTTPException`, validation failures and
    your own domain exceptions. Define domain exceptions with no HTTP knowledge and map them to
    status codes in one handler module.
17. Dependencies with `yield` use `try`/`finally`, and any `except` that catches must re-raise.
    Swallowing the exception still returns 500 but leaves the server with no log line at all.
18. A `yield` dependency's exit code runs *after the response is sent* by default. Use
    `Depends(f, scope="function")` when it must close before the client sees a byte — a session
    held across a slow response is a connection-pool leak.
19. Dependency results are cached for the duration of one request, so decompose into small
    dependencies freely; a shared sub-dependency runs once. `use_cache=False` is the
    exception that needs a comment.
20. Long-lived resources — connection pools, HTTP clients, loaded models — are created in an
    `asynccontextmanager` `lifespan` and read from `request.state`, not built per request and
    not stashed on `app.state`. `@app.on_event` is deprecated and stops firing entirely once a
    `lifespan` exists.
21. `BackgroundTasks` runs in the same worker process after the response, with no retry and no
    persistence. If losing the work would page someone, return `202` with a job id and hand it
    to a real queue.
22. Override dependencies in tests with `app.dependency_overrides[dep] = fake`, and clear them
    in teardown. Patching the module attribute does nothing: the route captured the callable
    when the decorator ran.
23. `TestClient(app)` without a `with` block never runs `lifespan`, so startup state is missing
    and the failure surfaces as an unrelated `AttributeError`. Use `with TestClient(app) as
    client:` in a fixture.
24. Use `TestClient` for tests that only send requests; switch to
    `AsyncClient(transport=ASGITransport(app=app))` only when the test body itself awaits
    application code. `AsyncClient(app=app)` is not a thing any more.
25. Finish with the gate: `uv run ruff format`, `uv run ruff check` (with `FAST` enabled), the
    project's type checker, `uv run pytest`, and one request against the running app for the
    path you touched. Report the commands and their output.

## Workflows

### add-or-change-an-endpoint

- [ ] Locate the router that owns this resource and read its `APIRouter(...)` line: the prefix,
      tags and shared dependencies already applied are part of your route's contract.
- [ ] Decide the models before the handler. Request model, response model, and whether they can
      honestly be the same type — if the response has an `id` or the request has a secret, they
      cannot (`references/pydantic-models.md`).
- [ ] Write the signature: `Annotated` for every parameter and dependency, declared return type,
      `status_code` on the decorator, `responses={...}` for the error codes a client must handle.
- [ ] Pick `async def` or `def` by looking at what the body calls, not at the neighbours
      (`references/async-and-lifecycle.md`).
- [ ] Route failures through the app's existing error contract; add a domain exception plus one
      handler entry rather than a bespoke `JSONResponse`
      (`references/responses-and-errors.md`).
- [ ] Add the test in the same change: one happy path asserting the status code and body, one
      asserting an excluded field is absent, one invalid payload asserting 422
      (`references/testing.md`).
- [ ] **Gate — the contract is what you think it is:** the new tests pass, `uv run ruff check`
      is clean with `FAST` enabled, and `/openapi.json` shows the operation with the intended
      status code, response schema and no field you meant to hide.

### fix-a-slow-or-stalling-endpoint

- [ ] Confirm the shape of the problem first: latency that grows with concurrency on endpoints
      that are not themselves slow means the event loop is blocked, not that the database is.
- [ ] Grep the `async def` handlers and `async def` dependencies for blocking calls: `requests`,
      `time.sleep`, `subprocess`, synchronous database drivers, file IO. Each one is a stall for
      the whole worker.
- [ ] For each, choose: make the handler `def` (whole body blocks), or keep `async def` and wrap
      the call in `run_in_threadpool` / `asyncer.asyncify` (mixed body). Say which and why.
- [ ] Count the threadpool consumers — `def` handlers plus `def` dependencies plus explicit
      threadpool calls — against the 40-slot default and against the connection pool behind
      them.
- [ ] Run with `PYTHONASYNCIODEBUG=1` to get the loop's slow-callback warnings if the blocking
      frame is not obvious from reading.
- [ ] Check what is being rebuilt per request that should be in `lifespan`: an HTTP client, an
      engine, a parsed config, a loaded model.
- [ ] Look for work that should not be in the request at all — anything multi-second belongs in
      a queue with a `202` and a job id, not in `BackgroundTasks`.
- [ ] **Gate — the symptom is explained, not just gone:** name the blocking frame or the
      per-request construction, and show a concurrent run (not a single request) where latency
      no longer scales with concurrency.

### write-or-fix-tests

- [ ] Inventory what the suite currently touches for real: identity providers, databases,
      queues, third-party APIs. Each one is a dependency to override, not a service to mock at
      the HTTP-library level.
- [ ] Build the client in a fixture with `with TestClient(app)` so `lifespan` runs, and set the
      overrides before the client is created so no request can reach the real dependency.
- [ ] Override the dependency that produces the value (`get_current_user`, `get_db`), not the
      security scheme and not the transport. Clear `app.dependency_overrides` in teardown.
- [ ] Keep exactly one test on the real token-decoding path with a locally signed token; the
      rest override the user.
- [ ] Add async tests only where the test body must await application code, and then use
      `ASGITransport` plus `pytest.mark.anyio` with an `anyio_backend` fixture.
- [ ] Assert the HTTP surface: status code, body, absence of excluded fields, the 422 shape for
      one invalid payload. Details in `references/testing.md`.
- [ ] **Gate — offline and honest:** the suite passes with no network access, the previously
      failing test now passes, and removing the behaviour under test makes it fail again.

### migrate-legacy-fastapi-code

- [ ] Establish the floor: which FastAPI and Pydantic versions the project pins, and whether
      `pydantic.v1` shims are still imported anywhere.
- [ ] Convert dependency and parameter declarations to `Annotated` first —
      `uv run ruff check --select FAST002 --fix` does most of it mechanically, and everything
      else is easier afterwards.
- [ ] Work through the Pydantic v1 → v2 mapping in `references/pydantic-models.md`. Watch the
      one that fails silently: `Optional[X]` no longer implies a `None` default, so migrated
      `PATCH` models start rejecting requests that omit fields.
- [ ] Replace `@app.on_event` with a `lifespan` context manager, and check that no startup hook
      was left behind — once `lifespan` exists, the leftovers never run again.
- [ ] Drop `ORJSONResponse` / `UJSONResponse` (deprecated) and any `RootModel` wrappers in
      favour of declared return types.
- [ ] Delete `response_model=` where it now duplicates the return annotation (`FAST001`).
- [ ] Update the tests in the same change: `dependency_overrides` instead of patches,
      `ASGITransport` instead of `AsyncClient(app=...)`, `with TestClient(app)` for lifespan.
- [ ] **Gate — same contract, new code:** `/openapi.json` before and after the migration differ
      only where you intended, and the full suite passes with `FAST` rules enabled.

## Topic router

| Topic | Read when | File |
|---|---|---|
| `Annotated` dependencies, `yield` lifetime and exit `scope`, per-request caching, router and app-level dependencies, security schemes | Wiring anything through `Depends`, or chasing a connection held too long | `references/dependencies.md` |
| Request/response model split, `Field` placement, validators, aliases, `from_attributes`, discriminated unions, input/output schema separation, v1→v2 mapping | Designing or migrating the models at the HTTP boundary | `references/pydantic-models.md` |
| Return type vs `response_model`, status codes, `HTTPException`, exception handlers, error contract, OpenAPI metadata | A response leaks, drops fields, or the API answers errors in more than one shape | `references/responses-and-errors.md` |
| `async def` vs `def`, the 40-slot threadpool, `run_in_threadpool`, lifespan and lifespan state, background tasks vs a queue, middleware, workers | Latency grows with concurrency, or a resource is built per request | `references/async-and-lifecycle.md` |
| SSE with `EventSourceResponse`, JSON Lines, byte streaming, what breaks mid-stream, WebSockets | Building a long-lived or incremental response | `references/streaming.md` |
| `TestClient` vs `httpx.AsyncClient`, `httpx2`, lifespan in tests, `dependency_overrides`, conftest patterns, what to assert | Writing tests, or a test suite still reaching real services | `references/testing.md` |
| Install extras, `fastapi dev`/`run` and `[tool.fastapi] entrypoint`, the `FAST` ruff rules, project layout, library defaults, client generation | Setting up a project or its checks | `references/tooling.md` |

## Environment

- Install with `uv add 'fastapi[standard]'`: that brings the `fastapi` CLI and uvicorn with
  `uvloop`/`httptools`. Plain `fastapi` is the minimal install for a service that supplies its
  own server.
- Declare the app once in `pyproject.toml` so commands need no path argument:

  ```toml
  [tool.fastapi]
  entrypoint = "my_app.main:app"
  ```

  Then `fastapi dev` (reload, localhost) and `fastapi run` (production) work from anywhere in
  the project.
- Add `httpx2` as a test dependency (`uv add --group test httpx2`). Starlette 1.6's `TestClient`
  prefers it and emits a deprecation warning when it falls back to httpx v1 — which is the
  version `fastapi[standard]` installs.
- Enable the FastAPI lint group explicitly — it is off by default:

  ```toml
  [tool.ruff.lint]
  extend-select = ["FAST"]
  ```

- When a command named here does not exist in the project, say so and name the command the
  project actually uses rather than substituting your own.
