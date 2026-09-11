# Distributed training: picking the parallelism

Verified against: torch 2.14.0 (FSDP2 `fully_shard`), DeepSpeed ZeRO stages 1-3.

## Contents

- [The ladder](#the-ladder)
- [What each axis costs on the wire](#what-each-axis-costs-on-the-wire)
- [ZeRO stages and what they shard](#zero-stages-and-what-they-shard)
- [FSDP2 contract](#fsdp2-contract)
- [Sizing by model and topology](#sizing-by-model-and-topology)
- [Counting GPUs correctly](#counting-gpus-correctly)
- [Gradient accumulation and effective batch](#gradient-accumulation-and-effective-batch)
- [Failure signatures](#failure-signatures)

## The ladder

Climb in this order, and only when the rung below has run out:

1. **One GPU.** Gradient checkpointing, LoRA, a smaller micro-batch.
2. **DDP** — full replica per GPU, gradients all-reduced. Simplest, fastest
   per step, needs the whole model state to fit on one card.
3. **ZeRO-1/2 or FSDP with optimizer/gradient sharding** — same programming
   model as DDP, model state divided by the data-parallel world size.
4. **ZeRO-3 / FSDP full shard** — parameters sharded too, gathered
   just-in-time per layer. Adds an all-gather to every forward and backward.
5. **Tensor parallel** — one layer's matmuls split across GPUs. An all-reduce
   inside every block. NVLink-domain only.
6. **Pipeline parallel** — layers split across GPUs, micro-batches in flight.
   Cheap on the wire, expensive in bubbles.
7. **Context/sequence parallel** — for sequences that no other axis fits.

Each rung buys memory and costs either communication or utilisation. Skipping
rungs is the most common source of a 3x slowdown nobody can explain.

## What each axis costs on the wire

| Axis | Communication per step | Where it must live |
|---|---|---|
| DDP | one gradient all-reduce, overlappable with backward | anywhere |
| ZeRO-1 | all-reduce + optimizer-state gather at step | anywhere |
| ZeRO-2 | reduce-scatter of gradients | anywhere |
| ZeRO-3 / FSDP | parameter all-gather per layer, twice per step | fast interconnect |
| Tensor parallel | 2 all-reduces per transformer block | inside one NVLink domain |
| Pipeline parallel | point-to-point activations at stage boundaries | fine across nodes |
| Expert parallel | all-to-all of routed tokens | MoE only |

The rule that survives contact with real clusters: **keep tensor parallel
inside a single NVLink domain and use pipeline or data parallel to cross
nodes.** TP across nodes is almost always a net loss. [official]

Doubling TP as an OOM fix is a trap: NVIDIA's measured Llama3-70B SFT run
lost **28%** throughput going from TP=4 to TP=8, against a **3 GB** memory
saving, while simply enabling `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
fixed the same OOM at zero cost. [official]

## ZeRO stages and what they shard

| Stage | Optimizer state | Gradients | Parameters |
|---|---|---|---|
| 1 | sharded | replicated | replicated |
| 2 | sharded | sharded | replicated |
| 3 | sharded | sharded | sharded |

Stage 1 is nearly free and should be the default for anything above ~1B
parameters: the optimizer term is the largest part of model state, and
sharding it across the DP group costs one extra collective at step time.
Stage 3 pays an all-gather per layer per pass; on a cluster without
InfiniBand or NVLink between nodes it can be slower than not training at all.

CPU and NVMe offload (ZeRO-Infinity) trade device memory for PCIe bandwidth.
Use it to make a run *possible*, never to make it faster. [official]

## FSDP2 contract

PyTorch's current API is `torch.distributed.fsdp.fully_shard`, which shards
per-parameter as DTensors. Five rules the API assumes and does not enforce:

- Launch with `torchrun` and set the device from `LOCAL_RANK` before anything
  touches CUDA.
- Apply `fully_shard()` **bottom-up** — transformer blocks first, the root
  module last. Sharding only the root gives worse overlap and a higher peak,
  and it looks like it worked.
- Call `model(x)`, never `model.forward(x)`: the hooks that unshard
  parameters hang off `__call__`.
- Build the optimizer **after** sharding, so it holds DTensor parameters.
- Save with Distributed Checkpoint (`torch.distributed.checkpoint`) or the
  distributed state-dict helpers. A plain `torch.save(model.state_dict())`
  over DTensors produces a file that will not load anywhere else.

For gradient accumulation use `set_requires_gradient_sync(False)` on the
accumulating steps; FSDP1's `no_sync()` context manager does not exist in
FSDP2. [official]

## Sizing by model and topology

Starting points for dense models, to be profiled on iteration one, not
trusted: [official]

| Parameters | GPUs | Start with |
|---|---|---|
| <1B | 1-8 | DP only |
| 1-10B | 8-16 | TP 2-4 + DP |
| 10-70B | 16-64 | TP 4-8 + PP 2-4 + DP |
| 70-175B | 64-256 | TP 8 + PP 4-8 + DP |

By sequence length: add sequence parallel above ~2k tokens (requires TP>1),
context parallel above ~8k, and CP 4-8 above 32k. Context parallel requires
`seq_length % (2 * CP) == 0`. [official]

MoE inverts the intuition: TP is sized by **active** parameters, not total,
so a 671B model with 37B active needs *less* TP than a 70B dense model, and
expert parallel becomes the main axis. [official]

## Counting GPUs correctly

The minimum GPU count for a combined config is **not** the product of every
dimension:

```
min_gpus = PP * max(TP * CP, EP * ETP)
```

The dense `TP x CP` mesh and the MoE `EP x ETP` mesh share the same GPUs
inside each pipeline stage — they overlap rather than multiply. Only pipeline
stages multiply. The common `PP * TP * CP * EP * ETP` formula over-allocates
hardware and appears in many sizing tables; do not propagate it. [official]

Data-parallel size is implicit and must be consistent on both paths:

```
data_parallel_size        = world_size / (TP * PP * CP)
expert_data_parallel_size = world_size / (PP * EP * ETP)
```

## Gradient accumulation and effective batch

```
effective_batch = per_device_batch * gradient_accumulation_steps * world_size
```

Changing the world size therefore changes the effective batch and silently
changes the learning dynamics. When you scale from 1 GPU to 8 and keep every
other number, you have octupled the batch — the run that converged before now
underfits at the same learning rate and epoch count. Fix the effective batch
first, then derive `gradient_accumulation_steps` from the device count.

One subtlety that produces a real, small, mysterious quality difference:
transformers 5 defaults `average_tokens_across_devices=True`, so token-level
losses are averaged over the global token count rather than per device.
[verified] Comparing a run from transformers 4.x against one from 5.x with
identical hyperparameters compares two different loss normalisations.

## Failure signatures

| Symptom | Cause | Check |
|---|---|---|
| OOM on one rank, headroom on the others | fragmentation | is `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` set |
| Step time doubles going multi-node | TP crossed the node boundary | `TP <= GPUs per node` |
| Throughput drops after raising PP | DP fell, accumulation steps rose | recompute the effective batch |
| Loss differs between 1-GPU and N-GPU runs | effective batch changed, or loss normalisation | recompute; compare per-token loss |
| Hang at the first collective, no error | mismatched world size or a rank that died during model load | check every rank's log, not rank 0's |
| `ValueError: no support for Pipeline parallelism with CPU offloading` | CPU offload requires PP=1 | disable one of them |

Expandable segments is incompatible with NCCL user-buffer registration
(`--use-nccl-ub`), and with CUDA graphs on pre-Blackwell GPUs it requires
`NCCL_GRAPH_REGISTER=0`. [official]

<!-- sources: nvidia-skills, orchestra-ai-research, deepspeed-docs, pytorch-docs -->
