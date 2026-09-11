# GDScript and the node lifecycle

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`), GDScript 2.0

## Contents

- [The type system is enforced at parse time](#the-type-system-is-enforced-at-parse-time)
- [Integer arithmetic](#integer-arithmetic)
- [Lifecycle callbacks and what exists when](#lifecycle-callbacks-and-what-exists-when)
- [`_ready()` runs once](#_ready-runs-once)
- [`_process` versus `_physics_process`](#_process-versus-_physics_process)
- [Annotations](#annotations)
- [`await`](#await)
- [Script order and naming](#script-order-and-naming)
- [Warning levels worth changing](#warning-levels-worth-changing)
- [Old patterns](#old-patterns)

## The type system is enforced at parse time

GDScript 2.0 has three declaration forms and they are not interchangeable:

```gdscript
var a = 1                # untyped: Variant
var b := 1               # inferred: int, from the literal's static type
var c: int = 1           # explicit: int
```

Inference works only when the right-hand side has a concrete static type. When it does
not, the result would be `Variant`, and that is an **error** out of the box:
`debug/gdscript/warnings/inference_on_variant` ships at level 2 (Error), while
`untyped_declaration` and `inferred_declaration` both ship at 0 (Ignore).

```gdscript
var d := {"k": 1}
var x := d["k"]          # Parse Error: Cannot infer the type of "x" variable
                         # because the value doesn't have a set type.
var y := untyped_fn()    # same error; the function has no declared return type
var z: int = d["k"]      # fine: explicit type, runtime-checked assignment
```

The script does not load, so the scene loads without its script and the node silently
does nothing. The message names the *variable*, not the expression, which is why this
reads as a mystery. Sources of `Variant`: `Dictionary` and untyped `Array` reads,
functions with no `-> T`, `JSON.parse_string()`, `Object.get()`, `Callable.call()`.

`$Path`, `get_node()`, `PackedScene.instantiate()` and `load()` all have declared
return types (`Node`, `Node`, `Node`, `Resource`), so `:=` is legal on them — it just
infers the base type, not your subclass. Use an explicit type or `as` when you need the
subclass:

```gdscript
@onready var body: CharacterBody2D = $Body         # explicit, checked on assignment
var enemy := GRUNT.instantiate() as Enemy          # cast, null if the type is wrong
```

Typed containers are enforced at runtime, not just statically:

```gdscript
var ids: Array[int] = []
ids.append("x")          # runtime error, the array keeps its element type
var by_id: Dictionary[int, Enemy] = {}             # (Godot 4.4+)
```

Assigning a wider type into a narrower variable is a runtime error with a clear message
(`Trying to assign value of type 'Node' to a variable of type 'Enemy'`), so typing the
declarations converts a class of silent misbehaviour into an immediate failure.

## Integer arithmetic

`/` between two `int` values truncates. This is the single most common numeric defect in
gameplay code because it produces a plausible-looking zero:

```gdscript
var armour := 30                   # int
var reduced := amount * (1 - armour / 100)    # armour / 100 == 0, no reduction at all
var right   := amount * (1.0 - armour / 100.0)
```

`integer_division` ships as a warning, not an error, and a warning never reaches stdout
on a plain headless run — only the editor's Errors panel and the script debugger channel
show it. Do not rely on seeing it.

## Lifecycle callbacks and what exists when

| Callback | When | Children exist |
|---|---|---|
| `_init()` | On object construction, before any tree involvement | no |
| `_enter_tree()` | Each time the node enters the tree; parent first, then children | yes, but not `_ready` yet |
| `@onready` assignment | Immediately before `_ready()` | yes |
| `_ready()` | Once, children's `_ready()` first, then the parent's | yes |
| `_process(delta)` | Every rendered frame, after physics ticks | yes |
| `_physics_process(delta)` | Every physics tick | yes |
| `_exit_tree()` | Each time the node leaves the tree | yes |
| `NOTIFICATION_PREDELETE` | Just before destruction | being destroyed |

`_init()` cannot see children, so `get_node()`/`$Path` there is useless. That is what
`@onready` exists for. A field that is assigned but never declared is a parse error, so
`hp_bar = get_node(...)` in `_init()` without a `var hp_bar` above it fails twice over.

Both `_process` and `_physics_process` are only invoked if the node overrides them, and
only while it is inside the tree. Execution order within a tick is `process_priority`
(lower first), then tree order; `process_physics_priority` is the equivalent for the
physics tick.

`_process`'s `delta` is capped at
`Engine.time_scale * Engine.max_physics_steps_per_frame / Engine.physics_ticks_per_second`
— 8/60 ≈ 133 ms with the defaults. Under a stall, accumulated `delta` therefore diverges
from wall-clock time, so `delta` sums are not a clock. `_physics_process`'s `delta` is
exactly `Engine.time_scale / Engine.physics_ticks_per_second`, i.e. constant.

## `_ready()` runs once

`_ready()` is called at most once per node for the node's entire lifetime. Removing a
node from the tree and adding it back does **not** call it again:

```gdscript
var p := Pooled.new()
add_child(p)        # _ready() runs, count = 1
remove_child(p)
add_child(p)        # _ready() does NOT run, count = 1
remove_child(p)
p.request_ready()
add_child(p)        # _ready() runs, count = 2
```

`is_node_ready()` also stays `true` after removal, so it cannot be used to detect the
recycled state. Any object pool that re-parents nodes must call `request_ready()`, or
move initialisation into a method the pool calls explicitly. This is the usual cause of
"the pooled effect only plays the first time".

## `_process` versus `_physics_process`

Physics belongs in `_physics_process`, unconditionally. `move_and_slide()` reads the
physics step's delta internally, so calling it from `_process` runs the character
controller at the render rate.

`velocity` on `CharacterBody2D`/`CharacterBody3D` is already in units per second, and
the class reference calls out multiplying it by `delta` as the common mistake. The two
defects compound: a `_process` call site that also multiplies by `delta` scales twice
with frame rate.

```gdscript
func _physics_process(delta: float) -> void:
    velocity.x = Input.get_axis("left", "right") * SPEED     # no delta
    if not is_on_floor():
        velocity.y += GRAVITY * delta                         # an acceleration does use delta
    move_and_slide()
```

`RayCast2D`/`RayCast3D` results are refreshed on the physics tick, so read
`is_colliding()` from `_physics_process`; after moving a ray within the same tick, call
`force_raycast_update()` before reading it.

## Annotations

| Annotation | Note |
|---|---|
| `@export var x: float = 1.0` | Needs a type the Inspector can represent. Custom `Resource`/`Node` types must carry `class_name`, otherwise a less specific type is exported |
| `@export_range(0, 10, 0.5)` | Min, max, step; add `or_greater`/`or_less` to allow overshoot |
| `@export_group("Combat")` / `@export_subgroup` / `@export_category` | Inspector organisation only, no runtime effect |
| `@export_storage var x` | Serialised into the scene or resource but hidden from the Inspector, and copied by `duplicate()` unlike a plain field |
| `@export_tool_button("Bake")` | Inspector button that calls a `Callable`; `@tool` only `(Godot 4.4+)` |
| `@onready var n: Node = $Path` | Assigned immediately before `_ready()`; illegal on a non-`Node` class |
| `@tool` | The script also runs in the editor. Guard every side effect with `Engine.is_editor_hint()` or it will mutate project data while editing |
| `@rpc("any_peer", "call_local", "reliable")` | Order of the string arguments is free, but the set of `@rpc` methods in a script is part of the wire contract |
| `@abstract` | Class or method cannot be instantiated or must be overridden `(Godot 4.5+)` |

`class_name X` registers a project-global type. That registration lives in
`.godot/global_script_class_cache.cfg`, which the editor's filesystem scan writes — so on
a fresh clone the first headless run cannot resolve `X` and reports
`Could not find type "X" in the current scope`. `godot --headless --import` regenerates
the cache. `class_name` values must be unique project-wide.

## `await`

`await` suspends the function until a signal fires or a coroutine returns:

```gdscript
await get_tree().create_timer(0.2).timeout
await $AnimationPlayer.animation_finished
var result = await load_async()          # awaiting a coroutine returns its value
```

Two things to keep in mind. First, `await` inside `_ready()` means `_ready()` returns
early: the rest of the tree continues, and `is_node_ready()` is already `true` while your
initialisation is still pending. Second, awaiting a signal on a node that gets freed
leaves the coroutine suspended forever — check `is_instance_valid()` after any `await`
that could outlive the emitter, and remember that one `await get_tree().process_frame`
after a `queue_free()` is not enough for the instance to be gone.

## Script order and naming

```gdscript
class_name Player
extends CharacterBody2D

signal health_changed(current: int, maximum: int)

@export var speed: float = 220.0
@export_group("Combat")
@export var attack_damage: int = 10

@onready var _sprite: AnimatedSprite2D = $AnimatedSprite2D

const MAX_HEALTH := 100
var _health: int = MAX_HEALTH

func _ready() -> void: ...
func _physics_process(delta: float) -> void: ...
func take_damage(amount: int) -> void: ...
func _apply_knockback(dir: Vector2) -> void: ...
```

`snake_case` for files, functions and variables; `PascalCase` for `class_name` and node
names; `CONSTANT_CASE` for constants; a leading underscore for private members. Keep the
order above — exports at the top is what a designer opening the Inspector expects to
match.

## Warning levels worth changing

`debug/gdscript/warnings/*` are per-project. The two worth raising in a project that
intends to stay typed:

| Setting | Ships as | Raise to |
|---|---|---|
| `untyped_declaration` | 0 Ignore | 1 Warn |
| `unsafe_property_access` | 0 Ignore | 1 Warn |
| `integer_division` | 1 Warn | 2 Error in numeric-heavy projects |
| `inference_on_variant` | 2 Error | leave it |

Warnings only reach stdout through the script debugger channel, so a headless CI run
reports none of them. Gate on `--check-only` for parse errors and read the editor's
Errors panel, or run with `-d`, for warnings.

## Old patterns

<details>
<summary>Godot 3.x syntax that no longer parses</summary>

| 3.x | 4.x |
|---|---|
| `export var x` | `@export var x` |
| `onready var x` | `@onready var x` |
| `tool` | `@tool` |
| `yield(obj, "sig")` | `await obj.sig` |
| `connect("sig", self, "_on_sig")` | `sig.connect(_on_sig)` |
| `emit_signal("sig", a)` | `sig.emit(a)` |
| `scene.instance()` | `scene.instantiate()` |
| `remote func` / `master func` | `@rpc(...)` annotation |
| `rect_size` / `rect_position` / `rect_min_size` | `size` / `position` / `custom_minimum_size` |
| `OS.window_size`, `OS.get_screen_size()` | `DisplayServer.*` |

`Object.connect("sig", Callable(self, "_on_sig"))` still works but the string-method form
does not; prefer `sig.connect(_on_sig)` so the callable is checked at parse time.

</details>

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, haxqer-godot, wshobson-godot -->
