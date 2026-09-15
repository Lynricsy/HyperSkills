# KV reuse and request routing

Verified against: vLLM `vllm/config/cache.py`, `vllm/v1/metrics/loggers.py`,
SGLang `python/sglang/srt/entrypoints/http_server.py`.

## Contents

- [Prefix caching is already on](#prefix-caching-is-already-on)
- [Reading the hit rate](#reading-the-hit-rate)
- [Constructing a prefix-reuse benchmark](#constructing-a-prefix-reuse-benchmark)
- [Tiered KV offload](#tiered-kv-offload)
- [KV-aware routing](#kv-aware-routing)
- [When KV-aware routing is worse](#when-kv-aware-routing-is-worse)
- [Hot spots and session affinity](#hot-spots-and-session-affinity)
- [Block size is a consistency setting and a cost lever](#block-size-is-a-consistency-setting-and-a-cost-lever)
- [Queueing and admission](#queueing-and-admission)
- [Multiple router replicas](#multiple-router-replicas)

## Prefix caching is already on

vLLM's `CacheConfig.enable_prefix_caching` defaults to **`True`**. [official]
Passing `--enable-prefix-caching` is therefore a no-op, and the flag that changes
behaviour is `--no-enable-prefix-caching`. Any A/B that "turns prefix caching on"
measured nothing; the baseline arm is the one that must explicitly disable it.

The reuse itself works on the compressed/intermediate KV representation rather
than recomputing, which is why it pays off when prefill is compute-bound and
prefixes genuinely repeat — a shared system prompt, multi-turn sessions. Note it
stops being lossless once KV quantization (FP8 KV) is enabled. [official]

## Reading the hit rate

The two counters are declared in vLLM as `vllm:prefix_cache_queries` and
`vllm:prefix_cache_hits`, and their documentation strings say the unit is
**queried/cached tokens, not requests**. [verified]

**Query them by their exposed names, not their declared names.** The
`prometheus_client` library appends `_total` to every Counter when it renders the
`/metrics` endpoint, while Gauges are exposed verbatim. [verified] So the
time series that exist in Prometheus are:

```
hit_rate = rate(vllm:prefix_cache_hits_total[5m])
         / rate(vllm:prefix_cache_queries_total[5m])
```

The same rule explains why `vllm:num_preemptions_total` carries the suffix while
`vllm:gpu_cache_usage_perc` and `vllm:num_requests_waiting` do not — the first is
a Counter, the other two are Gauges. Reading a metric name out of the source and
pasting it into PromQL silently returns no data for every counter.

Cross-instance reuse through a KV connector has its own counters, declared as
`vllm:external_prefix_cache_queries` and `vllm:external_prefix_cache_hits` and
therefore queried with the same `_total` suffix. When evaluating cache-aware
routing, read local and external hits separately — merging them hides whether the
router is achieving anything. [official]

SGLang treats `cache_hit_rate` as a first-class metric (a `/v1/loads` field and
`sglang:cache_hit_rate`). **A hit-rate collapse after a deploy is the first
explanation to check for a TTFT regression**, before touching kernels. [official]

Adjacent capacity signal: `token_usage` approaching **1.0** means KV/token
capacity is saturated, and `num_waiting_reqs` rising while `gen_throughput` stays
low is queueing pressure rather than slow generation. [official]

## Constructing a prefix-reuse benchmark

Online, the dataset is `prefix_repetition` with four parameters: [official]

| Parameter | Meaning |
|---|---|
| `--prefix-repetition-prefix-len` | shared prefix tokens |
| `--prefix-repetition-suffix-len` | unique suffix tokens; total input = prefix + suffix |
| `--prefix-repetition-num-prefixes` | distinct prefixes; prompts per prefix = `num_requests // num_prefixes` |
| `--prefix-repetition-output-len` | output tokens |

From those semantics the target hit rate is analytic:

```
ideal token-level hit rate ≈ prefix_len / (prefix_len + suffix_len)
                             × (1 − num_prefixes / num_prompts)
```

Prefix 512, suffix 128, 5 prefixes over 100 prompts gives about
`0.8 × 0.95 ≈ 76%`. Varying `--prefix-repetition-num-prefixes` sweeps the hit-rate
curve.

Two flags are mandatory for this measurement to mean anything: [official]

- `--no-oversample`. Without it, a dataset smaller than `--num-prompts` is
  repeat-sampled, fabricating 100% prefix hits and overstating the benefit.
- `--disable-shuffle`. Shuffling changes the temporal locality of reuse, and
  therefore how many times a block is reused before eviction, so two shuffled
  runs are not comparable.

Offline, `benchmarks/benchmark_prefix_caching.py` needs no server. It takes
`--model`, `--num-prompts`, `--input-length-range min:max`, plus `--repeat-count`
(default 1; **higher raises the hit rate**), `--prefix-len` for a fixed shared
prefix, `--sort`, and `--disable-detokenize` to isolate engine performance from
detokenize overhead. [official]

For natural rather than synthetic reuse, ShareGPT with `--repeat-count 5` and
`--input-length-range 128:256` shows the prefix sharing that actually occurs in
multi-turn traffic, which is normally far below the synthetic ceiling. [official]

`--prefix-caching-hash-algo` offers `sha256` (default), `sha256_cbor`, `xxhash`,
`xxhash_cbor`. Hashing long prefixes has real CPU cost and xxhash is markedly
faster, so changing the algorithm changes the CPU side of hit lookup — compare
two runs only under the same algorithm. [official]

Profiling caveat: because repeated prompts are short-circuited by the cache,
prefill profiling needs mutually distinct probe prompts, and the server log should
confirm no cache short-circuit occurred inside the active prefill window.
[official]

## Tiered KV offload

Capacity invariants, violated at the cost of a regression: [official]

- The **CPU tier must not be smaller than the GPU KV tier**, or write-through
  churn degrades performance.
- The **disk tier must not be smaller than the CPU tier**, and its path must sit
  on a suitable block-device filesystem.
- Express capacity as either GB or block coverage — never a mix of both.

Promote offload when repeated long prefixes make prefill/TTFT dominant *and* host
or disk capacity can retain useful KV. Demote it when decode latency is the
primary objective, prefixes do not repeat, or the transfer and host-memory cost
has not been measured. [official]

Offload transfer has two opposing knobs: concurrent transfer count (too high
competes with inference and saturates the interconnect) and transfer batch size
(larger is more efficient per byte but raises per-request latency and transient
memory). [official]

Model-specific side caches — indexer K cache, scale-factor pools, landmark caches
— should be registered as a typed pool inside the unified paged KV manager sharing
block IDs, not given a private shadow allocator. Only then do they inherit
paging, prefix reuse, host offload, eviction and correct capacity accounting. Two
consequences: a mixed-dtype pool sums by **physical** dtype, and offloaded blocks
index by **decoded pool index** rather than logical block ID. [official]

## KV-aware routing

The routing decision is a weighted combination of **KV prefix overlap** and
**worker active load**. The balance is set by how much credit overlap receives,
and credit set too high **keeps sending requests to an already busy worker**. The
antidotes — overlap-credit decay and prefill-load scaling — are independent knobs;
change only the one the observed scoring problem supports. [official]

Routing modes available in a mature router: `round-robin`, `random`,
`power-of-two`, `least-loaded`, `kv`, `direct`, `device-aware-weighted`.
`power-of-two` and `least-loaded` take a synchronous prefill path under
disaggregated prefill; `direct` requires an external orchestrator to pick the
worker. [official]

Two TTL concepts are easy to conflate: [official]

- Approximate-mode router TTL applies **only when KV events are disabled**.
- Predicted-TTL bridges the short delay when a KV event arrives later than the
  next related request (paired with predict-on-route state) and **requires KV
  events to be enabled**.

They are independent settings.

Router load estimation can track active blocks, output blocks, prefill tokens and
assumed KV reuse — **each independently**. Output tracking and the reuse
assumption must match actual workload behaviour or the load estimate is
systematically biased. [official]

For external shared KV caches, a shared-cache hit **must not be valued the same
as a device-local hit** (it needs its own multiplier), or the router overestimates
the worth of remote reuse. [official]

## When KV-aware routing is worse

Three situations, all of which look like a router bug and are not: [official]

1. The prefix reuse exists only because the synthetic input repeats — real
   traffic has none.
2. Cache bookkeeping overhead dominates at the target load.
3. **Workers do not publish KV events.** In that case KV mode stalls waiting for
   events, and the deployment must switch to approximate mode (KV events off,
   default on) so the router *predicts* cache state from its own routing
   decisions instead.

When prefix reuse stops being valuable and load should dominate, a load-aware
preset exists — but it changes several router fields at once. Treat it as one
documented mode and **do not attribute its gain to any single field.** [official]

Experimental discipline for comparing routing modes: identical model, worker set,
prompt set, concurrency and sampling settings; to demonstrate KV reuse the prompts
must actually repeat prefixes; too few samples means it is labelled a smoke
comparison. **Never conclude a throughput improvement from a single chat
request.** [official]

## Hot spots and session affinity

Deterministic KV routing produces **persistent hot spots**. Router temperature
(0 = fully deterministic) spreads requests among similarly scored workers and
improves tail latency at the cost of hit locality. [official]

Session affinity TTL keeps a session's later requests on the same worker,
improving continuation locality and avoiding repeated prefill. The costs are skew,
and the fact that the binding is only **best-effort synchronised** across multiple
router replicas. [official]

## Block size is a consistency setting and a cost lever

First, consistency: the frontend's KV cache block size, the standalone router's
block size, and the backend engine's block size **must all be identical**, or
cache-overlap and capacity accounting are simply wrong. [official] This is not a
free tuning parameter.

Second, within that constraint, block size is a measurable routing cost. Smaller
blocks mean more blocks per prompt, which means more radix-tree and hashing work
in the frontend and more block bookkeeping in the worker: [official]

| Block size | Blocks for a 60k-token prompt | KV bookkeeping share of worker CPU |
|---|---|---|
| 64 | ≈ 940 | ≈ 48% |
| 512 | ≈ 117 | ≈ 3% |

That is a routing-side explanation for a CPU-bound frontend that no amount of GPU
tuning will fix.

## Queueing and admission

When every worker is saturated, concentrate the waiting at the router. Queue
policies: [official]

| Policy | Optimises |
|---|---|
| `fcfs` (default, with priority boosting) | tail TTFT |
| `wspt` (weighted shortest processing time, Smith's rule) | mean TTFT |
| `lcfs` | — |

**Deeper waiting adds no capacity.** It only re-expresses overload as latency.

Queueing introduces its own failure mode: a queued request is dispatched using a
**stale prefix-overlap score**. An overlap-refresh interval re-reads cache
locality after a long wait to improve the eventual worker choice; it only applies
when router queueing is on, lower values cost more indexing, and zero disables it.
[official]

Worker-side admission: an engine request limit caps active engine requests,
converting overload failures into controlled rejection. Set below the engine's
usable capacity it **strands throughput**; unset, worker-side rejection is off
entirely. A burst buffer queue is only effective once the engine request limit is
enabled, and a deeper queue again hides overload as latency. [official]

To drop over-busy workers from the candidate set earlier, thresholds exist on
active decode blocks and on active prefill tokens (absolute and fractional,
combined with OR). These run through rejection logic, so **set too tight they
leave capacity idle.** [official]

In-flight request migration on worker loss is a **resilience** path: its state
tracking costs memory and delivers nothing for a healthy steady-state service. Do
not treat it as a performance knob. [official]

## Multiple router replicas

Multiple frontend replicas require the chosen routing mode's state behaviour to
match. When replicas disagree about active sequences, replica synchronisation can
be enabled — best-effort, paid for in event-plane traffic. [official]

Request distribution and event transport are two independent planes: the request
plane changes router-to-worker latency and throughput, while the **KV event plane
changes cache-state propagation delay**, which directly affects the freshness of
every KV-aware feature. Switching either changes infrastructure and failure
behaviour, not just performance. [official]

Frontend saturation presents as endpoint-side queueing; the response is more
frontend replicas and more frontend CPU/memory, verified through per-pod CPU,
event-loop or request latency, and load distribution. Tokenization-bound CPU has
its own separate knobs, where a fast tokenizer implementation affects only BPE
encoding. [official]

`/health` returning green while requests time out is a known blind spot: use an
endpoint that actually runs a generate or embedding pass (`/health_generate`) to
catch a wedged scheduler or a broken worker path. [official]

<!-- sources: vllm-skills, vllm-docs, dynamo, sglang -->
