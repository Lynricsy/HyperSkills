# Rendering backends and selection

Verified against: Godot 4.7.2 — feature matrix from the engine's own documentation source;
visual behaviour is `[official]`, not reproduced on this machine (headless creates no
RenderingDevice)

## Contents

- [Three renderers, two backends](#three-renderers-two-backends)
- [How the renderer is chosen](#how-the-renderer-is-chosen)
- [Reading the renderer at runtime](#reading-the-renderer-at-runtime)
- [Feature matrix](#feature-matrix)
- [Choosing](#choosing)
- [Switching an existing project](#switching-an-existing-project)
- [2D specifics](#2d-specifics)
- [Version-gated rendering changes](#version-gated-rendering-changes)
- [Headless](#headless)

## Three renderers, two backends

| Renderer | Project value | Driver | Backend |
|---|---|---|---|
| Forward+ | `forward_plus` | Vulkan, Direct3D 12 or Metal | RenderingDevice |
| Mobile | `mobile` | Vulkan, Direct3D 12 or Metal | RenderingDevice |
| Compatibility | `gl_compatibility` | OpenGL 3.3 / OpenGL ES 3.0 / WebGL 2 | — |

The renderer decides which features exist. The driver decides which GPUs can run it.
Forward+ uses clustered forward lighting; Mobile and Compatibility use single-pass
forward, and on Compatibility shadow-casting lights take a multi-pass path with less
accurate blending. Compatibility also performs lighting on non-linear sRGB data, which is
why the same scene looks different there rather than merely worse.

## How the renderer is chosen

```
rendering/renderer/rendering_method          default "forward_plus"
rendering/renderer/rendering_method.mobile   default "mobile"
rendering/renderer/rendering_method.web      default "gl_compatibility"
```

The per-platform overrides are why a desktop Forward+ project silently becomes a
Compatibility project on web and a Mobile project on Android — **web supports
Compatibility only**, there is no choice to make there. The `--rendering-method <method>`
command-line argument overrides all of it.

Independently of the renderer, the driver has its own overrides. Notably
`rendering/rendering_device/driver.windows` defaults to `vulkan`, but a project created
in Godot 4.6 or later has `d3d12` written into `project.godot` — so an upgraded project
and a new project use different graphics APIs on Windows out of the box.

Since Godot 4.4, a RenderingDevice renderer that cannot get Vulkan falls back to
Direct3D 12 and vice versa, and if neither is available it falls back to Compatibility
unless `rendering/rendering_device/fallback_to_opengl3` (default `true`) is turned off.
The project runs; it just does not look like it was authored to.

## Reading the renderer at runtime

```gdscript
func _ready() -> void:
    print("renderer: ", RenderingServer.get_current_rendering_method())
    print("driver:   ", RenderingServer.get_video_adapter_api_version())
```

The class reference is explicit that the project setting may not reflect reality, because
of fallback or a command-line override, and that
`RenderingServer.get_current_rendering_method()` is the value to use. It exists from
**Godot 4.4** onward `(Godot 4.4+)`; before that there is no runtime accessor at all.
Any code that branches on the renderer — enabling an effect, choosing a shader variant,
sizing a buffer — must read it from there. Logging it at startup is what makes a silent
fallback visible in a player's log instead of in a bug report titled "looks wrong on my
machine".

## Feature matrix

Absent from all three lists means available everywhere.

| Feature | Compatibility | Mobile | Forward+ |
|---|---|---|---|
| Web | yes | no | no |
| XR | works, not recommended | recommended | works, poorly optimised |
| Mobile | yes (low-end) | yes (high-end) | works, poorly optimised |
| Max Omni/Spot lights | 8 per mesh (raisable) | 8 per mesh, 256 per view | 512 per cluster (raisable) |
| Max DirectionalLights | 8 | 8 | 8 |
| PCSS soft shadows, Omni/Spot | no | yes | yes |
| PCSS soft shadows, Directional | no | no | yes |
| Light projector textures | no | yes | yes |
| ReflectionProbe | 2 per mesh | 8 per mesh | unlimited |
| LightmapGI | renders baked lightmaps; baking needs RenderingDevice | yes | yes |
| VoxelGI, SDFGI, SSIL | no | no | yes |
| SSAO | **yes** | **no** | yes |
| Screen-space reflections | no | no | yes |
| Volumetric fog | no | no | yes |
| Subsurface scattering | no | no | yes |
| CompositorEffects | no | yes | yes |
| Fullscreen-quad post-processing | yes | yes | yes |
| MSAA 3D | yes | yes | yes |
| MSAA 2D | no | yes | yes |
| FXAA, SMAA | no | yes | yes |
| TAA, FSR2 | no | no | yes |
| Normal/roughness buffer | no | no | yes |
| Compute shaders | no | yes, slow on older devices | yes |
| Decals, particle trails, particle SDF collision | no | yes | yes |
| Depth of field blur, debanding, VRS | no | yes | yes |
| 2D HDR viewport, HDR output | no | yes | yes |
| Colour precision | RGBA8 | RGB10A2 (RGBA16F with HDR 2D) | RGBA16F |
| Depth precision | 24-bit, no reverse Z | 24-bit, reverse Z | 32-bit, reverse Z |
| Direct `RenderingDevice` access | no | yes | yes |
| Base cost / scaling | low base, high scaling | medium / medium | highest base, low scaling |

Two entries usually surprise people. **SSAO works on Compatibility but not on Mobile** —
it is not a simple capability ladder. And Compatibility renders baked lightmaps but
cannot bake them, so a Compatibility-only project still needs a RenderingDevice-capable
machine somewhere in the pipeline.

## Choosing

- **Forward+** for desktop-only 3D that wants the full feature set, and for 2D that needs
  compute shaders. It has the highest base cost per frame and the best scaling, so it wins
  on complex scenes and loses on trivial ones.
- **Mobile** for phones, tablets and standalone XR, and for desktop builds that must share
  a feature set with those. Forward+ is supported on mobile hardware but poorly optimised
  for it, so "just use Forward+ everywhere" is the wrong default for a cross-platform
  title.
- **Compatibility** for web (no alternative), for old hardware, and for most 2D. Lowest
  base cost, widest reach, fewest features.

Pick per platform, not once. A concrete example: a project with volumetric fog and SSR on
desktop ships on web with neither, which is a design change, not a quality slider. Decide
whether those effects are load-bearing before the web preset exists, and give the
Compatibility path an authored fallback rather than an accidental absence.

## Switching an existing project

Switching between Mobile and Forward+ needs modest adjustment; switching to or from
Compatibility needs lighting and environment rework, because of the non-linear lighting
and the missing effects. Budget for that rather than treating it as a project-setting
change. Effects still assigned in an `Environment` but unsupported by the active renderer
are simply not drawn — there is no error, so the only signal is the image.

## 2D specifics

`display/window/stretch/mode` defaults to `disabled` (one scene unit per screen pixel),
and `stretch/aspect` to `keep`. A project created in Godot 4.6 or later has
`canvas_items` plus `expand` written into `project.godot` instead, which is the sensible
default for a game and the wrong default for a tool. Check the file rather than assuming.

`gui/common/snap_controls_to_pixels` defaults to `true` and snaps `Control` vertices to
whole pixels. For pixel-art projects also set the texture filter to nearest on the
project's default texture import and use `canvas_items` stretch with an integer-friendly
base resolution; a fractional scale plus linear filtering is what produces shimmering
sprites.

`(Godot 4.7)` `CanvasItem` no longer adds an antialiasing feather when drawing lines, so
lines drawn with `draw_line` are thinner than in 4.6 and projects that relied on the
feather must pass a larger width.

## Version-gated rendering changes

| Version | Change |
|---|---|
| `(Godot 4.4+)` | RenderingDevice renderers fall back Vulkan to Direct3D 12 and back, then to Compatibility |
| `(Godot 4.6)` | Glow's default blend mode became Screen, which is much brighter than the previous Soft Light; other glow defaults changed with it. Volumetric fog blending became more physically accurate and appears brighter. Mobile's glow was rewritten and looks different |
| `(Godot 4.7)` | The `LinearToSRGB` visual shader node no longer clamps to 0..1 on Mobile and Forward+ |

After upgrading across any of these, re-tune `Environment` rather than assuming the scene
is unchanged.

## Headless

`--headless` selects the headless display server and creates no RenderingDevice, so it
cannot validate anything on this page. It is still the right way to run logic tests,
exports and dedicated servers:

```gdscript
if DisplayServer.get_name() == "headless" or OS.has_feature("dedicated_server"):
    _start_server_only()
```

Anything that must be checked visually needs a real display or a GPU-capable CI runner.
Report that boundary instead of reasoning about an image you did not render.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, haxqer-godot -->
