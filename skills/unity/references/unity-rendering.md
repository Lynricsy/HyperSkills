# Unity rendering: URP, batching and materials

Verified against: Unity 6.3 LTS (6000.3) with URP 17.x; facts checked on the Unity 6.6
manual where noted.

## Contents

- [Pick the counter that matters](#pick-the-counter-that-matters)
- [The SRP Batcher](#the-srp-batcher)
- [Compatibility, object by object](#compatibility-object-by-object)
- [MaterialPropertyBlock](#materialpropertyblock)
- [material versus sharedMaterial](#material-versus-sharedmaterial)
- [GPU Resident Drawer](#gpu-resident-drawer)
- [The other batching paths](#the-other-batching-paths)
- [Shaders and pipeline compatibility](#shaders-and-pipeline-compatibility)
- [URP asset and renderer structure](#urp-asset-and-renderer-structure)
- [Render Graph and Scriptable Renderer Features](#render-graph-and-scriptable-renderer-features)
- [Migrating from the Built-in Render Pipeline](#migrating-from-the-built-in-render-pipeline)
- [A diagnosis order that works](#a-diagnosis-order-that-works)

## Pick the counter that matters

The Frame Debugger and the Rendering module report several counters; they mean different
things and only one of them is usually the bottleneck.

- **Draw calls / Draw Mesh** — how many meshes were submitted.
- **SetPass calls** — how many times the render state (shader, material data, keywords) was
  reconfigured. This is the expensive one on the CPU.
- **Batches** and **Saved by batching** — what static/dynamic batching merged.
- **SRP Batcher batches** — how many SRP batches were formed.

A capture where SetPass ≈ draw calls means essentially nothing batched: every object forced
a state change. That is a content problem (per-object state), never a switch you forgot.

## The SRP Batcher

The SRP Batcher does **not** reduce the number of draw calls. It reduces render-state
changes between them, by keeping material constant buffers resident in GPU memory and
updating only the per-object properties through a dedicated code path. `[official]`

Two consequences people get backwards:

- It batches by **shader variant**, not by material. You may use as many different
  materials as you like as long as they share the shader variant; what costs you is variant
  count (keywords, shader features, multi-compile permutations).
- It is available in URP, HDRP and custom SRPs, and **not** in the Built-in Render
  Pipeline. `[official]`

So "merge these 40 materials into 4" is usually the wrong optimization under URP, while
"stop generating 40 shader variants" is the right one.

## Compatibility, object by object

A GameObject uses the SRP Batcher fast path only if all of the following hold `[official]`:

- it has a mesh or skinned mesh (a particle system does not qualify);
- it does **not** use a `MaterialPropertyBlock`;
- its shader is compatible.

A shader is compatible when:

- all built-in engine properties (`unity_ObjectToWorld`, `unity_SHAr`, …) are declared in a
  single constant buffer named **`UnityPerDraw`**;
- all material properties are declared in a single constant buffer named
  **`UnityPerMaterial`**.

Every lit and unlit URP and HDRP shader satisfies this except the particle variants. A
hand-written or heavily edited shader usually does not. The shader Inspector shows the
compatibility status, and the Frame Debugger names the reason per node — read that before
theorising.

When fixing a custom shader, the `UnityPerMaterial` layout must be **identical in every
pass**, including `ShadowCaster` and `DepthOnly`. One pass with a different layout
disqualifies the shader as a whole.

## MaterialPropertyBlock

An MPB overrides per-renderer constants outside the batcher's model, so a renderer carrying
one is SRP-Batcher-incompatible **by definition** `[official]`, and is also excluded from
the GPU Resident Drawer. It is not a batching optimization under an SRP — it is an opt-out.

Two further costs when it appears in `Update`: `new MaterialPropertyBlock()` allocates, and
`SetPropertyBlock` is a per-renderer call. Four hundred crates tinting themselves each
frame is 400 allocations plus 400 state overrides.

What to use instead, in order of preference:

1. Bake the variation into mesh data (vertex colour, UV2) and read it in the shader —
   zero per-frame CPU cost, one material.
2. Quantise to a small set of shared materials or material variants. Material count is not
   the batching lever (see above).
3. If the value genuinely must vary per instance every frame, move to GPU instancing with
   instanced shader properties. That path accepts MPBs, but it is mutually exclusive with
   the SRP Batcher for those renderers — choose one deliberately.

## material versus sharedMaterial

`renderer.material` **instantiates a copy** of the material for that renderer the first
time it is accessed, and the copy is owned by nobody: it is not destroyed with the scene
and shows up as a leak in the Memory Profiler. `[official]`

- `sharedMaterial` — edits the asset. Affects every user, and in the Editor it dirties the
  asset on disk. Correct for a global change.
- `material` — a per-renderer instance. Correct only when you intend one, and then you own
  `Destroy(renderer.material)` in `OnDestroy`.
- a **material variant** — an asset that overrides specific properties of a parent
  material. Correct for a permanent authored difference, with no runtime cost.

Note that many material instances do not by themselves break SRP batching (same shader
variant still batches). The reason to avoid `renderer.material` is memory and leaked
assets, not batch count.

## GPU Resident Drawer

The GPU Resident Drawer uses the `BatchRendererGroup` API to draw GameObjects with GPU
instancing. Its prerequisites are strict and failures are **silent** — ineligible objects
just fall back with no warning and no counter change. `[official]`

Project/pipeline prerequisites:

- a render pipeline asset whose renderers all use the **Forward+ or Deferred+** rendering
  path (plain Forward does not qualify);
- Project Settings > Graphics > Shader Stripping > **BatchRendererGroup Variants** set to
  `Keep All`;
- SRP Batcher enabled on the URP asset;
- **GPU Resident Drawer** set to `Instanced Drawing` on the URP asset;
- a graphics API with compute-shader support — never OpenGL ES, and not visionOS;
- Realtime Global Illumination with Enlighten disabled.

Per-renderer eligibility — a Mesh Renderer that:

- does not use *Use Proxy Volume* and does not set *Anchor Override* in its Light Probes
  setting;
- has **no MaterialPropertyBlock**;
- has default `sortingLayerID` / `sortingOrder`;
- uses materials that support `BatchRendererGroup`, at most 128 of them;
- is not on a GameObject with a Text Mesh component;
- is **not** on a GameObject whose MonoBehaviours implement `OnWillRenderObject`,
  `OnBecameVisible` or `OnBecameInvisible`;
- is in the hierarchy of Animation/Animator components.

That third-from-last item is the one that catches teams: a visibility callback used for
audio or AI culling silently removes the renderer from the drawer. Note it is the
*visibility* callbacks that exclude, and `OnRenderObject` is not on the list — the
intuitive guess is backwards.

Costs of enabling it: build times grow because all `BatchRendererGroup` shader variants are
compiled, and Probe Atlas Blending becomes the default with Forward+/Deferred+. LOD Group
animated cross-fading degrades to static distance cross-fading, and
`Light.shadowMatrixOverride` stops affecting shadow-caster culling.

## The other batching paths

- **Static batching** merges meshes of Static-flagged objects sharing a material. It trades
  memory (the merged mesh is stored in the build) for fewer draw calls, and it defeats
  per-object culling for the merged group. It does not fix per-object state changes.
- **Dynamic batching** applies to small meshes only and costs CPU to transform vertices
  every frame; under URP it is off by default and should stay off.
- **GPU instancing** (`Enable GPU Instancing` on the material) draws many copies of one
  mesh+material in one call. It is the right answer for hundreds of identical props, and it
  accepts per-instance properties.

These are alternatives to, not additions on top of, the SRP Batcher for a given renderer.
Turning several of them on at once and re-measuring gives you no attribution.

## Shaders and pipeline compatibility

A Built-in Render Pipeline shader (`Standard`, `Standard (Specular setup)`,
`Legacy Shaders/*`) does not compile against URP and the object renders **magenta** — the
error shader. There is no runtime fallback. `[official]` Fix by running
Window > Rendering > Render Pipeline Converter (Built-in to URP Material Upgrade) or by
reassigning `Universal Render Pipeline/Lit` / `.../Unlit` and re-authoring the properties.

Custom BiRP shaders must be ported: the include paths, lighting functions and
`CGPROGRAM`/`HLSLPROGRAM` conventions all differ. Shader Graph targets a specific pipeline
and needs its Target changed, not just a reimport.

## URP asset and renderer structure

- The active pipeline comes from **Project Settings > Graphics** (default) and per-level
  overrides in **Quality**. It is not a per-scene setting; a scene that "looks right in one
  project" is reading a different URP asset.
- One URP asset holds shadow, lighting and post-processing budgets and a **Renderer List**.
- A `UniversalRendererData` in that list sets the Rendering Path (Forward, Forward+,
  Deferred, Deferred+), the depth/opaque texture toggles and the Renderer Features.
- Requesting the camera's colour or depth texture in a shader requires the corresponding
  *Opaque Texture* / *Depth Texture* toggle; without it the sample silently reads garbage.
- Post processing is authored with **Volumes** (a Global Volume plus local volumes with
  colliders), not with per-camera components. A camera must have Post Processing enabled to
  see any of it.

## Render Graph and Scriptable Renderer Features

URP compiles its passes through Render Graph. Consequences for custom passes:

- `ScriptableRenderPass` declares its resources through the Render Graph API; the older
  `Execute(ScriptableRenderContext, ref RenderingData)` form is the compatibility path and
  is being retired.
- Resources must be declared as reads and writes so the graph can cull and alias them. A
  pass that grabs a texture outside the declared graph either gets culled away or breaks
  frame-debugger attribution.
- `OnRenderImage`, `Camera.main.RenderWithShader` and other BiRP image-effect hooks do not
  run under URP at all. An unconverted post effect is silent, not broken-looking.

## Migrating from the Built-in Render Pipeline

1. Install URP, create one URP asset per quality level, assign in Graphics and Quality.
2. Convert materials with the Render Pipeline Converter; hand-fix the remaining magenta.
3. Port custom shaders and Shader Graphs (change the Target; re-check per-pass
   `UnityPerMaterial` layout).
4. Replace image effects with Volume components and Renderer Features.
5. Re-author lighting: URP has its own additional-light limits, shadow cascade settings and
   per-quality light budgets, so an unconverted scene is usually *dim or blown out* before
   it is obviously broken.
6. Verify with a Frame Debugger capture showing URP passes and a non-zero SRP Batcher batch
   count.

## A diagnosis order that works

1. Frame Debugger: is SetPass ≈ draw calls? If so, stop looking at global switches.
2. Click the worst node and read the SRP Batcher reason string. It names the cause.
3. Fix correctness first (magenta materials), then content-level incompatibility (MPBs,
   shader CBUFFERs), then revisit any global switch.
4. Change one thing, re-capture, and attribute the delta. Two switches at once gives you
   no information.

<!-- sources: nicewolf-unity, unity-official-skills, unity-docs, unity-graphics -->
