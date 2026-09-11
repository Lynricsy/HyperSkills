#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the per-GPU memory ledger for a transformer training run.

Answers the only question that matters before launching: which term is the
one that does not fit. Weights, gradients, optimizer state and activations
are reported separately because each has a different, non-interchangeable
remedy.

Everything here is arithmetic on the four terms, not a measurement. Treat the
total as a lower bound: it excludes allocator fragmentation, NCCL and cuBLAS
workspaces, CUDA graph buffers and the framework's own overhead, which
together routinely add 10-20% on a real run.

    uv run scripts/vram_ledger.py --params 8e9 --seq 4096 --micro-batch 4
    uv run scripts/vram_ledger.py --params 8e9 --seq 8192 --micro-batch 1 \
        --lora --grad-checkpoint --zero 3 --dp 8
"""

from __future__ import annotations

import argparse
import sys

GIB = 1024**3

# Adam/AdamW keeps two fp32 moments per trainable parameter (exp_avg,
# exp_avg_sq). Measured on torch 2.14: 8.000005 bytes/param for a 58M model,
# the remainder being the scalar `step` entry per parameter tensor.
ADAM_BYTES_PER_PARAM = 8
# Mixed-precision training additionally keeps an fp32 master copy of every
# trainable weight, which the optimizer updates. bf16 compute + fp32 master
# is the default shape of torch AMP and of DeepSpeed/Megatron mixed precision.
FP32_MASTER_BYTES = 4
# 8-bit optimizers (bitsandbytes adamw_bnb_8bit) keep the same two moments
# quantized to one byte each.
ADAM8BIT_BYTES_PER_PARAM = 2

# Activation bytes per token per layer, in units of `hidden`, for a standard
# pre-norm transformer block storing its intermediates in 2-byte precision.
# Derived from the term list in "Reducing Activation Recomputation in Large
# Transformer Models" (Korthikanti et al.), counting only the tensors kept for
# backward. It is a model-shape estimate, not a profile: real numbers move
# with the attention kernel (FlashAttention drops the seq^2 score matrix) and
# with fused kernels.
ACT_BYTES_PER_TOKEN_PER_LAYER_PER_HIDDEN = 34


def human(n: float) -> str:
    return f"{n / GIB:8.2f} GiB"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--params", type=float, required=True,
                   help="total parameter count, e.g. 8e9")
    p.add_argument("--layers", type=int, default=32)
    p.add_argument("--hidden", type=int, default=4096)
    p.add_argument("--seq", type=int, required=True, help="sequence length in tokens")
    p.add_argument("--micro-batch", type=int, required=True,
                   help="per-device micro-batch; gradient accumulation does not change it")
    p.add_argument("--dp", type=int, default=1, help="data-parallel world size")
    p.add_argument("--tp", type=int, default=1, help="tensor-parallel degree")
    p.add_argument("--pp", type=int, default=1, help="pipeline-parallel degree")
    p.add_argument("--zero", type=int, choices=[0, 1, 2, 3], default=0,
                   help="ZeRO/FSDP sharding stage across the DP group")
    p.add_argument("--lora", action="store_true",
                   help="train adapters only; --lora-frac sets the trainable share")
    p.add_argument("--lora-frac", type=float, default=0.005,
                   help="trainable fraction under LoRA (0.005 = 0.5%%, typical for r=16 on q/v)")
    p.add_argument("--grad-checkpoint", action="store_true",
                   help="recompute activations; keeps one block's worth plus layer boundaries")
    p.add_argument("--optimizer", choices=["adamw", "adamw8bit", "sgd"], default="adamw")
    p.add_argument("--weight-bytes", type=int, default=2, choices=[1, 2, 4],
                   help="bytes per stored weight: 2 for bf16/fp16, 1 for 8-bit, 4 for fp32")
    a = p.parse_args()

    if a.params <= 0 or a.seq <= 0 or a.micro_batch <= 0:
        print("--params, --seq and --micro-batch must all be positive", file=sys.stderr)
        return 2
    if a.lora and not 0 < a.lora_frac < 1:
        print(f"--lora-frac must be in (0, 1); got {a.lora_frac}", file=sys.stderr)
        return 2

    n = a.params
    shard = a.tp * a.pp            # model sharded across TP x PP ranks
    dp_shard = a.dp if a.zero else 1

    trainable = n * a.lora_frac if a.lora else n

    weights = n * a.weight_bytes / shard
    if a.zero == 3:
        weights /= dp_shard

    grads = trainable * 2 / shard  # gradients live in compute precision
    if a.zero >= 2:
        grads /= dp_shard

    per_param = {"adamw": ADAM_BYTES_PER_PARAM,
                 "adamw8bit": ADAM8BIT_BYTES_PER_PARAM,
                 "sgd": 0}[a.optimizer]
    # The fp32 master copy is part of the optimizer's state, not the weights:
    # it is sharded and offloaded with the optimizer, and it disappears with
    # the frozen parameters under LoRA.
    opt = trainable * (per_param + FP32_MASTER_BYTES) / shard
    if a.zero >= 1:
        opt /= dp_shard

    tokens = a.micro_batch * a.seq
    layers_held = 1 if a.grad_checkpoint else a.layers / a.pp
    act = tokens * a.hidden * ACT_BYTES_PER_TOKEN_PER_LAYER_PER_HIDDEN * layers_held / a.tp
    if a.grad_checkpoint:
        # Checkpointed runs still hold every layer's input boundary tensor.
        act += tokens * a.hidden * 2 * (a.layers / a.pp) / a.tp

    total = weights + grads + opt + act
    print(f"per-GPU ledger  params={n:.3g}  trainable={trainable:.3g}"
          f"  TP={a.tp} PP={a.pp} DP={a.dp} ZeRO={a.zero}")
    print(f"  weights        {human(weights)}")
    print(f"  gradients      {human(grads)}")
    print(f"  optimizer      {human(opt)}   ({a.optimizer}"
          f"{' + fp32 master' if per_param else ''})")
    print(f"  activations    {human(act)}   "
          f"({'recomputed' if a.grad_checkpoint else 'stored'}, "
          f"{a.micro_batch}x{a.seq} tokens)")
    print(f"  ---------------{'-' * 12}")
    print(f"  lower bound    {human(total)}   (add 10-20% for fragmentation and workspaces)")

    biggest = max([("weights", weights), ("gradients", grads),
                   ("optimizer", opt), ("activations", act)], key=lambda kv: kv[1])
    print(f"\n  dominant term: {biggest[0]}")
    if biggest[0] == "activations":
        print("  -> cut micro-batch or sequence length, or turn on gradient checkpointing;"
              "\n     sharding (ZeRO/FSDP) does not touch this term")
    elif biggest[0] == "optimizer":
        print("  -> LoRA, an 8-bit optimizer, or ZeRO stage 1 across the DP group;"
              "\n     gradient checkpointing does not touch this term")
    elif biggest[0] == "gradients":
        print("  -> ZeRO stage 2, or freeze parameters (LoRA)")
    else:
        print("  -> ZeRO stage 3 / FSDP, tensor or pipeline parallelism, or a smaller model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
