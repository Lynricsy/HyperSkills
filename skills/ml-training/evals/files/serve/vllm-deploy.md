# Serving the fine-tuned ticket assistant

One A100 80GB, same box that trained it. Model is a full fine-tune of
Llama-3.1-8B saved in bf16 (no adapter, 16 GB of safetensors).

Target: 60 concurrent support agents, prompts are 4k-12k tokens (the whole
ticket thread is pasted in), answers are short (under 300 tokens). Agents
complain when the first token takes longer than a second.

## Current launch command

```bash
vllm serve /srv/models/ticket-assistant-v3 \
  --gpu-memory-utilization 0.98 \
  --max-model-len 131072 \
  --max-num-seqs 512 \
  --max-num-batched-tokens 4096 \
  --enable-chunked-prefill false \
  --enforce-eager \
  --swap-space 32 \
  --enable-metrics \
  --metrics-port 9090 \
  --port 8000
```

## Symptoms

- The server sometimes refuses to start at all; the log ends after the model
  weights finish loading.
- When it does start, the log repeats:
  `Sequence group 41 is preempted by PreemptionMode.RECOMPUTE mode because
  there is not enough KV cache space ... total_cumulative_preemption_cnt=863`
- `curl http://localhost:9090/metrics` returns connection refused.
- Throughput is about a third of what the same box did with a 7B model last
  year, and time-to-first-token spikes to 6 s under load.

## What we tried

Dropped `--max-num-seqs` to 64. Preemption warnings got rarer but TTFT did
not improve and the GPU sat at 40% utilisation.
