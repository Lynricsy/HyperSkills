# Collector pipelines

Verified against: otelcol-contrib 0.160.0 (official image
`otel/opentelemetry-collector-contrib`). Every error message and default quoted below was produced
by that version; component names, defaults and stability move between releases, so establish the
version before applying any rule here.

## Contents

- [The five component kinds](#the-five-component-kinds)
- [One pipeline per signal](#one-pipeline-per-signal)
- [Processor order](#processor-order)
- [`memory_limiter`](#memory_limiter)
- [Batching and the sending queue](#batching-and-the-sending-queue)
- [Enrichment processors](#enrichment-processors)
- [Redaction and dropping](#redaction-and-dropping)
- [Agent and gateway](#agent-and-gateway)
- [Component names and stability](#component-names-and-stability)
- [Internal telemetry](#internal-telemetry)
- [Proving a config instead of reading it](#proving-a-config-instead-of-reading-it)
- [What `validate` does not check](#what-validate-does-not-check)

## The five component kinds

| Kind | Role | Placed in |
|---|---|---|
| Receiver | Brings telemetry in — OTLP, a scrape, a log file | `receivers:` of a pipeline |
| Processor | Transforms, enriches or drops telemetry in an ordered chain | `processors:` of a pipeline |
| Exporter | Sends telemetry out | `exporters:` of a pipeline |
| Connector | Exporter in one pipeline and receiver in another — the only way to derive one signal from another | `connectors:`, referenced on both sides |
| Extension | Capability with no pipeline position — health checks, storage, auth | `service.extensions:`, referenced by other components |

Connectors are the piece most often missed. Deriving request-rate metrics from spans is a
connector's job, and it is what makes RED metrics possible without touching application code.

## One pipeline per signal

Pipelines are typed. A receiver that does not support the pipeline's signal is a startup error,
not a warning — placing `hostmetrics` in a traces pipeline fails `validate` with
`failed to create "hostmetrics" receiver for data type "traces": telemetry type is not supported`.
Use named pipelines (`traces/application`, `traces/infrastructure`) when one signal needs two
different treatments. Fan-out — several exporters in one pipeline — gives each exporter an
independent copy, which doubles memory and network per additional destination.

## Processor order

The chain executes in the order written. Getting it wrong does not error; it changes behaviour.

1. `memory_limiter` — first, so backpressure applies before anything else allocates.
2. `resource_detection`, `k8s_attributes` — enrichment early, so later processors can match on
   what they add.
3. `resource` — static attributes after detection, to supplement or deliberately override.
4. Redaction (`transform`, `redaction`) — after enrichment, so every attribute that could carry
   sensitive data exists by the time it runs.
5. Filters, transforms, samplers — last, because they drop or rewrite based on the enriched state.

Two consequences worth stating explicitly. Redaction before enrichment cannot redact what
enrichment is about to add. And a sampler before a metrics-deriving connector means the derived
metrics describe the sample, not the traffic.

## `memory_limiter`

It is a safety valve, not a sizing tool. When the Go heap crosses the soft limit
(`limit_mib - spike_limit_mib`) it refuses incoming data; past the hard limit it drops to protect
the process.

Placement is a convention the Collector does not enforce. Measured on 0.160.0, a pipeline
declaring `processors: [resource, memory_limiter]` starts completely clean — `Memory limiter
configured`, then `Everything is ready. Begin running and processing data.`, with no warning of
any kind. The cost of the misordering only arrives later, as an OOM under load. This is therefore
a review gate, not something CI can catch. [verified]

Both load-bearing keys are required; there are no usable defaults:

```
$ otelcol validate --config c2.yaml     # limit_mib set, check_interval missing
Error: processors::memory_limiter: 'check_interval' must be greater than zero

$ otelcol validate --config c3.yaml     # check_interval set, no limit
Error: processors::memory_limiter: 'limit_mib' or 'limit_percentage' must be greater than zero
```

Further behaviour that changes how it is configured:

- **The limit is Go heap, not RSS.** Process memory runs meaningfully higher (runtime, stacks,
  mmap'd files), so the container limit must sit above `limit_mib` with headroom — otherwise the
  kernel OOM-kills the process before the limiter ever refuses anything. RSS above `limit_mib` is
  expected, not a bug.
- **`limit_mib` silently wins over `limit_percentage`** when both are set. Set only the one meant.
- **`spike_limit_mib` must be smaller than `limit_mib`**, or the soft limit would be non-positive
  and startup fails.
- **Refusal is a non-permanent error**, so well-behaved receivers retry with backoff. A client or
  receiver that does not retry loses that data — this is backpressure by design, not buffering.
- **Sustained refusal is an under-provisioning signal.** The limiter does not make a small
  Collector handle more load; below capacity it simply refuses constantly. Scale out or size up,
  and keep the limiter as the backstop.
- **It reports component health (Collector 0.156+)** via component status, so a status-aware
  health-check extension surfaces memory pressure without log scraping. `limit_percentage` needs
  cgroups to mean anything: on non-Linux hosts it reads total system memory rather than a
  container limit, so prefer `limit_mib` there.
- **A middleware extension form exists (Collector 0.142+, Beta since 0.158)** but is not compiled
  into the stock distributions. On 0.160.0 contrib, configuring it under `extensions:` fails at
  load with `'extensions' unknown type: "memory_limiter"` followed by the list of valid extension
  ids, so the pipeline processor remains the form to use unless you build a custom distribution.
  [verified]

## Batching and the sending queue

Configure batching on the exporter's `sending_queue`, and give the queue persistent storage when a
restart must not lose data:

```yaml
exporters:
  otlp_grpc/vendor:
    endpoint: ingest.example.net:4317
    compression: gzip
    sending_queue:
      enabled: true
      queue_size: 5000
      batch:
        flush_timeout: 200ms
        min_size: 100
    retry_on_failure:
      enabled: true

extensions:
  file_storage:
    directory: /var/lib/otelcol/queue
```

The reason to prefer this over the `batch` processor is durability: an in-memory batch is gone
when the process restarts, while a queue backed by `file_storage` survives it. `sending_queue`
plus `retry_on_failure` is also what makes a downstream outage survivable — without a queue an
exporter failure becomes receiver backpressure within seconds, and with an unbounded queue it
becomes an OOM instead, so size the queue and set the limiter.

What is *not* true, and is worth correcting because a well-known vendor guide says otherwise: the
`batch` processor is neither removed nor deprecated in 0.160.0. A pipeline that references it
starts with no deprecation warning of any kind. Use it where pipeline-level batching is genuinely
wanted, placed after the processors that drop data so it batches only what survives. The
`sending_queue.batch` sub-block is opt-in, and validates cleanly on 0.160.0. [verified]

## Enrichment processors

`resource_detection` fills in infrastructure identity from the environment. List only the
detectors that apply — each adds startup latency and a failure mode — and keep `override: false`
so an application's own `service.name` is not replaced by a detected value.

`k8s_attributes` resolves pod, namespace, workload and node metadata by querying the Kubernetes
API. Three things decide whether it works:

- **Pod association order.** `k8s.pod.uid` from the downward API first, connection IP only as a
  fallback. Behind a service mesh the Collector sees the sidecar's IP, so a connection-only
  association attaches the *wrong* pod's metadata — enrichment that is confidently incorrect.
- **RBAC.** Without read access to pods, namespaces and the workload resources, the processor
  fails **silently** and telemetry simply arrives un-enriched. There is no error to grep for.
- **Names versus UIDs.** Kubernetes names are unique only within a namespace and kind. In a
  multi-cluster setup, extract both `*.name` and `*.uid`, and set `k8s.cluster.name` — a cluster
  has no built-in notion of its own name, so nothing supplies it unless the Collector does.

The `resource` processor is the right place for genuinely Collector-side facts
(`k8s.cluster.name`, `deployment.environment.name`) and the wrong place for service identity:
`upsert` on `service.name` overwrites what every SDK set and collapses the whole fleet into one
entity. Use `action: insert` for identity attributes so SDK values win.

## Redaction and dropping

`transform` (OTTL statements) rewrites; `filter` (OTTL conditions) drops; `redaction` does
allow/block-list masking of attribute keys and values.

OTTL accepts two syntaxes on 0.160.0 — the context-inferred flat form and the older explicit
`context:` block — and both validate:

```yaml
processors:
  transform/redact:
    error_mode: ignore
    trace_statements:
      - set(span.attributes["network.peer.address"], "REDACTED")
        where span.attributes["network.peer.address"] != nil
```

Running that against real spans produces exactly what it claims —
`-> network.peer.address: Str(REDACTED)` in the `debug` exporter output. Prefer the flat form in
new configs; recognise the block form in existing ones rather than flagging it as broken.
[verified]

When dropping to reduce volume, scope the condition to the instrumentation scope that produces the
unwanted record, not to the metric name alone — a name-only filter will eventually drop a
legitimate metric from a different source. Leave a comment naming the library version that made
the filter necessary and the condition under which it can be removed.

## Agent and gateway

| Shape | Where it runs | Good for | Costs |
|---|---|---|---|
| Agent | One per host or node (DaemonSet), or as a sidecar | Local-network hop from the app, host metadata, log file tailing, per-node buffering | One config per fleet to keep in sync; sees only local traffic |
| Gateway | A scaled deployment behind a service | Anything needing a fleet-wide view: tail sampling, cross-service aggregation, egress control, credential isolation | Another hop; stateful when sampling; needs its own scaling and monitoring |

Most production setups use both: agents collect and forward, a gateway does the work that needs
the whole picture. The division is not a preference — tail sampling and any cross-service
derivation are simply wrong on an agent, because an agent never sees the whole trace. A gateway
running stateful processors is also not fungible: terminating a pod discards its buffered spans,
so `preStop` hooks and a real termination grace period are part of the configuration.

## Component names and stability

Many components were renamed to snake_case across releases 0.146–0.154, with the old names kept as
deprecated aliases — `logdedup` → `log_dedup`, `hostmetrics` → `host_metrics`, `spanmetrics` →
`span_metrics`, `k8sattributes` → `k8s_attributes`, `resourcedetection` → `resource_detection`,
`loadbalancing` → `load_balancing`. An old config keeps working; a new one should use the current
name.

Exporters moved too: on 0.160.0 the canonical exporter names are `otlp_grpc` and `otlp_http`
(renamed from `otlp` in core v1.50.0), while the **receiver** is still `otlp`. The old exporter
name is still accepted. This asymmetry is visible in `otelcol components`. [verified]

Stability is per component and per signal. The same component can be Beta for traces and Alpha for
logs, so "is this production-ready?" has to be answered per signal from the component's own
metadata, not from a general impression. Treat Development and Alpha as prototype-only, Beta as
production-viable, Stable as backward-compatible.

Component defaults are the other version-sensitive surface. The `otlp` receiver's default endpoint
is **localhost**, confirmed on 0.160.0:

```
$ otelcol --config c10.yaml             # protocols: grpc: {} with no endpoint
Starting GRPC server  {... "endpoint": "127.0.0.1:4317"}
```

A containerised Collector that omits `endpoint` therefore receives nothing from other pods. With
`endpoint: 0.0.0.0:4317` the same log line reads `[::]:4317`. [verified]

## Internal telemetry

The Collector's own metrics are the first place to look when telemetry goes missing:

| Metric family | What a non-zero value means |
|---|---|
| `otelcol_receiver_accepted_*` | Data is arriving |
| `otelcol_receiver_refused_*` | Backpressure — usually the memory limiter or a full queue |
| `otelcol_exporter_sent_*` | Data is leaving |
| `otelcol_exporter_send_failed_*` | The downstream is rejecting: network, auth, quota |
| `otelcol_exporter_queue_size` vs `_capacity` | At capacity means the exporter cannot keep up |

Configure it under `service.telemetry`, and bind the endpoint to `0.0.0.0` — bound to localhost
inside a pod, nothing can scrape it. Set log encoding to JSON in production. Note that
memory-limiter metric names changed in Collector 0.156 to a component-specific prefix
(`otelcol_processor_memory_limiter_accepted_*` / `_refused_*`), so an alert written against the
older names silently stops matching after that upgrade.

## Proving a config instead of reading it

The Collector is a single static binary with an official image, which makes a configuration
question cheaper to settle by running it:

```bash
# Syntax, component existence, per-component validation — offline, no network.
docker run --rm -v "$PWD:/cfg" otel/opentelemetry-collector-contrib:0.160.0 \
  validate --config /cfg/config.yaml

# Establish which rules even apply.
docker run --rm otel/opentelemetry-collector-contrib:0.160.0 --version
# otelcol-contrib version 0.160.0
```

To prove behaviour rather than syntax, add a temporary `debug` exporter, start the collector, and
generate traffic with `telemetrygen` (note the empty `Parent ID` and `Kind: Client` below — the
generator's root span is itself the anti-pattern from the instrumentation rules):

```bash
docker run -d --name otelexp --network host -v "$PWD:/cfg" \
  otel/opentelemetry-collector-contrib:0.160.0 --config /cfg/config.yaml

docker run --rm --network host \
  ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  traces --otlp-insecure --otlp-endpoint localhost:4317 --traces 2 --service exp-svc

docker logs otelexp
```

With `debug: { verbosity: detailed }` the output prints each record in full, which is what turns a
claim about a pipeline into an observation:

```
ResourceSpans #0
Resource SchemaURL: https://opentelemetry.io/schemas/1.40.0
Resource attributes:
     -> service.name: Str(exp-svc)
     -> deployment.environment.name: Str(exp)
Span #1
    Trace ID       : cbb8bbfcb16cc4a9dcbf0f86b996815a
    Parent ID      :
    Name           : lets-go
    Kind           : Client
```

Remove the `debug` exporter afterwards. On a production logs pipeline it writes every record to
stdout, which doubles the log volume and tends to end up back in the log store.

## What `validate` does not check

`validate` exits 0 on configurations that are wrong in ways that matter. Measured on 0.160.0:

| Passes validation | Actual consequence |
|---|---|
| `memory_limiter` last in the chain | OOM under load, with no warning at startup |
| A component declared but referenced by no pipeline | None — it is clutter, not an error. A well-known guide claims this is a startup error; it is not: a config declaring an unused `batch` processor validates silently and then logs `Everything is ready. Begin running and processing data.` |
| `debug` exporter on a production pipeline | Every record printed to stdout |
| A sampler upstream of a metrics-deriving connector | Derived rates describe the sample, not the traffic |
| `resource` upserting `service.name` | Every service collapses into one identity |
| `pod_association` on connection only | Wrong pod metadata behind a service mesh |
| `decision_wait` shorter than the slowest operation | Traces force-decided on partial data |

Every row in that table is a review finding, not a CI finding. That is why reviewing a Collector
config is a systems review — processor order, memory budget, sampling topology, identity handling
and queue durability have to be considered together before the config is called safe.

<!-- sources: ollygarden-otel-skills, dash0-agent-skills, o11y-dev-otel, otel-collector-contrib, otel-docs -->
