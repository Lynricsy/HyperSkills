# Quantization

## Contents

- [Three different things called quantization](#three-different-things-called-quantization)
- [Choosing a format](#choosing-a-format)
- [QLoRA](#qlora)
- [What quantization actually buys](#what-quantization-actually-buys)
- [Measuring the damage](#measuring-the-damage)
- [Order of operations](#order-of-operations)

## Three different things called quantization

Distinguish them before discussing trade-offs; they fail differently.

| Kind | When | Purpose |
|---|---|---|
| Post-training quantization (PTQ) | after training, on the finished weights | shrink a model for serving |
| Quantized training / QLoRA | during training, base weights frozen in low precision | fit training onto smaller GPUs |
| Quantization-aware training (QAT) | during training, simulating the target precision | recover accuracy PTQ loses |

PTQ is the default and covers most needs. QAT is worth its cost only when
PTQ has been measured and the loss is unacceptable — it requires a training
run, which is the thing you were trying to avoid.

## Choosing a format

For serving a decoder LLM:

| Format | Bits | Calibration | Use when |
|---|---|---|---|
| bf16 | 16 | none | it fits; the baseline everything else is measured against |
| FP8 | 8 | none or minimal | Hopper/Blackwell — near-lossless with real speedup |
| AWQ / GPTQ | 4 | a calibration set | weights must be 4-bit for serving throughput |
| bitsandbytes NF4 | 4 | none | loading for *training* (QLoRA), not for peak serving throughput |
| GGUF (llama.cpp) | 2-8 | none | CPU or laptop inference; not a GPU-serving format |

Two rules that save a wasted week:

- **Calibration data must resemble production traffic.** A 4-bit model
  calibrated on generic web text and served on code degrades on code. The
  calibration set is small (hundreds of samples) and choosing it badly is
  free to do and expensive to discover.
- **Use the format your serving stack has a fast kernel for.** A quantization
  with no fused kernel in your engine dequantises at runtime and is *slower*
  than bf16 while being less accurate.

## QLoRA

Frozen base in 4-bit NF4, LoRA adapters trained in bf16 on top, with
double quantization and paged optimizers to survive memory spikes.

What it changes in the ledger: the *weights* term drops roughly fourfold.
The gradient and optimizer terms were already tiny under LoRA, and the
activation term is unchanged. So QLoRA is the right tool when the frozen base
is what does not fit, and pointless when activations are the dominant term.

Costs to state honestly:

- Slower per step than LoRA in bf16 — dequantisation happens on every forward.
- Slightly worse than LoRA at the same rank; the gap is small and usually
  worth it, but it is not zero.
- Merging the adapter back into the 4-bit base compounds error. Merge into
  the bf16 base, then quantise for serving.

## What quantization actually buys

Be specific about which resource is freed:

- **Weight memory** — 4-bit is roughly a quarter of bf16. This is the real,
  reliable gain.
- **Memory bandwidth, therefore decode speed** — LLM decoding is
  bandwidth-bound, so smaller weights genuinely decode faster *when a fused
  kernel exists*.
- **KV cache** — separately quantizable and often the larger term at long
  context. Quantizing weights does nothing for it.
- **Prefill compute** — barely affected; prefill is compute-bound.

Quantization does **not** reduce the activation memory of a training step,
and it does not make a 4-bit model trainable in the ordinary sense —
gradients do not flow to 4-bit frozen weights, which is why QLoRA needs
adapters.

## Measuring the damage

Perplexity on a held-out set is the cheap screen; it is not sufficient.
Quantization damage is concentrated in the tails — long generations,
structured output, arithmetic, code — where a small perplexity change hides
a large behavioural one.

The minimum check for a quantized candidate:

1. perplexity against the bf16 model on the same text
2. your task metric, same eval set, same decoding parameters
3. a structured-output check — does valid JSON still come out
4. a long-generation check — does it still terminate

Report all four against the bf16 baseline. "4-bit, perplexity +0.03" alone is
not evidence that it is safe to ship.

## Order of operations

```
train (bf16) -> merge adapter into bf16 base -> evaluate bf16 -> quantize
             -> evaluate quantized -> compare -> serve
```

Every arrow that gets skipped shows up later as "the model got worse and
nobody knows when". In particular, quantizing before establishing the bf16
number leaves you unable to attribute the loss to quantization at all.

<!-- sources: orchestra-ai-research, hf-skills, vllm-docs -->
