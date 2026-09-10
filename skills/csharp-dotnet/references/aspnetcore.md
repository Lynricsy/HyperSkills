# ASP.NET Core

Verified against: ASP.NET Core 10 (.NET 10).

## Contents

- [Endpoint style](#endpoint-style)
- [Minimal API shape](#minimal-api-shape)
- [OpenAPI](#openapi)
- [Errors](#errors)
- [Service lifetimes](#service-lifetimes)
- [Captive dependencies and scope validation](#captive-dependencies-and-scope-validation)
- [Registration organisation](#registration-organisation)
- [Middleware](#middleware)
- [Configuration and options](#configuration-and-options)
- [HttpClient](#httpclient)
- [Authentication and authorization](#authentication-and-authorization)
- [Background work](#background-work)
- [EF Core on the request path](#ef-core-on-the-request-path)

## Endpoint style

Scan `Program.cs` and the project for `app.MapGet`/`MapPost` and for classes deriving from
`ControllerBase` before writing anything, and continue with whichever is already there. Do not
mix the two styles in one project. For a new project, default to minimal APIs; use controllers
when you need model binding conventions, filters by attribute, or an existing MVC/Razor Pages
surface.

## Minimal API shape

```csharp
var orders = app.MapGroup("/orders")
                .WithTags("Orders")
                .RequireAuthorization();

orders.MapGet("/{id:int}", async Task<Results<Ok<OrderResponse>, NotFound>> (
        int id, IOrderRepository repo, CancellationToken ct) =>
    await repo.FindAsync(id, ct) is { } order
        ? TypedResults.Ok(order.ToResponse())
        : TypedResults.NotFound())
    .WithName("GetOrder");
```

- `MapGroup` for a shared prefix, shared metadata, shared auth and shared filters.
- `TypedResults` plus an explicit `Results<T1, T2>` union, so the generated OpenAPI document
  gets the real status codes and schemas. Plain `Results.Ok(x)` erases the type.
- Dedicated `sealed record` request and response types. Never bind or return an EF Core
  entity: it drags navigation properties, lazy loading and your storage shape into the
  contract.
- `DateTimeOffset` rather than `DateTime` in DTOs, so the offset survives serialisation.
- Take `CancellationToken` in the handler; ASP.NET Core binds the request-aborted token to it.
- Validation on a minimal API is not automatic in the way `[ApiController]` model validation
  is. Use an endpoint filter or an explicit validation call, and return
  `TypedResults.ValidationProblem`.
- Keep handlers thin: a handler that is more than about 20 lines belongs in a service that the
  handler calls, so it can be tested without the pipeline.

## OpenAPI

`builder.Services.AddOpenApi()` plus `app.MapOpenApi()` produce the document from the built-in
support (no Swashbuckle needed). Fill it from the code rather than from attributes where you
can:

- XML doc comments on DTOs and handlers become schema and operation descriptions when
  `GenerateDocumentationFile` is on.
- `WithName` sets `operationId`; `WithSummary`/`WithDescription` set the prose.
- Document transformers add servers, tags and security schemes; schema transformers adjust
  generated schemas. Both are registered on `AddOpenApi`.
- `[Description]` on parameters and properties for the rest.

## Errors

- Register `AddProblemDetails()` and use `UseExceptionHandler` plus `UseStatusCodePages` so
  every unhandled failure and every bare status code becomes RFC-shaped `ProblemDetails`.
- Return the specific typed result for expected outcomes (`NotFound`, `Conflict`,
  `ValidationProblem`); reserve exceptions for genuinely exceptional states.
- Never let an exception message reach the client in production. `UseDeveloperExceptionPage`
  is Development only.

## Service lifetimes

| Lifetime | One instance per | Use for |
|---|---|---|
| Transient | Resolution | Cheap, stateless helpers |
| Scoped | Request (or explicitly created scope) | Anything holding per-request state: `DbContext`, unit of work, the current user |
| Singleton | Application | Expensive-to-create, genuinely shared, thread-safe state |

- A singleton must be thread-safe; the container's own thread safety only covers resolving
  services, not using them.
- Do not register `IDisposable` as transient and resolve it from the root container: the
  container holds the reference until the process exits, which is a slow leak. Use a factory,
  or make it scoped and dispose the scope.
- Do not put request data (a shopping cart, the current user's id) in the container. Use the
  options pattern for configuration and pass data as arguments.
- Never call `BuildServiceProvider()` while configuring: it creates a second container with
  duplicate singletons, so half the app gets a different instance. Use the registration
  overload that hands you an `IServiceProvider`, or bind configuration directly.
- Keep DI factories fast and synchronous. Calling `.Result` inside an implementation factory
  deadlocks.

## Captive dependencies and scope validation

A singleton that takes a scoped service in its constructor keeps the first instance forever.
The scoped service is effectively promoted to singleton lifetime, which produces:

- stale data (the captured `DbContext` never sees another request's changes);
- concurrency failures — `A second operation was started on this context instance` is the
  canonical symptom;
- cross-request leakage of anything the scoped service holds.

Fixes, in preference order:

1. Do not hold the scoped service. Inject `IServiceScopeFactory` (or `IDbContextFactory<T>`)
   and create a scope per operation.
2. Move the consumer to scoped, if it does not actually need to be shared.
3. Extract the genuinely shared, immutable part into the singleton and leave the rest scoped.

Scope validation detects this at startup, but it is enabled by default **only in the
Development environment**. To make it fail everywhere:

```csharp
builder.Host.UseDefaultServiceProvider(options =>
{
    options.ValidateScopes = true;    // scoped resolved from root -> throw
    options.ValidateOnBuild = true;   // unresolvable/captive graphs -> throw at startup
});
```

`ValidateOnBuild` costs a little startup time and turns a class of production-only bug into a
build-out failure. Turn it on.

## Registration organisation

Group registrations into `Add{Feature}` extension methods on `IServiceCollection` that return
`IServiceCollection`, placed next to the feature they register. That is the framework's own
convention, it keeps `Program.cs` readable, and it lets an integration test reuse the exact
production wiring and override only what it must.

Keyed services (`AddKeyedSingleton`/`AddKeyedScoped`/`AddKeyedTransient` with
`[FromKeyedServices("name")]` at the injection point) replace the old "inject a factory and
switch on a string" pattern when you need several implementations of one interface.

Registering the same service type twice means the last registration wins for a single resolve,
while `IEnumerable<TService>` yields all of them in registration order. `TryAdd*` registers
only if absent — use it in library extension methods so a consumer's own registration is not
overwritten.

## Middleware

- Order is behaviour. The usual spine: exception handler → HSTS/HTTPS redirection → static
  files → routing → CORS → authentication → authorization → endpoints.
- Conventional middleware (a class with a `RequestDelegate` constructor parameter) is
  constructed **once**. A scoped service must arrive as a parameter of `InvokeAsync`;
  constructor injection of a scoped service throws at runtime because it would force the
  service to behave like a singleton.
- Factory-based middleware (`IMiddleware`, registered in DI and activated per request) is the
  alternative when constructor injection is genuinely wanted.
- Always call `await next(context)` unless the middleware is deliberately terminal, and never
  write to the response after `next` has already started it — check `HasStarted`.

## Configuration and options

- Bind to a typed options class, do not read `IConfiguration["Section:Key"]` from business
  code:

```csharp
builder.Services.AddOptions<OrdersOptions>()
    .BindConfiguration("Orders")
    .ValidateDataAnnotations()
    .ValidateOnStart();          // fail at startup, not at first request
```

- `IOptions<T>` for a value fixed at startup, `IOptionsSnapshot<T>` for per-request rebinding,
  `IOptionsMonitor<T>` for a singleton that must observe reloads. Injecting `IOptions<T>` into
  a singleton and expecting reload to work is a common silent bug.
- Configuration sources layer in order; environment variables and user secrets override
  `appsettings.{Environment}.json`, which overrides `appsettings.json`. Secrets belong in user
  secrets locally and in the platform's secret store in production, never in a checked-in file.

## HttpClient

Register a typed client and let the factory own the handler lifetime:

```csharp
builder.Services.AddHttpClient<IPricingClient, PricingClient>(c =>
{
    c.BaseAddress = new Uri(options.PricingBaseUrl);
    c.Timeout = TimeSpan.FromSeconds(10);
})
.AddStandardResilienceHandler();   // Microsoft.Extensions.Http.Resilience: retry, timeout, circuit breaker
```

`new HttpClient()` per call exhausts sockets under load (each disposed handler leaves a socket
in TIME_WAIT); a single static instance never picks up DNS changes. The factory solves both by
rotating pooled handlers.

## Authentication and authorization

- Authentication establishes who the caller is; authorization decides what they may do. Both
  middlewares must be present and in that order.
- Prefer policies over role strings: `AddAuthorization(o => o.AddPolicy("CanEditOrders", p =>
  p.RequireClaim("scope", "orders:write")))`, then `RequireAuthorization("CanEditOrders")` on
  the endpoint or group. A policy is one place to change; scattered `[Authorize(Roles=...)]`
  is not.
- Apply authorization at the group level and opt out with `AllowAnonymous`, so a new endpoint
  is protected by default rather than by memory.
- Validate the token's issuer, audience and lifetime explicitly; do not disable validation to
  make a test pass.
- Anti-forgery is on by default for form posts in Razor components and MVC; keep it.

## Background work

- `BackgroundService` for a long-running loop; `IHostedService` when you only need start/stop
  hooks. Respect the stopping token in every loop and every await.
- A `BackgroundService` is a singleton. To use scoped services inside it, create a scope per
  iteration with `IServiceScopeFactory` — this is the most common captive-dependency site
  after caches.
- On .NET 6 and later an unhandled exception in `ExecuteAsync` stops the host by default.
  Catch, log and decide explicitly inside the loop.

## EF Core on the request path

The full data-modelling story is out of scope here; these are the failures that show up as
ASP.NET Core defects:

- `DbContext` is scoped and not thread-safe. Two concurrent operations on one instance throw
  `InvalidOperationException: A second operation was started on this context instance`. In a
  singleton, a Blazor circuit, or a `Parallel.ForEachAsync` body, use
  `AddDbContextFactory<T>` and create one per unit of work.
- Read-only queries get `AsNoTracking()`. Change tracking on a large read is pure overhead and
  keeps every entity alive for the scope.
- Project to the DTO in the query (`Select(o => new OrderResponse(...))`) rather than loading
  entities and mapping afterwards; that is what stops the query pulling every column.
- The classic N+1 is a loop that touches a navigation property. Use `Include` for a single
  related set, `AsSplitQuery` when multiple `Include`s cause a cartesian explosion, and a
  projection when you only need a few columns.
- Every query in a request path gets the `CancellationToken` overload
  (`ToListAsync(ct)`, `FirstOrDefaultAsync(ct)`).
- Client evaluation of something the provider cannot translate either throws or silently pulls
  the table into memory depending on the construct — check the generated SQL with
  `ToQueryString()` when a query is slow.
- Never call `SaveChangesAsync` inside a loop over items; batch the changes and save once.

<!-- sources: dotnet-official, aspnetcore-docs, dotnet-docs, aaronontheweb, awesome-copilot -->
