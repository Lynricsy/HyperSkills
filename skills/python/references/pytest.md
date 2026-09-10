# pytest: configuration, fixtures and isolation

Verified against: pytest 9.1.x.

## Contents

- [Where configuration lives, and the version trap](#where-configuration-lives-and-the-version-trap)
- [Settings that pay for themselves](#settings-that-pay-for-themselves)
- [Fixtures and scope](#fixtures-and-scope)
- [conftest.py layering](#conftestpy-layering)
- [Parametrization](#parametrization)
- [Test isolation: diagnosing order-dependent failures](#test-isolation-diagnosing-order-dependent-failures)
- [Mocking](#mocking)
- [Async tests](#async-tests)
- [Plugins](#plugins)
- [Coverage](#coverage)
- [Invocations worth memorising](#invocations-worth-memorising)

## Where configuration lives, and the version trap

Two table names work in `pyproject.toml` and they have different floors:

```toml
# pytest 9.0+: native TOML types
[tool.pytest]
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--strict-config"]

# pytest 6.0+: INI-style values inside TOML
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
```

Use `[tool.pytest]` only when the project requires pytest 9 or newer. With an
older pytest the table is not recognised at all: `testpaths`, `markers`,
`filterwarnings` and `asyncio_mode` are silently dropped, tests still run, and
the missing enforcement looks like the settings simply had no effect.

The failure mode is that `requires-python`-style pins do not protect you here: a
`pytest>=8.3` constraint resolves to whatever the lockfile happens to hold, so the
same `pyproject.toml` enforces its settings on one machine and ignores them on
another. Measured against the same config declaring `markers = ["slow: ..."]`
under `[tool.pytest]` [verified]: pytest 9.1.1 registers the marker
(`pytest --markers` lists it), pytest 8.3.5 emits `PytestUnknownMarkWarning:
Unknown pytest.mark.slow` and applies none of the table. Symptom to recognise: a
declared marker still warns as unknown, or `filterwarnings = ["error"]` fails to
turn a warning into a failure.

File precedence: `pytest.toml` / `.pytest.toml`, then `pytest.ini` / `.pytest.ini`,
then `pyproject.toml`, then `tox.ini`, then `setup.cfg`. The **first match wins
and the others are not merged**, so a leftover empty `pytest.ini` at the repo root
disables an entire `pyproject.toml` configuration. Confirm which file pytest chose
by reading the `configfile:` line in its startup header.

## Settings that pay for themselves

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
markers = [
  "slow: takes more than a second",
  "integration: needs an external service",
]
filterwarnings = [
  "error",                                  # a new DeprecationWarning fails CI
  "ignore::DeprecationWarning:vendor_lib.*", # except from code you do not own
]
```

- `--strict-markers` turns a typo'd `@pytest.mark.slwo` into an error instead of a
  silently unapplied marker.
- `--strict-config` errors on unknown config keys — the other half of the
  silent-misconfiguration problem above.
- `-ra` prints a summary of every non-passing outcome, so skips and xfails stop
  hiding in the scroll.
- `filterwarnings = ["error"]` is how you find out about a deprecation before the
  release that removes it.

## Fixtures and scope

| Scope | Created once per | Safe when |
|---|---|---|
| `function` (default) | test | always |
| `class` | test class | the object is immutable or reset |
| `module` | file | as above |
| `package` | package directory | as above |
| `session` | whole run | genuinely read-only or externally managed |

Anything above `function` scope that tests can mutate makes the suite
order-dependent. That is the single most common cause of "passes alone, fails in
the suite". If a slow resource must be shared, share the expensive part and reset
the mutable part:

```python
@pytest.fixture(scope="session")
def engine():                       # expensive, immutable
    return create_engine("sqlite://")

@pytest.fixture
def db(engine):                     # cheap, per-test, rolled back
    conn = engine.connect()
    tx = conn.begin()
    yield conn
    tx.rollback()
    conn.close()
```

Cleanup goes after `yield`, and it runs even when the test fails. It does **not**
run if the setup half raised, so anything acquired before the `yield` that can
fail belongs in its own fixture or a `try`.

A factory fixture is the answer when a test needs several instances or needs to
choose parameters:

```python
@pytest.fixture
def make_order():
    created = []
    def _make(sku="SKU-1", qty=1):
        order = Order(sku=sku, qty=qty)
        created.append(order)
        return order
    yield _make
    for order in created:
        order.delete()
```

`autouse=True` applies a fixture to every test in scope. Use it for environment
hygiene (resetting a global, freezing a clock); avoid it for anything that
provides a value, because the dependency becomes invisible at the call site.

## conftest.py layering

Fixtures resolve from the test file upward: `tests/unit/conftest.py` overrides
`tests/conftest.py` for tests under `unit/`. This is the intended way to give a
subtree a different database or a different client, and also the reason a fixture
"stopped working" after a file moved.

`conftest.py` is imported, not collected — do not put tests in it. Plugin hooks
(`pytest_collection_modifyitems`, `pytest_addoption`) must live in the root
`conftest.py`; in a nested one they are ignored for some hooks and inconsistently
applied for others.

## Parametrization

```python
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("2026-01-01", date(2026, 1, 1), id="iso"),
        pytest.param("01/01/2026", date(2026, 1, 1), id="us"),
        pytest.param("", None, id="empty"),
        pytest.param("nope", None, id="garbage", marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_parse_date(raw: str, expected: date | None) -> None:
    assert parse_date(raw) == expected
```

- Give every case an `id`. Without one the report shows `test_parse_date[nope-None]`
  or worse, and a failing case that cannot be named cannot be re-run.
- `xfail(strict=True)` fails the suite if the case starts passing, which is what
  keeps a fixed bug from staying marked broken.
- Parametrizing a fixture (`@pytest.fixture(params=[...])`) multiplies every test
  that uses it. That is right for "run the whole suite against three backends" and
  wrong as a way to give one test several inputs.
- Rows that exercise the same code path are padding. One row per distinct
  behaviour, boundary or error.

## Test isolation: diagnosing order-dependent failures

Passes alone, fails in the suite. Work through this in order:

1. Confirm it is ordering, not the environment: run the failing test alone, then
   run the file, then the suite. `uv run pytest --lf` re-runs only the failures.
2. Bisect the ordering: `uv run pytest tests/ -x -p no:randomly` versus a
   randomised run, then `uv run pytest tests/a.py tests/b.py` pairs to find the
   test that poisons the later one.
3. Look for the four usual carriers of state:
   - a fixture with scope above `function` that tests mutate;
   - a mutable default argument (`def __init__(self, log=[])`) — one list shared by
     every instance ever created, including across tests;
   - a module-level singleton, cache or registry (`functools.lru_cache`, a
     module-level dict, a class attribute used as an instance attribute);
   - `monkeypatch`-adjacent state changed without `monkeypatch` (a raw
     `os.environ[...] = ...`, `sys.path.append`, a changed working directory).
4. Fix at the source. Narrowing the fixture's scope, or resetting in a
   function-scoped `autouse` fixture, is a fix; adding `-p no:randomly` to
   `addopts` is hiding it.
5. Use `monkeypatch` and `tmp_path` for anything environmental — both undo
   themselves at teardown, which is exactly what hand-rolled setup forgets.

## Mocking

`patch` rebinds a name inside one namespace, so the target depends on how the
module under test imported it:

```python
# orders.py
from httpx import get          # a new name in orders' namespace
def fetch(): return get(...)

patch("orders.get")            # correct
patch("httpx.get")             # no effect: orders.get still points at the original
```

```python
# orders.py
import httpx                   # attribute lookup happens at call time
def fetch(): return httpx.get(...)

patch("orders.httpx.get")      # correct
patch("httpx.get")             # also correct: same module object, same attribute
```

So `from x import y` is the case that bites: patching the definition site leaves
the module under test holding its own reference, the test passes, and nothing was
substituted. Reading the import line first costs less than debugging it.

A patch also only holds while its context is active. A fire-and-forget task that
runs after the `with patch(...)` block exits sees the real function — the
assertion inside the block passes because the mock was never called by anything,
and the real request escapes. Await the task inside the patched scope.

- Awaited callables need `AsyncMock`; a plain `Mock` returns a `Mock` where the
  code awaits, and the failure surfaces as `object Mock can't be used in 'await'
  expression` — or, worse, silently succeeds when nothing inspects the result.
  `create_autospec`/`autospec=True` picks the right kind automatically and rejects
  calls with the wrong signature.
- Assert on behaviour: `assert_called_once_with(...)` or `mock.call_args`. Asserting
  a mock merely exists tests the mock.
- Mock at the process boundary — HTTP, clock, filesystem, message bus. Mocking your
  own collaborators means the test passes when their contract changes.
- `mocker` (pytest-mock) undoes patches at teardown; a bare `patch` used as a
  plain call rather than a context manager or decorator leaks into later tests.

## Async tests

An async test needs a plugin. With `pytest-asyncio`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"          # every async def test runs; no marker needed
```

In `strict` mode (the default) an unmarked `async def test_...` is not run: pytest
fails it with "async def functions are not natively supported" [verified]. That is
the good outcome — older pytest only warned and skipped, so advice written against
it claims a green suite can be testing nothing. Either declare the mode or mark
every async test.

Async fixtures need the same treatment (`@pytest_asyncio.fixture` in strict mode);
an async fixture nobody awaits yields a coroutine object into the test, which
usually surfaces as an `AttributeError` on the coroutine rather than as a setup
error. An event loop is created per test by default; sharing one across a session
requires an explicit loop-scope setting and reintroduces the isolation problem
above. `anyio` is the alternative when the code under test must run on trio too.

## Plugins

| Plugin | Why |
|---|---|
| `pytest-cov` | coverage with a failure threshold |
| `pytest-asyncio` (or `anyio`) | async tests |
| `pytest-mock` | `mocker` fixture with automatic teardown |
| `pytest-xdist` | `-n auto` parallelism; requires genuinely isolated tests |
| `pytest-randomly` | shuffles order, so isolation bugs surface in CI rather than in production |
| `pytest-timeout` | kills a hung test instead of hanging the run |

`pytest-xdist` and `pytest-randomly` are the two that find real bugs; both are
also the two that expose existing isolation debt, so introduce them expecting
failures.

## Coverage

```toml
[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
  "@abstractmethod",
]
```

`branch = true` matters: line coverage counts an `if` with no `else` path as
covered. Excluding `if TYPE_CHECKING:` is not cheating — those lines never execute
by design.

A threshold is a ratchet against regression, not a quality measure. Chasing the
last few percent produces tests that assert nothing.

## Invocations worth memorising

```bash
uv run pytest -x --tb=short -q                    # fast signal while iterating
uv run pytest --lf                                # only what failed last time
uv run pytest tests/test_orders.py::test_place -v # one test
uv run pytest -k "order and not slow"             # by name
uv run pytest -m "not integration"                # by marker
uv run pytest -n auto                             # parallel; isolation must hold
uv run pytest --collect-only -q                   # what would run
uv run pytest -x --pdb                            # drop into the debugger on failure
uv run pytest -p no:randomly                      # pin order while bisecting
```

`-q --tb=short` is the right default when reading output programmatically: a full
traceback per failure buries the one line that names the cause.

<!-- sources: laurigates-python, beagle-python, trailofbits-modern-python, awesome-copilot-python, wshobson-python, pytest-docs -->
