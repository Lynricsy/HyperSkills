# Parallelism and topology for inference

Verified against: TensorRT-LLM `docs/source/features/parallel-strategy.md`,
`attention.md`, `feature-combination-matrix.html`.

## Contents

- [A topology decides four things, only one of which is memory](#a-topology-decides-four-things-only-one-of-which-is-memory)
- [DP versus TP: the inference-side criterion](#dp-versus-tp-the-inference-side-criterion)
- [What TP does to attention heads and KV](#what-tp-does-to-attention-heads-and-kv)
- [Sizing arithmetic](#sizing-arithmetic)
- [Attention-DP and ragged padding](#attention-dp-and-ragged-padding)
- [MoE: EP, ETP, and hot experts](#moe-ep-etp-and-hot-experts)
- [The evaluation order](#the-evaluation-order)
- [Communication as the bottleneck](#communication-as-the-bottleneck)
- [Verifying the interconnect](#verifying-the-interconnect)
- [Feature combinations that do not exist](#feature-combinations-that-do-not-exist)
- [Controls that reverse direction with load](#controls-that-reverse-direction-with-load)

## A topology decides four things, only one of which is memory

Choosing a parallel layout simultaneously fixes: [official]

1. **Effective per-rank batch and arithmetic intensity** — the throughput axis.
2. **Weight and KV memory footprint** — the fits-at-all axis.
3. **Collective pattern and volume** — TP does all-reduce, EP does all-to-all, DP
   does neither.
4. **Whether attention and weights are replicated or sharded.**

**Never judge a topology change on memory alone.** When memory is not the binding
constraint the topology question is not closed; it has moved to compute and
communication.

Fitting is a constraint, not a goal. An inherited layout is a *candidate*, not a
settled decision — rank candidates cheaply first (sizing arithmetic,
extrapolation, a published recipe for the same model) before spending a
deployment on one. Revisit the topology after baseline characterisation and
whenever the measured limiting regime changes. [official]

A sibling recipe for the same model on *different* hardware is a hypothesis prior,
not adoption evidence: even when its checkpoint or hardware is incompatible, its
parallelism dimensions and serving-mode choice still transfer as candidates.
[official]

A topology change usually moves several config fields at once. Treat it as one
functionality-required mechanism, record every changed field including the GPU
resource delta, and still obey one-variable discipline. **Do not change topology
because a lower-level knob failed, or because the cluster happens to have idle
capacity.** [official]

Changing `replicas` changes the resource budget — results from it must not be
attributed to per-GPU efficiency. Changing node placement (nodeSelector,
affinity, tolerations, pack domain) can change *node quality*, invalidating the
node-equivalence assumption; separate a placement gain from a node-quality
difference. [official]

## DP versus TP: the inference-side criterion

This is where inference diverges from training, and the reason is per-rank batch:
[official]

- **Data parallel** makes each replica serve `batch/N`, which **shrinks per-rank
  batch and starves the compute** — even when everything fits comfortably.
- **Tensor parallel** runs the whole batch through one sharded forward, which
  **raises per-rank batch and frees memory, paid for in collectives.**

Among all layouts that fit with operating headroom, prefer the one that
**maximises effective per-rank batch and compute efficiency at the target
concurrency**, then weigh its communication cost.

The engine-level framing of the same trade-off: TP for attention suits small
batch or memory-constrained serving; DP suits large batch and high throughput.
Under DP all GEMM weights are **replicated** per card while the KV cache is
**partitioned**, because different requests route to different DP ranks.
[official]

## What TP does to attention heads and KV

TP shards attention `num_heads` and the surrounding GEMM weights evenly, so **TP
size must divide the head count.** [official]

The trap: when `num_heads < tensor_parallel_size` — routine with GQA, MQA and MLA
— the KV cache is **no longer sharded but replicated in full on every card**. Any
memory estimate that still divides KV by TP is wrong, and wrong in the direction
that OOMs at start-up. [official]

## Sizing arithmetic

Per-token KV size: [official]

```
GQA:  2 × num_attention_layers × (num_key_value_heads / TP) × head_dim × dtype_bytes
MLA:      num_attention_layers × (kv_lora_rank + qk_rope_head_dim) × dtype_bytes
```

MLA carries no TP divisor. With attention-DP enabled, use a divisor of 1 for GQA
because KV is replicated per rank.

Concurrency ceiling: [official]

```
max_requests ≈ floor( (GPU_HBM × 0.90 − model_weights_bytes / TP)
                      / (kv_per_token × (ISL + OSL)) )
```

The `0.90` reserves roughly 10% for CUDA context, driver and runtime. This is an
**upper bound only** — it ignores activation memory, CUDA-graph workspace, MoE
expert workspace and attention-DP overhead.

A cross-vendor budget check that catches the common start-up failure: [official]

```
remaining_for_kv = VRAM − weights − ~4 GB runtime overhead
```

The overhead covers activation profiling, graph capture and internal buffers, and
the start-up peak exceeds steady state. `≥6 GB` remaining is safe; `2-6 GB` is
worth trying, and if the log OOMs *after* "capturing CUDA/HIP graphs" then eager
mode reclaims 1-2 GB at the cost of slightly higher decode latency; **below 2 GB
it will OOM during activation profiling — do not start it.**

## Attention-DP and ragged padding

Attention-DP's memory cost scales with attention type: small for MLA's compressed
KV, large for GQA's full replication. Lower the KV memory fraction when enabling
it; MoE combined with attention-DP is the configuration most prone to OOM.
[official]

The performance failure mode is padding. When per-rank token counts are uneven,
the framework pads every rank to the maximum, wasting attention/MoE compute and
host bookkeeping on dummy tokens. Signals: low MFU, throughput scaling
sub-proportionally with DP degree, and dummy-token computation visible in a
profile. The fix is length-aware (variable-length) allgather/reducescatter rather
than pad-to-max. [official]

## MoE: EP, ETP, and hot experts

Three execution shapes: [official]

| Shape | Weights | Tokens per card |
|---|---|---|
| TP | each expert sliced | all tokens |
| EP | whole expert on one card | only tokens routed to local experts |
| Hybrid ETP | sliced across a subgroup | subgroup's routed tokens |

The constraint is `moe_tensor_parallel_size × moe_expert_parallel_size ==
tensor_parallel_size`, and EP size need not equal TP size. [official]

EP's intrinsic problem is expert load imbalance — hot experts. The engineering
answer is decoupling experts from slots and placing replicas of hot experts across
cards: offline rebalancing for known traffic, online for drifting traffic, with
the periodic weight movement kept off the critical stream or the rebalance itself
introduces bubbles. [official]

When swapping the EP all-to-all for a specialised communication library, check
CUDA-graph compatibility: the high-throughput variant is typically not
capturable, so the decode path must select the low-latency (graph-safe) variant or
capture fails and the whole segment falls back to eager. [official]

For quantized models, quantizing activations **before** the collective and
shipping them (FP8 ≈ ½ the bytes, FP4 ≈ ¼) with scale factors packed alongside is
a real win, but it is **lossy** — it needs an accuracy record and a rollback
criterion before being called optimal. [official]

No AllReduce algorithm wins at every message size; select on
`(SM architecture, TP size, fused epilogue or not, hidden size, token count)` via
an offline lookup table or runtime autotune. Pinning one algorithm guarantees a
regression at some shape. [official]

## The evaluation order

Fixed order, because each step changes what the next one is allowed to consider:
[official]

1. Compute model/activation/KV memory fit; establish the **minimum viable** TP,
   PP, EP.
2. Compute **effective per-rank batch** at the target concurrency.
3. Among layouts that fit with headroom, rank by per-rank batch and compute
   efficiency, then weigh communication.
4. Spend leftover cards in a fixed GPU budget on **more replicas**, when the load
   can absorb them.
5. Consider aggregated versus disaggregated only when load shape, scale, or
   independent prefill/decode targets justify the transfer and coordination cost.
6. For an existing disaggregated deployment, check the P/D ratio and rate
   matching **before** adding workers.
7. When the chosen topology spans GPUs or nodes, verify node placement and the
   required fast fabric.

Three numbers must agree: the container's GPU request, the node count, and the
engine-side parallel shape. When they disagree the deployment still starts — with
a parallel shape that is not the one you intended. [official]

## Communication as the bottleneck

Compute the collective share of step time before attributing anything to host
overhead: [official]

```
nccl_ratio = nccl_kernel_us / gpu_active_us
```

Above `0.20`, GPU idle cannot be attributed to the host, and the conclusion must
carry a communication caveat.

Cross-rank straggler detection: per-step wall time differing across ranks usually
means one rank runs extra coordinator-only host code, or queue depth has formed a
feedback loop. Compare kernel summaries and per-step host breakdowns **across
ranks**, not on rank 0 alone. [official]

## Verifying the interconnect

**A deployment can pass an endpoint smoke test while disaggregation is silently
broken.** If the transport cannot reach the peer worker over RDMA or NVLink, KV
transfer falls back to a slow path or fails outright. Validate the fabric
read-only before trusting any disaggregated number. [official]

Transport variables and how they fail: [official]

| Variable | Purpose | Failure when wrong |
|---|---|---|
| `UCX_TLS` | permitted transports; needs `rc`/IB plus `cuda_ipc`/`cuda_copy` | resolving to `tcp` only makes KV transfer crawl |
| `UCX_NET_DEVICES` | pins UCX to a specific HCA/port (`mlx5_0:1`) | unset or wrong falls back to the management NIC |
| `UCX_IB_GPU_DIRECT_RDMA` | lets the NIC DMA into/out of device memory | staged copies through host memory |
| `UCX_RNDV_SCHEME` / `UCX_RNDV_THRESH` | rendezvous for large messages | large-transfer inefficiency |
| `NCCL_IB_HCA` | usable HCA list | wrong device selected |
| `NCCL_SOCKET_IFNAME` | bootstrap/rendezvous NIC | a wrong guess hangs init outright |
| `NCCL_IB_DISABLE` | must be `0`/unset to use IB | `1` forces sockets |
| `NCCL_IB_GID_INDEX` | needed for RoCE/EFA, not classic IB | connection failures |

`NCCL_DEBUG=INFO` prints the transport NCCL actually selected — the only way to
verify that configured equals effective. [official]

Read-only capability checks and what each proves: [official]

- `/dev/infiniband` plus `ibv_devinfo -l` — RDMA devices exposed into the pod.
  Empty means no RDMA, usually a missing device plugin or an unrequested
  resource.
- `ibstat` showing `State: Active` / `LinkUp` — `Down`/`Polling` is cabling, the
  subnet manager, or the fabric.
- `nvidia_peermem` loaded — GPUDirect RDMA kernel support. **Without it, RDMA is
  staged through host memory.**
- `/dev/gdrdrv` — GDRCopy, for low-latency small transfers.
- `nvidia-smi topo -m`: `NV#` rows are NVLink between GPUs; `PIX`/`PXB` rows show
  GPU-to-NIC affinity, and that affinity should agree with the
  `UCX_NET_DEVICES` / `NCCL_IB_HCA` selection.

**Capability present does not mean two workers can talk.** Run a pairwise
transfer test between the prefill and decode pods — RDMA path across nodes,
NVLink path on one node. A `skipped` result from a missing tool is *unknown*, not
pass. [official]

Checking the recipe text for environment variables is insufficient: they may be
baked into the image or injected at runtime by an operator or init container, so
"not in the recipe" is a warning and the real check is the environment inside the
pod. A single-node aggregated deployment never exercises the transport, so this
validation only applies to disaggregated or multi-node setups. [official]

## Feature combinations that do not exist

Check the target deployment's **feature-by-feature** combination, not a
per-feature checklist. Known incompatibilities in one engine's matrix:
[official]

- Speculative decoding × Pipeline Parallelism = **No** (all three of linear,
  dynamic-tree and NGram paths). A deployment needing speculative decoding cannot
  choose PP.
- PP × chunked prefill = **Untested**.
- Logits post-processor × disaggregated serving = **No**.
- LoRA × EP / attention-DP / disaggregated serving = **Untested** — multi-LoRA
  together with large-scale parallelism or P/D separation is unvalidated
  territory.

Multi-node recipes carry a reading trap: `gpu_count` in a multi-node response is
**per node**, so total demand is `node_count × gpu_count`. A missing flat field
is a schema branch, not a missing recipe. [official]

## Controls that reverse direction with load

Several high-impact controls change sign as concurrency rises, which is why a
single-operating-point measurement misleads: [official]

- **Speculative decoding** — strongest on low-concurrency decode latency,
  neutral to harmful on high-concurrency throughput.
- **Prefix caching** — needs genuinely repeated prefixes; beneficial at low load,
  while at high load its bookkeeping overhead can reduce throughput.
- **Autotuner results** — depend on TP, concurrency, engine version and the
  active collective path.
- **CUDA graph capture** — must cover the peak engine batch shape observed at
  *every* target operating point, not just one.

<!-- sources: trtllm, dynamo, amd-skills -->
