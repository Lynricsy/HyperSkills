---
name: model-serving
description: "Benchmarks and tunes deployed LLM inference servers for latency, throughput and capacity"
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.15"
  category: task
---

# model-serving

## Scope

Covers the performance of a model that is already being served: designing a
benchmark that predicts production, turning an SLO into a capacity number,
attributing a latency or throughput regression to a cause, KV cache reuse and
request routing, inference-side parallelism and topology, and the signals that
drive replica scaling. Engines: vLLM primarily, with SGLang, TensorRT-LLM and
Dynamo where their behaviour differs.

Not covered:

- Training, fine-tuning and anything that changes weights, including the
  handoff of a checkpoint to a server, quantization format selection and
  training-side memory tuning: the `ml-training` skill.
- Getting a GPU into a container, device plugins, MIG and time-slicing,
  RuntimeClass, driver/CUDA compatibility, probe and manifest shape: the
  `containers` skill. This skill says what the probe budget must cover and why;
  `containers` says how probes behave.
- Prompt design, RAG, agent loops, tool calling and model selection for a
  product: the `ai-engineering` skill.
- Tracing, dashboards, alert routing and SLO bookkeeping as a practice: the
  `observability` skill. The serving metrics worth alerting on are here.
- Managed inference control planes (SageMaker, Vertex, Azure ML): the `aws`,
  `gcp` and `azure` skills.

## Core rules

1. Establish the situation from the artefact before applying any rule below.
   State what its numbers, events and log lines actually say — including when
   they contradict the question's premise — then name the workload objective,
   because TTFT, TPOT and throughput are the same resource spent differently
   and no configuration maximises all three. A generic checklist that does not
   quote this deployment's values is not a diagnosis, and every rule below is
   worthless applied to a situation that was never established.
2. A benchmark with `--request-rate inf` measures the saturation ceiling, not
   latency. Every percentile in such a run is a queueing artefact and cannot
   become an SLO.
3. Derive capacity from a rate sweep against an SLO, never by dividing a
   saturation throughput number by a target rate. Sweep the rate and find where
   goodput collapses; that rate is the capacity number.
4. Never plan capacity from a single run. One un-repeated run has no noise
   floor, so a difference between two configurations cannot be attributed to
   the change.
5. Discard the first run after a fresh start. It carries weight load,
   `torch.compile` and CUDA-graph capture; warmup is hundreds of requests, not
   ten.
6. Check the readiness gate explicitly rather than trusting a default - the
   benchmark CLI's ready check is skipped by default, so a script that starts a
   server, sleeps and measures has no gate at all.
7. Make the synthetic load match production in four dimensions or say which one
   it does not: input/output length distributions, arrival schedule, rate and
   burstiness, and prefix reuse structure. A fixed 512/512 shape understates p99
   and overstates throughput.
8. Pass `--ignore-eos` when comparing configurations, otherwise the output
   length is only a ceiling and generated-token counts are incomparable.
9. Read the metric that matches the question: TPOT for capacity planning, ITL
   p99 for jitter, E2EL for what a waiting human experiences. E2EL is not
   reported unless requested.
10. Treat GPU utilization as a liveness signal, never a saturation signal.
   Decode is memory-bandwidth-bound, so utilization reads near-full at three
   requests in flight and at three hundred; a metric that is nearly constant
   cannot drive an autoscaler.
11. Use KV cache occupancy, queue depth and preemption as the saturation
   signals: `vllm:gpu_cache_usage_perc`, `vllm:num_requests_waiting`,
   `vllm:num_preemptions_total`. Preemption is a capacity signal, not a bug.
12. Scale on queue depth or latency against the SLO, not on GPU utilization.
   Before prescribing any damping, read the scaling events and pod states to
   establish what the autoscaler is actually doing: a replica count that falls
   while every event is a scale-up is capacity being destroyed underneath it
   (restarts, evictions, unschedulable pods), not an autoscaler oscillating,
   and damping the wrong direction of a loop that was never oscillating fixes
   nothing.
13. Size the startup budget from a measured cold start with its parts named
   (checkpoint load, KV profiling, CUDA-graph capture). Weight load from network
   storage usually dominates and is fixed by moving the weights, not by tuning
   probe numbers.
14. Readiness must mean the engine can accept work. An endpoint that answers
   while the engine is still loading produces 503s behind a Ready pod and takes
   the replica into rotation early.
15. Attack prefill cost with prefix caching before anything else when requests
   share a system prompt; it is the only lever that makes the shared part free.
   Measure it as a hit rate over tokens, not requests.
16. Read cache hit rate as `rate(hits) / rate(queries)` over the counters the
   engine exposes, and keep local and external hits separate - merging them
   hides whether a cache-aware router is achieving anything.
17. Check the hit rate first when TTFT regresses after a deploy. A prefix-cache
   collapse explains more TTFT regressions than any kernel change.
18. Speculative decoding shortens decode only. It cannot improve TTFT, and it
   is a low-concurrency tool: at production concurrency, continuous batching
   already keeps the GPU busy and speculation competes with it.
19. Justify a draft-token count with a measured acceptance rate. Above roughly
   0.6 acceptance the longer proposals pay for themselves; below it they are
   wasted verification work.
20. Account for every byte a feature takes out of the KV cache. A draft model,
   a LoRA adapter and a larger CUDA-graph capture set all shrink the cache, and
   the cost appears as preemption rather than as an error.
21. Read `--gpu-memory-utilization`'s default from the release in use (0.92 in
   vLLM 0.29.0, 0.90 earlier) and treat anything near 0.98 as trading a
   preemption warning for a start-up or burst-time crash; the headroom covers the
   profiled activation peak and graph capture buffers.
22. `--max-model-len` is a KV reservation, not a request filter. Set it from the
   p99 prompt length that must be served and give the long tail its own
   deployment; a value below the real p99 rejects those requests outright.
23. Pick a parallelism strategy from what is actually scarce: memory, latency
   or per-GPU throughput. Tensor parallelism must divide the attention head
   count, and pipeline parallelism solves capacity rather than latency.
24. Keep tensor parallelism inside one NVLink domain and cross node boundaries
   with pipeline or data parallelism. TP across nodes is almost always a net
   loss.
25. Report the version of every engine flag you rely on. Defaults in this
   ecosystem reverse between releases, so a flag's behaviour is a fact about a
   release, not about the tool.

## Workflows

### benchmark-a-serving-deployment

Read `references/benchmarking.md`.

- [ ] Write down the objective and the SLO first (TTFT, TPOT or E2EL, and the
      target rate). Without it there is no pass/fail.
- [ ] Characterise production: input and output length distributions, arrival
      rate and burstiness, prefix reuse. Every one you cannot measure is a
      caveat that belongs in the report.
- [ ] Choose the load source in this order: a real trace, then a preset dataset
      that matches the shape, then a parameterised synthetic load. State which
      one and why.
- [ ] Gate on readiness explicitly, then warm up with hundreds of requests and
      discard that run.
- [ ] Sweep finite request rates (or a linear ramp) with a goodput SLO
      attached, holding burstiness fixed, and find where goodput collapses.
- [ ] Repeat each point enough times to have a noise floor, and save results
      with metadata so two runs can be compared later.
- [ ] **Gate:** the report states the objective, the four load dimensions, the
      rate at which goodput collapsed, the noise floor, and every dimension
      that was not reproduced. A report without a stated arrival model is not
      signed off.

### diagnose-a-latency-or-throughput-regression

- [ ] Separate the symptom before theorising: TTFT is prefill and queueing,
      TPOT and ITL are decode, E2EL includes client-side queueing.
- [ ] Read the saturation signals, not utilization: KV cache occupancy, queue
      depth, preemption counters.
- [ ] For a TTFT regression, check the prefix cache hit rate first
      (`references/kv-reuse-and-routing.md`), then prompt length distribution,
      then the batched-token budget.
- [ ] For a throughput regression with rising preemption, find what took memory
      out of the KV cache - a new adapter, a draft model, a larger context
      setting, a capture-size change.
- [ ] For jitter without a mean change, read ITL p99 and look for prefill
      chunks stalling decodes.
- [ ] **Gate:** name the mechanism and the metric that would move if the
      diagnosis is right, then change one thing and re-measure it.

### size-and-scale-a-deployment

- [ ] Establish per-replica capacity from a rate sweep first; replica count
      without it is arithmetic on a guessed number.
- [ ] Check the context budget against the p99 prompt length before scaling
      anything, then decide where the long tail is served.
- [ ] Pick the scaling signal: queue depth or latency against the SLO. Reject
      GPU utilization and say why.
- [ ] Break the measured cold start into its parts (checkpoint load, KV
      profiling, graph capture) with the number for each, name the dominant
      term, and decide whether the fix is warm capacity, faster weight loading,
      or admission control.
- [ ] Read the scaling events and pod states before changing autoscaler
      parameters, and state which case this deployment is in from the values
      you read: a genuinely oscillating loop (events in both directions), or
      capacity disappearing under an autoscaler that only ever scales up
      (restarts, evictions, pods pending against the node ceiling). Damp
      scale-down past the cold start only once the loop is confirmed.
- [ ] **Gate:** state the SLO-compliant rate per replica, the replica count
      including failure headroom, and what happens to requests that arrive
      during a cold start.

### evaluate-a-serving-configuration-change

Use for a proposal such as enabling speculative decoding, raising memory
utilization, changing parallelism, or adding adapters.

- [ ] State which metric the change is supposed to move, and check it is the
      metric that is actually failing. Speculative decoding cannot move TTFT.
- [ ] State what the change takes away, usually KV cache, and predict the
      preemption consequence.
- [ ] Require measurement at both concurrency 1 and production concurrency; a
      single-stream improvement says nothing about queue behaviour.
- [ ] Define the withdrawal rule before enabling it: the improvement threshold
      at production concurrency, and the throughput regression that cancels it.
- [ ] **Gate:** the decision cites a number measured at production concurrency,
      not a single-request observation, and a withdrawal rule that a later
      operator can apply.

## Topic router

| Topic | Read when | File |
|---|---|---|
| What a closed-loop client measures, open vs closed loop and burstiness, warmup and readiness traps, metric definitions that get misread, goodput and SLO-to-capacity, synthetic load fidelity, comparing configuration families, reporting | Designing, running or reviewing a serving benchmark | `references/benchmarking.md` |
| What topology decides and what it does not, tensor/pipeline/data/expert parallelism and their failure modes, attention-head divisibility, NVLink domains and cross-node collectives, CUDA-graph capture across operating points, prefill/decode disaggregation | Choosing or changing a parallelism or placement strategy | `references/parallelism-and-topology.md` |
| Prefix caching semantics and hit-rate measurement, the counter/gauge naming trap in PromQL, cache-aware routing and KV connectors, constructing a prefix-reuse benchmark, adapter and multi-tenant KV effects, queue-depth routing | Attacking prefill cost, or a TTFT regression after a deploy | `references/kv-reuse-and-routing.md` |
| Inference memory model and KV as the residual, `max-model-len` as a reservation, the batched-token budget and chunked prefill, preemption and its fix order, CUDA-graph capture, where the metrics are, adapter capacity cost, equivalent knobs in SGLang and TensorRT-LLM | Setting or reviewing engine configuration, or capacity is short | `references/engine-configuration.md` |

## Output format

When reviewing a benchmark, a scaling configuration or a proposed change, lead
with the decision, then group evidence by claim:

```
Decision: <sign off | reject | conditional on X>

<claim being examined>
  Evidence: <value quoted from the artefact, with file and line>
  Consequence: <what it means for the question asked>
  Fix: <the change, or the measurement that would settle it>
```

**Every claim must carry a value from the artefact.** A row whose Evidence
line would read "check whether X is high" is not a finding — either quote the
value the artefact already gives, or move it to an explicitly separate list of
things to measure next. Reviews fail in practice by returning a plausible
checklist instead of reading the evidence that was supplied.

Quote flags and metric names exactly as they appear in the artefact. Separate
what was measured from what was inferred, and list the production dimensions
the benchmark did not reproduce - an unstated caveat is the failure mode this
skill exists to prevent.

## Environment

- Facts about vLLM CLI flags, defaults and metric names in this skill are
  pinned to **vLLM 0.29.0**. Defaults in this ecosystem reverse between
  releases; check `vllm bench serve --help` and the engine's `/metrics` output
  against the version in use before quoting one.
- `vllm bench serve` ships with vLLM; NVIDIA AIPerf and `genai-perf` are
  alternatives for multi-engine comparison.
- Prometheus is needed to read the serving metrics over time; the counter
  suffix trap in `references/kv-reuse-and-routing.md` applies to any PromQL
  query written against engine metric names.
