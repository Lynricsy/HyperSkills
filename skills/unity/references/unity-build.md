# Unity builds: player pipeline, batch mode and CI

Verified against: Unity 6.3 LTS (6000.3); Editor command-line facts checked on the Unity 6.6
manual.

## Contents

- [What ends up in a player](#what-ends-up-in-a-player)
- [Scripting backend](#scripting-backend)
- [Managed code stripping and link.xml](#managed-code-stripping-and-linkxml)
- [Scripting a build that fails loudly](#scripting-a-build-that-fails-loudly)
- [Editor command-line arguments that matter](#editor-command-line-arguments-that-matter)
- [Licensing on a CI runner](#licensing-on-a-ci-runner)
- [A shell wrapper that propagates failure](#a-shell-wrapper-that-propagates-failure)
- [Addressables content builds](#addressables-content-builds)
- [Build size and build time](#build-size-and-build-time)
- [Verifying the artifact](#verifying-the-artifact)

## What ends up in a player

- **Scenes**: only those listed and enabled in Build Profiles / Build Settings. Index 0 is
  the boot scene. `SceneManager.LoadScene` can only load listed scenes — a scene that works
  in the Editor and 404s in the build is almost always unlisted.
- **Assets**: anything referenced from a listed scene, plus everything under `Resources/`
  (always included, never stripped, loaded eagerly at startup — this is why `Resources/` is
  discouraged), plus Addressables content built separately, plus `StreamingAssets/` copied
  verbatim.
- **Code**: the assemblies produced from `Assets/` and from packages, after managed
  stripping.
- **Build Profiles** (Unity 6) supersede the old per-platform settings screen: each profile
  carries its own scene list, scripting defines and player settings overrides. A CI job that
  ignores profiles and sets `BuildPlayerOptions` by hand gets the *project-level* settings,
  not the profile's.

## Scripting backend

| | Mono | IL2CPP |
|---|---|---|
| Compilation | JIT at runtime | C# → C++ → native, AOT |
| Iteration | fast | slow (a full C++ compile) |
| Runtime speed | lower | higher |
| Reverse engineering | trivial (readable IL) | hard |
| Platform support | desktop | required on iOS, WebGL, consoles, and the usual choice on Android |
| Requires | nothing extra | the platform C++ toolchain (Android NDK, MSVC build tools, Xcode) |

Symptoms that are backend-specific: an IL2CPP build failing on a fresh machine is a missing
C++ toolchain, not a code problem; a `MissingMethodException` or `TypeLoadException` that
only appears in an IL2CPP build is stripping (next section); `System.Reflection.Emit` and
runtime code generation do not work under IL2CPP at all.

## Managed code stripping and link.xml

Stripping levels are Disabled → Minimal → Low → Medium → High. The linker keeps what it can
*see*; reflection, JSON deserialization into a type never constructed in code, and types
resolved by name are all invisible to it.

```xml
<!-- Assets/link.xml -->
<linker>
  <assembly fullname="MyGame.Runtime" preserve="all"/>
  <assembly fullname="Newtonsoft.Json">
    <type fullname="MyGame.Save.SaveFile" preserve="all"/>
  </assembly>
</linker>
```

`[Preserve]` on a type or member is the finer-grained alternative and keeps the annotation
next to the code that needs it. Lowering the global stripping level to fix one type is the
wrong trade: it costs size everywhere. The failure is silent at build time and loud at
runtime, so any project using reflection needs a smoke run of the *stripped* build.

## Scripting a build that fails loudly

`BuildPipeline.BuildPlayer` returns a `BuildReport` and **does not throw** when the build
fails. Ignoring the return value is what makes a CI job green while shipping nothing.
`[official]`

```csharp
// Assets/Editor/CI/BuildScript.cs  — must be under an Editor folder (or an Editor-only asmdef)
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace CI
{
    public static class BuildScript
    {
        // Exit codes: 0 ok, 1 build failed/cancelled, 2 unexpected exception, 3 bad setup.
        public static void BuildAndroid()
        {
            if (!EditorUserBuildSettings.SwitchActiveBuildTarget(
                    NamedBuildTarget.Android, BuildTarget.Android))
            {
                Debug.LogError("could not switch active build target to Android");
                EditorApplication.Exit(3);
                return;
            }

            var options = new BuildPlayerOptions
            {
                scenes = EditorBuildSettings.scenes.Where(s => s.enabled)
                                            .Select(s => s.path).ToArray(),
                locationPathName = "artifacts/MyGame.apk",
                target = BuildTarget.Android,
                options = BuildOptions.StrictMode,   // no Development/AllowDebugging in a release
            };

            try
            {
                BuildReport report = BuildPipeline.BuildPlayer(options);
                BuildSummary summary = report.summary;

                foreach (BuildStep step in report.steps)
                    foreach (BuildStepMessage m in step.messages)
                        if (m.type is LogType.Error or LogType.Exception)
                            Debug.LogError($"[{step.name}] {m.content}");

                if (summary.result != BuildResult.Succeeded)
                {
                    Debug.LogError($"build {summary.result}: {summary.totalErrors} errors");
                    EditorApplication.Exit(1);
                    return;
                }

                Debug.Log($"build ok: {summary.totalSize} bytes in {summary.totalTime}");
                EditorApplication.Exit(0);
            }
            catch (System.Exception e)
            {
                Debug.LogError(e);
                EditorApplication.Exit(2);
            }
        }
    }
}
```

Four requirements this satisfies that are easy to miss:

1. **The script must live under an `Editor` folder** (or an assembly definition with
   `Editor` as its only platform) for `-executeMethod` to resolve it. `Assets/CI/BuildScript.cs`
   is a runtime script that happens to `using UnityEditor`; it does not compile into the
   player and the method is not found at build time in the way you expect. `[official]`
2. **The method sets the exit code.** Either throw (batch mode exits 1) or call
   `EditorApplication.Exit(nonZero)`. `[official]`
3. **`SwitchActiveBuildTarget` returns `bool`.** A failed switch followed by a build
   produces an artifact for the wrong platform.
4. **`report.steps[].messages` carries the actual error text.** The console in batch mode
   often shows only `Aborting batchmode due to failure`; the useful text is in the report.

## Editor command-line arguments that matter

All of these are from the official Editor command-line reference `[official]`:

| Argument | Behaviour worth knowing |
|---|---|
| `-batchmode` | no dialogs; an unhandled exception makes Unity exit with code 1 |
| `-executeMethod <Ns.Class.Method>` | runs a static method after the project opens; script must be in an `Editor` folder; to signal an error, throw or call `EditorApplication.Exit` |
| `-quit` | quits after the other commands finish. It **can hide error messages**; with `-runTests` it quits before tests complete; with asynchronous code it can hang the process |
| `-logFile -` | streams the Editor log to stdout. A file path leaves CI with nothing to show |
| `-nographics` | no graphics device, for GPU-less runners. **Turns output logs off unless `-logFile` is given**, and cannot bake global illumination |
| `-accept-apiupdate` | without it the API Updater does **not** run in batch mode, which surfaces as unexplained compiler errors |
| `-projectPath <path>` | absolute or relative to the working directory |
| `-buildTarget <name>` | opens the Editor with that active target, avoiding a mid-run switch |
| `-silent-crashes` | suppresses the crash dialog in automated runs |
| `-disable-assembly-updater` | skips the assembly half of the API Updater; the script updater still runs |

The single most common CI defect is `-quit` plus an unchecked build result: the Editor exits
0, the shell sees success, and the artifact is absent.

## Licensing on a CI runner

A headless Editor still needs an activated licence, and it fails before it reaches your
method. `[official]`

- `-serial <key>` activates a serial-based or named-user licence; it **must** be combined
  with `-batchmode`, and Unity recommends `-quit` for the activation invocation
  specifically.
- `-username` / `-password` supply the Unity ID for named-user activation.
- `-returnlicense` releases the seat. Run it in a `trap`/`finally`, or a crashed job leaks
  a seat until it times out.
- Manual activation is the three-step `-createManualActivationFile` → upload →
  `-manualLicenseFile <file.ulf|.xml>` flow, used for offline or air-gapped runners.
- Keep the serial in the CI secret store and pass it through the environment. Never inline
  it in a script that lands in version control.

## A shell wrapper that propagates failure

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${UNITY_SERIAL:?UNITY_SERIAL is not set}"
UNITY=${UNITY:-/opt/unity/Editor/Unity}
PROJECT=$(cd "${1:-.}" && pwd)          # absolute: -projectPath relative to cwd is fragile
ARTIFACT="$PROJECT/artifacts/MyGame.apk"

cleanup() { "$UNITY" -batchmode -nographics -logFile - -returnlicense -quit || true; }
trap cleanup EXIT

"$UNITY" -batchmode -nographics -logFile - -projectPath "$PROJECT" \
         -serial "$UNITY_SERIAL" -quit

set +e
"$UNITY" -batchmode -nographics -accept-apiupdate -logFile - \
         -projectPath "$PROJECT" -buildTarget android \
         -executeMethod CI.BuildScript.BuildAndroid 2>&1 | tee build.log
status=${PIPESTATUS[0]}                  # set -e only inspects the last pipe stage
set -e

[ "$status" -eq 0 ] || { echo "unity exited $status" >&2; exit "$status"; }
[ -f "$ARTIFACT" ]  || { echo "no artifact at $ARTIFACT" >&2; exit 1; }
```

Note `-quit` on the activation call (Unity recommends it there) and its **absence** on the
build call, where the method owns the exit code. `${PIPESTATUS[0]}` is required because
`set -e` only reacts to the final stage of a pipeline, so piping through `tee` swallows the
Editor's status.

Prove the pipeline fails: break a script deliberately once and confirm the job goes red. A
CI build that has never failed has not been shown to detect failure.

## Addressables content builds

- Addressables content is built **separately** from the player
  (Window > Asset Management > Addressables > Build, or
  `AddressableAssetSettings.BuildPlayerContent`). A player build does not rebuild it.
- A stale catalog ships silently and fails at load with a missing-key error. Build content
  before the player in CI, every time.
- Remote content needs the profile's build and load paths pointing at the real CDN for the
  build being made; a profile left on `Local` produces a player that looks for content next
  to itself.
- `Use Existing Build` in Play-mode script means Play mode reads the last content build.
  "It works in the Editor" after an asset change usually means that mode is on.

## Build size and build time

- The Editor log and the build report name the largest assets. Textures dominate almost
  always; see `unity-assets-and-memory.md`.
- Shader variants are the second-biggest contributor and the biggest contributor to build
  *time*. Strip keywords, and be aware that enabling the GPU Resident Drawer forces all
  `BatchRendererGroup` variants to compile.
- The Library folder is a cache, not an output. Preserve it between CI runs (keyed on Unity
  version and platform) or every job re-imports every asset.
- An incremental IL2CPP build is much faster than a clean one; keep the platform build
  cache too.

## Verifying the artifact

A `Succeeded` build report is not a working game. Before calling a build good:

1. install and launch on the target platform, not in the Editor;
2. reach the first interactive screen — stripping and missing native plugins both fail at
   load, after the splash;
3. check the player log for `MissingMethodException`, `TypeLoadException`,
   `DllNotFoundException`, missing-Addressables-key errors;
4. if no device or Editor is available, say so and do not describe the build as verified.

<!-- sources: gamedev-unity, nicewolf-unity, unity-official-skills, unity-docs -->
