---
name: unity
description: "Develops Unity games with C#, engine APIs, rendering and asset workflows."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# unity

## Scope

Covers Unity 6 game and tool development: the MonoBehaviour lifecycle and event-execution
order, Unity's own serializer and the prefab/ScriptableObject data model, coroutines and
`Awaitable`, per-frame allocation and the Profiler workflow, the Universal Render Pipeline
(SRP Batcher, GPU Resident Drawer, Render Graph, materials and shader compatibility),
runtime UI in uGUI and UI Toolkit, built-in 3D physics (fixed timestep, colliders,
triggers, layers, queries), assets and memory (Addressables, sprite atlases, texture
compression), Editor extension code and domain reload, the DOTS/ECS boundary, the Unity
Test Framework, and batch-mode player builds with IL2CPP, managed stripping, licensing and
exit codes in CI.

Targets **Unity 6 (6000.x)**. When a project does not state a version, assume
**Unity 6.3 LTS (6000.3)** — the current LTS; **Unity 6.6 (6000.6)** is the current Update
release. Rules that differ across those versions carry an explicit gate. Unity 2022 LTS and
earlier are out of scope; so is the Built-in Render Pipeline except where a project is
migrating off it.

Not covered: C# language features, the .NET SDK, MSBuild, NuGet, ASP.NET Core and general
.NET engineering belong to the `csharp-dotnet` skill; Unity's scripting conventions,
serialization, lifecycle, coroutines, Editor extensions, URP, UI Toolkit, DOTS and the
Unity build pipeline belong here. Godot and Unreal are separate skills (`godot`, `unreal`)
and nothing here transfers to them. The visual design of game UI — hierarchy, type, colour,
motion — belongs to `frontend-design`; this skill covers the implementation.
Test-driven development as a practice belongs to `test-driven-development`; browser E2E
belongs to `web-testing`. Also out of scope: Unity Gaming Services products (Cloud Save,
Economy, LevelPlay, Vivox, IAP), art authoring in DCC tools, and store submission.

Paths below are relative to this skill's directory.

## Read first

`references/unity-serialization.md` before writing or reviewing any `MonoBehaviour` or
`ScriptableObject` field. Unity does not use .NET serialization: a field can compile, look
right, and simply never be stored, with no error anywhere. "The Inspector is empty" and
"the constructor's values are gone" are the same bug class, and it is the single most
common source of wasted debugging on this engine.

## Core rules

1. Unity serializes **fields**, never properties. A field must be public or carry
   `[SerializeField]`, and must not be `static`, `const` or `readonly` — on those three
   the attribute is legal and silently ineffective. On a property it is not legal at all:
   `SerializeField` is declared `[AttributeUsage(AttributeTargets.Field)]`, so
   `[SerializeField] public int Ammo { get; set; }` is CS0592 and the whole file fails to
   compile. Give the property an explicit backing field. `[verified]`
2. A plain class or struct used as a serialized field type needs `[System.Serializable]`,
   and the attribute is **not inherited** — apply it to every class in the hierarchy. A
   missing one yields an empty Inspector row, not a warning. `[official]`
3. Jagged arrays, multidimensional arrays and directly nested containers are never
   serialized. `Dictionary<TKey, TValue>` behind `[SerializeField]` is supported **only
   from Unity 6.6**; on 6.3 LTS it is a multilevel type and is dropped. Wrap the nested
   type in a `[Serializable]` class, or implement `ISerializationCallbackReceiver`.
   `[verified]`
4. An interface-typed or polymorphic field needs `[SerializeReference]`. Without it Unity
   serializes only the declared base type's fields and reconstructs the **base** class on
   load, so a derived instance silently degrades. `[official]`
5. A `MonoBehaviour`/`ScriptableObject` constructor and its field initializers do not
   establish runtime state: Unity constructs the object and then overwrites every
   serialized field with the deserialized value. Initialize in `Awake`/`OnEnable`
   (`Reset`/`OnValidate` for authoring-time defaults). Engine APIs such as `Time.time` are
   not valid from a constructor at all. `[official]`
6. Renaming a serialized field discards every stored value in every scene, prefab and
   asset that referenced it. `[FormerlySerializedAs("oldName")]` is the only recovery, and
   it must be added in the same change as the rename. `[official]`
7. `Awake` runs once per instance on load, `OnEnable` on every enable, `Start` before the
   first `Update` — and order *across* objects is undefined unless set explicitly
   (`[DefaultExecutionOrder]` or Script Execution Order). Self-setup goes in `Awake`,
   cross-object wiring in `Start`. `[official]`
8. Rigidbody motion, forces and `linearVelocity` writes belong in `FixedUpdate`; input
   polling and camera work belong in `Update`/`LateUpdate`. Driving a Rigidbody from
   `Update` fights the solver and makes behaviour timestep-dependent. `[official]`
9. In Unity 6 `Rigidbody.velocity`, `.drag` and `.angularDrag` are `[Obsolete]` in favour
   of `linearVelocity`, `linearDamping` and `angularDamping` — but they still exist and
   still compile, with `(UnityUpgradable)` so the API Updater rewrites them. They are
   warnings, not errors; do not budget an upgrade as if the code were broken. `[verified]`
10. Collision messages require at least one **dynamic** (non-kinematic Rigidbody) collider
    in the pair. Static↔static, static↔kinematic and kinematic↔kinematic pairs send
    nothing. Trigger messages need either side to be a dynamic or kinematic trigger; a
    static trigger only reports against dynamic or kinematic colliders. A callback that
    "never fires" is almost always this table, not a code bug. `[official]`
11. `Object.FindObjectsOfType`/`FindObjectOfType` are `[Obsolete]` across Unity 6; use
    `FindObjectsByType`/`FindAnyObjectByType`. From **Unity 6.4** the `FindObjectsSortMode`
    enum, every overload taking it, and `FindFirstObjectByType` are *also* `[Obsolete]`
    because instance-ID ordering is being replaced by `EntityId`. Code written to the 6.3
    advice grows hundreds of warnings on upgrade. `[verified]`
12. Nothing that searches the scene graph belongs in a per-frame path: `GameObject.Find`,
    the `FindObjectsByType` family, `Camera.main` (a tag lookup) and `GetComponent` all
    cost per call. Cache them in `Awake` into fields. `[official]`
13. Compare tags with `CompareTag`, never `gameObject.tag == "x"`: the `tag` getter
    returns a managed string, so the comparison allocates every time it runs. `[official]`
14. Per-frame managed allocation is the GC sawtooth. String concatenation and
    interpolation (including inside `Debug.Log`, whose arguments are evaluated before the
    call), `Physics.RaycastAll`/`OverlapSphere`, `GetComponents<T>()` and LINQ all allocate
    on every call. Use the `NonAlloc`/`List<T>` overloads and preallocated buffers, and
    guard log calls behind a conditional. `[official]`
15. `StartCoroutine` from inside `Update` starts a *new* coroutine every frame. Coroutines
    survive `enabled = false` but are killed by deactivating the GameObject or destroying
    the component, so a re-arm in `OnEnable` is not equivalent to a guard. `[verified]`
16. An `Awaitable` may be awaited **once**; it is pooled and re-awaiting is undefined
    behaviour. It captures neither `ExecutionContext` nor `SynchronizationContext`, and
    continuations run synchronously on whatever thread raised completion. `[verified]`
17. Touch `destroyCancellationToken` at least once while the component is alive (in
    `Awake`/`Start`). The getter throws `MissingReferenceException` if it is first read
    after the object is destroyed — exactly where cancellation code tends to sit.
    `[verified]`
18. `renderer.material` instantiates a **copy** of the material for that renderer and
    leaks one material instance per renderer. Use `sharedMaterial` for shared edits, a
    material variant for a permanent difference, and `SetPropertyBlock` only with rule 19
    in mind. `[official]`
19. A renderer carrying a `MaterialPropertyBlock` is SRP-Batcher-incompatible by
    definition, and is also excluded from the GPU Resident Drawer. MPB is not a batching
    optimization in URP — it disables the batcher for that object. `[official]`
20. The SRP Batcher reduces render-state changes between draw calls, not the number of
    draw calls, and it batches by **shader variant** rather than by material. A custom
    shader qualifies only if engine properties live in a `UnityPerDraw` constant buffer and
    material properties in a `UnityPerMaterial` one. Fewer materials with the same shader
    is not the lever; fewer shader variants is. `[official]`
21. The GPU Resident Drawer needs a URP renderer on **Forward+ or Deferred+**, Project
    Settings > Graphics > Shader Stripping > *BatchRendererGroup Variants* set to
    `Keep All`, compute-shader support (never OpenGL ES), and per-renderer eligibility:
    no MaterialPropertyBlock, no `OnWillRenderObject`/`OnBecameVisible`/`OnBecameInvisible`
    MonoBehaviour, ≤128 materials. Ineligible objects fall back silently — no warning, no
    counter change. `[official]`
22. A Built-in Render Pipeline shader (`Standard`, `Legacy Shaders/*`) renders magenta
    under URP. Fix it with the Render Pipeline Converter or by reassigning a URP shader;
    there is no runtime fallback. `[official]`
23. For runtime UI Unity recommends **uGUI**, with UI Toolkit as the alternative; for
    Editor UI it recommends **UI Toolkit**, with IMGUI as the alternative. This is
    unchanged from 6.3 LTS through 6.6. Reach for UI Toolkit when the project has a lot of
    UI, many resolutions, world-space or shader-driven UI; stay on uGUI when you need
    in-scene authoring or Inspector-serialized events, which UI Toolkit does not have.
    uGUI is not legacy — IMGUI is. `[official]`
24. Custom `VisualElement` types register with `[UxmlElement]` and `[UxmlAttribute]`;
    `UxmlFactory` and `UxmlTraits` are `[Obsolete]` and slated for removal. `[verified]`
25. `BuildPipeline.BuildPlayer` returns a `BuildReport` and does not throw on failure.
    Inspect `summary.result` and call `EditorApplication.Exit(nonZero)` yourself — with
    `-quit` alone the Editor exits 0 on a failed build, which is how a CI job goes green
    while shipping nothing. `-executeMethod` also requires the script to live under an
    `Editor` folder or an Editor-only assembly. `[official]`

## Workflows

### implement

- [ ] Read `ProjectSettings/ProjectVersion.txt` (the Unity version every gated rule
      depends on), `Packages/manifest.json` (is URP, Input System, Addressables, Entities
      in use?) and the nearest `.asmdef`. Guessing any of the three invalidates the rest.
- [ ] Read one existing component in the same folder and adopt its conventions:
      `[SerializeField] private` vs public fields, event style, namespace, assembly.
- [ ] Model the serialized data first against `references/unity-serialization.md`, then
      write behaviour. Retrofitting serialization means re-authoring assets by hand.
- [ ] Put work in the right callback per rules 7–8, cache every lookup in `Awake`
      (rule 12), and keep per-frame paths allocation-free (rules 13–14).
- [ ] Add the component to a scene or prefab and set its fields, or state explicitly that
      the wiring is left to the user — a script nobody references does nothing.
- [ ] **Gate:** the project compiles with no new warnings (obsolete-member warnings
      included), and Play mode reaches the changed code path with no Console exception.

### review

- [ ] Establish the Unity version and active render pipeline before judging anything;
      rules 3, 9, 11 and 21 change answer with the version.
- [ ] Walk the Core rules in order — they are ordered by how often each is the real defect.
- [ ] Check every serialized field against rule 1–6, then every per-frame method body
      against rules 12–15. These two passes find most of what a Unity review finds.
- [ ] Check lifetime: subscriptions and coroutines started in `OnEnable` and released in
      `OnDisable`, `Destroy` on instantiated materials and meshes, `Addressables.Release`
      on every load.
- [ ] Report only findings with a reachable trigger and a concrete impact. A text match is
      a lead, never a finding.
- [ ] **Gate:** every finding carries `path:line`, the trigger, the impact and a fix, and
      any engine claim names the Unity version it holds for.

### optimize-frame-time

- [ ] Measure before changing anything: Profiler (CPU + Memory modules) for allocation and
      main-thread cost, Frame Debugger for SetPass/batch counts. Name the bottleneck as
      CPU-bound, GPU-bound or GC-bound.
- [ ] For GC: sort the Profiler's `GC.Alloc` by call site and fix the top few per
      `references/unity-performance.md`. One allocation in one `Update` on 400 objects is
      400 per frame.
- [ ] For draw submission: read `references/unity-rendering.md` and check SRP Batcher
      compatibility object by object in the Frame Debugger before trying any batching
      switch. Rules 19–21 explain most "the toggle did nothing" reports.
- [ ] For memory: check texture and mesh footprints per `references/unity-assets-and-memory.md`
      — import settings usually dominate script allocation on mobile.
- [ ] Re-measure on the target device, not in the Editor. Editor overhead and the Editor's
      non-stripped code make Editor numbers unusable as a baseline.
- [ ] **Gate:** a before/after number from the same capture method on the same device, plus
      the Profiler marker or Frame Debugger row that proves the cause was the one fixed.

### build-and-ship

- [ ] Confirm the scene list (only listed, enabled scenes ship; index 0 boots), the
      scripting backend (Mono vs IL2CPP), the managed stripping level and any `link.xml`.
- [ ] Build content before the player when Addressables are used — a player build does not
      rebuild Addressables groups, and a stale catalog ships silently.
- [ ] Script the build per rule 25 and `references/unity-build.md`: check
      `BuildReport.summary.result`, exit with a real code, `-logFile -` to stdout.
- [ ] Run the built player on the target platform. A build that returned `Succeeded` can
      still crash on load from stripping or a missing native dependency.
- [ ] **Gate:** the CI job fails on a deliberately broken build (verify it once), and the
      installed player reaches the first interactive screen on a real device.

### migrate-birp-to-urp

- [ ] Install URP, create a URP asset per quality level, and assign it in Graphics and
      Quality settings — the pipeline is selected in settings, not per scene.
- [ ] Run the Render Pipeline Converter for materials first; hand-fix anything still
      magenta (rule 22) and every custom shader (rule 20).
- [ ] Replace image effects: BiRP `OnRenderImage` scripts do not run under URP. Post
      processing moves to Volumes, and custom passes become Scriptable Renderer Features.
- [ ] Re-check lighting: URP has its own light limits, shadow cascades and per-pipeline
      light settings, so an unconverted scene usually looks wrong before it looks broken.
- [ ] **Gate:** no magenta material in the scene, and a Frame Debugger capture showing the
      URP render passes plus an SRP Batcher batch count above zero.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Serialization and data model | Any `[SerializeField]`, empty Inspector, lost values, ScriptableObject or prefab data | `references/unity-serialization.md` |
| Scripting and lifecycle | Writing a MonoBehaviour, callback choice, execution order, coroutines vs `Awaitable`, events | `references/unity-scripting.md` |
| Performance and GC | GC sawtooth, hot `Update`, Profiler workflow, pooling, obsolete `Find*` APIs | `references/unity-performance.md` |
| Rendering and URP | SetPass/batch counts, SRP Batcher, GPU Resident Drawer, materials, shaders, Render Graph, BiRP→URP | `references/unity-rendering.md` |
| Runtime and Editor UI | Choosing uGUI vs UI Toolkit, UXML/USS, canvas rebuild cost, TextMeshPro | `references/unity-ui.md` |
| Physics | `FixedUpdate` motion, colliders, triggers, layers, queries, tunnelling, character movement | `references/unity-physics.md` |
| Assets and memory | Addressables, sprite atlases, texture compression, `Resources`, load/release lifetime | `references/unity-assets-and-memory.md` |
| Build and CI | Build profiles, IL2CPP, stripping, `link.xml`, batch mode, licensing, exit codes | `references/unity-build.md` |
| Editor tooling and tests | Custom inspectors, property drawers, editor windows, `.asmdef`, domain reload, Unity Test Framework | `references/unity-editor-and-testing.md` |
| DOTS and ECS | Entities/Jobs/Burst, whether DOTS is warranted at all, ECB, baking | `references/unity-dots.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
Assets/Scripts/UI/EnemyHudController.cs
  L19 blocking - scoreLabel.text is rebuilt from string concatenation every frame; with
       the interpolated Debug.Log on L44 this is the GC sawtooth in the capture.
       before: scoreLabel.text = "Score: " + score + " / " + maxScore;
       after:  cache the last value, assign only on change, and build with a StringBuilder
  L26 blocking - GameObject.Find("Player") searches the whole scene graph per frame.
       Cache in Awake; a respawn should push the new reference in, not be polled for.
  L30 important - FindObjectsOfType<Enemy>() is obsolete in Unity 6 and becomes a second
       warning class on 6.4+. Use FindObjectsByType<Enemy>() and keep the result.
  ✓ Time.deltaTime scaling on L52 is correct.

Assets/Scripts/Loot/LootTable.cs
  L26 blocking - [SerializeField] Dictionary is dropped on 6000.3 (supported only from
       6.6); the table is empty in the Inspector for that reason, not a UI bug.
```

Severities: `blocking` (does not compile, throws, loses authored data, ships a broken
player, or is the measured bottleneck), `important` (obsolete API, leaked object or
subscription, per-frame allocation, silently ineligible for a batching path), `minor`
(naming, ordering, dead code). End with a one-line verdict: ship, ship after blocking
fixes, or rework. Name the Unity version every engine claim holds for, and list checks you
could not run separately from findings — never describe an unrun Play-mode or device check
as passed.

## Environment

The Unity Editor supplies the compiler, package manager, build pipeline and test runner;
there is no supported way to build a Unity player without it. `Unity` below is the Editor
binary from Unity Hub — `/opt/unity/Editor/Unity` on Linux,
`/Applications/Unity/Hub/Editor/<ver>/Unity.app/Contents/MacOS/Unity` on macOS, and
`Unity.exe` under the Hub's `Editor/<ver>/Editor` directory on Windows.

```bash
Unity -version                                    # Editor version actually on PATH
Unity -batchmode -nographics -logFile - \
  -projectPath . -executeMethod CI.BuildScript.Build   # scripted build; method exits
Unity -batchmode -nographics -logFile - \
  -projectPath . -runTests -testPlatform EditMode \
  -testResults results.xml                        # no -quit: unsupported during tests
Unity -batchmode -logFile - -projectPath . -serial "$UNITY_SERIAL" -quit   # activate
Unity -batchmode -logFile - -returnlicense -quit  # release the seat before the runner dies
```

Add `-accept-apiupdate` to any batch-mode run or the API Updater is skipped and its
omissions surface as unexplained compiler errors. `-nographics` also turns off output logs
unless `-logFile` is given, and cannot bake global illumination.

When no Editor is installed, say so and reason only from the project files; do not report a
build, a Play-mode result or a Profiler number you did not produce.
