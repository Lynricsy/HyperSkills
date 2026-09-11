# Cloudflare's observability surface for Workers

Verified against: configuration fields present in wrangler 4.131.0's schema; product behaviour
from the official documentation.

Where a local failure can be reproduced, use the `debugging` skill; where only production
signals exist (logs, metrics, traces, alerts), this is the `observability` skill's job. This
file covers only the **Cloudflare product surface** — which knobs exist, what they cost, what
each signal is called. Instrumentation design, semantic conventions, Collector configuration,
RED/USE metrics, SLOs and alert routing belong to the `observability` skill.

## Contents

- [Turn it on before you need it](#turn-it-on-before-you-need-it)
- [Structured logging](#structured-logging)
- [Invocation outcomes](#invocation-outcomes)
- [wrangler tail](#wrangler-tail)
- [Tail Workers](#tail-workers)
- [OpenTelemetry export](#opentelemetry-export)
- [Logpush](#logpush)
- [Choosing a destination](#choosing-a-destination)
- [Reading a production-only failure](#reading-a-production-only-failure)

## Turn it on before you need it

```jsonc
{
  "observability": {
    "enabled": true,
    "logs": { "enabled": true, "head_sampling_rate": 1 },
    "traces": { "enabled": true, "head_sampling_rate": 0.01 }
  }
}
```

Two things go wrong here repeatedly:

- **`observability.enabled` does not enable traces.** `observability.traces.enabled` is a
  separate field. A Worker with the top-level flag set and no traces block has logs and no
  traces, which is discovered during the incident.
- `observability` is non-inheritable, so an environment that does not redeclare it does not
  have it. Production is the environment most likely to have been missed.

`head_sampling_rate` is the volume and cost control: 1 keeps everything, 0.01 keeps one percent.
Sample traces aggressively and logs less so; a log you dropped is a log you cannot query.

## Structured logging

`console.log` output reaches Workers Logs either way, but a concatenated string is not
queryable. Emit JSON, and use `console.error` for errors so they land at error severity:

```ts
console.log(JSON.stringify({
  message: "incoming request",
  method: request.method,
  path: new URL(request.url).pathname,
  requestId,
}));

console.error(JSON.stringify({
  message: "request failed",
  requestId,
  error: error instanceof Error ? error.message : String(error),
}));
```

Generate a `requestId` with `crypto.randomUUID()` at the top of the handler and put it in every
line and in the error response, so a user-reported failure maps to a log query. Never log
secrets, tokens, cookies or full request bodies.

## Invocation outcomes

Every invocation has an outcome, and it is the first thing to read — it distinguishes "the code
threw" from "the platform stopped it":

| Outcome | Meaning |
|---|---|
| `ok` | completed |
| `exception` | uncaught error in the Worker |
| `exceededCpu` | CPU limit hit (Error 1102 to the client) |
| `exceededMemory` | 128 MB isolate limit hit (Error 1102) |
| `canceled` | the client disconnected before completion |
| `scriptNotFound` | no Worker for the route |

CPU time and wall time appear per invocation in Workers Logs, at the top level of the Logpush
`workers_trace_events` dataset, and in the dashboard under **Metrics → Errors → Invocation
Statuses**. For local CPU and memory profiling there is DevTools, which is the tool to reach
for when the reproduction is local — see the `debugging` skill.

## wrangler tail

```sh
npx wrangler tail                      # live stream from the deployed Worker
npx wrangler tail --format json        # pipe into jq
npx wrangler tail --status error       # only failing invocations
```

`wrangler tail` is a live stream, not storage: it shows what happens while it is attached and
retains nothing. It is the right tool for "reproduce it now while I watch" and the wrong tool
for "what happened at 03:00".

## Tail Workers

A Tail Worker receives execution information about a producer Worker — statuses,
`console.log()` payloads, uncaught exceptions — *after* the producer finishes, including
sub-requests made through service bindings and dynamic dispatch.

```jsonc
{ "tail_consumers": [{ "service": "log-collector" }] }
```

```ts
export default {
  async tail(events: TraceItem[]) {
    await fetch("https://collector.example.com/ingest", {
      method: "POST",
      body: JSON.stringify(events),
    });
  },
};
```

Available on Workers Paid and Enterprise, billed by CPU time rather than by request. It is
invoked once per producer invocation, so an unbatched forward is one outbound request per
request — which is why Cloudflare's own guidance is to treat Tail Workers as the advanced
option and prefer the OTel export for ordinary "send logs to a vendor" needs.

## OpenTelemetry export

Configure an OTel destination on the Worker and logs and traces are sent to it **in batches**,
rather than per invocation as a Tail Worker would. That is the supported path for Sentry,
Grafana, Honeycomb and similar destinations, and the reason not to hand-roll a Tail Worker for
export.

The Cloudflare side of this is configuration: a destination and its credentials. The
instrumentation itself — span naming, attributes, context propagation across service bindings
and Queues, trace-based alerting — is the `observability` skill's subject, not this one's.

## Logpush

Logpush delivers batched logs to R2, S3, a SIEM or an HTTP endpoint on a schedule, and is the
retention answer. For Workers the relevant dataset is `workers_trace_events`, whose top-level
fields include the script name, outcome, event timestamp, CPU time and wall time, plus the
`logs` and `exceptions` arrays.

Logpush is an Enterprise feature for most datasets and must be configured before the incident
that needs it. Cloudflare One has its own Logpush surface for Gateway, Access, Network and DEX
logs, configured separately from the Workers datasets.

## Choosing a destination

| Need | Use |
|---|---|
| Watch a deployed Worker right now | `wrangler tail` |
| Query the last few days of logs in the dashboard | Workers Logs with `observability.logs` |
| Traces across service bindings and Durable Objects | `observability.traces.enabled` |
| Ship logs and traces to Sentry/Grafana/Honeycomb | the OTel export (batched) |
| Custom filtering, transformation or fan-out per invocation | a Tail Worker |
| Long retention, SIEM, compliance | Logpush |

## Reading a production-only failure

The order matters, because each step rules out a class of cause:

1. **Outcome first.** `exceededCpu`, `exceededMemory`, `canceled` and `exception` have
   different fixes, and the distinction is free to obtain.
2. **Match the outcome to a limit**, not to the code: `exceededCpu` against `limits.cpu_ms`
   (including a value set *below* the 30 s default), `exceededMemory` against a buffering
   callsite, `1027` against the Free daily request cap, a `429` from a store against its
   per-key write rate, `overloaded` against a single Durable Object or D1 database.
3. **Ask what the deployment is doing**, not only what the code says: a gradual deployment
   serving two versions explains behaviour that alternates; a secret that deployed itself when
   it was set explains a change nobody released; a dashboard edit explains a difference between
   the repository and production.
4. **Check whether the failure is even reproducible locally**, and if not, say why. Local KV is
   read-after-write consistent, local D1 and Durable Objects are single-process, and nothing
   propagates globally — so consistency, contention and quota failures cannot appear in
   `wrangler dev`. `--remote` is the way to exercise them.
5. **Cite a signal.** Each conclusion names a log field, an invocation outcome, or a documented
   limit with its number.

<!-- sources: cloudflare-skills, cloudflare-docs -->
