# Web layer and outbound HTTP

Verified against: Spring Boot 4.1 / Spring Framework 7.

## Contents

- [MVC or WebFlux](#mvc-or-webflux)
- [Controllers](#controllers)
- [Validation](#validation)
- [Error responses](#error-responses)
- [Outbound calls: HTTP service interfaces](#outbound-calls-http-service-interfaces)
- [RestClient and WebClient](#restclient-and-webclient)
- [Timeouts and resilience](#timeouts-and-resilience)
- [WebFlux specifics](#webflux-specifics)

## MVC or WebFlux

Choose MVC unless the *entire* request path is non-blocking. One JDBC call, one blocking SDK or one
`block()` on a Reactor event loop costs more than MVC ever would, and the failure mode is a stalled
event loop rather than a slow request.

With virtual threads (`spring.threads.virtual.enabled=true`, Java 21+) MVC handles high-concurrency
I/O-bound workloads without the reactive programming model, which removes most of the historical
reason to pick WebFlux. Reach for WebFlux when you need streaming with backpressure, very large
numbers of long-lived connections, or you already have R2DBC and a reactive stack end to end.

Never put both `spring-boot-starter-webmvc` and `spring-boot-starter-webflux` on the classpath by
accident: Boot picks MVC and the WebFlux beans quietly do nothing.

## Controllers

Keep controllers thin: bind, validate, delegate, map. Business rules belong in the service, and
`@Transactional` on a controller holds a transaction open across serialisation.

- Accept and return `record` DTOs. Exposing a JPA entity leaks the schema and serialises lazy
  associations outside the transaction.
- Return `ResponseEntity` only when the status or headers vary; otherwise annotate with
  `@ResponseStatus` and return the body type.
- Constructor injection, `private final` fields. Field injection cannot be constructed in a test
  and hides a growing dependency list.
- For a paged endpoint accept `Pageable` and cap the page size
  (`spring.data.web.pageable.max-page-size`) — an uncapped `size` parameter is a denial-of-service
  primitive.

API versioning is built in from Boot 4: configure `spring.mvc.apiversion.*` (or
`spring.webflux.apiversion.*`) and declare `@RequestMapping(version = "1.1")`, rather than encoding
versions by hand in every path.

## Validation

`@Valid` on a `@RequestBody` triggers Jakarta Validation and produces a
`MethodArgumentNotValidException`, which the framework already maps to a 400. Validation on path
variables and request parameters needs `@Validated` on the class and raises
`HandlerMethodValidationException` instead — the two have different exception types and are easy to
handle inconsistently.

Validate at the boundary; enforce invariants inside the domain object's constructor or factory. A
constraint annotation on an entity field fires at flush time, which is far away from the request
that caused it.

## Error responses

One error contract per API. For a new API that is RFC 9457 Problem Details (which obsoletes
RFC 7807):

```yaml
spring:
  mvc:
    problemdetails:
      enabled: true       # spring.webflux.problemdetails.enabled for WebFlux
```

That switch makes Spring's own exceptions (400, 404, 405, 415, …) render as
`application/problem+json`. Add a `@RestControllerAdvice` extending `ResponseEntityExceptionHandler`
for domain exceptions so the framework's handling is preserved rather than replaced.

```json
{
  "type": "https://api.example.com/errors/order-not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Order 123 not found",
  "instance": "/api/v1/orders/123",
  "errorCode": "ORDER_NOT_FOUND"
}
```

- `type` is optional and defaults to `about:blank`; when omitted, `title` should be the status
  phrase. When present it must be a stable URI you own.
- Put machine-readable detail in extension members (`errorCode`, `violations`), never in prose the
  client has to parse.
- The HTTP status and the body `status` must agree.
- Never surface a persistence or infrastructure exception message. Log it, return a generic 500.
- Authentication and authorization failures never reach the advice; they are handled in the
  security filter chain by an `AuthenticationEntryPoint` and an `AccessDeniedHandler`.

An existing API with a different error envelope keeps it. Migrating the contract is its own change,
not a side effect of touching one endpoint.

## Outbound calls: HTTP service interfaces

Declare the remote API as an interface and let Boot 4 register the proxy:

```java
@HttpExchange("/orders")
public interface OrderApiClient {
    @GetExchange("/{id}") OrderDto get(@PathVariable UUID id);
    @PostExchange OrderDto create(@RequestBody CreateOrderRequest request);
}

@SpringBootApplication
@ImportHttpServices(group = "orders", basePackages = "com.example.client.orders")
class Application { }
```

```yaml
spring:
  http:
    clients:
      connect-timeout: 2s          # global transport defaults
      read-timeout: 5s
    serviceclient:
      orders:                       # group name must match @ImportHttpServices
        base-url: https://orders.internal.example.com
        read-timeout: 10s
```

The interface needs no `@Component` and no implementation. Group settings live under
`spring.http.serviceclient.<group>`, global transport defaults under `spring.http.clients` — the
singular `spring.http.client.*` is not the same key. The default client type is the blocking
`RestClient`; an interface returning `Mono`/`Flux` must select
`HttpServiceGroup.ClientType.WEB_CLIENT` and bring the WebFlux starter.

Hand-built `HttpServiceProxyFactory` beans still work and remain the escape hatch for a single
one-off client, but they are the Boot 3 pattern.

## RestClient and WebClient

For imperative call sites without an interface, use `RestClient` (the synchronous successor to
`RestTemplate`). Use `WebClient` only inside a reactive pipeline.

Build clients from the injected builder so Boot's timeouts, observability and SSL bundles apply;
`new RestTemplate()` or `WebClient.create()` bypasses all of it. Under Spring Framework 7's
JSpecify annotations, `RestClient`'s `body(...)` is explicitly nullable — a Kotlin caller will be
forced to handle it, and Java code should too.

## Timeouts and resilience

Every outbound call gets a connect and a read timeout; the JDK default is "wait forever", which
turns one slow dependency into an exhausted thread pool. Retries, concurrency limits and
circuit-breaking come from core Spring Framework in Boot 4 — `@Retryable` and `@ConcurrencyLimit`
from `org.springframework.resilience.annotation` with `@EnableResilientMethods`, not the separate
`spring-retry` dependency. Retry only idempotent operations, and only on transient failures.

## WebFlux specifics

- Return `Mono`/`Flux`; never call `block()` or `subscribe()` in request-handling code. The
  framework subscribes.
- Blocking work that cannot be avoided goes on `Schedulers.boundedElastic()` at the adapter
  boundary. `Mono.just(jdbcCall())` still blocks — the call happens during assembly.
- Bound `flatMap` concurrency to what the downstream can take; unbounded `flatMap` is an
  unintentional load test.
- Request-scoped data goes in the Reactor `Context`, not a `ThreadLocal`.
- Avoid `onErrorContinue`; it silently skips elements. Use `onErrorResume` with a defined fallback.
- Test publishers with `StepVerifier` including cancellation, empty and error paths.

<!-- sources: rrezart-spring-boot, spring-docs, spring-boot-wiki, awesome-copilot -->
