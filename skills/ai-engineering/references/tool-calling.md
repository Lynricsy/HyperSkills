# Tool calling

Verified against: openai 3.13.0, anthropic 1.5.0.

## Contents

- [A tool definition is a contract with a stranger](#a-tool-definition-is-a-contract-with-a-stranger)
- [Descriptions are not optional, the field just is](#descriptions-are-not-optional-the-field-just-is)
- [Declaring side effects and reversibility](#declaring-side-effects-and-reversibility)
- [Idempotency](#idempotency)
- [Errors the model can act on](#errors-the-model-can-act-on)
- [Errors the model must not see](#errors-the-model-must-not-see)
- [Tool-set size and confusable pairs](#tool-set-size-and-confusable-pairs)
- [Gating: visibility, approval, authorisation](#gating-visibility-approval-authorisation)
- [Parallel tool calls](#parallel-tool-calls)
- [Reviewing a tool set](#reviewing-a-tool-set)

## A tool definition is a contract with a stranger

The model sees the tool's name, its description, and its parameter schema.
Nothing else. Not your docstring conventions, not the calling code, not the
fact that `escalate` is cheap and `issue_refund` is not. Every judgement it
makes about which tool to call and with what arguments comes from those three
things, so they are the interface — and like any interface, the failures are
at the edges nobody wrote down.

## Descriptions are not optional, the field just is

In `anthropic` 1.5.0, `ToolParam` declares `description` as an optional key;
in `openai` 3.13.0, `FunctionDefinition` declares `name`, `description`,
`parameters` and `strict` all optional [verified]. A tool with a name and a
parameter schema and nothing else type-checks, passes CI, and ships.

What the model then has is an identifier. `issue_refund` and `escalate` both
plausibly "deal with an unhappy customer"; `send_email` and `escalate` both
plausibly "tell someone". The model picks by name similarity to the task, and
the choice is unpredictable across model versions — which is how a prompt
that worked for six months starts refunding on upgrade day.

A tool description answers four questions, in this order:

```python
{
  "name": "issue_refund",
  "description": (
      "Refunds money to the customer's original payment method. "
      "IRREVERSIBLE: the money leaves the merchant account immediately and "
      "cannot be recalled. "
      "Use only after confirming the order id against lookup_order and only "
      "when the customer is entitled to a refund under the returns policy. "
      "For anything ambiguous, disputed, or above the per-ticket cap, call "
      "escalate instead."
  ),
  ...
}
```

1. What it does, in the domain's words.
2. What it changes, and whether that can be undone.
3. The precondition — what must be true, or already called, first.
4. The alternative — which tool to use instead in the cases this one is
   wrong for. This is the line that stops confusable pairs from being coin
   flips.

## Declaring side effects and reversibility

Classify every tool before writing its description:

| Class | Example | Treatment |
|---|---|---|
| Pure read | `lookup_order` | Retryable, cacheable, safe in any phase |
| Read of untrusted content | `read_ticket_thread`, `fetch_url` | Retryable, but its result is third-party text (`prompt-injection.md`) |
| Reversible write | `add_internal_note`, `set_tag` | Needs an idempotency key; failure is recoverable |
| Irreversible write | `issue_refund`, `send_email`, `delete_account` | Needs an idempotency key *and* a gate outside the model |

The classification is what the review in `SKILL.md` walks. A tool set where
every tool is in row 1 needs almost none of this reference; the moment row 4
exists, all of it applies.

## Idempotency

Non-idempotent tools break on the ordinary paths, not the exotic ones:

- the model calls the same tool twice in one turn because the first result
  read ambiguously;
- the process is restarted and the run resumes from its last checkpoint;
- a network timeout fires after the server committed;
- a retry wrapper reruns the turn (see rule 6 in `SKILL.md`).

The fix is not "be careful". It is a key:

```python
def issue_refund(order_id: str, amount_cents: int, *, run_id: str) -> dict:
    key = f"{run_id}:{order_id}:{amount_cents}"      # caller-supplied, stable
    return billing.refunds.create(
        order_id=order_id, amount_cents=amount_cents, idempotency_key=key,
    )
```

Two properties matter. The key is derived from the *caller's* run identity,
not from a UUID generated inside the function — a fresh UUID per call makes
every retry a new refund. And a duplicate key returns the original result
rather than an error, so the model sees success and does not try a third
time.

Where the downstream service has no idempotency support, record the intent in
your own store before calling it and check that record first. The window
between write and call is small; the window without it is the whole run.

## Errors the model can act on

A tool failure is information, and the model is often the right component to
act on it — if the message says what to do. Compare:

```
Error: HTTPError 422
```

```
No order found with id "ORD-4417". Order ids look like "ord_000123".
The customer's ticket references order "ord_004417"; call lookup_order with
that id, or call escalate if no order matches.
```

The second ends the loop in one extra turn. The first produces a retry with
the same argument, then a guess, then an apology to the customer.

Rules for the error payload:

- Say what was wrong with the input, and what valid input looks like — the
  field, the format, the allowed values. This is the same principle as a good
  CLI error.
- Say whether retrying could help. "Rate limited, retry in 30s" is
  actionable; "Internal error" plus an implicit invitation to retry is a loop.
- Name the alternative tool when there is one.
- Keep it short. Tool errors are appended to the transcript and paid for on
  every subsequent turn; a stack trace is thousands of tokens of noise that
  also leaks your file layout.

Frameworks give this a seam. The OpenAI Agents SDK's `@function_tool` takes a
`failure_error_function` which formats the exception into the message the
model sees, and passing `None` re-raises instead, so the exception reaches
your code as a `ModelBehaviorError` (invalid arguments from the model) or a
`UserError` (your code crashed). Distinguishing those two matters: the first
is worth another turn, the second is a bug and should end the run.

## Errors the model must not see

Not every failure should be handed back. A failure ends the run when:

- it indicates the run's premise is wrong (the ticket does not exist, the
  tenant is suspended) — further turns only produce a more confident wrong
  answer;
- it is an authorisation failure. Reporting "you are not allowed to call
  this" to the model invites it to try the neighbouring tool, and turns your
  permission system into a search space;
- it contains anything the model should not repeat: credentials, another
  tenant's data, internal hostnames. The model will quote it to the customer.

## Tool-set size and confusable pairs

Every tool costs schema tokens on every request and adds a wrong choice. Two
practical checks:

- Read the descriptions as a set and look for pairs that answer the same need.
  Each such pair needs an explicit "use X not Y when …" clause in both
  descriptions, or one of them should not exist.
- Prefer one tool with an enum parameter over four near-identical tools. The
  enum is enforced by the schema; the choice between four names is not.

Where the set is genuinely large, gate by phase rather than shipping all of
it: the tool list is per-request, so it can differ per turn.

## Gating: visibility, approval, authorisation

Three distinct mechanisms, frequently confused:

- **Visibility** — the tool is absent from this request's tool list. The model
  cannot call what it cannot see. Cheapest and strongest control available at
  the prompt layer.
- **Approval** — the call is proposed, execution pauses, a human accepts,
  edits, or rejects, then the run resumes with the result. This is the only
  control that scales to "the action is legitimate but expensive".
- **Authorisation** — the check inside the tool, against the caller's
  identity and the specific resource. It runs regardless of what the model
  asked for.

Visibility is not authorisation. A framework flag that filters the tool list
controls what is offered and dispatched; it does not check that *this* order
belongs to *this* ticket. That check lives in the tool body — or the first
time a tool is exposed one turn too early, it executes.

Rejection needs a designed path too: when a human rejects a proposed call,
the model needs a tool result saying so ("the refund was declined by an
operator; do not retry, explain the decision to the customer"), not silence.
Silence reads as a failed call and invites a retry.

## Parallel tool calls

Providers will return several tool calls in one assistant turn. Two things to
decide before enabling it:

- Every result must be appended, each matched to its own call id, before the
  next request. A partially answered batch is the desynchronised transcript
  again.
- Side-effecting tools in a parallel batch execute without the model seeing
  any intermediate result, so `issue_refund` twice in one batch is two
  refunds with no chance to reconsider. Either restrict parallel batches to
  read-only tools, or serialise the batch and let the first result inform the
  rest.

## Reviewing a tool set

Walk this table and fill every cell; blanks are findings.

| Tool | Class (read / untrusted read / reversible write / irreversible write) | Description states effect + reversibility? | Idempotency key? | Gate (none / visibility / approval / authz) | Error payload actionable? |
|---|---|---|---|---|---|

A row with class "irreversible write" and gate "none" is the finding that
matters; everything else is hygiene.

<!-- sources: openai-agents-python, anthropics-claude-api, langchain-skills, vercel-ai-sdk, owasp-llm-top10, google-skills -->
