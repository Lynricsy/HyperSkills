# Unity Editor tooling and the Test Framework

Verified against: Unity 6.3 LTS (6000.3) with `com.unity.test-framework` 1.5.

## Contents

- [Assembly definitions](#assembly-definitions)
- [Editor code placement](#editor-code-placement)
- [Domain reload and static state](#domain-reload-and-static-state)
- [Custom inspectors and property drawers](#custom-inspectors-and-property-drawers)
- [Editor windows](#editor-windows)
- [Asset postprocessors and importers](#asset-postprocessors-and-importers)
- [Edit-mode versus play-mode tests](#edit-mode-versus-play-mode-tests)
- [Writing a test that is worth its runtime](#writing-a-test-that-is-worth-its-runtime)
- [Running tests from the command line](#running-tests-from-the-command-line)
- [What is hard to test, and what to do instead](#what-is-hard-to-test-and-what-to-do-instead)

## Assembly definitions

An `.asmdef` turns a folder into its own assembly. Why it matters beyond tidiness:

- compile time: a change inside one assembly recompiles that assembly and its dependents,
  not all of `Assembly-CSharp`;
- dependency direction becomes enforceable — gameplay cannot accidentally reference Editor
  code;
- `Auto Referenced` off means other assemblies must declare the reference explicitly;
- **platform constraints** are how Editor-only code is excluded from a player build;
- `Define Constraints` gate an assembly on a scripting define (`UNITY_EDITOR`,
  a package's own define, your own).

Test assemblies need `"references": ["UnityEngine.TestRunner", "UnityEditor.TestRunner"]`
and `"optionalUnityReferences": ["TestAssemblies"]` (the Test Runner's "create test
assembly folder" button writes this correctly — hand-writing it is how tests stop being
discovered).

Scripts with no enclosing `.asmdef` land in `Assembly-CSharp` (or
`Assembly-CSharp-Editor` under an `Editor` folder), which references every other assembly
and is referenced by none — so code there cannot be depended on from an `.asmdef`.

## Editor code placement

- Anything using the `UnityEditor` namespace must be excluded from player builds, by living
  under a folder literally named `Editor` or in an `.asmdef` constrained to the Editor
  platform. A `using UnityEditor` in a runtime script breaks the player build with
  "The type or namespace name 'UnityEditor' could not be found".
- `-executeMethod` requires the target script to be in an `Editor` folder. `[official]`
  A CI build script placed at `Assets/CI/BuildScript.cs` is a runtime script; move it to
  `Assets/Editor/CI/` or give it an Editor-only assembly.
- `#if UNITY_EDITOR` inside a runtime script is the escape hatch for a few lines; it is not
  a substitute for placement, because the file still compiles into the player assembly.

## Domain reload and static state

Entering Play mode reloads the scripting domain by default: statics reset, `[RuntimeInitializeOnLoadMethod]`
runs, event subscriptions from the Editor session are dropped. **Enter Play Mode Options**
(Project Settings > Editor) can disable domain reload and/or scene reload to make entering
Play mode near-instant — and then:

- `static` fields keep their values from the previous Play session;
- `static` event subscriptions survive and fire twice;
- `[InitializeOnLoad]` and `[RuntimeInitializeOnLoadMethod]` do not re-run.

Code that assumed a fresh domain breaks in exactly the way that is hardest to attribute.
Reset statics explicitly with `[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]`
so the code works with the option either way. This is also the difference between "works in
the Editor" and "works in the player": a player always starts with a fresh domain.

## Custom inspectors and property drawers

Choose the narrowest tool:

| Need | Tool |
|---|---|
| change how one field type draws, everywhere | `[CustomPropertyDrawer(typeof(T))]` |
| change how one attribute decorates a field | `[CustomPropertyDrawer(typeof(MyAttribute))]` |
| change the whole component's Inspector | `[CustomEditor(typeof(T))] : Editor` |
| decorate without changing layout | `PropertyAttribute` + `DecoratorDrawer` |

Rules that keep custom Inspectors from corrupting data:

- Work through `SerializedObject`/`SerializedProperty`, not through the target object's
  fields. That is what gives you undo, multi-object editing and prefab-override bars for
  free. Direct field assignment bypasses all three and does not mark the asset dirty.
- Bracket changes with `serializedObject.Update()` … `serializedObject.ApplyModifiedProperties()`.
- `[CanEditMultipleObjects]` on the editor, or selecting two objects shows nothing.
- A `PropertyDrawer` must respect the `position` rect it is handed and report its height
  through `GetPropertyHeight`, or neighbouring fields overlap.
- UI Toolkit (`CreateInspectorGUI` returning a `VisualElement`) is the recommended path for
  new Editor UI; IMGUI (`OnInspectorGUI`) remains for parity with older code.

`OnGUI`/`OnInspectorGUI` run several times per frame (layout and repaint passes). Any
allocation or `Find` in there is multiplied accordingly.

## Editor windows

```csharp
public class LevelAuditWindow : EditorWindow
{
    [MenuItem("Tools/Level Audit")]
    private static void Open() => GetWindow<LevelAuditWindow>("Level Audit");

    private void CreateGUI() { /* build a VisualElement tree here */ }
}
```

- `EditorWindow` state does not survive a domain reload unless the fields are serialized;
  mark them `[SerializeField]` and treat `OnEnable` as "may run again at any time".
- Long operations need `EditorUtility.DisplayProgressBar` plus a `try`/`finally` with
  `ClearProgressBar`, or a cancelled operation leaves the Editor with a stuck bar.
- Batch asset edits inside `AssetDatabase.StartAssetEditing()`/`StopAssetEditing()` in a
  `try`/`finally`; without it every single change triggers an import.
- Destructive tools follow plan → validate → execute: produce a list of intended changes,
  show it, then apply. An Editor script that mutates 500 prefabs with no preview and no
  undo group is not recoverable.

## Asset postprocessors and importers

- `AssetPostprocessor` (`OnPreprocessTexture`, `OnPostprocessModel`, …) enforces import
  settings project-wide. This is how you make "all UI sprites have mipmaps off" true rather
  than aspirational.
- A postprocessor changing settings must also handle the already-imported case — add a
  menu item that reimports the affected folder, or existing assets keep their old settings
  forever.
- `ScriptedImporter` is for a custom file format; do not parse custom files at runtime from
  `StreamingAssets` when an importer can produce a real asset at build time.

## Edit-mode versus play-mode tests

| | Edit mode | Play mode |
|---|---|---|
| Runs in | the Editor, no game loop | a running player loop (Editor or a built player) |
| Speed | milliseconds | seconds, plus domain reload |
| Can use | `UnityEditor` APIs, `AssetDatabase` | scene loading, physics steps, coroutines |
| Frame-advancing test | `[UnityTest]` works but there is no frame loop for `yield return null` | `[UnityTest]` + `yield return null` advances a real frame |

Put pure logic — damage formulas, inventory rules, save serialization, state machines — in
edit-mode tests in an assembly that does not reference `UnityEngine` scene APIs. Reserve
play-mode tests for behaviour that genuinely needs the loop: physics settling, animation
events, scene transitions.

`[UnityTest]` returns `IEnumerator` and can yield; `[Test]` cannot. `[UnitySetUp]` /
`[UnityTearDown]` are their yieldable setup counterparts.

## Writing a test that is worth its runtime

- Test an observable contract, not the wiring. "The component has a serialized field" is
  not a test; "damage below armour threshold deals zero" is.
- Construct objects with `new GameObject().AddComponent<T>()` in `SetUp` and `Object.DestroyImmediate`
  them in `TearDown`; a leaked test object pollutes later tests in the same run.
- Physics needs steps, not time: in a play-mode test `yield return new WaitForFixedUpdate()`
  a known number of times rather than `WaitForSeconds`, so the test does not depend on frame
  rate.
- `LogAssert.Expect(LogType.Error, ...)` when the code under test is supposed to log an
  error; otherwise the Test Framework fails the test on any logged error — which is a
  feature, not a nuisance.
- Never assert on `Time.time` or on frame counts; assert on state.

## Running tests from the command line

Unity Test Framework adds arguments to the Editor's own set `[official]`:

```bash
Unity -batchmode -nographics -logFile - \
  -projectPath . \
  -runTests -testPlatform EditMode \
  -assemblyNames "MyGame.Tests" \
  -testResults results.xml
```

- `-testPlatform` accepts `EditMode`, `PlayMode`, or any `BuildTarget` value to run
  play-mode tests on a built player. Omitting it runs **edit-mode** tests.
- **`-quit` is not supported while tests are running.** With `-runTests` it makes the Editor
  quit before in-progress tests complete. Leave it out.
- There is **no defined exit code contract** for individual Unity components under test:
  parse the NUnit XML from `-testResults` and decide the job's outcome from it. Treating the
  process exit code as the test verdict is unreliable by documentation.
- `-testFilter` and `-testCategory` accept semicolon lists or regexes, and support negation
  by prefixing the value with an exclamation mark. `-repeat` re-runs passing tests to catch
  flakiness; `-retry` re-runs failing ones and is a way to hide it.
- `-playerHeartbeatTimeout` (default 10 minutes) is what a hung play-mode-on-player run
  waits for before failing.
- `-runSynchronously` runs everything in one Editor update; edit-mode only, and it filters
  out `[UnityTest]` and anything with `[UnitySetUp]`/`[UnityTearDown]`.

## What is hard to test, and what to do instead

Rendering output, shader correctness, input feel and UI layout are not economically
unit-testable. Cover them with:

- a small set of play-mode smoke tests that load each scene and assert no exception and a
  non-null critical reference;
- a deliberate visual-regression pass (screenshot comparison at a fixed resolution) only
  where a visual change is a release blocker;
- manual verification with the Frame Debugger and Profiler, reported with the capture
  rather than asserted in CI.

Methodology for deciding what to test at all belongs to the `test-driven-development`
skill; browser-based end-to-end testing belongs to `web-testing`.

<!-- sources: nicewolf-unity, unity-official-skills, unity-docs -->
