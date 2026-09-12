---
name: godot
description: "Develops Godot games with GDScript, scenes, nodes and engine APIs."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# godot

## Scope

Covers Godot 4 application code and project configuration: the scene tree and node
lifecycle, scene instancing and ownership, GDScript 2.0 and its static type system,
signals and groups, `_process` versus `_physics_process`, the three rendering backends
and how to choose between them, `Control` layout and theming, physics bodies with
collision layers and masks, `Resource` design and `.tres`/`.res` files, export presets
with headless command-line builds and CI, high-level multiplayer, and the differences a
C# project hits relative to GDScript.

Targets **Godot 4.7** as the default baseline, with rules gated back to the release that
introduced them (`(Godot 4.3+)`, `(Godot 4.6+)`, `(Godot 4.7)`). Godot 3.x is a different
engine — the renderer, `TileMap`, GDScript syntax and the signal API all changed — and is
covered only as a source of migration traps.

Not covered: the C# language, the .NET SDK, MSBuild, NuGet and general .NET project
work — use the `csharp-dotnet` skill; only the Godot-specific C# bindings and their
divergence from GDScript are here. Unity and Unreal are separate skills (`unity`,
`unreal`) and nothing here transfers. Visual design — colour, typography, hierarchy,
spacing — belongs to `frontend-design`; this skill covers how a Godot UI is *implemented*.
Test-driven development as a method belongs to `test-driven-development`, and browser
end-to-end testing to `web-testing`; running Godot's own test tooling is here. Also out
of scope: shader authoring beyond backend availability, animation and audio node
authoring, art pipelines, and store publishing.

Paths below are relative to this skill's directory.

## Read first

`references/godot-scripting.md` before writing or reviewing any `.gd` file. GDScript's
inference rules are enforced as **parse errors**, not warnings: a script that looks
idiomatic can stop the project from loading at all, and the message names the variable
rather than the cause.

## Core rules

1. `free()` destroys the object immediately, so every statement after it in the same
   function runs against a dead instance. Use `queue_free()`; it defers deletion to the
   end of the frame and is safe to call twice. `(Godot 4.x)` `[verified]`
2. `queue_free()` does not make the instance invalid at the next `await
   get_tree().process_frame` — deletion happens after all deferred calls, so code
   resuming from one `process_frame` still sees `is_instance_valid() == true`, and only
   the second one clears it. Code that awaits once and then "checks" validity is checking
   nothing. `[verified]`
3. `_ready()` runs at most once per node. `remove_child()` followed by `add_child()` does
   not run it again; `request_ready()` before re-adding does. An object pool that recycles
   nodes therefore never re-initialises them. `[verified]`
4. Node children do not exist during `_init()`, so `get_node()`/`$Path` there returns
   nothing usable. Use `@onready`, which resolves immediately before `_ready()`.
   `[verified]`
5. Never resolve a node path in `_process`/`_physics_process`. Measured over 200k lookups
   eight levels deep: a `String` path costs about 45x a cached reference and a `NodePath`
   constant about 10x. Hold the reference in an `@onready` variable. `[verified]`
6. `:=` on an expression whose static type is `Variant` is a parse error, not a warning —
   `debug/gdscript/warnings/inference_on_variant` ships at Error while
   `untyped_declaration` and `inferred_declaration` ship at Ignore. `var x := dict["k"]`
   and `var x := untyped_call()` both stop the script from loading. Declare the type
   explicitly instead. `[verified]`
7. `/` between two integers truncates. `hp - amount * (1 - armour / 100)` with an integer
   `armour` below 100 applies no reduction at all, silently. `[verified]`
8. A `Signal` can only be connected once to the same `Callable`: the second
   `sig.connect(_on_x)` returns `ERR_INVALID_PARAMETER`, prints an error, and leaves one
   connection. What actually stacks is a **freshly built** `Callable` — two lambdas with
   identical text are two objects and both connect. Guard lambda connections, not method
   connections. `[verified]`
9. `CONNECT_REFERENCE_COUNTED` is the only way to register the same `Callable` twice, and
   it still fires once per emission; it takes as many `disconnect` calls as `connect`
   calls to remove. `[verified]`
10. Put `move_and_slide()` and every other physics call in `_physics_process`; it reads the
    physics step's delta internally, so calling it from `_process` runs the simulation at
    the wrong rate. `[official]`
11. `CharacterBody2D`/`3D.velocity` is already in units per second. Multiplying it by
    `delta` turns a velocity into a per-frame displacement and makes movement speed depend
    on the frame rate — the official class reference names this as the common mistake.
    `[official]`
12. Collision layer is what a body *is*; collision mask is what it *scans for*. Detection
    is one-directional: for A to notice B, B's layer must be in A's mask. Both default to
    `1`, which is why unrelated prototypes appear to work until a second layer exists.
    `[verified]`
13. An exported `Resource` property assigned in the Inspector points at one loaded object,
    so every `PackedScene.instantiate()` shares it and mutating it through one instance
    changes all of them — and in the editor the change is written back into the `.tres` on
    save. Set `resource_local_to_scene` on the resource, or `duplicate()` it per instance.
    `duplicate()` is shallow by default: nested resources, arrays and dictionaries stay
    shared. `[verified]`
14. Per-instance mutable state (current health, cooldowns, ammo) does not belong on a
    shared design-data `Resource` even after the sharing is fixed. Keep the resource
    read-only at runtime. `[verified]`
15. Writing to `res://` in an exported build is **not** blocked and reports no error, but
    every later read still returns the packed bytes, so the write is a silent no-op;
    `ProjectSettings.globalize_path("res://")` also returns an empty string in an export.
    In the editor the same code works, because `res://` is the project folder — so this
    defect always survives testing. `user://` is the only writable location. `[verified]`
16. Web runs the **Compatibility** renderer only, which is why
    `rendering/renderer/rendering_method.web` defaults to `gl_compatibility`. Volumetric
    fog, screen-space reflections, SDFGI, VoxelGI, TAA and FSR2 are Forward+ only and are
    silently absent from a web build. `[official]`
17. Read the renderer at runtime from `RenderingServer.get_current_rendering_method()`
    `(Godot 4.4+)`, never from the `rendering/renderer/rendering_method` project setting:
    the engine may have fallen back to another driver or renderer, or `--rendering-method`
    may have overridden it. `[verified]`
18. A project upgraded from an earlier Godot behaves differently from one created in 4.6
    or later, because new projects are written four non-default settings:
    `physics/3d/physics_engine = "Jolt Physics"` (engine default is GodotPhysics3D),
    `display/window/stretch/mode = "canvas_items"` (default `disabled`),
    `display/window/stretch/aspect = "expand"` (default `keep`), and
    `rendering/rendering_device/driver.windows = "d3d12"` (default `vulkan`). Read
    `project.godot` before reasoning about physics or scaling behaviour. `(Godot 4.6+)`
    `[verified]`
19. A `Container` owns its children's layout. A child's `position`, `size` and anchors are
    overwritten on the next sort, so `set_anchors_preset()` inside a container does
    nothing. Move the node out of the container, or wrap it. `[verified]`
20. Set anchors with the method `set_anchors_preset()`. Assigning the `anchors_preset`
    property is an editor-facing path whose setter returns early unless `layout_mode` is
    already Anchors or Uncontrolled, so from code it is a silent no-op. `[verified]`
21. `Control.mouse_filter` defaults to `MOUSE_FILTER_STOP`, and `Panel` and `ColorRect`
    inherit that default — a decorative full-rect panel swallows every click beneath it.
    `Label` overrides the default to `IGNORE` and `TextureRect` to `PASS`. `[verified]`
22. Multiplayer authority must be derived from a value that is identical on every peer,
    such as the node name assigned by the spawner. The avatar script runs on all peers, so
    `set_multiplayer_authority(multiplayer.get_unique_id())` in `_ready()` makes each peer
    claim every avatar locally. `set_multiplayer_authority()` does not replicate itself,
    and a parent's authority does not propagate to children added later. `[official]`
23. RPCs travel as a numeric id derived from the **sorted position** of the method name in
    the node's RPC config, not as a name. Adding, removing or renaming any `@rpc` method
    shifts the ids of the others, so peers built from different source execute different
    functions; the engine only prints `The rpc node checksum failed` once, while confirming
    a node path, and then keeps running. `[verified]`
24. `add_child(node)` replaces a colliding name with a generated `@`-prefixed name from a
    per-process counter, so node paths diverge across peers. Use `MultiplayerSpawner`, or
    `add_child(node, true)` with a deterministic name, for anything addressed by path.
    `[verified]`
25. `godot --headless --quit-after N` exits with status **0** even when the main scene's
    script failed to parse, and `N` counts main-loop iterations, not seconds. A CI smoke
    test that only checks the exit code passes on a completely broken build. Gate on
    `--check-only` and on the absence of `SCRIPT ERROR`/`ERROR` in the output.
    `[verified]`
26. A fresh clone has no `.godot/global_script_class_cache.cfg`, so `class_name` global
    types do not resolve on the first headless run and produce `Could not find type ... in
    the current scope`. Run `godot --headless --import` before any export or smoke step.
    `[verified]`

## Workflows

### implement

- [ ] Read `project.godot` first: `config/features` (which Godot last wrote it),
      `renderer/rendering_method`, `physics/3d/physics_engine`, `display/window/stretch/*`,
      the `[autoload]` block, and `physics_ticks_per_second`. Rules 16-18 all depend on
      these values.
- [ ] Read one existing scene and one existing script to learn the project's conventions:
      typed or untyped GDScript, `@onready` or `get_node`, composition depth, whether
      resources are shared or `local_to_scene`.
- [ ] Model data before nodes. A `Resource` subclass for read-only design data (rule 13),
      plain fields on the node for per-instance state (rule 14).
- [ ] Write the script in the project's order: `class_name`, `extends`, signals, `@export`,
      `@onready`, private `_fields`, lifecycle callbacks, public API. Type every
      declaration (rule 6).
- [ ] Split the loops: input and rendering-rate work in `_process`, everything physical in
      `_physics_process` (rules 10-11).
- [ ] Wire communication with signals emitted upward, per
      `references/godot-signals.md`; reach for an autoload only for genuinely global state.
- [ ] **Gate:** `godot --headless --check-only --script res://<new>.gd` reports nothing,
      and `godot --headless --import && godot --headless --quit-after 300` produces no
      `SCRIPT ERROR` or `ERROR` lines.

### review

- [ ] Establish the engine version and the four settings from rule 18 before judging
      anything version-dependent. A finding that depends on the physics engine is not a
      finding until you know which one is configured.
- [ ] Walk the Core rules in order; they are ordered by how often each is the real defect.
- [ ] Trace object lifetime end to end: who creates the node, who frees it, whether
      anything holds a reference across the free (rules 1-3).
- [ ] Trace every connect site and classify it: same-`Callable` method connection (noisy
      but harmless), or freshly built lambda or `bind` (really stacks). Rule 8 makes these
      opposite findings.
- [ ] Check every `@export`ed `Resource` for shared mutation (rules 13-14) and every
      `res://` write for rule 15.
- [ ] Report only findings with a reachable trigger and a concrete consequence. A text
      match is a lead, never a finding; read the function and its callers first.
- [ ] **Gate:** every finding carries `path:line`, the trigger, the runtime consequence and
      a fix, and any version-dependent claim names the Godot version it holds for.

### debug-runtime-error

- [ ] Reproduce headlessly and capture both streams:
      `godot --headless --path <project> --quit-after 600 2>&1 | tee run.log`. The
      interesting output is on stderr and is lost by default.
- [ ] Fix the first error, not the loudest one. Later errors are usually cascades of a
      failed script load.
- [ ] Match the message shape to the cause: `Parse Error: Cannot infer the type` is rule 6;
      `Could not find type ... in the current scope` is rule 26; `Attempt to call ... on a
      previously freed instance` is rule 1 or 2; `Signal ... is already connected` is
      rule 8; `The rpc node checksum failed` is rule 23.
- [ ] For a stale or wrong-looking UI, check layout ownership before rendering: a control
      at the origin with the wrong size is rule 19 or 20, a dead button is rule 21.
- [ ] **Gate:** the reproduction command no longer prints the diagnostic, and the log is
      attached to the finding rather than summarised from memory.

### choose-renderer

- [ ] List the target platforms first. Web forces Compatibility (rule 16); older mobile
      and old desktop GPUs force it too.
- [ ] List the rendering features the project actually depends on and check each against
      the matrix in `references/godot-rendering.md`. Volumetric fog, SSR, SDFGI, VoxelGI,
      TAA, FSR2 and subsurface scattering are Forward+ only; decals, particle trails,
      CompositorEffects, MSAA 2D and HDR need a RenderingDevice renderer.
- [ ] Decide one renderer per platform using
      `rendering/renderer/rendering_method` plus the `.mobile` and `.web` overrides — not
      one renderer for everything.
- [ ] Log `RenderingServer.get_current_rendering_method()` at startup (rule 17) so a
      silent fallback is visible in a player's log.
- [ ] **Gate:** the feature list and the chosen renderer are stated together, with each
      feature that the fallback renderer loses named explicitly.

### export-and-ship

- [ ] `godot --headless --import` first (rule 26), then confirm the export templates
      installed match the engine version exactly.
- [ ] Read `export_presets.cfg` and use the preset names verbatim: the CLI matches them
      exactly and reports `Invalid export preset name` with a list of what it did find.
- [ ] Create the output directory before exporting; a missing directory fails with
      `Prepare Template: The given export path doesn't exist`.
- [ ] Export with `--export-release` for shipping and `--export-debug` only for internal
      builds; add non-resource files (`*.json`, `*.txt`) to the preset's include filter or
      they are absent from the pack.
- [ ] Run the exported binary, not just the editor build, and check rule 15 for every save
      path.
- [ ] **Gate:** the export exits 0, the exported binary boots and prints no `ERROR`, and
      the smoke step fails on error output rather than on exit status alone (rule 25).

## Topic router

| Topic | Read when | File |
|---|---|---|
| GDScript and the node lifecycle | Writing or fixing any `.gd`; typing and inference errors; `@export`/`@onready`/`@tool`; `await`; 3.x syntax migration | `references/godot-scripting.md` |
| Nodes and scenes | Scene composition, instancing, `queue_free`, autoloads, `owner`, pooling, `.tscn` structure | `references/godot-nodes-and-scenes.md` |
| Signals and groups | Decoupling nodes, connect flags, duplicate-connection bugs, groups, event buses | `references/godot-signals.md` |
| Rendering backends | Choosing Forward+ / Mobile / Compatibility; a feature missing on one platform; web or mobile visual differences | `references/godot-rendering.md` |
| UI and Control nodes | HUDs, menus, anchors, containers, `Theme`, focus, input that does not reach a control | `references/godot-ui.md` |
| Physics | Body type choice, layers and masks, `Area` detection, raycasts, character controllers, Jolt versus GodotPhysics3D | `references/godot-physics.md` |
| Resources and data | `Resource` subclasses, `.tres`/`.res`, shared-instance bugs, `load` versus `preload`, save data | `references/godot-resources.md` |
| Build, export and CI | Export presets, headless CLI, platform requirements, dedicated servers, test frameworks | `references/godot-build.md` |
| Multiplayer | ENet peers, `@rpc`, authority, `MultiplayerSpawner`/`MultiplayerSynchronizer`, cheat surface | `references/godot-multiplayer.md` |
| C# interop | A `.csproj` Godot project; translating GDScript idioms; `[Export]`/`[Signal]`; GDScript-to-C# calls | `references/godot-csharp-interop.md` |

## Output format

For `review` and any other report on existing code, group findings by file, ordered by
severity, with no preamble:

```
entities/player.gd
  L69 blocking - free() destroys the node immediately, so change_scene_to_file and the
       print below it run against a freed instance. This is the intermittent crash.
       before: free()
       after:  queue_free()   # and move the scene change to a caller that outlives it
  L29 blocking - move_and_slide() in _process runs the character controller at the render
       rate, and velocity.x is additionally multiplied by delta. velocity is already
       per-second, so speed scales with frame rate twice over.
  L38 important - two absolute string node paths resolved every frame; measured at roughly
       45x a cached reference. Move both to @onready.
  L23 minor - the two identical mgr.connect(...) calls do not double the handler: the
       second is rejected with ERR_INVALID_PARAMETER and logs an error. The two lambdas on
       L25-26 do double it.

project.godot
  L31 important - no physics/3d/physics_engine key, so this upgraded project runs
       GodotPhysics3D while a project created in 4.6+ runs Jolt Physics.
  ok - renderer/rendering_method is forward_plus, which is correct for the desktop target.
```

Severities: `blocking` (crashes, loses data, does not load, silently drops a save, or lets
any client mutate authoritative state), `important` (frame-rate-dependent behaviour,
per-frame allocation or lookup, stale UI, shared-resource mutation, input that never
reaches a control, a silent renderer downgrade), `minor` (naming, ordering, noisy but
harmless errors). End with a one-line verdict: ship, ship after blocking fixes, or rework.
Name the Godot version every version-dependent claim holds for, and list checks you did
not run separately from findings.

## Environment

The Linux editor build runs headless, so everything below works on a machine with no
display or GPU.

```bash
godot --headless --version                       # confirm the exact build
godot --headless --path . --import               # build .godot/, register class_name types
godot --headless --check-only --script res://x.gd   # parse gate; exits 1 on failure
godot --headless --path . --quit-after 600       # boot smoke test; N is frames, not seconds
godot --headless --path . --script res://tools/task.gd   # run a SceneTree/MainLoop script
godot --headless --export-release "<preset>" build/<dir>/<out>   # output dir must exist
godot --headless --export-debug   "<preset>" build/<dir>/<out>
godot --headless --export-pack    "<preset>" build/game.pck
```

Export templates must match the engine version exactly and are installed under
`~/.local/share/godot/export_templates/<version>/`. In a container or sandbox, point
`XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` at a project-local directory, or
`user://` writes and template lookup fail. C# projects need the .NET editor build plus a
matching .NET SDK; the standard build cannot run C# at all.
