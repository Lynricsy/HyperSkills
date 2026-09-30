# Native OpenTelemetry in FastAPI

Verified against: FastAPI 0.142.1, opentelemetry-sdk 1.45.0, opentelemetry-instrumentation-fastapi
0.66b0. Every `[verified]` line below was reproduced locally against an OTLP sink.

## Contents

- [What is on by default](#what-is-on-by-default)
- [The `telemetry` settings](#the-telemetry-settings)
- [What happens at startup when an OTLP endpoint is set](#what-happens-at-startup-when-an-otlp-endpoint-is-set)
- [Choosing a setup](#choosing-a-setup)
- [The contrib `FastAPIInstrumentor` on 0.142+](#the-contrib-fastapiinstrumentor-on-0142)
- [Adding attributes to the request span](#adding-attributes-to-the-request-span)
- [Exception logs carry the exception message](#exception-logs-carry-the-exception-message)
- [Testing the telemetry](#testing-the-telemetry)

The vendor-neutral side — span naming, attribute cardinality, sampling, Collector pipelines — belongs
to the `observability` skill. This file covers only what FastAPI itself does.

## What is on by default

From FastAPI 0.142, with no code at all, the framework records:

- a server span per HTTP request (`POST /charges`) and per WebSocket connection (`WS /ws/{room}`);
- child "operation spans" for dependency resolution (`fastapi.dependencies`), the path operation
  (`fastapi.endpoint`), response serialisation (`fastapi.serialization`) and each `BackgroundTasks`
  task — the background spans stay in the request's trace but start after the server span ends, so
  they do not inflate measured latency;
- HTTP request metrics (count, duration, active requests) — HTTP only, not WebSockets;
- log records for unhandled exceptions (ERROR, even when the trace is not sampled) and for request
  validation failures (WARNING, with the route and error count but not the invalid input).

`opentelemetry-api` is a core dependency, so without an SDK all of this goes to no-op providers.
`fastapi[standard]` (or `fastapi[opentelemetry]`) adds the SDK and the OTLP **http/protobuf**
exporter, and then setting `OTEL_SERVICE_NAME` and `OTEL_EXPORTER_OTLP_ENDPOINT` is the whole
setup. Traces, metrics and logs go to `/v1/traces`, `/v1/metrics` and `/v1/logs` under the
endpoint; `OTEL_EXPORTER_OTLP_HEADERS` carries authentication.

So for a new app on 0.142+: do not add `opentelemetry-instrumentation-fastapi`, and do not write
provider boilerplate unless something below requires it.

## The `telemetry` settings

Everything is configured through one dict on the constructor, `FastAPI(telemetry={...})`:

| Key | Effect | Default |
|---|---|---|
| `tracing` | request and WebSocket spans | `True` |
| `metrics` | HTTP request metrics | `True` |
| `logs` | exception and validation-failure log records | `True` |
| `operation_spans` | the dependency/endpoint/serialisation/background child spans | `True` |
| `exclude` | callable receiving the ASGI scope; `True` skips that request | `None` |
| `auto_configure` | attach OTLP exporters from the `OTEL_*` environment at startup | `True` |
| `tracer_provider`, `meter_provider`, `logger_provider` | use this provider instead of the global one | global |

Health checks: `telemetry={"exclude": lambda scope: scope["path"] == "/healthz"}` — it receives the
scope, not a URL string, so the contrib instrumentor's `excluded_urls="healthz"` regex does not carry
over. [verified]

A mounted sub-application shares the global providers; independent telemetry settings per mounted
app are not guaranteed.

## What happens at startup when an OTLP endpoint is set

With `auto_configure` on and `OTEL_EXPORTER_OTLP_ENDPOINT` (or a per-signal
`OTEL_EXPORTER_OTLP_<SIGNAL>_ENDPOINT`) set, FastAPI acts on the ASGI `lifespan.startup` event —
**before your own `lifespan` function runs**:

1. **No SDK provider installed globally yet** → FastAPI creates one with an OTLP exporter and
   installs it as the global provider. A `trace.set_tracer_provider(...)` inside your `lifespan` is
   then refused by OpenTelemetry (`Overriding of current TracerProvider is not allowed`, a log
   warning only): your provider, its resource, sampler and exporters are silently discarded.
   [verified]
2. **An SDK provider is already installed** (your module-level setup, Logfire, Sentry's OTel mode, a
   vendor distro) → FastAPI adds its own OTLP exporter to that provider. It never inspects the
   exporters already there, so if yours also points at the environment endpoint, **every span —
   including your manual ones — is exported twice**. [verified]
3. **The environment asks for something other than OTLP http/protobuf** —
   `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`, or `OTEL_TRACES_EXPORTER` / `_METRICS_` / `_LOGS_` set to
   anything but `otlp` or `none` while an endpoint is set → `FastAPIError`, `Application startup
   failed`, and the process exits. An upgrade to 0.142 can therefore crash-loop a deployment whose
   collector is reached over gRPC on 4317 even though the application code did not change.
   [verified under uvicorn]

`OTEL_SDK_DISABLED=true` skips the automatic setup entirely.

## Choosing a setup

| Situation | Do this |
|---|---|
| No existing OpenTelemetry code | Set the `OTEL_*` variables; point `OTEL_EXPORTER_OTLP_ENDPOINT` at the collector's http/protobuf port (4318 by convention). Nothing else. |
| Collector reachable only over gRPC, or you need a non-OTLP exporter | Build the provider yourself at import time with that exporter and pass `telemetry={"auto_configure": False}`. |
| Another component already configures providers and exports to the environment endpoint (Logfire, a vendor distro, your own SDK setup) | Let it configure at import time, before the app starts, and pass `telemetry={"auto_configure": False}` so FastAPI records into those providers without adding a second exporter. |
| You want FastAPI's spans in a provider you pass explicitly | `telemetry={"tracer_provider": provider}` (same for meter/logger). |

Two consequences of `auto_configure: False` to state when choosing it: FastAPI still records into the
global providers, so metrics and exception logs are exported only if something installed a meter
and a logger provider too; and whoever created a provider owns its shutdown.

Provider setup of any kind belongs at import time or in the application factory — never inside
`lifespan`, which runs after FastAPI's own startup hook.

## The contrib `FastAPIInstrumentor` on 0.142+

`opentelemetry-instrumentation-fastapi` still works, but only in one position:

- Called before the app receives its first ASGI event (module level, or `FastAPIInstrumentor()
  .instrument()` before the app is created) → the contrib middleware takes over and FastAPI's native
  spans and metrics for that app switch off. No duplicate server spans. [verified]
- Called from `lifespan` or later → **silently no effect**. The first ASGI event is the lifespan
  event itself, which already built the middleware stack; `server_request_hook` never fires and
  `excluded_urls` is never applied, while the native spans carry on. No error, no warning.
  [verified]

Prefer migrating to the native telemetry over moving the call to module level. The hook's jobs have
native equivalents: `excluded_urls` → `exclude`, `server_request_hook` → HTTP middleware (next
section).

## Adding attributes to the request span

Where the native server span is the current span:

| Code location | `trace.get_current_span()` returns |
|---|---|
| `@app.middleware("http")` or a pure ASGI middleware | the request's server span |
| a dependency | the `fastapi.dependencies` operation span |
| the path operation | the `fastapi.endpoint` operation span |

So a per-request attribute such as a tenant id goes in middleware: [verified]

```python
@app.middleware("http")
async def tag_tenant(request: Request, call_next):
    if tenant_id := request.headers.get("x-tenant-id"):
        trace.get_current_span().set_attribute("tenant.id", tenant_id)
    return await call_next(request)
```

Setting it from a dependency lands on the operation span instead — unless `operation_spans` is
`False`, in which case the server span is current there too.

## Exception logs carry the exception message

Every unhandled exception becomes an ERROR log record with `exception.type`, `exception.message` and
`exception.stacktrace`, exported to `/v1/logs` whether or not the trace was sampled. Anything
interpolated into an exception message — a card number, a token, an email address — is now shipped
to the telemetry backend. [verified: `ValueError(f"... {card_number}")` arrived verbatim in the
OTLP log payload]

When upgrading, grep the `raise` sites for interpolated request data. Then choose: keep secrets out of
exception messages (the fix that also protects every other log sink), redact with a log-record
processor on the logger provider, or `telemetry={"logs": False}`.

## Testing the telemetry

Pass in-memory providers through the dict rather than patching globals:

```python
exporter = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
app = create_app(telemetry={"tracer_provider": provider, "auto_configure": False})

with TestClient(app) as client:
    client.get("/items/1", headers={"x-tenant-id": "acme"})

(server,) = [s for s in exporter.get_finished_spans() if s.name == "GET /items/{item_id}"]
assert server.attributes["tenant.id"] == "acme"
```

Global providers can be set only once per process, so a test that needs `trace.set_tracer_provider`
has to run in a subprocess.

<!-- sources: fastapi-official-skill, fastapi-docs -->
