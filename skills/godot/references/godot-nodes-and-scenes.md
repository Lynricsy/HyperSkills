# Nodes, scenes and object lifetime

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`)

## Contents

- [Composition, not inheritance](#composition-not-inheritance)
- [Instancing a scene](#instancing-a-scene)
- [Node naming and why it matters](#node-naming-and-why-it-matters)
- [Reaching other nodes](#reaching-other-nodes)
- [Node path cost, measured](#node-path-cost-measured)
- [Freeing nodes](#freeing-nodes)
- [Autoloads](#autoloads)
- [Changing the running scene](#changing-the-running-scene)
- [`owner` and saving scenes from code](#owner-and-saving-scenes-from-code)
- [`.tscn` structure and hand-editing](#tscn-structure-and-hand-editing)
- [Groups](#groups)

## Composition, not inheritance

A scene is a tree of nodes saved as `.tscn`; loading one yields a `PackedScene` that can
be instanced any number of times. Build small single-purpose scenes (Player, Bullet,
Hurtbox, HealthBar) and compose larger ones from them. Prefer adding a child node with a
narrow job over subclassing a deep chain: a `Hurtbox` scene with its own `Area2D`,
`CollisionShape2D` and script drops into anything, while a `DamageableCharacterBody2D`
base class does not.

Scene inheritance (`New Inherited Scene`) exists and is the right tool when many variants
share a node tree that must stay in sync — enemy variants over one rig, for example.
It is not the right tool for behaviour sharing; a child node or a `Resource` is.

## Instancing a scene

```gdscript
const BULLET := preload("res://bullet.tscn")     # parse time, path must be a constant

func shoot(at: Vector2, dir: Vector2) -> void:
    var bullet := BULLET.instantiate() as Bullet
    bullet.direction = dir                        # setting state before add_child is fine
    add_child(bullet)                             # now it is in the tree and _ready has run
    bullet.global_position = at                   # global_* needs a parent transform
```

`preload` resolves at parse time and blocks the script's load; `load` resolves at runtime
and accepts a variable path. Setting plain fields before `add_child()` is fine, and it is
the only way to have them available inside the child's `_ready()`. `global_position` and
anything else derived from the parent's transform must be set after `add_child()`.

For anything spawned per-frame or per-shot, load the `PackedScene` once into a `const`
and reuse it — `load()` inside a hot path re-hits the resource cache each call.

## Node naming and why it matters

`add_child()` requires unique sibling names, and its default behaviour when there is a
collision is not "append a number":

```gdscript
var a := Node.new(); a.name = "Bullet"
var b := Node.new(); b.name = "Bullet"
var c := Node.new(); c.name = "Bullet"
add_child(a)            # "Bullet"
add_child(b)            # "@Node@3"   <- generated from a per-process counter
add_child(c, true)      # "Bullet2"   <- force_readable_name = true
```

The `@`-prefixed form comes from a counter that depends on how many nodes the process has
created, so it is **not reproducible** between runs or between peers. Anything addressed
by node path — RPCs, `MultiplayerSynchronizer`, saved references — breaks on it. Pass
`force_readable_name = true`, or assign a deterministic name yourself, whenever the path
matters; the class reference notes the readable form is slow, so leave it `false` for
bullets and particles that nothing addresses.

`add_child(node, false, Node.INTERNAL_MODE_FRONT|BACK)` hides a child from
`get_children()` and from duplication. Use it for machinery a user of your scene should
not see or delete.

## Reaching other nodes

```gdscript
@onready var sprite: Sprite2D = $Body/Sprite2D          # fixed child, resolved once
@onready var bar: ProgressBar = %HealthBar              # scene-unique name
var maybe := get_node_or_null("Optional/Thing")         # null instead of an error
```

`$Path` is sugar for `get_node(NodePath)`. It breaks on rename or reparent. A
scene-unique name (`%Name`, set with `Access as Unique Name` on the node) survives both,
because it is resolved through the owning scene's unique-name map rather than by path —
which is also why `%Name` returns `null` on a node whose `owner` is not set, for example
one built with `Node.new()` and never saved into a scene.

Reaching *upward* or *sideways* with a path (`get_parent().get_parent().hud`,
`/root/Main/UI/HUD`) couples a scene to its position in a tree it does not own. Emit a
signal upward instead, or read an autoload. A child that knows its grandparent's path
cannot be tested or reused in another level.

## Node path cost, measured

200,000 lookups of an eight-level path, Godot 4.7.2 headless:

| Access | Total | Per call | Relative |
|---|---|---|---|
| `get_node("L0/L1/.../L7")` (String) | 75.3 ms | 0.377 µs | 45x |
| `get_node(np)` (`NodePath` constant) | 16.5 ms | 0.083 µs | 10x |
| cached reference in a variable | 1.65 ms | 0.008 µs | 1x |

Most of the String cost is the `String` to `NodePath` conversion, which is why a
`NodePath` constant is already 4.6x cheaper than the equivalent string. None of this
matters once per `_ready()`; all of it matters at 60 Hz times the number of nodes doing
it. Resolve paths in `@onready` and hold the reference.

## Freeing nodes

```gdscript
node.free()          # destroyed immediately, on this line
node.queue_free()    # destroyed at the end of the frame, after all deferred calls
```

`free()` is the cause of most intermittent "previously freed instance" crashes, because
the statements after it in the same function still run:

```gdscript
func die() -> void:
    free()
    get_tree().change_scene_to_file("res://ui/game_over.tscn")   # runs on a dead object
    print(get_parent().name)                                      # crash
```

`queue_free()` is safe to call more than once, sets `is_queued_for_deletion()`
immediately, and leaves the node in the tree until it is actually deleted. The timing
matters when awaiting:

```gdscript
n.queue_free()
await get_tree().process_frame
is_instance_valid(n)      # true  - process_frame fires before the deletion
await get_tree().process_frame
is_instance_valid(n)      # false
```

So "queue_free then await one frame then check validity" checks nothing. If you need the
node gone before continuing, await twice, or restructure so the caller does not need to
know. Re-parenting a queued node does not cancel the deletion, and
`enemy.get_parent().remove_child(enemy)` after a `queue_free()` will fail outright if the
node already left the tree.

Signals connected *to* a node are dropped automatically when that node is freed, so a
receiver going away does not need an explicit `disconnect` and emitting afterwards does
not error. The reverse is not true for a `Callable` whose object is a `RefCounted` kept
alive only by the connection.

## Autoloads

Registered in Project Settings > Globals > Autoload; instantiated before the main scene,
in list order, and reachable everywhere by the registered name.

```gdscript
# game_state.gd, registered as "GameState"
extends Node

signal score_changed(value: int)
var score := 0

func add_score(points: int) -> void:
    score += points
    score_changed.emit(score)
```

Two constraints. An autoload cannot depend on the main scene existing, and it cannot
depend on an autoload listed below it. And an autoload is global mutable state: use them
for genuinely process-wide services (persistent game state, audio bus routing, scene
transitions, an event bus), not as a shortcut to avoid passing a reference. Every
autoload is also a node that survives scene changes, so anything it connects to a level's
nodes must be disconnected when that level goes away.

## Changing the running scene

```gdscript
get_tree().change_scene_to_file("res://levels/level_2.tscn")
get_tree().change_scene_to_packed(LEVEL_2)
```

Both are **deferred**: the swap and the old tree's deletion happen at the end of the
current frame. Code after the call still runs against the old tree, and
`get_tree().current_scene` is not the new scene until the next frame. Read the new
scene's nodes from that scene's own `_ready()`.

Either call returns an `Error`: `ERR_CANT_OPEN` if the path will not load,
`ERR_CANT_CREATE` if the scene will not instantiate. Ignoring it turns a typo'd path into
a frozen game with one line on stderr.

## `owner` and saving scenes from code

`PackedScene.pack(root)` only stores nodes whose `owner` is the root being packed.
Nodes added at runtime have `owner == null`, so a scene packed from a runtime tree comes
out containing only the root:

```gdscript
var child := Node2D.new()
root.add_child(child)
child.owner = root          # required, and only valid after add_child
var packed := PackedScene.new()
packed.pack(root)
ResourceSaver.save(packed, "res://generated/level.tscn")
```

## `.tscn` structure and hand-editing

`.tscn` is text, which is good for review but does not mean it is safe to author by hand.
A node's place in the tree comes from its `parent` attribute, relative to the root:

```
[node name="Main" type="Node2D"]
[node name="UI" type="CanvasLayer" parent="."]
[node name="HUD" type="Control" parent="UI"]
[node name="Label" type="Label" parent="UI/HUD"]
```

Writing `parent="."` on every node — the common mistake when generating a scene — loads
with **zero errors** and stacks every `Control` at the origin. Nothing in the engine
flags it. Drive scene edits through `godot --headless --script` and the scene API, or
through the editor; treat text editing of `.tscn` as a last resort for a one-line
property fix.

Two format changes to expect in diffs: `(Godot 4.6+)` no longer writes `load_steps` and
does write per-node unique ids. Both directions load fine, but a scene last saved by 4.5
produces a large diff the first time 4.6 or later saves it.

## Deprecated node types in older scenes

A scene carried forward from an older Godot still instantiates the old node types, with
no error. Two matter, and their gates are different — a single "4.3 deprecations" story
is wrong:

| Node | Replacement | Marked deprecated |
|---|---|---|
| `TileMap` | one `TileMapLayer` per layer | `(Godot 4.3+)` |
| `ParallaxBackground` + `ParallaxLayer` | `Parallax2D` | `(Godot 4.5+)`; `Parallax2D` itself exists from `(Godot 4.3+)` |

So a 4.3 or 4.4 project can legitimately still be on `ParallaxBackground` — it was not
deprecated yet — while `TileMap` was already on notice. `TileMap` has an in-editor
conversion that extracts its layers into `TileMapLayer` nodes; the parallax replacement
is a manual restructure, because `Parallax2D` is a `Node2D` rather than a `CanvasLayer`
and the scroll maths is expressed differently.

## Groups

```gdscript
add_to_group("enemies")
get_tree().get_nodes_in_group("enemies").size()
get_tree().call_group("enemies", "set_paused", true)
```

Groups are global to the `SceneTree`, not per-scene, so two levels using `"enemies"`
share membership — namespace the name if that matters. `call_group` acts on every
matching node immediately, which can stall a frame on a large group, and it **silently
ignores** nodes whose method is missing or whose signature does not match. A typo in the
method name fails quietly, so prefer a typed signal whenever the contract matters.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, haxqer-godot -->
