# Structured output

Verified against: openai 3.13.0, pydantic 2.13.5, google-genai 2.23.0.

## Contents

- [Three levels of enforcement](#three-levels-of-enforcement)
- [What strict mode does to your model class](#what-strict-mode-does-to-your-model-class)
- [Optional fields under strict mode](#optional-fields-under-strict-mode)
- [The four non-success outcomes](#the-four-non-success-outcomes)
- [Provider schema dialects](#provider-schema-dialects)
- [Field descriptions are part of the contract](#field-descriptions-are-part-of-the-contract)
- [Validation is not authorisation](#validation-is-not-authorisation)
- [Designing the schema for the model, not the database](#designing-the-schema-for-the-model-not-the-database)
- [Old patterns](#old-patterns)

## Three levels of enforcement

| Level | What it guarantees | What it does not |
|---|---|---|
| Prompt asks for JSON | Nothing | Output may be prose, fenced, or truncated |
| JSON mode (`response_format={"type": "json_object"}`) | The text parses as JSON | Keys, types, enums, nesting — all unchecked |
| Schema mode (strict JSON schema / `response_schema`) | The output conforms to the schema | That the values are *correct* |

The middle level is the dangerous one, because it looks like the third. Code
that does `json.loads(message.content)` on JSON mode output and then
`Model(**data)` is doing schema validation *after* the fact, at which point a
missing key is an exception in production rather than a constraint the
provider enforced.

Use the SDK helper that combines the schema and the parse:

```python
completion = client.chat.completions.parse(
    model=MODEL,
    messages=[...],
    response_format=RefundDecision,      # a pydantic BaseModel
)
decision = completion.choices[0].message.parsed
```

## What strict mode does to your model class

`openai.lib._pydantic.to_strict_json_schema` — the conversion the SDK applies
to your Pydantic class — is not a pass-through. Given

```python
class RefundDecision(BaseModel):
    order_id: str
    currency: str = "EUR"
    internal_note: Optional[str] = None
    lines: list[RefundLine]
```

it produces a schema in which:

- `additionalProperties: false` is added to every object, including nested
  `$defs`. A model that invents a key now fails rather than being silently
  dropped — this is the part you want.
- **every** property is listed in `required`, including `currency` and
  `internal_note`.
- the `default` on `internal_note` is stripped; the `default` on `currency`
  survives in the schema but the field is required anyway, so nothing ever
  defaults.

[verified: openai 3.13.0]

## Optional fields under strict mode

There are no optional fields under strict mode. There are nullable required
fields. The practical consequences, in the order teams discover them:

1. A prompt instruction like "leave `internal_note` out if there is nothing
   worth noting" is unsatisfiable — the schema forbids omitting it. The model
   will emit `"internal_note": null`, or worse, invent a note to satisfy what
   reads like an instruction to provide one.
2. `if "internal_note" in data:` is always `True`. Membership is no longer a
   presence test. The guard that used to protect
   `data["internal_note"].strip()` now lets `None` through, and that is the
   `AttributeError: 'NoneType' object has no attribute 'strip'` in the
   incident channel.
3. Python-side defaults never apply. `currency: str = "EUR"` means the model
   chooses the currency on every call, from a field name. Give it an enum, or
   drop it from the schema and set it in code after parsing.

The rule that follows: fields the model must not decide do not belong in the
schema. Put them in the code that consumes the parsed object.

For genuinely optional data, model it as a nullable union and test the value:

```python
note: str | None          # emitted as null when absent
...
if decision.internal_note is not None:
    ...
```

## The four non-success outcomes

A schema-mode call has four ways not to give you an object, and they need
four different handlers. Collapsing them into `except Exception` is why the
same bug gets rediscovered.

| Outcome | Signal | Right response |
|---|---|---|
| Truncation | `finish_reason == "length"`; SDK `parse()` raises `LengthFinishReasonError` | Raise the output budget, or reduce what you asked for — retrying identically truncates identically |
| Refusal | `message.refusal` is set; `message.parsed` is `None` and **no exception is raised** | Treat as a decision, not an error: log it, return the refusal path |
| Content filter | `finish_reason == "content_filter"`; SDK raises `ContentFilterFinishReasonError` | Terminal for this input; do not retry |
| Invalid schema | 400 from the provider at request time | Fix the schema; never retried |

Two details that cost real time:

- `LengthFinishReasonError` and `ContentFilterFinishReasonError` subclass
  `OpenAIError`, not `APIStatusError`. A retry decorator that catches
  `APIError` will not catch them, and one that catches everything will retry
  a truncation forever at full price [verified: openai 3.13.0].
- On a refusal, the SDK's parse helper returns `None` rather than raising:
  content is only parsed when `message.content and not message.refusal`. Code
  written as `if result.parsed:` therefore reads a refusal as an empty
  result — the model declined and your pipeline recorded "nothing to do"
  [verified: openai 3.13.0 `maybe_parse_content`].

Without the SDK helper, check `finish_reason` *before* parsing. A JSON decode
error is the symptom; the length condition is the cause, and it is available.

## Provider schema dialects

The schema languages are similar enough to be mistaken for the same one.

| Feature | OpenAI strict | Anthropic tool `input_schema` | Gemini `response_schema` |
|---|---|---|---|
| `$ref` / `$defs` | supported | supported | supported (`ref`, `defs` fields exist on `types.Schema` in google-genai 2.23.0) |
| Unions | `anyOf` | `anyOf` | `any_of` |
| Nullability | `anyOf: [T, null]` | `anyOf: [T, null]` | `nullable: true` |
| Every field required | enforced | not enforced | not enforced |
| Key order | not controllable | not controllable | `property_ordering` |
| Unconstrained object (`dict`) | accepted by the converter, rejected by the API | accepted | accepted |

Two traps:

- A `dict[str, Any]` field passes the local strict conversion and fails at the
  API, so the failure surfaces on the first real call rather than at import
  [verified: openai 3.13.0 accepted `data: dict`]. Type the object.
- Reusing one Pydantic class across two providers works only if you convert
  per provider. Hand-writing a second copy of the schema guarantees they
  diverge; generate both from the class.

## Field descriptions are part of the contract

`amount_cents: int` tells the model the name and the type. It does not say
minor units, currency, or whether a partial refund is allowed. A value in
euros validates perfectly and is 100× wrong.

Every field that has a unit, a format, a range, or a source gets a
description:

```python
amount_cents: int = Field(
    description="Refund amount in minor units of the order's currency. "
                "Must not exceed the order total. Use 0 to refuse."
)
reason: Literal["damaged", "late", "wrong_item"] = Field(
    description="Pick from the order's dispute categories; do not invent one."
)
```

Enums beat free strings everywhere you have a closed set: they remove a class
of downstream normalisation code, and they are enforced by the provider
rather than by a `match` statement that falls through to `else: pass`.

## Validation is not authorisation

A parsed, schema-valid object is a well-formed *claim*. Before it causes a
side effect, every field the model produced is checked against something the
model did not write:

- Does the order exist, and is it the order attached to this ticket?
- Is the amount ≤ the order total, and ≤ the per-ticket cap?
- Is the target email the account's email, or one the model pulled from the
  ticket body?

Absent those checks, one bad extraction is an irreversible payment, and the
schema was never the thing protecting you.

## Designing the schema for the model, not the database

- Flat beats deep. Every level of nesting is another place the model can get
  the bracket structure right and the semantics wrong.
- Ask for decisions, not prose: `should_refund: bool` plus
  `reason: Literal[...]` is checkable; `summary: str` is not.
- Include a field for "I could not determine this", explicitly. Without one,
  a required field forces a guess, and the guess is indistinguishable from a
  finding.
- Do not ask for computed values you can compute. A `total_cents` the model
  sums is a field you have to verify; derive it in code.

## Old patterns

<details>
<summary>Function calling as a structured-output workaround</summary>

Before schema-constrained responses existed, the standard trick was to
declare a single "tool" whose parameters were the desired shape and force the
model to call it. It still works and is still how Anthropic tool schemas are
enforced, but for a pure extraction on OpenAI or Gemini it adds a tool-call
round trip and an extra failure mode (the model answering in text instead of
calling the tool). Use the response-schema path for extraction; keep tools
for actions.

</details>

<details>
<summary>Regex or "grab the first {…} block" parsing</summary>

Pulling JSON out of prose with a regex was necessary when no mode enforced
it. It fails on nested braces, on JSON inside a fenced block with a language
tag, and on truncation — where it happily returns a prefix that parses.
Delete it when you adopt schema mode; leaving it as a fallback means
truncated output silently becomes a partial record.

</details>

<!-- sources: openai-agents-python, anthropics-claude-api, vercel-ai-sdk, google-skills, langchain-skills, openai-docs, anthropic-docs -->
