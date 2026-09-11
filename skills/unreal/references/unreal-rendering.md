# Rendering and VFX: Lumen, Nanite, Niagara (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]`; nothing
in this file was checked against a running engine, and no numbers here were measured on this
machine.

## Contents

- [What these systems trade](#what-these-systems-trade)
- [Lumen: enabling and its hard rules](#lumen-enabling-and-its-hard-rules)
- [Lumen: the cost knobs](#lumen-the-cost-knobs)
- [Lumen latency](#lumen-latency)
- [Nanite: what it is for](#nanite-what-it-is-for)
- [Nanite: unsupported and limited](#nanite-unsupported-and-limited)
- [Nanite and ray tracing](#nanite-and-ray-tracing)
- [Niagara](#niagara)
- [Review checklist](#review-checklist)

## What these systems trade

Lumen replaces baked lightmaps with real-time global illumination and reflections; Nanite
replaces manual LOD chains with virtualized geometry. Both are defaults for new UE5 projects
and both have categorical limits — material blend modes, light mobility, platform features —
that cannot be tuned away. Diagnosing "the scene is dark" or "my material reverted" starts
with those categories, not with the quality sliders.

## Lumen: enabling and its hard rules

- New projects have Lumen Global Illumination and Reflections on, together with their
  dependencies such as Generate Mesh Distance Fields. A project **converted from UE4 does not
  get Lumen enabled automatically**, deliberately, so the existing lighting path is not
  changed underneath it.
- Enabling Mesh Distance Fields (required for Lumen's Software Ray Tracing) requires an engine
  restart, and it increases build time, memory use and static-mesh disk size.
- **Lights with Mobility set to `Static` are not supported.** Static light contribution lives
  entirely in lightmaps and is disabled when Lumen is on — so a level lit with static lights
  goes dark, and the fix is the light's mobility, not a Lumen setting.
- Sky lighting is solved inside Lumen's Final Gather, including sky shadowing, which is what
  makes interiors genuinely darker than exteriors.
- Emissive materials contribute through the Final Gather at no extra cost, but small, very
  bright emissive areas are the standard source of noise artifacts; they are harder to solve
  than a placed light.
- Lumen Reflections can be used without Lumen GI — useful for a static-lighting project that
  wants better reflections — but standalone Lumen Reflections require Lumen's Hardware Ray
  Tracing mode, which automatically enables hit lighting for reflections.

## Lumen: the cost knobs

| Setting | Trade |
|---|---|
| Use Hardware Ray Tracing when available | Higher quality where the GPU, RHI and OS support it, falling back to Software Ray Tracing otherwise. **Significant scene update cost above roughly 100,000 instances** |
| Ray Lighting Mode (Surface Cache vs Hit Lighting) | Surface Cache is the default and the fast path; Hit Lighting computes lighting at the hit point for higher-quality reflections |
| Software Ray Tracing Mode (Detail vs Global Tracing) | Detail Tracing traces per-mesh distance fields for quality; Global Tracing uses the lower-detail global distance field for speed |
| Final Gather Quality | Less noise, more GPU |
| Max Trace Distance | Too small leaks light into enclosed spaces such as caves; large values cost GPU |
| Lumen Scene Detail / Minimum Detail Size / View Distance | Represent smaller objects and further geometry at proportional GPU cost |
| Surface Cache Resolution scale | Saves GPU memory at a quality cost; defaults to 0.5 when not overridden |
| Max Reflection Bounces | Default is 1 — a single reflection ray with no secondary reflections. More bounces remove black areas in mirrored surfaces and cost accordingly; beyond the post-process maximum requires hardware ray tracing with hit lighting |
| High Quality Translucency Reflections | Mirror-quality front layer only; other layers fall back to glossy radiance-cache reflections. Costs GPU and requires the project setting first |

## Lumen latency

Lumen caches aggressively. Local lighting changes propagate quickly, but a **global** change —
switching off the sun — can take multiple seconds to settle. The Lumen Scene and Final Gather
Lighting Update Speed controls shorten that delay at a GPU cost. A cinematic that cuts
lighting between shots must budget for this rather than treat it as a bug.

## Nanite: what it is for

Nanite virtualizes geometry: level of detail is handled automatically, so meshes no longer
need hand-authored LOD chains. It can be enabled on static meshes and geometry collections,
and on skeletal meshes through their own Nanite settings (Nanite skeletal meshes have no
geometry LODs and use animation LODs instead). Conversion costs processing time per mesh, so a
shared Derived Data Cache matters on a large project.

Nanite-enabled meshes work with static mesh, skeletal mesh, instanced and hierarchical
instanced static mesh, spline mesh, geometry collection, foliage painter and landscape grass
components.

## Nanite: unsupported and limited

- **Materials:** `Opaque` and `Masked` blend modes only. An unsupported material is replaced
  with the default material and a warning in the Output Log — that is the "my material
  disappeared" report.
- **Mesh decals** are not supported (they need a translucent blend mode); projected decals
  are.
- **Deformation:** dynamic translation, rotation and non-uniform scale are fine. World
  Position Offset works but splits the mesh into individually culled clusters, so the
  displacement must be clamped. **Morph targets are not supported.**
- **Per-vertex tangents are not stored**; tangent space is derived in the pixel shader, which
  can show as discontinuities at edges.
- **Rendering features not supported:** view-specific filtering by minimum screen radius or
  distance culling, forward rendering, VR stereo rendering, MSAA, lighting channels, and the
  wireframe view.
- **Instance cap:** the scene is hard-locked to 16 million instances, counting every streamed-in
  instance, not just Nanite ones.
- Custom expression nodes (and material functions built on them, such as parallax occlusion
  mapping) can produce artifacts, because Nanite has no analytic derivative support yet.
  Vertex Interpolator and Custom UVs work but are evaluated three times per pixel.
- **Platforms:** current consoles and desktop with DirectX 12 and Shader Model 6.

## Nanite and ray tracing

Ray tracing does not trace Nanite geometry directly by default: it uses the mesh's **Fallback
Mesh**, whose fidelity is controlled by Fallback Relative Error in the Static Mesh Editor.
Native ray tracing of Nanite meshes is experimental behind `r.RayTracing.Nanite.Mode 1`, which
keeps full detail at much lower GPU memory than a zero-error fallback. A ray-traced reflection
that does not match the rasterized silhouette is the fallback mesh, not a bug.

## Niagara

Niagara is the VFX system: systems contain emitters, emitters are built from modules, and
effects are previewed in real time. Points that decide whether an effect is affordable:

- Niagara reads Chaos Destruction break and collision events, so destruction-driven VFX are
  data-driven rather than scripted.
- Collisions in Niagara are a per-particle cost and are configured per emitter; particle
  collision is a feature you opt into deliberately.
- Lightweight emitters exist for high-count, low-feature effects; use them when the effect
  does not need the full module stack.
- Niagara ships its own debugging and optimization tooling (the Niagara Debugger and the
  performance views). Attribute a VFX cost with it before rewriting the effect.
- Cascade is superseded by Niagara; new effects use Niagara. `[community]`

## Review checklist

- [ ] Scene went dark after enabling Lumen → check for `Static` mobility lights.
- [ ] Upgraded project has no GI → Lumen was not auto-enabled by the UE4 conversion.
- [ ] Hardware ray tracing enabled on a scene with >100k instances → measure the scene update
      cost before keeping it.
- [ ] Material reverted to default on a Nanite mesh → blend mode is not Opaque or Masked;
      check the Output Log warning.
- [ ] Morph-target or mesh-decal effect broken → not supported with Nanite.
- [ ] MSAA, forward rendering or VR stereo required → Nanite is not available for that path.
- [ ] Ray-traced reflections disagree with the raster image → fallback mesh error.
- [ ] Lighting change lags by seconds → Lumen cache propagation, not a script bug.
- [ ] VFX cost claimed without a capture → measure with the Niagara tooling or Insights first.

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue, maystudios-unreal -->
