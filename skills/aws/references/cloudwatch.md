# CloudWatch as a product: quotas, billing and investigation

Verified against: the Amazon CloudWatch and CloudWatch Logs user guides on
docs.aws.amazon.com.

This file is the CloudWatch **product surface** — what it charges for, what its quotas are,
how to query it, and how to investigate with it. Instrumentation itself belongs elsewhere:
OpenTelemetry, Collector configuration, semantic conventions, structured logging design,
RED/USE metric selection, tracing and alerting/SLO methodology are the `observability`
skill's job. Where a local failure can be reproduced, that is the `debugging` skill's job.

## Contents

- [The three things CloudWatch bills for](#the-three-things-cloudwatch-bills-for)
- [Metric cardinality](#metric-cardinality)
- [The embedded metric format](#the-embedded-metric-format)
- [Metric resolution, retention and rollup](#metric-resolution-retention-and-rollup)
- [Logs: groups, retention and classes](#logs-groups-retention-and-classes)
- [Logs Insights](#logs-insights)
- [Alarms](#alarms)
- [Investigating with CloudWatch](#investigating-with-cloudwatch)
- [Quotas that bite](#quotas-that-bite)
- [Cross-account and cross-region](#cross-account-and-cross-region)

## The three things CloudWatch bills for

1. **Custom metrics**, charged per *distinct metric* per month, where a distinct metric is a
   unique combination of namespace, metric name and dimension values. This is the line that
   surprises people, because nobody publishes "eleven thousand metrics" on purpose.
2. **Logs ingestion**, charged per GB ingested — the dominant cost for a chatty application.
3. **Logs storage**, charged per GB per month, **forever by default**, because a log group
   created without a retention setting never expires.

API requests (`GetMetricData`, `PutMetricData`, Logs Insights scans), dashboards, alarms and
Contributor Insights each have their own charge, but the three above are where the money
usually is.

Prices vary by region and change; look them up with the Price List API rather than quoting a
remembered figure.

## Metric cardinality

Every distinct dimension value creates a new metric. Dimensions that are safe: environment,
service, region, instance type, status class. Dimensions that are not: request id, user id,
session id, pod name, full URL path, customer id in a multi-tenant system.

The arithmetic is multiplicative. Ten metric names, times four environments, times three
hundred pod names, is twelve thousand billable metrics for what a human would describe as
"ten metrics".

Fixes, in order:

- Remove the high-cardinality dimension and put the value in a **log field** instead. Logs
  are cheap per event and support high cardinality; metrics are not and do not.
- Aggregate before publishing: emit per-service, not per-instance, and let the service name
  be the dimension.
- Use Contributor Insights when the question really is "which top-N contributors", instead of
  a metric per contributor.

A metric with no data points for 15 months is deleted automatically, but that does not
refund the months it billed.

## The embedded metric format

EMF lets an application write a structured JSON log line that CloudWatch Logs parses into
metrics asynchronously. It is the right default for Lambda and container workloads:

- No `PutMetricData` call on the request path, so no added latency and no extra API cost.
- The same log event keeps the high-cardinality fields, which remain queryable in Logs
  Insights without becoming billable metrics.
- You choose which fields become dimensions in the `_aws.CloudWatchMetrics` block, so the
  billing consequence is explicit and visible in code review.

The trap is putting a high-cardinality field in the dimension list — that reproduces exactly
the cost you were avoiding, just from inside a log line.

## Metric resolution, retention and rollup

- Standard resolution is one-minute; high resolution is one-second and costs more per metric
  and per alarm.
- Data is rolled up as it ages: one-second data is kept for hours, one-minute for days,
  five-minute and one-hour data for months. Metrics older than 15 months are removed. An
  investigation into something that happened a year ago will find hourly granularity at best.
- A metric only exists once something publishes it. A dashboard or alarm referencing a metric
  that has never been published shows "no data" rather than an error, which is why
  `INSUFFICIENT_DATA` alarms so often turn out to be typos in a dimension value.

## Logs: groups, retention and classes

- **Set retention on every log group.** The default is never expire. In CloudFormation and
  CDK, create the log group explicitly with `RetentionInDays` rather than letting the service
  create it implicitly — an implicitly created group has no retention and no tags, and it
  survives stack deletion.
- **Log classes.** Standard supports all features; Infrequent Access costs less to ingest but
  supports a reduced feature set (no Live Tail, no metric filters, no subscription filters in
  the same way). It is the right class for logs kept for compliance rather than for
  investigation — check the current feature matrix before moving an operational log group.
- **Metric filters** turn a log pattern into a metric without changing the application. That
  is the cheap way to alarm on "ERROR appeared in the log" — but the resulting metric is a
  custom metric and bills like one.
- **Subscription filters** stream log events to Kinesis, Firehose or Lambda in near real time.
  This is how logs leave CloudWatch for a data lake or a third-party backend; there is a
  limit on subscription filters per log group, so a fan-out needs Firehose in the middle.
- Logs are ingested with a size limit per event and a batch limit per `PutLogEvents` call;
  an agent that silently drops oversized events is a common reason a specific stack trace
  never appears.

## Logs Insights

The query language is pipe-separated and its own thing — not SQL, not Lucene:

```
fields @timestamp, @message, @requestId
| filter @message like /ERROR/
| stats count() by bin(5m)
| sort @timestamp desc
| limit 100
```

Operational notes:

- Queries are **charged by the bytes scanned**, so always bound the time range first. A
  seven-day query over a high-volume group costs real money and is usually answerable from an
  hour.
- The CLI flow is asynchronous: `aws logs start-query` returns a query id, then poll
  `aws logs get-query-results` until `status` is `Complete`. A script that reads the first
  response gets zero rows and reports "no errors found".
- `parse` extracts fields from unstructured lines; structured JSON logs are parsed
  automatically and their fields are addressable as `field.subfield`, which is the single
  best argument for JSON logging.
- `stats` results are capped, and the display limit is not the scan limit — a `stats` over a
  wide window still scans the whole window.
- Cross-log-group queries are supported and are how you follow a request id across services.

## Alarms

- An alarm has three states, and `INSUFFICIENT_DATA` is not a failure. Choose
  `TreatMissingData` deliberately: `missing` (keep the current state) is right for a metric
  that is genuinely sparse; `breaching` is right when absence of data is itself the incident
  (a heartbeat); `notBreaching` hides real outages and is almost always wrong on an error
  metric.
- `M out of N` datapoints suppresses single-sample noise without lengthening the period.
- **Composite alarms** are how you stop an incident producing forty pages: alarm on the
  composite, keep the children for diagnosis. They are also cheaper than an alarm per child
  with its own action.
- **Anomaly detection** bands fit a model to the metric's own history and are the right tool
  for "unusual for this time of day" where a static threshold would fire every Monday.
- Alarm on the signal a user would notice — error rate, latency percentile, queue age — not
  on CPU. CPU alarms fire during healthy load and stay quiet during a deadlock.
- Route actions to SNS and let the routing live downstream. An alarm wired directly to one
  email address is an alarm that stops working when that person leaves.

## Investigating with CloudWatch

A workable sequence when production is misbehaving and you cannot reproduce it locally:

1. **Scope it in time.** Find the first bad minute from the metric, not from the ticket.
2. **Scope it in space.** Which service, which region, which AZ, which version. Metric
   dimensions answer this faster than logs.
3. **Correlate the deploy.** CloudTrail and the deployment pipeline; most incidents start
   with a change.
4. **Go to logs only with a filter.** A request id, an error class, a customer id — from the
   metric or the trace, not by scrolling.
5. **Use Live Tail** for a fault you can still provoke, and Logs Insights for one that has
   already happened.
6. **Check the service's own control-plane signals** before blaming the application: ECS
   Action Logs, CloudFormation events, Health Dashboard, Service Quotas utilisation.

The quota question is worth asking early: many "the application got slow" incidents are a
throttle, and throttles appear as service metrics (`ThrottledRequests`, `Throttles`, `4XX`)
rather than as application errors.

## Quotas that bite

- `PutMetricData` has a per-request payload limit and an account-level transactions-per-second
  limit; a fleet publishing one metric per instance per second hits the second one, and the
  failure is a throttling error on the publish path.
- `GetMetricData` limits the number of metrics per request and the data points returned; a
  dashboard with hundreds of widgets throttles itself.
- Dimensions per metric, alarms per account, and log groups per account are all bounded and
  all adjustable. Check with Service Quotas rather than discovering it at scale.
- CloudWatch Logs has a per-log-stream sequencing model; a very high write rate to one stream
  is slower than the same volume spread over streams.

## Cross-account and cross-region

CloudWatch cross-account observability links monitoring accounts to source accounts, so
metrics, logs and traces from many accounts are queryable in one place. Set it up at the
organisation level rather than per account, and remember that it is a read path: it does not
move data, and the source account still pays for ingestion and storage.

Dashboards can span regions; alarms cannot. An alarm evaluates a metric in its own region,
so a multi-region workload needs the alarm replicated per region, with a composite or an
SNS fan-in if you want a single notification.

<!-- sources: awesome-copilot-aws, aws-agent-toolkit, aws-docs -->
