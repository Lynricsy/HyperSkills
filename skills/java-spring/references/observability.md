# Actuator, Micrometer and logs

Verified against: Spring Boot 4.1.

Instrument user-visible operations and the boundaries the service depends on. Instrumenting every
method produces cardinality and cost, not insight.

## Actuator surface

Expose the minimum and secure the rest. `management.endpoints.web.exposure.include: "*"` on a
service reachable from anywhere publishes `env`, `configprops`, `beans`, `heapdump` and
`threaddump` — an inventory of your configuration and, with `heapdump`, its secrets.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      probes:
        enabled: true
      show-details: when-authorized
```

Run the management endpoints on a separate port (`management.server.port`) when the platform can
route to it privately. Never disable sanitisation on `env`/`configprops` to debug something.

## Health and probes

- Liveness answers "should this process be restarted". It must not depend on a database or a
  broker: a dependency outage then turns into a restart loop that makes the outage worse.
- Readiness answers "should this instance receive traffic". Traffic-critical dependencies belong in
  the readiness group.
- A slow startup needs a startup probe, not a longer liveness timeout.
- Custom `HealthIndicator`s need a hard timeout and stable detail keys; an indicator that blocks
  makes `/actuator/health` itself the outage.

## Metrics and traces

Use the Micrometer `Observation` API rather than the OpenTelemetry API directly: one instrumentation
produces both a metric and a span, and Boot already instruments MVC, WebFlux, `RestClient`,
`WebClient`, repositories and scheduled tasks. Annotating an already-instrumented controller with
`@Observed` double-counts it.

```java
Observation.createNotStarted("orders.create", registry)
    .lowCardinalityKeyValue("channel", channel)     // metric dimension
    .highCardinalityKeyValue("order.id", id)        // trace attribute only
    .observe(() -> service.create(request));
```

The cardinality split is the rule that matters. A user id, an order id, a URL containing an id or
an exception message as a *metric* tag creates one time series per value and eventually takes down
the metrics backend. Those belong on the span or in the log line.

Name observations after a stable operation (`orders.create`), never after a URL with a path
variable in it.

Export over OTLP when the platform boundary is an OpenTelemetry collector:
`spring-boot-starter-opentelemetry` plus `management.opentelemetry.tracing.export.otlp.*`.

Context propagation does not cross an `@Async` or executor boundary by itself. Register a
`ContextPropagatingTaskDecorator` on the executor. In Reactor, enable automatic context propagation
deliberately and prove it with a test rather than assuming it.

## Logs

- Emit structured logs (`logging.structured.format.console=ecs|logstash|gelf`) so fields are
  queryable instead of parsed out of a message.
- Correlate with trace and span ids so a log line leads to the trace and back.
- Use parameterised SLF4J calls (`log.info("order {} placed", id)`), not string concatenation.
- Redact credentials, tokens, personal data and request bodies by default. Never log a bearer
  token, not even truncated.
- Log an exception with the throwable as the last argument, so the stack trace is attached rather
  than flattened into the message.

## Alerts

Alert on symptoms a user would notice — error ratio, latency percentile, saturation, queue lag —
not on individual resource gauges. Every actionable alert carries the service identity, the
dependency involved and a runbook link; an alert nobody knows how to act on is training people to
ignore the next one.

<!-- sources: rrezart-spring-boot, spring-docs -->
