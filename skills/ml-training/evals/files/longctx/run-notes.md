# Contract-review LoRA — run notes

## Box

- 1x H100 80GB SXM, single node, no other jobs on the GPU.
- Requirements pinned as in the script header (trl 1.17.1).

## What we measured (first 50 optimizer steps, packed 32k sequences)

| Config | Peak allocated | Peak reserved | Step time (one optimizer step = 16 micro-batches) |
|---|---|---|---|
| As committed (`gradient_checkpointing=True`) | 38.9 GB | 41.2 GB | 61 s |
| `gradient_checkpointing=False` | OOM at micro-batch 1 (tried to allocate 21.4 GiB with 74.6 GiB in use) | — | — |

`torch.profiler` on one micro-batch with checkpointing on: about 31% of the
backward pass is the recomputed forward, and most of that recompute is the
FlashAttention forward kernel (at 32k tokens attention dominates the layer).

## Ask

Training is correct, just slow: 2 epochs is ~4.5 days at this rate and we have
the GPU for 3. Turning checkpointing off does not fit. We would rather not
shorten `max_length` (the p50 transcript is 27k tokens) or change the effective
batch of 16. How do we get the speed back?
