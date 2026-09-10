# Build, startup and packaging

Verified against: Spring Boot 4.1, GraalVM 25+.

## Contents

- [Maven and Gradle](#maven-and-gradle)
- [Multi-module layout](#multi-module-layout)
- [Container images](#container-images)
- [Runtime behaviour in a container](#runtime-behaviour-in-a-container)
- [AOT and native image](#aot-and-native-image)
- [Startup cost](#startup-cost)

## Maven and Gradle

Let the Boot BOM manage versions. Pinning an explicit Hibernate, Jackson or Jakarta version defeats
the whole point of the platform and produces combinations nobody tested. Override deliberately, in
one place, with a comment saying why.

- Maven: inherit `spring-boot-starter-parent`, or import `spring-boot-dependencies` as a BOM when
  the project already has a corporate parent. Override a managed version through the documented
  property (`<hibernate.version>`), not by adding a `<dependency>` with a version.
- Gradle: apply `io.spring.dependency-management` (or the Boot plugin's platform) and declare
  versions in `gradle/libs.versions.toml`. A version literal in a module build file is a version
  that drifts.

`mvn dependency:tree` / `./gradlew dependencies` is the first command to run for any
`NoSuchMethodError`, duplicate-class or "two Jackson generations" symptom.

## Multi-module layout

Split by responsibility, not by technical layer:

```
app/            @SpringBootApplication, wiring, the only bootJar
domain/         plain Java, no Spring, no Jakarta Persistence
persistence/    entities, repositories, migrations
web/            controllers, DTOs, error handling
```

- Only the application module produces an executable jar. In Maven, disable `repackage` in the
  library modules; in Gradle, disable `bootJar` and enable `jar` for them. A library packaged as a
  Boot uber-jar cannot be consumed as a dependency.
- Keep the domain module free of framework imports. That is what makes it unit-testable without a
  context and reusable from another entry point.
- Module cycles are not possible in Maven and are a design error in Gradle; if two modules need
  each other, the shared part is a third module.

## Container images

Prefer the build plugin's `build-image` goal (Cloud Native Buildpacks) over a hand-written
Dockerfile: it produces layered images, a non-root user and an SBOM without you maintaining any of
it. Pin the builder and run-image family, and promote by digest.

A hand-written Dockerfile must be multi-stage and must extract the jar so dependencies and
application code land in different layers:

```dockerfile
FROM eclipse-temurin:25-jdk AS builder
WORKDIR /build
COPY target/app.jar app.jar
RUN java -Djarmode=tools -jar app.jar extract --layers --destination extracted

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=builder /build/extracted/dependencies/ ./
COPY --from=builder /build/extracted/spring-boot-loader/ ./
COPY --from=builder /build/extracted/snapshot-dependencies/ ./
COPY --from=builder /build/extracted/application/ ./
USER 1000
ENTRYPOINT ["java", "-jar", "app.jar"]
```

A plain `mvn package` does not create `target/dependencies/` or `target/application/`; those come
from the `jarmode=tools` extraction above. Copying paths that do not exist is the most common
broken Dockerfile in this area.

Run as non-root with a read-only filesystem where possible, inject secrets at runtime only, and
never copy a credential into a build context — it stays in the layer even if a later step deletes
it.

## Runtime behaviour in a container

- Verify JVM ergonomics under the actual CPU and memory limits. The JVM sizes the heap from the
  container limit, so a limit change silently changes GC behaviour.
- Configure graceful shutdown (`server.shutdown=graceful`,
  `spring.lifecycle.timeout-per-shutdown-phase`) to be shorter than the platform's termination
  grace period, or in-flight requests are killed anyway.
- Expose liveness and readiness separately (see the observability topic) and give expensive
  initialisation a startup probe.

## AOT and native image

AOT processing evaluates the bean topology at build time. Native image then compiles under the
closed-world assumption: the classpath, the profiles and the conditional beans are fixed at build
time and cannot change at runtime. A profile that flips a `@ConditionalOnProperty` bean will not
work — that decision has already been made.

Workflow when adding native support:

1. Add the native build support (Maven `native` profile / Gradle GraalVM plugin) and GraalVM 25+.
2. Build the executable and run it. Do not infer anything from a green JVM test suite.
3. Read the failure. `ClassNotFoundException`, a missing resource or a failed proxy at runtime
   names exactly what needs a hint.
4. Register the narrowest possible `RuntimeHints` for that reflection, resource, serialisation,
   JNI or proxy use, via a `RuntimeHintsRegistrar`. Blanket reflection registration inflates the
   binary and hides the next problem.
5. Where a library provides GraalVM reachability metadata, prefer it over your own hints.
6. Iterate until the executable starts and the smoke path passes; then run the integration suite
   against the executable, not the jar.

Choose native from measurements — startup, memory, throughput and build time — not from fashion.
Throughput is usually lower than a warmed JVM, build times are minutes, and debugging is harder.
For fast startup on the JVM, the AOT cache and CRaC checkpoint/restore are cheaper options.

Generate an SBOM, scan the image, and rebuild regularly on patched run images; sign and attest
releases where the platform supports it.

## Startup cost

- `spring.main.lazy-initialization=true` speeds up development startup but moves failures from
  boot to first request. Never enable it in production.
- Component scanning over a wide package tree is a real cost; a narrow `@SpringBootApplication`
  package is the fix, not `@ComponentScan` exclusions.
- Virtual threads (`spring.threads.virtual.enabled=true`, Java 21+) change concurrency, not startup.

<!-- sources: rrezart-spring-boot, awesome-copilot, spring-docs -->
