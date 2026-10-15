# payments-service upgrade plan

Today: Spring Boot 3.5.x on Java 21. Target: Spring Boot 4.1.x on Java 25 this sprint,
Java 26 next quarter. Container build is the Dockerfile in this directory.

1. Bump the parent to `spring-boot-starter-parent` 4.1.x and fix whatever the compiler and
   the test suite report.
2. Dockerfile: keep as is; the layered extraction has worked since Boot 2.3.
3. Drop `resilience4j-spring-boot3`. Boot 4 brings retries, concurrency limits and circuit
   breakers into core Spring Framework, so `@CircuitBreaker(name = "ledger")` on
   `LedgerClient` and `@Retry(name = "ledger")` both move to the core annotations.
4. JVM flags: keep `-XX:-ZGenerational`. We measured non-generational ZGC as better for our
   heap shape in 2024 and do not want to re-tune during an upgrade.
5. Java 25: `Money(BigDecimal amount)` now validates the amount before calling `super(...)`.
   Statements before `super(...)` are a preview feature, so add `--enable-preview` to the
   compiler plugin, Surefire and the container `JAVA_TOOL_OPTIONS`.
