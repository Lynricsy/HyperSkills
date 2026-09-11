# transformers 5 / trl 1 API boundary

Verified against: torch 2.14.0, transformers 5.17.0, trl 1.13.0, peft 0.20.0.
Every entry below was checked by constructing the object on this machine.

## Contents

- [Why this file exists](#why-this-file-exists)
- [Arguments that were removed](#arguments-that-were-removed)
- [Defaults that changed](#defaults-that-changed)
- [Gradient checkpointing](#gradient-checkpointing)
- [Recognising the version from an error](#recognising-the-version-from-an-error)
- [Checking instead of guessing](#checking-instead-of-guessing)

## Why this file exists

Most training scripts in circulation, in blog posts, and in model-card
snippets were written against transformers 4.x and trl 0.x. They fail at
**config construction**, before a GPU is touched, with a `TypeError` that
names one argument at a time. Fixing them one `TypeError` per launch is the
slowest possible way to discover a rename, especially on a cluster where each
launch queues.

Read the whole table once, fix the script in one pass.

## Arguments that were removed

| Old | Now | Symptom |
|---|---|---|
| `SFTConfig(max_seq_length=...)` | `max_length` | `TypeError: SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'` |
| `DPOConfig(max_prompt_length=...)` | folded into `max_length` | `TypeError: ... unexpected keyword argument 'max_prompt_length'` |
| `TrainingArguments(evaluation_strategy=...)` | `eval_strategy` | `TypeError: ... unexpected keyword argument 'evaluation_strategy'` |
| `TrainingArguments(warmup_ratio=...)` | `warmup_steps` | `TypeError: ... unexpected keyword argument 'warmup_ratio'` |
| `Trainer(tokenizer=...)` | `processing_class=` | `TypeError: ... unexpected keyword argument 'tokenizer'` |
| `TrainingArguments(save_safetensors=...)` | gone; safetensors always | `TypeError` |
| `from_pretrained(torch_dtype=...)` | `dtype=` | warning: `` `torch_dtype` is deprecated! Use `dtype` instead! `` |
| `TrainingArguments(group_by_length=...)` | gone; use packing or padding-free batching | `TypeError` |

[verified] All eight checked against transformers 5.17.0 / trl 1.13.0 on this
machine: seven raise the `TypeError` shown, `torch_dtype` only warns.

`warmup_ratio` is the one that costs a run rather than a launch: converting
it is arithmetic you have to do yourself, `warmup_steps = ratio x
total_steps`, and `total_steps` depends on the dataset size, the effective
batch and the epoch count. Getting it wrong gives a schedule that warms up
for the whole run or not at all.

`torch_dtype` still works and only warns — which means a script can be half
migrated and look fine.

## Defaults that changed

| Setting | Value in transformers 5.17 / trl 1.13 | Why it matters |
|---|---|---|
| `TrainingArguments.optim` | `adamw_torch_fused` | fused kernel; memory is unchanged, still 8 bytes/param of state |
| `TrainingArguments.average_tokens_across_devices` | `True` | token-level losses are normalised globally, not per device — runs are not comparable across the version boundary |
| `TrainingArguments.seed` | `42` | `data_seed` is `None`, so the data order follows `seed` unless you split them |
| `SFTConfig.learning_rate` | `2e-5` | |
| `DPOConfig.learning_rate` | `1e-6` | twentyfold below SFT; carrying the SFT rate here is the most common wasted preference run |
| `GRPOConfig.learning_rate` | `1e-6` | |
| `SFTConfig.max_length` | `1024` | truncates from the start (`truncation_mode='keep_start'`) |
| `SFTConfig.packing` | `False`, strategy `bfd` when on | |
| `GRPOConfig.beta` | `0.0` | KL penalty off by default |
| `GRPOConfig.loss_type` | `'dapo'` | not the loss in the original GRPO paper |
| `GRPOConfig.num_generations` | `8` | must divide `generation_batch_size` |
| `GRPOConfig.vllm_mode` | `'colocate'`, `vllm_gpu_memory_utilization=0.3` | 30% of the device disappears when `use_vllm=True` |
| `SFTConfig/DPOConfig/GRPOConfig.bf16` | `None` | resolved from the accelerator; on a CPU-only box this raises `Your setup doesn't support bf16/gpu` |
| `LoraConfig` | `r=8, lora_alpha=8, target_modules=None` | almost every recipe overrides all three |

[verified] Read off the dataclass fields of the installed packages.

## Gradient checkpointing

`PreTrainedModel.gradient_checkpointing_enable()` in transformers 5 takes
three arguments, and the two new ones are the interesting part: [verified]

```python
model.gradient_checkpointing_enable(
    gradient_checkpointing_kwargs=None,   # defaults to {"use_reentrant": False}
    every_n_layers=1,                     # 1 = checkpoint every layer
    offload=False,                        # keep saved activations in pinned host memory
)
```

- `use_reentrant=False` is now the default. The reentrant implementation was
  the source of the "gradients are None with checkpointing + LoRA" class of
  bug; if you see advice to pass `use_reentrant=False` explicitly, it is
  describing an older version.
- `every_n_layers` makes checkpointing partial. Full checkpointing is roughly
  a 30% step-time tax for a large activation saving; if the saved memory goes
  unused, `every_n_layers=2` gives back half the speed. This is the
  transformers equivalent of selective recompute.
- `offload=True` moves saved activations to pinned host memory, freeing
  `layers x sequence x hidden` bytes of device memory at the cost of a
  device-to-host copy on the compute stream in forward and the reverse in
  backward. Long-sequence runs win; short-sequence runs just get slower.

One behaviour that catches people: enabling checkpointing does **not** flip
`config.use_cache`. [verified] It stays `True` and the model logs
`` `use_cache=True` is incompatible with gradient checkpointing. Setting
`use_cache=False`. `` at the first forward. That is a log line, not a Python
warning, so a script filtering `warnings` will not see it, and the same
config object handed to a generation call afterwards still says `True`.

## Recognising the version from an error

| Error text | Meaning |
|---|---|
| `unexpected keyword argument 'max_seq_length'` | trl >= 1.0 with a trl 0.x script |
| `unexpected keyword argument 'evaluation_strategy'` | transformers >= 5 with a 4.x script |
| `generation_batch_size (N) must be divisible by num_generations (G)` | GRPO batch arithmetic, not a memory problem |
| `Your setup doesn't support bf16/gpu` | no accelerator; `bf16=None` resolved to bf16 |
| `` `torch_dtype` is deprecated! `` | partially migrated script |

## Checking instead of guessing

Do not recall defaults; read them from the installed version:

```bash
python -c "import dataclasses, trl; print({f.name: f.default for f in dataclasses.fields(trl.GRPOConfig)})"
python -c "import transformers, trl, peft, torch; print(torch.__version__, transformers.__version__, trl.__version__, peft.__version__)"
```

A config field that does not appear in that dump does not exist in this
version, whatever the tutorial says.

<!-- sources: hf-skills, trl-docs, peft-docs -->
