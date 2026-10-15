# Node overview dashboard - migration to Elasticsearch

We are retiring our Prometheus server. Metrics now arrive in Elasticsearch 9.5.3 through Prometheus
remote write into the `metrics-prometheus-default` time series data stream. Grafana will use the
Prometheus data source pointed at Elasticsearch's Prometheus-compatible API, and a few panels will move
to Kibana ES|QL.

Grafana data source settings we plan to keep: exemplars enabled (trace links), "Custom query parameters"
= `lookback_delta=2m&dedup=true`.

| Panel | PromQL today |
|---|---|
| 1. Memory available ratio per node | `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` |
| 2. Request rate of healthy targets | `sum by (job) (rate(http_requests_total[5m])) and on(job) up == 1` |
| 3. Peak 1h request rate | `max_over_time(rate(http_requests_total[1m])[1h:])` |
| 4. Targets down | `up == 0` |
| 5. p95 latency | `histogram_quantile(0.95, sum by (le, job) (rate(http_request_duration_seconds_bucket[5m])))` |

Panel 4 must show a node as down within a minute of its exporter disappearing.

Ask: which panels will work unchanged, rewrite the ones that will not, and give the Kibana ES|QL
version of panel 1 for the new capacity dashboard.
