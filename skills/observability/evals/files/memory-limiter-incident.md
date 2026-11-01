# Postmortem draft: missing billing logs during the 14:05 traffic spike

Author: Priya (platform). Status: draft, action items not yet approved.

## Setup

Gateway Collector: Deployment, 3 replicas, contrib image, each pod `resources.limits.memory: 2Gi`.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 1600
    spike_limit_mib: 400
  batch: {}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp_grpc/backend]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp_grpc/backend]
```

Senders:

- `checkout-api`, `cart-api` (Node): OpenTelemetry JS SDK, OTLP gRPC exporter, default settings.
- `billing-cron` (Python): no SDK. A helper `post_logs()` does
  `requests.post(f"{GATEWAY}/v1/logs", data=payload, timeout=2)`, writes the status code to stdout
  and returns. Nothing is ever re-sent.

## Timeline (2026-10-29)

- 14:05 Load test traffic is accidentally pointed at prod; span volume roughly triples.
- 14:06 Gateway Go heap (`otelcol_process_runtime_heap_alloc_bytes`) climbs past 1.2 GiB on all
  three pods and peaks at about 1.5 GiB. Container RSS peaks at 1.87 GiB of the 2 GiB limit.
  No pod restarts.
- 14:06–14:19 `otelcol_receiver_refused_spans` and `otelcol_receiver_refused_log_records` rise
  steadily on all pods.
- 14:06–14:19 `billing-cron` stdout shows a run of `503` responses from `/v1/logs`.
- 14:20 Load test stopped; heap falls back to ~700 MiB.

Impact: the backend has **no billing-cron logs for 14:06–14:19**. Traces from checkout-api and
cart-api for the same window are complete in the backend, only delayed by a few minutes.

## Root cause (Priya)

Once the heap crossed the hard limit, memory_limiter started dropping data to protect the process.
That is where the billing logs went. Checkout and cart were simply luckier.

## Proposed action items

1. Raise `limit_mib` from 1600 to 1950 so we never reach the hard limit again.
2. Remove `spike_limit_mib` so the limiter only reacts at the hard limit.
3. If it still drops data, take `memory_limiter` out of the logs pipeline — billing logs are
   audit-relevant and must never be dropped by the Collector.
