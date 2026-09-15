# Engine configuration and capacity

Verified against: vLLM 0.29.0 source (`vllm/config/cache.py`,
`vllm/config/scheduler.py`, `vllm/engine/arg_utils.py`,
`vllm/v1/core/sched/scheduler.py`), TensorRT-LLM and SGLang documentation.
Defaults below are interface facts pinned to that release; the mechanisms are
not.

## Contents

- [Where the memory goes at inference](#where-the-memory-goes-at-inference)
- [max-model-len is a KV reservation](#max-model-len-is-a-kv-reservation)
- [The batched-token budget and chunked prefill](#the-batched-token-budget-and-chunked-prefill)
- [Preemption is the capacity signal](#preemption-is-the-capacity-signal)
- [CUDA graphs and startup](#cuda-graphs-and-startup)
- [Where the metrics are](#where-the-metrics-are)
- [Adapters](#adapters)
- [Latency versus throughput](#latency-versus-throughput)
- [The same knobs in other engines](#the-same-knobs-in-other-engines)

## Where the memory goes at inference

Training's four terms collapse to two: **weights** and **KV cache**. There are
no gradients and no optimizer state, and activations are one forward pass with
nothing retained for backward.

vLLM pre-allocates. It takes `gpu_memory_utilization` of the device, subtracts
weights and the profiled activation peak, and gives the remainder to the KV
cache as paged blocks. **KV cache is the residual**, so anything that grows the
weights or the reserved overhead shrinks concurrency — and it does so silently,
surfacing as preemption rather than as an error.

`gpu_memory_utilization` defaults to **0.92** in 0.29.0 (it was 0.90 in earlier
releases — check the version before quoting a number). [verified] It is a
per-instance limit and is unaware of any other process on the card: two
instances at 0.92 on one GPU do not negotiate, they both try to take 92%.
[verified] Pushing toward 0.98 leaves no room for the profiled activation peak,
CUDA-graph capture buffers or the framework's own allocations, and produces
either a start-up OOM or a crash under the first real burst.

The reason the ceiling is not higher is worth stating plainly: the headroom is
not slack, it is a reservation for allocations that happen *after* the KV cache
is sized.

## max-model-len is a KV reservation

`--max-model-len` is not "how long a prompt we allow". It sets the ceiling the
scheduler reserves against, out of the same pool that serves concurrency.
Declaring 128k for a workload whose prompts top out at 12k spends the KV cache
on capacity nobody uses, and the symptom is low concurrency with constant
preemption — never an error mentioning length.

Set it from the measured p99 of prompt plus completion, with headroom. When
some requests genuinely need more, give them a second deployment rather than
sizing the whole fleet for the tail.

The inverse error is worse because it is silent in the other direction: a value
*below* the real p99 makes those requests fail outright rather than be served
slowly. Check the context budget against the prompt-length distribution before
tuning anything else.

Other levers on the same pool: `--max-num-seqs` (concurrent sequences),
quantizing the weights, quantizing the KV cache, and tensor parallelism — which
shards the weights and therefore leaves more room per card.

## The batched-token budget and chunked prefill

Chunked prefill splits large prefills into chunks and batches them with decode
requests; the V1 scheduler prioritises decodes.

**The default is decided by the model, not hardcoded.** `enable_chunked_prefill`
arrives as `None` and is resolved from `model_config.is_chunked_prefill_supported`
(prefix caching resolves the same way from `is_prefix_caching_supported`).
[verified] So "chunked prefill is on by default" is true for most generate
models and false for others, and the honest way to know is the startup log line
that names the resolved value together with `max_num_batched_tokens`.

Overriding it manually is guarded rather than forbidden: disabling chunked
prefill on a `generate` model that supports it logs *"This model does not
officially support disabling chunked prefill. Disabling this manually may cause
the engine to crash or produce incorrect outputs."* The mirror case — enabling
it on a `pooling` model that does not support it — warns identically.
[verified] Treat either warning as a configuration bug, not as noise.

With chunked prefill **disabled**, `max_num_batched_tokens` must be at least
`max_model_len`. Violating it raises a `ValueError` naming both values and
explaining that the smaller budget would otherwise cap the sequence length and
reject longer sequences. [verified] It is a clean startup failure with a
readable message — do not go looking for an OOM.

One more guard is only a warning and therefore easy to leave in place:
`max_num_batched_tokens > max_num_seqs * max_model_len` logs *"may lead to
unexpected behavior"* and continues. [verified]

Tuning the budget with chunked prefill on:

| Direction | Effect |
|---|---|
| Smaller (around 2048) | better inter-token latency — decodes are interrupted less |
| Larger (above 8192) | better TTFT and better throughput, especially small models on large GPUs |

The mechanism behind both rows is the same: a large prefill chunk occupies the
step that a decode would otherwise have used. That is why ITL p99 is the metric
that moves first when this budget is wrong.

## Preemption is the capacity signal

```
Sequence group N is preempted by PreemptionMode.RECOMPUTE mode because
there is not enough KV cache space ... total_cumulative_preemption_cnt=...
```

This is a capacity message, not a bug. V1 preempts by recomputation rather than
by swapping, because recompute is cheaper in that architecture. A steadily
rising `vllm:num_preemptions_total` means the KV cache cannot hold the working
set, and the cost lands on TTFT (the recomputed prefill re-queues) and on
throughput (work is done twice).

Under `SchedulingPolicy.PRIORITY` the victim is chosen explicitly: the running
request with the highest `(priority, arrival_time)` is preempted first.
[verified] A priority class therefore does change who suffers — which is the
one way to protect a latency-critical tenant from a batch tenant on a shared
deployment.

Fixes in order of what they cost you:

1. reduce `max_model_len` to the real requirement
2. reduce `max_num_seqs`
3. raise `gpu_memory_utilization` **if** there is genuinely headroom
4. add tensor parallelism

Step 3 is third because it trades a preemption warning for a crash under load.
Step 4 is last because it costs a GPU and adds a collective to every layer.

## CUDA graphs and startup

`--enforce-eager` disables CUDA-graph capture entirely. It makes start-up fast
and costs steady-state decode performance. It is a development setting that
reaches production because it once made an OOM go away — and the OOM it fixed
was the capture buffer, which has a cheaper fix.

When capture memory is the problem, restrict the captured batch sizes through
`compilation_config.cudagraph_capture_sizes` instead of turning capture off.
The capture set must cover the batch shapes the engine actually reaches at every
operating point you benchmark, or the measurement silently falls off the graphed
path at the shapes it does not cover.

Capture happens during startup, after weight load and KV profiling. It is
therefore part of the cold-start budget a startup probe has to cover, and it is
the reason the last minute of a multi-minute startup shows no log activity.

## Where the metrics are

vLLM exposes Prometheus metrics on the **`/metrics` path of the API server
port**. With `vllm serve ... --port 8000` that is `http://host:8000/metrics`.
There is no separate metrics port and no flag to enable them — `--enable-metrics`
is not an argument of `vllm serve`. [verified] A deployment scraping 9090 is
scraping nothing.

Worth alerting on:

| Metric | Why |
|---|---|
| `vllm:num_preemptions_total` | rising means the KV cache is undersized |
| `vllm:gpu_cache_usage_perc` | approaching 1.0 means capacity is saturated |
| `vllm:num_requests_waiting` | queue depth — the scaling signal |
| TTFT histogram | the SLO most users feel |

The counter-versus-gauge naming trap that makes half of these queries silently
return nothing is in `references/kv-reuse-and-routing.md`; read it before
writing PromQL against any of these names.

## Adapters

Serving a LoRA adapter unmerged keeps one base model resident and swaps
adapters per request — right when there are many adapters and moderate traffic.
Merging the adapter into the weights is faster per request and is the right
default for a single adapter in production.

Either way the base model revision must match the one the adapter was trained
against. A mismatch does not error; it degrades.

The capacity consequence is the one that gets missed: unmerged adapters occupy
memory that came out of the KV cache, and each concurrent distinct adapter adds
to that. On a deployment that is already preempting, enabling multi-LoRA makes
the preemption worse, and the evidence will look like a throughput regression
with no configuration change to the model.

## Latency versus throughput

They are the same resource spent differently, and no configuration maximises
both:

| Goal | Move |
|---|---|
| Lower TTFT | smaller `max_num_batched_tokens`, lower concurrency, prefix caching for shared prompts |
| Higher throughput | larger `max_num_batched_tokens`, higher `max_num_seqs`, more KV cache |
| Lower inter-token latency | smaller batched-token budget so decodes are not stalled behind prefills |

State which one the product needs before tuning. "Long prompts, short answers,
humans waiting" is a TTFT workload, and prefill cost per request is the thing to
attack — with prefix caching when the prompts share a prefix, and by not sending
content the model does not need.

## The same knobs in other engines

The mechanisms transfer; the names and the failure modes do not.

| Concern | vLLM | SGLang | TensorRT-LLM |
|---|---|---|---|
| Memory fraction for the engine | `--gpu-memory-utilization` | `--mem-fraction-static` | `kv_cache_config.free_gpu_memory_fraction` |
| Context ceiling | `--max-model-len` | `--context-length` | `max_seq_len` |
| Concurrency cap | `--max-num-seqs` | `--max-running-requests` | `max_batch_size` |
| Batched-token budget | `--max-num-batched-tokens` | `--chunked-prefill-size` | `max_num_tokens` |
| Prefix reuse | on by model support; `vllm:prefix_cache_*` | RadixAttention; `sglang:cache_hit_rate` | KV cache reuse, block reuse settings |

Two differences worth knowing before porting a configuration:

- SGLang exposes cache hit rate as a first-class metric and a `/v1/loads`
  field, which makes hit-rate regressions easier to see than in vLLM, where it
  must be derived from two counters.
- TensorRT-LLM couples more decisions to build time than to serve time, so a
  knob that is a flag in vLLM may be a rebuild here. Check whether the change
  you are proposing is a serve-time flag at all before scheduling the
  experiment.

<!-- sources: vllm-source, vllm-docs, vllm-skills, trtllm, sglang, nvidia-skills -->
