# Signals and the OpenTelemetry data model

Verified against: OpenTelemetry semantic conventions v1.44.0, otelcol-contrib 0.160.0.

## Contents

- [Which signal answers which question](#which-signal-answers-which-question)
- [Where an attribute lives](#where-an-attribute-lives)
- [Resource identity](#resource-identity)
- [`schema_url`](#schema_url)
- [Context propagation](#context-propagation)
- [The three joins](#the-three-joins)
- [Exemplars](#exemplars)
- [Metric instruments and temporality](#metric-instruments-and-temporality)
- [What each signal cannot tell you](#what-each-signal-cannot-tell-you)

## Which signal answers which question

| Signal | The question it answers | Cost shape | Fails by |
|---|---|---|---|
| Metric | How often, how fast, how many — in aggregate | Fixed per series, independent of traffic; grows with *label combinations* | Cardinality explosion; aggregation that hides the tail |
| Trace | Where the time or the failure entered a request that crossed several components | Per request; usually sampled | Sampling that discards the interesting request; broken context; cardinality in span names |
| Log record | What exactly happened in this one case, with the specifics | Per event; grows linearly with traffic | Unstructured text; no correlation key; secrets |

The short form: a metric tells you *that* something is wrong, a trace tells you *where*, a log
record tells you *why*. Three signals that each answer the same question are three bills for one
capability. Before adding one, name the question it answers and check no existing signal already
answers it.

A useful ordering when instrumenting something new: metrics first (they are what alerts fire on),
then traces (they are what turns an alert into a location), then log records at the specific
points the trace cannot explain. Instrumenting in the other order produces a log stream that is
expensive to store and impossible to alert on.

## Where an attribute lives

OpenTelemetry has three places to hang a key-value pair, and the choice is not cosmetic:

| Level | Scope | Set by | Examples |
|---|---|---|---|
| Resource | The entity producing telemetry; identical on every record from that process | SDK at startup, or a Collector processor | `service.name`, `service.version`, `deployment.environment.name`, `host.name`, `k8s.pod.name` |
| Instrumentation scope | The library or module that emitted the record | The instrumentation itself | scope name and version |
| Record | This span, data point or log record | Instrumentation or application code | `http.route`, `db.operation.name`, `order.id` |

Putting a resource-level fact on every record wastes bytes and invites drift between records that
should agree. Putting a record-level fact on the resource is worse: it becomes part of the
producing entity's identity, which for metrics means a new time series per value.

The most common mistake is a per-request value promoted to the resource — a tenant or user
identifier set once on the resource because it was convenient at startup. Everything that
resource produces is now a distinct series.

## Resource identity

Four attributes decide whether a backend can tell your services apart:

- `service.name` — required. Without it, SDKs fall back to `unknown_service`, and every
  unnamed process in the fleet merges into one node on the service map.
- `service.namespace` — disambiguates two services that share a name in different teams or
  clusters.
- `service.version` — makes "did this start with the deploy?" answerable.
- `service.instance.id` — distinguishes replicas; needed for per-instance metrics to make sense.

These belong to the producer. Set them in the SDK or in the deployment manifest (for example from
the Kubernetes downward API), and let nothing downstream overwrite them. A Collector that
`upsert`s `service.name` is not enriching, it is erasing; `insert` is the correct action for
identity attributes, so SDK-set values win and only genuinely missing ones get filled.

`deployment.environment.name` is the correct current key. `deployment.environment` has been
deprecated since semantic conventions v1.27.0, and instrumentation or dashboards still using it
will silently fail to match records from a current SDK.

## `schema_url`

Every resource and instrumentation scope can carry a `schema_url` that names the semantic
convention version the record was written against — for example
`https://opentelemetry.io/schemas/1.40.0`. This is observable: with a `debug` exporter at
`verbosity: detailed`, a Collector 0.160.0 prints it directly:

```
ResourceSpans #0
Resource SchemaURL: https://opentelemetry.io/schemas/1.40.0
Resource attributes:
     -> service.name: Str(exp-svc)
```

Treat it as the ground truth for "which convention version is this stream speaking". When two
services disagree about an attribute name, comparing their `schema_url` values is faster than
reading either one's dependency tree. [verified]

## Context propagation

A trace survives a process boundary only if the context crosses it. In-process, the active span
lives in a context that the SDK attaches to the current execution; across processes it travels as
the W3C `traceparent` header (and optionally `tracestate`).

The boundaries that break traces in practice are the ones with no HTTP request in them:

- Queue and topic messages — the context must be written into message metadata by the producer and
  extracted by the consumer. Most messaging instrumentation does this; hand-rolled publishers do
  not.
- Scheduled and batch work — there is no incoming context at all, so the job must start a new
  trace deliberately rather than inherit whatever context happened to be active.
- Manually managed threads, worker pools and callbacks — anything that escapes the runtime's own
  context mechanism.
- Anything that re-serialises a request, such as a proxy or gateway that constructs a fresh
  outbound call without copying headers.

The symptom of a broken boundary is not an error; it is a trace that ends where the boundary was,
plus a second trace that starts there with no parent. When traces look suspiciously shallow, look
for the boundary rather than for missing instrumentation.

## The three joins

Correlating signals is entirely a matter of shared keys. There are three joins worth designing
for, and each one fails in a recognisable way when its key is absent:

| Join | Key | Without it |
|---|---|---|
| Log record → trace | `trace_id` (and `span_id`) on the log record | The only grouping left is time plus pod name; interleaved requests cannot be separated |
| Metric → trace | An exemplar carrying `trace_id` on the sample | A latency spike on a chart has no example request behind it |
| Any signal → service | Consistent resource attributes across all three | The same service appears under different identities per signal |

The first is the one that decides how an incident goes. Emitting `trace_id` and `span_id` on every
log record written inside a span costs two fields and turns "find the request this customer
complained about" from archaeology into a filter.

## Exemplars

An exemplar attaches a `trace_id` (or any key-value pair) to a specific metric sample without
adding a label dimension. This is the escape hatch for high-cardinality correlation data:
identifiers that are useful when you need one example, and ruinous as a label.

Exemplars need Prometheus 2.26+ on the store side and an exemplar-capable exchange format; they
are read through a UI's exemplar support rather than through aggregation in a query. `trace_id`
and a debug identifier are exactly what belongs there. [official]

## Metric instruments and temporality

Pick the instrument by what the value *is*, not by what is convenient to compute:

| Instrument | Use for | Trap |
|---|---|---|
| Counter | Monotonic totals — requests, errors, bytes | Exporting a rate you computed yourself; let the query do it |
| UpDownCounter | Values that rise and fall — queue depth, active connections | Using a counter and getting negative rates |
| Gauge | A current measurement — temperature, utilisation | Aggregating gauges across instances as if they summed |
| Histogram | Distributions — latency, payload size | Every label multiplies by the bucket count; averages read off `_sum/_count` |

Temporality matters at the export boundary: delta temporality reports what changed in an interval,
cumulative reports a running total. Prometheus-style stores expect cumulative; some vendor
backends expect delta. A mismatch does not error — it produces graphs that either ramp forever or
reset constantly. Decide it once, at the exporter, and write down which one the backend wants.

Read percentiles, never averages. An average latency of 800 ms is compatible with everyone being
served in 800 ms and with 99% being served in 100 ms while 1% wait 70 seconds. The second case is
the one that produces support tickets, and the average cannot distinguish them.

## What each signal cannot tell you

Stating the limit is part of the answer:

- **Sampled traces cannot establish rates.** If 5% of traces are kept, the number of error traces
  is not the number of errors, and the ratio is only unbiased if the sampling was unbiased —
  which tail sampling deliberately is not.
- **Metrics cannot identify an instance of a problem.** They aggregate by construction; without an
  exemplar there is no path from the spike to a request.
- **Logs cannot establish rates cheaply.** Counting log lines to get an error rate works until the
  log pipeline drops records under load, at which point the rate silently improves.
- **A trace cannot prove causation.** It shows where time was spent and where an error surfaced.
  A slow database span may be a slow database, or a saturated connection pool, or a neighbour
  saturating the disk.
- **None of them cover what was never instrumented.** The absence of a signal is not evidence of
  the absence of a failure, and this is the most common reasoning error in an incident.

<!-- sources: otel-docs, dash0-agent-skills, addyosmani-agent-skills, grafana-skills, o11y-dev-otel, otel-semconv, otel-collector-contrib, prometheus -->
