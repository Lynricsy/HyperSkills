# Checkpoints, resumption, reproducibility

Verified against: torch 2.14.0, transformers 5.17.0.

## Contents

- [A checkpoint is not the weights](#a-checkpoint-is-not-the-weights)
- [Resuming correctly](#resuming-correctly)
- [Sharded checkpoints](#sharded-checkpoints)
- [Adapters and merging](#adapters-and-merging)
- [What "reproducible" can mean](#what-reproducible-can-mean)
- [Seeding everything](#seeding-everything)
- [The irreducible nondeterminism](#the-irreducible-nondeterminism)
- [Recording a run](#recording-a-run)

## A checkpoint is not the weights

A resumable checkpoint contains, at minimum:

- model weights
- optimizer state (both Adam moments — this is the large part)
- LR-scheduler state
- the training step / global step counter
- RNG state for torch, CUDA, numpy and python
- dataloader position, or enough to reconstruct it

A "checkpoint" that is only the weights resumes as a fresh run from a warm
start: the optimizer restarts with zero momentum and the scheduler restarts
its warmup. The loss curve shows a visible discontinuity at the resume point,
and on a long run the damage is real rather than cosmetic.

Budget the disk. Full-model checkpoints cost roughly 16 bytes per parameter
(bf16 weights plus fp32 optimizer state and master copy), so an 8B run writes
about 120 GB per checkpoint. Two epochs of checkpoints every 500 steps fills
a scratch volume during the night and the job dies with a disk error, not a
training error. Set `save_total_limit`, and keep the best checkpoint
separately from the rolling ones.

## Resuming correctly

- Resume from the checkpoint directory, not from the weights file.
- Keep the effective batch, the dataset and its order identical. Resuming
  with a different world size changes the effective batch mid-run and the
  schedule no longer matches the step count.
- The dataloader position matters. Without it, resumption replays data the
  model has already seen in this epoch — invisible in the loss, visible as
  mild memorisation.
- A resumed run is a new artifact. Record which checkpoint it came from; a
  results table with two rows that both say "3 epochs" and came from
  different resume points explains nothing.

## Sharded checkpoints

With ZeRO-3 or FSDP, each rank holds a shard. Two ways to save, with
different properties:

- **Distributed Checkpoint** (`torch.distributed.checkpoint`) — every rank
  writes in parallel, producing multiple files, and load-time resharding lets
  a run resume on a different world size. This is the default for anything
  sharded. [official]
- **Consolidated state dict** — gather to rank 0 with
  `get_model_state_dict(..., full_state_dict=True, cpu_offload=True)`. This
  is what you publish or serve; it needs enough host RAM for the whole model
  and it is not the format you resume from.

A plain `torch.save(model.state_dict())` over DTensor parameters writes
something that loads nowhere else. The failure appears weeks later, at the
moment someone tries to serve the model. [official]

Sharded checkpoints also carry a topology assumption. Verify resumption at
the world size you will actually use, on a two-step run, before relying on it
during an incident.

## Adapters and merging

A LoRA checkpoint is small because it is only the adapter — it is worthless
without the exact base model revision it was trained against. Record the base
model id *and* its commit hash next to the adapter; "Llama-3.1-8B" is not a
version.

Merge order matters: merging a bf16-trained adapter into a 4-bit quantised
base loses accuracy relative to merging into the bf16 base and quantising
afterwards.

## What "reproducible" can mean

Be precise about which of these you are promising, because they cost
different amounts:

| Level | Guarantee | Cost |
|---|---|---|
| Recorded | you can say exactly what ran | free; do this always |
| Statistically reproducible | reruns land within noise | cheap |
| Bitwise reproducible | identical weights, same hardware and versions | slow, and only sometimes possible |

PyTorch does not promise reproducibility across releases, commits or
platforms, and results are not reproducible between CPU and GPU even with
identical seeds. [official] Bitwise reproducibility across a version bump is
not a goal you can meet; do not write it into an acceptance criterion.

## Seeding everything

`seed=42` in `TrainingArguments` seeds torch, numpy and python. It does not
cover everything that varies:

```python
torch.manual_seed(s)          # CPU and all CUDA devices
random.seed(s)
numpy.random.seed(s)          # not Generator objects, which seed separately
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.benchmark = False
```

- `torch.use_deterministic_algorithms(True)` raises on any op with no
  deterministic implementation instead of silently varying — which is the
  point. Deterministic kernels are slower. [official]
- `cudnn.benchmark=True` picks the fastest convolution algorithm by timing
  it, and the timing differs between runs. It is a separate setting from
  `cudnn.deterministic`. [official]
- Dataloader workers need their own `worker_init_fn` or a generator; the
  parent seed does not propagate into worker processes.
- `data_seed` defaults to `None`, so the data order follows `seed`. Splitting
  them lets you re-run the same model init against a different data order —
  which is how you find out whether a delta is real. [verified]

## The irreducible nondeterminism

Even fully seeded, these still move the weights:

- **Non-associative floating-point reduction order.** Atomics and
  multi-GPU all-reduce sum in whatever order the kernels finish.
- **Kernel and library versions.** cuBLAS/cuDNN algorithm selection changes
  between versions and across GPU models.
- **World size.** Gradients are reduced over a different partition; the
  arithmetic differs even with the same data.
- **Mixed precision.** bf16 rounding differences are amplified by the
  optimizer over thousands of steps.

The practical consequence: two runs that differ by 0.2 points on an eval are
the same run. Establish the noise floor by running the same config twice with
different seeds before attributing a delta to a change.

## Recording a run

Store with every checkpoint, in the checkpoint directory:

- resolved config (the merged one, not the file you edited)
- package versions — torch, transformers, trl, peft, accelerate, the CUDA
  version, the GPU model and count
- dataset identity: path, revision or content hash, row count, token count
- base model id and revision
- the launch command, verbatim
- git commit of the training code, and whether the tree was dirty

This is the difference between "the good checkpoint from last month" and an
artifact someone else can rebuild.

<!-- sources: pytorch-docs, orchestra-ai-research, nvidia-skills, hf-skills -->
