# Spring Modulith

Verified against: Spring Modulith 2.x with Spring Boot 4.1.

Spring Modulith gives a single deployable a verifiable internal structure: named modules, an
explicit public API per module, and events as the supported way to cross a boundary. It is worth
adding when a monolith already has recognisable feature areas that keep leaking into each other.
It is not worth adding to a service that has one feature, and it is never worth adding as a side
effect of an unrelated change.

Match the Modulith 2.x line to the exact Boot 4 minor. A Boot 3-era Modulith 1.x BOM against Boot 4
fails in ways that look like your own wiring.

## Module layout

Each direct subpackage of the application's root package is a module.

```
com.example.shop            <- @SpringBootApplication
├── order                   <- module API: what other modules may call
│   └── internal            <- implementation; unreachable from other modules
├── inventory
│   └── internal
└── shared                  <- avoid: see below
```

- Keep the module's API — the types other modules are allowed to touch — at the module root, and
  everything else in `internal` subpackages.
- Expose a *named interface* only for an intentional shared API, not to make a compile error go
  away.
- Use `@ApplicationModule(allowedDependencies = …)` when the architecture needs the dependency
  direction pinned rather than merely acyclic.
- Resist a generic `shared`/`common` module that every feature depends on: it becomes the place
  where boundaries go to die, and the cycle checker cannot see through it.

## Verification

```java
class ModularityTests {
    @Test
    void verifiesModuleStructure() {
        ApplicationModules.of(ShopApplication.class).verify();
    }
}
```

Add `spring-modulith-starter-test` in test scope and run this in CI. `verify()` fails on cycles
between modules and on access to another module's `internal` package. `@ApplicationModuleTest`
bootstraps a single module for behaviour tests, which is much cheaper than `@SpringBootTest`.

A passing structure check proves nothing about transactional or delivery correctness. It is a
compile-time-shaped guarantee only.

## Events across modules

Publish an immutable event carrying ids and the facts the consumer needs. Publishing a managed JPA
entity hands another module a lazy-loading proxy attached to a persistence context that is about to
close.

```java
// order module
events.publishEvent(new OrderPlaced(order.getId(), order.getTotal()));

// inventory module
@ApplicationModuleListener                    // async + transactional + after-commit
void on(OrderPlaced event) { … }
```

`@ApplicationModuleListener` combines `@Async`, `@Transactional(propagation = REQUIRES_NEW)` and
`@TransactionalEventListener(AFTER_COMMIT)`. That covers ordering, but not durability: an in-memory
registry loses events on a crash between commit and handling.

For delivery that must survive a restart, add the JDBC or JPA event publication registry starter
and manage its schema through your normal migrations. Then:

- Make handlers idempotent. A crash after the business effect but before the completion record is
  written causes redelivery.
- Configure republication on startup, retry policy and retention explicitly; the defaults are not
  a delivery guarantee.
- Test the failing listener and the restart, not just the happy path.
- For an external broker, use the supported event externalisation with persistent publication
  tracking. Do not promise end-to-end exactly-once — the registry gives at-least-once.

<!-- sources: rrezart-spring-boot, spring-docs -->
