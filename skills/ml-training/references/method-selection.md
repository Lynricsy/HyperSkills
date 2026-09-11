# Choosing the training method

Verified against: trl 1.13.0, transformers 5.17.0, peft 0.20.0.

## Contents

- [The prior question](#the-prior-question)
- [What each method needs](#what-each-method-needs)
- [SFT](#sft)
- [DPO](#dpo)
- [GRPO and verifiable rewards](#grpo-and-verifiable-rewards)
- [Learning-rate scales](#learning-rate-scales)
- [Full fine-tune, LoRA, or QLoRA](#full-fine-tune-lora-or-qlora)
- [Continued pretraining](#continued-pretraining)

## The prior question

Before choosing a method: does this task need weight changes at all?

Fine-tuning teaches *behaviour* — format, tone, the shape of a good answer,
a tool-calling convention, a domain's idiom. It is a poor way to install
*facts*: facts go stale, cannot be cited, and a model that learned them by
gradient descent will state the retired ones just as confidently. Retrieval
and prompting change facts in an afternoon; a fine-tune commits you to a
retraining cycle every time the facts move.

The honest test: write ten examples of the behaviour you want. If a prompt
containing those ten examples already produces it, you have your answer and
it is not a training run.

## What each method needs

| Method | Data shape | Volume that is not a waste of GPU hours | Needs a reference model | Needs generation in the loop |
|---|---|---|---|---|
| SFT | `messages`, or `prompt`/`completion`, or raw `text` | 1k-100k demonstrations | no | no |
| DPO | `prompt` + `chosen` + `rejected` | 5k-50k pairs | yes (frozen copy) | no |
| GRPO | `prompt` only + a reward function | 1k+ prompts, plus a reward you trust | optional (`beta`) | yes — dominates step time |
| Reward model | `chosen`/`rejected` pairs | as DPO | no | no |

The order is a pipeline, not a menu: preference methods assume a model that
already produces plausible candidates. Running DPO on a base model teaches it
to prefer one incoherent answer over another.

## SFT

The default. Everything else is a correction applied to an SFT'd model.

Failure modes that are not obvious from the loss curve:

- **Loss computed on the prompt.** For conversational data you want the loss
  on the assistant turns only. `SFTConfig.completion_only_loss` defaults to
  `None`, meaning the trainer infers it from the dataset shape: on
  prompt-completion data it masks the prompt, on plain `text` it cannot.
  Getting this wrong trains the model to generate user turns. [verified]
- **Chat template mismatch.** Training with one template and serving with
  another produces a model that is subtly worse at everything and passes
  every unit test. Render one training example to a string and compare it
  byte-for-byte with what the serving stack sends.
- **Truncation silently eating the answer.** `SFTConfig.max_length` defaults
  to 1024 and `truncation_mode` to `keep_start`, so a 3k-token example is cut
  at 1024 and the assistant's answer is gone — the row survives as a
  prompt-only example and contributes gradient noise. Check the token-length
  distribution against `max_length` before launching. [verified]
- **Packing.** `packing=False` by default; enabling it concatenates short
  examples up to `max_length` so padding stops dominating the step. Use it
  when your median length is far below `max_length`; the `bfd` strategy
  (best-fit-decreasing, the default when packing is on) minimises waste.
  [verified]

## DPO

Preference optimisation against a frozen reference copy of the starting
policy. `beta` is the strength of the KL anchor to that reference:

- `beta=0.1` is the library default and the value most published recipes use.
- Higher `beta` keeps the policy near the reference — safer, learns less.
- Lower `beta` lets it drift — learns the preference, degrades everything
  else, and shows up as a model that is better on the preference set and
  worse on the eval set.

Preconditions people skip:

- **The reference model is the SFT checkpoint, not the base model** — DPO
  measures drift from where you started, and starting elsewhere makes the KL
  term meaningless.
- **Pairs must differ on the axis you care about.** Pairs where `chosen` is
  simply longer teach length. Check the length distribution of `chosen`
  versus `rejected` before trusting a win.
- **Self-generated rejections drift.** If `rejected` is sampled from the model
  being trained, the pairs are stale after the first epoch — this is the
  argument for an online method rather than more epochs.
- Two to three epochs is already a lot. Five epochs on a few thousand pairs
  is memorisation with a KL penalty attached.

`DPOConfig` in trl 1.13 has **no `max_prompt_length`** — prompt and completion
budgets were unified into `max_length` and passing the old name is a
`TypeError`. [verified]

## GRPO and verifiable rewards

Online RL: for each prompt the trainer samples `num_generations` completions,
scores them with your reward function, and pushes the policy toward the
above-average ones in each group.

It is the right method only when the reward is **verifiable** — a test suite
passes, the arithmetic checks out, the JSON parses against a schema. When the
reward is a heuristic string match, GRPO will find the cheapest way to satisfy
it, and that is not a bug in the algorithm.

Batch arithmetic is a hard gate, not a guideline:

```
generation_batch_size = per_device_train_batch_size
                        x world_size
                        x steps_per_generation   # defaults to gradient_accumulation_steps
```

`generation_batch_size` must be divisible by `num_generations`, otherwise
`GRPOConfig` raises before the first step:
`generation_batch_size (2) must be divisible by num_generations (8)`.
[verified] On a single GPU with `per_device_train_batch_size=2` and no
accumulation, the largest legal `num_generations` is 2 — and a group of 2 is
a coin flip, not an advantage estimate. Raising the accumulation steps is how
you buy group size on one card.

Defaults in trl 1.13 that differ from the published GRPO paper and from older
recipes: `beta=0.0` (KL penalty **off**), `loss_type='dapo'`,
`scale_rewards='group'`, `num_generations=8`, `epsilon=0.2`. [verified] With
`beta=0.0` there is nothing anchoring the policy to the reference, so a
gameable reward degrades the model quickly and quietly.

Generation dominates the step. `use_vllm=True` is the difference between
hours and days, and it costs GPU memory the ledger must account for: the
default `vllm_mode='colocate'` puts the inference engine on the same card as
the trainer with `vllm_gpu_memory_utilization=0.3`, i.e. 30% of the device is
gone before the trainer allocates anything. [verified] Server mode moves that
cost to another GPU.

## Learning-rate scales

The single most common wasted run is an SFT learning rate carried into
preference training.

| Config | Default LR in trl 1.13 |
|---|---|
| `SFTConfig` | 2e-5 |
| `DPOConfig` | 1e-6 |
| `GRPOConfig` | 1e-6 |

[verified] The twentyfold gap is not conservatism: preference methods move a
policy that is already good, and at 2e-5 they move it off the manifold. A DPO
run at 2e-5 produces a model that wins the preference eval and cannot hold a
conversation.

## Full fine-tune, LoRA, or QLoRA

Default to **LoRA** for any model you cannot hold three times over — weights,
gradients and optimizer state run to roughly 16 bytes per parameter. Use a **full
fine-tune** when you are changing what the model fundamentally does and have
the GPUs; use **QLoRA** when even the frozen base does not fit.

- `r` controls capacity. 8-16 for style and format, 32-64 for a genuinely new
  skill. Raising `r` past the point where the loss stops improving buys
  nothing except a larger adapter.
- `lora_alpha` is a scale, conventionally `2 x r`. `LoraConfig` defaults to
  `r=8, lora_alpha=8`; almost every recipe overrides both. [verified]
- `target_modules` defaults to `None`, which resolves to the model family's
  registered default — usually the attention projections only. Adding the MLP
  projections roughly triples the adapter and is what you do when attention-
  only LoRA underfits. [verified]
- Merging an adapter trained in bf16 back into a 4-bit base loses accuracy;
  merge into the bf16 base, then quantise.

## Continued pretraining

Raw-text training on a domain corpus, before any instruction tuning. Worth it
only when the domain's *tokens* are unusual — a language the tokenizer splits
badly, an internal DSL, a notation. For domain *knowledge* expressed in
ordinary prose, retrieval wins on cost and on being correctable.

Catastrophic forgetting is the tax: without a replay mixture of general data
(commonly 5-20% of the corpus), the model gets better at your domain and
measurably worse at instruction following. Measure both before and after, on
the same eval.

<!-- sources: hf-skills, trl-docs, orchestra-ai-research, peft-docs -->
