# Cost and reliability

Verified against: openai 3.13.0, anthropic 1.5.0.

## Contents

- [The SDK already retries](#the-sdk-already-retries)
- [Which statuses retry, and which never will](#which-statuses-retry-and-which-never-will)
- [Timeouts](#timeouts)
- [Where a retry is safe](#where-a-retry-is-safe)
- [Rate limits and the retry storm](#rate-limits-and-the-retry-storm)
- [Cost accounting that survives a sprint](#cost-accounting-that-survives-a-sprint)
- [Prompt caching](#prompt-caching)
- [Model selection and fallback](#model-selection-and-fallback)
- [Streaming](#streaming)
- [Batch](#batch)
- [Pinning model versions](#pinning-model-versions)

## The SDK already retries

Both official Python clients default to `max_retries = 2` — three attempts
total — with exponential backoff and jitter, and both default to a 600 s read
timeout with a 5 s connect timeout [verified: openai 3.13.0, anthropic 1.5.0].

So the code that looks careful:

```python
for attempt in range(5):
    try:
        return client.chat.completions.create(...)
    except Exception:
        time.sleep(2 * attempt)
```

issues up to **15 paid requests** per logical call, four of which the SDK
already decided were pointless, and it does so on errors that will never
succeed. It also swallows the SDK's `Retry-After` handling, so it retries
faster than the provider asked.

Configure the client instead:

```python
client = OpenAI(max_retries=4, timeout=httpx.Timeout(60.0, connect=5.0))
# or per request, where one call needs different behaviour:
client.with_options(max_retries=0).chat.completions.create(...)
```

An outer retry loop is justified in exactly one case: you are switching to a
different model or provider on failure (see fallback, below). Then it is not
a retry, it is a different request.

## Which statuses retry, and which never will

Both clients retry on 408, 409, 429 and every 5xx, and obey an
`x-should-retry` header in either direction; `openai` additionally declines to
retry when `Retry-After` exceeds its maximum acceptable delay [verified].

Not retried, by design:

| Status | Meaning | Why retrying is wrong |
|---|---|---|
| 400 | Malformed request — including a prompt over the context window and an invalid schema | Identical request, identical rejection. Retrying converts a fast failure into a slow, billed one |
| 401 / 403 | Bad or insufficient credentials | Nothing changes between attempts |
| 404 | Unknown model or endpoint | Usually a deprecated model id; retrying hides it |
| 422 | Semantically invalid | Same as 400 |

The `prompt is too long: 241813 tokens > 200000 maximum` case is the one to
internalise: it is a 400, it is fully deterministic, and the correct response
is to shrink the request (`context-budget.md`). A wrapper that catches it,
sleeps, and re-sends four more times — as in the fixture this skill was built
against — pays five times for the same rejection and delays the real fix.

`LengthFinishReasonError` and `ContentFilterFinishReasonError` are not HTTP
errors at all: they subclass `OpenAIError`, so a decorator catching
`APIStatusError` misses them, and one catching everything retries a
truncation identically forever (`structured-output.md`).

## Timeouts

600 s is a sensible default for a long reasoning call and a terrible one for
an interactive request: a hung connection holds a worker for ten minutes, and
with the default two retries a single user request can occupy 30 minutes.

- Set the timeout from the p99 of the call you are actually making, plus
  headroom. Interactive: 30–60 s. Long agentic turn: a few minutes.
- Streaming changes the meaning of the timeout: the first token arrives
  quickly and the stream may run long, so the useful control is a
  time-to-first-token deadline plus an inactivity timeout, not one total
  budget.
- A timeout is not a failure of the request — the provider may have completed
  it and billed it. Treat a timed-out non-idempotent operation as *unknown*,
  not failed.

## Where a retry is safe

| Operation | Retry safe? |
|---|---|
| A model call with no tool execution | Yes — it is a pure function of the request, and you pay again |
| A model call that already executed tool calls | No — retry the *call*, not the turn |
| An idempotent tool | Yes |
| A non-idempotent tool with an idempotency key | Yes, and that is the point of the key |
| A non-idempotent tool without one | No. Never |
| The whole agent turn | No — every side effect that already succeeded runs again |

The distinction that matters in review: retrying the model is a cost problem,
retrying the turn is a correctness problem.

## Rate limits and the retry storm

Rate limits are per organisation, not per process, and they bite requests and
tokens separately. Two properties make them a systemic failure rather than a
local one:

- Everything that shares the key shares the limit — production, the nightly
  eval, someone's notebook, and every sub-agent in a fan-out.
- The natural reaction to a 429 is to retry, which is more load. Without
  jitter, N clients that started together retry together, and the limit is
  hit in a tighter and tighter rhythm.

Controls, in order of effect:

1. Honour `Retry-After`. It is the provider telling you when to come back.
2. Cap concurrency at the source — a semaphore around the call, sized under
   the limit — rather than absorbing rejections downstream.
3. Share one client instance, so its connection pool and backoff are shared.
4. Separate keys or projects per workload, so the nightly eval cannot rate
   limit production.
5. Queue and shed, rather than retry indefinitely, for anything
   user-triggered.

## Cost accounting that survives a sprint

Record `usage` from every response — prompt tokens, completion tokens, cached
tokens, reasoning tokens — against a run id and a feature tag. Two reasons
this is not optional:

- Cost per run varies by more than an order of magnitude between the median
  and the tail, and the tail is what the bill is made of. An average is not
  actionable; a p99 with a run id is.
- Without per-feature attribution, a cost increase has no owner and the only
  available response is to reduce quality everywhere.

Set a hard cap where the money is spent — per run, per tenant, per day — and
make exceeding it an explicit outcome (`agent-loop.md`). A cap that
only alerts is a cap that fires at 3 a.m. and is acknowledged at 9.

Structural costs worth knowing before optimising:

- In a loop, history is re-sent every turn, so cost grows roughly
  quadratically in turns, not linearly. Halving the turn count more than
  halves the cost.
- Output tokens cost several times input tokens. Asking for a shorter answer
  is often a bigger saving than trimming context.
- Tool schemas are re-sent every request. Ten verbose tools is a fixed tax on
  every turn of every run.

## Prompt caching

A cached prefix is billed at a fraction of the input rate (and Anthropic
charges a premium on the initial cache write). Three rules decide whether you
get it:

- **Order matters.** Stable content first, volatile last
  (`prompt-structure.md`). A timestamp or request id near the top means
  you never get a cache hit and the prompt looks innocent.
- **Any earlier change invalidates everything after it.** Editing a tool
  description invalidates the cache for every request using that tool set, so
  batch schema changes rather than tuning them one at a time in production.
- **Caches expire in minutes.** Caching helps within a conversation or a
  burst; it does nothing for a request that arrives hourly.

Verify from the response's cached-token counts rather than by reasoning about
the layout. A prompt you believe is cached and is not is a silent 5–10×
overcharge.

## Model selection and fallback

Pick per call site, from measurement on your own eval set, not from
benchmarks. The useful pattern is a cheap model on the high-volume path and
an expensive one where the judgement is hard — routing, classification and
extraction are usually the cheap path.

Fallback to a second provider is worth building only if you have measured the
fallback model on your eval set. An untested fallback is a silent quality
drop that activates exactly during an incident, when nobody is looking at
answer quality. And record which model served each request, or your eval
numbers mix two populations.

## Streaming

Streaming buys perceived latency, not throughput. What it costs:

- Errors can arrive mid-stream, after you have shown the user half an answer.
  Decide whether to discard or keep the partial.
- Structured output cannot be validated until the stream completes, so a
  UI that renders partial JSON renders invalid JSON.
- Usage numbers arrive at the end. Code that reads `usage` mid-stream gets
  nothing, so cost accounting must handle the final event.
- A dropped connection mid-stream is the timeout case: billed, and unknown.

## Pinning model versions

Pin the dated snapshot, not the floating alias. An alias moves under you, and
when it does:

- behaviour changes with no deploy, so the change is not in your changelog;
- every historical eval score becomes incomparable
  (`evaluation.md`);
- prompts tuned against the old snapshot can regress, and the regression
  appears as a quality complaint with no code change to bisect.

Upgrading is then a deliberate change: run the eval set on the new snapshot,
compare against the pinned one, and move both the pin and the recorded
baseline together. Deprecation windows are the forcing function — track them,
because a retired model is a 404 that arrives at whatever time the provider
chose.

<!-- sources: openai-agents-python, anthropics-claude-api, vercel-ai-sdk, owasp-llm-top10, google-skills, anthropic-docs, openai-docs -->
