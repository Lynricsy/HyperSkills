# Modules, build, packaging and tests (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]`; nothing
in this file was checked against a running engine.

## Contents

- [Modules](#modules)
- [Build.cs](#buildcs)
- [Module descriptors in .uproject and .uplugin](#module-descriptors-in-uproject-and-uplugin)
- [Editor code in a runtime module](#editor-code-in-a-runtime-module)
- [Live Coding](#live-coding)
- [Cook, package, deploy, run](#cook-package-deploy-run)
- [Release versions and patches](#release-versions-and-patches)
- [Automation tests](#automation-tests)
- [Low-Level Tests](#low-level-tests)
- [Measuring a frame](#measuring-a-frame)
- [Editor automation from an agent](#editor-automation-from-an-agent)
- [Failure symptom table](#failure-symptom-table)

## Modules

A module is the unit of Unreal's architecture: a standalone piece of code with its own
dependencies, its own `Public`/`Private` split, and a controllable load point. Every module
needs a `[ModuleName].Build.cs` in its root directory — without it the build system does not
know the module exists.

Unreal Build Tool builds from the `Target.cs` and `Build.cs` files, **not** from the IDE
solution. "It compiles in my IDE" is therefore not evidence about the build; and after
editing a `Build.cs` or moving source files between folders you must regenerate project
files before the IDE agrees with reality.

UBT compiles only the modules that appear in your project's dependency chain. A module that
nothing depends on is skipped entirely, which is why a missing entry surfaces as an
unresolved external symbol rather than as "module not found".

## Build.cs

```csharp
using UnrealBuildTool;

public class ArenaGame : ModuleRules
{
    public ArenaGame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        // Used in this module's public headers -> propagates to dependents
        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput"
        });

        // Used only in .cpp files -> cheaper for everyone downstream
        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "UMG", "Slate", "SlateCore", "Niagara",
            "GameplayAbilities", "GameplayTags", "GameplayTasks"
        });
    }
}
```

- `PublicDependencyModuleNames` is for modules used **publicly**, such as in a public `.h`,
  so that modules depending on yours can include your headers without extra work.
- `PrivateDependencyModuleNames` is for modules used only privately, in `.cpp` files. Private
  dependencies are preferred wherever possible because they reduce compile times.
- Putting everything in the public list is not "safer": it propagates every include and every
  rebuild to every dependent module.
- Plugin modules must also be *enabled* for the project. A `Build.cs` entry for a module that
  belongs to a disabled plugin does not build.

## Module descriptors in .uproject and .uplugin

```json
{
    "Modules": [
        { "Name": "ArenaGame", "Type": "Runtime", "LoadingPhase": "Default" },
        { "Name": "ArenaGameEditor", "Type": "Editor", "LoadingPhase": "PostEngineInit" }
    ]
}
```

- The common types are `Runtime` for in-game classes and `Editor` for editor-only classes.
  Most gameplay modules only need a name; `Type` defaults matter when they do not.
- Loading order **within** a `LoadingPhase` is not deterministic. If one module must be
  initialized before another — for example inside `StartupModule` — call `LoadModule` or
  `LoadModuleChecked` explicitly instead of relying on the order; use `GetModule` when the
  module may legitimately be absent.
- Do not declare dependencies in the descriptor's `AdditionalDependencies` when a `Build.cs`
  entry will do; the documentation points you at `Build.cs`.

## Editor code in a runtime module

Editor-only modules such as `UnrealEd` and the asset tooling exist in editor targets only. A
runtime game module that lists one compiles happily in the editor and fails when a packaged
(Development, Shipping, or server) target is built, because the module is not part of that
target at all. The fix is structural: move the editor code into an `Editor`-type module, or —
for a small amount of code — gate it with `WITH_EDITOR` and keep the dependency behind
`Target.bBuildEditor`.

This asymmetry is the single most common "works in the editor, fails to package" cause worth
checking first.

## Live Coding

Live Coding (an integration of Live++) rebuilds C++ and patches the running binary. It works
in the editor, in Play-In-Editor, and in a packaged desktop build attached to the editor; it
is **not** available when launching on consoles or mobile. `Ctrl+Alt+F11` starts a build.

Behaviour worth knowing before blaming the engine:

- Default values changed in a **constructor in a `.cpp`** do not update existing instances;
  the same change made in the **header** does take effect.
- Object Reinstancing (on by default) replaces existing instances so structural changes —
  new functions, new variables, refactors — can take effect. It covers anything declared with
  `UCLASS`, `UFUNCTION`, `USTRUCT`, `UENUM` and `UDELEGATE`, plus the generated artefacts such
  as Blueprint nodes. Disabling it makes large changes behave unpredictably and usually
  crash.
- With reinstancing on, code that caches pointers to reinstanced objects must update them
  through `ReloadReinstancingCompleteDelegate`/`ReloadCompleteDelegate`. Stale caches
  typically crash **on editor shutdown**, because only one version of a destructor can exist.
- Module preloading speeds up iteration on the preloaded modules and slows editor start.
  Avoid preloading engine modules unless you are changing engine source.
- Hot Reload still exists as a fallback if Live Coding is disabled, and tolerates stale
  reinstanced pointers better — which hides the bug rather than fixing it.

A new module or a changed `Build.cs` is a build-graph change, not a patch: regenerate project
files and build normally.

## Cook, package, deploy, run

The Automation Tool's `BuildCookRun` command drives six stages: **Build** (compile the
executables), **Cook** (convert assets into the platform's formats), **Stage** (copy to a
staging directory), **Package** (platform distribution format), **Deploy** (push to a
device), **Run**.

```bash
# Windows; use RunUAT.sh on Linux and macOS
Engine/Build/BatchFiles/RunUAT.bat BuildCookRun -project=MyProject.uproject -clientconfig=Shipping
UnrealEditor-cmd.exe MyProject.uproject -run=cook -targetplatform=Windows
```

Cooking converts source formats (PNG, WAV) into platform formats, which on some platforms are
proprietary and readable only there. Two modes:

- **Cook By the Book** — everything ahead of time. What performance tests, playtests and
  releases use.
- **Cook On the Fly** — a cook server feeds the running game on demand. For iterating on
  individual assets, not for measuring anything.

Authoring UAT command lines by hand is error-prone; build a custom launch profile in the
Project Launcher, run it once, and copy the command line it prints from `BuildCookRun`
onward.

If a platform is missing or greyed out, check the platform SDK version the engine supports,
the platform's external tooling, and whether the device is claimed in the Device Manager.

## Release versions and patches

To package a release through the Project Launcher: Build configuration **Shipping**, Cook
**By the Book** with the cultures and maps you ship, and — under the release settings — tick
"create a release version" with a version number. Compress content, save packages without
versions, and store content in a single pak unless you have a reason not to; set the cooker
build configuration to Shipping too.

Keep the asset registry and pak from `[Project]/Releases/[Version]/[Platform]`: every later
patch and DLC is diffed against them. On Windows the staged build to test is under
`Saved/StagedBuilds/`.

## Automation tests

The Automation Test Framework is C++, is not associated with the UObject environment, and
depends on engine systems — the documentation is explicit that it is **not ideal for pure
unit testing**. Test categories: Unit (API-level), Feature (system-level such as PIE or
resolution changes), Smoke, Content Stress (load every map, compile every Blueprint) and
Screenshot Comparison. Interfaces on top of it include Automation Spec (BDD), Automation
Driver (input simulation), Functional Testing (level tests in Blueprint), CQTest (fixtures
and async syntax), and the screenshot comparison tool.

Epic's own design guidelines, which are also the review criteria for a test:

- Do not assume the state of the game or the editor — tests can run out of order or in
  parallel across machines.
- Leave files on disk as you found them; delete anything the test generates.
- Assume the previous run left a bad state, and clean up *before* the test starts.
- A Smoke test is a speed promise: it must complete within one second, and only unit tests or
  fast feature tests should be marked Smoke.

Tests can live in plugins, which lets you enable them individually and keep their content out
of the project's `Content` folder. Automation test plugins must be enabled in
*Edit > Plugins > Testing*, followed by an editor restart, before `Window > Test Automation`
appears.

## Low-Level Tests

Low-Level Tests are the framework for genuine unit tests, decoupled from the editor and from
engine startup. Reach for them when the subject is a plain `F`-struct, an algorithm or a
parser; reach for Automation when the subject needs a world, actors or assets. Choosing the
wrong framework produces either a test that cannot run in CI or a "unit test" that boots an
engine.

## Measuring a frame

- `stat unit` splits frame time into game, draw and GPU — always the first command, because
  it decides which of the other tools is relevant.
- `stat game`, `stat collision` and the other stat groups attribute game-thread cost.
- Unreal Insights is the profiler for a timeline capture; the legacy stat profiler is
  superseded by it. Capture the same scene before and after a change and compare, rather
  than asserting an improvement.
- The Gameplay Debugger inspects live gameplay state (AI, perception, abilities) on a
  selected actor, which is usually faster than adding logging.

## Editor automation from an agent

Epic ships an official MCP server for Unreal Editor that exposes the editor's toolsets —
actors, Blueprints, materials, Niagara, Sequencer, widgets, GAS, automation testing — through
meta-tools, plus a skill format for in-editor agent instructions. When a task genuinely
requires driving the editor (creating assets, wiring Blueprints, running in-editor
automation), that server is the sanctioned path; without it, an agent cannot manipulate
`.uasset` content and should say so rather than describe edits it cannot make.

## Failure symptom table

| Symptom | Cause to check first |
|---|---|
| Unresolved external for an engine type | The module is missing from `Build.cs`, or its plugin is disabled |
| Compiles in the editor, fails to package | A runtime module depends on an editor-only module |
| IDE does not see a new file or module | Project files not regenerated after the `Build.cs` change |
| A constructor default change does nothing | Live Coding does not update existing instances for `.cpp` constructor defaults; change the header |
| Crash on editor shutdown after several Live Coding builds | Cached pointers to reinstanced objects were never updated |
| `StartupModule` reads an uninitialized dependency | Load order inside a `LoadingPhase` is not deterministic; use `LoadModuleChecked` |
| Automation test passes alone, fails in a suite | The test assumes state; tests run out of order and in parallel |
| Packaged build behaves differently from PIE | Cooked content, missing plugin, or editor-only code path |

<!-- sources: epic-ue-docs, epic-ue-skills, gamedev-unreal, kevinpbuckley-ue, unrealxu-ue5 -->
