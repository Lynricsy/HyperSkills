---
name: observability
description: "Instruments production systems with OpenTelemetry traces, metrics, logs, SLOs and alerts."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

# observability

## Scope

Covers telemetry as a production capability: the OpenTelemetry data model and how traces, metrics
and logs are joined; SDK instrumentation (automatic versus manual, context propagation, span
naming, kind, status and attributes, error recording); semantic conventions — which are stable,
which still move, and how an instrumentation library switches between them; Collector pipelines
(receivers, processors, exporters, connectors, ordering, memory limits, agent versus gateway
deployment, head and tail sampling); metric cardinality as a cost and a correctness problem;
structured logging and its correlation to traces; RED and USE metrics; SLOs, error budgets and
burn-rate alerting; and the workflow that gets from an alert back to a line of code.

Where a local failure can be reproduced, use the `debugging` skill; where only production signals exist (logs, metrics, traces, alerts), this is the `observability` skill's job.

Collector facts in this skill are written against **otelcol-contrib 0.160.0** and semantic
conventions **v1.44.0**; rules that depend on a newer component than that carry a gate such as
`(Collector 0.156+)`.

Not covered:

- Cloud monitoring **products**: CloudWatch, Azure Monitor / Application Insights, Google Cloud
  Logging and Monitoring — their quotas, billing, agents, console workflows and IAM. Use the
  `aws`, `azure` or `gcp` skill. What this skill owns is the vendor-neutral layer: OTel
  instrumentation, Collector configuration, semantic conventions, structured logs, RED/USE,
  tracing, alerting and SLOs.
- Elasticsearch index design, mapping, ILM and query DSL. Use the `elasticsearch` skill; this
  skill covers the collection and alerting pipeline that feeds it, not the store.
- Kubernetes manifests, Helm charts and container images for the Collector itself. Use the
  `containers` skill. This skill covers what the Collector config must say and why.
- Review and testing methodology. Use `code-review` and `test-driven-development`. The only
  testing here is asserting on telemetry a change produces.
- Observing AI agents and LLM calls (`gen_ai.*` conventions), and continuous profiling as a
  fourth signal. No skill in this library covers either yet; say so rather than improvising.

Paths below are relative to this skill's directory.

## Core rules

1. Name the questions before emitting anything. Write down the two to four questions an on-call
   engineer will ask about this code path, and keep only signals that answer one of them.
   Telemetry with no question behind it is cost without capability.
2. Choose the signal by the question, not by habit: a metric answers *how often and how fast* in
   aggregate, a trace answers *where the time or the failure went*, a log record answers *what
   exactly happened in this one case*. Each has a different cost curve
   (`references/signals-and-data-model.md`).
3. Every log record emitted inside a span carries that span's `trace_id` and `span_id`. Without
   them a log line cannot be pivoted to its trace, and an incident degrades to grepping by pod
   name (`references/structured-logging.md`).
4. Span names must be low-cardinality: the route template, not the URL; the table, not the query;
   the operation, not the outcome. `charge_provider_88213` is one span name per order, which
   destroys every operation-level view (`references/instrumentation.md`).
5. Span status depends on span kind. On a `SERVER` span a 4xx is not an error — the server
   answered a bad request correctly — so leave it `UNSET`; on the corresponding `CLIENT` span the
   same 4xx is an error. Set `OK` only where the code has confirmed success, never speculatively.
6. Record exceptions as a log record inside the active span context, carrying `exception.type`,
   `exception.message` and `exception.stacktrace`, rather than `span.recordException`. The Span
   Event API is on a published deprecation path (OTEP 4430) in favour of log-based events.
7. Leave the SDK sampler at its default `AlwaysOn` and sample in the Collector. A head decision is
   made before the request's outcome is known, so `TraceIdRatioBased(0.05)` discards errors and
   latency outliers at the same 95% rate as everything else. The one escape hatch is a hop whose
   cost is itself unacceptable (egress billing, Lambda invocations) — and then say out loud that
   the tail is being sacrificed (`references/sampling.md`).
8. Materialise RED metrics from spans **before** any sampling step, with a connector. Rate and
   error rate computed after head sampling are scaled down; after tail sampling they are biased
   towards errors. Both are wrong, in opposite directions.
9. Never remove, at scrape or relabel time, a label that makes a series unique — not `pod`, not
   `instance`, not an identifier. Collapsing distinct series interleaves their counter resets, so
   `rate()` and `increase()` return absurd values, multiple samples land on one series per scrape,
   and there is no config error and no trace left in the data. Fix the source or aggregate
   post-ingest instead (`references/cardinality.md`).
10. The safe scrape-time drop is an entire metric by `__name__`. That discards a whole metric
    rather than merging series, and it is a deliberate, visible loss.
11. Unbounded values — user, order, request or trace identifiers, error message text, raw URLs —
    are never metric labels. They belong on spans, in log records, or in exemplars, which attach
    a `trace_id` to a sample without adding a dimension (Prometheus 2.26+).
12. A histogram multiplies its label cardinality by roughly the bucket count plus three, so
    trimming one label off a histogram is worth an order of magnitude more than trimming one off
    a counter. Native histograms (Prometheus 2.40+) replace the bucket family with one sparse
    series.
13. Put `memory_limiter` first in every processor list, so backpressure applies before anything
    else allocates. The Collector does not check this: a config with it last starts cleanly with
    no warning, and the cost arrives later as an OOM. This is a review gate, not a CI gate.
14. `memory_limiter.limit_mib` is compared against the Go heap, not process RSS, so the container
    memory limit must sit meaningfully above it — otherwise the kernel OOM-kills the process
    before the limiter ever refuses anything.
15. The `otlp` receiver's default endpoint is `localhost` (127.0.0.1:4317 and :4318). A
    containerised Collector that omits `endpoint` binds to loopback and receives nothing from
    other pods; write `0.0.0.0` explicitly.
16. Tail sampling needs every span of a trace at one instance. That means a gateway tier fed by a
    `load_balancing` exporter hashing on trace ID, behind a headless Service so DNS returns pod
    IPs. `tail_sampling` on a DaemonSet agent decides each node's fragment separately.
17. `decision_wait` is a deadline, not a hint: traces have no end marker, so when it expires the
    processor decides on whatever arrived. Set it above the p99 duration of the slowest operation
    being sampled, and remember memory scales with
    `decision_wait × traces/sec × spans/trace`.
18. Treat resource identity (`service.name`, `service.namespace`, `service.version`,
    `service.instance.id`) as owned by the SDK or the deployment manifest. A Collector `resource`
    processor that `upsert`s `service.name` silently collapses every service into one; use
    `insert` for identity attributes and reserve `upsert` for genuinely Collector-side facts such
    as `k8s.cluster.name`.
19. Check the stability of each convention before depending on it, and migrate deliberately:
    instrumentation switches with `OTEL_SEMCONV_STABILITY_OPT_IN`, where `<category>` moves to the
    stable set and `<category>/dup` emits both for a phased rollout (`/dup` wins when both are
    present). Read `schema_url` on the resource to learn which version a stream is actually
    speaking (`references/semantic-conventions.md`).
20. Alert on symptoms a user feels, not on causes. CPU, memory, disk and pod restarts belong on a
    dashboard; failed and slow requests belong on the pager. Cause alerts fire when nothing is
    wrong and stay silent for the failure nobody predicted
    (`references/alerting-and-slos.md`).
21. Alert on ratios and burn rates, never on counts. `increase(errors[5m]) > 100` fires on a busy
    afternoon and stays quiet during a traffic collapse.
22. An SLO whose alert window equals its compliance window cannot page in time — it fires once the
    budget is already gone. Page on a fast burn measured over hours with a short confirmation
    window, and ticket on a slow burn measured over days.
23. Every paging alert has a `for:` duration, a runbook link, and exactly one of two severities
    (page now / ticket this week). More tiers become a sorting exercise; a rotation paged more
    than once or twice a week stops reading the pager.
24. Verify the telemetry itself before calling the work done: trigger the failure path, find it by
    its correlation ID, confirm the fields are structured, follow one request end to end with no
    broken spans, and fire each new alert once. Instrumentation is code and can be wrong.
25. Say what the available signals cannot conclude. Sampled traces, a metric with no exemplars and
    a log stream with no trace correlation together support far fewer claims than they appear to;
    naming the gap is the answer, not a failure to answer.

## Workflows

### instrument-a-service

- [ ] Write the on-call questions first, then map each planned signal to one of them. Drop
      anything that maps to none (`references/signals-and-data-model.md`).
- [ ] Turn on automatic instrumentation before writing any manual span, and check what it already
      produces — a second manual span wrapping an auto-instrumented one only adds nesting
      (`references/instrumentation.md`).
- [ ] Set resource identity once, at the SDK or in the deployment manifest: `service.name`,
      `service.version`, `service.namespace`, `deployment.environment.name`.
- [ ] Add manual spans only for meaningful units of work, with low-cardinality names, the right
      kind, status set per the kind rules, and the domain attributes on-call will filter by.
- [ ] Wrap every headless entry point — cron, worker, CLI, consumer — in an explicit `SERVER` or
      `INTERNAL` root span, or the first outbound call becomes a parentless `CLIENT` root span.
- [ ] Emit structured logs with stable event names, a correlation ID, an entry-point field, and
      `trace_id`/`span_id` inside spans; allowlist the fields so no secret or PII can ride along
      (`references/structured-logging.md`).
- [ ] Add RED metrics for each endpoint and each outbound dependency with bounded label sets, and
      USE metrics for each pool or queue; attach exemplars instead of identifier labels.
- [ ] Flush on shutdown: handle `SIGTERM`, call the SDK's shutdown, and accept that `SIGKILL` and
      OOM kills bypass it.
- [ ] **Gate — the telemetry was observed, not assumed:** an induced failure in a non-production
      environment is located from telemetry alone, without reading the source; one request is
      followed end to end with no broken spans; every new metric series appears with exactly the
      intended labels.

### review-a-collector-config

- [ ] Establish the version first (`otelcol --version`, or the image tag). Component names,
      defaults and stability all move between releases, so a rule without a version is a guess
      (`references/collector-pipelines.md`).
- [ ] Check the ingress: is every `otlp` protocol block given an explicit `0.0.0.0` endpoint, and
      is TLS or authentication present on any hop that leaves the node?
- [ ] Check processor order per pipeline: `memory_limiter` first, enrichment next
      (`resource_detection`, `k8s_attributes`), static `resource` after it, redaction after
      enrichment, drops and transforms last.
- [ ] Check identity: nothing `upsert`s `service.*`; `k8s_attributes` associates on
      `k8s.pod.uid` first with connection only as fallback; the ServiceAccount actually has the
      RBAC the processor needs, since it fails silently without it.
- [ ] Check the sampling topology: where the decision is made, whether whole traces converge
      there, whether `decision_wait` exceeds the slowest operation, and whether RED metrics are
      materialised upstream of it (`references/sampling.md`).
- [ ] Check durability and memory: `sending_queue` with `file_storage` if a restart must not lose
      data, `limit_mib` below the container limit with headroom, and the internal metrics
      endpoint bound to `0.0.0.0` so it can be scraped.
- [ ] Check what is wired that should not be — a `debug` exporter on a production pipeline prints
      every record to stdout. A component that is declared but referenced by no pipeline is
      harmless clutter, not a startup error.
- [ ] **Gate — the config was executed, not read:** `otelcol validate --config <file>` exits 0,
      then the collector starts and `telemetrygen` plus a temporary `debug` exporter shows the
      expected attributes on the expected pipeline.

### fix-a-cardinality-problem

- [ ] Get the breakdown from the store rather than guessing: `seriesCountByMetricName`,
      `labelValueCountByLabelName` and `seriesCountByLabelValuePair` from the TSDB status endpoint
      (`references/cardinality.md`).
- [ ] Separate the three shapes — one metric with too many series, one label with unbounded
      values, and churn where series are created faster than they retire — because the remedies
      differ.
- [ ] Check histograms first: a `_bucket` series at the top of the list is amplified by the bucket
      count, so its labels are the highest-value target in the list.
- [ ] Fix at the source: template the path, bound the error label to an enum, stop emitting
      identifiers, move `version`/`git_sha` to an info metric joined at query time, and let
      target labels come from service discovery rather than application code.
- [ ] For series already stored that cannot be fixed at the source, aggregate post-ingest with a
      counter-reset-aware, auditable, reversible mechanism. Do not reach for `labeldrop`.
- [ ] If production is actively failing, the only safe emergency lever is dropping the whole
      offending metric by `__name__`, and it is a stated loss until the source fix lands.
- [ ] **Gate — the fix is measured, not asserted:** the series count for the affected metric is
      re-read from the same endpoint after the change, and `rate()` on a known-good counter still
      returns plausible values.

### design-alerts-and-slos

- [ ] Write each SLO as four parts: the thing measured, the success criterion, the target, and the
      compliance window. An SLI defined as "not 5xx" credits timeouts and 4xx storms as successes
      (`references/alerting-and-slos.md`).
- [ ] Justify the number of nines against the allowed failure time it implies, and against what
      one routine deploy costs; pick the lowest target the business actually needs.
- [ ] Define latency SLIs as a ratio of good events, not as an average or a quantile of an
      average — averages hide exactly the tail the objective exists to protect.
- [ ] Derive the paging alerts from the budget with multi-window multi-burn-rate rules: a fast
      burn pages, a slow burn tickets, and each long window is paired with a short one so the
      alert clears promptly.
- [ ] Re-classify every existing alert as symptom or cause, and move the causes to dashboards.
- [ ] Give each surviving paging alert a `for:` duration, a runbook link and one of two
      severities; write the error-budget policy with a consequence, not a meeting.
- [ ] **Gate — each alert was fired once:** the threshold is temporarily lowered, the notification
      arrives in the intended channel, and the runbook link resolves.

### investigate-from-production-signals

- [ ] Inventory what exists before theorising: which metrics, which log fields, how much of the
      trace volume survived sampling, and which join keys are actually present
      (`references/production-triage.md`).
- [ ] Establish the blast radius and the timeline from metrics — when it started, what fraction of
      traffic, which routes, tenants or versions.
- [ ] Pivot to a trace using an exemplar or a `trace_id` from a log record, and read the trace for
      where the time or the error entered, not for a root cause.
- [ ] Read the log records for that exact `trace_id` to get the specifics the span attributes
      omitted.
- [ ] Check the telemetry pipeline as a suspect too: a metric that stopped reporting, a Collector
      refusing data, an exporter queue full or a sampler discarding the interesting traces all
      look like application failures.
- [ ] State the conclusion at the confidence the signals support, and separate it from what is
      merely consistent with them.
- [ ] Close the loop by fixing the observability gap that made the investigation slow, and by
      turning the symptom into an alert if nothing caught it.
- [ ] **Gate — the next occurrence is cheaper:** name the specific signal added or corrected, and
      show the query an on-call engineer would run next time.

## Topic router

| Topic | Read when | File |
|---|---|---|
| The three signals and their cost curves, resource versus scope versus record attributes, context propagation and W3C `traceparent`, exemplars, `schema_url`, which signal answers which question | Deciding what to emit, or why two signals disagree | `references/signals-and-data-model.md` |
| SDK setup, automatic versus manual instrumentation, span naming, kind and status per kind, attributes and their cardinality budget, exception recording, headless root spans, span hygiene limits, graceful shutdown, asserting on trace shape in tests | Writing or reviewing instrumentation code | `references/instrumentation.md` |
| Convention stability levels, the domain list, the deprecated-to-stable rename table, `OTEL_SEMCONV_STABILITY_OPT_IN` and `/dup`, declarative version selection, `schema_url` and translation, where `gen_ai.*` moved | Migrating attribute names, or deciding whether a convention is safe to depend on | `references/semantic-conventions.md` |
| Receivers, processors, exporters, connectors and extensions; processor ordering; `memory_limiter` semantics and validation errors; batching and the sending queue; agent versus gateway; internal telemetry; the validation recipe with real output | Authoring, reviewing or debugging Collector YAML | `references/collector-pipelines.md` |
| Head versus tail sampling, policy design, sizing `decision_wait` and the buffer, the load-balancing tier and headless Service, consistent-hash instability during scaling, materialising metrics before sampling | Choosing or fixing a sampling strategy | `references/sampling.md` |
| Series arithmetic, the rule against dropping distinguishing labels and why it corrupts `rate()`, TSDB status diagnosis, churn, histogram amplification, info metrics and `info()`, exemplars, the five remediation levers in order | A store is OOMing, a bill jumped, or a label set needs auditing | `references/cardinality.md` |
| Event names and field conventions, severity to on-call action, correlation IDs and entry-point fields, trace correlation, exception fields, redaction and allowlisting, log-to-metric derivation, collection pipelines | Designing log output or a log pipeline | `references/structured-logging.md` |
| RED and USE, symptom versus cause, SLO anatomy, nines to allowed failure time, good-event ratios, multi-window multi-burn-rate tables, runbooks, severity tiers, alert audits, error-budget policy | Designing or pruning alerts and SLOs | `references/alerting-and-slos.md` |
| The triage order from alert to code, join keys and what to do when they are missing, reading a trace for locality, suspecting the telemetry pipeline, confidence language, the post-incident observability fix | Investigating something that only happens in production | `references/production-triage.md` |

## Output format

When reviewing instrumentation, a Collector config, or an alert set, group findings by file and
lead each with the location and the consequence rather than the rule name:

```
otel-collector-agent.yaml:8 - ingress - the otlp receiver declares `grpc: {}` with no endpoint,
  and the default is 127.0.0.1:4317, so this DaemonSet binds to loopback and receives nothing
  from other pods. Set `endpoint: 0.0.0.0:4317`.

otel-collector-agent.yaml:41 - sampling - `tail_sampling` runs on a per-node agent, so each
  instance sees only the spans produced on its node and decides each fragment separately. Move
  it to a gateway fed by a `load_balancing` exporter keyed on trace ID.
```

Order findings by what they cost: first the ones that silently produce wrong numbers (a merged
series, RED metrics derived after sampling, an overwritten `service.name`), then the ones that
lose data (loopback ingress, no flush on shutdown, an unbounded queue), then cost and cardinality,
then hygiene. A finding that produces wrong numbers ranks above one that produces none, because a
missing dashboard is visible and a lying dashboard is not.

Quote the evidence rather than asserting it: the config line, the `validate` error text, the
`status/tsdb` entry, the sampled-trace count against the request count. When a claim cannot be
grounded in the signals at hand, mark it as such and name the signal that would settle it.

Say explicitly when something is fine as written, and do not report two acceptable spellings of
the same thing as a finding — a `resource` processor versus an SDK resource attribute for the same
value is a preference, and reporting it buries the findings that matter.

## Environment

- The Collector is a single static binary and an official image, so a configuration question is
  cheaper to settle by running it than by arguing: `docker run --rm -v $PWD:/cfg
  otel/opentelemetry-collector-contrib:<tag> validate --config /cfg/config.yaml` decides syntax,
  defaults and validation offline, and `--version` establishes which rules apply at all.
- `otelcol validate` checks structure, component existence and per-component validation. It does
  not check pipeline *intent*: processor order, a `debug` exporter in production and metrics
  derived after sampling all validate cleanly.
- `telemetrygen traces|metrics|logs --otlp-insecure --otlp-endpoint <host>:4317` generates traffic
  without an application, and a temporary `debug` exporter with `verbosity: detailed` prints every
  record. That pair is how a claim about a pipeline becomes an observation. Remove the `debug`
  exporter afterwards; on a production logs pipeline it writes every record to stdout.
- The Collector's own metrics (`service.telemetry.metrics`, port 8888 by default) are the first
  place to look when telemetry goes missing:
  `otelcol_receiver_refused_*` means backpressure, `otelcol_exporter_send_failed_*` means the
  downstream is rejecting, and a queue at capacity means the exporter cannot keep up. Bind the
  endpoint to `0.0.0.0` or nothing outside the pod can scrape it.
- The SDK's own diagnostics are usually a log level away: raising the OTel internal log level, or
  swapping the OTLP exporter for a console exporter for one run, distinguishes "the SDK produced
  nothing" from "the Collector dropped it" without touching the application logic.
