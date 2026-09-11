# OOM and throughput triage

## Contents

- [OOM: the fixed order](#oom-the-fixed-order)
- [Reading the allocator message](#reading-the-allocator-message)
- [Fragmentation first](#fragmentation-first)
- [OOM at step 200 but not step 1](#oom-at-step-200-but-not-step-1)
- [Throughput: measure before tuning](#throughput-measure-before-tuning)
- [The usual throughput thieves](#the-usual-throughput-thieves)
- [What not to do](#what-not-to-do)

## OOM: the fixed order

Work down this list. The order is by cost — each step is cheaper in
throughput than the one after it — and skipping to step 6 is how runs end up
28% slower for a 3 GB saving.

1. **Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.** Zero
   throughput cost. Fixes fragmentation-induced OOM, which is a large share
   of borderline cases. [official]
2. **Run the ledger** (`scripts/vram_ledger.py`) and find the dominant term.
   Everything below depends on knowing which of the four it is.
3. **Cut the micro-batch, raise `gradient_accumulation_steps` to compensate.**
   Free in memory terms, mildly negative for throughput, keeps the effective
   batch — and therefore the learning dynamics — unchanged.
4. **Cut `max_length` to what the data actually needs.** Check the p99 length
   first; truncating real answers is not a memory fix, it is a data defect.
5. **Enable gradient checkpointing.** Large activation saving, roughly 30%
   slower step. In transformers 5, `every_n_layers=2` buys back half the
   speed for half the saving.
6. **Switch to LoRA or an 8-bit optimizer** if the optimizer term dominates.
7. **Shard: ZeRO-1, then ZeRO-2, then ZeRO-3/FSDP.** Only helps model state.
8. **Tensor or pipeline parallel.** Last, and only within the topology: tensor
   parallelism stays inside one NVLink domain, pipeline parallelism crosses nodes.

Between step 5 and step 6, re-run the ledger. Half the time the dominant term
has changed, and continuing down the list would attack the wrong one.

## Reading the allocator message

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB.
GPU 0 has a total capacity of 79.15 GiB of which 1.21 GiB is free.
Process ... has 77.94 GiB memory in use. Of the allocated memory
70.11 GiB is allocated by PyTorch, and 5.94 GiB is reserved by PyTorch
but unallocated.
```

Three numbers matter:

- **allocated** — the ledger's four terms. Compare against your estimate; a
  large gap means the estimate is wrong, not the GPU.
- **reserved but unallocated** — fragmentation. When this is multiple GB,
  step 1 above is the whole fix.
- **tried to allocate** — the size tells you the term. A few hundred MB is
  usually an activation or a logits tensor; tens of GB is model state.

An OOM that names a `logits` tensor of `batch x seq x vocab` is the loss
computation, not the model: reduce the eval batch, or use a chunked/fused
cross-entropy.

## Fragmentation first

The signature is an OOM with free memory on the card, or an OOM on one rank
while its peers have headroom. NVIDIA's measured case: a Llama3-70B SFT run
OOMing at 58.8 GB peak on 80 GB cards, "fixed" by parallelism changes that
cost 6-28% throughput, when the actual cause was fragmentation and
`expandable_segments:True` resolved it at no cost. The same investigation
had earlier misattributed the fix to a virtual-pipeline setting that in fact
used *more* peak memory. [official]

Two incompatibilities to know before setting it: expandable segments conflict
with NCCL user-buffer registration (`--use-nccl-ub`), and with CUDA graphs on
pre-Blackwell GPUs they require `NCCL_GRAPH_REGISTER=0`. [official]

## OOM at step 200 but not step 1

The run got through the hard part, so the cause is something that grows or
something periodic:

| Timing | Cause |
|---|---|
| At the first `eval_steps` boundary | the eval pass has its own peak; `per_device_eval_batch_size` is usually left at the training value |
| At the first `save_steps` boundary | checkpoint serialisation gathers state; with ZeRO-3/FSDP a full state dict is assembled |
| Exactly at a length percentile | a longer batch arrived; length-sorted or length-grouped batching hides this until it does not |
| Slow creep across hundreds of steps | something retaining graph references — a metric accumulated as a tensor instead of a float is the classic |
| At the first generation step (GRPO) | the sampling engine allocates its own KV cache on the same device |

## Throughput: measure before tuning

Get one number before changing anything: **tokens per second per GPU**, and
if you can, model FLOPs utilisation. Without it, every change is a guess and
"it feels faster" is the report.

Then find out whether the GPU is even busy. If utilisation sits at 40%, no
kernel-level optimisation will help — the bottleneck is upstream.

## The usual throughput thieves

| Symptom | Cause | Fix |
|---|---|---|
| GPU utilisation low and spiky | dataloader starvation | raise `dataloader_num_workers`, pre-tokenise, cache to disk |
| Step time proportional to the longest sequence in the batch | padding waste | packing, padding-free batching, or length grouping |
| Everything slower than a comparable published run | eager attention instead of a fused kernel | check the attention implementation actually in use |
| Multi-GPU barely faster than single | communication not overlapped, or TP across nodes | check the topology before the code |
| Step time fine, epoch time terrible | per-epoch re-tokenisation or a shuffle buffer on slow storage | cache the tokenised dataset |
| Regression after a config change with no memory change | recompute or offload silently enabled | diff the effective config, not the intent |

Note the ordering: dataloader and padding come before anything involving
parallelism. They are the majority of real cases and the cheapest to fix.

## What not to do

- Do not raise TP to fix memory. It is the most expensive memory fix
  available, measured at -28% throughput for a 3 GB saving. [official]
- Do not raise PP at the cost of DP without recomputing the gradient
  accumulation steps; halving DP doubles them and costs about 6%. [official]
- Do not enable CPU offload with PP > 1; it raises
  `ValueError: Currently there is no support for Pipeline parallelism with
  CPU offloading`. [official]
- Do not change two things at once. A config where three knobs moved and
  throughput dropped 20% cannot be bisected afterwards.

<!-- sources: nvidia-skills, pytorch-docs, hf-skills, trl-docs -->
