# Dependency injection

Verified against: FastAPI 0.141.

## Contents

- [Declare dependencies with Annotated](#declare-dependencies-with-annotated)
- [When something deserves to be a dependency](#when-something-deserves-to-be-a-dependency)
- [Dependencies with yield](#dependencies-with-yield)
- [Exit scope: request or function](#exit-scope-request-or-function)
- [Exceptions inside a yield dependency](#exceptions-inside-a-yield-dependency)
- [Results are cached per request](#results-are-cached-per-request)
- [Router-level and app-level dependencies](#router-level-and-app-level-dependencies)
- [Avoid class dependencies](#avoid-class-dependencies)
- [Security dependencies](#security-dependencies)
- [Long-lived resources belong to lifespan](#long-lived-resources-belong-to-lifespan)

## Declare dependencies with Annotated

Use `Annotated[T, Depends(f)]` and give it a name so it can be reused:

```python
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


def get_current_user() -> User:
    ...


CurrentUser = Annotated[User, Depends(get_current_user)]


@app.get("/items/")
async def read_items(user: CurrentUser):
    ...
```

The alternative — `user: User = Depends(get_current_user)` — puts a sentinel object in the
default slot. The signature then lies to every other caller, to type checkers, and to anyone
who wants to call the function directly in a unit test. `ruff`'s `FAST002` flags it and can
rewrite it.

`Annotated` is also the form for `Path`, `Query`, `Header`, `Cookie`, `Form`, `File` and `Body`.

## When something deserves to be a dependency

- It needs request data (a header, a query parameter, a cookie) that the handler itself does not use.
- It needs cleanup: a session, a file handle, a lock.
- It can fail early and identically for many endpoints: authentication, feature flags, rate limits.
- Several endpoints or other dependencies need the same computed value.

If the logic is pure field validation, it belongs in the Pydantic model instead. A dependency that
only reshapes a value the handler already has is indirection with no payoff.

## Dependencies with yield

Code before `yield` runs on the way in, the yielded value is injected, code after `yield` runs on
the way out. Use `try`/`finally` so the exit code runs on the error path too:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
```

Yield exactly once per dependency. FastAPI wraps the function in a context manager internally, so
do not add `@contextmanager` yourself; a `with` block *inside* the dependency is fine.

Sub-dependencies with `yield` unwind in the right order automatically: an outer dependency's exit
code still sees the inner values it depended on.

## Exit scope: request or function

`Depends()` takes a `scope`:

| `scope` | Exit code runs | Use for |
|---|---|---|
| `"request"` (default for `yield` deps) | after the response has been sent | DB sessions that may still be used while streaming the response |
| `"function"` | after the handler returns, before the response is sent | anything you must be sure is released before the client sees a byte |

```python
UserName = Annotated[str, Depends(get_username, scope="function")]
```

The constraint runs one way only: a `scope="function"` dependency may depend on both scopes, but a
`scope="request"` dependency may not depend on a `scope="function"` one. An outer dependency has to
be able to close before its sub-dependencies, because its exit code may still use them.

This matters for connection-pool exhaustion: with the default scope, a session is held until the
response is fully written, so slow clients hold database connections. Either switch to
`scope="function"` or stop holding the session across the response.

## Exceptions inside a yield dependency

An exception raised in the handler (including `HTTPException`) propagates into the `yield`
dependency, so `except SomeError:` there can see it.

If you catch it, re-raise it — `raise` on its own, or a new `HTTPException`. Swallowing it still
returns 500 to the client, but the server logs nothing at all, which is the worst possible
combination: an incident with no evidence.

Turning a caught exception into a response is the job of an exception handler, not of the
dependency.

## Results are cached per request

A dependency called several times within one request runs once; later uses get the cached value.
So decomposing into small dependencies is free:

```python
TokenData = Annotated[dict, Depends(parse_jwt)]


async def owned_post(post: PostById, token: TokenData) -> Post: ...
async def active_author(token: TokenData) -> User: ...
```

`parse_jwt` decodes once even though two dependencies ask for it. Pass `Depends(f, use_cache=False)`
when you genuinely need a fresh value each time — a new idempotency key, a second independent
session — and say why in a comment, because it is the surprising choice.

Caching is per request, not per process. Nothing here is a substitute for a real cache.

## Router-level and app-level dependencies

Cross-cutting dependencies go on the router, declared where the router is created:

```python
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)
```

Not on `include_router(...)`: the router's own contract should be readable from the router's own
definition, and moving the file should not change what guards it. Use `dependencies=[...]` (rather
than a parameter) when the return value is unused — the dependency's effect is raising, not returning.

`FastAPI(dependencies=[...])` covers every *path operation*, but **not** `/docs` and
`/openapi.json` — those are plain Starlette routes added by FastAPI itself, so a global auth
dependency leaves your whole schema readable [verified]. Hide the schema with
`FastAPI(openapi_url=None)` (which 404s `/docs` too) or serve the docs yourself behind the same
auth.

## Avoid class dependencies

`Annotated[Paginator, Depends()]` makes FastAPI introspect `__init__`, which ties your constructor
signature to your HTTP query string. Write a function dependency that returns the object instead:

```python
@dataclass
class Paginator:
    offset: int = 0
    limit: int = 100


def get_paginator(offset: int = 0, limit: int = 100) -> Paginator:
    return Paginator(offset=offset, limit=limit)


PaginatorDep = Annotated[Paginator, Depends(get_paginator)]
```

Now the class is an ordinary object you can construct in a test, and the HTTP surface is one
editable function.

## Security dependencies

The `fastapi.security` classes are dependencies that also register the scheme in OpenAPI, which is
what puts the Authorize button in the docs. Rolling your own header parsing loses that:

```python
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")
Token = Annotated[str, Depends(oauth2)]
```

From FastAPI 0.122 the built-in security utilities answer a failed authentication with **401** plus
a `WWW-Authenticate` header, not 403. To keep the old 403 for existing clients, subclass the scheme
and override `make_not_authenticated_error` — it returns the exception instance rather than raising it.

Use `Security(dep, scopes=[...])` instead of `Depends(dep)` when the dependency needs OAuth2
scopes; scopes declared along the dependency chain accumulate and arrive as `SecurityScopes`.

Authorisation that depends on the object being touched ("is this post yours?") does not belong in a
scope check. Make it a dependency that loads the object and raises, then let the handler receive the
already-authorised object.

## Long-lived resources belong to lifespan

A dependency runs per request. A connection pool, an HTTP client or a loaded model must be created
once at startup, in `lifespan`. The pattern is: build it there, read it from `request.state` in a
thin dependency, and inject that dependency.

<!-- sources: fastapi-official-skill, fastapi-docs, zhanymkanov-best-practices, kludex-fastapi-tips, microsoft-skills-py, ruff-fast-rules -->
