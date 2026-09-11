# Structured logging

Verified against: OpenTelemetry semantic conventions v1.44.0, otelcol-contrib 0.160.0.

## Contents

- [Events, not prose](#events-not-prose)
- [Severity and the on-call action](#severity-and-the-on-call-action)
- [Correlation keys](#correlation-keys)
- [Naming the entry point](#naming-the-entry-point)
- [Exception records](#exception-records)
- [Field conventions](#field-conventions)
- [Redaction](#redaction)
- [Deriving metrics from logs](#deriving-metrics-from-logs)
- [Collection paths](#collection-paths)
- [Reviewing log output](#reviewing-log-output)

## Events, not prose

A log record is a queryable object with a stable event name and machine-readable fields. Every
value interpolated into a message string is a value that cannot be filtered, grouped or graphed.

```typescript
// Unqueryable: three facts welded into one string, and a different string for every order.
logger.info(`Payment ${id} failed for user ${userId} after ${n} retries`);

// Queryable: stable event name, separate fields.
logger.warn({
  event: "payment_failed",
  payment_id: id,
  provider: "stripe",
  error_type: err.code,
  attempt: n,
}, "payment failed");
```

The event name is the axis everything else hangs off. It must be stable across releases and
low-cardinality — `payment_failed`, not `payment 88213 failed` — because it is what an alert
matches and what a dashboard groups by. Changing an event name is a breaking change to every
consumer, exactly like renaming a metric.

Three queryable events beat three hundred lines of prose. The instinct that more logging is more
observability is backwards: unstructured volume makes an incident slower, because the search space
grows while the number of answerable questions stays at zero.

## Severity and the on-call action

Levels are only useful if they map to a decision:

| Level | Meaning | On-call action |
|---|---|---|
| `error` | An invariant is broken; someone may need to act | Investigate |
| `warn` | Degraded but handled — a retry succeeded, a fallback was used | Watch for trends |
| `info` | A significant business event — order placed, job finished | None |
| `debug` | Diagnostic detail | Off in production by default |

Two failure modes, both common. Logging handled conditions at `error` trains the rotation to
ignore `error`. Logging genuine failures at `warn` because "it is retried" hides the case where
every retry failed. The test is the action column: if nobody would act on it, it is not `error`.

Keep `debug` off in production by default, and make the level runtime-configurable rather than
build-time, so raising it during an incident does not require a deploy.

## Correlation keys

A log record without a correlation key is an orphan: interleaved requests cannot be separated, and
"show me everything that happened to this one request" is unanswerable.

Three keys, in increasing value:

1. **A request or run identifier**, generated or accepted at the system boundary and attached to
   every record.
2. **`trace_id` and `span_id`** for records emitted inside a span. These are what let a log line
   be pivoted to its trace and back, which is the join that decides how an incident goes.
3. **The resource identity** (`service.name`, `service.version`,
   `deployment.environment.name`) so records from different services can be compared at all.

```typescript
// Boundary middleware: one child logger per request, identifier propagated downstream.
app.use((req, res, next) => {
  req.id = req.headers["x-request-id"] ?? crypto.randomUUID();
  req.log = logger.child({ request_id: req.id });
  res.setHeader("x-request-id", req.id);
  next();
});
```

For trace correlation, read the identifiers from the active span rather than threading them
manually:

```typescript
import { trace, context } from "@opentelemetry/api";

function traceFields() {
  const sc = trace.getSpan(context.active())?.spanContext();
  return sc ? { trace_id: sc.traceId, span_id: sc.spanId } : {};
}
```

Several logging bridges do this automatically once the OTel SDK is initialised. Prefer the bridge
where it exists — a helper that has to be remembered at each call site will be forgotten at the
one that matters.

The identifiers have to cross every boundary the request crosses: HTTP headers, queue message
metadata, job payloads. A correlation key that stops at the queue produces two disconnected halves
of one story.

## Naming the entry point

A correlation identifier says *which run* a record belongs to. It does not say *what started the
run*. When one log sink is written by a scheduler, a replay endpoint and a manual CLI invocation,
their records are interchangeable, and attributing one falls back to elimination against external
evidence — a deploy log, a process table, someone's memory — which holds only as long as that
evidence happens to survive.

Stamp the entry point where the run starts, next to the correlation identifier, and propagate both
the same way:

```typescript
export const runLog = (entry_point: "scheduler" | "replay_endpoint" | "cli", run_id: string) =>
  logger.child({ entry_point, run_id });
```

A field that merely correlates with an entry point is a hint, not an attribution: anything that
can invoke the job can reproduce that correlation. Only a field set at the point of entry and
carried across the boundaries is evidence.

## Exception records

Exceptions belong in log records rather than span events, and the fields are conventional:

| Field | Content |
|---|---|
| `exception.type` | The exception class |
| `exception.message` | The message |
| `exception.stacktrace` | The stack trace, serialised as a single string |

Emit the record inside the active span context so it carries `trace_id` and `span_id`, and give it
a message that names the failed operation (`order.charge.failed`), not a generic `"exception"`.
The `exception.*` fields already carry the details; the message is what makes the stream scannable.

The corresponding span gets `ERROR` status with a one-line message naming the error class — not
the stack trace. One stack trace per failure, in the log record, is the rule; duplicating it onto
the span inflates trace storage and gives the two copies a chance to disagree.

## Field conventions

- **One name per concept, repository-wide.** `user_id` in one service and `userId` in another
  produces two fields, and every cross-service query has to know both.
- **Reuse OpenTelemetry attribute names** where one exists (`http.request.method`,
  `http.response.status_code`, `db.operation.name`, `enduser.id`). A consumer who has never seen
  your service can then query it.
- **Namespace custom fields** with something you own, and check that a chosen name does not
  collide with a reserved one in the target schema — log schemas commonly reserve whole
  namespaces for their own use.
- **Stable types.** A field that is a number in one record and a string in another breaks
  indexing, and in a strictly typed store it silently drops the record.
- **Bounded event names, unbounded field values.** The opposite of the metric rule: a field value
  may be an identifier, because a log record is not a time series. The event *name* must stay
  bounded.

## Redaction

Telemetry pipelines are a classic data-leak path, and a log store is usually the least protected
copy of production data.

- **Allowlist fields; never log a whole request or response body.** A body is unbounded in size,
  unpredictable in content, and the first place a new personal-data field will appear without
  anyone noticing.
- **Never log credentials, tokens, cookies, authorisation headers, keys or full personal data.**
- **Treat prepared-statement parameters as sensitive.** They are off by default in every OTel SDK
  for exactly this reason; switching them on requires deciding what redacts them downstream.
- **Redact in the pipeline as a safety net, not as the plan.** A Collector `transform` processor
  can mask, hash or delete an attribute, and `filter` can drop a whole record that cannot be
  safely redacted. Both belong after enrichment and before export, so every attribute that could
  carry sensitive data already exists when they run. That this actually works is observable: a
  `set(span.attributes["network.peer.address"], "REDACTED")` statement produces
  `-> network.peer.address: Str(REDACTED)` in the `debug` exporter output on 0.160.0. [verified]
- **Hash rather than delete** where correlation must survive redaction — a hashed identifier still
  groups records without exposing the value.

The ordering matters: the application not emitting the value is prevention; the pipeline masking
it is mitigation. Only the first one protects the copy that some other consumer already took.

## Deriving metrics from logs

Counting log lines to produce an error rate works until the log pipeline drops records under load
— at which point the error rate silently improves during exactly the incident it exists to
detect. Prefer a counter incremented in application code, or a metric derived from spans by a
connector.

Log-derived metrics are the right answer in two cases: telemetry from something you cannot
instrument (an appliance, a third-party component, an access log), and a one-off count during an
incident where an approximate number now beats a precise number after a deploy. Say which case
applies rather than treating the derived metric as equivalent.

## Collection paths

| Path | Use when | Watch for |
|---|---|---|
| OTLP from the application | The app already has an OTel SDK | Losing the last batch on an abrupt exit; use a local Collector with a persistent queue |
| File tailing (`file_log` receiver) | The app writes files and cannot be changed | Offset tracking across rotation; store the offsets durably or a restart re-reads or skips |
| stdout collected by the platform | Containers | Whatever the platform does to multi-line records — a stack trace becomes N records unless something reassembles it |
| Syslog or platform-native | Appliances, managed services | Timestamp and timezone handling, and severity mappings that do not match yours |

Multi-line handling is the most common silent defect: a Java or Python stack trace arriving as
forty separate records with forty separate timestamps, none of which carries the exception type.
Whatever the path, confirm on a real stack trace that it arrives as one record.

Structured output also means the writer should not do the formatting. Emit JSON and let the
collector or the store present it; a log line pretty-printed for a human terminal is a log line
that has to be re-parsed by everything downstream.

## Reviewing log output

- Is every record structured, with a stable event name — no interpolated values in messages?
- Does every record inside a span carry `trace_id` and `span_id`?
- Does every record carry a correlation identifier, set at the boundary and propagated across
  HTTP, queues and jobs?
- Does any sink written by more than one entry point carry an entry-point field set where the run
  starts?
- Do the levels match the on-call action column, particularly: nothing handled logged at `error`?
- Are exceptions recorded with `exception.type`, `exception.message` and `exception.stacktrace`,
  once, in the log record?
- Is any secret, token, cookie, authorisation header or unredacted personal field present?
  Spot-check real output, not the intent of the code.
- Does a real multi-line stack trace arrive as one record?
- Is anything computing a rate by counting log lines where a counter or a span-derived metric
  would be sound?

<!-- sources: addyosmani-agent-skills, dash0-agent-skills, grafana-skills, ollygarden-otel-skills, otel-semconv, otel-docs, otel-collector-contrib -->
