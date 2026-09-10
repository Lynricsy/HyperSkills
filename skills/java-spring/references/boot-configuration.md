# Auto-configuration, beans and configuration properties

Verified against: Spring Boot 4.1.

## Contents

- [How auto-configuration decides](#how-auto-configuration-decides)
- [Beans and injection](#beans-and-injection)
- [Typed configuration properties](#typed-configuration-properties)
- [Property sources and profiles](#property-sources-and-profiles)
- [Secrets](#secrets)
- [Null safety with JSpecify](#null-safety-with-jspecify)
- [Diagnosing startup](#diagnosing-startup)

## How auto-configuration decides

Auto-configuration is a set of `@Conditional` classes evaluated after your own beans are defined.
The two rules that explain most surprises:

- `@ConditionalOnMissingBean` means *your* bean wins. Declaring a `DataSource`, an `ObjectMapper`
  or a `SecurityFilterChain` silently switches off Boot's version, including everything Boot would
  have configured on it.
- Conditions are evaluated on the classpath as it actually is. In Boot 4's modular layout, a
  technology contributes auto-configuration only when its module is present, which is why adding a
  library without its starter produces "no bean of type X" rather than a helpful error.

`--debug` (or `debug=true`) prints the condition evaluation report: which auto-configurations
matched, which did not, and why. Read it before adding a bean to "force" something.

Order matters only through `@AutoConfiguration(before = …, after = …)` in an auto-configuration
class; `@Order` on a plain `@Bean` method does nothing for wiring.

## Beans and injection

- Constructor injection, fields `private final`. Field injection cannot be constructed in a test
  and hides how many collaborators a class has grown.
- A single constructor needs no `@Autowired`.
- A circular dependency is a design signal, not a configuration problem;
  `spring.main.allow-circular-references=true` postpones the fix and makes startup order
  load-bearing.
- `@Component` scanning starts at the `@SpringBootApplication` class's package. A bean in a sibling
  package is not found — move the class or add an explicit `@ComponentScan`.
- Prefer `@Bean` methods in a `@Configuration` class for third-party types you do not own;
  `@Component` only for your own classes.
- `@Configuration(proxyBeanMethods = false)` skips CGLIB subclassing when `@Bean` methods do not
  call each other. It is the right default for `@TestConfiguration` and for AOT/native builds.

## Typed configuration properties

```java
@ConfigurationProperties("app.payments")
@Validated
public record PaymentProperties(
        @NotBlank String baseUrl,
        @NotNull Duration readTimeout,
        @DefaultValue("3") int maxRetries,
        @Valid Retry retry) {

    public record Retry(@NotNull Duration initialDelay, @Positive int attempts) {}
}
```

- A record is not a bean by itself: register it with `@EnableConfigurationProperties(PaymentProperties.class)`
  or `@ConfigurationPropertiesScan`. This is the single most common reason a "properties class"
  binds nothing.
- `@Validated` needs a validation provider on the classpath (`spring-boot-starter-validation`).
  Without it the annotations are inert and invalid configuration reaches production.
- Nested objects need `@Valid` to be validated at all.
- Durations and sizes take units (`5s`, `10MB`). A bare number is interpreted in the annotated unit
  or in milliseconds — an easy factor-of-1000 outage. `@NotNull` on a `Duration` does not reject
  zero or a negative value; add an explicit constraint.
- Give a default only when the default is operationally safe. A missing credential or endpoint
  should fail startup, not fall back.
- Never make a full secret a record component: the generated `toString` will eventually reach a log.

Prefer one `@ConfigurationProperties` group over scattered `@Value` — `@Value` has no validation,
no metadata, no IDE completion, and no single place to see what a feature needs.

## Property sources and profiles

Later sources override earlier ones: defaults in the jar, then `application.yml` outside it, then
profile-specific documents, then environment variables, then command-line arguments. Relaxed
binding maps `APP_PAYMENTS_BASE_URL` onto `app.payments.base-url`.

- YAML lists are replaced wholesale, not merged, when a higher-precedence source defines them.
- Do not activate a profile from inside a document that profile activates; use
  `spring.config.activate.on-profile` for conditional documents and `spring.profiles.active`
  (or the environment) to choose.
- Binding happens at startup. Editing a file or rotating a mounted secret changes nothing until the
  process restarts — decide and document the reload/restart behaviour.
- Test the override path you actually deploy. `ApplicationContextRunner` asserts both a successful
  binding and a startup failure on invalid input without booting the application:

```java
new ApplicationContextRunner()
    .withUserConfiguration(PaymentConfig.class)
    .withPropertyValues("app.payments.base-url=", "app.payments.read-timeout=5s")
    .run(context -> assertThat(context).hasFailed());
```

## Secrets

Inject secrets from the environment or a mounted secret tree; never commit them and never bake them
into an image layer. Keep `configprops` and `env` actuator endpoints off the public surface and
leave sanitisation on — turning it off "to debug" writes the secret to whoever is watching.

## Null safety with JSpecify

Spring Framework 7 annotates its own API with JSpecify, and Boot 4 follows. For application code:

```java
@NullMarked
package com.example.orders;

import org.jspecify.annotations.NullMarked;
```

Inside a `@NullMarked` package everything is non-null by default; annotate only the exceptions with
`@Nullable`. Position matters: `@Nullable List<String>` is a nullable list of non-null elements,
`List<@Nullable String>` is a non-null list that may contain nulls.

The annotations are metadata. Kotlin reads them as real nullability; Java needs NullAway (with
`JSpecifyMode=true`) or IDE inspections to enforce anything. Migrate a module at a time and drop
`org.springframework.lang.Nullable` as you go — mixing both systems in one module means neither
tool sees the whole picture.

## Diagnosing startup

- A failure analyzer already prints the actionable message for the common cases (port in use,
  missing datasource URL, circular reference). Read it before reading the stack trace.
- `/actuator/configprops` shows what actually bound, `/actuator/env` shows which source won.
  Comparing these two across an upgrade finds renamed properties faster than reading a changelog.
- `spring-boot-properties-migrator` (runtime scope, temporarily) reports and remaps renamed
  properties at startup. Remove it before release; it is a diagnostic, not a compatibility layer.

<!-- sources: rrezart-spring-boot, awesome-copilot, spring-docs -->
