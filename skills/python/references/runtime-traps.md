# Runtime traps

Traps that pass both ruff and a type checker, or that produce a wrong answer
rather than an error. Nothing here is a style preference.

## Contents

- [Shared mutable state](#shared-mutable-state)
- [Late binding in closures and loops](#late-binding-in-closures-and-loops)
- [Exceptions](#exceptions)
- [Resources](#resources)
- [Equality, identity and truthiness](#equality-identity-and-truthiness)
- [Caching](#caching)
- [Iterators consumed twice](#iterators-consumed-twice)
- [Import-time side effects](#import-time-side-effects)
- [Numbers and text](#numbers-and-text)
- [Logging](#logging)

## Shared mutable state

**Mutable default arguments.** The default is evaluated once, at function
definition, and then shared by every call for the lifetime of the process:

```python
def __init__(self, audit_log: list[str] = []) -> None:   # one list, all instances
    self.audit_log = audit_log
```

```python
def __init__(self, audit_log: list[str] | None = None) -> None:
    self.audit_log = [] if audit_log is None else audit_log
```

The symptom is data from a previous request or a previous test appearing in a
fresh object. ruff's `B006` catches the literal form; it does not catch
`= DEFAULT_LIST` where the module-level list is later mutated.

**Class attributes used as instance state.** A mutable class attribute is one
object shared by every instance, and `self.items.append(x)` mutates it in place
without ever creating an instance attribute:

```python
class Cart:
    items: list[str] = []        # shared

class Cart:
    def __init__(self) -> None:
        self.items: list[str] = []   # per instance
```

The same mistake in a dataclass raises at class creation
(`ValueError: mutable default`) — use `field(default_factory=list)`.

**Module-level singletons.** A module-level dict, registry, connection or
`lru_cache` is process-global. In tests it carries state between cases; under a
threaded or forked server it is shared in ways the code did not plan for.
Anything a test needs to reset is a design signal, not just a fixture problem.

## Late binding in closures and loops

Closures capture the variable, not its value at creation time:

```python
handlers = [lambda: print(i) for i in range(3)]   # all three print 2
handlers = [lambda i=i: print(i) for i in range(3)]        # bound at definition
handlers = [functools.partial(print, i) for i in range(3)] # clearer
```

The same shape appears with `asyncio.create_task(worker(i))` in a loop when
`worker` reads a nonlocal `i` instead of taking it as an argument, and in
`@property` methods that close over a loop variable during class construction.
ruff's `B023` catches the common cases.

## Exceptions

```python
try:
    parse(raw)
except ValueError as exc:
    raise ConfigError("bad config") from exc     # keeps the original traceback
```

- `raise X from exc` preserves the cause. A bare `raise X` inside an `except`
  block still chains implicitly, but `from None` — which suppresses the context —
  is sometimes written by accident and destroys the diagnostic.
- `except Exception` does not catch `KeyboardInterrupt`, `SystemExit` or
  `asyncio.CancelledError`; they derive from `BaseException`. That is usually what
  you want. `except BaseException` without a re-raise makes a process unkillable.
- `except:` bare catches everything including those. Never.
- A `finally` that returns or raises **discards** the in-flight exception, so a
  failure disappears and the caller sees a normal return.
- An exception raised inside an `except` block replaces the original in the
  traceback's "During handling of the above exception" section — readable, but the
  original's message is no longer the one that surfaces in an alert.
- `ExceptionGroup` (3.11+) is handled with `except*`; a plain `except ValueError`
  does **not** match a `ValueError` inside a group, which is how a `TaskGroup`
  failure gets past an apparently correct handler.

## Resources

- Every file, socket, connection and lock goes through `with`. CPython usually
  closes on refcount drop, so a leak works fine until it runs on PyPy, under a
  cycle, or at enough concurrency to hit the descriptor limit.
- `contextlib.ExitStack` for a dynamic number of resources; `closing()` for
  objects that have `close()` but no context manager.
- A generator's `finally` runs when the generator is closed or collected, which
  may be much later than the loop that stopped consuming it. If cleanup timing
  matters, use `contextlib.closing` or restructure so the generator is exhausted.
- `subprocess.Popen` without `wait()` leaves a zombie; `subprocess.run` handles it.
  A `PIPE` that nobody reads deadlocks once the pipe buffer fills —
  `communicate()` exists for exactly this.
- `tempfile.NamedTemporaryFile` deletes on close, so on Windows a second opener
  cannot read it while it is open. `delete=False` plus explicit cleanup, or
  `tempfile.TemporaryDirectory`, is the portable form.

## Equality, identity and truthiness

- `is` compares identity. It is correct only for `None`, `True`, `False` and
  sentinels. `x is 0` or `s is "abc"` may work through interning and then stop
  working for a computed value — the classic Heisenbug.
- `if not value:` is true for `0`, `0.0`, `""`, `[]`, `{}` and `None` alike. When
  the difference matters — an explicit zero versus a missing field — test
  `if value is None:`.
- `==` on floats: `0.1 + 0.2 != 0.3`. Use `math.isclose`, or `decimal.Decimal` for
  money.
- Defining `__eq__` without `__hash__` makes the class unhashable; a dataclass
  needs `frozen=True` (or `eq=False`) to stay usable as a dict key.
- `NaN != NaN`, so a container holding NaN behaves inconsistently under `in`,
  `sort` and deduplication.
- `sorted(..., key=...)` is stable; `sorted` on a heterogeneous list raises at
  comparison time, which may be after some work has been done.

## Caching

```python
class Client:
    @functools.lru_cache            # keeps every self alive, forever
    def fetch(self, key: str) -> bytes: ...
```

`lru_cache` on a method includes `self` in the key, so every instance is retained
by the cache — an unbounded leak in a long-lived process, and cross-test pollution
in a suite. Cache a module-level function, or use `functools.cached_property` for
per-instance memoisation, or an explicit dict you can clear.

Also: `lru_cache` requires hashable arguments (a `list` argument raises at call
time), it is not thread-safe for the *computation* (two threads can both compute
on a miss), and `cache_clear()` is the only way to reset it — which every test
touching a cached function must do.

## Iterators consumed twice

`map`, `filter`, `zip`, generator expressions, `csv.reader`, `os.scandir` and
`itertools.*` are one-shot:

```python
rows = (parse(line) for line in fh)
if any(r.invalid for r in rows):   # consumes rows
    ...
process(rows)                      # empty, silently
```

The second pass sees nothing and reports success on zero items. Materialise with
`list(...)` when you need two passes, or restructure to one. `len()` on any of
them raises, which at least fails loudly.

## Import-time side effects

Module-level code runs on first import, in import order, and it runs during test
collection too:

- Reading configuration or environment variables at module level freezes them
  before a test's `monkeypatch` can take effect.
- Opening a connection, spawning a thread or starting a scheduler at import time
  makes importing the module a side effect, which breaks `--collect-only`,
  documentation builds and anything that imports for introspection.
- Mutable module state initialised at import cannot be reset without
  `importlib.reload`, which has its own hazards (old objects keep the old class).

Put it in a function, a factory or a lazily-initialised accessor. `__init__.py`
that imports every submodule for convenience makes the import cost of the package
the sum of all of them, and turns any circular import into a hard failure.

## Numbers and text

- Integer division `//` floors toward negative infinity: `-7 // 2 == -4`. `%`
  follows, so `-7 % 2 == 1`.
- `round` uses banker's rounding: `round(0.5) == 0`, `round(2.5) == 2`.
- `int(x)` on a float truncates toward zero (`int(-1.7) == -1`), which disagrees
  with both `//` and `round`. On a string it tolerates surrounding whitespace and
  interior underscores (`int(" 4_2") == 42` [verified]) but not a trailing one, so
  input validation cannot lean on it. `float("nan")` and `float("inf")` succeed
  silently, which is how a NaN reaches a comparison much later.
- `open()` without `encoding=` uses the platform default, so a file that reads
  fine locally fails in a container with a different locale. Always pass
  `encoding="utf-8"` (ruff `PLW1514` / `W1514`).
- `str.strip("abc")` strips *characters*, not the substring — `"abcdef".strip("abc")`
  is `"def"` but `"abcabc".strip("abc")` is `""`. Use `removeprefix`/`removesuffix`.
- `datetime.now()` is naive local time. Use `datetime.now(tz=UTC)` and store UTC;
  naive datetimes compare against aware ones with a `TypeError`, usually in
  production and not in the test that used a fixed naive value.

## Logging

- `logging.info("user %s", user_id)` defers formatting to when the record is
  actually emitted; an f-string formats unconditionally, which costs on a disabled
  level and loses the structured arguments a handler could use.
- `logger.exception(...)` inside an `except` block attaches the traceback;
  `logger.error(...)` does not. An error log without the traceback is the most
  common reason an incident takes an extra hour.
- `logging.basicConfig` in library code hijacks the application's configuration.
  Libraries get `logging.getLogger(__name__)` and nothing else.
- `print` in library code writes to whatever stdout happens to be, unfiltered by
  level and invisible to log aggregation. In a CLI, print is the output channel and
  is correct; everywhere else it is a missing log line.

<!-- sources: wshobson-python, beagle-python, developer-kit-python, probabl-python-style, python-docs, ruff-docs -->
