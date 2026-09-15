# Speculative decoding rollout — regression

We enabled speculative decoding on the chat service last Thursday to cut
per-token latency. It made things worse and we want to know whether to push
`num_speculative_tokens` higher or lower.

## Before

```bash
vllm serve /srv/models/assistant-32b \
  --port 8000 \
  --max-model-len 16384 \
  --max-num-seqs 64 \
  --gpu-memory-utilization 0.90
```

Steady state, measured over a week of production traffic:

| Metric | Value |
|---|---|
| Sustained concurrency | 32 in flight (p50), 58 (p99) |
| TTFT p99 | 2.4 s |
| TPOT p50 | 26 ms |
| TPOT p99 | 41 ms |
| KV cache usage (vllm gauge) | 0.61 p50 |
| `vllm:num_preemptions_total` | flat at 0 |

## After

Added, nothing else changed:

```bash
  --speculative-config '{
    "method": "draft_model",
    "model": "/srv/models/assistant-1b",
    "num_speculative_tokens": 5
  }'
```

| Metric | Before | After |
|---|---|---|
| TTFT p99 | 2.4 s | 4.9 s |
| TPOT p50 | 26 ms | 24 ms |
| TPOT p99 | 41 ms | 77 ms |
| Output token throughput | 4120 tok/s | 2980 tok/s |
| KV cache usage p50 | 0.61 | 0.94 |
| `vllm:num_preemptions_total` | 0 | 14200 and climbing |

Single-request latency in a manual `curl` test does feel snappier than
before.

## What we want to decide

The draft model is 1B against a 32B target, same family. Someone suggested
raising `num_speculative_tokens` from 5 to 8 "since the draft is cheap", and
someone else wants to keep speculation but also raise
`--gpu-memory-utilization` to 0.97 to win back the KV cache we lost.

Workload shape: 900-token prompts (a fixed 700-token system prompt plus a
short user turn), 300-token answers, humans waiting in a chat UI.

Which way do we go?
