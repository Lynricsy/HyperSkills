# Testing

Verified against: .NET 10 SDK, Microsoft.Testing.Platform.

## Contents

- [Framework selection](#framework-selection)
- [Microsoft.Testing.Platform](#microsofttestingplatform)
- [Running tests](#running-tests)
- [Test levels](#test-levels)
- [Integration tests with WebApplicationFactory](#integration-tests-with-webapplicationfactory)
- [Testability: replace ambient state](#testability-replace-ambient-state)
- [Test doubles](#test-doubles)
- [Shape of a good test](#shape-of-a-good-test)
- [Test smells](#test-smells)

## Framework selection

Use the framework the repository already uses. Migrating a suite is a project, not a
side effect of adding a test.

For a new test project, default to **xUnit v3 on Microsoft.Testing.Platform**. The escape
hatches: MSTest when the repository is already Microsoft-tooling-heavy or targets WinUI, NUnit
when the team's existing tests are NUnit, TUnit when a project wants source-generated tests
and native AOT test hosts.

| | xUnit v3 | NUnit | MSTest | TUnit |
|---|---|---|---|---|
| Per-test isolation | New class instance per test | `[SetUp]` per test, shared fixture instance | New class instance per test | New instance per test |
| Setup/teardown | Constructor + `IDisposable`/`IAsyncLifetime` | `[SetUp]`/`[TearDown]` | `[TestInitialize]`/`[TestCleanup]` | `[Before]`/`[After]` |
| Parameterised | `[Theory]` + `[InlineData]`/`[MemberData]` | `[TestCase]`/`[TestCaseSource]` | `[DataRow]`/`[DynamicData]` | `[Arguments]`/`[MethodDataSource]` |
| MTP support | Native (v3) | NUnit runner | MSTest runner | Native |

## Microsoft.Testing.Platform

MTP is the replacement for VSTest. The platform is embedded in the test project itself, so the
test project is an executable; there is no `vstest.console` host.

What follows from that:

- The project is a real app: `dotnet run` in the test project runs the tests, and the same
  binary works in CI, in an IDE test explorer, and inside a container.
- Extensions (coverage, retry, crash dump, reporting) are NuGet packages, registered at
  compile time. With `Microsoft.Testing.Platform.MSBuild` present — the default for the
  MSTest, NUnit and xUnit runners — installing the package is all that is required. If you
  disable the generated entry point with `<GenerateTestingPlatformEntryPoint>false</...>`, you
  must register each extension by hand in `Main`.
- Supported targets are .NET 8+ and .NET Framework 4.6.2+.
- `dotnet test` works against MTP projects through the same MSBuild integration.

The practical reason to prefer it: determinism. No reflection-based discovery, no
`AppDomain`/`AssemblyLoadContext` isolation, so a test that passes locally and fails in CI is
a real difference rather than a host artefact.

## Running tests

```bash
dotnet test                                  # builds, then runs everything
dotnet test --no-build --no-restore          # reuse an existing build
dotnet test --filter "FullyQualifiedName~Orders"       # VSTest-style filter
dotnet test -- --filter-query "/*/*/OrderTests/*"      # MTP filter, after --
```

`dotnet test` builds by default; do not run a build "just in case" first. Identify which
platform the project is on before quoting a filter — the syntaxes are not interchangeable, and
a filter that silently matches nothing reports success with zero tests. Always check the test
count in the output.

## Test levels

- **Unit** for pure logic: a calculation, a state machine, a parser, a validation rule. Fast,
  no I/O, no host.
- **Integration** for the composed application: routing, model binding, filters, auth,
  serialisation, DI wiring, EF Core translation. Use `WebApplicationFactory`.
- **Database** against the real engine — an in-memory provider translates LINQ differently and
  enforces no constraints, so it proves nothing about the SQL that will run. Use Testcontainers
  or a local instance.
- **End-to-end** through a browser is out of scope for this skill.

Do not test the framework: a DI registration, a plain property, a controller that only
forwards to a service. Those tests fail only when you rename something.

## Integration tests with WebApplicationFactory

```csharp
public sealed class OrdersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public OrdersApiTests(WebApplicationFactory<Program> factory) =>
        _client = factory.WithWebHostBuilder(b => b.ConfigureTestServices(services =>
        {
            services.RemoveAll<IPricingClient>();
            services.AddSingleton<IPricingClient, StubPricingClient>();
        })).CreateClient();
}
```

- `ConfigureTestServices` runs **after** the app's own registrations, so it can replace them.
  `ConfigureServices` runs before and will be overwritten.
- Replace only the boundary the test cannot cross — an external HTTP dependency, a clock, a
  payment gateway. Replacing your own repositories turns an integration test into a slow unit
  test that proves nothing about the wiring.
- `Program` must be reachable: with top-level statements add
  `public partial class Program;` at the end of `Program.cs`.
- One factory per test class (via `IClassFixture`) — constructing the host per test dominates
  the runtime.
- Assert on what the client observes: status code, headers, body. Not on internal service
  calls.

## Testability: replace ambient state

Code that reads ambient state directly cannot be tested without the environment. Inject an
abstraction instead:

| Ambient | Inject |
|---|---|
| `DateTime.Now`/`UtcNow`, `Stopwatch`, `Task.Delay` | `TimeProvider` (`FakeTimeProvider` in tests) |
| `File`, `Directory`, `Path` | `System.IO.Abstractions`' `IFileSystem` |
| `Environment.GetEnvironmentVariable` | Bound options |
| `Random` | A seeded instance passed in |
| `Guid.NewGuid` | A small `IIdGenerator`, or accept the id as a parameter |
| `Console` | `ILogger<T>` or an output abstraction |
| `HttpClient` constructed inline | A typed client injected |

`TimeProvider` is the one that pays for itself immediately: it makes timeouts, retries,
expiry and scheduling testable without `Thread.Sleep` in a test.

## Test doubles

- Prefer a hand-written fake implementing the interface — an in-memory store, a stub client.
  It is readable, refactors with the interface, and has no framework to learn.
- Add a mocking library only when there is no interface you can implement, or when the test is
  genuinely about the interaction (that the message was published, exactly once).
- Never assert on mock calls as a substitute for asserting on behaviour. `Verify(x =>
  x.Save(It.IsAny<Order>()))` passes when `Save` writes nothing.
- Do not mock types you do not own (`DbContext`, `HttpClient`, framework classes). Wrap them
  or use the real thing against a test double at a lower layer (`Testcontainers`, a stub
  `HttpMessageHandler`).

## Shape of a good test

- Name it so a failure in CI is self-explanatory:
  `MethodOrBehaviour_Condition_ExpectedResult`.
- Arrange–Act–Assert with blank lines between the three; more than one Act means more than one
  test.
- One behaviour per test. A test that asserts five unrelated things reports only the first
  failure.
- Deterministic: no wall-clock time, no ordering dependence, no shared mutable static state, no
  network. A test that needs a retry to pass is a broken test.
- Use a builder or an object mother for complex fixtures so the test body shows only what
  matters to *this* case.
- Async tests return `Task`, never `void`, and never block on a result.

## Test smells

Signals worth flagging in review:

- No assertion, or an assertion that cannot fail (`Assert.NotNull` on a freshly constructed
  object, `Assert.True(true)`).
- Assertions on a mock instead of on the observable result.
- `try { ... } catch { }` around the act — the test passes when the code throws.
- Conditional logic in the test body: an `if` around an assert means the test sometimes checks
  nothing.
- Magic values with no name — `Assert.Equal(42.7m, total)` with no indication of where the
  number came from.
- Tests that depend on execution order or on another test's side effect.
- A test that changes whenever an implementation detail changes but never when behaviour does.
  Delete it; it is a maintenance tax with no defect-detection power.

<!-- sources: dotnet-official, dotnet-docs, kevintsengtw-testing, awesome-copilot, csharpguidelines -->
