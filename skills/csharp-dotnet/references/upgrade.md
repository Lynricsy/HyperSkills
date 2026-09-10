# Upgrades

Verified against: .NET 10 (LTS). .NET 11 is the next STS; the .NET 11 section covers changes
documented while it was in preview and must be re-checked against the release notes at GA.

## Contents

- [Support state](#support-state)
- [The sequence](#the-sequence)
- [Where the errors come from](#where-the-errors-come-from)
- [.NET 9 to .NET 10](#net-9-to-net-10)
- [.NET 10 to .NET 11](#net-10-to-net-11)
- [Adopting nullable reference types](#adopting-nullable-reference-types)
- [Trimming and Native AOT](#trimming-and-native-aot)
- [Legacy .NET Framework](#legacy-net-framework)

## Support state

| Channel | Type | State |
|---|---|---|
| .NET 10 | LTS | Active — the default target for new work |
| .NET 11 | STS | The next release; C# 15 |
| .NET 9, .NET 8 | STS / LTS | Maintenance, both ending shortly — plan the move off them |

Check the current state from `dotnet/core`'s `release-notes/releases-index.json` rather than
assuming; support phases move.

## The sequence

Upgrade **one major version at a time**. Jumping two versions merges two independent sets of
breaking changes into one debugging session.

1. Get a clean build with zero new warnings on the current target. That baseline is what every
   later failure is compared against; skipping it means you cannot tell a pre-existing warning
   from one you caused.
2. Bump `TargetFramework` (or add the new TFM to `TargetFrameworks`).
3. Bring `Microsoft.Extensions.*`, `Microsoft.AspNetCore.*` and `Microsoft.EntityFrameworkCore.*`
   to the matching major version — in `Directory.Packages.props` if the repository uses CPM.
4. `dotnet restore` and read the NuGet diagnostics *before* building. NU1510 means the package
   is now part of the shared framework: remove the reference rather than pinning it.
5. Build, and work through errors by area, committing per area.
6. Then hunt behavioural changes, which produce no build error. They surface as failing tests
   or wrong output.
7. Update `global.json`, the Dockerfile base images and the CI SDK version last, in one commit.

Commit at each boundary. A bisectable history is the difference between "the upgrade broke
something" and "this commit broke this thing".

## Where the errors come from

Check which of these the project uses, because it determines which breaking changes apply at
all:

| Signal | Area |
|---|---|
| `Microsoft.NET.Sdk.Web` | ASP.NET Core |
| `Microsoft.EntityFrameworkCore.*` | EF Core |
| `<UseWPF>`/`<UseWindowsForms>` | Desktop |
| A Dockerfile | Base images, ICU, globalization |
| P/Invoke, `DllImport` | Interop and native library resolution |
| `System.Text.Json` with polymorphism | Serialisation |
| Cryptography APIs | Algorithm availability and obsoletions |
| `BackgroundService` | Host lifetime semantics |

## .NET 9 to .NET 10

Language and compiler (C# 14):

- `field` is a contextual keyword inside property accessors. A local named `field` is now
  CS9272 (error); a member named `field` referenced without `this.` is CS9258 (warning).
  Rename, or escape as `@field`.
- `extension` is a contextual keyword: a type, alias or type parameter with that name must be
  renamed or escaped.
- Overload resolution changed around span parameters. `.Contains()` on an array can now bind to
  `MemoryExtensions.Contains` instead of `Enumerable.Contains`, and `Enumerable.Reverse` on an
  array can resolve to the in-place span extension. Inside expression trees this is a compile
  error; elsewhere it can silently change behaviour. Fix with `.AsEnumerable()` or an explicit
  static call.

Libraries and SDK:

- `System.Linq.Async` conflicts with the built-in `System.Linq.AsyncEnumerable`. Remove the
  package, or exclude its compile assets if it arrives transitively.
- New obsoletions SYSLIB0058–SYSLIB0062, notably `Rfc2898DeriveBytes` constructors (use the
  static `Rfc2898DeriveBytes.Pbkdf2`) and `SslStream`'s individual algorithm properties (use
  `NegotiatedCipherSuite`). If those properties were used to *reject* weak ciphers, port the
  check — do not just delete it.
- `dotnet new sln` defaults to the SLNX format.
- `dotnet restore` now audits transitive packages, so new advisory warnings are expected.

ASP.NET Core:

- `Microsoft.AspNetCore.OpenApi` 10 depends on `Microsoft.OpenApi` v2, which restructures
  namespaces and models: `OpenApiString`/`OpenApiAny` are gone (use `JsonNode`), schema
  collections may be null, `OpenApiSchema.Nullable` is removed. Any custom document or schema
  transformer needs rewriting.
- `WebHostBuilder`/`IWebHost`, `IActionContextAccessor`, `WithOpenApi` and Razor runtime
  compilation are obsolete.

Behavioural changes (no build error):

- The runtime no longer registers a default SIGTERM handler. Generic Host and ASP.NET Core apps
  register their own, but a plain console app in a container must call
  `PosixSignalRegistration.Create(PosixSignal.SIGTERM, ...)` to shut down cleanly.
- `BackgroundService.ExecuteAsync` now runs entirely on a background thread, so the synchronous
  part before the first `await` no longer blocks startup. Move startup-ordering work to
  `StartAsync`.
- Configuration preserves JSON `null` instead of converting it to an empty string — a bound
  property with a non-default initial value now gets overwritten with `null`.
- EF Core translates `.Contains()` on a collection as scalar parameters rather than
  JSON/OPENJSON, which changes plans for large collections.
- Default container base images moved from Debian to Ubuntu.
- `Uri` length limits were removed; if `Uri` construction was used to reject oversized untrusted
  input, add an explicit length check.
- `XmlSerializer` no longer ignores `[Obsolete]` properties — audit for accidental exposure.

## .NET 10 to .NET 11

Language and compiler (C# 15):

- Collection expressions of `Span<T>`/`ReadOnlySpan<T>` have declaration-block safe-context;
  assigning one to an outer-scope variable is now an error.
- `with(...)` inside a collection expression is parsed as constructor arguments; a method
  named `with` must be escaped as `@with(...)`.
- `nameof(this.P)` in an attribute must become `nameof(P)`.
- `(X.Y) when` in a switch arm now parses as a constant pattern with a `when` clause rather
  than a cast.

Libraries and hosting:

- **An unhandled exception from `BackgroundService.ExecuteAsync` stops the host.** Any
  background loop that should survive a transient failure needs its own `try`/`catch`.
- SYSLIB0063 obsoletes the `NamedPipeClientStream` constructor taking `isConnected`; with
  `TreatWarningsAsErrors` that is a build break.
- `Microsoft.OpenApi` moves to v3 — another round of changes for direct users.
- EF Core: the Cosmos provider's synchronous I/O now always throws; `Microsoft.EntityFrameworkCore.Design`
  is no longer pulled in transitively by `.Tools`/`.Tasks`.
- Compression and archive APIs validate more: ZIP CRC32 and TAR header checksums are now
  checked, so previously-tolerated corrupt archives throw.
- Minimum hardware baseline moves to `x86-64-v2`, and Windows Arm64 requires LSE. Verify the
  deployment target before shipping.
- `SqlClient` 7.0 separates Entra ID authentication into its own package.
- Blazor `Virtualize` changes its default `OverscanCount` from 3 to 15.
- Native AOT native libraries on Unix gain the `lib` filename prefix.

## Adopting nullable reference types

Turning `<Nullable>enable</Nullable>` on repository-wide produces thousands of warnings and
nobody fixes them. Do it in slices:

1. Enable annotations and warnings in `Directory.Build.props`, then set
   `<Nullable>disable</Nullable>` in the projects not ready yet, so the default for new
   projects is on.
2. Inside a project, migrate file by file with `#nullable enable` at the top. Start with the
   leaves — models and value objects — because their annotations propagate outward.
3. Fix by shape, not by warning count: CS8618 (uninitialised non-nullable member) is usually
   `required` or constructor initialisation; CS8602 (possible dereference) is usually a missing
   guard clause; CS8603/CS8604 usually mean the signature is wrong rather than the code.
4. The null-forgiving operator is a last resort. A migration that ends with hundreds of them
   has moved the warnings, not removed the bugs.
5. Turn nullable warnings into errors for the migrated project once it is clean, so it stays
   clean.

## Trimming and Native AOT

`PublishTrimmed` and `PublishAot` remove code the linker cannot see being used. Reflection is
exactly that.

- Set `<IsAotCompatible>true</IsAotCompatible>` on a library to get the analyzers, and fix the
  warnings before publishing anything.
- The warning families: IL2026 (a member requires unreferenced code), IL2067/IL2070/IL2072
  (a type flowing into a reflection call whose members cannot be statically determined), IL3050
  (dynamic code required at runtime).
- Annotate with `[DynamicallyAccessedMembers]` where the reflection is genuine and bounded;
  replace it where it is not. Source generators are the escape route — a
  `JsonSerializerContext` for `System.Text.Json`, `[GeneratedRegex]` for regular expressions,
  the logging and configuration-binding generators for the rest.
- `[RequiresUnreferencedCode]`/`[RequiresDynamicCode]` propagate the warning to callers, which
  is the honest answer for an API that genuinely cannot be trimmed.
- Test the published, trimmed output. Trimming failures appear only at runtime, only in the
  published configuration, and often only on a code path that runs once a month.

## Legacy .NET Framework

Moving from .NET Framework is a port, not an upgrade, and it is out of the one-version-at-a-time
sequence above. The shape of the work:

- Convert projects to the SDK-style format first, while still on `net48`. That alone is a
  reviewable change.
- Replace framework-only dependencies: `System.Web`, WCF server-side, AppDomains, remoting,
  `ConfigurationManager`, `HttpContext.Current`.
- `Microsoft.Windows.Compatibility` covers a surprising amount of the surface and buys time.
- Run the .NET Upgrade Assistant for the mechanical parts, then review every change it made;
  it is a starting point, not an authority.

<!-- sources: dotnet-official, dotnet-docs, aaronontheweb -->
