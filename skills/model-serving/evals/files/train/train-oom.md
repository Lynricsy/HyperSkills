# SFT run dies at step ~200

8x H100 80GB, single node. Full fine-tune of a 8B model with TRL `SFTTrainer`,
bf16, FSDP2 full shard.

Config in use:

```python
SFTConfig(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    max_length=8192,
    packing=False,
    gradient_checkpointing=False,
    bf16=True,
    optim="adamw_torch",
    learning_rate=2e-5,
)
```

The first ~190 steps run fine at about 4.1 s/step. Then:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 3.52 GiB.
GPU 0 has a total capacity of 79.15 GiB of which 1.88 GiB is free.
Process 1 has 77.26 GiB memory in use. Of the allocated memory
71.04 GiB is allocated by PyTorch, and 4.61 GiB is reserved by PyTorch
but unallocated.
```

Batch size is already 1 per device, so we cannot reduce it further. Someone
suggested we just buy H200s.

The dataset has a long tail: token-length p50 is 900, p99 is 7800, max is
8192 after truncation.

What is actually going on and what do we change?
