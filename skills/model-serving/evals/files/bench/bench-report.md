# Serving benchmark — ticket-assistant-v3, sign-off request

Owner: platform. Target: replace the 7B currently behind `/v1/chat`.
Hardware: 1x H100 80GB, CUDA 12.8, vLLM 0.29.0.

## Server

```bash
vllm serve /srv/models/ticket-assistant-v3 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

Server was started and the benchmark launched immediately afterwards
(script does `vllm serve ... & sleep 45 && vllm bench serve ...`).

## Benchmark command

```bash
vllm bench serve \
  --backend openai-chat \
  --model /srv/models/ticket-assistant-v3 \
  --base-url http://localhost:8000 \
  --dataset-name random \
  --random-input-len 512 \
  --random-output-len 512 \
  --num-prompts 200 \
  --request-rate inf
```

Single run. We did not repeat it — the numbers looked stable enough in the
progress output.

## Results

| Metric | Value |
|---|---|
| Successful requests | 200 |
| Benchmark duration (s) | 42.13 |
| Total input tokens | 102400 |
| Total generated tokens | 102400 |
| Request throughput (req/s) | 4.75 |
| Output token throughput (tok/s) | 2430.62 |
| Total token throughput (tok/s) | 4861.24 |
| Mean TTFT (ms) | 8104.22 |
| Median TTFT (ms) | 8033.10 |
| P99 TTFT (ms) | 17303.44 |
| Mean TPOT (ms) | 31.02 |
| Median TPOT (ms) | 30.55 |
| P99 TPOT (ms) | 47.02 |
| Mean ITL (ms) | 30.88 |
| Median ITL (ms) | 29.14 |
| P99 ITL (ms) | 49.80 |

`nvidia-smi` showed **95-99% GPU utilization** for the whole run, so the card
is clearly saturated and this is the hardware's ceiling.

## Proposed SLO

From the P99 numbers above:

- TTFT SLO: 17.5 s
- TPOT SLO: 50 ms
- Capacity: 4.75 req/s per H100, so 7 cards for our 30 req/s peak.

## Production traffic, for reference

Pulled from the gateway logs, last 14 days:

- Prompt length: p50 5.9k tokens, p99 11.4k tokens (long ticket threads
  pasted in, plus a 1.2k-token system prompt that is identical on every
  request).
- Completion length: p50 180 tokens, p99 410 tokens.
- Arrival: 30 req/s at peak, bursty, humans waiting on the answer in a
  support console.
- Current 7B service: TTFT p99 is 1.9 s and support is happy with it.

Sign off?
