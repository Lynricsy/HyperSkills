# Benchmarking a serving deployment

Verified against: vLLM 0.29.0 (`vllm bench serve` and
`vllm/benchmarks/datasets/datasets.py`), NVIDIA AIPerf CLI fields. Flag names and
defaults below are interface facts pinned to that release; the mechanisms are not.

## Contents

- [What a closed-loop client actually measures](#what-a-closed-loop-client-actually-measures)
- [Open loop, closed loop, and burstiness](#open-loop-closed-loop-and-burstiness)
- [Warmup, and what the first run contains](#warmup-and-what-the-first-run-contains)
- [Metric definitions that get misread](#metric-definitions-that-get-misread)
- [Sweeping: where to put the points](#sweeping-where-to-put-the-points)
- [From an SLO to a capacity number](#from-an-slo-to-a-capacity-number)
- [Comparing configuration families](#comparing-configuration-families)
- [Synthetic load versus real load](#synthetic-load-versus-real-load)
- [The noise floor](#the-noise-floor)
- [What makes two runs comparable](#what-makes-two-runs-comparable)
- [The client is a common false bottleneck](#the-client-is-a-common-false-bottleneck)
- [Audit a result before explaining it](#audit-a-result-before-explaining-it)

## What a closed-loop client actually measures

A fixed-in-flight client measures itself as much as the server:

```
throughput ≈ concurrency / mean_request_latency          (Little's law)
```

A closed-loop result is **not** maximum server throughput: it follows the chosen
concurrency and observed latency. [official] Doubling concurrency need not double
throughput; low throughput can mean low concurrency, not a slow server.
Two consequences:

- **Service-process CPU idle at fixed concurrency usually means latency-bound,
  not "server is fast"**: each request spends most of its time waiting between
  streamed tokens. Pushing the server toward saturation needs higher concurrency
  *and* lower per-request latency (shorter outputs, smaller blocks). [official]
- **Congestion collapse is real**: past some point, raising concurrency makes
  throughput *fall*, because latency explodes faster than concurrency rises.
  Sweep for the knee; never assume more load means more throughput. [official]

The latency decomposition that localises the problem:

```
request_latency ≈ TTFT + output_tokens × ITL
```

If TTFT dominates and grows with load, the bottleneck is upstream of generation —
queueing, admission, or prefill capacity — not the decode kernels. [official]

## Open loop, closed loop, and burstiness

`vllm bench serve --request-rate` defaults to `inf`: **every request is issued
at t=0**, measuring the saturation ceiling. [official] Its latency percentiles
are queueing artefacts, not SLOs: mean TTFT of 8 s versus production p99 of 1.9 s
reflects the queue, not the model.

With a finite rate, arrival times are synthesised from a Poisson process or a
gamma distribution, which is what produces a latency curve at a given RPS.
[official] `--burstiness` (default `1.0`) only takes effect at finite rates:

| `--burstiness` | Arrival shape | Effect on p99 |
|---|---|---|
| `1.0` | Poisson | the baseline |
| `0 < b < 1` | gamma, more bursty | inflated |
| `b > 1` | more uniform | deflated |

Burstiness alone can move p99 severalfold at identical RPS; pin it across
comparisons. [official] `--max-concurrency` caps in-flight requests, whereas
`--request-rate` gates issue rate. With both set, achieved rate can fall below
requested rate. The report's `qps` label is *configured*, not measured; quoting
it unchecked overstates capacity. [official]

## Warmup, and what the first run contains

`--num-warmups` defaults to **0**; default-configuration first requests therefore
include weight load, `torch.compile`, and CUDA-graph capture. [verified]

The readiness-check **default reversed between releases**: in 0.29.0,
`--ready-check-timeout-sec` defaults to `0`, **skipping the check entirely**;
in 0.11.0 it defaulted to `600`, as its help text stated. [verified] The check
runs only above zero. A start-server/sleep/run-CLI script was guarded on the
older release but is unguarded now and can measure before the server is up.
Pass the flag explicitly rather than relying on a remembered version default.
The benchmark *function* still has Python default
`ready_check_timeout_sec: int = 600`, but argparse supplies `0`: the signature
does not give the CLI default. [verified]

Warmup serves two distinct purposes — priming the prefix cache and priming the
memory allocator — and a realistic warmup is hundreds of requests, not ten.
[official] Even with warmup, **the first run after a new build is a systematically
slow outlier and should be discarded.** [official]

On ROCm the first request additionally pays HIP kernel compilation, measured at
40-45 s on `gfx942`; a warmup request after the health check returns 200 is
mandatory or it lands inside the measurement. [official] CPU backends compile on
first token too, sometimes one to two minutes. [official]

Tear the server down and restart it between runs. Router and tokenizer caches
accumulate state across runs, so a reused instance inflates later runs; verify
the worker count in service discovery has actually reached zero, because
lease-backed keys linger until expiry. [official]

Never compile during a run — the compiler steals cores and ruins it. [official]

## Metric definitions that get misread

```
TPOT = (latency - ttft) / (output_len - 1)
```

When `output_len <= 1`, TPOT is recorded as 0 and still counted in goodput,
artificially lowering short-output TPOT means. [official] **ITL is not TPOT**:
it measures gaps between streamed chunks. Backends packing multiple tokens per
chunk produce fewer, larger ITL entries than tokens. Use ITL p99 for jitter,
TPOT for capacity planning. [official]

**E2EL is client-side**, from issue to full response including network and queueing.
`--percentile-metrics` has no literal default: unset, it resolves to `ttft,tpot,itl`
for generative models and `e2el` for pooling models; allowed names are `ttft`,
`tpot`, `itl`, `e2el`. [verified] Reporting emits only selected metrics, so
generative runs silently omit E2EL, the waiting human's latency. Request it:

```
--percentile-metrics ttft,tpot,itl,e2el --metric-percentiles 50,99
```

`--metric-percentiles` defaults to `"99"`; request p50 explicitly. [verified]
E2EL starts when the client *issues* the request, excluding time held in its own
queue by `--max-concurrency`. Capped runs understate user-visible latency by that
wait; account for it or drive open-loop load with a finite `--request-rate`.

Output length is uncontrolled unless `--ignore-eos` is passed; without it the
configured output length is only a ceiling, and generated-token counts and
output-throughput figures are not comparable across configurations. [official]

Tokenizer accounting: the client re-aligns prompts through the server's
`/tokenize` and `/detokenize` endpoints, so input-token counts against a remote
non-vLLM endpoint that lacks them are not trustworthy. [official]

`--probe-request-rate` sends single-token probe requests alongside the main load,
bypassing `--max-concurrency`, and reports their E2EL separately. That is the
direct measurement of head-of-line blocking — how long a heavy load stalls an
unrelated small request. [official]

## Sweeping: where to put the points

A sweep is not mandatory. When it is needed: [official]

1. If the workload names exact concurrency values, run only those.
2. Otherwise use a bounded power-of-two grid — `1,2,4,8,…` — up to a declared
   ceiling. With no safe ceiling, do not invent an unbounded sweep.
3. Include `c=1` only when the goal is to characterise the whole
   latency/throughput frontier, not to pad a user-constrained set.
4. Use non-power-of-two points only for a named reason: the workload demands it,
   a baseline is being reproduced, the tool's search selected it, or you are
   refining around an SLO boundary or an observed knee. Record which.

Request count must reach concurrency to form even one full batch; the practical
floor is `--num-prompts >= 100` except for smoke tests. The measurement window,
not a fixed multiple, sets the upper bound. [official]
Rate and concurrency experiments are **different series**, never one comparison
curve; hold everything except the load variable fixed. [official]

`--ramp-up-strategy linear|exponential` with `--ramp-up-start-rps` /
`--ramp-up-end-rps` climbs within a single run, which draws the load-latency
curve and locates the knee in one pass. [official]

Coarse profiler-free checks: double batch size; if throughput or GPU utilization
does not rise proportionally, suspect host overhead. [official] If concurrent
throughput barely exceeds single-stream throughput, the deployment is
memory-bandwidth-bound, not compute-bound: try smaller quantization before
tuning anything else. [official]

## From an SLO to a capacity number

Pick the objective function first: [official]

- **SLO exists** → optimise **goodput**, the fraction of requests meeting every
  stated SLO simultaneously.
- **SLO does not exist** → keep a Pareto view of throughput, latency and errors.
  Do not collapse it into one scalar.

`--goodput` is declared `nargs="+"`, so it takes **space-separated**
`KEY:VALUE` pairs in milliseconds, and the only valid keys are `ttft`, `tpot`,
`e2el` — `itl` is not accepted. [verified] Comma-separating them is the common
mistake and it does not degrade gracefully: the whole string arrives as one
token and fails to parse.

```
--goodput ttft:500 tpot:50
```

Sweep the rate and find where goodput collapses. That point, not the saturation
throughput, is the capacity number to plan against.

## Comparing configuration families

**Compare families on their own SLO frontiers, never at one shared operating
point.** [official] A topology or configuration family changes *where the
SLO-compliant operating region ends*, and the frontier position is itself the
lever: a family that wins at fixed low concurrency but breaches the SLO earlier
loses to one that sustains higher concurrency. A fixed-operating-point comparison
between families whose frontiers differ is invalid.

After any topology-level change, relocate the frontier — the highest measured
operating point that still passes the SLO — before comparing again. Frontier
relocation happens inside that family's own series and within the declared load
envelope. [official]

Cross-family judgement is a recommendation-level comparison between each family's
best under-SLO result within its own series. It is **not** a cross-series delta
claim. [official]

## Synthetic load versus real load

Load input priority, in strict order: [official]

1. An exact trace supplied by the user.
2. An exact request shape plus traffic control supplied by the user.
3. The closest existing recipe workload, labelled `recipe_proxy`.

A proxy supports exploration, not validation of the user's workload: label results
proxy-derived and document mismatches in limitations. [official] Judge fidelity
on four axes: endpoint/tokenizer/prompt format/streaming behaviour; input/output
length distributions; arrival schedule, rate or concurrency; and **prefix and
cache reuse structure**. [official]

`--random-range-ratio` must be in `[0,1)` and defaults to **0** (zero length
variance). Fixed 512/512 versus production p50 5.9k / p99 11.4k tokens understates
p99 and overstates throughput. A symmetric shape also inverts the prefill:decode
ratio of long-prompt/short-answer traffic, so neither TTFT nor TPOT transfers.
Pass JSON to set input/output variance separately. [official]
The `random` dataset's `--random-prefix-len` (default `0`) prepends fixed tokens:
**total input = `random-prefix-len` + a length sampled from
`[input_len × (1 − range_ratio), …]`**. [verified] This cheaply models a fixed
system prompt without switching datasets. For the hit-rate *curve* instead, use
`prefix_repetition`, which parameterises how many distinct prefixes share the population.

Real-trace datasets: `sharegpt` (multi-turn, naturally prefix-sharing),
`hf`, `burstgpt`, `timed_trace` (real arrival timestamps). Add `--no-oversample`
so a dataset smaller than `--num-prompts` is not repeat-sampled into fabricated
prefix hits, and `--disable-shuffle` when order matters. [official]

When the user has neither a trace nor a matching preset, a **parameterised
description** is a first-class third option: modern tools synthesise ISL/OSL mean
and standard deviation, prefix-reuse structure via a prefix pool, and multi-turn
sessions (session count, turns per session, inter-turn delay) from one command.
[official]

Validate a supplied trace as JSONL and record path, SHA256, line count, timestamp
range, ISL/OSL distribution, and **any line exceeding the served context limit**.
Do not silently filter or truncate lines. [official]

If the user's production shape differs from the unit under test — fleet-wide
traffic numbers against a single-replica deployment — derive the per-unit load
explicitly and confirm it before recording. [official]

## The noise floor

Default to **one measurement run per candidate**, with a window of 30 minutes or
less. GPU benchmarking is expensive; do not repeat runs merely to produce
confidence intervals. [official]

Measure the noise floor instead of assuming it: at a decision point, run an `n=3`
pilot on one configuration, compute run-to-run spread, and derive the minimum
detectable effect (MDE). The pilot is done once per series and amortised across
its candidates. [official]

**Any default percentage — "over 5% counts" — is a placeholder, never a measured
noise floor.** An uncontrolled variable such as prefix-cache residue across runs
can raise the true floor by an order of magnitude. [official]

Screening and categorical outcomes — OOM, error storms, a gross SLO miss — are
valid at `n=1` and need no repetition. [official]

When a delta lands inside the noise band and the decision is adopt/discard, use
**paired repetition**: two arms on different nodes concurrently, or alternating
AB/BA order, analysing the paired differences rather than comparing two means.
[official]

Where intervals exist, separation means `ci_low` > reference `ci_high` when
higher is better, and `ci_high` < reference `ci_low` when lower is better.
Overlapping intervals are `inconclusive`, **not** `noise`; a single run yields a
degenerate `ci_low == ci_high == mean`, which is evidence of nothing. [official]

**An adaptive search across many candidates systematically overestimates the best
observed value.** Give the finalist a fresh confirmation run. [official]

Separate detectability from practical significance: declare the smallest delta
worth caring about, and claim nothing below it however significant it looks.
Absent a user number, default to **2x the measured MDE** and say so. [official]

The A/B protocol that survives drift: alternate A,B,A,B,…, at least three per
arm, and **compare medians, not means** — the mean is dragged by the cold first
run. Share one binary across arms when the difference is a runtime flag;
otherwise rebuild between arms and never during a run. [official]

For a high-cost regression gate, a seeded balanced set of alternating pairs
(half baseline-first, each pair's two calls adjacent) supports an **exact
distribution-free bound on the median ratio** taken from order statistics rather
than a Wald interval; the pass/fail thresholds are on that bound, and you may
**not** adaptively add samples while still claiming the original confidence
level. [official] It rests on an arguable exchangeability assumption that pair
adjacency alone does not establish, so declare serial-dependence diagnostics up
front and report inconclusive when they trip. [official]

**Never drop an observation for looking like an outlier.** A product failure —
an error, a failed assertion, malformed timing — fails that row rather than
becoming a discardable sample. Only pre-declared environmental conditions
(scheduler eviction, node health failure, affinity violation, independently
detected competing load) invalidate a sample, and then both members of the pair
are invalidated and re-run in the same arm order. [official]

## What makes two runs comparable

**Cache state.** For reuse-heavy workloads, reset the cache between points and use
cold, identical inputs while *ranking* candidates; then confirm the finalist in
**hot steady state** before quoting absolute numbers. A short cold-start window
measures the cold-to-hot transient, not production. [official]

**Neighbour occupancy.** Record every measurement's co-located work and compare
only like occupancy; idle-neighbour results cannot extrapolate to a full node or
cluster without co-located confirmation. [official] Occupancy is a *recorded
condition, not an admission gate*: exclusive nodes may not exist on shared
clusters, so real-occupancy noise sets the decision floor. Invalidate a mid-run
neighbour change only if the run's time series shows a matching performance step;
otherwise record it and keep the run, avoiding a rule no run can satisfy. [official]

**Tool version.** Same or patch-different versions are comparable if recorded.
A **minor** difference requires release notes proving no measurement-relevant
change or a **bridging run**: re-measure the best prior configuration on the new
version and confirm its delta is inside the series noise floor. Major differences,
measurement-affecting changes, or bridging deltas outside that floor exclude the
mismatched run from all comparisons. [official] A shared series ID is insufficient:
reused or hand-edited series can mix versions; check each recorded runtime version.

**Everything else.** Results are comparable only when model, quantization, prompt
length, output length, power mode, clocks and thermal state are all controlled,
and quantization formats never share a table without an explicit `quant` column.
[official] Pin the image by digest rather than a floating tag, or cross-time
comparison is meaningless.

CPU affinity is a measurement variable, not folklore: pinning the process to the
GPU's NUMA node changes host overhead by up to **2x** on a multi-socket machine.
Fix it and record it. [official]

## The client is a common false bottleneck

A load generator tokenises every prompt and manages many processes' streams;
CPU competition can masquerade as server collapse. Read server-process CPU with
`pidstat` and client cores with `mpstat`: **pegged client cores with low server
CPU identify a client bottleneck.** [official] Two operational traps:

- The aggregating finaliser can hang on large runs (stuck at "processing
  records…") while the **per-request JSONL is written incrementally**. Recompute
  throughput from the raw JSONL rather than waiting for the aggregate. Prefer a
  duration-based window over an enormous fixed request count. [official]
- Orphaned client processes hold ZMQ/mmap resources and wedge the next run.
  Killing the parent leaves them; if the previous capture ran under sudo, a
  non-root `pkill` will not reap them. [official]

## Audit a result before explaining it

A finished job needs a separate validity verdict: `valid`, `valid_with_recovery`,
or `invalid`. [official] Before interpreting it:

- Separate warmup and profiling records, excluding only what the plan says to.
- Reconcile attempted / successful / failed / cancelled / timed-out counts.
- Compare the **measured** ISL/OSL distribution against the intended load and
  report output-length shortfall.
- Check timestamps, schedule coverage, duplicate or missing request ids,
  malformed metrics, NaN/inf, units, and impossible negative latencies.

Re-run invalid-but-fixable runs in the same series without overwriting original
artefacts: **invalid runs are failure evidence, never discarded**.
**Never make a failing benchmark complete** by reducing request count, dropping
hard trace lines, relaxing the SLO, lowering load, switching schedule mode, or
changing ISL/OSL: each changes the benchmark plan and comparison series. [official]

Report `(current - prior) / prior * 100` with both the direction and whether it
is an improvement; a bare signed percentage gets misread. [official]

**The attribution boundary.** Client-side data establishes only client-visible
behaviour, not router, scheduler, transport or backend root causes. It cannot prove
per-role queueing, runtime admission, KV transfer engagement, cache pressure, or
CUDA-graph coverage. Report these as evidence-unavailable; internal mechanisms
remain hypotheses without independent runtime evidence. [official]

Throughput is ground truth; function-level profiler gains are leading indicators,
not wins unless throughput moves. [official] Optimisations interact: removing a
50 ms bottleneck exposes the hidden 30 ms one; re-profile after every change. [official]

Two traps invalidate a capture outright: repeated prompts are short-circuited by
the prefix cache, so anything measuring prefill needs mutually distinct probe
prompts; and a capture taken while the service was idle answers no latency or
queueing question at all — re-capture under load. [official]

<!-- sources: dynamo, trtllm, vllm-skills, vllm-docs, sglang, amd-skills, nvidia-skills -->
