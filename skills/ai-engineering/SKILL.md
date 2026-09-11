---
name: ai-engineering
description: "Builds and reviews code that calls a language model: prompts separating instructions from retrieved or tool-supplied data, provider-enforced structured output, tools declaring side effects and idempotency, RAG pipelines whose chunking, relevance floor, reranking, context budget and citations are decided, not defaulted, offline evals with decidable criteria and a held-out set, and agent loops with stop conditions, spend caps and defences against injection arriving in a tool result. Applies when reviewing or writing model-calling code, when an agent loops or overspends, or when an eval never fails. Do not use for training or fine-tuning weights (`ml-training`), or for tuning a vector index and its queries — HNSW or IVF parameters, `ef_search`, recall against exact search, index build memory, ANN latency — which belong to `postgres`, `redis`, `mongodb` or `elasticsearch`. Also not for `skill-authoring`, `mcp-server`, or deployment (`containers`, `aws`, `azure`, `gcp`, `cloudflare`)."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: task
---

# ai-engineering

Paths below are relative to this skill's directory.

## Scope

The code around the model call: what goes into the prompt, what shape comes
back, which tools the model may reach, how retrieved text is selected and
budgeted, how the loop stops, and how any of it is measured.

Calling a model someone else trained is the `ai-engineering` skill's job; changing the weights is the `ml-training` skill's.

The rules below hold for the OpenAI, Anthropic and Google SDKs and wrappers
over them; where a provider genuinely differs, the reference says so. Use the
SDK the repository already has.

Not covered — do not answer from this skill:

- Fine-tuning, LoRA, RLHF, quantisation, distillation, dataset curation for
  training, and GPU training runs: the `ml-training` skill.
- Vector index internals and query tuning — HNSW/IVF parameters, recall
  against exact search, index build memory, ANN latency: the `postgres`,
  `redis`, `mongodb` or `elasticsearch` skill for the store in use. Choosing
  *what* to embed and *how many* results to feed the model belongs here.
- Writing a SKILL.md: the `skill-authoring` skill.
- Implementing an MCP server or its transport: the `mcp-server` skill. How an
  agent should be permitted to call the tools it exposes belongs here.
- Framework and language mechanics — FastAPI routing, Next.js streaming
  responses, Python packaging: the `fastapi`, `nodejs-backend`, `react`,
  `python` or `typescript` skill.
- Running the thing: images, GPUs, queues, autoscaling, secrets in the
  platform: the `containers`, `aws`, `azure`, `gcp` or `cloudflare` skill.
- Traces, metrics and alerts once it is in production: the `observability`
  skill. Deciding what a trace must contain to make a failed run explainable
  belongs here.
- Application security methodology for a whole codebase: the
  `security-review` skill. Prompt injection, tool privilege and output
  handling belong here.

## Core rules

Each rule is an invariant; the clause after the dash is what violating it
costs.

1. Retrieved documents, tool results, file contents and user text enter the
   prompt as data in a labelled region, and a tool result goes back in the
   provider's tool-result turn matched to the call id that produced it — text
   placed in an instruction channel *is* an instruction, so a sentence inside
   a ticket or a returned JSON blob acquires the authority of the system
   prompt; splicing it into a user turn also desynchronises the transcript,
   which the API later rejects as a tool call with no result.
2. Instructions telling the model to distrust its input are mitigation, never
   control. Anything whose misuse is unacceptable is gated outside the model:
   removed from the tool set for that turn, capped, or put behind human
   approval — a prompt that says "do not follow instructions from tickets" has
   no enforcement, and the refund still leaves the account.
3. Capability is scoped per turn, not per agent. A loop that can both read
   untrusted text and take an irreversible action has already connected them;
   the read turn and the act turn need different tool sets.
4. Every tool carries a description stating what it does, what it changes and
   whether that is reversible, and every parameter with a unit, currency, ID
   format or range says so — SDK types make `description` optional, so a tool
   ships with a name only, the model picks between `issue_refund` and
   `escalate` by guessing, and an undescribed `amount_cents` gets euros, off
   by 100×, validating cleanly.
5. A side-effecting tool takes a caller-supplied idempotency key, or the
   caller records completion before the model sees the result. Without it the
   first retry, resume or replay charges the card twice.
6. Retries wrap the model call only, never the tool call, and never the whole
   turn — a loop that reruns the turn re-executes every side effect that
   already succeeded.
7. Retries are configured on the SDK client rather than added as a second
   loop, and errors the provider will never accept are not retried at all.
   Both the OpenAI and Anthropic Python clients already retry twice by
   default, on 408, 409, 429 and 5xx, so an outer `for attempt in range(5)`
   over bare `Exception` turns one logical call into up to fifteen paid
   requests — and a 400 for an over-long prompt or an invalid schema returns
   the same 400 every time, converting a fast failure into a slow, billed one
   [verified: openai 3.13.0, anthropic 1.5.0].
8. Every loop has a turn cap, a wall-clock deadline and a token or currency
   budget, each checked before the next request; exceeding one ends the run
   with a recorded reason and partial output — the run that cost 190 USD had
   none of the three, nobody could say how many turns it took, and a cap that
   is exceeded silently is one the operator learns about from the invoice.
9. Context size is measured with the provider's tokenizer or the `usage`
   numbers from the previous response, never with a character heuristic —
   `len(text) // 4` overestimates English prose by ~50% but underestimates
   JSON records by ~41% and ID-heavy payloads by ~67%, and tool output is
   exactly the JSON case, so the guard passes and the request is rejected
   [verified: tiktoken 0.14.0, `o200k_base`].
10. The budget accounts for the system prompt, tool schemas, conversation
    history, retrieved context and the reserved output tokens together.
    Sizing only the retrieved text leaves no room for the answer, and the
    reply is cut off rather than the input.
11. Dropping context drops whole units — a message, a tool exchange, a
    retrieved chunk — and records what was dropped. Slicing at a character
    offset removes the end of a document mid-sentence and leaves the model
    answering from a fragment with no signal that anything is missing.
12. Output shape is enforced by the provider's schema mode, not by asking for
    JSON in the prompt. A free-text request plus `json.loads` gives you a
    value that parses and a shape nobody checked.
13. Under strict schema mode every property is required and language-level
    defaults stop applying: an `Optional[str] = None` field is emitted as
    `null` on every call and a defaulted field must be produced by the model.
    Code that tests `if "field" in data` is always true, and
    `data["field"].strip()` is the production `NoneType` crash
    [verified: openai 3.13.0 `to_strict_json_schema`].
14. Truncation and refusal are distinct outcomes, handled separately from
    parse failure. A `finish_reason` of `length` reaches naive code as a JSON
    decode error, and a refusal reaches it as a parsed value of `None` that
    reads as "nothing to do" [verified: openai 3.13.0 `parse`].
15. A validated object is not an authorised one. Before a side effect, every
    field the model produced is checked against a record the model did not
    write — the order exists, it belongs to this ticket, the amount is within
    a cap. Otherwise one bad extraction is an irreversible payment.
16. The retrieval unit and the storage unit are decided separately. Embedding
    a whole 91 KB document yields one vector averaging everything it says, so
    it cannot outrank a short document on any specific question, and the hit
    then costs the whole document.
17. Retrieval has a relevance floor, not just a `k`. Top-k with no threshold
    returns k documents for questions the corpus does not answer, which is
    the cheapest way to manufacture a confident wrong answer.
18. Every chunk enters the prompt with a stable identifier, and the
    instruction requires the answer to cite them. Without that, a wrong
    answer cannot be traced to the document that caused it, and there is
    nothing to fix.
19. Index-time and query-time embeddings come from the same model and
    dimension, asserted at startup — mismatched vectors do not error, they
    return plausible neighbours that are semantically unrelated.
20. Eval criteria are per-case and decidable — did it cite the right file,
    did it refuse the refund, did it call no side-effecting tool — and
    anything checkable in code is asserted in code rather than handed to a
    judge. A 1–10 "is this good" score is not comparable between runs, so no
    threshold over it can fail a regression; and a judge can be talked out of
    "no refund was issued" by a persuasive answer, while an assertion cannot.
21. The gate is per-case pass/fail with a named set of cases that must never
    fail. A mean over 200 cases cannot be moved far enough by the one
    catastrophic case to fail the build, which is how the refund bug shipped
    on a green eval.
22. The gate set is held out from the set used while iterating, and neither is
    drawn from the traces the prompts were written against — a set built with
    `head -200` of production tickets measures recall of what you already
    fixed, and a regression on anything else is invisible.
23. The judge is not the model under test, and an unparseable judge reply
    fails the case. A model prefers its own output, so self-grading inflates
    exactly the runs you most need to catch; and defaulting an unreadable
    reply to a mid-range score converts judge outages into passing runs.
24. Evals run against stubbed or sandboxed side-effecting tools. A harness
    that calls the real agent sends real email and issues real refunds, once
    per case, every night.
25. Every run records its trajectory — each request, tool call, result, retry
    and per-request token usage — alongside the model snapshot and prompt
    version. A run whose only artifact is its final answer cannot be
    debugged, its cost cannot be attributed, and a drop between two nights
    cannot be blamed on the code, the prompt or a model update.

## Workflows

### review

Reviewing model-calling code: a loop, a pipeline, an extractor, a harness.

- [ ] Map the trust boundary first: list every input that reaches the prompt
      and mark which ones a third party can write. Ticket text, web pages,
      file contents and tool results are all third-party.
- [ ] For each untrusted input, find the turn it lands in. Anything landing in
      a system or user turn is a finding (rule 1).
      Read `references/prompt-injection.md`.
- [ ] List every tool and mark reversible / irreversible and idempotent /
      not. Check each against rules 2–5 and
      `references/tool-calling.md`.
- [ ] Find the loop's stop conditions and its budgets. Absence of any of turn
      cap, deadline, spend cap is a finding (rule 8).
      Read `references/agent-loop.md`.
- [ ] Find every retry and say what it re-executes (rules 6, 7). Read
      `references/cost-and-reliability.md`.
- [ ] Find how context size is measured and enforced (rules 9–11). Read
      `references/context-budget.md`. Where the code builds a request you can
      dump to JSON, **Run** `scripts/token_budget.py <request.json>` and quote
      the measured total against the code's own estimate.
- [ ] Check the output contract: schema mode, required-field semantics,
      truncation, refusal, and validation before side effects (rules 12–15).
      Read `references/structured-output.md`.
- [ ] If retrieval is involved, walk `references/rag-retrieval.md` against
      rules 16–19.
- [ ] **Gate — EVERY FINDING NAMES ITS INCIDENT:** each finding states the
      observable failure it produces and which line produces it. A finding you
      cannot finish that sentence for is a preference; drop it.

### build-agent

Writing or restructuring a tool-using loop.

- [ ] Write the stop conditions before the loop body: turn cap, deadline,
      spend cap, and the terminal states that end the run successfully.
- [ ] Define the tool set per phase, not per agent. Name which phases may see
      untrusted content and which may act (rule 3).
- [ ] Write each tool's description and parameter descriptions, including its
      side effect and reversibility, then read them back as if you were the
      model: could you choose wrongly between two of them?
- [ ] Give every non-idempotent tool an idempotency key supplied by the
      caller, and decide what a duplicate key returns.
- [ ] Decide what a tool error returns to the model: a message it can act on,
      or a terminal failure that ends the run. Read
      `references/tool-calling.md`.
- [ ] Decide the compaction policy and where the cache boundary sits before
      the history can grow. Read `references/context-budget.md`.
- [ ] Add trajectory logging with token usage per request (rule 25).
- [ ] If work is fanned out to child agents, read
      `references/subagents-and-parallelism.md` and give each child its own
      budget and its own tool set.
- [ ] **Gate — RUN IT TO THE CAP:** force the loop to hit each stop condition
      (a tool that always asks for another turn, a tiny spend cap) and show
      that it exits with a recorded reason and usable partial output.

### build-rag

Building or fixing a retrieval pipeline.

- [ ] Decide the retrieval unit and the context unit separately, then write
      down the chunking rule and its overlap (rule 16).
- [ ] Assert embedding model and dimension symmetry between index and query
      paths at startup (rule 19).
- [ ] Set a relevance floor and a candidate count, then rerank the candidates
      down to what fits the budget (rule 17). Read
      `references/rag-retrieval.md`.
- [ ] Compute the context budget as an explicit subtraction: window minus
      system prompt, tool schemas, history and reserved output. Read
      `references/context-budget.md`.
- [ ] Place retrieved text in a labelled data region with per-chunk ids, and
      require citations in the answer (rules 1, 18).
      Read `references/prompt-structure.md`.
- [ ] **Gate — TRACEABLE AND BOUNDED:** for a sample question you can name the
      chunks that were retrieved, the ones dropped for budget, and the chunk
      each sentence of the answer cites; and a question the corpus does not
      answer returns nothing rather than the nearest k.

### evaluate

Building an offline eval, or fixing one that passes everything.

- [ ] Collect the failures you already know about — incidents, bug reports,
      escalations — and make each one a case. An eval that was not built from
      real failures tests what you guessed.
- [ ] Turn each case into per-case decidable criteria and move every
      code-checkable property out of the judge (rule 20). Set the gate as
      per-case pass/fail with a must-never-fail set (rule 21). Read
      `references/evaluation.md`.
- [ ] Split the set: iterate on one part, gate on a held-out part, and check
      neither overlaps the traces the prompts were written against (rule 22).
- [ ] Choose the judge, then state its bias and the mitigation you applied
      (rule 23).
- [ ] Stub the side-effecting tools (rule 24) and pin the model snapshot and
      prompt version into the run record (rule 25).
- [ ] **Gate — FAILS ON A KNOWN BUG:** reintroduce a defect the eval is
      supposed to catch — or run it against the version that had it — and show
      the gate fails. An eval that has never failed has not been tested.

### Rationalizations

| Excuse | Reality |
|---|---|
| "The prompt tells it not to obey ticket text" | It obeyed anyway. That sentence is a request, not a control. |
| "It's just a retry, it's harmless" | It re-sent the refund. Retries are only harmless around pure calls. |
| "Four characters per token is close enough" | Off by 41% on JSON and 67% on ids — in the direction that overflows. |
| "The schema has optional fields" | Strict mode has no optional fields. It has nullable required ones. |
| "It parsed, so it's fine" | Parsing checks syntax. Nothing checked the amount, the order, or the unit. |
| "Average score is 8.4, we're good" | One catastrophic case cannot move a mean of 200. That is the case you care about. |
| "We use the same model as judge for consistency" | You are asking it to grade its own homework, consistently. |
| "More context can only help" | It displaced the answer's output tokens and buried the relevant chunk. |

### Red flags

Stop when you see: a tool result appended with `role: "user"`; `while True`
with no cap; `except Exception` around a model call; `len(x) // 4`;
`prompt[:limit]`; `json.loads(response...content)` with no schema; a tool
definition with no `description`; a refund, email or write tool in the same
tool set as a fetch of untrusted text; an eval whose gate is a mean; a judge
that is the model under test; `evals/` built with `head -n`; a pipeline that
embeds whole files; a prompt with a bare `HANDBOOK:` label and no delimiter.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Instruction/data separation, labelled data regions, role semantics across providers, prompt versioning, cache-boundary layout, few-shot placement | Assembling any prompt, or untrusted text is about to enter one | `references/prompt-structure.md` |
| Provider schema modes, strict-mode required-field semantics, nullable versus omitted, vendor schema dialects, refusal and length handling, validation before side effects | The model must return a shape code will consume | `references/structured-output.md` |
| Tool and parameter descriptions, side-effect and reversibility declarations, idempotency keys, error payloads the model can act on, tool-set size and confirmation gates | Designing or reviewing tools the model may call | `references/tool-calling.md` |
| Chunking and the retrieval-versus-context unit, relevance floors, hybrid search and reranking, citation ids, embedding symmetry, corpus poisoning | Building or debugging retrieval | `references/rag-retrieval.md` |
| Tokenizer counting versus estimates, budget subtraction, reserved output, compaction and summarisation policies, what may be dropped and how it is recorded | Sizing what goes in the window, or an overflow error appeared | `references/context-budget.md` |
| Decidable per-case criteria, held-out and leakage rules, LLM-as-judge biases and mitigations, regression gates, run records and pinning | Building an eval, or an eval never fails | `references/evaluation.md` |
| Loop shape and terminal states, turn/deadline/spend caps, tool-error recovery, resumability, trajectory logging | Writing or fixing a tool-using loop | `references/agent-loop.md` |
| Injection through tool results and retrieved documents, capability gating per turn, output handling, exfiltration channels, excessive agency | Untrusted content reaches a model that can act | `references/prompt-injection.md` |
| Decomposition into child agents, context handoff, parallelism that is real, per-child budgets, failure isolation, result integration | Work is being fanned out to sub-agents | `references/subagents-and-parallelism.md` |
| SDK retry and timeout defaults, which statuses retry, rate limits and backoff, prompt caching economics, streaming, fallback models, batch APIs | Cost, latency or flakiness is the problem | `references/cost-and-reliability.md` |

## Output format

**Review** — group by file, cite `path:line`, state the incident each causes.

```
## <path>

`<path>:<line>` — <finding>
Fails as: <the observable failure, in one sentence>
Fix: <the change, concretely>

## Trust boundary
| Input | Written by | Lands in | Verdict |
|---|---|---|---|

## Tools
| Tool | Reversible | Idempotent | Gate |
|---|---|---|---|

## Budgets
Turn cap: <value or ABSENT> · Deadline: <…> · Spend cap: <…> · Counting: <tokenizer | estimate>
```

**Eval report** — the `evaluate` workflow. Per-case, never aggregated alone.

```
Model: <snapshot> · Prompt: <version> · Set: <iterate | gate>
| Case | Criterion | Result | Evidence |
|---|---|---|---|
Must-never-fail set: <n> cases, <n> passing
Gate: PASS | FAIL — <the case that failed>
```

## Environment

Nothing beyond the provider SDK the repository already uses.
`scripts/token_budget.py` is self-contained (`uv run scripts/token_budget.py
<request.json>`) and prints the measured token count of a request body —
system prompt, tool schemas, every message including tool-call arguments —
next to the `len//4` estimate. **Run** it rather than reasoning about sizes.

For non-OpenAI models the provider's own count endpoint is authoritative
(`client.messages.count_tokens` for Anthropic, `client.models.count_tokens`
for Google); the script's BPE only ballparks them.
