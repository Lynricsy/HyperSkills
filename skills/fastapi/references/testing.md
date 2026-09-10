# Testing a FastAPI application

Verified against: FastAPI 0.141, Starlette 1.6, httpx2 2.12.

## Contents

- [Which client](#which-client)
- [Install httpx2](#install-httpx2)
- [TestClient and lifespan](#testclient-and-lifespan)
- [The async client needs an explicit transport](#the-async-client-needs-an-explicit-transport)
- [Override dependencies, do not patch them](#override-dependencies-do-not-patch-them)
- [A conftest that scales](#a-conftest-that-scales)
- [Faking authentication](#faking-authentication)
- [What to assert](#what-to-assert)
- [Background tasks in tests](#background-tasks-in-tests)
- [Streaming endpoints](#streaming-endpoints)

## Which client

| Test body | Client |
|---|---|
| only sends requests and asserts on responses | `TestClient` — a plain `def` test |
| must `await` application code itself (an async repository, an async fixture) | `httpx.AsyncClient` + `ASGITransport` in an async test |

`TestClient` drives the ASGI app from a sync test by running the event loop for you. That machinery
is exactly what stops working inside an `async def` test, which is the only reason to switch — not
"the app is async, so the test should be".

Default to `TestClient`. It is shorter, it runs lifespan, and it needs no async plugin.

## Install `httpx2`

Starlette 1.6's test client imports `httpx2` and falls back to `httpx` with
`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2
instead.` [verified]. `fastapi[standard]` pulls in httpx v1 only, so a default install hits the
warning — and a project with `filterwarnings = ["error"]` fails on import.

```bash
uv add --group test httpx2
```

Both packages can coexist; `httpx2` exposes the same `AsyncClient` / `ASGITransport` names.

## `TestClient` and lifespan

```python
with TestClient(app) as client:
    response = client.get("/")
```

A bare `TestClient(app)` **never runs lifespan** [verified]: startup state is missing, so the first
handler that reads it fails with `AttributeError` on `request.state` rather than with anything that
names the cause. Use the `with` form whenever the app has a `lifespan`, and prefer a fixture so no
test can forget:

```python
@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
```

The flip side: if lifespan opens real connections, every test module pays for it. Either override
the lifespan-provided resources (below), or point them at a test double before the fixture enters.

## The async client needs an explicit transport

```python
import pytest
from httpx2 import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

`AsyncClient(app=app, ...)` no longer works — httpx removed the `app` shortcut, so the parameter is
just an unexpected keyword [verified: `"app" in signature(AsyncClient.__init__).parameters` is
false]. Every pre-2024 example and most community skills still show it.

`ASGITransport` does **not** run lifespan. When the async test needs startup state, drive it
yourself with `asgi-lifespan`'s `LifespanManager`, or get the state from the same fixture that
supplies it to the app.

Use `pytest.mark.anyio` with an `anyio_backend` fixture — FastAPI and Starlette are built on AnyIO,
and this avoids a second async plugin:

```python
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

`pytest.mark.asyncio` is fine if the project already uses `pytest-asyncio`, but an unregistered
marker silently does nothing more than warn, and the coroutine is never awaited.

## Override dependencies, do not patch them

```python
app.dependency_overrides[get_current_user] = lambda: User(id=1, email="t@example.com")
```

The key is the original callable, the value is the replacement. FastAPI resolves the override at
request time for every place the dependency is used — path operation, router `dependencies=[...]`,
sub-dependency.

`monkeypatch.setattr("my_app.deps.get_current_user", fake)` does **not** work [verified]: the route
captured the function object when the decorator ran, so rebinding the module attribute afterwards
changes nothing. This is the single most common wasted hour in a FastAPI test suite — the patch
applies cleanly, the test still calls production.

Overrides live on the app object and therefore leak between tests. Clear them in fixture teardown:

```python
@pytest.fixture
def override_user() -> Iterator[None]:
    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()
```

Use `.clear()` rather than `= {}` if anything else holds a reference to the dict.

An override may itself be a `yield` function, which is how you inject a session bound to a
transaction that is rolled back afterwards.

## A conftest that scales

```python
@pytest.fixture
def session() -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    with Session(bind=connection) as s:
        yield s
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Two properties make this worth copying: the override is set before the client is built, so no
request can slip through against the real dependency; and the teardown order is
client-then-overrides-then-transaction, so nothing is rolled back while a request could still be
running.

Build the app itself with a factory (`create_app(settings)`) when the suite needs several
configurations. Overriding settings on one module-level `app` works until two tests want different
settings, at which point ordering decides the result.

## Faking authentication

Override the dependency that produces the user, not the one that parses the token, and definitely
not the identity provider's HTTP client:

```python
app.dependency_overrides[get_current_user] = lambda: admin_user
```

Overriding the security scheme itself (`oauth2_scheme`) leaves your own token-decoding code
untested while still not exercising the provider. Exactly one test should go through the real
decoding path with a locally signed token; the rest override the user.

## What to assert

Assert on the HTTP surface, because that is the contract:

- `response.status_code` — a route that returns 200 where 201 was intended is a contract change no
  unit test on the service will catch.
- `response.json()` — and specifically that fields you excluded are **absent**:
  `assert "password_hash" not in body`. A leak test that checks the happy fields only passes forever.
- Aliases: assert on the response body, not on `model_dump()`, since path operations serialise with
  aliases by default while `model_dump()` does not.
- The 422 shape for one representative invalid payload, so a change to the error contract is visible.
- `client.get("/openapi.json")` when generated clients depend on the schema — it catches an
  accidentally removed `operation_id` or `response_model`.

## Background tasks in tests

`TestClient` runs background tasks before the response is handed back to the test, so an assertion
right after the call already sees their effect [verified]. That is convenient and unlike
production, where the client gets the response first — do not write assertions that depend on the
ordering.

Exceptions inside a background task surface as test errors under `TestClient` and as silent
failures in production. A task that only works because the test client is strict is not working.

## Streaming endpoints

Use the streaming API rather than `response.text`, which waits for the whole body:

```python
with client.stream("GET", "/events") as response:
    lines = [line for _, line in zip(range(3), response.iter_lines())]
```

Bound what you read. A test that consumes an unbounded stream to completion hangs the suite instead
of failing it.

<!-- sources: fastapi-docs, starlette-docs, kludex-fastapi-tips, fastapi-official-skill -->
