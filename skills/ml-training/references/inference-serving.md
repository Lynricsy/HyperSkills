# Serving a model you trained

Verified against: vLLM V1 documentation (`docs/configuration/`, `docs/usage/metrics.md`).

## Contents

- [The handoff](#the-handoff)
- [Where the memory goes at inference](#where-the-memory-goes-at-inference)
- [max-model-len is a KV cache decision](#max-model-len-is-a-kv-cache-decision)
- [Chunked prefill and the batched-token budget](#chunked-prefill-and-the-batched-token-budget)
- [Preemption](#preemption)
- [CUDA graphs and startup](#cuda-graphs-and-startup)
- [Metrics](#metrics)
- [Serving adapters](#serving-adapters)
- [Latency versus throughput](#latency-versus-throughput)

## The handoff

A checkpoint is not a service. Before serving, confirm three things, because
each is a silent quality regression rather than an error:

- the chat template the server applies is the one the model was trained with
- the tokenizer shipped in the checkpoint is the one training used
- the stop strings and EOS handling match, or generations run to the length
  limit and get truncated mid-sentence

Serve the merged bf16 model first and measure it. Quantize afterwards, and
compare against that bf16 number rather than against expectations.

## Where the memory goes at inference

Training's four terms collapse to two: **weights** and **KV cache**. There
are no gradients and no optimizer state. Activations are small — one forward
pass over a batch, nothing retained for backward.

vLLM pre-allocates: it takes `gpu_memory_utilization` of the device, subtracts
weights and profiled activation peak, and gives the remainder to the KV
cache as paged blocks. So **KV cache is the residual**, and everything that
grows the weights or the reserved overhead shrinks your concurrency.

`gpu_memory_utilization=0.9` is the default and is already aggressive. Pushing
to 0.98 leaves no room for the profiled activation peak, CUDA graph capture
buffers, or the framework's own allocations, and produces a start-up OOM or a
crash under the first real burst.

## max-model-len is a KV cache decision

`--max-model-len` is not "how long a prompt we allow". It sets the ceiling
the scheduler reserves against, and it is measured out of the same pool that
serves concurrency. Declaring 128k on a workload whose prompts top out at
12k spends the KV cache on capacity nobody uses, and the symptom is
low concurrency with constant preemption rather than any error mentioning
length.

Set it from the measured p99 of prompt plus completion, with headroom. If
some requests genuinely need more, run a second deployment for them rather
than sizing the whole fleet for the tail.

Other real levers on the same pool: `--max-num-seqs` (concurrent sequences),
quantizing the weights, quantizing the KV cache, and tensor parallelism —
which shards the weights and therefore leaves more room per card. [official]

## Chunked prefill and the batched-token budget

In vLLM V1 chunked prefill is **enabled by default whenever possible**: large
prefills are split into chunks and batched with decode requests, and the
scheduler prioritises decodes. [official]

The constraint that breaks start-up: with chunked prefill **disabled**,
`max_num_batched_tokens` must be greater than `max_model_len`, otherwise the
server can crash at start-up. [official] A config that disables chunked
prefill and sets a small token budget against a huge model length fails
before serving a single request — and the log simply stops after the weights
load, which reads like an OOM and is not one.

Tuning `max_num_batched_tokens` with chunked prefill on: [official]

- smaller (around 2048) — better inter-token latency, decodes are interrupted
  less
- larger (above 8192) — better time-to-first-token and better throughput,
  particularly for small models on large GPUs

## Preemption

```
Sequence group N is preempted by PreemptionMode.RECOMPUTE mode because
there is not enough KV cache space ... total_cumulative_preemption_cnt=...
```

This is a capacity message, not a bug. V1 preempts by recomputation rather
than swapping, because recompute is cheaper in that architecture. [official]
A steadily rising counter means the KV cache cannot hold the working set.

The fixes, in order of what they cost you: reduce `max_model_len` to the real
requirement; reduce `max_num_seqs`; raise `gpu_memory_utilization` if there
is genuinely headroom; add tensor parallelism. [official] Raising utilisation
is listed third because it is the one that trades a preemption warning for a
crash under load.

## CUDA graphs and startup

`--enforce-eager` disables CUDA graph capture entirely. It makes start-up
fast and costs steady-state decode performance — it is a development and
debugging setting that ends up in production configs because it once made an
OOM go away. [official] If graph capture memory is the problem, restrict the
captured batch sizes via `compilation_config.cudagraph_capture_sizes`
instead of turning capture off. [official]

## Metrics

vLLM exposes Prometheus metrics on the **`/metrics` path of the API server
port**. With `vllm serve ... --port 8000`, that is
`http://host:8000/metrics`. [official] `vllm serve` has no separate metrics
port and no flag to enable them — a deployment scraping port 9090 is scraping
nothing. (`--enable-metrics` does exist, but only on `vllm run-batch`, where
it starts a Prometheus server on that command's own `--port`.)

Worth alerting on: `vllm:num_preemptions_total` (rising means the KV cache is
undersized), the KV cache usage gauge, and the time-to-first-token histogram.

## Serving adapters

Serving a LoRA adapter unmerged keeps one base model resident and swaps
adapters per request — right when you have many adapters and moderate
traffic. Merging the adapter into the weights is faster per request and is
the right default for a single adapter in production.

Either way the base model revision must match the one the adapter was trained
against. A mismatch does not error; it degrades.

## Latency versus throughput

They are the same resource spent differently, and a config cannot maximise
both:

| Goal | Move |
|---|---|
| Lower TTFT | smaller `max_num_batched_tokens`, lower concurrency, prefix caching for shared system prompts |
| Higher throughput | larger `max_num_batched_tokens`, higher `max_num_seqs`, more KV cache |
| Lower inter-token latency | smaller batched-token budget so decodes are not stalled behind prefills |

State which one the product needs before tuning. "Long prompts, short
answers, humans waiting" is a TTFT workload, and the prefill cost per request
is the thing to attack — with prefix caching if the prompts share a prefix,
and by not pasting content the model does not need.

<!-- sources: vllm-docs, orchestra-ai-research -->
