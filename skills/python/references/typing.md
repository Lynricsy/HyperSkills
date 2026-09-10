# Typing: modelling, narrowing and the strictness ratchet

Verified against: Python 3.12–3.14, mypy 1.14+, pyright 1.1.39x.

## Contents

- [Which checker](#which-checker)
- [Annotate the boundaries](#annotate-the-boundaries)
- [Protocol instead of a base class](#protocol-instead-of-a-base-class)
- [Structured payloads](#structured-payloads)
- [Generics: PEP 695 and the pre-3.12 form](#generics-pep-695-and-the-pre-312-form)
- [Narrowing](#narrowing)
- [`Self`, `override` and friends](#self-override-and-friends)
- [`Any` and where it is honest](#any-and-where-it-is-honest)
- [`if TYPE_CHECKING`](#if-type_checking)
- [mypy configuration](#mypy-configuration)
- [pyright configuration](#pyright-configuration)
- [The strictness ratchet](#the-strictness-ratchet)
- [Shipping types](#shipping-types)

## Which checker

An existing project's configured checker stays. For a new project pick mypy (the
reference implementation, widest plugin ecosystem) or pyright (fast, strong
inference, the engine behind Pylance). `ty` is Astral's Rust checker — very fast,
and self-described as beta with a `0.0.x` version, so it belongs behind a
deliberate decision rather than as a default: `uvx ty check src` is a cheap way to
evaluate it without committing.

Do not run two checkers in CI. They disagree on real cases (inference depth,
narrowing of `self`, unreachable-code handling), and reconciling both means
writing to the intersection of two type systems.

## Annotate the boundaries

Public signatures, class attributes, and anything crossing a module or process
edge. Locals stay unannotated where inference is obvious — an annotation the
checker could have derived is maintenance with no verification value.

```python
def enrich(events: list[Event], lookup: ProfileSource) -> list[EnrichedEvent]:
    out: list[EnrichedEvent] = []   # annotated: the empty literal has no element type
    for event in events:            # inferred: Event
        ...
    return out
```

Use built-in generics (`list[str]`, `dict[str, int]`, `tuple[int, ...]`) and
`X | None`; `typing.List` and `Optional[X]` are only needed below 3.9/3.10 and
ruff's `UP` rules rewrite them for you.

Bare `list`, `dict` or `set` as an annotation is `list[Any]` in effect. It passes
the "has annotations" check while verifying nothing.

## Protocol instead of a base class

When several unrelated implementations satisfy a dependency — production client,
test stub, in-memory cache — describe the shape, not the ancestry:

```python
from typing import Protocol

class ProfileSource(Protocol):
    def get_profile(self, user_id: str) -> Profile | None: ...
```

Any object with a matching `get_profile` now type-checks, with no import of your
module and no inheritance. An ABC would force every implementation, including a
three-line test stub, to import and subclass.

`@runtime_checkable` makes `isinstance()` work against the protocol, but it checks
only that the attributes **exist** — not their signatures or types. A callable
with the wrong arity passes. Treat it as a coarse guard, never as validation.

Protocols also express callbacks better than `Callable[..., X]` because parameter
names survive:

```python
class Handler(Protocol):
    def __call__(self, event: Event, *, retries: int = 0) -> None: ...
```

## Structured payloads

`dict[str, Any]` is the annotation that looks finished and checks nothing:
every access on it is `Any`, and that `Any` spreads to whatever the value flows
into. Pick by ownership of the data:

| Shape | Use |
|---|---|
| JSON you parse, keys known, no runtime validation wanted | `TypedDict` |
| Internal value object | `@dataclass(frozen=True)` |
| Lightweight immutable record, tuple-compatible | `NamedTuple` |
| Data crossing a trust boundary that must be validated | Pydantic `BaseModel` |

```python
from typing import NotRequired, TypedDict

class EnrichedEvent(TypedDict):
    user_id: str
    kind: str
    occurred_at: str
    plan: str
    region: NotRequired[str]   # may be absent, not "may be None"
```

`NotRequired`/`Required` control key presence; `X | None` controls the value.
Conflating them produces a checker that accepts `{"region": None}` where the code
does `row["region"].upper()`. `total=False` flips the default for the whole class
— readable for a mostly-optional payload, misleading otherwise. `ReadOnly`
(3.13+) marks keys a consumer must not mutate.

A `TypedDict` is a static claim only. Nothing validates the dict at runtime, so
for external input either validate first (Pydantic) or narrow explicitly.

## Generics: PEP 695 and the pre-3.12 form

Python 3.12+ has dedicated syntax, and the variance of each parameter is
**inferred** from usage — no more `covariant=True`:

```python
def first_or_default[T](items: Iterable[T], default: T) -> T: ...

class Cache[K, V]:
    def get(self, key: K) -> V | None: ...

type Rows = list[dict[str, str]]         # type alias statement
```

Below 3.12, the same thing with the older machinery:

```python
from typing import Generic, TypeVar
T = TypeVar("T")

def first_or_default(items: Iterable[T], default: T) -> T: ...
class Cache(Generic[K, V]): ...
```

State which floor you targeted. Using PEP 695 syntax in a project whose
`requires-python` is `>=3.11` is a `SyntaxError` at import time, not a type error
— it will not be caught by the checker.

Constrain rather than over-generalise: `bound=` for "this type or a subtype",
constraints (`TypeVar("S", str, bytes)`) for "exactly one of these". An
unconstrained `T` in a function that calls `.strip()` on it is a lie the checker
will report at the call site, confusingly far from the cause.

## Narrowing

The checker follows control flow. Give it something to follow.

```python
profile = lookup.get_profile(user_id)
if profile is None:
    raise ProfileMissing(user_id)
# profile is Profile from here on
```

- Early `return`/`raise` narrows the rest of the function; nested `if` bodies
  narrow only their own block.
- `isinstance` narrows; `type(x) == Y` does not.
- Comprehensions narrow: `[x for x in items if x is not None]` is `list[Item]`.
- `assert x is not None` narrows but disappears under `python -O`. Fine in tests,
  wrong as a production guard.
- `match` on a sealed set of dataclasses narrows per case, and with
  `assert_never(x)` in the default branch the checker fails the build when a new
  variant is added and unhandled — the cheapest exhaustiveness check available.
- Custom predicates: annotate the return as `TypeIs[T]` (3.13+, or
  `typing_extensions`) rather than `bool`. `TypeGuard` narrows only the positive
  branch; `TypeIs` narrows both, which is what you want almost always.
- `cast(T, x)` asserts without checking. Legitimate straight after a runtime check
  the checker cannot see; a code smell anywhere else.

## `Self`, `override` and friends

```python
from typing import Self, final, override

class QueryBuilder:
    def where(self, clause: str) -> Self:   # subclass chaining keeps its own type
        ...

class SqlStore(Store):
    @override                                # 3.12+: errors if the base drops the method
    def load(self, key: str) -> bytes: ...
```

`@override` catches the rename-in-base-class failure that tests usually miss, and
costs one decorator. `@final` on a class or method states the extension point is
closed and lets the checker act on it.

## `Any` and where it is honest

`Any` is right in exactly two places: data whose shape is genuinely unknown at
that point (before validation), and the boundary with an untyped third-party
library. Everywhere else it is a hole.

For unknown-but-must-be-inspected data, `object` is usually the better choice:
the checker forces you to narrow before use, which is the behaviour you wanted.

For an untyped dependency, put the `Any` in one adapter function and return a
real type from it, so the untyped surface is one file rather than a spreading
stain. Then look for a stub package (`types-requests` and friends) before
accepting the loss.

## `if TYPE_CHECKING`

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acme.orders import OrderService   # import cycle, or an expensive module
```

Breaks import cycles and keeps heavy imports out of the runtime path.
Consequences: the annotations must be strings, so add `from __future__ import
annotations` (or quote them), and anything that reads annotations at runtime —
Pydantic, dataclass field resolution, `typing.get_type_hints` — will fail to
resolve the name. Do not hide an import behind `TYPE_CHECKING` if a runtime
consumer introspects that class.

Coverage configs commonly exclude `if TYPE_CHECKING:` blocks; without that
exclusion they show as permanently uncovered lines.

## mypy configuration

```toml
[tool.mypy]
python_version = "3.12"
files = ["src", "tests"]
strict = true                      # the aggregate flag; see per-module relaxations below
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]

[[tool.mypy.overrides]]
module = ["acme.legacy.*"]
disallow_untyped_defs = false      # this subtree is not ready yet

[[tool.mypy.overrides]]
module = ["untyped_vendor.*"]
ignore_missing_imports = true      # third party has no stubs
```

`enable_error_code = ["ignore-without-code"]` is the one non-obvious setting worth
copying: it turns a bare `# type: ignore` into an error, which is what makes the
suppression discipline enforceable instead of aspirational.

`ignore_missing_imports` belongs in a narrow per-module override. Globally, it
hides your own typos in your own module paths.

## pyright configuration

```toml
[tool.pyright]
pythonVersion = "3.12"
include = ["src", "tests"]
typeCheckingMode = "standard"      # off | basic | standard | strict
reportMissingTypeStubs = "warning"

executionEnvironments = [
  { root = "src/acme/legacy", reportUnknownMemberType = "none" },
]
```

pyright's per-directory relaxation is `executionEnvironments`, not per-module
overrides. `# pyright: ignore[reportX]` is its suppression comment; it also
honours `# type: ignore` unless `enableTypeIgnoreComments` is disabled.

## The strictness ratchet

Turning `strict` on across a large repository yields thousands of errors and one
commit nobody can review. Do it in batches instead:

1. Get the exclusion list (or the relaxed-override list) and pick one module or
   one small package. Ownership boundaries make better batches than directory
   boundaries.
2. Remove exactly that entry. Change nothing else in the config.
3. Run the checker on those paths only — `uv run mypy src/acme/orders` — for fast
   feedback. Fix from the top: an inaccurate return type usually explains a dozen
   downstream errors.
4. Fix by typing, not by suppressing: narrow the union, annotate the class
   attribute, give the untyped dependency a Protocol. When a suppression is
   genuinely unavoidable it is `# type: ignore[<code>] — <reason>`.
5. Run the tests for the touched area. Annotating exposes real bugs — an argument
   that was never the type the caller passed — so expect some batches to be fixes.
6. Widen the run to the package, then commit that batch on its own.
7. Stop and split when the error count is growing rather than shrinking, or when a
   fix would require changing another team's module. A batch that spreads is a
   batch that was too big.

Track the number of remaining exclusions and remaining ignores; both should only
decrease. A ratchet that can slip is not a ratchet.

## Shipping types

A distributed package with annotations needs a `py.typed` marker file inside the
package directory, declared as package data, or consumers get no types at all
(PEP 561). A wheel with full annotations and no marker is, to a consumer's
checker, an untyped dependency.

<!-- sources: getsentry-typing, wshobson-python, beagle-python, developer-kit-python, gvre-python, laurigates-python, typing-docs, python-docs -->
