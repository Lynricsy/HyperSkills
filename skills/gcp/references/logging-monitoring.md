# Cloud Logging and Cloud Monitoring: the product surface

Scope: the Google Cloud products — query language, buckets, sinks, retention, quotas and what
each line of the bill is. Instrumentation with OpenTelemetry, Collector configuration,
semantic conventions, RED/USE metric design, SLOs and alert-routing policy are the
`observability` skill's subject and are not repeated here.

Verified against: Google Cloud SDK 584.0.0 (`gcloud logging` help text quoted below is from
that release); retention, quota and pricing figures from cloud.google.com.

## Contents

- [Reading logs without getting an empty answer](#reading-logs-without-getting-an-empty-answer)
- [Query language](#query-language)
- [Resource types you will actually use](#resource-types-you-will-actually-use)
- [Audit logs](#audit-logs)
- [Buckets, views and retention](#buckets-views-and-retention)
- [Sinks](#sinks)
- [What logging costs](#what-logging-costs)
- [Log-based metrics](#log-based-metrics)
- [Monitoring: metric kinds and alignment](#monitoring-metric-kinds-and-alignment)
- [Monitoring quotas that bite](#monitoring-quotas-that-bite)
- [Metrics scopes](#metrics-scopes)

## Reading logs without getting an empty answer

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="checkout-api" AND severity>=ERROR' \
  --project=PROJECT_ID --freshness=7d --order=asc --limit=200 \
  --format="table(timestamp, severity, textPayload, jsonPayload.message)"
```

**`--freshness` defaults to `1d`.** A query for an incident four days ago, with a perfectly
correct filter, returns nothing and exits zero. There is no warning and no error. This is the
single most common reason an agent concludes "the logs are gone" when they are not — and
adding `timestamp >= "..."` to the filter does **not** override it, because the freshness
window is applied in addition to the filter.

Also: `--order` defaults to `desc` (newest first), so a `--limit=10` on an incident window
returns the *end* of the incident, not the beginning. Use `--order=asc` when you want the
first failure.

## Query language

Logging Query Language, not SQL and not PromQL:

- **Double quotes only.** `severity="ERROR"`. Single quotes are not string literals in LQL —
  they are how you escape a field path with special characters.
- Boolean operators uppercase: `AND`, `OR`, `NOT`. Parenthesise anything mixed; `AND` binds
  tighter than `OR` and relying on that is how filters silently widen.
- `=` is exact match, `:` is "has / contains" (substring for strings, key presence for
  structs), `=~` is a RE2 regex match and `!~` its negation.
- `severity>=ERROR` works as an ordered comparison; the severity ladder is
  `DEFAULT < DEBUG < INFO < NOTICE < WARNING < ERROR < CRITICAL < ALERT < EMERGENCY`.
- Absent field: `NOT field:*`. There is no `IS NULL`.
- `SEARCH("text")` does a global tokenised search across the entry, and
  `SEARCH(field, "text")` scopes it to a field.

When you do not know the exact JSON path, do not guess `jsonPayload.foo.bar` — a wrong path
matches nothing silently. Pull one entry first and read its shape:

```bash
gcloud logging read 'resource.type="cloud_run_revision"' \
  --project=PROJECT_ID --freshness=7d --limit=1 --format=json
```

## Resource types you will actually use

| Service | `resource.type` | Key labels |
|---|---|---|
| Cloud Run service | `cloud_run_revision` | `service_name`, `revision_name`, `location` |
| Cloud Run job | `cloud_run_job` | `job_name` |
| GKE | `k8s_container`, `k8s_pod`, `k8s_node`, `k8s_cluster` | `cluster_name`, `namespace_name`, `pod_name`, `container_name` |
| Cloud SQL | `cloudsql_database` | `database_id` = `PROJECT:INSTANCE` |
| Compute Engine | `gce_instance` | `instance_id` (**numeric**), `zone` |
| Load balancer | `http_load_balancer`, `internal_http_lb_rule` | `forwarding_rule_name`, `url_map_name` |
| Cloud Storage | `gcs_bucket` | `bucket_name` |
| API enable/disable, quota | `audited_resource` | `service` |

Two traps in that table. `gce_instance` labels carry the numeric `instance_id`, not the
instance name — comparing a name against it matches nothing; use
`resource.labels.instance_name` where present or `SEARCH("my-instance")`. And internal HTTP
load balancers log under `internal_http_lb_rule`, not `http_load_balancer`, so a filter on
the latter silently excludes them.

## Audit logs

Four kinds, and only one of them is on for free:

| Kind | Default | Content |
|---|---|---|
| Admin Activity | always on, free, cannot be disabled | who created/modified/deleted a resource |
| System Event | always on, free | Google-initiated actions |
| Policy Denied | on when it occurs, billed | requests denied by a security policy |
| Data Access | **off** except for BigQuery, billed | who read or wrote data |

"Who deleted this bucket" is answerable out of the box. "Who read this object" is only
answerable if Data Access logging was turned on *before* it happened — that is a
`gcloud projects set-iam-policy` on the audit config, decided in advance.

Audit entries live under `protoPayload` with `logName` ending in
`cloudaudit.googleapis.com%2Factivity` or `%2Fdata_access`:

```
logName="projects/PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity"
AND protoPayload.authenticationInfo.principalEmail="someone@example.com"
AND SEARCH(protoPayload.methodName, "storage.buckets.delete")
```

Use `SEARCH()` on `methodName` rather than `=`: the recorded value carries a service and
version prefix that varies (`google.cloud.run.v2.Services.DeleteService`,
`storage.buckets.delete`), so exact match fails on a correctly guessed verb. Do not use `:`
either — substring matching produces false positives across similarly named methods.

## Buckets, views and retention

| Bucket | Level | Default retention | Configurable |
|---|---|---|---|
| `_Required` | project, folder, org | **400 days** | no — and it cannot be deleted or filtered |
| `_Default` | project | 30 days | yes, 1–3650 days |
| `_Default` | folder, org | 30 days | no |
| user-defined | project | 30 days | yes, 1–3650 days |

`_Required` holds Admin Activity and System Event audit logs, free, for 400 days. Everything
else lands in `_Default` unless a sink routes it elsewhere.

Extending retention on a folder- or organization-level bucket is not possible. The supported
pattern is a sink from the folder/org into a **project-level** bucket whose retention you then
set.

Shortening a bucket's retention has a 7-day grace period before the expired entries are
physically deleted — but they are unqueryable immediately, so shortening retention is
effectively irreversible from the operator's point of view.

**Log views** scope who can read what inside one bucket (`_AllLogs`, `_Default`, plus custom
views with a filter). That is how you let a team read their own service's logs from a shared
bucket without granting `roles/logging.viewer` on everything.

## Sinks

A sink = a filter + a destination (log bucket, BigQuery dataset, Cloud Storage bucket,
Pub/Sub topic). Every sink has a **writer identity** — a service account that Logging creates
— and that identity must be granted write access on the destination, or the sink silently
drops everything.

```bash
gcloud logging sinks create prod-errors \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/log_analysis \
  --project=PROJECT_ID \
  --log-filter='severity>=ERROR AND resource.type="cloud_run_revision"' --quiet

# read back the writer identity, then grant it on the destination
gcloud logging sinks describe prod-errors --project=PROJECT_ID \
  --format="value(writerIdentity)"
```

- **Aggregated sinks** at folder or organization level with `--include-children` capture logs
  from every project below. That is the mechanism for a central security log project; a
  per-project sink in 200 projects is not.
- Routing a log **does not stop it being ingested into `_Default`**. To avoid paying twice,
  add an exclusion filter on the `_Default` sink
  (`gcloud logging sinks update _Default --add-exclusion=...`).
- The `_Required` sink cannot be modified or excluded.

## What logging costs

- **$0.50 per GiB ingested**, with the first **50 GiB per project per month free**. The charge
  includes 30 days of storage.
- Retention beyond 30 days: **$0.01 per GiB per month**.
- `_Required` audit logs are free and do not count against the allotment.
- Vended network logs (VPC flow logs, firewall logs, Cloud NAT logs) are $0.25/GiB.

The bill is driven by volume, so the cheap controls are upstream: exclusion filters on
`_Default` for health-check and load-balancer noise, sampling with a
`sample(insertId, 0.1)` exclusion condition, and not logging request bodies at INFO. Turning
on Data Access audit logs organization-wide without an exclusion is the classic way to
multiply a logging bill overnight.

## Log-based metrics

Two shapes: **counter** (count entries matching a filter) and **distribution** (extract a
numeric value and bucket it). They are the bridge from "we log it" to "we can alert on it"
without changing the application.

The failure mode is label cardinality. A label extracted from a user ID, a request ID or a
full URL path produces one time series per distinct value, and you pay per time series while
the charts become unusable. Extract the status code and the route template, never the
identifier.

System-defined log-based metrics exist already for common cases (`logging.googleapis.com/
byte_count`, error counts); check before defining a duplicate.

## Monitoring: metric kinds and alignment

Three metric kinds, and the difference decides what a chart means:

| Kind | Value | Needs |
|---|---|---|
| `GAUGE` | a measurement at a point in time | no alignment beyond a reducer |
| `DELTA` | change over the sampling interval | sum-align to get a rate |
| `CUMULATIVE` | a monotonically increasing total since a start time | must be rate-aligned; reading the raw value is meaningless |

Charting a `CUMULATIVE` counter without an aligner gives an ever-rising line that tells you
nothing; the alignment period is also what smooths or hides a spike, and an alignment period
longer than the alert's evaluation window makes the alert unable to fire quickly.

Query languages: **PromQL** is the current recommendation and is what Managed Service for
Prometheus speaks; **MQL** still works and is what older dashboards contain. Use PromQL for
new work.

Google Cloud system metrics (`run.googleapis.com/*`, `cloudsql.googleapis.com/*`,
`kubernetes.io/*`) are free to ingest. Custom metrics and Managed Service for Prometheus
samples are billed per sample, which is why cardinality is a cost problem and not only a
usability one.

## Monitoring quotas that bite

| Limit | Value |
|---|---|
| Custom metric descriptors per project | 10,000 |
| Labels per custom metric descriptor | 30 |
| Write rate per single time series | one point per 5 seconds |
| Time series per write request | 200 |

Exceeding the write rate for one time series returns an error for the extra points and drops
them — which looks like a gap in the chart, not like a quota error, unless you are reading the
client's error log.

## Metrics scopes

A **metrics scope** is what a Cloud Monitoring workspace can see. By default a project's scope
is itself. Adding other projects as monitored projects lets one dashboard span an entire
environment; a project can be monitored by several scopes, and the scoping project is where
dashboards and alert policies live.

Set this up before building dashboards. Rebuilding a dashboard because it was created in the
wrong scoping project is pure rework.

<!-- sources: gcp-docs, google-skills -->
