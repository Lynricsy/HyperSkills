# Sampling traces

Verified against: otelcol-contrib 0.160.0.

## Contents

- [Where the decision belongs](#where-the-decision-belongs)
- [Head sampling](#head-sampling)
- [Tail sampling](#tail-sampling)
- [The load-balancing tier](#the-load-balancing-tier)
- [Sizing `decision_wait` and the buffer](#sizing-decision_wait-and-the-buffer)
- [Policy design](#policy-design)
- [Materialise metrics before sampling](#materialise-metrics-before-sampling)
- [Reading sampled data honestly](#reading-sampled-data-honestly)
- [The operational bill](#the-operational-bill)
- [Diagnosing a sampling problem](#diagnosing-a-sampling-problem)

## Where the decision belongs

Three places can drop a trace, and they differ in what they know when they decide:

| Location | Knows | Consequence |
|---|---|---|
| SDK (head) | The trace ID, and nothing about the outcome | Errors and slow requests are discarded at the same rate as everything else |
| Collector agent (head) | Same as the SDK, plus resource attributes | Same blindness, but changeable centrally without a redeploy |
| Collector gateway (tail) | The whole trace: status, duration, attributes | Can keep exactly the interesting traces — at the cost of buffering and a stateful tier |

The default: SDKs run `AlwaysOn` and export everything to a local Collector; the Collector decides.
That single choice is what makes "keep every error" possible at all, because at the moment the
SDK decides, nothing knows whether the request will fail.

The one situation that justifies head sampling in the SDK is a hop whose cost is itself the
problem — metered egress, per-invocation serverless billing, a constrained device link. Take it
deliberately and say what it costs: errors and tail latency are sacrificed at the sampling rate.

## Head sampling

Head sampling keeps a fixed percentage, derived deterministically from the trace ID, so every
Collector in the fleet reaches the same decision for the same trace without coordinating:

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 10

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, probabilistic_sampler]
      exporters: [otlp_grpc/vendor]
```

Determinism from the trace ID is the property that matters: it means a trace is kept or dropped
whole, rather than fragmented across instances. Use head sampling as a coarse volume reduction
ahead of tail sampling, or where a tail tier is not worth operating — never as the only mechanism
in a system whose errors you care about.

## Tail sampling

Tail sampling buffers all the spans of a trace, then decides on the complete picture. It can keep
every error, every slow request, and a configurable baseline of normal traffic for comparison.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 1638
    spike_limit_mib: 400
  tail_sampling:
    decision_wait: 30s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    policies:
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: slow
        type: latency
        latency:
          threshold_ms: 1000
      - name: baseline
        type: probabilistic
        probabilistic:
          sampling_percentage: 10
```

`tail_sampling` is Beta for traces on 0.160.0 and this minimal shape validates cleanly. It also
supports in-process concurrency through `num_shards`, which spreads the decision work across
goroutines — that is not a substitute for scaling across instances, which still needs a
load-balancing tier. [verified]

The hard requirement: **every span of a trace must reach the same Collector instance.** Running
`tail_sampling` on a per-node agent means each instance sees only the spans produced on its node,
so a trace that crosses three nodes is decided three times on three fragments — and a policy
looking for an error span will miss it whenever the error happened on a different node.

## The load-balancing tier

The two-tier shape that makes tail sampling correct:

```
Applications -> Agent (DaemonSet) -> Gateway (sampling) -> Backend
                      |                    |
             load_balancing exporter   tail_sampling processor
             hashes the trace ID      buffers and decides
```

The agent exports traces through `load_balancing` instead of a plain OTLP exporter, resolving
gateway instances by DNS. Metrics and logs bypass the sampling tier entirely and go straight out.

Two details decide whether the hashing actually works:

- The gateway needs a **headless Service** (`clusterIP: None`) so DNS returns individual pod IPs.
  A normal ClusterIP Service returns one virtual IP, and the consistent hash then has exactly one
  bucket — every trace goes to whichever pod the kube-proxy picks, and spans of one trace land on
  different pods.
- The routing key must be **deterministic and stable**. Trace ID for tail sampling; a tenant or
  cluster attribute when routing for isolation rather than sampling. A non-string attribute has to
  be normalised first, or the hash input changes representation between instances.

DNS-based discovery is eventually consistent, so scaling the gateway temporarily routes spans of
one trace to different instances. Expect a short window of split traces after every scale event;
that is a reason to scale the gateway rarely, not a reason to avoid the design.

## Sizing `decision_wait` and the buffer

`decision_wait` is a deadline, not a hint. Distributed traces carry no end-of-trace marker, so
when the timer expires the processor decides with whatever spans have arrived.

Set it above the p99 duration of the slowest operation being sampled. A `decision_wait` of 5
seconds in a system with 30-second batch jobs and 10-second upstream timeouts systematically
force-decides exactly the traces that matter — the slow and timed-out ones — on partial data, and
the result looks like missing instrumentation rather than a sampling misconfiguration.

Memory scales as roughly `decision_wait × traces_per_second × spans_per_trace × span_size`. Set
the container limit from that estimate, and `memory_limiter.limit_mib` below it with headroom.

| Setting | Meaning | Guidance |
|---|---|---|
| `decision_wait` | How long to buffer before deciding | Above the p99 of the slowest sampled operation |
| `num_traces` | Traces held in memory | Exceeding it force-decides the oldest; size from throughput × wait |
| `expected_new_traces_per_sec` | Pre-allocation hint | Approximate traces per second |

## Policy design

Policies are evaluated together and a trace is kept if any matches, so think of them as a union of
reasons to keep something:

| Policy type | Keeps | Role |
|---|---|---|
| `status_code` | Traces containing an `ERROR` span | Always — errors are the highest-signal traces |
| `latency` | Traces over a duration threshold | Always — slow requests are the second |
| `probabilistic` | A random baseline | Always — without a baseline there is nothing to compare an error trace against |
| `string_attribute` | Traces matching an attribute value | Specific tenants, routes or operations that matter more |
| `rate_limiting` | A fixed number per second | A predictable ceiling on volume |

The baseline policy is the one most often left out, and it is what makes the others useful: a
corpus of only errors and slow requests cannot answer "is this latency unusual for this route?"

## Materialise metrics before sampling

Rate and error rate cannot be derived from sampled traces. Head sampling scales counts down by the
sampling rate; tail sampling biases them towards errors, because errors are kept preferentially.
Both produce wrong numbers, in opposite directions, and neither announces itself.

Generate the metrics from spans with a connector placed upstream of the sampler, then let the
sampled traces go their own way:

```yaml
connectors:
  signaltometrics:
    spans:
      - name: http.server.request.duration
        unit: s
        conditions:
          - kind == SPAN_KIND_SERVER and attributes["http.request.method"] != nil
        attributes:
          - key: http.request.method
          - key: http.response.status_code
            optional: true
          - key: http.route
            optional: true
        include_resource_attributes:
          - key: service.name
        exponential_histogram:
          value: Seconds(end_time - start_time)

service:
  pipelines:
    traces/derive:
      receivers: [otlp]
      processors: [memory_limiter]
      exporters: [signaltometrics, load_balancing]
    metrics/red:
      receivers: [signaltometrics]
      processors: [memory_limiter]
      exporters: [otlp_grpc/vendor]
```

Keep the dimension list bounded. Every dimension multiplies the derived series count, so a
per-request identifier as a dimension turns a useful RED metric into the cardinality problem the
metric was meant to avoid. Route template, method, status code and `error.type` are the right
shape; a user or order identifier is not.

## Reading sampled data honestly

This is where sampling causes wrong conclusions rather than missing data:

- **A count of sampled traces is not a count of events.** Eleven error traces over a window whose
  error-rate metric implies 190,000 failures is a sampling artefact, not a contradiction — and
  reading it as "we only had eleven errors" inverts the investigation.
- **Tail-sampled corpora are deliberately biased.** The proportion of error traces in storage is
  not the error rate, by design.
- **Missing traces have three different causes** that look identical in a UI: the sampler dropped
  them, `decision_wait` expired before the interesting spans arrived, or the spans were never
  emitted. Check the Collector's own metrics and the sampler configuration before concluding it is
  an instrumentation gap.
- **A parent dropped while a child was kept produces an orphan span.** That is a sampling
  consistency problem, not broken propagation, and the two get confused constantly.

## The operational bill

Tail sampling is the most operationally expensive thing in a telemetry pipeline. Before choosing
it, accept the whole cost:

- Two tiers to scale, monitor and upgrade independently.
- A stateful gateway: terminating a pod loses its buffered spans, so `preStop` hooks and a real
  termination grace period are part of the design.
- Cross-zone traffic. The routing key is the trace ID, which has no relationship to topology, so
  spans cross availability-zone boundaries routinely and the network bill reflects it.
- A new failure mode: a gateway under memory pressure refuses data, and the agents then apply
  backpressure to applications.

Where that is too much, head sampling at a rate the error budget can tolerate, with RED metrics
materialised from unsampled spans at the agent, is a defensible answer. What is not defensible is
tail sampling configured as if it were stateless.

## Diagnosing a sampling problem

- Compare the trace count in storage to the request count from an unsampled metric. The ratio
  should match the configured baseline; a large discrepancy points at `decision_wait` or a
  gateway that is not receiving whole traces.
- Look for orphan spans and `CLIENT` root spans. A spike in either after a sampling change means
  traces are being split, not that instrumentation regressed.
- Check `otelcol_processor_*` and exporter queue metrics on the gateway. A sampler that is
  dropping because it is out of buffer looks exactly like a sampler doing its job.
- Check whether the errors you expect to be kept actually have `ERROR` status. A `status_code`
  policy cannot match a failure that the instrumentation recorded as `UNSET` — which is what
  happens when a `CLIENT` span sets `OK` regardless of the response.

<!-- sources: dash0-agent-skills, ollygarden-otel-skills, o11y-dev-otel, otel-collector-contrib, otel-docs -->
