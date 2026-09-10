# Pydantic models at the HTTP boundary

Verified against: Pydantic 2.13, FastAPI 0.141.

## Contents

- [Model per direction, not per table](#model-per-direction-not-per-table)
- [Field metadata: assignment or Annotated](#field-metadata-assignment-or-annotated)
- [Constraints before validators](#constraints-before-validators)
- [Validators](#validators)
- [ValueError becomes a 422](#valueerror-becomes-a-422)
- [Reading ORM objects](#reading-orm-objects)
- [Aliases](#aliases)
- [Coercion, unions and collections](#coercion-unions-and-collections)
- [Subclasses are serialised as the declared type](#subclasses-are-serialised-as-the-declared-type)
- [Separate input and output schemas](#separate-input-and-output-schemas)
- [Settings](#settings)
- [Pydantic v1 to v2 checklist](#pydantic-v1-to-v2-checklist)

## Model per direction, not per table

One resource usually needs three models, and the reason is that the three have genuinely different
field sets:

| Model | Contains | Notes |
|---|---|---|
| `UserCreate` | what a client may send on create | includes `password`, never `id` |
| `UserUpdate` | same fields, all optional | `PATCH` semantics; distinguish "absent" from `null` with `model_fields_set` |
| `User` | what the API returns | no secrets, no internal columns |

Sharing one model across all three is how `password_hash` reaches a client. Trimming it back with
`response_model_exclude={"password_hash"}` is a filter someone can forget to add to the next
endpoint; a model that never declares the field cannot leak it.

Keep the shared fields in a small base model and inherit — but only for field reuse, not to make the
API and the database the same type.

## Field metadata: assignment or Annotated

```python
class Item(BaseModel):
    # assignment form: metadata a type checker needs to see
    name: str = Field(alias="itemName")
    created: datetime = Field(default_factory=utcnow)

    # Annotated form: everything else, and any number of pieces
    price: Annotated[float, Field(gt=0), WithJsonSchema(...)]
```

`alias`, `default` and `default_factory` change what a static type checker should accept, so they go
in the assignment slot. Constraints and schema metadata go in `Annotated`, where you can stack
several and where nobody mistakes `x: int = Field(gt=0)` for "x has a default".

Never write `...` as the default: `name: str` is already required, and `Field(...)` adds a token of
noise per field with no effect.

Field-specific metadata applies to the whole annotation, so put it outside a union:
`Annotated[int | None, Field(deprecated=True)]`, not `Annotated[int, Field(deprecated=True)] | None`.

## Constraints before validators

Prefer declarative constraints; they appear in OpenAPI, they run in Rust, and they cannot drift from
the schema:

```python
age: Annotated[int, Field(ge=0, le=130)]
slug: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)]
```

`StringConstraints` is the only way to express `strip_whitespace`, `to_upper`, `to_lower`,
`pattern` and `ascii_only` — reaching for a validator to call `.strip()` is the common mistake.

## Validators

Prefer `mode="after"`: the value already has the field's type, so the function has one input shape
instead of "anything the client sent". Prefer the annotated form so the rule sits next to the field:

```python
def even(v: int) -> int:
    if v % 2:
        raise ValueError("must be even")
    return v


class Model(BaseModel):
    count: Annotated[int, AfterValidator(even)]

    # decorator form: must be a classmethod, and mode is worth stating
    @field_validator("name", mode="after")
    @classmethod
    def not_reserved(cls, v: str) -> str:
        ...
```

Two traps in the decorator form: forgetting `@classmethod` (Pydantic accepts it, but the first
argument then silently means something else to readers and type checkers), and inheritance —
validator ordering across subclasses is not obvious, which is a second reason to prefer
`AfterValidator`.

Use `mode="before"` only when the raw input needs reshaping (a comma-separated string into a list).
For a model validator, `before` gets whatever the client sent, which is not necessarily a dict.

## ValueError becomes a 422

A `ValueError` raised inside a validator of a request-body model is converted by FastAPI into the
standard 422 validation response, with the field location filled in. That is the mechanism to use
for field-level rules — you do not need to raise `HTTPException` from a model.

Raise `ValueError`, not `assert`. Assertions disappear under `python -O`, so an `assert "@" in v`
validator silently stops validating in a container that sets `PYTHONOPTIMIZE`.

## Reading ORM objects

Returning a SQLAlchemy row where a Pydantic model is declared works even without
`from_attributes`: FastAPI validates request and response fields with `from_attributes=True`
regardless of the model's own config (`fastapi/_compat/v2.py`) [verified]. So the usual advice
"add `from_attributes` or the response breaks" is wrong for path operations.

You do need it when *your own* code calls `Model.model_validate(row)` — in a service layer, a
background task or a test:

```python
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
```

Either way, every declared field is read as an attribute, so a lazy relationship is loaded during
serialisation — after the handler returned, possibly after the session closed, which surfaces as
`DetachedInstanceError` rather than as a query you can see. Declare only fields the query actually
fetched.

## Aliases

`alias` covers both directions, which is usually not what an API wants. Split them when they differ:

- `validation_alias` — the name accepted on input.
- `serialization_alias` — the name emitted on output.
- `alias_generator=to_camel` — for a whole model of `camelCase` names.
- `populate_by_name=True` — also accept the Python field name on input. Without it, an aliased field
  can only be populated by its alias, which breaks constructing the model in your own code and tests.

Response serialisation uses aliases only when you ask for it; `response_model_by_alias` defaults to
true for path operations, so a `serialization_alias` does show up in JSON while `model_dump()` in
your own code does not use it unless you pass `by_alias=True`. Assert on the HTTP body, not on
`model_dump()`, when the alias is the thing you care about.

## Coercion, unions and collections

Outside strict mode, Pydantic coerces: `"123"` validates as `int`, a tuple validates as `list[str]`.
Two consequences:

- `int | str` does not mean "coerce the string to an int" — it means the field can be either, and
  every reader downstream now has to check. Unions at the HTTP boundary should be discriminated or
  absent.
- `Sequence[str]` to "accept lists and tuples" is unnecessary and slower than `list[str]`.

## Subclasses are serialised as the declared type

```python
class Main(BaseModel):
    model: Base   # declared type


Main(model=Sub1(base_field=1, sub1_field="x")).model_dump()
#> {"model": {"base_field": 1}}   -- sub1_field silently dropped
```

Validation follows the same rule: extra keys for the subclass are ignored rather than producing a
`Sub1`. So a `response_model` of a base class quietly truncates every richer object you return —
no error, no warning, just missing fields in production.

Fix it with a discriminated union, which also generates a correct OpenAPI `oneOf`:

```python
class Sub1(Base):
    type: Literal["sub1"]
    sub1_field: str


Subs = Annotated[Sub1 | Sub2, Field(discriminator="type")]
```

Generics (`Main[Sub1]`) work when the caller knows the concrete type.

## Separate input and output schemas

A model with defaulted fields used on both sides produces two OpenAPI schemas: `Item-Input`, where
the defaulted field is optional, and `Item-Output`, where it is required — because the response
always contains it, possibly as `null`. This is correct and makes generated clients better.

If existing generated SDKs cannot absorb the split yet, `FastAPI(separate_input_output_schemas=False)`
turns it off for the whole app. Prefer distinct `Create`/`Read` models over the flag: then the two
schemas are two names you chose rather than two names FastAPI derived.

## Settings

Configuration is a `BaseSettings` subclass from `pydantic-settings` (a separate package in v2),
instantiated once and injected like any other dependency. Two rules that matter in a web app:

- Read it through a cached dependency, not a module-level import chain, so tests can override it.
- Group per concern (`DatabaseSettings`, `AuthSettings`) rather than one global object every module
  imports; the global object is what forces every test to set every variable.

## Pydantic v1 to v2 checklist

| v1 | v2 |
|---|---|
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `allow_population_by_field_name` | `populate_by_name` |
| `@validator` | `@field_validator` + `@classmethod` |
| `@root_validator` | `@model_validator(mode="before"/"after")` |
| `.dict()` / `.json()` | `.model_dump()` / `.model_dump_json()` |
| `parse_obj` / `parse_raw` | `model_validate` / `model_validate_json` |
| `__fields_set__` | `model_fields_set` |
| `Optional[X]` implying a `None` default | `X | None` is required unless you write `= None` |

The last row breaks silently: in v1 an `Optional` field defaulted to `None`, in v2 it does not, so a
migrated `PATCH` model starts rejecting requests that omit fields.

Avoid `from __future__ import annotations` in modules defining models — stringified annotations are
harder for Pydantic to resolve. Quote only genuinely forward references, and on Python 3.14+ do not
quote at all. Recursive aliases need `type X = ...` (3.12+) or `TypeAliasType`, never a quoted
`TypeAlias`, which Pydantic cannot evaluate.

<!-- sources: pydantic-official-skill, pydantic-docs, fastapi-official-skill, fastapi-docs, microsoft-skills-py -->
