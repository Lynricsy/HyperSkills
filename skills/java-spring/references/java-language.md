# Java 17 → 21 → 25 in a Spring application

Verified against: JDK 25 (LTS). Spring Boot 4 requires Java 17; Java 21 or 25 is the practical
baseline.

## Contents

- [Upgrade order](#upgrade-order)
- [Java 21 features that change how you write Spring code](#java-21-features-that-change-how-you-write-spring-code)
- [Virtual threads](#virtual-threads)
- [Java 22–25 additions](#java-2225-additions)
- [Deprecations and runtime warnings](#deprecations-and-runtime-warnings)
- [Garbage collection](#garbage-collection)
- [Preview features](#preview-features)

## Upgrade order

Move the runtime first, the bytecode target second, the language level third:

1. Build and test on the new JDK while `release` stays at the old level. This surfaces
   agent/reflection/`Unsafe` warnings and third-party incompatibilities without touching code.
2. Raise `maven.compiler.release` / `java.toolchain.languageVersion` and fix compile errors.
3. Adopt language features in reviewable batches, not in the upgrade commit.

Bytecode-manipulating libraries are the usual blocker: Lombok, Mockito, ByteBuddy, ASM, JaCoCo and
any Gradle plugin embedding them must be new enough for the target class-file version. A
`ClassFormatError` or `UnsupportedClassVersionError` naming an internal ASM class is always this,
never your code.

## Java 21 features that change how you write Spring code

**Records** (17) are the default shape for DTOs, `@ConfigurationProperties` groups, events and
value objects: immutable, `equals`/`hashCode` for free, and a compact constructor for validation.
They are the wrong shape for JPA entities — Hibernate needs a mutable, non-final class with a
no-arg constructor.

**Sealed interfaces** (17) plus **pattern matching for `switch`** (JEP 441, standard in 21) turn a
result type into something the compiler checks:

```java
public sealed interface PaymentResult permits Captured, Declined, Pending {}

String describe(PaymentResult result) {
    return switch (result) {
        case Captured c   -> "captured " + c.amount();
        case Declined d   -> "declined: " + d.reason();
        case Pending p    -> "pending until " + p.retryAt();
    };                                  // no default: adding a case breaks the build
}
```

Omit `default` for a sealed hierarchy — that is the whole benefit. With a `default` branch, adding
a new subtype compiles and silently takes the wrong path.

**Record patterns** (JEP 440, 21) destructure in the same `switch`:
`case Declined(var reason, var code) -> …`.

**Sequenced collections** (JEP 431, 21) give `getFirst()`, `getLast()`, `reversed()` on `List`,
`Deque` and `LinkedHashMap`, replacing `list.get(list.size() - 1)`.

## Virtual threads

`spring.threads.virtual.enabled=true` (Java 21+) runs the servlet container's request handling, the
`@Async` executor and scheduled tasks on virtual threads. For a blocking, I/O-bound Spring MVC
service that is usually the single highest-leverage change available, and it removes most of the
reason to adopt WebFlux.

What to check before enabling it:

- **Pinning.** Before JDK 24, a virtual thread blocking inside a `synchronized` block pinned its
  carrier thread, so a `synchronized`-heavy library could throttle the whole pool. JEP 491
  (standard in JDK 24) removed that; on Java 21–23 audit hot paths for `synchronized` around I/O
  and replace with `ReentrantLock`. On 25 this is no longer a concern.
- **Connection pools.** Virtual threads make it trivially cheap to have 10 000 concurrent requests
  all waiting for a 20-connection HikariCP pool. Throughput is now bounded by the pool and the
  database, and the queue is invisible. Size the pool and add a connection-acquisition timeout.
- **`ThreadLocal` caches.** A pooled-thread cache keyed by `ThreadLocal` is per-request now, not
  per-worker; anything expensive stored there is allocated per request.
- **Thread-pool tuning.** `server.tomcat.threads.max` and friends stop meaning what they used to.
  Remove the tuning rather than carrying it forward.

`@Transactional` is unaffected: the transaction is bound to the thread either way, and virtual
threads are still threads.

## Java 22–25 additions

| Feature | Standard in | Why it matters here |
|---|---|---|
| Unnamed variables and patterns (`_`) — JEP 456 | 22 | Removes unused `catch`/lambda parameters that lint rules flag |
| Statements before `super(...)` — JEP 447/482/492 (Flexible Constructor Bodies) | 25 | Validate arguments before delegating, instead of in a static helper |
| Stream gatherers — JEP 485 | 24 | Custom intermediate operations (windowing, batching) without collecting to a list |
| Class-File API — JEP 484 | 24 | Replaces ad-hoc ASM use; relevant if you generate or inspect bytecode |
| Markdown doc comments — JEP 467 | 23 | `///` comments instead of HTML in Javadoc |
| Module import declarations — JEP 511 | 25 | `import module java.base;` — convenience, not architecture |
| Compact source files and instance `main` — JEP 512 | 25 | Scripts and spikes; not application code |
| Scoped values — JEP 506 | 25 | Immutable per-request context that works with virtual threads and structured concurrency, unlike `ThreadLocal` |
| Key Derivation Function API — JEP 510 | 25 | Standard KDF instead of a hand-rolled one |
| PEM encodings — JEP 470 | 25 (preview) | Reading keys and certificates without BouncyCastle |
| AOT command-line ergonomics and method profiling — JEP 514/515 | 25 | Faster JVM warmup; complements Spring's AOT processing |

Structured concurrency (JEP 505) is still a preview API in 25 — do not build on it in production.

## Deprecations and runtime warnings

These print warnings on a new JDK before they become errors, and they are usually the first thing
an upgrade surfaces:

- **`sun.misc.Unsafe` memory access** (deprecated 23) — comes from old ByteBuddy, Netty or cache
  libraries. Upgrade the library; you rarely call it yourself.
- **Dynamic agent loading** (JEP 451, warns since 21) — a profiler or mock library attaching at
  runtime. Add `-XX:+EnableDynamicAgentLoading` to silence it deliberately, or pass `-javaagent`
  at startup.
- **JNI usage warnings** (JEP 472, since 24).
- **Finalization** (JEP 421, deprecated since 18) — remove any `finalize()` override.
- **The Security Manager** was permanently disabled in 24 (JEP 486). Code that calls
  `System.setSecurityManager` now fails.
- **32-bit x86 ports** removed (24/25).

## Garbage collection

Generational ZGC became the default ZGC mode in 23 (JEP 474) and the non-generational mode was
removed in 24, so `-XX:-ZGenerational` now fails to start. G1 remains the JVM default and is the
right choice for most Spring services; move to ZGC when a pause-time target, not throughput, is the
constraint. Measure before switching — a GC change is not an upgrade step.

## Preview features

A preview feature needs `--enable-preview` at compile *and* run time, and class files compiled with
it refuse to load on any other JDK version. That makes them unsuitable for a library and risky for
an application whose runtime version is managed elsewhere. Keep production on standard features
only.

<!-- sources: awesome-copilot, pavithraa-springboot, openjdk-jeps, spring-docs -->
