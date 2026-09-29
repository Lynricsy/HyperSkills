# payments-api alerting runbook (current state)

Account 111122223333, us-east-1. Application logs go to `/app/payments-api` as JSON lines
(`{"level":"ERROR","endpoint":"/charge","latency_ms":812,...}`), ~40 GB/day.

## 1. Error alarm

```bash
aws logs put-metric-filter --log-group-name /app/payments-api \
  --filter-name errors --filter-pattern '{ $.level = "ERROR" }' \
  --metric-transformations metricName=PaymentsErrors,metricNamespace=Payments,metricValue=1

aws cloudwatch put-metric-alarm --alarm-name payments-errors \
  --namespace Payments --metric-name PaymentsErrors --statistic Sum \
  --period 300 --evaluation-periods 1 --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:111122223333:oncall
```

## 2. Per-endpoint latency

We want "p90 latency of any single endpoint above 1500 ms" to page, naming the endpoint.
Current plan: add a metric filter with `endpoint` as a dimension (about 900 distinct
endpoint values, including path parameters) and one alarm per endpoint.

## 3. Weekly maintenance (Sunday 02:00-06:00 America/New_York)

The on-call engineer runs, before and after the window:

```bash
aws cloudwatch disable-alarm-actions --alarm-names payments-errors payments-latency-*
# ... maintenance ...
aws cloudwatch enable-alarm-actions  --alarm-names payments-errors payments-latency-*
```

Twice this quarter the second command was forgotten and nothing paged until Tuesday.
Also, if the service is still broken at 06:00 we want the page to go out then, not be lost.
