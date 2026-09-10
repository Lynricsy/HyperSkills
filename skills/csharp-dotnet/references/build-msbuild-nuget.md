# Build: MSBuild and NuGet

Verified against: .NET 10 SDK.

## Contents

- [Evaluation order](#evaluation-order)
- [What belongs in which file](#what-belongs-in-which-file)
- [Property patterns](#property-patterns)
- [Item patterns](#item-patterns)
- [Multi-level Directory.Build files](#multi-level-directorybuild-files)
- [Central Package Management](#central-package-management)
- [Adopting CPM in an existing repository](#adopting-cpm-in-an-existing-repository)
- [Package reference hygiene](#package-reference-hygiene)
- [Custom targets](#custom-targets)
- [Incremental build](#incremental-build)
- [Diagnosing a build](#diagnosing-a-build)
- [Anti-pattern checklist](#anti-pattern-checklist)

## Evaluation order

```
Directory.Build.props → SDK .props → YourProject.csproj → SDK .targets → Directory.Build.targets
```

Two consequences drive almost every build surprise:

- A project file can override anything `Directory.Build.props` set, because it is evaluated
  later. A value in `Directory.Build.targets` cannot be overridden by the project at all.
- Anything the SDK computes (`OutputPath`, `TargetFramework` for a single-targeting project,
  `TargetFrameworkIdentifier`) is **not available** while `.props` is being evaluated.

The second point has a specific, silent consequence: a `PropertyGroup` with
`Condition="'$(TargetFramework)' == 'net10.0'"` in a `.props` file never matches for a
single-targeting project. Nothing warns; the properties simply are not set. Move that group to
`Directory.Build.targets` or into the project file. `ItemGroup` and `Target` conditions are
evaluated later and are not affected.

MSBuild auto-imports only the **first** `Directory.Build.props` found walking up from the
project. File name casing is exact on Linux and macOS.

## What belongs in which file

| `Directory.Build.props` | `Directory.Build.targets` |
|---|---|
| Language settings (`Nullable`, `LangVersion`, `ImplicitUsings`) | Custom targets |
| Assembly and package metadata | Late-bound overrides that read SDK values |
| Warning policy, analyzer settings | Post-build validation |
| Analyzer `PackageReference` items | Anything conditioned on `$(TargetFramework)` in a single-target project |

Not in either: project-specific TFMs and package references.

`Directory.Build.rsp` holds default MSBuild command-line arguments for everything under the
directory (one per line, e.g. `/maxcpucount`, `/nodeReuse:false`) — useful for making CI and
local builds behave identically.

`<ArtifactsPath>$(MSBuildThisFileDirectory)artifacts</ArtifactsPath>` (.NET 8+) puts every
project's `bin`, `obj` and `publish` under one tree keyed by project name, which removes the
whole class of output-directory clashes between projects that share a name.

## Property patterns

```xml
<PropertyGroup>
  <!-- Overridable default: the caller, the CI command line, or the project can win. -->
  <Configuration Condition="'$(Configuration)' == ''">Debug</Configuration>

  <!-- List-valued: always carry the previous value forward. -->
  <DefineConstants>$(DefineConstants);FEATURE_X</DefineConstants>
  <NoWarn>$(NoWarn);CS1591</NoWarn>
</PropertyGroup>
```

Rules that repeatedly matter:

- Quote both sides: `'$(Prop)' == 'Release'`. `$(Prop)==Release` fails to parse or
  misevaluates when the property is empty.
- Without `Condition="'$(Prop)' == ''"`, a property in a shared file cannot be overridden, and
  two unconditional assignments become an invisible last-write-wins.
- Overwriting `DefineConstants`, `NoWarn` or `TargetFrameworks` without `$(...)` discards
  everything the SDK and every earlier file contributed.
- Paths: `$(MSBuildThisFileDirectory)` (already ends with a separator),
  `$([MSBuild]::NormalizePath(...))`, `$([MSBuild]::GetDirectoryNameOfFileAbove(...))`. Never
  a hardcoded absolute path.
- Backslashes matter where the string leaves MSBuild — inside `<Exec Command="...">`, in text
  written by `WriteLinesToFile`, in response files. MSBuild's evaluator normalises separators
  for `Import` and for built-in tasks, so a backslash there is a style issue, not a bug. Use
  forward slashes in new code either way.
- TFM helpers for multi-targeting:
  `$([MSBuild]::GetTargetFrameworkIdentifier('$(TargetFramework)'))`,
  `$([MSBuild]::IsTargetFrameworkCompatible('$(TargetFramework)', 'net8.0'))`,
  `$([MSBuild]::IsOSPlatform('windows'))`.

## Item patterns

- SDK-style projects glob `**/*.cs` already. Explicit `<Compile Include>` items are redundant
  and cause "duplicate compile item" errors. Use `<Compile Remove="Legacy/**" />` to opt out.
  The exception is F#, where compilation order is significant and every file must be listed.
- Use `Update` (not `Include`) to add metadata to an item the SDK already globbed —
  `<None Update="appsettings.json" CopyToOutputDirectory="PreserveNewest" />`.
- `Include` on an already-globbed file is the usual cause of NETSDK1022.

## Multi-level Directory.Build files

Only the nearest file is imported automatically. To layer `src/` and `test/` settings on top
of repo-wide ones, import the parent explicitly at the top of the inner file:

```xml
<Project>
  <Import Project="$([MSBuild]::GetPathOfFileAbove('Directory.Build.props', '$(MSBuildThisFileDirectory)../'))"
          Condition="Exists('$([MSBuild]::GetPathOfFileAbove('Directory.Build.props', '$(MSBuildThisFileDirectory)../'))')" />
  <!-- inner overrides below -->
</Project>
```

Guard optional imports with `Exists()`; leave required imports unguarded so a missing file
fails loudly. (Files under a NuGet package's `build/`/`buildTransitive/` folders are a
documented exception — they import siblings that exist only in the packed layout.)

## Central Package Management

`Directory.Packages.props` at the repository root:

```xml
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>

  <ItemGroup>
    <PackageVersion Include="Serilog.AspNetCore" Version="9.0.0" />
    <PackageVersion Include="xunit.v3" Version="3.1.0" />
  </ItemGroup>

  <ItemGroup>
    <!-- Applied to every project; the right home for analyzers. -->
    <GlobalPackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="10.0.0" />
  </ItemGroup>
</Project>
```

Project files then reference without a version:

```xml
<PackageReference Include="Serilog.AspNetCore" />
```

- A `Version` on a `PackageReference` while CPM is on is **NU1008**. That is the first thing
  to check when restore breaks in a repository that has just adopted CPM.
- `VersionOverride="..."` on a single `PackageReference` is the sanctioned escape hatch for
  the one project that must differ. Use it deliberately, not to silence NU1008.
- Keep a shared MSBuild property (`$(SerilogVersion)`) only where it expresses a real
  constraint — a family of packages that must ship in lockstep. A one-off property indirecting
  a single version is noise; inline it.
- Conditional versions per TFM are expressed with a `Condition` on the `PackageVersion` item.

## Adopting CPM in an existing repository

1. Stop if any project still uses `packages.config` — migrate it to `PackageReference` first.
2. Capture a baseline: clean, restore, build, and record the resolved package graph
   (`dotnet list package --include-transitive`) plus a binary log. Every later comparison is
   against this.
3. Audit: package ids and resolved versions per project, conflicts, versions coming from
   MSBuild properties, conditional references, and references living in imported
   `.props`/`.targets` files rather than in `.csproj`.
4. Decide the conflict strategy explicitly (usually "take the highest version already in the
   repository") and record which projects move. Aligning across a major version is a
   behavioural change and needs a test run; a minor/patch alignment usually does not.
5. Write `Directory.Packages.props`, then remove `Version` from managed `PackageReference`
   items while preserving `Condition`, `PrivateAssets`, `IncludeAssets`, `ExcludeAssets` and
   `GeneratePathProperty`.
6. Restore, build, and diff the resolved package graph against the baseline. An unexplained
   version change is a defect, not a detail.

Do not fold a version upgrade into the conversion. Convert first, upgrade after, so a
regression has one candidate cause.

## Package reference hygiene

- `PrivateAssets="all"` on analyzers, source generators and build-only tools, or declare them
  as `GlobalPackageReference`. Without it they flow to every downstream consumer.
- Direct-reference a package you use in code even if it arrives transitively; a transitive
  version can disappear in any upgrade.
- NU1510 on a newer SDK means the package is now provided by the shared framework — remove the
  reference rather than pinning it.
- Enable `<NuGetAudit>` (on by default) and read the advisories; treat a transitive
  vulnerability as a real finding.

## Custom targets

```xml
<Target Name="WriteVersionFile"
        BeforeTargets="CoreCompile"
        Inputs="$(MSBuildProjectFile)"
        Outputs="$(IntermediateOutputPath)version.txt">
  <WriteLinesToFile File="$(IntermediateOutputPath)version.txt" Lines="$(Version)" Overwrite="true" />
  <ItemGroup>
    <FileWrites Include="$(IntermediateOutputPath)version.txt" />
  </ItemGroup>
</Target>
```

- One responsibility per target; a 50-line target cannot be skipped, debugged or extended.
- Use built-in tasks (`Copy`, `MakeDir`, `Delete`, `WriteLinesToFile`, `Touch`) rather than
  `Exec` with shell commands. They are cross-platform, participate in incremental build and
  log structurally.
- Register everything you generate in `FileWrites` so `Clean` removes it.
- Defaults belong in `.props`, not in a `.targets` file where an earlier target may already
  have read the empty value.

## Incremental build

A build that redoes work when nothing changed is almost always one of:

- a custom target with no `Inputs`/`Outputs` — it runs every time by definition;
- outputs written outside the declared `Outputs`, so the timestamp comparison never sees them;
- a volatile value (timestamp, GUID, `$([System.DateTime]::Now)`) in a path or a generated
  file, which changes the input on every evaluation;
- generated files not registered in `FileWrites`;
- a glob whose match set changes between builds.

In a binary log, look for `Building target "X" completely` versus `Skipping target "X" because
all output files are up-to-date` — the log states the reason.

## Diagnosing a build

```bash
dotnet build --no-incremental -bl:build.binlog   # clean build + structured log
dotnet msbuild -pp:preprocessed.xml MyProject.csproj   # all imports inlined, final values
dotnet build -getProperty:OutputPath              # one property's evaluated value
dotnet restore --force-evaluate                   # re-evaluate the graph after CPM edits
```

Read the binary log with the MSBuild Structured Log Viewer or `dotnet msbuild` log analysis;
never read it as text. Answer "why is this property that value?" from `-pp`, not by reading
the files in order and reasoning — imports make the effective order non-obvious.

## Anti-pattern checklist

Run through this when reviewing a project or shared build file:

- `<Exec>` doing what a built-in task does.
- Unquoted conditions.
- Hardcoded absolute paths.
- Restated SDK defaults (`OutputType=Library`, `EnableDefaultItems=true`, `RootNamespace`
  equal to the project name).
- Manual `<Compile Include>` in an SDK-style project.
- `<Reference>` with a `HintPath` into a `packages/` folder.
- Analyzer packages without `PrivateAssets`.
- The same `PropertyGroup` copy-pasted into three or more projects.
- Package versions scattered across projects instead of a central file.
- A target with no `Inputs`/`Outputs`.
- Defaults set in `.targets`, logic in `.props`.
- An unguarded optional `<Import>`.
- The same property set unconditionally in a shared file and in a project.

<!-- sources: dotnet-official, aaronontheweb, awesome-copilot, dotnet-docs -->
