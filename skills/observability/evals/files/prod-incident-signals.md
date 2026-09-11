# Incident 2026-08-19 — what we have

Nothing reproduces locally or in staging. Everything below came out of the
production observability stack.

## 1. Pager

`ErrorCount` fired at 14:07 UTC. Checkout 5xx rate went from 0.2% to 6.1% and
stayed there for 41 minutes, then recovered on its own.

## 2. Log records (sample, from Loki, `{namespace="checkout"}`)

```
{"ts":"2026-08-19T14:07:11.402Z","level":"error","msg":"payment failed for order 88213 user u_91043: upstream timeout","pod":"checkout-7c9f4-2xql"}
{"ts":"2026-08-19T14:07:11.884Z","level":"error","msg":"payment failed for order 88214 user u_20117: upstream timeout","pod":"checkout-7c9f4-2xql"}
{"ts":"2026-08-19T14:07:12.006Z","level":"info","msg":"charge ok","pod":"checkout-7c9f4-hh8m"}
{"ts":"2026-08-19T14:07:13.771Z","level":"error","msg":"payment failed for order 88219 user u_44810: upstream timeout","pod":"checkout-7c9f4-2xql"}
```

There is no `trace_id` on any log record. `pod` is the only field we can group by.

## 3. Traces

Tempo has traces for the window, but a search for `service.name="checkout"` with
`status=error` returns 11 traces for a 41-minute window in which the error rate
metric implies roughly 190,000 failed requests. Most of the 11 have a root span
of kind `CLIENT` named `charge_provider_88213`, `charge_provider_88214`, and so
on — one distinct span name per order.

The collector agent config for this cluster sets
`tail_sampling.decision_wait: 5s` and a `probabilistic` baseline of 5%.

## 4. Metrics

`checkout_latency` has stopped returning data for the last 3 days:

```
$ curl -s http://prometheus.monitoring:9090/api/v1/status/tsdb | jq '.data.seriesCountByMetricName[:4]'
[
  {"name": "checkout_latency_bucket", "value": 2841190},
  {"name": "payment_attempts",        "value": 508117},
  {"name": "http_requests_total",     "value": 61204},
  {"name": "kube_pod_labels",         "value": 44018}
]
$ curl -s http://prometheus.monitoring:9090/api/v1/status/tsdb | jq '.data.labelValueCountByLabelName[:4]'
[
  {"name": "user_id",       "value": 402118},
  {"name": "order_id",      "value": 391004},
  {"name": "error_message", "value": 8841},
  {"name": "path",          "value": 6620}
]
```

Prometheus was OOMKilled twice on 2026-08-17 and the checkout dashboards have
been timing out since.

## 5. What we tried

Someone added this to the scrape job at 14:30 to "stop the bleeding". The 5xx
rate graph went flat and `rate(http_requests_total[5m])` started returning values
in the hundreds of thousands.

```yaml
metric_relabel_configs:
  - regex: (pod|instance|user_id|order_id)
    action: labeldrop
```
