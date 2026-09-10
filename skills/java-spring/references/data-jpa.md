# Spring Data JPA and transactions

Verified against: Spring Boot 4.1 (Spring Data JPA 4.x, Hibernate 7, Jakarta Persistence 3.2).

## Contents

- [Entity mapping](#entity-mapping)
- [Identity, versions and new-state detection](#identity-versions-and-new-state-detection)
- [equals, hashCode, toString](#equals-hashcode-tostring)
- [Relationships](#relationships)
- [Repositories: which query shape](#repositories-which-query-shape)
- [N+1 and how to see it](#n1-and-how-to-see-it)
- [Pagination](#pagination)
- [Transaction boundaries](#transaction-boundaries)
- [Propagation and self-invocation](#propagation-and-self-invocation)
- [Rollback rules](#rollback-rules)
- [Side effects after commit](#side-effects-after-commit)
- [Optimistic locking and retry](#optimistic-locking-and-retry)
- [Batch writes](#batch-writes)
- [Schema migrations](#schema-migrations)
- [open-in-view](#open-in-view)

## Entity mapping

An `@Entity` is persistent state with identity and a lifecycle. Everything else — request bodies,
responses, commands, read models — is a `record`. Records make poor entities: Hibernate needs a
non-final class and a no-arg constructor to instantiate and proxy.

```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_orders_status_created", columnList = "status, created_at")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Order {

    @Id @GeneratedValue(strategy = GenerationType.UUID)
    @Column(nullable = false, updatable = false)
    private UUID id;

    @Version
    private Long version;                       // wrapper, not primitive

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private OrderStatus status;                 // never ORDINAL

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();   // initialised inline

    public static Order create(UUID customerId) { … }    // static factory
    public void addItem(…) { … }                         // behaviour, not setters
}
```

- `@Enumerated(EnumType.ORDINAL)` stores the declaration index. Inserting or reordering a constant
  silently remaps every existing row; `STRING` cannot.
- Lombok `@Data` on an entity generates public setters plus `equals`/`hashCode`/`toString` over every
  field including associations. Use `@Getter` and a protected `@NoArgsConstructor` instead.
- `@Embeddable` records are fine, and are the right shape for value objects (`Money`, `Address`).
- Never return an entity from a controller. Serialising it walks lazy associations outside the
  transaction and couples the wire format to the table.

## Identity, versions and new-state detection

Spring Data decides "is this new?" by looking at a nullable `@Version` field first, then at a
nullable id. Two consequences:

- A primitive `long version` breaks the check: JPA treats `0` as an already-persisted version, so
  `save()` issues a `merge` and Hibernate emits a pointless `SELECT` before every insert.
- With a manually assigned id, neither signal exists. Add `@Version Long version`, or implement
  `Persistable` with an `isNew` flag cleared from `@PostPersist` and `@PostLoad`.

Prefer `GenerationType.UUID` or a pooled sequence. `GenerationType.IDENTITY` forces Hibernate to
read the generated key back after each row, which disables JDBC insert batching entirely.

## equals, hashCode, toString

- If the entity has a stable natural key (an email, an external reference), base equality on it and
  back it with a unique constraint.
- Otherwise keep the inherited object identity. A generated id is null before the flush, so
  id-based equality changes the hash code mid-persistence-context.
- Never include collections, mutable fields or associations. Use `instanceof`, not `getClass()`,
  so equality survives a Hibernate proxy.

## Relationships

- `@ManyToOne` and `@OneToOne` default to `FetchType.EAGER`. Set `fetch = FetchType.LAZY` on both.
- Add `@OneToMany(mappedBy = …)` only when parent-to-child navigation is genuinely used; a
  bidirectional pair you never traverse is two more places to keep consistent.
- `orphanRemoval = true` only when the parent owns the child's lifecycle.
- A `@ManyToMany` with attributes on the link is a modelling error: make the join row an entity.

## Repositories: which query shape

Create a repository per aggregate root, not per table. An entity reachable only through its
aggregate does not need its own repository — the aggregate's is the boundary.

| Need | Use |
|---|---|
| One or two simple filters | Derived query (`findByStatusAndCustomerId`) |
| Existence check | `existsBy…`, never `findBy…().isPresent()` |
| Joins, ordering, keyset predicates | `@Query` with JPQL |
| Bounded eager loading of one aggregate | `@EntityGraph(attributePaths = …)` |
| Read-only list or API view | Interface or record projection |
| Criteria API, bulk DML, `EntityManager` work | Custom repository fragment |
| Separate read model, reporting | Dedicated query service, no repository |

Derived-query names stop paying for themselves around the third condition; switch to `@Query`
before the method name needs to be read twice.

`save()` is `persist` on a new instance and `merge` on a detached one. `merge` returns a *copy* —
the argument stays detached, so `repo.save(order)` and then mutating `order` writes nothing. Inside
a transaction a managed entity is flushed by dirty checking and does not need `save()` at all.

## N+1 and how to see it

The symptom is one query for the list and one more per element. It appears wherever a lazy
association is touched inside a loop or during JSON serialisation.

Turn it into something you can see rather than guess at, in a test or dev profile:

```properties
logging.level.org.hibernate.SQL=DEBUG
spring.jpa.properties.hibernate.generate_statistics=true
```

Fixes, in order of preference:

1. A projection that selects only the columns the response needs. No graph is loaded at all.
2. `@EntityGraph(attributePaths = {"items"})` on the finder, for a bounded aggregate.
3. A JPQL `join fetch`.

Never `join fetch` two collections in one query: the cartesian product multiplies rows, and with
pagination Hibernate falls back to loading everything into memory to paginate there. Fetch one
collection per query, or use `@BatchSize`.

## Pagination

`Pageable` is right for a page-numbered UI. Its `OFFSET` scans and discards the skipped rows, so
deep pages and infinite scroll need keyset pagination instead:

```java
@Query("""
    select o from Order o
    where o.status = :status
      and (o.createdAt < :lastCreatedAt
           or (o.createdAt = :lastCreatedAt and o.id < :lastId))
    order by o.createdAt desc, o.id desc
    """)
List<Order> findNextPage(OrderStatus status, Instant lastCreatedAt, UUID lastId, Limit limit);
```

The `(createdAt, id)` tuple keeps the cursor stable when timestamps collide. Back it with an index
in the same order. `Page` also issues a second `count` query; return `Slice` when the caller only
needs "is there more".

## Transaction boundaries

- `@Transactional` belongs on service methods. On a controller it holds the transaction open across
  view rendering; on a repository it is one transaction per call, which cannot compose.
- Annotate the class `@Transactional(readOnly = true)` and override the writers with plain
  `@Transactional`. `readOnly` lets Hibernate skip dirty-check snapshots and lets the driver route
  to a replica.
- Keep remote calls out of the transaction. An HTTP call inside one holds a database connection for
  the length of someone else's timeout.

## Propagation and self-invocation

`@Transactional` is proxy-based. Three call shapes silently do nothing:

- `this.other(…)` — an internal call never leaves the object, so the proxy is not involved.
- A `private` (or `final`) method — the proxy cannot intercept it.
- A method invoked through a raw `new` instead of the injected bean.

The fix is a real call through a proxy: move the inner method to its own bean and inject it. Only
reach for `@EnableAspectJAutoProxy(exposeProxy = true)` and `AopContext.currentProxy()` when
extracting the bean is genuinely impossible.

`Propagation.REQUIRES_NEW` suspends the caller's transaction and needs a second connection from the
pool; a loop of `REQUIRES_NEW` calls with a pool of ten can deadlock against itself.

## Rollback rules

Rollback happens on `RuntimeException` and `Error`, not on checked exceptions. Declare
`@Transactional(rollbackFor = MyCheckedException.class)` when a checked exception must roll back.

Once any participant marks the transaction rollback-only, catching the exception in the caller does
not save it: the commit fails with `UnexpectedRollbackException`. If an inner step is allowed to
fail, it must run in its own `REQUIRES_NEW` transaction.

## Side effects after commit

Sending mail, publishing to a broker, invalidating a cache or calling a webhook inside the
transaction cannot be undone by a rollback. Publish an application event instead and act on commit:

```java
@Transactional
public Order place(UUID id) {
    Order order = orders.findById(id).orElseThrow();
    order.place();
    events.publishEvent(new OrderPlaced(order.getId()));   // not sent yet
    return order;
}

@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void onPlaced(OrderPlaced event) {
    mailer.sendConfirmation(event.orderId());
}
```

The listener runs after the commit, therefore outside the original transaction: a listener that
writes to the database needs its own `@Transactional(propagation = REQUIRES_NEW)`. Delivery is
in-process only — a crash between commit and listener loses the event. When that matters, use
Spring Modulith's persistent publication registry, or an outbox table.

## Optimistic locking and retry

`@Version` turns a lost update into an `ObjectOptimisticLockingFailureException` at flush time.
Retry it from a *calling* bean so each attempt gets a fresh transaction:

```java
@Configuration
@EnableResilientMethods                 // org.springframework.resilience.annotation
class ResilienceConfig {}

@Service
class OrderStatusFacade {
    private final OrderService orderService;          // separate bean

    @Retryable(includes = ObjectOptimisticLockingFailureException.class,
               maxRetries = 3, delay = 50, jitter = 25)
    Order updateStatus(UUID id, OrderStatus next) {
        return orderService.updateStatus(id, next);   // fresh @Transactional per attempt
    }
}
```

`@Retryable` and `@Transactional` on the same method retries inside a transaction that is already
marked rollback-only, so every attempt after the first fails at commit.

## Batch writes

```yaml
spring:
  jpa:
    properties:
      hibernate:
        jdbc.batch_size: 50
        order_inserts: true
        order_updates: true
```

Batching is silently off under `GenerationType.IDENTITY`. Bulk `@Modifying` JPQL bypasses the
persistence context, so add `@Modifying(clearAutomatically = true, flushAutomatically = true)` or
the context keeps serving stale entities for the rest of the transaction.

## Schema migrations

Use Flyway (or Liquibase) and never `spring.jpa.hibernate.ddl-auto` above `validate` outside a
throwaway database — `update` cannot drop, rename or backfill, so schemas drift silently.

In Spring Boot 4 the modular starters do not pull Flyway in transitively. `spring-boot-starter-flyway`
plus the database module (`flyway-database-postgresql`) must be declared, otherwise migrations
simply never run and the application starts against whatever schema exists.

Naming: `V<version>__<description>.sql` for versioned, `R__<description>.sql` for repeatable.
Never edit a migration that has run anywhere. Expand-then-contract for anything destructive: add
the nullable column, backfill, switch the code, drop the old column in a later release.

## open-in-view

`spring.jpa.open-in-view` defaults to `true` and keeps the persistence context open for the whole
request, which is why a lazy association that fails in a test succeeds through the controller. Set
it to `false` and fix the `LazyInitializationException`s it exposes: each one is a query issued
during view rendering, outside any transaction, on a connection held for the whole request.

<!-- sources: rrezart-spring-boot, pavithraa-springboot, spring-testing-skills, spring-docs -->
