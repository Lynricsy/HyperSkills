# Generation jobs: transport, cost and artefacts

## Contents

- [Three transports, chosen by measured latency](#three-transports-chosen-by-measured-latency)
- [Verifying a webhook before trusting it](#verifying-a-webhook-before-trusting-it)
- [The state machine and the record that survives a crash](#the-state-machine-and-the-record-that-survives-a-crash)
- [Retrying a generation call is not idempotent](#retrying-a-generation-call-is-not-idempotent)
- [Quotas, rate limits, concurrency and cold starts](#quotas-rate-limits-concurrency-and-cold-starts)
- [The cost model is not a token budget](#the-cost-model-is-not-a-token-budget)
- [Spend caps that actually bind](#spend-caps-that-actually-bind)
- [Batch jobs: isolate failures, resume from the manifest](#batch-jobs-isolate-failures-resume-from-the-manifest)
- [Download, address by content, and record the link](#download-address-by-content-and-record-the-link)

## Three transports, chosen by measured latency

| Transport | When it applies | What breaks it |
|---|---|---|
| Synchronous wait | Only where the provider offers a blocking mode, and only for calls whose p99 you have measured under 60 s — in practice images and short speech | Providers cap the blocking window in the tens of seconds and recommend it only for very fast models [official]. Past the cap you get a timeout, while the job keeps running and keeps being billed |
| Polling | The default for everything else; simplest thing that works behind a firewall | Polling too fast burns rate limit; polling too slowly adds latency. Back off, and cap total wait |
| Webhook | High volume, or jobs long enough that holding a poller is wasteful | Requires a public HTTPS endpoint, signature verification, and an idempotent handler, because deliveries repeat |

Video, music and long-form audio are asynchronous by design regardless of
transport, because the latency distribution rules out blocking: one vendor
documents 11 seconds to 6 minutes for a single video [official].

Every synchronous path needs a defined fallback: on timeout, convert to
polling on the same job id rather than re-submitting. Re-submitting doubles
the bill and produces a second, different artefact.

## Verifying a webhook before trusting it

A webhook endpoint is an unauthenticated public URL until you verify the
signature. Providers sign with three headers — a delivery id, a timestamp and
the signature itself — and publish the signing secret through an API call
rather than in the dashboard [official]. Verification is not optional: without
it, anyone who learns the URL can assert that an arbitrary job succeeded with
an arbitrary output URL, and a naive handler will download and publish it.

The handler needs five properties:

1. Compute the signature over the documented payload — the delivery id, the
   timestamp and the raw body, in the documented order — using the raw bytes.
   Re-serialised JSON produces a different signature.
2. Compare in constant time.
3. Reject deliveries whose timestamp is outside a small tolerance, so a
   captured delivery cannot be replayed later.
4. Be idempotent on the delivery id. Redelivery after a timeout is normal.
5. Return quickly and do the work elsewhere. Downloading a video inside the
   handler is how deliveries start timing out and repeating.

Cache the signing secret; fetching it per delivery adds a request to the
critical path and a new failure mode.

## The state machine and the record that survives a crash

Hosted generation jobs move through a small, common state machine [official]:

```
submitted --> starting --> processing --> succeeded
                  |            |
                  +------------+--> failed
                  |            |
                  +------------+--> canceled
```

Two of the states matter more than they look. `starting` covers cold starts,
which on community-hosted models can dominate total latency and are not a
sign of anything being wrong. `canceled` is reachable without your asking:
providers offer a job lifetime after which a runaway job is cancelled
automatically [official]. Set one. A stuck job that never terminates is
billed for as long as it runs.

Persist the job record before the submitting process can die — id, model
version string, full parameters, prompt, submission time, and the business
object it belongs to — as a write-ahead step, not as part of handling the
response. A process that crashes between "provider accepted" and "we wrote it
down" leaves a paid job nobody can find, and the only recovery is listing the
provider's jobs and matching on timestamps.

## Retrying a generation call is not idempotent

The reflex to wrap a call in a retry loop is wrong here in a specific way: a
retried generation is a second paid job that returns a different artefact.
There is no request-level deduplication to save you, and the failure you are
retrying is frequently a client-side timeout on a job that is still running.

Before any retry of a submission, query the original job's state. Only two
outcomes justify submitting again:

- The submission was rejected before a job existed — a validation error, an
  authentication failure, a quota rejection. Nothing is running and nothing
  was billed.
- The job reached a terminal failed state and the cause is transient.

Everything else — timeouts, connection resets, an unreadable response — means
a job may exist. Find it first. Give each logical unit of work your own
idempotency key, store the provider job id against it, and make submission a
function that returns the existing job when the key is already known.

Retrying a safety rejection deserves its own rule: an identical resubmission
will be blocked identically. It is a prompt change or nothing.

## Quotas, rate limits, concurrency and cold starts

Four separate ceilings, commonly confused:

- **Requests per minute.** Synthesis endpoints in the region of 50 RPM are
  normal [official]. Build the limit into the client as a hard constraint, not
  a comment, and derive job concurrency from it.
- **Concurrent jobs.** Independent of RPM. Submitting 200 jobs in a minute may
  be allowed while only a few execute at once, so the queue is invisible to
  you and the last job's latency is the sum of everything ahead of it.
- **Account or project quota.** Daily or monthly ceilings that fail the
  request rather than queueing it. Distinguish a quota rejection from a rate
  limit in error handling: one should back off, the other should stop.
- **Cold start.** Community or rarely used model versions load weights on
  first use; the first job after idleness is far slower than steady state
  [official]. Keep a warm path for latency-sensitive work, or set user
  expectations to the cold number.

## The cost model is not a token budget

Generation pricing has nothing in common with context-window accounting, and
carrying the text-model mental model over produces estimates that are wrong by
an order of magnitude in either direction:

| Modality | Billed by |
|---|---|
| Image | Emitted image tokens, fixed per resolution tier, which the aspect ratio and quality tier select. Input images add input tokens, and a high input-fidelity setting raises them substantially [official] |
| Video | Duration and resolution tier of a clip, per job, with one clip per job [official] |
| Speech | Input characters |
| Recognition | Audio duration |
| Self-hosted or community models | GPU-seconds of actual execution; providers expose the measured prediction time per job [official] |

Two facts change how you budget. Image and video cost is knowable before the
run, because the tier fixes it — so a batch has a computable price and should
refuse to start if that price exceeds the cap. GPU-second cost is not knowable
in advance, because it depends on queueing, cold starts and the model's
runtime, so it needs a live ceiling instead.

Prompt length is close to free in all of these. Iterating on prompt wording is
cheap; iterating on resolution, duration or batch size is not.

## Spend caps that actually bind

- Compute the projected cost of a batch before submitting it, from the tier
  table and the item count, and abort above a threshold rather than
  discovering it in the invoice.
- Track spend per run, not only per month. The damaging pattern is one
  runaway loop inside a single run.
- Set the provider-side job lifetime so an individual job cannot bill
  indefinitely [official].
- Cap total attempts per logical item across the whole run. Unbounded
  per-item retries plus per-item cost is the shape of every expensive
  accident in this domain.

## Batch jobs: isolate failures, resume from the manifest

Run a batch from an explicit manifest — one row per item, with its parameters
and a stable item key — and write per-item state back into it as jobs settle.
That single structure delivers the three properties a batch needs:

- **Failure isolation.** One item's safety rejection or timeout marks that
  row; it does not abort the run and it does not roll back completed items.
- **Resume.** Re-running skips rows already marked succeeded, so a crash costs
  the in-flight items only. Without this, every restart re-pays for everything
  already produced.
- **Auditability.** The manifest is the mapping from business item to job id
  to artefact hash, which is what you need when one published asset has to be
  explained months later.

Classify failures before retrying them: validation errors are permanent and
should be reported, safety rejections need a prompt change, rate limits need
backoff, and infrastructure failures can be retried once the original job's
state has been checked.

## Download, address by content, and record the link

Provider retention is not storage and the schedules do not agree — output URLs
that expire an hour after completion, generated video deleted server-side
after two days, and endpoints that return bytes inline and retain nothing are
all current behaviour [official]. Downloading and writing to your own storage
is a step of the generation flow.

Do it in the same run that created the artefact, before the job is reported
successful. Then:

- Address the stored object by the hash of its bytes. Two jobs producing
  identical bytes deduplicate; a re-download producing different bytes is
  immediately visible instead of silently overwriting.
- Store the generation record — prompt as sent, model version string, all
  parameters, seed, job id, timestamps, and the artefact hash — as a row that
  points at the object, not as filename convention.
- Keep the mapping bidirectional. Given a published asset you must be able to
  find the job; given a job you must be able to find everything it produced.
- Never reference a provider URL from durable state. A link stored in a
  database is a scheduled 404.

<!-- sources: replicate-skills, google-gemini-docs, openai-skills-imagegen, openai-skills-speech, fal-community-skills -->
