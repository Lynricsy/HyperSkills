# Instrumenting an application

Verified against: OpenTelemetry semantic conventions v1.44.0, OTEP 4430 (Span Event API
deprecation plan).

## Contents

- [Automatic first, manual second](#automatic-first-manual-second)
- [Span names](#span-names)
- [Span kind](#span-kind)
- [Span status](#span-status)
- [Recording exceptions](#recording-exceptions)
- [Span attributes](#span-attributes)
- [Root spans and headless work](#root-spans-and-headless-work)
- [Span hygiene limits](#span-hygiene-limits)
- [Metrics from application code](#metrics-from-application-code)
- [Sampling belongs elsewhere](#sampling-belongs-elsewhere)
- [Graceful shutdown](#graceful-shutdown)
- [Asserting on trace shape in tests](#asserting-on-trace-shape-in-tests)

## Automatic first, manual second

Turn on the language's automatic instrumentation before writing a single manual span. It covers
inbound and outbound HTTP, gRPC, the common database and messaging clients, and it sets the
protocol-level attributes correctly and consistently.

What automatic instrumentation cannot know is your domain. It produces spans that describe *how*
the process communicates, not *what business operation* is being performed. That gap is what
manual work fills — and the way to fill it is usually to enrich the existing span rather than
create a new one:

```typescript
import { trace } from "@opentelemetry/api";

app.post("/api/orders", async (req, res) => {
  const span = trace.getActiveSpan();          // the auto-instrumented SERVER span
  span?.setAttribute("order.id", req.body.orderId);
  span?.setAttribute("tenant.id", req.header("x-tenant-id"));
  // handler logic
});
```

Wrapping an auto-instrumented span in a second manual span just to attach attributes adds a level
of nesting and no information. Create a manual span only for a genuine unit of work that
automatic instrumentation has no way to see — a discount calculation, a batch of provider calls,
a scheduled job.

## Span names

Span names must be low-cardinality: the number of distinct names in a system has to be bounded and
small, because every operation-level view groups by name. A name containing an identifier produces
one "operation" per entity.

| Anti-pattern | Correct | Why |
|---|---|---|
| `GET /api/users/12345` | `GET /api/users/:id` | Route template, not the concrete path |
| `SELECT * FROM orders WHERE id=99` | `SELECT orders` | Table, not the query text |
| `charge_provider_88213` | `charge provider` | The order identifier is an attribute |
| `validation_failed` | `validate user_input` | Name the operation, not its outcome |

Per-signal conventions:

| Kind of work | Name format |
|---|---|
| HTTP server | `{method} {http.route}` |
| HTTP client | `{method} {url.template}`, or `{method}` alone if no template is available |
| Database | `{db.operation.name} {db.collection.name}`, falling back through `db.query.summary` → `{collection}` → `{db.system.name}` |
| RPC | `{rpc.service}/{rpc.method}` |
| Messaging | `{operation} {destination}` |

Never use a raw URI path as a span name. Most frameworks expose the matched route
(`req.route.path` in Express, the route template in ASP.NET Core, the URL pattern in Django), and
that is the value to use. Where none exists, use the method alone rather than inventing a name
from the path — and treat the missing route template as the actual defect.

## Span kind

Each span has exactly one kind, chosen by the communication pattern, not by the technology:

| Kind | Use when |
|---|---|
| `SERVER` | Handling an inbound synchronous request |
| `CLIENT` | Making an outbound synchronous request, including a database query |
| `PRODUCER` | Starting an asynchronous operation — publishing to a queue or topic |
| `CONSUMER` | Processing an asynchronous operation — handling a queued message |
| `INTERNAL` | Work with no remote counterpart at all |

The recurring mistakes:

- `INTERNAL` for everything. A database call is `CLIENT`; an HTTP handler is `SERVER`.
- `CLIENT` for publishing a message. `CLIENT` implies waiting for a response; publishing is
  `PRODUCER` unless the code genuinely blocks on an acknowledgement.
- `SERVER` for consuming a message. The producer is not waiting, so it is `CONSUMER`.

Kind is what a backend builds the service map from. Wrong kinds do not produce errors; they
produce a topology diagram that does not match the system.

## Span status

Leave status `UNSET` by default. Set `ERROR` only when the operation genuinely failed and the
failure is final. Set `OK` only where the code has confirmed success — after validating a
response or receiving an explicit acknowledgement — never speculatively, because `OK` tells the
backend the operation was *verified*, not merely that no exception escaped.

HTTP status mapping differs by span kind, and this is the single most misread convention:

| HTTP status | `SERVER` span | `CLIENT` span |
|---|---|---|
| 1xx, 2xx, 3xx | `UNSET` | `UNSET` |
| 4xx | `UNSET` — the server answered a bad request correctly | `ERROR` — the caller's request failed |
| 5xx | `ERROR` | `ERROR` |
| No response | `ERROR` | `ERROR` |

Two further rules:

- Do not set `ERROR` for a failure that was retried and ultimately succeeded, or for one handled
  by a fallback that produced a valid result. Record each failed attempt as an event and set
  `ERROR` only once the retries are exhausted.
- When setting `ERROR`, include a status message naming the error class and giving one line of
  context — enough to understand the failure without opening the trace. Not a stack trace; that
  belongs in a log record.

```typescript
// Useless: no message at all.
span.setStatus({ code: SpanStatusCode.ERROR });
// Useless: message with no diagnostic content.
span.setStatus({ code: SpanStatusCode.ERROR, message: "something went wrong" });
// Useful.
span.setStatus({
  code: SpanStatusCode.ERROR,
  message: "TimeoutError: payment provider did not respond within 5s",
});
```

## Recording exceptions

Emit the exception as a structured log record inside the active span context, not as a span event.
The Span Event API has a published deprecation plan (OTEP 4430 in the OpenTelemetry
specification repository) in favour of log-based events, and the log record is also the only place
a stack trace belongs.

```typescript
import { trace, context } from "@opentelemetry/api";

const spanContext = trace.getSpan(context.active())?.spanContext();
logger.error("order.charge.failed", {
  trace_id: spanContext?.traceId,
  span_id: spanContext?.spanId,
  "exception.type": error.name,
  "exception.message": error.message,
  "exception.stacktrace": error.stack,
});
```

Give the record a message naming the failed operation. `"exception"` or `"error"` as the message
wastes the one field that makes a log stream scannable, since `exception.*` already carries the
details.

<details>
<summary>Old pattern: <code>span.recordException(err)</code></summary>

`recordException` writes a span event with the `exception.*` attributes. It still works in every
SDK and existing code using it is not broken. The reasons to move: span events are not queryable
as log records in most backends, they inflate span size with stack traces, and the API is on a
deprecation path. Migrate when touching the code, not as a campaign.

</details>

## Span attributes

Automatic instrumentation sets the protocol attributes. Add the domain attributes that answer
"during an incident, what context would I need for this span?"

| Domain | Attributes worth adding |
|---|---|
| Commerce | `order.id`, `cart.item_count`, `payment.method` |
| Identity | `enduser.id`, `user.role`, `auth.method` |
| Multi-tenant | `tenant.id`, `tenant.plan` |
| Messaging | `message.type`, queue depth at publish time |
| Feature flags | `feature_flag.key`, `feature_flag.variant` |

Naming: dot-separated namespaces (`order.id`, never `orderId` or `order_id`); check the attribute
registry for an existing key before inventing one; prefix genuinely custom attributes with a
namespace you own (`com.acme.order.priority`).

Spans tolerate much higher cardinality than metrics — an `order.id` on a span is correct and an
`order.id` on a metric is a bug — but they are not unbounded. Safe: identifiers, bounded enums,
flag keys. Not safe: request bodies, serialised objects, a full URL with its query string, or
anything of unpredictable size. Prepared-statement parameter capture
(`db.query.parameter.<key>`) is off by default in every SDK because those values routinely carry
credentials and personal data; do not switch it on without deciding what redacts it downstream.

## Root spans and headless work

A root span describes what the service is *doing*, so its kind should be `SERVER`, `CONSUMER` or
`INTERNAL`. A `CLIENT` or `PRODUCER` root span means one of three things:

- HTTP server instrumentation is missing, so the framework's handler span does not exist.
- Context propagation is broken, so the incoming parent was never extracted.
- The work is headless — a cron job, scheduled task, CLI command or background worker with no
  inbound request — and nothing created a root span for it.

The third case is the common one, and the fix is explicit:

```javascript
// Wrong: the first database call becomes a parentless CLIENT root span.
async function processDaily() {
  await db.query("SELECT id FROM orders WHERE status = $1", ["pending"]);
}

// Right: a manual root span describes the unit of work.
async function processDaily() {
  await tracer.startActiveSpan("process daily orders", { kind: SpanKind.SERVER }, async (span) => {
    try {
      await db.query("SELECT id FROM orders WHERE status = $1", ["pending"]);
    } finally {
      span.end();
    }
  });
}
```

This is observable without an application: `telemetrygen traces` emits a root span of kind
`CLIENT` with an empty parent, which a `debug` exporter prints plainly — a convenient way to see
what the anti-pattern looks like in a trace view. [verified]

## Span hygiene limits

These are numeric gates, which makes them checkable rather than aspirational:

| Rule | Limit | What violating it means |
|---|---|---|
| Root span kind | Not `CLIENT` or `PRODUCER` | Missing instrumentation, broken context, or a headless job with no root span |
| `CLIENT`/`PRODUCER` spans | Must have a parent | The trace records the call but not the work that caused it |
| Orphan spans | Zero | A `parent_span_id` with no matching parent: broken propagation, or a parent dropped by sampling |
| `INTERNAL` spans | ≤ 10 per service per trace | Over-instrumentation; the trace view hides the real bottleneck |
| Spans under 5 ms | ≤ 20 per trace | Spans created in a tight loop |

The last two have the same fix: replace a span per iteration with one span per batch plus a
`batch.size` attribute, or use a log record where a child span was only ever an annotation.

## Metrics from application code

Instrument RED on every endpoint and every outbound dependency — rate, errors, duration as a
histogram — and USE on every pool, queue or host-like resource: utilisation, saturation, errors.

The failure mode is labels. Every distinct label combination is a separate series, labels are
multiplicative, and a histogram multiplies again by its bucket count. Label values must come from
small fixed sets:

```
Fine as a label:   route template, status class ("5xx", not "503"), provider name, error enum
Never a label:     user id, order id, request id, trace id, raw URL, error message text
```

Identifiers that are genuinely needed for correlation go on spans, in log records, or in
exemplars. Version-like metadata (`version`, `git_sha`, `image_tag`) does not belong on every
metric either — it changes on every deploy, and every change creates a new series. Put it on a
single info metric and join at query time.

## Sampling belongs elsewhere

Leave the SDK sampler at its default `AlwaysOn`. Do not configure `TraceIdRatioBased`,
`ParentBased` with a ratio, or anything else that drops spans in the application.

The reason is timing, not taste: a head sampler decides before the request's outcome is known. A
trace that looked unremarkable at its first span may turn out to contain the error, the latency
spike, or the rarely exercised path — and at a 5% rate, 95% of those are gone. Collector-side
sampling can evaluate the finished trace instead.

There is one legitimate escape hatch: when the SDK-to-Collector hop is itself the unacceptable
cost — metered egress, per-invocation serverless billing, a device on a slow link. Then sample in
the SDK (`OTEL_TRACES_SAMPLER=traceidratio` with `OTEL_TRACES_SAMPLER_ARG`), and state plainly
that errors and tail latency are being discarded at the same rate as everything else. In a normal
service, setting those two variables is the bug; `AlwaysOn` is the default and needs no variables.

## Graceful shutdown

SDKs batch spans, metrics and log records before exporting. If the process exits before the batch
flushes, the buffered telemetry is lost — including the data from the request that caused the
crash, which is precisely the data wanted.

Handle `SIGTERM` and call the SDK's shutdown (which flushes and stops the providers) before
exiting. Note the limit honestly: `SIGKILL`, an OOM kill and a segfault bypass every in-process
hook, and no configuration prevents that. Where losing the last batch is unacceptable, the answer
is a local Collector with a persistent queue, not a longer flush timeout.

## Asserting on trace shape in tests

Trace shape is a functional requirement: span names, parent-child relations, kinds, status codes
and attributes are what the dashboards and alerts are built on. An in-memory span exporter makes
them assertable in ordinary integration tests.

```typescript
import { SpanKind } from "@opentelemetry/api";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";

const exporter = new InMemorySpanExporter();
provider.addSpanProcessor(new SimpleSpanProcessor(exporter));

function assertNoParentlessOutboundSpans() {
  const bad = exporter
    .getFinishedSpans()
    .filter((s) => (s.kind === SpanKind.CLIENT || s.kind === SpanKind.PRODUCER) && !s.parentSpanId);
  if (bad.length > 0) {
    throw new Error(`CLIENT/PRODUCER root spans: ${bad.map((s) => s.name).join(", ")}`);
  }
}
```

The assertions worth keeping are the ones from the hygiene table: no parentless outbound spans, no
orphans, `ERROR` spans carry a message, and the per-trace counts stay under their limits. They
catch a real class of regression — a refactor that moves work out of a request handler, or a new
worker with no root span — and they do not restate the instrumentation. Do not assert that a
specific attribute was set on a specific span unless a dashboard or alert depends on it; that
pins the implementation and fails on every harmless rename.

<!-- sources: dash0-agent-skills, ollygarden-otel-skills, addyosmani-agent-skills, o11y-dev-otel, otel-semconv, otel-spec, otel-docs, getsentry-sdk-skills, dotnet-claude-kit -->
