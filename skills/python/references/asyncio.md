# asyncio: task lifetime, cancellation and blocking

Verified against: Python 3.11–3.14.

## Contents

- [Decide whether async is the answer](#decide-whether-async-is-the-answer)
- [Task lifetime](#task-lifetime)
- [TaskGroup versus gather](#taskgroup-versus-gather)
- [Cancellation](#cancellation)
- [Timeouts](#timeouts)
- [Blocking calls](#blocking-calls)
- [Async context managers and cleanup](#async-context-managers-and-cleanup)
- [Debugging a stalled or lost task](#debugging-a-stalled-or-lost-task)
- [Sync/async boundaries](#syncasync-boundaries)

## Decide whether async is the answer

| Situation | Approach |
|---|---|
| Many concurrent network or database calls | asyncio |
| CPU-bound work | `ProcessPoolExecutor` / `multiprocessing`; asyncio buys nothing |
| Mixed IO and CPU | asyncio, with CPU work in `asyncio.to_thread` or a process pool |
| A script with a handful of requests | stay synchronous; it is easier to read and to debug |

Keep a call path entirely sync or entirely async. A half-converted path is where
one synchronous call sits inside a coroutine and stalls the loop for everybody —
and it will not show up as an error, only as latency.

## Task lifetime

The event loop keeps only **weak** references to tasks. A task nobody holds a
reference to can be garbage collected before it completes, which is the
"sometimes it just doesn't happen" bug:

```python
asyncio.create_task(refresh_pricing(sku))   # may never run to completion
```

Two correct forms:

```python
# structured: the group awaits every child before exiting
async with asyncio.TaskGroup() as tg:
    tg.create_task(refresh_pricing(sku))

# genuinely fire-and-forget: own the reference explicitly
self._pending: set[asyncio.Task[None]] = set()
task = asyncio.create_task(refresh_pricing(sku))
self._pending.add(task)
task.add_done_callback(self._pending.discard)
```

The `add_done_callback(discard)` matters: without it the set grows forever, which
converts a lost-task bug into a memory leak.

Fire-and-forget has a second failure mode that a strong reference does not fix:
nothing ever awaits the task, so its exception is only reported when it is
collected — as "Task exception was never retrieved" on stderr, long after the
request it belonged to returned. Give every background task an explicit join
point (a `drain()` the caller awaits before the loop closes) or a done-callback
that logs failures.

ruff's `RUF006` flags the dangling `create_task` case; enable it.

## TaskGroup versus gather

```python
async with asyncio.TaskGroup() as tg:
    a = tg.create_task(fetch_user(uid))
    b = tg.create_task(fetch_orders(uid))
user, orders = a.result(), b.result()   # after the block: both are done
```

`TaskGroup` (3.11+) is the default because of what it does on failure: when one
child raises, the remaining children are **cancelled** and the group raises an
`ExceptionGroup` when the block exits. `gather` does the opposite — the first
exception propagates to the awaiting task while its siblings **keep running**,
unobserved.

```python
try:
    async with asyncio.TaskGroup() as tg:
        ...
except* ValueError as eg:          # except* unpacks an ExceptionGroup
    handle(eg.exceptions)
```

Reach for `gather` only when you need results positionally in one expression, or
when `return_exceptions=True` (collect every outcome, failures included) is
genuinely what you want. Note that `gather(..., return_exceptions=True)` returns
exception objects in the result list rather than raising, so a caller that does
not inspect the list swallows every failure silently.

`asyncio.as_completed` does not cancel the remaining tasks when the iteration
stops early either — the same leak, one level down.

## Cancellation

`CancelledError` derives from `BaseException`, deliberately, so `except
Exception:` does not catch it. Two consequences:

```python
try:
    await do_work()
except asyncio.CancelledError:
    await release_lock()     # cleanup is fine
    raise                    # but it must continue to propagate
finally:
    await close_connection() # runs on cancellation too
```

- Catching it and not re-raising breaks `TaskGroup` and `asyncio.timeout`, both of
  which implement their behaviour *with* cancellation. A coroutine that swallows
  it turns a timeout into a hang.
- `task.uncancel()` exists for the rare case where suppression is genuinely
  intended; needing it usually means the cancellation should have been handled a
  level up.
- Cleanup after cancellation must itself be cancellation-safe: an `await` inside a
  cancelled task's `finally` can be interrupted again. `asyncio.shield` protects a
  critical await, at the cost of the caller's timeout no longer bounding it.

## Timeouts

```python
async with asyncio.timeout(10):      # 3.11+
    await long_running_task()
```

The context manager cancels the inner task and converts the resulting
`CancelledError` into `TimeoutError`, so callers catch `TimeoutError` — not
`CancelledError`. `asyncio.timeout_at` takes an absolute deadline, and
`Timeout.reschedule` moves it, which is how you implement a per-chunk deadline on
a stream.

`asyncio.wait_for` is the older single-awaitable equivalent and remains fine.
Hand-rolled `asyncio.sleep`-plus-flag timeouts are not: they leave the slow task
running behind the timeout.

A network timeout is not a substitute. `httpx.AsyncClient(timeout=...)` bounds one
request; the asyncio timeout bounds the whole operation including retries and
connection acquisition. Production code usually wants both.

## Blocking calls

Anything that does not yield to the loop stalls every other task. The usual
offenders inside `async def`:

- `time.sleep` — use `await asyncio.sleep`
- `requests`, `urllib`, sync `httpx.get` — use `httpx.AsyncClient` or `aiohttp`
- synchronous DB drivers (`psycopg2`, `sqlite3`, sync SQLAlchemy) — use the async
  driver, or `asyncio.to_thread`
- `subprocess.run` — use `asyncio.create_subprocess_exec`
- `open().read()` on a network filesystem, `Path.write_text` of a large payload
- CPU-heavy work: JSON of megabytes, crypto, compression, big regex scans

```python
result = await asyncio.to_thread(legacy_blocking_call, arg)
```

`to_thread` propagates the current `contextvars.Context`, so request-scoped
context survives the hop. It does not help with CPU-bound work under the GIL —
that needs a process pool via `loop.run_in_executor`.

ruff's `ASYNC` rules catch several of these statically. They cannot catch a
blocking call hidden two frames deep in your own helper, so the call-path audit
still has to happen by reading.

## Async context managers and cleanup

```python
class Client:
    async def __aenter__(self) -> "Client": ...
    async def __aexit__(self, *exc: object) -> None: ...

async with Client() as c:
    ...
```

- Long-lived clients (`httpx.AsyncClient`, DB pools) belong at application scope,
  entered once. Creating one per request destroys connection pooling — a common
  cause of "async made it slower".
- `contextlib.asynccontextmanager` for the decorator form,
  `contextlib.AsyncExitStack` when the number of resources is dynamic.
- An async generator's `finally` runs when the generator is closed, which may be
  at garbage-collection time rather than where you expect. `aclosing()` makes the
  cleanup point explicit.

## Debugging a stalled or lost task

```python
asyncio.run(main(), debug=True)      # or PYTHONASYNCIODEBUG=1
```

Debug mode logs callbacks that take longer than 100 ms — pointing directly at the
blocking frame — and warns about coroutines that were never awaited.

Other tools, in order of usefulness:

- `asyncio.all_tasks()` plus `task.get_coro()` in a signal handler or a debug
  endpoint: a snapshot of what is actually pending right now.
- `asyncio.current_task().get_stack()` for where a suspended task is parked.
- `filterwarnings = ["error"]` in the pytest config turns "coroutine was never
  awaited" from a warning into a test failure, which is where it should be caught.
- A missing `await` on a coroutine that returns nothing is invisible at runtime
  without those warnings; the type checker catches it if the caller's return type
  is annotated.

## Sync/async boundaries

- `asyncio.run` once, at the top of the program. Calling it twice creates two
  loops and any object bound to the first (a pool, a lock, a queue) breaks in the
  second, usually as "attached to a different loop".
- Never call `asyncio.run` inside a running loop; use `await` there. If you are in
  synchronous code called *from* a loop, hand the work back with
  `loop.call_soon_threadsafe` or `asyncio.run_coroutine_threadsafe`.
- `asyncio.Lock`, `Queue`, `Event` are not thread-safe and are bound to their
  loop. For cross-thread work use `queue.Queue` plus `run_coroutine_threadsafe`.
- A short-lived loop per request (a sync wrapper that calls `asyncio.run`) closes
  the loop as soon as it returns, killing any task still pending. That is the
  other half of the lost-background-task bug, and no amount of strong references
  fixes it — the work has to be awaited before the loop closes.

<!-- sources: wshobson-python, developer-kit-python, awesome-copilot-mcp-python, python-docs, ruff-docs -->
