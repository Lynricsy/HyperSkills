---
name: java-spring
description: "Guides Spring Boot work end to end: auto-configuration and configuration properties, Spring MVC versus WebFlux and RFC 9457 error contracts, declarative HTTP service clients, Spring Data JPA (entity mapping, transaction boundaries, self-invocation, N+1, projections, Flyway), Spring Security 7 (lambda DSL filter chains, OAuth2 resource server, method security), slice and Testcontainers testing with @MockitoBean, Spring Modulith, Actuator and Micrometer, Maven and Gradle builds, container and GraalVM native packaging, Spring Boot 3.5 to 4 migration, and Java 17 to 25 upgrades including records, sealed types, pattern matching and virtual threads. Use when writing, reviewing, debugging, testing, upgrading or packaging Spring Boot services, or when reading pom.xml, build.gradle.kts, application.yml, an @Entity, a SecurityFilterChain or a @SpringBootTest. Do not use for Android or Kotlin mobile development, cloud hosting on AWS, Azure or GCP, or REST contract and OpenAPI design."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# java-spring

## Scope

Covers server-side Java (and Kotlin) applications built on Spring Boot: the auto-configuration and
configuration-property model, the web layer in both Spring MVC and WebFlux, outbound HTTP,
persistence with Spring Data JPA and its transaction semantics, Spring Security, testing at every
slice, Spring Modulith, Actuator/Micrometer instrumentation, the Maven or Gradle build, container
and GraalVM native packaging, the Spring Boot 3.5 → 4 migration, and the Java 17 → 21 → 25 language
upgrade a Spring codebase goes through alongside it.

The body is written against **Spring Boot 4.1**, the current GA line. Where Spring Boot 3.5 differs,
the difference is in `references/boot-4-migration.md` rather than duplicated inline.

Not covered:

- Android and Kotlin mobile development, including Kotlin coroutines on Android — use the `android`
  skill.
- Reviewing a diff for general correctness and style — use the `code-review` skill; come back here
  for the Spring-specific rules a reviewer applies.
- Working a reproducible local failure down to a root cause — use the `debugging` skill.
- Test-first methodology and what deserves a test at all — use the
  `test-driven-development` skill; this skill covers which Spring slice a test belongs in.
- REST contract and OpenAPI specification design. Use the `api-design` skill.
  GraphQL schema and operations: use the `graphql` skill. PostgreSQL schema, indexing and
  query tuning behind JPA: use the `postgres` skill.
- Kubernetes manifests and container images: use the `containers` skill; the cloud
  infrastructure underneath them: `terraform`.
- Cloud provider SDKs and managed services (AWS, Azure, GCP), Spring Cloud Gateway,
  Spring Batch and Spring AI. None of these has a skill in this library yet; say so
  rather than improvising.

Paths below are relative to this skill's directory.

## Core rules

1. Read `pom.xml` or `build.gradle.kts` plus `application.yml` before changing anything. The Spring
   Boot major version decides starter names, test annotations, the JSON library and the security
   DSL — every rule below branches on it.
2. Let the Boot BOM manage versions. A pinned Hibernate, Jackson or Jakarta version produces a
   combination nobody tested, and the failure appears at runtime as `NoSuchMethodError`.
3. Constructor injection with `private final` fields. Field injection cannot be constructed in a
   test and hides how many collaborators a class has accumulated.
4. Declaring your own bean of a type Boot auto-configures switches Boot's version off entirely
   through `@ConditionalOnMissingBean`. Run with `--debug` and read the condition evaluation report
   before adding a bean to force behaviour.
5. Bind related settings with one `@ConfigurationProperties` record, register it with
   `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`, and add `@Validated`. A
   properties class that is never registered binds nothing and fails silently at runtime instead of
   at startup.
6. Durations and sizes in configuration carry units (`5s`, `10MB`). A bare number is a
   factor-of-1000 outage waiting for the first timeout.
7. Choose Spring MVC unless the whole request path is non-blocking. One JDBC call or one `block()`
   on a Reactor event loop costs more than MVC ever would; with virtual threads MVC handles
   I/O-bound concurrency without the reactive model.
8. Accept and return records at the web boundary. Returning a JPA entity leaks the schema and
   serialises lazy associations outside the transaction.
9. One error contract per API, and for a new API that is RFC 9457 Problem Details. Authentication
   and authorization failures happen before the dispatcher servlet, so `@RestControllerAdvice`
   cannot see them — configure an `AuthenticationEntryPoint` and an `AccessDeniedHandler` too.
10. `@Transactional` belongs on service methods, with the class marked `readOnly = true` and
    writers overriding it. On a controller it spans view rendering; on a repository it cannot
    compose.
11. `@Transactional` and `@PreAuthorize` are proxy-based: an internal `this.method()` call, a
    `private` method or a `final` method is silently unadvised. Move the inner method to its own
    bean rather than changing the annotation.
12. Rollback happens on unchecked exceptions only. A checked exception needs
    `rollbackFor`, and catching an exception after any participant marked the transaction
    rollback-only still fails the commit with `UnexpectedRollbackException`.
13. Never send mail, publish to a broker or invalidate a cache inside the transaction. Publish an
    application event and act on `@TransactionalEventListener(AFTER_COMMIT)` — a rollback cannot
    unsend an e-mail.
14. Map enums with `@Enumerated(EnumType.STRING)` and version with a wrapper `Long`. `ORDINAL`
    remaps every row when a constant is inserted, and a primitive `version` breaks Spring Data's
    new-entity detection because JPA reads `0` as already persisted.
15. Set `fetch = FetchType.LAZY` on every `@ManyToOne` and `@OneToOne`; both default to eager. Keep
    Lombok `@Data` off entities — the generated `equals`/`hashCode`/`toString` walks associations
    and triggers lazy loads.
16. Fix an N+1 with a projection first, an `@EntityGraph` second, a `join fetch` third. Never
      `join fetch` two collections in one query: the cartesian product forces in-memory pagination.
17. Set `spring.jpa.open-in-view=false` and fix what breaks. Left on, every lazy association
    resolves during view rendering, outside a transaction, on a connection held for the whole
    request.
18. Own the schema with Flyway or Liquibase, never `ddl-auto` above `validate`. In Spring Boot 4
    the migration tool needs its own starter — without `spring-boot-starter-flyway` the application
    starts happily and never runs a migration.
19. Spring Security 7 has no `WebSecurityConfigurerAdapter`, no `and()` chaining, no
    `authorizeRequests()` and no `antMatchers()`. Declare a `SecurityFilterChain` bean and use the
    lambda DSL with `requestMatchers`.
20. Put `@PreAuthorize` on the service, not the controller: the controller is one entry point, the
    service is the boundary. Scopes are authorities, so a scope check is
    `hasAuthority("SCOPE_orders:read")`, never `hasRole`.
21. Use the narrowest test slice that gives confidence, and `@MockitoBean`/`@MockitoSpyBean` for
    collaborators — `@MockBean` and `@SpyBean` were removed in Boot 4.
22. In a `@DataJpaTest`, set data up through `TestEntityManager` and call `flush()` then `clear()`
    before asserting. Without `clear()` the assertion is served from Hibernate's first-level cache
    and the query is never executed, so the test passes while proving nothing.
23. Run repository tests against the real engine with Testcontainers and `@ServiceConnection`. An
    embedded database has different SQL, types and constraint behaviour, so a green H2 test says
    nothing about production.
24. Keep the Spring context cache key stable — same classes, same properties, same mocked types.
    A slow suite is almost always many nearly identical contexts, not slow tests.
25. Never expose all actuator endpoints, and never tag a metric with a user id, an entity id or an
    exception message. `env` and `heapdump` publish your configuration and its secrets; a
    high-cardinality tag creates one time series per value.

## Workflows

### implement-feature

- [ ] Read the build file, `application.yml` and one existing feature package; adopt its layering,
      naming and error contract instead of introducing a second one.
- [ ] Define the API types first as records (request, response, and the domain event if any).
- [ ] Write the persistence layer: entity per rule 14/15, repository per aggregate root, migration
      script. Decide the query shape before writing the method name.
- [ ] Write the service: `@Transactional(readOnly = true)` on the class, writers overriding it,
      no remote call and no side effect inside the transaction (rules 10, 13).
- [ ] Write the controller last: bind, validate with `@Valid`, delegate, map to a response record.
- [ ] Add authorization at the service boundary and confirm the route is covered by the filter
      chain's matchers.
- [ ] Add tests per `add-tests`.
- [ ] **Gate:** `./mvnw verify` (or `./gradlew build`) passes, and starting the application on the
      target profile logs no `spring-boot-properties-migrator`-style binding warnings.

### add-tests

- [ ] Choose the slice from the table in `references/testing.md` before writing a line; default to
      plain JUnit + Mockito for service logic.
- [ ] Controller: `@WebMvcTest` with `@MockitoBean` collaborators and `@WithMockUser`, asserting
      status, validation failures and the error body shape.
- [ ] Repository: `@DataJpaTest` with Testcontainers, `TestEntityManager` setup, `flush()`+`clear()`
      before every read assertion (rules 22, 23).
- [ ] Outbound client: `@RestClientTest` with `MockRestServiceServer`, asserting the request that
      was issued, not just the stubbed reply.
- [ ] Reserve `@SpringBootTest` for paths that genuinely need every layer, and add
      `@AutoConfigureMockMvc` or `@AutoConfigureRestTestClient` explicitly.
- [ ] Do not test getters, framework wiring or Spring's own auto-configuration.
- [ ] **Gate:** the suite passes, each new test fails when the behaviour it covers is broken, and
      the number of distinct Spring contexts did not grow.

### review

- [ ] Establish the diff scope and read its tests first — they state what the author believes the
      code does.
- [ ] Walk the Core rules in order; they are ordered by how often each one is the real defect.
- [ ] Check the transaction surface specifically: boundary placement, self-invocation, side effects
      inside the transaction, missing `readOnly`, rollback rules.
- [ ] Check the persistence surface: eager fetches, enum mapping, N+1 in a loop or in
      serialisation, unbounded `findAll`, an entity crossing the web boundary.
- [ ] Check the security surface: matcher order, a route that no rule covers, `hasRole` used for a
      scope, method security on the controller only.
- [ ] Check the build diff separately: a pinned managed version, a new starter duplicating an
      existing one, a test dependency that should be a technology test starter.
- [ ] Report with the Output format below.
- [ ] **Gate:** every finding carries `path:line`, one line of reasoning and a concrete fix.

### diagnose-runtime

- [ ] Reproduce and classify: startup failure, wrong behaviour, slow endpoint, or memory/connection
      exhaustion. They have different first moves.
- [ ] Startup: read the failure analyzer message, then `--debug` for the condition evaluation
      report, then `/actuator/configprops` and `/actuator/env` for what actually bound.
- [ ] Slow endpoint: turn on `org.hibernate.SQL` and `hibernate.generate_statistics` in a
      non-production profile and count queries before theorising. N+1 and a missing index look the
      same from the outside.
- [ ] Connection or thread exhaustion: look for a remote call inside a transaction, a
      `REQUIRES_NEW` loop, or a pool sized for the old thread model after enabling virtual threads.
- [ ] Wrong behaviour after an upgrade: diff `/actuator/configprops` against the previous version
      before reading any changelog.
- [ ] **Gate:** the fix is stated as a causal chain from an observed number or log line, and the
      same observation is repeated after the change.

### migrate-boot-4

- [ ] Get onto the newest 3.5.x first with every deprecation warning cleared; deprecated APIs are
      deleted in 4.0.
- [ ] Confirm the baseline: Java 17+, Kotlin 2.2+, Servlet 6.1 container, GraalVM 25+ if native,
      a Boot 4-compatible Spring Cloud train.
- [ ] Work through `references/boot-4-migration.md` in order: starters, test starters, removed
      features, Jackson 3, Security 7, relocated types, properties, tests.
- [ ] Keep the diff free of behaviour changes so any post-upgrade failure is attributable.
- [ ] **Gate:** the application starts on every profile with `spring-boot-properties-migrator`
      reporting nothing, `/actuator/configprops` diffs cleanly against the 3.5 capture, and the
      integration suite passes against real infrastructure.

### upgrade-java

- [ ] Run the build and tests on the new JDK with `release` unchanged, to separate runtime problems
      from language problems.
- [ ] Upgrade the bytecode-manipulating tools first — Lombok, Mockito, ByteBuddy, JaCoCo — since a
      `ClassFormatError` naming an ASM class is always one of them.
- [ ] Raise the `release` level, then adopt language features in separate reviewable commits.
- [ ] Before enabling virtual threads, size the connection pool for the new concurrency and, on
      Java 21–23, audit `synchronized` blocks around I/O for pinning.
- [ ] **Gate:** the suite passes on the new JDK, the startup log shows no new agent/`Unsafe`
      warnings, and a load-shaped smoke test shows the connection pool is not the new bottleneck.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Auto-configuration and configuration | Beans, conditions, `@ConfigurationProperties`, profiles, JSpecify, startup diagnosis | `references/boot-configuration.md` |
| Web layer and HTTP clients | Controllers, validation, error contracts, MVC vs WebFlux, `@HttpExchange` clients | `references/web-and-clients.md` |
| Data JPA and transactions | Entities, transactions, N+1, projections, pagination, locking, migrations | `references/data-jpa.md` |
| Security | Filter chains, Security 7 removals, OAuth2 resource server, method security, CSRF/CORS | `references/security.md` |
| Testing | Choosing a slice, `@MockitoBean`, Testcontainers, context caching | `references/testing.md` |
| Spring Modulith | Module boundaries, verification, reliable module events | `references/modulith.md` |
| Observability | Actuator exposure, health probes, Micrometer observations, structured logs, alerts | `references/observability.md` |
| Build and packaging | Maven/Gradle version management, multi-module layout, images, AOT, native | `references/build-and-packaging.md` |
| Spring Boot 3.5 → 4 migration | Any upgrade work, or deciding whether a rule applies to 3.5 | `references/boot-4-migration.md` |
| Java language upgrade | Moving JDK version, records/sealed/pattern matching, virtual threads | `references/java-language.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by severity,
with no preamble:

```
src/main/java/com/example/order/OrderService.java
  L31 blocking - submitBatch calls this.submitOne(id), so the proxy is bypassed and
       REQUIRES_NEW never takes effect; every item shares the outer transaction.
       before: ids.forEach(id -> this.submitOne(id));
       after:  ids.forEach(id -> orderProcessor.submitOne(id));   // separate bean
  L38 blocking - confirmation e-mail is sent inside the transaction; a later rollback
       cannot unsend it. Publish OrderSubmitted and handle it in
       @TransactionalEventListener(phase = AFTER_COMMIT).
  L45 important - findAll() then getItems()/getCustomer() per row is an N+1 over the whole
       table. Use a projection query filtered by status.

src/main/java/com/example/order/Order.java
  L28 important - @Enumerated(EnumType.ORDINAL): inserting an enum constant silently
       remaps existing rows. Use EnumType.STRING with an explicit length.
```

Severities: `blocking` (data loss, wrong behaviour, security hole, removed API), `important`
(N+1, leaked entity, missing transaction boundary, missing test slice), `minor` (naming, dead
code, style). End with a one-line verdict: ship, ship after blocking fixes, or rework.

## Environment

JDK 17 or newer (21 or 25 recommended); Maven or Gradle comes from the project's wrapper.
Testcontainers-backed tests need a running Docker daemon; native image builds need GraalVM 25+.

```bash
./mvnw verify                       # or ./gradlew build
./mvnw spring-boot:run              # or ./gradlew bootRun
./mvnw dependency:tree              # or ./gradlew dependencies
./mvnw spring-boot:build-image      # or ./gradlew bootBuildImage
./mvnw -Pnative native:compile      # or ./gradlew nativeCompile
```

Run the application with `--debug` to print the auto-configuration condition evaluation report.
