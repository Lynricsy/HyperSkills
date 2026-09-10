# Responses, status codes and errors

Verified against: FastAPI 0.141.

## Contents

- [Return type first, response_model second](#return-type-first-response_model-second)
- [The response is validated twice](#the-response-is-validated-twice)
- [Status codes per operation](#status-codes-per-operation)
- [Do not pick a JSON response class](#do-not-pick-a-json-response-class)
- [HTTPException](#httpexception)
- [One error contract for the whole API](#one-error-contract-for-the-whole-api)
- [Custom exception handlers](#custom-exception-handlers)
- [Overriding validation errors](#overriding-validation-errors)
- [Returning a Response directly](#returning-a-response-directly)
- [What ends up in OpenAPI](#what-ends-up-in-openapi)

## Return type first, `response_model` second

Annotate the return type. FastAPI uses it to validate, filter, document and serialise:

```python
@router.get("/items/{item_id}")
async def get_item(item_id: int) -> Item: ...
```

Use `response_model=` only when the declared public schema differs from what the function actually
returns — the classic case being an internal object filtered down to a public model:

```python
@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int) -> Any:
    return internal_item  # has secret_key; Item does not declare it
```

Annotate the return as `Any` in that case, otherwise the type checker and FastAPI disagree about
which type wins. Writing both a matching return type *and* `response_model` for the same type is
redundant — `ruff`'s `FAST001` flags it.

A return annotation FastAPI cannot build a schema from — a `Response` subclass, an ORM class, any
non-Pydantic type — raises `FastAPIError` with the message "Invalid args for response field" at
import time, not at request time [verified]. `response_model=None` is the fix: it tells FastAPI to
skip the response field entirely and keeps the annotation for your type checker.

## The response is validated twice

FastAPI runs the returned value through `jsonable_encoder` and then validates it against the
response field. A model you constructed yourself is therefore built twice per request: once by your
code, once by FastAPI [verified — an `after` model validator fires twice per request, both with
`response_model=` and with a return annotation].

Consequences worth acting on:

- Do not put side effects, logging or expensive computation in a model validator on a response model.
- Returning a plain dict from the handler is not slower than returning a model; the model gets built
  either way. Return whichever is clearer.
- Do not chase this with `ORJSONResponse` (see below) or by dropping the response model. Pydantic
  serialises in Rust once validation is done; the second construction is the cost of getting the
  filtering and the schema for free.

## Status codes per operation

Declare the success code on the decorator, not by returning a hand-built response:

| Operation | Code | Notes |
|---|---|---|
| create | `201` | return the created resource |
| accepted for later processing | `202` | return a job id, not the result |
| delete / update with no body | `204` | with `response_model=None` and a `-> None` return |
| everything else | `200` | the default |

```python
@router.post("/items", status_code=201)
async def create_item(payload: ItemCreate) -> Item: ...


@router.delete("/items/{item_id}", status_code=204, response_model=None)
async def delete_item(item_id: int) -> None: ...
```

A `204` sends no body: Starlette drops whatever the handler returned, with no error anywhere
[verified]. So a `204` endpoint that returns data does not fail — the data just never arrives, and
the bug shows up in the client.

Read-only operations are `GET`; a `GET` that mutates state breaks caches, prefetchers and retries.
State-changing operations get `POST`, `PUT`, `PATCH` or `DELETE`.

## Do not pick a JSON response class

`ORJSONResponse` and `UJSONResponse` are deprecated. Declare a return type or response model and let
Pydantic serialise; the fast path is in Rust and needs no extra library.

`JSONResponse` still has its uses — a hand-built error body, a redirect, a custom header set — but
never as a performance choice.

## HTTPException

```python
raise HTTPException(status_code=404, detail="Item not found")
```

Raise it from anywhere in the call stack, including helpers and dependencies; the rest of the
handler does not run. FastAPI's `HTTPException` accepts any JSON-able `detail`, and takes
`headers=` for cases the spec requires them — `WWW-Authenticate` on a 401, `Retry-After` on a 429.

FastAPI's `HTTPException` subclasses Starlette's. Register handlers against **Starlette's** class:

```python
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException): ...
```

Registering against FastAPI's own class means the exceptions Starlette itself raises — 404 for an
unmatched route, 405 for the wrong method — bypass your handler and come back in the framework's
default shape. Then your API has two error formats and only one of them is documented.

Do not raise `HTTPException` from a Pydantic validator. A raised `ValueError` there becomes the
standard 422 with the field path filled in; `HTTPException` loses that.

## One error contract for the whole API

Pick one error body shape and make every path produce it: your own exceptions, `HTTPException`,
validation failures, and unhandled exceptions. For a new API, RFC 9457 Problem Details
(`type`, `title`, `status`, `detail`, `instance` under `application/problem+json`) is the default
worth having; the point is not the specific keys but that clients parse one shape.

FastAPI's default shape is `{"detail": ...}` for `HTTPException` and
`{"detail": [{"loc": ..., "msg": ..., "type": ...}]}` for validation errors — two different shapes
out of the box. If you keep the defaults, say so and document both; if you standardise, override
both handlers, not just the one you noticed.

Define domain exceptions that carry no HTTP knowledge and map them at the edge:

```python
class ItemNotFound(Exception):
    def __init__(self, item_id: int) -> None:
        self.item_id = item_id


@app.exception_handler(ItemNotFound)
async def item_not_found(request: Request, exc: ItemNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"item {exc.item_id} not found"})
```

The service layer stays testable without an HTTP context, and the status-code decision lives in one
file.

## Custom exception handlers

```python
@app.exception_handler(MyError)
async def handler(request: Request, exc: MyError) -> Response: ...
```

Handlers are matched by exception class, most specific first. Two limits to know:

- A handler for bare `Exception` runs, but the response then goes out *after* Starlette's
  `ServerErrorMiddleware` has already been involved; keep it to logging plus a generic 500 body and
  do not rely on it for control flow.
- Exceptions raised inside a `BackgroundTasks` function happen after the response is sent, so no
  handler can turn them into a response. They need their own try/except and their own logging.

`fastapi.exception_handlers` exports the defaults (`http_exception_handler`,
`request_validation_exception_handler`), so a custom handler can log and then delegate instead of
reimplementing the body.

## Overriding validation errors

```python
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"errors": exc.errors()})
```

`exc.errors()` is the structured list; `exc.body` is the raw payload that failed. Logging `exc.body`
is tempting and is how request bodies with passwords and tokens end up in log aggregation — redact
or log only the field paths.

A `ResponseValidationError` means *your* code returned something that does not match the declared
response model. It is a 500, and it should stay a 500: catching it hides a bug in your handler.

## Returning a `Response` directly

Returning a `Response` (or `JSONResponse`, `RedirectResponse`, `FileResponse`) skips validation,
filtering and serialisation entirely, and FastAPI cannot document the shape. Do it for redirects,
files and pre-encoded payloads. For anything you want in the schema, return data and let the
response model do its job.

To change only the status code or add headers while keeping the model, declare a `Response`
parameter and mutate it:

```python
@router.put("/items/{item_id}")
async def upsert(item_id: int, payload: ItemCreate, response: Response) -> Item:
    item, created = await service.upsert(item_id, payload)
    response.status_code = 201 if created else 200
    return item
```

Note that the declared `status_code` is what OpenAPI documents; a runtime override is invisible to
clients reading the schema, so document the alternative with `responses={...}`.

## What ends up in OpenAPI

- `summary` comes from the function name unless you pass it; the docstring becomes `description`,
  and Markdown in it renders.
- `tags` group operations in the UI. Set them on the `APIRouter`, not per route.
- `responses={404: {"model": ErrorBody}}` documents the error shapes a client must handle. Without
  it your schema claims every call succeeds.
- `include_in_schema=False` hides an operation; `deprecated=True` marks it without removing it.
- `operation_id` is what client generators turn into method names. FastAPI derives one from the
  function name and path, which produces long names and changes when you rename a function — set it
  explicitly for any API with generated clients.
- Response models are only documented if FastAPI can see them, which is another reason a bare
  `Response` return is a documentation hole.

<!-- sources: fastapi-official-skill, fastapi-docs, starlette-docs, zhanymkanov-best-practices, microsoft-skills-py, ruff-fast-rules -->
