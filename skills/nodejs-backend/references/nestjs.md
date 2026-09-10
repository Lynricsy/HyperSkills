# NestJS branch

Verified against: NestJS 12

## Contents

- [Read the project before advising](#read-the-project-before-advising)
- [Modules by capability](#modules-by-capability)
- [Providers and injection tokens](#providers-and-injection-tokens)
- [Provider scopes and the bubble-up cost](#provider-scopes-and-the-bubble-up-cost)
- [Request context without request scope](#request-context-without-request-scope)
- [The request pipeline](#the-request-pipeline)
- [Validation: the pipe defaults are wrong](#validation-the-pipe-defaults-are-wrong)
- [Exception filters and their three blind spots](#exception-filters-and-their-three-blind-spots)
- [Lifecycle hooks and shutdown](#lifecycle-hooks-and-shutdown)
- [Logging](#logging)
- [Express or Fastify underneath](#express-or-fastify-underneath)
- [Testing](#testing)

## Read the project before advising

Read `package.json`, `nest-cli.json`, `main.ts` and the root module's import
graph before recommending anything structural. In particular do not label a
project "Clean Architecture", "hexagonal" or "DDD" from folder names: a `domain/`
directory next to services that import the ORM entity is none of those, and
advice premised on the label will contradict the code.

State the current architecture in one sentence first. Then flag a convention
only when it damages correctness, security or operability — not because it
differs from a preferred layout.

## Modules by capability

Group by business capability, not by technical layer. `orders/` containing its
controller, service, repository and DTOs is navigable; `controllers/`,
`services/`, `repositories/` with the same feature spread across three
directories means every change touches three places and no boundary is
enforceable.

The file-naming convention is worth keeping because tooling and readers both
rely on it: `*.controller.ts`, `*.service.ts`, `*.module.ts`, `*.dto.ts`,
`*.entity.ts`, `*.guard.ts`, `*.interceptor.ts`, `*.pipe.ts`, `*.filter.ts`.
`common/` holds cross-cutting decorators, filters, guards, interceptors and
pipes; `config/` holds configuration; feature modules live side by side.

A module's public surface is its `exports`. Anything not exported is private, so
prefer exporting a small service over exporting the repository — an exported
repository lets another module write to your tables and the boundary is gone.

Circular imports between modules are a design signal, not a wiring problem.
`forwardRef` makes the cycle compile and keeps the cycle; extracting the shared
piece into a third module removes it.

## Providers and injection tokens

Constructor injection with `private readonly` parameters. Property injection
(`@Inject()` on a field) cannot be satisfied by a constructor call, so the class
becomes untestable without the container, and it hides how many collaborators
the class has accumulated.

For anything you want to substitute — an outbound client, a clock, a gateway —
inject against an interface through a token:

```ts
export const PAYMENT_GATEWAY = Symbol('PAYMENT_GATEWAY')

@Module({
  providers: [{ provide: PAYMENT_GATEWAY, useClass: StripeGateway }],
  exports: [PAYMENT_GATEWAY],
})
export class PaymentModule {}

@Injectable()
export class Checkout {
  constructor(@Inject(PAYMENT_GATEWAY) private readonly gateway: PaymentGateway) {}
}
```

Interfaces vanish at runtime, so the token is what the container resolves. A
`Symbol` avoids the string-collision class of bug entirely.

Resist `ModuleRef.get()` inside methods. It is the service-locator pattern: the
dependency no longer appears in the constructor, so nothing tells you what the
class needs and a missing provider fails at call time. Its legitimate uses are
dynamic resolution by a key computed at runtime and resolving a scoped provider
from a singleton context.

## Provider scopes and the bubble-up cost

Three scopes: `DEFAULT` (singleton), `REQUEST`, `TRANSIENT`. Singleton is the
right answer for nearly everything, because Node does not use a
thread-per-request model — sharing an instance across requests is safe as long
as the instance holds no per-request state.

`REQUEST` scope **bubbles up the injection chain**. If `OrdersService` is
request-scoped, `OrdersController` becomes request-scoped too, and so does
anything else that injects it. A common dependency — a database wrapper, a
logger — turned request-scoped therefore converts most of the application, and
30 000 concurrent requests mean 30 000 ephemeral instances plus garbage
collection.

Places request scope is not allowed at all: WebSocket gateways (each wraps one
real socket), Passport strategies, cron controllers. They must be singletons.

`durable` providers exist for the one shape where request scope is tempting and
wrong: multi-tenancy, where the aggregation key is the tenant rather than the
request. They give one DI sub-tree per tenant instead of one per request. Reach
for them only after measuring; they are a specialised tool.

## Request context without request scope

The default answer for request id, tenant, user and trace context is
`AsyncLocalStorage`, which keeps every provider a singleton. `nestjs-cls`
packages it; plain `AsyncLocalStorage` in middleware works identically.

The mistake this replaces is a mutable field on a singleton:

```ts
@Injectable()
export class AuditService {
  private currentUserId: string | null = null    // shared by every request
  bindRequest(id: string) { this.currentUserId = id }
}
```

Request A sets the field, awaits a query, and request B overwrites it during
that await. A then logs B's user. It passes every test and fails under load.

Where to enter the store matters:

- **Middleware** wraps the most (`als.run(store, next)`) but runs *before*
  guards, so `request.user` is not populated yet.
- **An interceptor** runs after guards, so the principal is available — but
  `next.handle()` only *builds* the observable; Nest subscribes after
  `intercept()` returns, by which time `run()` has exited. Enter the store
  around the subscription, not around the call:

```ts
intercept(ctx: ExecutionContext, next: CallHandler): Observable<unknown> {
  const store = buildStore(ctx.switchToHttp().getRequest())
  return new Observable((subscriber) =>
    als.run(store, () => next.handle().subscribe(subscriber)),
  )
}
```

The practical combination is: enter in middleware with the ids, and have the
guard write the principal into the existing store rather than starting a second
one.

## The request pipeline

```
middleware → guards → interceptors (before) → pipes → handler
           → interceptors (after) → exception filters
```

Each layer has exactly one job:

| Layer | Job | Wrong use |
|---|---|---|
| middleware | framework-level concerns, context entry | authorization (runs before guards can set the principal) |
| guard | may this caller proceed | transforming the body |
| interceptor | cross-cutting around the call: timing, caching, mapping | authorization (runs after guards for a reason) |
| pipe | validate and transform one argument | side effects |
| filter | turn a thrown error into a response | business logic |

Guards run before interceptors and pipes, which is why a guard cannot rely on a
validated DTO. Authorization that depends on the request body belongs in the
service, not in a guard.

Keep controllers thin: bind, delegate, map. A controller that queries the
database has no seam for a test and duplicates itself at the next entry point
(a queue consumer, a CLI).

## Validation: the pipe defaults are wrong

`new ValidationPipe()` on its own lets unknown properties through to the
handler. The production configuration is:

```ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,             // strip properties with no decorator
  forbidNonWhitelisted: true,  // ...or reject the request instead
  transform: true,             // instantiate the DTO class, apply @Type
}))
```

Why each matters: without `whitelist`, a client can send `isAdmin: true` into a
DTO that never declared it and a downstream `Object.assign` writes it.
`forbidNonWhitelisted` turns silent stripping into a 400, which is the better
default on write endpoints — a client that misspelled `discount` should hear
about it. Without `transform`, the parameter is a plain object, so
`class-transformer` decorators and nested validation do not run.

Write a separate DTO per operation (`CreateOrderDto`, `UpdateOrderDto`,
`ListOrdersQueryDto`); reusing one with everything optional means the create
path validates nothing. Nested objects need `@ValidateNested({ each: true })`
plus `@Type(() => Child)`, or the children are never validated.

Serialising **out** is the other half. `ClassSerializerInterceptor` with
`@Exclude()` on sensitive entity fields is the Nest equivalent of a response
schema; returning an ORM entity directly ships every column, including the ones
added since the endpoint was written.

## Exception filters and their three blind spots

A global filter for unexpected errors, plus narrower `@Catch(SpecificError)`
filters for the domain errors you raise:

```ts
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  constructor(private readonly logger: LoggerService) {}

  catch(exception: unknown, host: ArgumentsHost): void {
    // 1. This filter also runs for queue workers, gateways and microservices,
    //    where there is no HTTP response to write.
    if (host.getType() !== 'http') {
      this.logger.error('non-http failure', exception as Error)
      throw exception
    }

    const res = host.switchToHttp().getResponse()
    // 2. A streamed or already-started response cannot be re-headered.
    if (res.headersSent) {
      this.logger.error('failure after headers sent', exception as Error)
      return
    }

    const status = exception instanceof HttpException ? exception.getStatus() : 500
    this.logger.error('request failed', exception as Error)
    res.status(status).json(
      exception instanceof HttpException
        ? { code: codeOf(exception), requestId: currentRequestId() }
        : { code: 'INTERNAL', requestId: currentRequestId() },
    )
  }
}
```

The third blind spot: errors thrown **outside** a request — in a lifecycle hook,
a timer, a queue consumer's own scheduling — never reach any filter. Those paths
need their own logging and their own effect on process exit (see
`lifecycle-and-shutdown.md`).

Throw Nest's built-in exceptions (`NotFoundException`, `ConflictException`,
`BadRequestException`) or subclass the closest one and attach a stable `code`.
Never format an error response by hand in a controller: that is how an API ends
up with four error shapes.

Register the global filter as a provider (`{ provide: APP_FILTER, useClass:
... }`) rather than `app.useGlobalFilters(new ...)` when it needs injected
dependencies — the `useGlobalFilters` form is constructed outside the container.

## Lifecycle hooks and shutdown

Order on the way up: `onModuleInit` (per module, bottom-up) →
`onApplicationBootstrap` (everything initialised). On the way down:
`onModuleDestroy` → `beforeApplicationShutdown` → `onApplicationShutdown`.

Two rules:

- Connect in `onModuleInit`, and **await it**. `onModuleInit() { this.pool.connect() }`
  without `async`/`await` reports the module ready while the pool is still
  connecting, so early requests fail with an unrelated error. Cross-module
  warm-up goes in `onApplicationBootstrap`, where every module is initialised.
- Do work in hooks, not in constructors. A constructor cannot be awaited or
  retried, and blocking there blocks the whole wiring phase.

**Shutdown hooks are disabled by default.** Without `app.enableShutdownHooks()`
in `main.ts`, `SIGTERM` ends the process and no `onModuleDestroy` runs — so a
rolling deploy loses whatever those hooks were supposed to flush. Nest keeps
them off because the listeners cost resources and multiple apps in one process
(parallel tests) then exceed Node's listener limit.

```ts
const app = await NestFactory.create(AppModule)
app.enableShutdownHooks()
await app.listen(config.port)
```

Also note that `app.close()` runs the hooks but does **not** terminate the
process: an outstanding interval or watcher keeps it alive afterwards. Clear
them in `onModuleDestroy`, and await any in-flight work before closing the
store it writes to. `SIGTERM` does not exist on Windows; `SIGINT` does.

## Logging

The `Logger` from `@nestjs/common` takes a message and an optional context
string — it does not accept a structured-metadata object the way pino does, so
`logger.log({ orderId })` stringifies the object into the message. A project
that wants queryable logs replaces the logger (`nestjs-pino` is the usual
choice) and injects `LoggerService`, rather than passing objects to the default
logger.

Pass the error, not `error.message`, so the stack is recorded. Bind the request
id from the context store (above) so every line correlates.

## Express or Fastify underneath

`@nestjs/platform-express` is the default; `@nestjs/platform-fastify` is
supported. Which one is installed changes: the request and response object types
in filters, interceptors and middleware; what `getRequest()` returns; and which
third-party middleware works at all.

If the project uses the Fastify adapter, its request lifecycle, hook semantics
and error-handler behaviour are Fastify's — read `fastify.md` for those and stay
here for modules, providers and DI. Do not write `@Res() res: Response` from
`express` in a project on the Fastify adapter.

Reaching for `@Res()` at all opts that handler out of Nest's response
handling — interceptors and serialisation stop applying to it. Use it only for
a genuine streaming or raw-response case, and know what you gave up.

## Testing

```ts
const moduleRef = await Test.createTestingModule({ imports: [OrdersModule] })
  .overrideProvider(PAYMENT_GATEWAY).useValue(stubGateway)
  .compile()

const app = moduleRef.createNestApplication()
await app.init()                                  // no listen: no port
await request(app.getHttpServer()).post('/orders').send({ items: [] }).expect(400)
await app.close()
```

`overrideProvider` is the reason tokens matter: it is how a real module is
compiled with one collaborator replaced, without a module-mocking library.
`app.init()` gives a working HTTP server object without binding a port.
`app.close()` in teardown is not optional — a testing module that is never
closed keeps its pools open and the suite hangs.

Test the service directly (plain construction, stub collaborators) for business
logic; go through `getHttpServer()` when the assertion is about routing,
validation, serialisation or a filter — the layers a direct service call skips.

Resolving a request-scoped provider in a test needs `moduleRef.resolve()`, not
`moduleRef.get()`, which is one more reason to keep providers singleton.

<!-- sources: kadajett-nestjs, myatminlu-nestjs, amirtaherkhani-nestjs, awesome-copilot, nestjs-docs, nodejs-docs -->
