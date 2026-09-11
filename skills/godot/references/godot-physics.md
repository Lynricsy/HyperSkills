# Physics: bodies, layers, detection, characters

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`). Concepts apply to 2D
and 3D — swap the `2D`/`3D` suffix.

## Contents

- [Which physics engine is actually running](#which-physics-engine-is-actually-running)
- [Body types](#body-types)
- [Layers and masks](#layers-and-masks)
- [Area detection](#area-detection)
- [Driving a RigidBody](#driving-a-rigidbody)
- [CharacterBody](#characterbody)
- [Raycasts and shape queries](#raycasts-and-shape-queries)
- [The physics tick](#the-physics-tick)
- [Tunnelling](#tunnelling)
- [Version gates](#version-gates)

## Which physics engine is actually running

```
physics/2d/physics_engine   default "DEFAULT" == GodotPhysics2D
physics/3d/physics_engine   default "DEFAULT" == GodotPhysics3D
```

But a project created in Godot 4.6 or later has `physics/3d/physics_engine = "Jolt
Physics"` written into `project.godot`. An upgraded project has no such key, so it runs
GodotPhysics3D. **Read `project.godot` before making any 3D physics claim**: the two
engines differ in behaviour, and the Godot 4.7 behaviour changes below apply only to the
Jolt path.

Jolt is generally faster and more reliable, so switching is usually right — but it is a
behaviour change, not a performance switch, and it needs re-tuning rather than a flag
flip. Setting the value explicitly (to either engine) is better than leaving `DEFAULT`,
which the class reference says may change meaning in future releases.

Jolt also ignores several space-level GodotPhysics tunables and warns about each one:
contact recycle radius, contact max separation, contact max allowed penetration and
contact default bias. A project that tuned those is tuning nothing after the switch.

## Body types

| Node | Moves | Simulated | Use for |
|---|---|---|---|
| `StaticBody` | no | no | floors, walls, anything fixed |
| `AnimatableBody` | by animation or code | no, but pushes others | moving platforms, doors |
| `RigidBody` | by the solver | yes | debris, props, vehicles, anything that should tumble |
| `CharacterBody` | by your script | no | players and most enemies |
| `Area` | by code | no | triggers, hurtboxes, water volumes, audio zones |

Every body needs a `CollisionShape` (or `CollisionPolygon`) child with a shape actually
assigned. An empty shape slot means the body never collides, with no warning at runtime.

Prefer primitive shapes. A `ConvexPolygonShape` is far cheaper than a
`ConcavePolygonShape`, and a concave shape on a moving body is not supported in a useful
way — decompose it into several convex shapes instead.

## Layers and masks

Layer = what this body **is**. Mask = what this body **scans for**. Both default to `1`,
which is why a two-object prototype appears to work and the third object breaks it.

Detection is one-directional: for A to notice B, B's `collision_layer` must intersect A's
`collision_mask`. For a solid collision response between two physics bodies you normally
want it mutual; for an `Area` hurtbox you often want it one-way on purpose.

```gdscript
func _ready() -> void:
    set_collision_layer_value(1, true)      # I am on layer 1 (layer numbers are 1..32)
    set_collision_mask_value(2, true)       # I scan layer 2 (walls)
    set_collision_mask_value(3, true)       # and layer 3 (enemies)
    # bitfield forms also work: collision_layer = 1; collision_mask = 0b110
```

Name the layers in Project Settings > Layer Names. An unnamed layer set is unreadable
after a month and is the reason layer bugs recur: nobody can tell whether layer 4 means
"enemy" or "enemy projectile".

## Area detection

```gdscript
extends Area2D

func _ready() -> void:
    body_entered.connect(_on_body_entered)
    area_entered.connect(_on_area_entered)

func _on_body_entered(body: Node2D) -> void:
    if body.has_method("take_damage"):
        body.take_damage(10)
```

Three switches must all be right or nothing fires: `monitoring` (default `true`) lets
this area detect others; `monitorable` (default `true`) lets others detect this area;
and the layer/mask pair must intersect. `body_entered` is documented as requiring
`monitoring`, and a `TileMap`/`TileMapLayer` is only detected if its `TileSet` has
collision shapes.

Signals are emitted during the physics step, so mutating the tree from a handler
(`add_child`, `queue_free`, changing a shape) is the classic source of "flushing queries"
errors. Use `call_deferred`, `set_deferred` or a `CONNECT_DEFERRED` connection for
structural changes; `queue_free()` is already deferred and is safe.

`get_overlapping_bodies()`/`get_overlapping_areas()` reflect the state as of the last
physics step, not the current instant, so a body that moved this frame may not be listed
yet.

## Driving a RigidBody

Never assign `position` to a `RigidBody`. It fights the solver, produces jitter, and lets
the body pass through thin geometry because no motion was integrated.

```gdscript
extends RigidBody3D

func push(direction: Vector3) -> void:
    apply_central_impulse(direction * 8.0)          # instantaneous velocity change

func _physics_process(_delta: float) -> void:
    apply_central_force(Vector3.FORWARD * 4.0)      # continuous force, per tick
```

To teleport one, do it in `_integrate_forces` through the supplied
`PhysicsDirectBodyState` and zero the velocities there, or set `freeze = true` with
`freeze_mode = FREEZE_MODE_KINEMATIC` and move it as a kinematic body. `custom_integrator`
plus `_integrate_forces` is the escape hatch for fully hand-written dynamics.

`mass`, `gravity_scale`, `linear_damp` and `angular_damp` are the tuning surface;
`lock_rotation` is usually what people actually want when they reach for a joint.

## CharacterBody

```gdscript
extends CharacterBody2D

const SPEED := 220.0
const JUMP_VELOCITY := -400.0
const GRAVITY := 1200.0

func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y += GRAVITY * delta               # acceleration: delta belongs here
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY
    velocity.x = Input.get_axis("left", "right") * SPEED    # velocity: no delta
    move_and_slide()
```

Three invariants:

1. `move_and_slide()` reads the physics step's delta itself, so it belongs in
   `_physics_process`. From `_process` the simulation runs at the render rate.
2. `velocity` is in units per second. The class reference names multiplying it by `delta`
   as the common mistake; it converts a velocity into a per-frame displacement and makes
   speed frame-rate dependent.
3. `is_on_floor()`, `is_on_wall()` and `is_on_ceiling()` report the result of the **last**
   `move_and_slide()`, classified by `up_direction` (default `Vector2.UP`) and
   `floor_max_angle` (default 45°). Reading them before the first `move_and_slide()` of
   the frame reads last frame's answer.

`motion_mode` picks the model: `MOTION_MODE_GROUNDED` (default) has a floor concept and
enables the floor properties; `MOTION_MODE_FLOATING` reports every collision as a wall,
which is what a top-down or space game wants. `up_direction` cannot be zero — use
floating mode instead.

`move_and_slide()` modifies `velocity` when it slides, so re-reading `velocity` after the
call gives the post-collision value, not your intent. Keep your intended velocity in a
separate variable if you need it. `move_and_collide()` is the lower-level alternative that
returns a `KinematicCollision` and does not slide.

Platform behaviour worth knowing before writing a custom solution: a moving platform's
velocity is added automatically, and `platform_on_leave` controls whether the body keeps
that velocity when it steps off.

## Raycasts and shape queries

Node form, polled after physics updated:

```gdscript
@onready var ray: RayCast2D = $RayCast2D            # target_position set in the scene

func _physics_process(_delta: float) -> void:
    if ray.is_colliding():
        var hit := ray.get_collider()
        var point := ray.get_collision_point()
```

`enabled` must be true, and results are refreshed on the physics tick — reading
`is_colliding()` from `_process` can be a frame stale. After moving the ray within the
same tick, call `force_raycast_update()` before reading.

One-shot query, no node:

```gdscript
func ground_under(from: Vector2) -> Dictionary:
    var space := get_world_2d().direct_space_state
    var q := PhysicsRayQueryParameters2D.create(from, from + Vector2(0, 64))
    q.collision_mask = 1
    q.exclude = [self.get_rid()]                    # Array[RID], not an array of nodes
    return space.intersect_ray(q)                   # {} when nothing was hit
```

`exclude` takes `RID`s; passing nodes silently excludes nothing, which shows up as a ray
that always hits its own owner. `intersect_shape`, `cast_motion` and
`collide_shape` cover the non-ray cases, all with the same `direct_space_state` +
parameters shape. `hit_from_inside` and `hit_back_faces` decide whether a query starting
inside a shape reports it.

Direct `PhysicsServer` access exists and is the right tool for thousands of queries per
frame, but it bypasses the node layer entirely — no signals, no editor visibility, manual
RID lifetime.

## The physics tick

```
physics/common/physics_ticks_per_second        default 60
physics/common/max_physics_steps_per_frame     default 8
physics/common/physics_interpolation           default false
```

`_physics_process`'s `delta` is exactly `Engine.time_scale /
Engine.physics_ticks_per_second`, so it is constant. Raising the tick rate costs CPU
roughly linearly and improves fast-object accuracy — racing games often do. Dropping
below about 30 breaks physics behaviour and makes input feel laggy.

`max_physics_steps_per_frame` is the guard against the physics spiral of death, where the
simulation cannot keep up, the frame rate drops, more steps are needed, and it collapses
to 1-2 FPS. The cost of the guard is that the game visibly slows down once the render
rate falls below `physics_ticks_per_second / max_physics_steps_per_frame`.

`physics_interpolation` interpolates transforms between the last two physics states so
motion looks smooth when ticks and frames do not line up. It is read only at startup —
change it at runtime through `SceneTree.physics_interpolation` — it disables
`physics_jitter_fix` (the two are incompatible), and it needs
`Node.reset_physics_interpolation()` after any teleport, or the object visibly streaks
across the screen. Per-branch control is `Node.physics_interpolation_mode`.

## Tunnelling

A fast body passes through thin geometry because the solver only sees discrete positions.
Options, in order of preference: make the wall thicker; enable continuous collision
detection on the `RigidBody` (`continuous_cd`); raise the tick rate; or replace the body
with a raycast-driven projectile that queries the swept segment each tick. Bullets are
almost always better as raycasts than as `RigidBody` instances.

## Version gates

| Version | Change |
|---|---|
| `(Godot 4.6+)` | New projects are created with Jolt Physics as the 3D engine; upgraded projects are not |
| `(Godot 4.7)` | `area_mask` default changed from `1` to `0` on **`AudioStreamPlayer2D` and `AudioStreamPlayer3D`** — the plain `AudioStreamPlayer` has no such property, despite how the migration note reads. If you use `audio_bus_override` on an `Area2D`/`Area3D` **and** left the player's mask at the default, the overrides stop working — set it back to layer 1 |
| `(Godot 4.7)`, Jolt only | `WorldBoundaryShape3D` now interprets `plane.d` with Godot's sign convention, the opposite of Godot 4.6 under Jolt. Flip the sign |
| `(Godot 4.7)`, Jolt only | `SoftBody3D` defaults to 1 kg for the whole body instead of 0 (which meant 1 kg per point), and applies `linear_stiffness` differently. Re-tune `linear_stiffness` and `damping_coefficient` |
| `(Godot 4.7)`, Jolt only | `Area3D` now reports overlaps with `SoftBody3D`; exclude them through layers and masks if that is unwanted |
| `(Godot 4.7)` | `PhysicsServer2D.body_set_shape_as_one_way_collision` gained a `direction` parameter, and `CollisionShape2D` gained `one_way_collision_direction` |

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, haxqer-godot -->
