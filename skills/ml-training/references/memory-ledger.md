# The memory ledger

Verified against: torch 2.14.0, transformers 5.17.0, trl 1.13.0, peft 0.20.0.

## Contents

- [Four terms, four remedies](#four-terms-four-remedies)
- [Bytes per parameter](#bytes-per-parameter)
- [What mixed precision actually costs](#what-mixed-precision-actually-costs)
- [The activation term](#the-activation-term)
- [What each remedy moves](#what-each-remedy-moves)
- [Worked ledgers](#worked-ledgers)
- [Why the estimate is always low](#why-the-estimate-is-always-low)

## Four terms, four remedies

Peak device memory during a training step is four independent terms:

```
weights + gradients + optimizer state + activations
```

They are independent in the sense that matters: no single knob shrinks more
than two of them. Answering "we are out of memory" without first saying which
term dominates produces the classic wasted afternoon — halving the batch size
on a run whose optimizer state alone exceeds the card.

`scripts/vram_ledger.py` prints the split and names the dominant term.

## Bytes per parameter

Per **trainable** parameter, for the common bf16-compute / fp32-optimizer setup:

| Term | Bytes | Note |
|---|---|---|
| Weight (bf16/fp16) | 2 | 4 if training in pure fp32, 1 under 8-bit, ~0.5 under NF4 |
| Gradient | 2 | matches compute precision; only trainable parameters have one |
| Adam `exp_avg` | 4 | fp32 |
| Adam `exp_avg_sq` | 4 | fp32 |
| fp32 master weight | 4 | the copy the optimizer updates |

[verified] `torch.optim.AdamW` state measured at **8.000005 bytes per
parameter** on a 58,073,600-parameter Llama after one `step()` — two fp32
moments (`exp_avg`, `exp_avg_sq`) plus a scalar `step` per parameter tensor.
There is no hidden third moment and no per-parameter overhead worth modelling.

So a full fine-tune costs roughly **16 bytes per parameter of model state**
before a single activation is stored, and about 18 with the fp32 master copy.
For an 8B model that is ~119 GiB — which is why full fine-tuning an 8B model
on one 80 GB card is arithmetically impossible, not merely tight, and why no
batch size or sequence length rescues it.

SGD with momentum is 4 bytes of state per parameter, plain SGD is 0. They are
rarely worth it for LLM fine-tuning: the learning-rate schedule that makes
them converge costs more wall-clock than the memory saves.

## What mixed precision actually costs

`bf16=True` does not halve training memory. It halves the *weight* and
*gradient* terms and leaves the optimizer term alone, because the optimizer
still keeps fp32 moments and an fp32 master copy of each trainable weight.
Expect roughly a 25-30% reduction in model state, not 50%. [official]

bf16 over fp16 for anything above toy scale: bf16 has fp32's exponent range,
so it does not need loss scaling and does not produce the fp16 overflow-to-inf
failure that shows up as a loss that goes NaN in the middle of a long run.
fp16 remains the only option on pre-Ampere hardware. [official]

## The activation term

Activations are what the backward pass needs and the forward pass saved. They
scale with `micro_batch x sequence_length x hidden x layers` — note
`micro_batch`, not effective batch. Gradient accumulation multiplies the
effective batch without touching this term, which is precisely why it is the
first lever when activations dominate.

Two consequences people get wrong:

- **Sequence length is linear here, not quadratic** — with FlashAttention or
  any fused attention kernel the `seq^2` score matrix is never materialised.
  A run that OOMs at 8192 tokens and survives at 4096 is telling you about the
  linear term; if it behaves quadratically, the attention implementation fell
  back to the eager path.
- **Evaluation has its own peak.** An eval pass with the same
  `per_device_eval_batch_size` as training holds activations without needing
  gradients, but the logits tensor over a 128k-token vocabulary at long
  sequence lengths is itself gigabytes. An OOM that only happens at the first
  `eval_steps` boundary is this, not a training-loop problem.

## What each remedy moves

| Remedy | Weights | Grads | Optimizer | Activations |
|---|---|---|---|---|
| LoRA / QLoRA | — (frozen, still resident) | ~0 | ~0 | small drop |
| Gradient checkpointing | — | — | — | large drop, ~30% slower step |
| 8-bit optimizer | — | — | halves moments | — |
| ZeRO-1 / FSDP optimizer shard | — | — | / DP | — |
| ZeRO-2 | — | / DP | / DP | — |
| ZeRO-3 / FSDP full shard | / DP | / DP | / DP | — |
| Tensor parallel | / TP | / TP | / TP | / TP |
| Pipeline parallel | / PP | / PP | / PP | / PP (per stage) |
| Smaller micro-batch | — | — | — | linear drop |
| Activation offload to host | — | — | — | large drop, PCIe-bound |

The two rows that surprise people:

- **LoRA does not shrink the weights.** The base model stays resident in full;
  only gradients and optimizer state collapse to the adapter's size. A 70B
  model in bf16 still needs 140 GB of weights under LoRA. QLoRA attacks that
  term separately by keeping the frozen base in 4-bit.
- **Sharding does not shrink activations.** ZeRO and FSDP partition model
  state across the data-parallel group; each rank still computes its own
  micro-batch and stores its own activations. A run whose dominant term is
  activations gets no relief from going to more GPUs with ZeRO-3.

[verified] LoRA `r=16` on `q_proj`/`v_proj` of a 58.07M-parameter Llama leaves
262,144 trainable parameters — 0.45% — so the AdamW state drops from 464 MB to
2.1 MB. The ratio, not the absolute size, is the point: it holds at any scale.

## Worked ledgers

8B parameters, 32 layers, hidden 4096, bf16, AdamW, one GPU, computed by
`scripts/vram_ledger.py`:

| Configuration | Weights | Grads | Optim | Activations | Lower bound |
|---|---|---|---|---|---|
| Full FT, micro-batch 8, seq 8192 | 14.9 | 14.9 | 89.4 | 272.0 | 391 GiB |
| Full FT, micro-batch 1, seq 4096, checkpointing | 14.9 | 14.9 | 89.4 | 1.5 | 121 GiB |
| LoRA 0.5%, micro-batch 1, seq 8192, checkpointing | 14.9 | 0.07 | 0.45 | 3.1 | 18 GiB |

Read the middle row: even with the activation term driven to nothing, full
fine-tuning still needs 121 GiB. The first configuration's problem is not the
batch size, and the second configuration's problem is not solvable by tuning.

## Why the estimate is always low

The four terms are a lower bound. Real peak adds:

- allocator fragmentation — free memory exists but not contiguously
- NCCL and cuBLAS workspaces, and CUDA graph capture buffers
- the transient full-precision copy created during an optimizer step
- for MoE, token-routing imbalance: the ledger assumes even expert load

Budget 10-20% headroom, and treat "the estimator said it fits" as a reason to
launch, never as a reason to skip reading the first step's memory report.
NVIDIA's own memory estimator carries the same caveat: it excludes
fragmentation, workspace, CUDA graph buffers and dispatcher memory. [official]

<!-- sources: nvidia-skills, hf-skills, trl-docs, pytorch-docs, deepspeed-docs -->
