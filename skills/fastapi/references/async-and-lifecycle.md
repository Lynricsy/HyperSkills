# Async boundaries, lifespan and background work

Verified against: FastAPI 0.141, Starlette 1.6, AnyIO 4.

## Contents

- [The decision: async def or def](#the-decision-async-def-or-def)
- [The threadpool has 40 slots](#the-threadpool-has-40-slots)
- [Pushing a blocking call out of an async handler](#pushing-a-blocking-call-out-of-an-async-handler)
- [Finding the blocking frame](#finding-the-blocking-frame)
- [Lifespan](#lifespan)
- [Lifespan state instead of app.state](#lifespan-state-instead-of-appstate)
- [Background tasks versus a task queue](#background-tasks-versus-a-task-queue)
- [Middleware](#middleware)
- [Workers and concurrency](#workers-and-concurrency)

## The decision: `async def` or `def`

The body decides, not preference:

| Handler body | Declare | Runs on |
|---|---|---|
| only awaited calls (async driver, `httpx.AsyncClient`, `asyncio.sleep`) | `async def` | the event loop |
| any blocking call (sync DB driver, `requests`, `time.sleep`, file IO, a CPU loop) | `def` | the threadpool |
| mixed | `async def` + push the blocking part out (below) | both |

The same rule applies to dependencies, which are not exempt: a `def` dependency also runs in the
threadpool, so a chain of `def` dependencies costs several threadpool slots per request.

Getting it wrong in the `async def` direction is the expensive mistake. One `requests.get` inside
`async def` stalls **every** in-flight request on that worker, not just its own — the loop cannot
schedule anything while a native call holds the thread. The symptom is latency that scales with
concurrency for endpoints that are not even slow.

Getting it wrong in the `def` direction only costs a threadpool slot and a context switch. That is
why "when in doubt, use `def`" is the safe default rather than "prefer async".

## The threadpool has 40 slots

The AnyIO default thread limiter has 40 tokens
(`anyio.to_thread.current_default_thread_limiter().total_tokens == 40`) [verified]. Every `def`
handler, every `def` dependency and every `run_in_threadpool` call takes one for its duration. Once
they are gone, requests queue with no visible error.

If that ceiling is genuinely the constraint — many endpoints on a sync database driver — raise it in
`lifespan`, where it applies before the first request:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    anyio.to_thread.current_default_thread_limiter().total_tokens = 100
    yield
```

Raise it deliberately and in step with the pool it feeds: 100 threads in front of a 20-connection
database pool moves the queue rather than shortening it.

## Pushing a blocking call out of an async handler

When a handler must stay `async def` — it awaits other things too — wrap the blocking call:

```python
from fastapi.concurrency import run_in_threadpool

@router.get("/report")
async def report() -> Report:
    data = await service.fetch()             # async
    pdf = await run_in_threadpool(render_pdf, data)   # blocking, now off the loop
    return Report(url=upload(pdf))
```

`asyncer.asyncify(fn)(...)` is the same thing with a nicer type signature, and `asyncer.syncify`
does the reverse for calling async code from a `def` handler. Add `asyncer` when a codebase crosses
the boundary often; `run_in_threadpool` is enough for one call.

Neither helps a CPU-bound call: the GIL means a thread does not give you a second core. Genuine
computation goes to a process pool or an external worker.

## Finding the blocking frame

Reading code for `requests`, `time.sleep`, `open(...).read()`, `subprocess.run` and synchronous
database drivers inside `async def` catches most of it. For the rest, run with asyncio debug mode
(`PYTHONASYNCIODEBUG=1`): the loop logs a warning naming any callback that ran longer than its
threshold, which points at the frame instead of at the endpoint.

`fastapi dev` reloads on change but does not enable debug mode; set the environment variable.

## Lifespan

Resources shared by all requests — a connection pool, an HTTP client, a loaded model — are created
once in `lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
    async with AsyncClient(base_url=settings.upstream) as client:
        yield {"client": client}


app = FastAPI(lifespan=lifespan)
```

`@app.on_event("startup")` and `("shutdown")` are deprecated. They are also all-or-nothing: pass a
`lifespan` and the event handlers stop being called, which is a silent failure if a migration left
some behind.

Lifespan runs once per worker process, so anything in it happens N times for N workers — a
migration or a schema check there will run concurrently on deploy. Those belong in a release step,
not in application startup.

Lifespan does not run for sub-applications mounted with `app.mount()`; a mounted sub-app needs its
own, and nothing warns you.

Under test, a bare `TestClient(app)` never runs lifespan; the client has to be entered as a
context manager.

## Lifespan state instead of `app.state`

Yield a mapping from `lifespan` and read it from `request.state`:

```python
class State(TypedDict):
    client: AsyncClient


@router.get("/proxy")
async def proxy(request: Request) -> dict[str, Any]:
    client = cast(AsyncClient, request.state.client)
    return (await client.get("/upstream")).json()
```

This works [verified] and is preferable to `app.state`: the state is typed in one place, and it is
scoped to the lifespan that created it rather than to a global object any module can mutate.

Wrap the `request.state` read in a small dependency rather than repeating the `cast` in every
handler; that also gives tests one thing to override.

## Background tasks versus a task queue

`BackgroundTasks` runs the function after the response, in the same worker process. There is no
retry, no persistence, no visibility, and a redeploy or a crash loses the work.

| Use `BackgroundTasks` | Use an external queue (Celery, arq, RQ, Dramatiq) |
|---|---|
| sub-second work | seconds to minutes |
| losing it is acceptable | needs retries or a dead-letter path |
| in-process side effect: one email, one audit row | CPU-heavy, or wants its own worker pool |
| no scheduling | cron, ETA, rate limiting, fan-out |

The test: if you would page someone when the work is silently lost, it does not belong in
`BackgroundTasks`. For queued work, return `202` with a job id and an endpoint to poll.

Declaring a `BackgroundTasks` parameter works in dependencies and sub-dependencies too; FastAPI
merges them into the same object, so tasks added anywhere in the chain run together after the
response.

Exceptions inside a background task happen after the response has been sent, so no exception handler
can convert them. Each task needs its own try/except and its own log line, or failures are invisible.

## Middleware

`@app.middleware("http")` and `BaseHTTPMiddleware` are convenient and carry a measurable overhead,
because each request is bridged through an anyio stream. For cross-cutting work on a hot path, write
a pure ASGI middleware:

```python
class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        ...
        await self.app(scope, receive, send)
```

Two more reasons to prefer it: middleware sees the raw ASGI scope, so it cannot use dependencies,
and a `BaseHTTPMiddleware` that reads `request.body()` consumes the stream in a way that has
historically broken streaming handlers.

Anything that needs dependency injection, per-route configuration or the parsed body is a dependency,
not a middleware.

`CORSMiddleware` is the exception you should still use as-is, and it must be added before any
middleware that can return early, or preflight responses lose their headers.

## Workers and concurrency

`fastapi run` serves the app in production mode; `fastapi dev` adds reload and binds to localhost
only. Declare the app once in `pyproject.toml` so neither command needs a path argument:

```toml
[tool.fastapi]
entrypoint = "my_app.main:app"
```

[verified against 0.141: `fastapi run` prints `Using import string: my_app.main:app` and serves.]

Process count is a deployment decision: one worker per core is the usual starting point for
CPU-bound work, more for IO-bound work on `def` handlers, and exactly one when a platform already
runs one container per replica. Whatever the number, remember each worker has its own event loop,
its own 40-slot threadpool, its own lifespan and its own in-process caches — anything you cache in a
module-level dict is per worker, and any `BackgroundTasks` work dies with that worker.

<!-- sources: fastapi-official-skill, fastapi-docs, kludex-fastapi-tips, zhanymkanov-best-practices, starlette-docs, microsoft-skills-py -->
