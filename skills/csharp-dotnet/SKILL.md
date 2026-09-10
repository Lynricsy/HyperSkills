---
name: csharp-dotnet
description: "Guides C# and .NET application work end to end: C# language rules (nullable reference types and the nullability attributes, records, pattern matching, exception and disposal contracts), async and concurrency (ValueTask, cancellation, ConfigureAwait, thread-pool starvation, Channels), the SDK build (Directory.Build.props and .targets evaluation order, MSBuild properties and items, Central Package Management, incremental build, binlogs), ASP.NET Core (minimal APIs, DI lifetimes and captive dependencies, middleware, options, auth, OpenAPI, EF Core on the request path), Blazor render modes and prerendering, .NET MAUI, testing on Microsoft.Testing.Platform with xUnit, NUnit or MSTest, production diagnostics with dotnet-counters, dotnet-trace and dotnet-dump, and target-framework upgrades through .NET 10 and 11. Use when writing, reviewing, building, testing, profiling or upgrading .cs, .csproj, .razor, .props or .targets files. Do not use for Unity C# and its engine APIs, or for Azure resource orchestration."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# csharp-dotnet

## Scope

Covers application and library code on modern .NET: the C# language, the SDK build
(MSBuild, NuGet, Central Package Management), ASP.NET Core services and APIs, Blazor,
.NET MAUI, the testing stack, runtime and build diagnostics, and moving a codebase across
target frameworks. .NET 10 is the current LTS and the default target here; C# 14 is its
language version, and .NET 11 with C# 15 is the next STS.

Not covered: reviewing a diff for general correctness and risk — use the `code-review`
skill. Root-causing a reproducible local failure — use the `debugging` skill. Test-first
methodology and what deserves a test at all — use the `test-driven-development` skill.
Visual and layout design of a web UI — use the `frontend-design` skill. Unity C# and its
engine APIs, and Azure resource orchestration (Bicep, azd, ARM, Azure SDK clients), have
no skill here and are out of scope entirely; so are .NET Aspire orchestration, F# and
Visual Basic, database schema design, and Windows Forms/WPF beyond the upgrade checklist.

Paths below are relative to this skill's directory.

## Core rules

1. Read `global.json`, the target framework, `Directory.Build.props`/`.targets` and
   `Directory.Packages.props` before changing a project. Every rule below depends on which
   SDK, TFM and package policy the repository is actually on.
2. Adopt what the project already uses — minimal APIs or controllers, xUnit or MSTest,
   constructor injection or `Add*` extension methods. A second convention beside an
   existing one gives the same concept two answers.
3. `Directory.Build.props` is imported before the project file and `Directory.Build.targets`
   after the SDK targets. Defaults go in `.props`; anything reading an SDK-computed value
   goes in `.targets`.
4. A `PropertyGroup` conditioned on `$(TargetFramework)` inside a `.props` file never
   matches for a single-targeting project — the property is not set yet, so the condition
   fails silently. Move it to `.targets`. `ItemGroup` and `Target` conditions are unaffected.
5. Give shared defaults `Condition="'$(Prop)' == ''"`. Without it the value cannot be
   overridden, and an unconditional assignment in two files is a silent last-write-wins.
6. Append to list-valued properties: `<DefineConstants>$(DefineConstants);FEATURE_X</DefineConstants>`.
   A bare assignment drops every constant set upstream, including the SDK's own.
7. Quote both sides of every MSBuild comparison. `$(X)==Release` misevaluates or fails to
   parse the moment `X` is empty.
8. Under Central Package Management a `PackageReference` must not carry `Version` — that is
   NU1008. Put the version in `Directory.Packages.props` as `PackageVersion`, and use
   `VersionOverride` only where one project genuinely needs a different version.
9. Analyzer and build-tool packages need `PrivateAssets="all"`, or become
   `GlobalPackageReference` in `Directory.Packages.props`. Otherwise they flow transitively
   to everyone who consumes the library.
10. Do not restate SDK defaults or list `Compile` items in an SDK-style project. Redundant
    properties hide the real customisations and pin old behaviour when defaults change.
11. Add or remove a single package with `dotnet add package` / `dotnet remove package`; edit
    the XML directly for bulk alignment, conditional versions and `VersionOverride`, which
    the CLI cannot express. Either way, prove the result with `dotnet restore` and a build.
12. Custom targets declare `Inputs`/`Outputs` and register generated files in `FileWrites`,
    and every build question is answered from a binary log (`-bl`) or a preprocessed project
    (`-pp`) rather than from reading the files and guessing.
13. Turn on `<Nullable>enable</Nullable>` and let control flow prove non-nullness — a guard
    clause or pattern match creates a null-safe region. Reach for the null-forgiving operator
    only when a real external invariant cannot be expressed, and use the
    `System.Diagnostics.CodeAnalysis`
    attributes (`NotNullWhen`, `MemberNotNull`, `NotNullIfNotNull`, `DoesNotReturn`) for
    contracts the signature cannot carry.
14. A singleton must never capture a scoped service. The captured instance is promoted to
    singleton lifetime, which is a correctness bug (stale state, concurrent use), not a
    performance one. Scope validation catches it, but it is on by default only in the
    Development environment — set `ValidateScopes` and `ValidateOnBuild` explicitly.
15. A `DbContext` is scoped and is not thread-safe. Never hold one in a singleton or use one
    from two concurrent operations; take `IServiceScopeFactory` or `IDbContextFactory<T>`
    and create one per unit of work.
16. Conventional middleware is instantiated once, so a scoped dependency must arrive as a
    parameter of `InvokeAsync`, not through the constructor. Constructor injection of a
    scoped service throws at runtime; the alternative is factory-based middleware.
17. Never call `BuildServiceProvider()` while configuring services. It builds a second
    container with its own copies of every singleton. Use the options pattern, or the
    registration overload that hands you an `IServiceProvider`.
18. Never block on asynchronous work with `.Result`, `.Wait()` or `GetAwaiter().GetResult()`.
    It deadlocks wherever a synchronization context is captured and starves the thread pool
    where one is not — which is how an ASP.NET Core app stops responding under load.
19. `async void` is for event handlers only. Its exceptions are raised on the synchronization
    context and cannot be caught by the caller, so failures disappear.
20. A `ValueTask` may be awaited exactly once and never after the operation completes.
    Awaiting one twice is undefined behaviour; store the result, or call `AsTask()`.
21. Flow `CancellationToken` into every async call you make. A token that stops at the method
    signature makes shutdown and request abort silently ineffective.
22. `ConfigureAwait(false)` belongs in library code that might run under a UI or legacy
    ASP.NET synchronization context. ASP.NET Core has no synchronization context, so adding
    it there fixes nothing — the blocking call in rule 18 is the actual defect.
23. Get `HttpClient` from `IHttpClientFactory` or a typed client. A `new HttpClient()` per
    call exhausts sockets, and a long-lived static one never sees DNS changes.
24. Return `TypedResults` and an explicit `Results<Ok<T>, NotFound>`-style union from minimal
    API handlers, and surface failures as `ProblemDetails`. Untyped `Results.Ok(...)` leaves
    the generated OpenAPI document with no response schema.
25. Judge performance and memory only from a Release build in its real deployment form, with
    a deterministic reproduction and an equivalent before/after measurement. A single average
    from a Debug build cannot support any claim.

## Workflows

### add-feature

- [ ] Read the build files (rule 1) and one existing feature of the same shape to copy its
      layout, DI style and naming.
- [ ] Define the contract first: request/response `sealed record` types, the interface the
      feature depends on, and the failure cases. Never expose EF Core entities on the wire.
- [ ] Register services in an `Add{Feature}` extension method returning `IServiceCollection`,
      so the same wiring is reusable from `WebApplicationFactory` in tests.
- [ ] Pick the narrowest lifetime that works, then re-check rule 14 for every singleton you
      added.
- [ ] Write the handler last: async all the way, `CancellationToken` threaded through,
      `TypedResults` on the way out.
- [ ] Add packages per rule 11; if the repository uses CPM, the project file gets no version.
- [ ] Add tests per `add-tests`.
- [ ] **Gate:** `dotnet build -warnaserror` and `dotnet test` for the affected projects pass,
      and the new endpoint or entry point is exercised by at least one test.

### fix-build

- [ ] Reproduce with a clean build (`dotnet build --no-incremental`) and capture a binary log:
      `dotnet build -bl:build.binlog`. Read the log, not the console tail.
- [ ] Classify first: restore/NuGet error (NU*), evaluation problem (a property or item is
      not what you expect), compile error, or a custom target misbehaving.
- [ ] For an evaluation problem run `dotnet msbuild -pp:preprocessed.xml <project>` and find
      which file wrote the final value — rules 3 to 7 are the usual causes.
- [ ] For NU1008/NU1010 and version drift, check CPM state: is
      `ManagePackageVersionsCentrally` on, does every `PackageReference` lack `Version`, is
      there a stray version in an imported `.props`.
- [ ] For "it rebuilds when nothing changed", look for custom targets with no `Inputs`/
      `Outputs`, outputs written outside the declared `Outputs`, and volatile values
      (timestamps, GUIDs) in a path.
- [ ] **Gate:** two consecutive builds — the second reports the targets as skipped/up to date,
      and `dotnet restore` is clean.

### review

- [ ] Establish the diff scope and read its tests first; they state what the author believes
      the code does.
- [ ] Walk the Core rules in order — they are ordered by how often each one is the real defect.
- [ ] Check the DI diff separately: new singletons against rule 14, new middleware against
      rule 16, any `BuildServiceProvider` against rule 17.
- [ ] Check every `await`-free `Task` return, every `.Result`, every `async void`, and every
      `CancellationToken` parameter that is accepted but never passed on.
- [ ] Check the build diff separately: versions outside the central file, new analyzer
      packages without `PrivateAssets`, properties added unconditionally.
- [ ] Report with the Output format below.
- [ ] **Gate:** every finding carries `path:line`, one line of reasoning, and a concrete fix.

### diagnose-runtime-issue

- [ ] Establish the symptom and the violated target in numbers, then a deterministic
      reproduction on a Release build in its real deployment form (rule 25).
- [ ] Record the environment before collecting anything: commit, SDK and runtime versions,
      OS, architecture, container limits, and the exact commands used.
- [ ] Start with counters (`dotnet-counters monitor`): thread-pool queue length and thread
      count point at blocking (rule 18); Gen 2/LOH growth points at a leak; high time-in-GC
      points at allocation rate.
- [ ] Then take the artefact the symptom calls for — `dotnet-trace collect` for CPU and
      wall-clock time, `dotnet-dump collect` for a hang or a leak, and analyse the dump with
      `dotnet-dump analyze` (`dumpheap -stat`, `gcroot`).
- [ ] Change one thing, then re-measure the same workload the same way. Report before and
      after with the spread, not a single average.
- [ ] **Gate:** the report names the dominant cause with the evidence that identifies it, and
      the after-measurement comes from an equivalent run.

### add-tests

- [ ] Use the framework already in the repository. For a new test project, default to
      xUnit v3 on Microsoft.Testing.Platform.
- [ ] Put pure logic in unit tests, and test the composed application through
      `WebApplicationFactory<TEntryPoint>`, replacing only the boundary the test needs.
- [ ] Replace ambient state with an injectable abstraction — `TimeProvider` for time,
      `System.IO.Abstractions` for the file system — instead of asserting around it.
- [ ] Prefer a hand-written fake at an interface boundary; add a mocking library only when
      there is no interface you can implement.
- [ ] Assert observable behaviour: the response the caller sees, the row that was written,
      the message that was published. Not the calls made on a mock.
- [ ] **Gate:** `dotnet test` passes, and each new test fails when the behaviour it covers is
      broken.

### upgrade-target-framework

- [ ] Record the current TFMs, SDK, and package versions, and get a clean build with zero new
      warnings on the current target first. That is the baseline every later failure is
      compared against.
- [ ] Move one major version at a time. Change `TargetFramework`, then bring
      `Microsoft.Extensions.*`, `Microsoft.AspNetCore.*` and `Microsoft.EntityFrameworkCore.*`
      to the matching major version, in `Directory.Packages.props` if CPM is on.
- [ ] Run `dotnet restore` and read the new NuGet diagnostics before building: pruned
      framework-provided packages (NU1510) should be removed rather than pinned.
- [ ] Build, then work through errors by area — compiler/language, core libraries, ASP.NET
      Core, EF Core, serialization, cryptography, containers — committing per area.
- [ ] Then look for behavioural changes, which the compiler cannot show you: they surface as
      failing tests or changed output, not as build errors.
- [ ] Update the Dockerfile, CI SDK version and `global.json` last, in one commit.
- [ ] **Gate:** clean build with no new warnings, full test suite green, and the app starts
      and serves one real request on the new runtime.

## Topic router

| Topic | Read when | File |
|---|---|---|
| C# language | Nullability, records, pattern matching, exceptions, disposal, Span, generics | `references/csharp-language.md` |
| Async and concurrency | `async`/`await`, `ValueTask`, cancellation, Channels, parallelism, thread pool | `references/async-concurrency.md` |
| Build, MSBuild and NuGet | Project files, `Directory.Build.*`, CPM, restore errors, incremental build, binlogs | `references/build-msbuild-nuget.md` |
| ASP.NET Core | Minimal APIs, controllers, DI, middleware, options, auth, OpenAPI, EF Core on the request path | `references/aspnetcore.md` |
| Blazor | Render modes, prerendering, component authoring, JS interop, disposal | `references/blazor.md` |
| .NET MAUI | App lifecycle, bindings, Shell navigation, `CollectionView`, platform code | `references/maui.md` |
| Testing | Choosing a framework or test level, MTP, integration tests, testability | `references/testing.md` |
| Diagnostics and performance | Slow, leaking, hanging or allocation-heavy code in a real environment | `references/diagnostics.md` |
| Upgrades | Moving target frameworks, adopting nullable, trimming and Native AOT | `references/upgrade.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
src/Orders.Api/Program.cs
  L11 blocking - OrderCache is a singleton holding the scoped OrdersDbContext. The context
       is promoted to singleton lifetime, so it serves stale data and throws on concurrent
       use.
       before: builder.Services.AddSingleton<IOrderCache, OrderCache>();  // ctor takes OrdersDbContext
       after:  OrderCache takes IDbContextFactory<OrdersDbContext> and creates one per call.
  L44 blocking - http.GetStringAsync(...).Result blocks a request thread; under load this
       starves the thread pool. Make the handler async and await it.
  L82 important - TenantMiddleware takes the scoped IOrderRepository in its constructor.
       Move it to a parameter of InvokeAsync.

src/Orders.Api/Orders.Api.csproj
  ✓ pass
```

Severities: `blocking` (wrong behaviour, data loss, crash, build break, removed API),
`important` (leaks, lifetime and thread-safety hazards, missing cancellation, silently
dropped configuration), `minor` (naming, redundant defaults, dead code). End with a one-line
verdict: ship, ship after blocking fixes, or rework.

## Environment

The .NET SDK, from `global.json` when the repository pins one. Commands used above:

```bash
dotnet --info                            # SDK and runtimes actually installed
dotnet restore                           # NuGet errors surface here, not in build
dotnet build --no-incremental -bl:b.binlog   # clean build plus a binary log to read
dotnet msbuild -pp:pp.xml <project>      # fully expanded project: who set which property
dotnet test                              # builds by default; add --no-build to reuse output
dotnet format --verify-no-changes        # only where the repository already uses it
```

Diagnostics need the global tools, installed on demand and independent of the app:

```bash
dotnet tool install -g dotnet-counters   # live runtime counters
dotnet tool install -g dotnet-trace      # CPU and event traces
dotnet tool install -g dotnet-dump       # dump capture and post-mortem analysis
```

MAUI additionally needs the platform workloads (`dotnet workload install maui`), and iOS and
Mac Catalyst targets additionally require macOS with Xcode.
