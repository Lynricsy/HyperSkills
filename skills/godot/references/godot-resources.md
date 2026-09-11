# Resources, data and save files

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`)

## Contents

- [What a Resource is for](#what-a-resource-is-for)
- [Writing a custom Resource](#writing-a-custom-resource)
- [The sharing trap](#the-sharing-trap)
- [`duplicate()` is shallow](#duplicate-is-shallow)
- [Design data versus instance state](#design-data-versus-instance-state)
- [`load`, `preload`, and the cache](#load-preload-and-the-cache)
- [`.tres` versus `.res`](#tres-versus-res)
- [Save files: never `res://`](#save-files-never-res)
- [Loading untrusted data](#loading-untrusted-data)
- [UIDs and moving files](#uids-and-moving-files)

## What a Resource is for

A `Resource` is a reference-counted data object that can be saved to a file, shared by
many nodes, and edited in the Inspector. Everything data-shaped in Godot is one:
`Texture2D`, `Mesh`, `Material`, `AudioStream`, `Animation`, `Theme`, `Curve`,
`PackedScene`.

Defining your own is the engine's answer to data-driven design: an `EnemyProfile`
resource with a `.tres` per enemy type gives designers Inspector editing, version
control on text files, and no parallel spreadsheet. The alternative — a giant
`Dictionary` constant or a JSON file — gives up type checking and the Inspector.

## Writing a custom Resource

```gdscript
# enemy_profile.gd
class_name EnemyProfile
extends Resource

@export var display_name: String = ""
@export var max_hp: int = 20
@export_range(0.0, 100.0) var damage: float = 5.0
@export var loot: Array[LootEntry] = []
```

`class_name` is required for the Inspector to offer the type when assigning to an
`@export var profile: EnemyProfile` — without it, a less specific type is exported. That
registration lives in `.godot/global_script_class_cache.cfg`, written by the editor's
filesystem scan, so a fresh clone needs `godot --headless --import` before anything can
resolve `EnemyProfile`.

`_init()` with required parameters breaks `duplicate()`, which the class reference calls
out explicitly. Give every parameter a default.

## The sharing trap

An exported `Resource` property whose value is an external `.tres` points at **one**
loaded object. Every `PackedScene.instantiate()` gets a reference to that same object:

```gdscript
var scene := load("res://enemies/grunt.tscn") as PackedScene
var a := scene.instantiate()
var b := scene.instantiate()
a.profile == b.profile     # true, same instance id
a.profile.max_hp = 1
b.profile.max_hp           # 1
```

Consequences, in order of how much damage they do:

1. Mutating one instance's profile mutates every instance, including ones already
   spawned.
2. In the editor, the mutated resource is the project file, so the change is written back
   to the `.tres` on save — the values survive a restart and show up as a spurious diff.
3. Because the editor and the export behave the same way here, the bug looks like "our
   difficulty reset is broken" rather than "we are editing our own design data".

Two fixes, and they are not equivalent:

```gdscript
# 1. On the resource: every scene instance using it gets its own duplicate.
#    Inspector checkbox "Local to Scene"; in the .tres:
#    resource_local_to_scene = true
# 2. In code, per instance:
enemy.profile = enemy.profile.duplicate()
```

`resource_local_to_scene` is the declarative fix and applies to every user of that
resource. It is read at instantiation, so changing it at runtime does not affect
duplicates that already exist. The code fix is explicit and local, and is the right one
when only some call sites need a private copy.

Note what is **not** affected: a script-level default such as
`@export var stats: Stats = Stats.new()` evaluates the default expression once per
instance, so those are already distinct. The trap is specifically the Inspector-assigned
external resource.

## `duplicate()` is shallow

`Resource.duplicate()` copies exported and storage properties. By default it is
**shallow**: nested `Array`, `Dictionary` and `Resource` properties are not copied and
stay shared with the original. So duplicating an `EnemyProfile` that holds
`loot: Array[LootEntry]` gives a private profile with a shared loot array.

Pass `true` for a deep copy of arrays, dictionaries and packed arrays; nested resources
are only duplicated if they are local, which is what `duplicate_deep()` and the
`DEEP_DUPLICATE_*` modes control. Properties flagged
`PROPERTY_USAGE_ALWAYS_DUPLICATE`/`NEVER_DUPLICATE` override all of it.

Also: plain `var` fields are not exported and therefore **not** copied by `duplicate()`.
`@export_storage var x` is serialised and copied without appearing in the Inspector,
which is the annotation for internal state that must survive a duplicate.

## Design data versus instance state

Fix the sharing and one problem remains: current health does not belong on a shared
design resource at all.

```gdscript
# enemy.gd
@export var profile: EnemyProfile          # read-only at runtime
var hp: int                                # per-instance

func _ready() -> void:
    hp = profile.max_hp
```

Treat a design resource as immutable once the game is running. If a runtime system needs
to scale difficulty, it writes to the node, or the spawner hands the node a computed
value — it does not edit the profile. This rule removes a whole class of bug, because a
mutation that cannot happen needs no `local_to_scene` reasoning.

## `load`, `preload`, and the cache

| Form | When | Path |
|---|---|---|
| `preload("res://x.tscn")` | Parse time; blocks the script's own load | must be a constant |
| `load("res://x.tscn")` | Runtime | may be a variable |
| `ResourceLoader.load_threaded_request/get` | Runtime, off the main thread | variable |

`load()` returns the cached instance when the resource is already loaded, which is
exactly why the sharing trap exists. `ResourceLoader.load(path,
"", ResourceLoader.CACHE_MODE_IGNORE)` bypasses the cache when you deliberately want a
separate copy of a file-backed resource.

Put anything spawned repeatedly in a `const` with `preload` so the hot path holds a
reference instead of re-entering the loader. Use threaded loading for level transitions —
a synchronous `load()` of a large scene is a visible hitch.

## `.tres` versus `.res`

`.tres`/`.tscn` are text: diffable, mergeable, reviewable. `.res`/`.scn` are binary:
smaller and faster to parse. Default to text in source control; the exporter converts
to binary for the pack anyway when the project setting for it is enabled.

`(Godot 4.6+)` `.tscn`/`.tres` no longer store `load_steps` and do store per-node unique
ids, which makes refactoring more robust and produces one large diff the first time a
4.5-era file is saved.

## Save files: never `res://`

`res://` is the project. In an exported build it is a read-only pack — but the failure
mode is not an error:

```gdscript
# Exported build, Godot 4.7.2, Linux:
var f := FileAccess.open("res://save.json", FileAccess.WRITE)
f != null                         # true
FileAccess.get_open_error()       # 0  (OK)
f.store_string(payload)           # appears to work
FileAccess.get_file_as_string("res://save.json")   # still the packed bytes
ProjectSettings.globalize_path("res://")           # ""  (empty string)
```

The bytes land in a file relative to the process working directory, and every read still
resolves to the pack, so the save is a silent no-op. In the editor the same code works
perfectly, because there `res://` *is* the project directory — which is why this defect
always reaches a release build.

```gdscript
const SAVE_PATH := "user://save.json"        # the only writable location

func save(data: Dictionary) -> Error:
    var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if f == null:
        return FileAccess.get_open_error()
    f.store_string(JSON.stringify(data))
    return OK
```

`user://` maps to the OS application-data directory; `OS.get_user_data_dir()` prints
where. In a container or sandbox it follows `XDG_DATA_HOME`, so set that to a
project-local directory in CI or `user://` writes fail.

## Loading untrusted data

`ResourceLoader.load()` on a `.tres` instantiates whatever the file says, including
scripts, so loading a player-supplied or downloaded resource is arbitrary code execution.
Save game state as JSON or as a `ConfigFile` of primitives and rebuild the objects
yourself, or use `ResourceLoader.load(path, "", CACHE_MODE_IGNORE)` only on files you
produced. `var2str`/`str_to_var` round-trips are safe only with
`allow_objects = false`, which is the default and must stay that way for untrusted input.

## UIDs and moving files

Resources carry a `uid://` identifier, and scenes reference dependencies by UID as well
as by path, so moving a file inside the editor keeps references intact. Moving it with
`mv` outside the editor breaks the `.uid` sidecar association — either move files from
the FileSystem dock, or re-run `godot --headless --import` and check for missing-
dependency errors afterwards.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, abagames-headless-godot -->
