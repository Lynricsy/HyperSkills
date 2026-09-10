# Spring Boot 3.5 to 4 migration

Verified against: Spring Boot 4.1 (from 3.5.x).

## Contents

- [Spring Boot 4 differences](#spring-boot-4-differences)
- [Baseline before you start](#baseline-before-you-start)
- [Step 1: starters and modules](#step-1-starters-and-modules)
- [Step 2: test dependencies](#step-2-test-dependencies)
- [Step 3: removed features](#step-3-removed-features)
- [Step 4: Jackson 3](#step-4-jackson-3)
- [Step 5: Spring Security 7](#step-5-spring-security-7)
- [Step 6: relocated types and retry](#step-6-relocated-types-and-retry)
- [Step 7: configuration properties](#step-7-configuration-properties)
- [Step 8: tests](#step-8-tests)
- [Verification](#verification)
- [4.0 versus 4.1](#40-versus-41)

## Spring Boot 4 differences

Everything a Spring Boot 3.5 codebase does differently, in one table. The rest of this skill is
written against 4.x; this is the delta.

| Area | Spring Boot 3.5 | Spring Boot 4 |
|---|---|---|
| Framework / platform | Framework 6, Jakarta EE 10, Servlet 6.0 | Framework 7, Jakarta EE 11, Servlet 6.1 |
| Web starter | `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| Technology support | fat starters, Flyway/Liquibase pulled in transitively | one module and one starter per technology; `spring-boot-starter-flyway` must be declared |
| Test dependencies | `spring-boot-starter-test` for everything | `spring-boot-starter-<tech>-test` per technology |
| JSON | Jackson 2, `com.fasterxml.jackson` | Jackson 3, `tools.jackson` |
| Mocking in tests | `@MockBean` / `@SpyBean` | `@MockitoBean` / `@MockitoSpyBean` |
| HTTP integration test client | `TestRestTemplate` | `RestTestClient` |
| `@SpringBootTest` + MockMvc | auto-configured | needs `@AutoConfigureMockMvc` |
| Declarative HTTP clients | manual `HttpServiceProxyFactory` | `@ImportHttpServices` + `spring.http.serviceclient.*` |
| Retry | `spring-retry` + `@EnableRetry` | core `org.springframework.resilience.annotation` + `@EnableResilientMethods` |
| Nullability | `org.springframework.lang.Nullable` | JSpecify `@NullMarked` / `@Nullable` |
| Embedded servers | Tomcat, Jetty, Undertow | Tomcat, Jetty (Undertow removed) |
| Security | Security 6, chained DSL still compiles | Security 7, lambda DSL only |
| API versioning | hand-rolled | `spring.mvc.apiversion.*` + `@RequestMapping(version = …)` |

## Baseline before you start

- Upgrade to the newest 3.5.x first and build with `--warning-mode all` (Gradle) or review compiler
  warnings (Maven). Everything deprecated in 3.x is deleted in 4.0, so each remaining warning is a
  future compile error.
- Java 17 minimum; use the newest LTS. Kotlin 2.2+. GraalVM 25+ for native images.
- A Boot 4-compatible Spring Cloud release train, if you use one.
- Do the upgrade on its own branch with no behaviour changes in the diff. Mixing a feature into
  this diff makes every post-upgrade failure ambiguous.

## Step 1: starters and modules

Boot 4 ships small focused modules following a strict convention: module `spring-boot-<technology>`,
root package `org.springframework.boot.<technology>`, starter `spring-boot-starter-<technology>`.

Renames that break the build:

| 3.5 | 4.x |
|---|---|
| `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| `spring-boot-starter-web-services` | `spring-boot-starter-webservices` |
| `spring-boot-starter-aop` | `spring-boot-starter-aspectj` (only if you use `org.aspectj.lang.annotation`) |
| `spring-boot-starter-oauth2-client` | `spring-boot-starter-security-oauth2-client` |
| `spring-boot-starter-oauth2-resource-server` | `spring-boot-starter-security-oauth2-resource-server` |
| `spring-boot-starter-oauth2-authorization-server` | `spring-boot-starter-security-oauth2-authorization-server` |

Additions that are easy to miss: a technology that previously arrived transitively now needs its
own starter. Flyway and Liquibase are the usual casualties — the build still compiles and the
application still starts, but migrations never run.

`spring-boot-starter-classic` and `spring-boot-starter-test-classic` bundle the old surface as a
temporary bridge. They are deprecated on arrival; use them to get green, then replace them one
technology at a time, because leaving them in re-introduces the dependency bloat the modular
layout exists to remove.

## Step 2: test dependencies

Every technology starter has a `-test` companion, and each of those brings
`spring-boot-starter-test` transitively — so list the technologies under test rather than the
generic starter. This is not cosmetic: `@WithMockUser` and `@WithUserDetails` need
`spring-boot-starter-security-test`, and without it the annotations are on the classpath but the
supporting infrastructure is not, which fails in confusing ways.

Do not add both a technology test starter and the classic test starter: two overlapping test graphs
give version conflicts that surface as `NoSuchMethodError` at runtime.

## Step 3: removed features

- **Undertow** — incompatible with the Servlet 6.1 baseline. Move to Tomcat or Jetty. Do not deploy
  a Boot 4 application to a container that is not Servlet 6.1 compliant.
- **Executable launch scripts** — `bootJar { launchScript() }` and the Maven plugin's
  `<executable>true</executable>` are gone. Run `java -jar`, or use Gradle's application plugin.
- **Classic uber-jar loader** — remove `loaderImplementation = CLASSIC`.
- **Reactive Pulsar** — Spring Pulsar dropped Reactor support.
- **Spring Session Hazelcast / MongoDB** — moved to the respective vendors; declare an explicit
  version if you still need them.
- **Elasticsearch low-level REST client and sniffer** — no longer managed separately.
- **Hibernate `hibernate-jpamodelgen`** — renamed to `hibernate-processor`; `hibernate-proxool` and
  `hibernate-vibur` are no longer published at all.

## Step 4: Jackson 3

Group ID and packages move from `com.fasterxml.jackson` to `tools.jackson`. The one exception is
`jackson-annotations`, which keeps the `com.fasterxml.jackson.core` group ID and the
`com.fasterxml.jackson.annotation` package — so `@JsonProperty` imports do not change while
`ObjectMapper` imports do.

Renamed Spring types:

| 3.5 | 4.x |
|---|---|
| `Jackson2ObjectMapperBuilderCustomizer` | `JsonMapperBuilderCustomizer` |
| `JsonObjectSerializer` | `ObjectValueSerializer` |
| `JsonValueDeserializer` | `ObjectValueDeserializer` |
| `@JsonComponent` | `@JacksonComponent` |
| `@JsonMixin` | `@JacksonMixin` |

Behaviour changes worth knowing:

- Boot 4 auto-configures format-specific mappers. Defining an `ObjectMapper` bean no longer
  replaces the auto-configured one — define a `JsonMapper` or an `XmlMapper` bean.
- Every Jackson module on the classpath is now registered automatically (3.x registered only
  well-known ones). Disable with `spring.jackson.find-and-add-modules=false`.
- `spring.jackson.parser.*` properties with a `JsonReadFeature` equivalent moved to
  `spring.jackson.json.read.*`; the rest need a `JsonMapperBuilderCustomizer`.

Staged migration: `spring.jackson.use-jackson2-defaults=true` keeps Jackson 2's defaults on the
Jackson 3 mapper. The `spring-boot-jackson2` module lets Jackson 2 run alongside; it ships
deprecated and will be removed, so treat it as a deadline, not a destination. Jersey 4 does not yet
support Jackson 3 and requires `spring-boot-jackson2`.

## Step 5: Spring Security 7

The security topic covers the full list of removals. The migration-shaped summary: the adapter class
and the chained `and()` DSL are gone, `antMatchers`/`mvcMatchers` become `requestMatchers`,
`DaoAuthenticationProvider` takes its `UserDetailsService` through the constructor,
`@EnableGlobalMethodSecurity` becomes `@EnableMethodSecurity`, and the OAuth2 starters moved into
the security namespace. Delete any `spring-authorization-server.version` override — the
authorization server is versioned with Spring Security now.

For a large security configuration, upgrade to Security 6.5 first and turn on its preparation flags
one at a time, then move to 7.0.

## Step 6: relocated types and retry

- `org.springframework.boot.BootstrapRegistry` → `org.springframework.boot.bootstrap.BootstrapRegistry`
- `org.springframework.boot.env.EnvironmentPostProcessor` → `org.springframework.boot.EnvironmentPostProcessor`
  (update `META-INF/spring.factories` accordingly)
- `spring-retry` is unnecessary: `@Retryable`, `@ConcurrencyLimit` and `@EnableResilientMethods`
  live in `org.springframework.resilience.annotation` in core Spring Framework. The attribute names
  differ from Spring Retry's — `includes`/`maxRetries`/`delay`/`jitter`, not
  `retryFor`/`maxAttempts`/`backoff`.

Trailing-slash URL matching stays removed, and static resource handling changed defaults; check any
custom `WebMvcConfigurer`.

## Step 7: configuration properties

Add `spring-boot-properties-migrator` with `runtime` scope, start every profile the application
supports, and fix each key it reports. Then remove it — it is a diagnostic that rewrites properties
at runtime, which is not something to ship.

Diff `/actuator/configprops` before and after the upgrade. That catches renamed keys the migrator
does not know about, and it catches keys that silently stopped binding because their module is no
longer on the classpath.

## Step 8: tests

- `@MockBean`/`@SpyBean` → `@MockitoBean`/`@MockitoSpyBean`. The new annotations cannot be declared
  on `@Configuration` class fields; a shared mock set becomes class-level
  `@MockitoBean(types = {...})`, optionally behind a composed annotation.
- `@SpringBootTest` no longer auto-configures `MockMvc`; add `@AutoConfigureMockMvc`.
- Replace `TestRestTemplate` with `RestTestClient` and `@AutoConfigureRestTestClient`.
- `@PropertyMapping` moved package.
- Add the technology-specific test starters (step 2) before assuming a slice annotation is broken.

## Verification

Run in this order, fixing before moving on:

1. Compile. Everything above surfaces here except property and JSON changes.
2. Unit and slice tests.
3. Start each profile with `spring-boot-properties-migrator` present; fix reported keys.
4. Integration tests against real infrastructure (Testcontainers).
5. Diff `/actuator/configprops`, the JSON of a representative response, security failure bodies and
   the actuator exposure list against a 3.5 baseline capture.
6. Inspect the dependency tree for surviving old starters, two Jackson generations, and unmanaged
   versions.
7. If you ship a native image, build and run it — a green JVM suite says nothing about AOT.

## 4.0 versus 4.1

- Spock integration was removed in 4.0 and restored in 4.1. A Groovy/Spock suite should target 4.1.
- 4.1 adds `spring.http.clients.cookie-handling`, `InetAddressFilter` SSRF mitigation for HTTP
  clients, Spring gRPC support, and lazy JDBC connection fetching.
- 4.1 deprecates Derby support and layertools, and raises the jOOQ baseline to 3.20, which requires
  Java 21.

<!-- sources: spring-boot-wiki, awesome-copilot, adityamparikh-boot4, rrezart-spring-boot, pavithraa-springboot -->
