---
name: ml-training
description: "Trains and fine-tunes model weights with LoRA, distributed training and GPU optimization."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

# ml-training

Paths below are relative to this skill's directory.

## Scope

Everything between "we have a model and some data" and "the weights we
produced are serving traffic": method choice, the memory arithmetic that
decides whether a run is possible, distributed strategy, dataset hygiene,
evaluation that can be believed, checkpointing, and the handoff to an
inference server.

Calling a model someone else trained is the `ai-engineering` skill's job; changing the weights is the `ml-training` skill's.

Not covered — do not answer from this skill:

- Prompting, RAG, agent loops, and anything whose remedy is a better request
  to a hosted model: the `ai-engineering` skill.
- Running someone else's diffusion or speech weights to produce images,
  video or audio, and the reproducibility of those renders: the
  `generative-media` skill. Training or adapting those weights belongs here.
- Python packaging, virtualenvs, type checking, the language itself: the
  `python` skill. Training code is Python, but its problems here are
  numerical and memory-shaped.
- Dockerfiles, Kubernetes, job schedulers: the `containers` skill.
- Inference-serving performance: benchmarking a deployment, KV cache and
  `max-model-len` sizing, batching and chunked prefill, prefix caching,
  inference-side parallelism, and replica scaling: the `model-serving` skill.
  The handoff of a checkpoint to a server belongs here; everything the server
  does with it afterwards does not.
- GPU instance types, quota requests, spot interruption, storage classes:
  the `aws`, `azure` and `gcp` skills.
- Vector stores and index tuning: the `redis`, `mongodb`, `postgres` and
  `elasticsearch` skills.
- Writing a SKILL.md: the `skill-authoring` skill.
- Classical tabular ML, forecasting, computer-vision pipelines that are not
  transformer fine-tunes, and scientific or bioinformatics workflows. Nothing
  here is tuned for them.

## Read first

`references/api-versions.md` before touching any training script. Most
scripts in circulation were written against transformers 4.x and trl 0.x and
fail at config construction on transformers 5 / trl 1, one `TypeError` per
launch. Fix them in one pass.

## Core rules

Each rule is an invariant; the clause after the dash is what violating it costs.

1. Before any run, write the memory ledger — weights, gradients, optimizer
   state, activations, separately. A total without a breakdown cannot tell
   you which knob to turn, and the default guess (batch size) is wrong
   whenever model state dominates.
2. Full fine-tuning costs about 16 bytes per parameter of model state before
   a single activation: 2 for the bf16 weight, 2 for the gradient, 8 for
   Adam's two fp32 moments, 4 for the fp32 master copy. An 8B model is
   therefore ~119 GiB and does not fit on one 80 GB card at any batch size —
   proposing a smaller batch there wastes a launch and a queue slot.
3. `bf16=True` does not halve training memory. It halves weights and
   gradients and leaves the optimizer term alone, so expect 25-30% off model
   state, not 50% — a plan built on "half" is short by a card.
4. Gradient accumulation changes the effective batch, not the activation
   peak; the micro-batch is what activations scale with. Reaching for
   `gradient_accumulation_steps` to fix an OOM without lowering the
   per-device batch changes nothing and costs a run.
5. Sharding (ZeRO, FSDP) divides model state across the data-parallel group
   and leaves activations untouched. A run whose dominant term is activations
   gets no relief from more GPUs, and the cluster bill says otherwise.
6. LoRA freezes the base model; it does not shrink it. Gradients and
   optimizer state collapse to the adapter's size, the weights stay resident
   in full — so LoRA does not rescue a model whose *weights* alone exceed the
   card. QLoRA is the tool for that term.
7. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` before changing any
   parallelism degree. Fragmentation-induced OOM is common and this costs
   nothing, where doubling tensor parallelism to fix the same OOM has been
   measured at -28% throughput for 3 GB. (Incompatible with `--use-nccl-ub`.)
8. Keep tensor parallelism inside one NVLink domain and cross node boundaries
   with pipeline or data parallelism — TP over the network turns an
   all-reduce per transformer block into the step's critical path.
9. Minimum GPUs for a combined config is `PP * max(TP * CP, EP * ETP)`, not
   the product of every dimension: the dense and expert meshes share the GPUs
   inside a pipeline stage. The product form over-allocates hardware and is
   in many sizing tables.
10. Deduplicate and decontaminate the pooled corpus **before** splitting.
    Deduplicating each split separately leaves every cross-split pair intact,
    which is exactly the pair that inflates the eval number you will report.
11. Split by the unit of independence — thread, document, customer, time —
    never by row. A random row split over re-opened tickets or chunked
    documents measures memorisation.
12. Any public benchmark you report on is checked against the training corpus
    by n-gram overlap (n=13 is the standard), and the contaminated fraction
    is reported with the score. An unchecked benchmark number is not a
    measurement, and mixing the benchmark into training for "domain coverage"
    destroys it outright.
13. Measure the base model on the same eval set before training. Without that
    baseline the fine-tune gets credit for everything the base model already
    did, and a pointless training cycle becomes a quarterly ritual.
14. Every fine-tune runs a regression suite against general capability, not
    only its own task metric — a model that is better at one task and worse
    at everything else passes task-only evaluation and fails in the product.
15. Preference methods run at roughly 1e-6, SFT at roughly 2e-5 (the trl 1.13
    defaults). Carrying an SFT learning rate into DPO or GRPO moves the
    policy off the manifold: it wins the preference eval and cannot hold a
    conversation.
16. DPO's `beta` is the KL anchor to the reference model, and the reference
    is the SFT checkpoint the run started from. Anchoring to the base model,
    or dropping `beta` to learn faster, buys preference-set wins and pays in
    everything else.
17. GRPO requires a reward that is verifiable — a test passes, the arithmetic
    checks, the schema validates. A reward that can be satisfied by emitting
    a fixed string will be, especially at the trl 1.13 default `beta=0.0`,
    which switches the KL penalty off.
18. GRPO's `generation_batch_size` (per-device batch x world size x
    steps-per-generation) must be divisible by `num_generations`, or the
    config raises before the first step. On one GPU this is what forces
    gradient accumulation: a group of two is a coin flip, not an advantage
    estimate.
19. A resumable checkpoint carries optimizer state, scheduler state, step
    count, RNG state and the dataloader position. Weights alone resume as a
    warm start with zero momentum and a restarted warmup, and the loss curve
    shows it.
20. Under FSDP or ZeRO-3, save with Distributed Checkpoint or the distributed
    state-dict helpers. `torch.save(model.state_dict())` over DTensors writes
    a file that loads nowhere else, and that is discovered at serving time.
21. Verify the loss mask by decoding the positions where `labels != -100` on
    one real batch. If that text is not exactly what the model should
    produce, every subsequent number is measuring the wrong objective.
22. Render one training example and compare it byte-for-byte with what the
    serving stack sends. A template or BOS mismatch degrades everything and
    fails no test.
23. Two runs differing by a fraction of a point are the same run. Establish
    the noise floor with two seeds before attributing a delta to a change —
    reduction order, kernel versions and world size all move weights even
    when fully seeded.
24. Change one thing per run and record the resolved config, package
    versions, dataset hash and base-model revision with the checkpoint. A run
    you cannot reconstruct is an anecdote, and a config where three knobs
    moved cannot be bisected.

## Workflows

### plan-a-run

Before requesting GPUs.

- [ ] State the goal as an acceptance criterion that can come out false, and
      name the eval set it will be judged on. Freeze that set now.
- [ ] Check whether weights need to change at all: write ten examples of the
      wanted behaviour and try them as a prompt. If that works, stop — this
      is the `ai-engineering` skill's problem.
- [ ] Pick the method from the data you have, not the one you want:
      `references/method-selection.md`.
- [ ] Compute the token-length distribution with the real tokenizer and chat
      template. Set `max_length` from the p99, and note the truncated
      fraction.
- [ ] Run `uv run scripts/vram_ledger.py` for the candidate configuration.
      Identify the dominant term and choose the remedy that moves *that*
      term: `references/memory-ledger.md`.
- [ ] If it needs more than one GPU, choose the parallelism from the model
      size and the interconnect, and compute the minimum GPU count:
      `references/parallelism.md`.
- [ ] Run `uv run scripts/dataset_overlap.py --train ... --eval ...` and fix
      what it reports before training: `references/dataset-hygiene.md`.
- [ ] Decide checkpoint cadence, retention and disk budget at roughly 16
      bytes per parameter per checkpoint.
- [ ] Smoke-run: 10 steps at the real sequence length and micro-batch, with
      eval and checkpointing both triggered once. Record peak memory.
- [ ] **Gate — THE LEDGER MATCHES THE SMOKE RUN:** measured peak is within
      about 20% of the estimate, the overlap check is clean, and the decoded
      loss mask is the text you want generated. A mismatch means the
      configuration is not the one you costed.

### debug-oom

- [ ] Read the allocator message: allocated, reserved-but-unallocated, and
      the size of the failed allocation. Reserved-but-unallocated in the
      gigabytes means fragmentation.
- [ ] Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` and retry before
      anything else.
- [ ] Establish *when* it OOMs — step 1, the first eval boundary, the first
      save, or gradually. Each has a different cause:
      `references/oom-and-throughput.md`.
- [ ] Run the ledger, then walk the fixed order in that file. Re-run the
      ledger after each change; the dominant term moves.
- [ ] **Gate — THE FIX MATCHES THE DOMINANT TERM:** you can name the term
      that dominated, the remedy that moves it, and the throughput it cost.
      "It stopped OOMing after I changed four things" is not a diagnosis.

### review-training-code

Reviewing a script or config before GPU hours are spent.

- [ ] Check it against the installed versions first: the renames in
      `references/api-versions.md` fail at construction and hide everything
      behind them.
- [ ] Recompute the memory ledger from the config's own numbers and say
      whether it fits the stated hardware.
- [ ] Recompute the effective batch and, for GRPO, the generation-batch
      divisibility.
- [ ] Check learning rate against the method (rule 15), and the epoch count
      against the dataset size.
- [ ] Trace the data path: where the split happens relative to dedup and
      decontamination, what the loss is masked to, what gets truncated.
- [ ] Check what is saved and whether it can be resumed and served.
- [ ] **Gate — EVERY FINDING NAMES ITS FAILURE:** each finding says whether
      it stops the script, wastes the run, or silently degrades the result.
      A finding you cannot classify is a style preference; drop it.

### diagnose-quality

The metric and reality disagree, or the fine-tune did not help.

- [ ] Check contamination first — benchmark against corpus, and both sides of
      the split against each other. It is the most likely cause and the
      cheapest to rule out.
- [ ] Check independence: is the reported subset carved out of the eval
      split, is the eval set derived from anything used in filtering.
- [ ] Compare against the base model on the same set with the same decoding
      parameters. Then compare against the previous release.
- [ ] Check the metric against the goal: exact match rewards reproducing a
      reference string, which memorisation does perfectly.
- [ ] Check training-time defects last: loss mask, template, truncation,
      learning rate, epochs. `references/evaluation.md`.
- [ ] **Gate — THE DISAGREEMENT IS EXPLAINED, NOT NARROWED:** you can say
      which measurement was wrong and why, and which numbers must be
      re-measured. Adjusting a threshold until the numbers agree is not an
      explanation.

### Rationalizations

| Excuse | Reality |
|---|---|
| "Just lower the batch size" | Only if activations dominate. Say which term does first. |
| "We'll use LoRA, so memory is fine" | The frozen base is still resident. LoRA moves two of four terms. |
| "More GPUs will fix the OOM" | Not if activations dominate; sharding does not touch them. |
| "The benchmark is 86%, ship it" | Check whether the benchmark is in the training set before believing it. |
| "We deduplicated the data" | Per split, after splitting? Then the leakage is still there. |
| "It converged, so the data is fine" | Convergence on leaked data is memorisation with a nice curve. |
| "bf16 halves the memory" | It halves two terms of four. The optimizer is unchanged. |
| "Same hyperparameters as the SFT run" | For DPO or GRPO that is a twentyfold learning rate. |
| "We'll evaluate after we see the loss" | Then the criterion will describe whatever you built. |

### Red flags

Stop when you catch any of these: an OOM "fixed" by changing several knobs at
once; a reported benchmark that was never checked against the corpus; a
train/eval split created before deduplication; a preference run at 2e-5; a
GRPO reward that a fixed string satisfies; a checkpoint directory containing
only weights; a run comparison across a transformers major version; a
`max_length` chosen without looking at the length distribution; "we'll merge
the adapter later" with no record of the base revision; a quantized model
shipped without a bf16 number to compare against.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Bytes per parameter, the four terms, what mixed precision really costs, what each remedy moves, worked ledgers | Sizing a run, or an OOM whose cause is unclear | `references/memory-ledger.md` |
| SFT vs DPO vs GRPO preconditions and data shapes, learning-rate scales, LoRA/QLoRA/full choice, continued pretraining | Choosing how to train, or reviewing someone's choice | `references/method-selection.md` |
| DDP/ZeRO/FSDP2/TP/PP/CP ladder, communication costs, minimum GPU count, effective batch across world sizes | The run needs more than one GPU | `references/parallelism.md` |
| transformers 5 / trl 1 removed arguments, changed defaults, gradient-checkpointing signature, reading a version from its error | Before editing any training script | `references/api-versions.md` |
| Dedup/decontaminate/split order, n-gram contamination, token-length inspection, loss masking, how much data is enough | Building or auditing a dataset pipeline | `references/dataset-hygiene.md` |
| The four measurements, reading loss curves, benchmark-versus-human disagreement, regression suites, LLM-as-judge discipline | Deciding whether a model is better | `references/evaluation.md` |
| The fixed OOM order, reading the allocator message, OOM-at-step-200 causes, throughput thieves | Something is out of memory or slower than it should be | `references/oom-and-throughput.md` |
| What a resumable checkpoint contains, distributed checkpoints, adapter provenance, seeding, irreducible nondeterminism | Setting up saving/resume, or a result will not reproduce | `references/checkpointing-and-reproducibility.md` |
| PTQ vs QAT vs QLoRA, format choice, what quantization actually buys, measuring the damage | Shrinking a model for training or serving | `references/quantization.md` |
| The three silent mismatches at the handoff (chat template, tokenizer, stop strings), establishing the bf16 baseline, adapter provenance | Handing a trained checkpoint to an inference server | `references/serving-handoff.md` |

## Output format

**Training-code review** — the `review-training-code` workflow. Group by
severity, because the classes have different urgency: a construction error
costs a launch, a hyperparameter error costs the run, a data defect costs
every number measured afterwards.

```
## Blocks the launch
path:line - <finding> - <the error it raises> - <fix>

## Wastes the run
path:line - <finding> - <what the run will produce instead> - <fix>

## Silently degrades the result
path:line - <finding> - <what it corrupts and how you would notice> - <fix>

## Memory ledger for this config
weights <X> | gradients <X> | optimizer <X> | activations <X> | total <X>
dominant term: <term> -> <remedy that moves that term>
fits <hardware>: yes / no
```

**Run plan** — the `plan-a-run` workflow. Short, and every line a number
someone can check.

```
Method: <SFT|DPO|GRPO|continued pretraining> because <the data you have>
Base: <model id @ revision>
Data: <rows> rows, <tokens> tokens, p99 <N> tokens, truncated at max_length=<N>: <X>%
Overlap check: <clean | N eval rows share a 13-gram with train>
Ledger: <per-GPU total> on <hardware>, dominant term <term>
Parallelism: <config>, min GPUs <PP * max(TP*CP, EP*ETP)>
Effective batch: <per-device> x <accum> x <world> = <N>
Acceptance: <criterion that can come out false>, measured on <frozen eval set>
Regression: <suite>, tolerance <N points>
```

## Environment

The scripts in `scripts/` are dependency-free and run anywhere:

```bash
uv run scripts/vram_ledger.py --params 8e9 --seq 4096 --micro-batch 4
uv run scripts/dataset_overlap.py --train train.jsonl --eval eval.jsonl
```

Both are **Run** scripts. `dataset_overlap.py` exits non-zero when it finds
leakage, so it can gate a pipeline.

For the training stack itself, read the versions rather than assuming them:

```bash
python -c "import torch, transformers, trl, peft; print(torch.__version__, transformers.__version__, trl.__version__, peft.__version__)"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```
