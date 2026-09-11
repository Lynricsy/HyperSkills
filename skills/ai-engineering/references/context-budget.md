# Context budget

Verified against: tiktoken 0.14.0 (`o200k_base`), openai 3.13.0, anthropic 1.5.0.

## Contents

- [Counting, not estimating](#counting-not-estimating)
- [Measured error of the four-characters rule](#measured-error-of-the-four-characters-rule)
- [The budget is a subtraction](#the-budget-is-a-subtraction)
- [Reserving output tokens](#reserving-output-tokens)
- [What to drop, and how](#what-to-drop-and-how)
- [Compaction for long agent runs](#compaction-for-long-agent-runs)
- [Tool results are the biggest line item](#tool-results-are-the-biggest-line-item)
- [Position effects](#position-effects)
- [Where the caching boundary goes](#where-the-caching-boundary-goes)
- [Overflow is a 400, not a truncation](#overflow-is-a-400-not-a-truncation)

## Counting, not estimating

Three sources of truth, in descending order of authority:

1. The `usage` block on the previous response. It is the provider's own
   accounting, includes everything you cannot see (schema serialisation,
   role framing, cached-prefix bookkeeping), and costs nothing.
2. The provider's count endpoint before sending:
   `client.messages.count_tokens` (Anthropic),
   `client.models.count_tokens` (Google). An extra call, exact for that
   provider.
3. A local tokenizer — `tiktoken` with the encoding for the model family.
   Exact for the text, blind to framing overhead, and only approximate for
   non-OpenAI models.

A character heuristic is not on this list, and the reason is not purity.

## Measured error of the four-characters rule

Encoding the same content with `o200k_base` and comparing against
`len(text) // 4` [verified: tiktoken 0.14.0]:

| Content | chars/token | `chars//4` error |
|---|---|---|
| English prose | 6.01 | **+50%** (overestimates) |
| Python source | 3.87 | −3% |
| JSON records (ids, timestamps, enums) | 2.35 | **−41%** (underestimates) |
| Bare UUIDs | 1.32 | **−67%** (underestimates) |

The direction is what matters. The heuristic is conservative on prose and
dangerously optimistic on exactly the content an agent accumulates most of:
tool results, database rows, log lines, identifiers. A guard written as

```python
if len("".join(contents)) // 4 > 180_000:      # wrong twice over
    compact()
```

does not fire until the real count is well past the window, so the request is
rejected before the guard ever trips. The same code also silently
overestimates a prose-heavy conversation and compacts history that would have
fitted, throwing away context for no reason.

A second defect in that snippet: it measures `content` only. It misses tool
*call* arguments, the tool schemas (five tools with descriptions is easily
1–2k tokens on every request), the system prompt, and images. Measure the
request you are about to send, not the parts of it that happen to be strings.

## The budget is a subtraction

Write it once, explicitly, and keep the terms named:

```python
WINDOW = 200_000                    # model's context window
RESERVED_OUTPUT = 8_000             # max_tokens for the reply
OVERHEAD = 1_500                    # system prompt + tool schemas, counted once

available_for_context = WINDOW - RESERVED_OUTPUT - OVERHEAD - history_tokens
```

Then fill `available_for_context` from retrieved chunks in rank order until
the next one does not fit, and record how many were dropped.

Sizing only the retrieved text — the common shortcut — spends the whole
window on input, and the reply is the thing that gets cut. That failure
presents as "the model stops mid-sentence", which nobody connects to the
retrieval code.

## Reserving output tokens

The output reservation is part of the input budget on every provider: input +
output must fit the window. Two consequences:

- Set `max_tokens` / `max_completion_tokens` deliberately, from the largest
  legitimate output. Leaving it at the model's default reserves a large
  unknown; setting it too low truncates (`structured-output.md`).
- Reasoning models spend tokens on reasoning before producing output, and
  those tokens count. A run that fits with a non-reasoning model can overflow
  with a reasoning one at the same reservation — budget for the reasoning
  allowance separately when the provider exposes one.

## What to drop, and how

Drop whole units, in a defined priority order, and record the drop.

| Unit | Drop order | Note |
|---|---|---|
| Retrieved chunks below the relevance floor | first | They should not have been retrieved |
| Oldest tool exchanges | second | Drop the call *and* its result together |
| Oldest conversation turns | third | Keep the first user turn: it holds the task |
| System prompt, tool schemas | never | Dropping these changes behaviour silently |

Never slice a string to fit:

```python
prompt = prompt[:limit * 4]      # cuts mid-word, mid-JSON, mid-document
```

This removes the *end* of the context — typically the question itself, or the
last retrieved chunk, or half a code block — and leaves the model answering
from a fragment with nothing signalling that anything is missing. It also
produces an invalid transcript when the cut lands inside a tool exchange:
an assistant turn with a tool call whose result was truncated away, which the
API rejects on the next request.

Every drop gets recorded — count and identity — and, where it affects the
answer, stated to the model: `[12 earlier turns and 3 handbook sections were
omitted for length]`. A model that knows its context is partial hedges; one
that does not, confabulates the missing part.

## Compaction for long agent runs

A run that has to exceed the window needs a compaction policy chosen in
advance, not a fallback triggered at the boundary.

- **Summarise-and-replace.** When history exceeds a threshold, summarise the
  oldest portion into a structured note (decisions taken, facts established,
  tool results that still matter, open questions) and replace those turns
  with it. The summary is produced by the model but is *your* text from then
  on, so it sits in the instruction region as established state.
- **Externalise state.** Keep the durable facts in a file or a store the
  agent reads and writes, and let the transcript be disposable. This is
  strictly better for anything that must survive a restart, and it makes the
  run resumable (`agent-loop.md`).
- **Keep the anchors.** The first user turn and the task definition never get
  summarised away; they are what the whole run is judged against.

Compaction is lossy by construction, so it needs the same discipline as a
migration: log what was compacted, keep the pre-compaction transcript in the
trajectory log, and make the summary a visible artifact so a wrong summary is
debuggable rather than mysterious.

## Tool results are the biggest line item

A single `SELECT *` returned verbatim can be tens of thousands of tokens of
JSON — and by the table above, JSON is where a character estimate
underestimates worst. Bound tool output at the tool, not at the prompt:

- Project the fields the model needs, not the row.
- Paginate, and say so in the result: `"showing 20 of 4,318; call again with
  cursor=..."`. Truncating silently makes the model reason about a subset it
  believes is the whole.
- Return identifiers plus a fetch tool rather than full bodies, for anything
  large.
- Strip base64, embedded images, and HTML boilerplate at the tool boundary.

## Position effects

Long contexts are not uniformly attended. Material at the very beginning and
very end of a long context is used more reliably than material in the middle.
Practical uses:

- Put the question or instruction *after* a long data region as well as
  before it.
- Put the highest-ranked retrieved chunk closest to the instruction, not
  first in a list of thirty.
- If an answer improves when you remove half the context, the problem is
  precision, not window size. Adding context is not free; it displaces
  attention and output tokens.

Two findings worth designing around, both reported from long-context
benchmark work rather than measured here [community]:

- Usable context is smaller than advertised context. Degradation on
  multi-step retrieval tasks typically begins well before the window limit,
  so treating the window as the budget means operating in the degraded
  region. Measure where *your* workload degrades and set the compaction
  trigger below it.
- A single irrelevant document hurts disproportionately more than the second
  and third do. That makes the relevance floor
  (`rag-retrieval.md`) a correctness control, not an optimisation: one
  off-topic chunk costs most of the available accuracy, so "include it just
  in case" is the expensive choice.

## Where the caching boundary goes

Cached prefixes are matched exactly, so the budget layout and the cache
layout are the same decision: stable prefix first (system prompt, tool
schemas, examples, unchanging documents), volatile suffix last (history,
retrieved chunks, the user turn). See `prompt-structure.md` for the
invalidation traps — the short version is that anything varying per request
must not appear before anything you want cached.

Compaction interacts with caching: rewriting history invalidates the cache
from the rewrite point. Compact at a boundary you control, in one step,
rather than trimming a turn per request and paying uncached rates forever.

## Overflow is a 400, not a truncation

No provider silently drops input to make it fit; a request over the window is
rejected with a 400 naming the counts
(`prompt is too long: 241813 tokens > 200000 maximum`). Three things follow:

- It is not retryable. The same request produces the same 400, so a retry
  wrapper turns a fast error into a slow, billed one
  (`cost-and-reliability.md`).
- The recovery is to reduce the request — compact, drop chunks, paginate the
  tool result — and the error message tells you by how much.
- The error is the last line of defence, not the plan. Reaching it means the
  budget was never counted.

<!-- sources: anthropics-claude-api, openai-agents-python, langchain-skills, murat-context-engineering, anthropic-docs, openai-docs -->
