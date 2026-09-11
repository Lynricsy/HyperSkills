# Pager output — checkout-api, 03:41 UTC

Alert: `checkout-api latency SLO burn rate > 14.4x (1h window)`

## What the on-call has

OpenTelemetry only. No profiler, no local reproduction, no failing test.

### Metrics (Prometheus / OTLP)

| Metric | 03:00 | 03:41 |
|---|---|---|
| `http.server.request.duration` p50 | 48 ms | 61 ms |
| `http.server.request.duration` p99 | 210 ms | 4 900 ms |
| `http.server.active_requests` | 22 | 310 |
| `db.client.connections.usage{state="used"}` | 9 | 40 (pool max 40) |
| `db.client.connections.pending_requests` | 0 | 268 |
| `process.runtime.jvm.gc.duration` | 12 ms/min | 15 ms/min |

### One exemplar trace (`trace_id=8f1c2a...`, 4 812 ms wall)

```
POST /v2/checkout/confirm                       4812 ms
├── middleware.auth                                6 ms
├── cart.load                                     11 ms
├── pricing.quote                                 18 ms
├── payments.authorize (HTTP client)             120 ms
└── orders.persist                              4650 ms
    ├── db.connect  (span attr: pool.wait_ms=4380) 4381 ms
    └── db.query INSERT INTO orders …              9 ms
```

### Log sample (structured, ECS-ish)

```
{"@timestamp":"...T03:41:12Z","log.level":"WARN","service.name":"checkout-api","message":"connection pool exhausted","pool.pending":268,"trace.id":"8f1c2a..."}
```

## Question for the assistant

I have the alert, the metric series above and this one exemplar trace. Nothing
reproduces locally. Walk me from this alert back to the specific code path I
should be changing, and tell me what instrumentation is missing so that next
time the signal points at the code directly.
