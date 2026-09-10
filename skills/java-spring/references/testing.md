# Testing a Spring Boot application

Verified against: Spring Boot 4.1 (JUnit 5/6, Mockito 5, AssertJ, Testcontainers).

## Contents

- [Pick the narrowest slice](#pick-the-narrowest-slice)
- [Plain unit tests](#plain-unit-tests)
- [Bean overrides](#bean-overrides)
- [@WebMvcTest](#webmvctest)
- [@DataJpaTest](#datajpatest)
- [Testcontainers](#testcontainers)
- [Full integration tests](#full-integration-tests)
- [Context caching is the real cost](#context-caching-is-the-real-cost)
- [Other slices](#other-slices)
- [Assertions](#assertions)

## Pick the narrowest slice

| What is under test | Use |
|---|---|
| Business logic in a service | Plain JUnit + Mockito, no Spring context |
| Controller mapping, validation, status codes, JSON | `@WebMvcTest` |
| Repository queries and mappings | `@DataJpaTest` + Testcontainers |
| An outbound `RestClient`/`RestTemplate` | `@RestClientTest` + `MockRestServiceServer` |
| Serialisation of one type | `@JsonTest` |
| Wiring, security chain, end-to-end HTTP | `@SpringBootTest` |

Everything above `@SpringBootTest` in that table starts a smaller context and reuses it more often.
Reaching for `@SpringBootTest` by default is the single biggest cause of slow suites.

## Plain unit tests

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository orders;
    @InjectMocks OrderService service;
}
```

Prefer a hand-written fake at the repository or gateway boundary when the collaborator has an
interface; reach for Mockito when it does not. Mockito's strict stubs throw
`UnnecessaryStubbingException` on a stub no test path reaches — that is a signal the test drifted
from the code, not noise to silence with `lenient()`.

## Bean overrides

Spring Boot 4 removed `@MockBean` and `@SpyBean`. Use `@MockitoBean` and `@MockitoSpyBean` from
`org.springframework.test.context.bean.override.mockito`.

They are not a drop-in replacement in one respect: the new annotations may be used on test-class
fields but not on `@Configuration` class fields. A shared set of mocks becomes a class-level
declaration, which can be folded into a composed annotation:

```java
@SpringBootTest
@MockitoBean(types = { OrderService.class, UserService.class })
@MockitoBean(name = "ps1", types = PrintingService.class)
class ApplicationTests { }
```

`@MockitoBean` also participates in the context cache key, so every distinct combination of mocked
types creates another application context.

## @WebMvcTest

Loads controllers, converters, `@ControllerAdvice` and the security filter chain — nothing below.
Collaborators are supplied with `@MockitoBean`.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvcTester mvc;
    @MockitoBean OrderService orderService;

    @Test
    @WithMockUser(roles = "USER")
    void rejectsEmptyBody() {
        assertThat(mvc.post().uri("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON).content("{}"))
            .hasStatus(HttpStatus.BAD_REQUEST)
            .bodyJson().extractingPath("$.type").isEqualTo("about:blank");
    }
}
```

`MockMvcTester` gives AssertJ-style assertions over the same `MockMvc` infrastructure; classic
`mockMvc.perform(...).andExpect(...)` remains valid where a project already uses it. Pick one per
codebase.

The security filter chain is active in this slice: without `@WithMockUser` (or an explicit
`.with(jwt())`) every request is a 401 and the assertion failure points at the wrong thing.
`@WithMockUser` and `@WithUserDetails` need `spring-boot-starter-security-test` on the classpath in
Boot 4 — the plain test starter no longer brings `spring-security-test`.

## @DataJpaTest

Loads the entity manager, repositories and a transaction manager. Each test method runs in a
transaction that is rolled back afterwards.

Two rules turn this slice from decorative into useful:

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
@Import(TestcontainersConfig.class)
class OrderRepositoryTest {
    @Autowired TestEntityManager em;
    @Autowired OrderRepository orders;

    @Test
    void findByStatusReturnsOnlyMatching() {
        em.persist(Order.create(OrderStatus.PENDING));
        em.persist(Order.create(OrderStatus.SHIPPED));
        em.flush();     // SQL actually reaches the database
        em.clear();     // first-level cache evicted, so the query really runs

        assertThat(orders.findByStatus(OrderStatus.PENDING)).hasSize(1);
    }
}
```

1. **Set up through `TestEntityManager`, not through the repository under test.** Using the
   repository for both setup and assertion means a bug in it can mask itself.
2. **`flush()` then `clear()` before asserting.** Without `flush()` the insert may still be
   pending; without `clear()` the repository call is served from Hibernate's first-level cache and
   the query is never executed. The test passes while asserting nothing.

The surrounding transaction also hides two production failures: lazy associations always resolve,
and constraint violations surface only at the rollback that never happens. Force a `flush()` where
a constraint is the thing under test, and use `@Transactional(propagation = NOT_SUPPORTED)` on a
test that must observe committed state.

Bulk `@Modifying` queries need `clearAutomatically = true` or the test reads pre-update entities
back out of the context.

## Testcontainers

The embedded database is a different engine with different SQL, different types and different
constraint behaviour; a green `@DataJpaTest` on H2 proves nothing about PostgreSQL. Run the real
engine and let `@ServiceConnection` wire the properties:

```java
@TestConfiguration(proxyBeanMethods = false)
class TestcontainersConfig {
    @Bean @ServiceConnection
    PostgreSQLContainer<?> postgres() {
        return new PostgreSQLContainer<>("postgres:17-alpine");
    }
}
```

`@ServiceConnection` replaces manual `@DynamicPropertySource` plumbing and works for most supported
technologies. Declare the container `static`, or reuse it through a shared configuration class, so
one container serves the whole suite instead of one per class. Where Docker genuinely is not
available in CI, an embedded database is the documented fallback — record that decision rather than
letting it be the default.

## Full integration tests

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
@Import(TestcontainersConfig.class)
class OrderIntegrationTest {
    @Autowired RestTestClient client;
}
```

- In Boot 4 `@SpringBootTest` no longer auto-configures `MockMvc`: add `@AutoConfigureMockMvc`
  (or `@AutoConfigureRestTestClient`) explicitly.
- `RestTestClient` supersedes `TestRestTemplate`; it works both against `MockMvc` and against a
  running port, so the same assertions survive the move between them.
- Autowiring both `MockMvc` and a port-bound client in one test class means half the tests never
  touch the server they claim to test.

Keep these to the handful of paths that genuinely need every layer: authentication, a transaction
that spans services, a migration plus a query.

## Context caching is the real cost

Spring caches an application context per unique configuration key: the classes, active profiles,
property overrides, `@MockitoBean` declarations, context customisers. Tests that share a key share
one context and one startup; anything that varies the key pays full startup again.

- Put shared setup in one abstract base class or one `@TestConfiguration`, and let test classes
  inherit it instead of each declaring its own `@TestPropertySource`.
- `@DirtiesContext` evicts the cached context and forces a rebuild for the next test that needs it.
  Use it only when a test genuinely corrupts global state.
- A suite that takes minutes usually has a handful of near-identical contexts, not slow tests.

## Other slices

- `@RestClientTest(MyClient.class)` plus `MockRestServiceServer` asserts the request that was
  actually issued, which a mocked client cannot.
- `@JsonTest` covers serialisation edge cases (null handling, date formats, polymorphism) far more
  cheaply than a controller test.
- `@WebFluxTest` with `WebTestClient` for reactive controllers; `StepVerifier` for publishers,
  including cancellation and error paths.

## Assertions

Use AssertJ (`assertThat(...).isEqualTo(...)`, `assertThatThrownBy(...)`) throughout rather than
mixing in JUnit's `assertEquals`. For interaction checks prefer BDDMockito
(`given(...).willReturn(...)`, `then(mock).should()`) and `ArgumentCaptor` when the argument itself
is the assertion.

<!-- sources: awesome-copilot, spring-testing-skills, rrezart-spring-boot, spring-docs, spring-boot-wiki -->
