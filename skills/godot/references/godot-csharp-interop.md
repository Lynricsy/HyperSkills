# C# bindings: where they differ from GDScript

Verified against: Godot 4.7 .NET, .NET 8. `[official]` throughout — this machine has the
standard (non-.NET) editor build, so none of it was executed here.

Scope: only the ways Godot's C# surface differs from GDScript and from ordinary C#. The C#
language itself, the .NET SDK, MSBuild, NuGet, analyzers and general .NET project layout
belong to the `csharp-dotnet` skill.

## Contents

- [Prerequisite](#prerequisite)
- [`partial` is mandatory](#partial-is-mandatory)
- [Lifecycle names and delta type](#lifecycle-names-and-delta-type)
- [`[Export]`](#export)
- [`[Signal]` and events](#signal-and-events)
- [Node access](#node-access)
- [Structs are value types](#structs-are-value-types)
- [Collections](#collections)
- [`await` and signals](#await-and-signals)
- [Lifetime and disposal](#lifetime-and-disposal)
- [Calling into GDScript](#calling-into-gdscript)
- [Logging](#logging)
- [What does not change](#what-does-not-change)
- [Platform limits](#platform-limits)

## Prerequisite

C# needs the **.NET editor build** plus a matching .NET SDK. The standard build cannot
run C# at all — there is no error that says so clearly; scripts simply do not attach.
Creating the first `.cs` script generates the `.csproj`/`.sln`. Build from the editor or
with `dotnet build`; the editor does not hot-reload C# the way it reloads GDScript, so a
change needs a build and usually a scene reload.

## `partial` is mandatory

```csharp
using Godot;

public partial class Player : CharacterBody2D
{
}
```

Every class that extends a Godot type must be `partial`, because a source generator emits
the other half (`SignalName`, `PropertyName`, `MethodName`, the signal events, the
marshalling glue). Omit it and `[Export]` and `[Signal]` fail with build errors that point
at the generated code rather than at the missing keyword. The file name should match the
class name.

## Lifecycle names and delta type

| GDScript | C# |
|---|---|
| `_ready()` | `public override void _Ready()` |
| `_process(delta: float)` | `public override void _Process(double delta)` |
| `_physics_process(delta: float)` | `public override void _PhysicsProcess(double delta)` |
| `_enter_tree()` / `_exit_tree()` | `_EnterTree()` / `_ExitTree()` |
| `_input(event)` | `_Input(InputEvent @event)` |
| `_init()` | the constructor |

PascalCase, and `delta` is `double`, not `float`. A misspelled or mis-cased override is
not an error — it is simply never called, which presents as "my script does nothing".
`double` also means most vector maths needs an explicit `(float)delta` cast, and
forgetting it is a compile error rather than a silent bug, so that one is self-correcting.

`_Ready()` keeps GDScript's semantics exactly: children first, and at most once per node,
so a pooled node needs `RequestReady()` before being re-added.

## `[Export]`

```csharp
[Export] public float Speed = 220.0f;
[Export(PropertyHint.Range, "0,100,1")] public int MaxHp = 100;
[Export] public PackedScene BulletScene { get; set; }
[ExportGroup("Combat")]
[Export] public int AttackDamage = 10;
```

Fields and auto-properties both work; the type must be one the engine can marshal.
A custom `Resource` or `Node` type must be a `partial` class registered as a global class
for the Inspector to offer it, the same requirement `class_name` satisfies in GDScript.

The sharing trap from GDScript applies unchanged: an exported `Resource` assigned in the
Inspector is one object shared by every instance of the scene. `ResourceLocalToScene` on
the resource, or `Duplicate()` per instance, are the same two fixes.

## `[Signal]` and events

```csharp
[Signal] public delegate void HealthChangedEventHandler(int current, int max);

public override void _Ready() => HealthChanged += OnHealthChanged;

private void Raise(int hp) => EmitSignal(SignalName.HealthChanged, hp, MaxHp);
```

The delegate name **must** end in `EventHandler`; the engine exposes the signal under the
name without that suffix, and the generator creates both a C# `event` and a
`SignalName.X` constant. Use `SignalName.X` rather than a string literal — it avoids
allocating a `StringName` per call and it is checked at compile time.

The GDScript duplicate-connection rules still hold underneath: `Connect` with the same
`Callable` is rejected, while a fresh lambda is a new `Callable` and stacks. C# `event`
subscription (`+=`) has the same problem in its own right — `+=` in `_Ready()` or
`_EnterTree()` without a matching `-=` in `_ExitTree()` stacks handlers across scene
reloads.

## Node access

```csharp
private AnimatedSprite2D _sprite;

public override void _Ready()
{
    _sprite = GetNode<AnimatedSprite2D>("AnimatedSprite2D");
    var bar = GetNode<ProgressBar>("%HealthBar");       // scene-unique name
    var maybe = GetNodeOrNull<Label>("Optional/Label");
}
```

There is no `@onready`, so `_Ready()` is where node references are cached — and caching
them is not optional: the measured per-frame cost of resolving a node path applies to C#
as well. `[Export] public Node2D Target;` wired in the Inspector avoids the path
entirely and is the better default for cross-scene references.

## Structs are value types

`Vector2`, `Vector3`, `Color`, `Transform2D`, `Quaternion` and `Rect2` are C# structs, so
a property returning one returns a **copy**:

```csharp
Velocity.X = 100;                 // does not compile: cannot modify the return value
Vector2 v = Velocity;             // copy
v.X = 100;
Velocity = v;                     // write it back
```

The same applies to `GlobalPosition`, `Scale` and anything else exposed as a struct
property. In GDScript these read as mutable because the engine special-cases the
assignment; in C# they do not.

## Collections

`Godot.Collections.Array<T>` and `Godot.Collections.Dictionary<TKey, TValue>` are
engine-backed and marshal across the boundary. `System.Collections.Generic.List<T>` does
not — it cannot be exported, cannot be sent through a signal, and cannot be an RPC
argument. Use the `Godot.Collections` types at the boundary and plain .NET collections
inside your own code, converting explicitly at the edge; the conversion copies.

`StringName` and `NodePath` have implicit conversions from `string`, which allocates each
time. In a hot path use the generated `SignalName`/`PropertyName`/`MethodName` constants
or cache a `StringName` in a `static readonly` field.

## `await` and signals

```csharp
await ToSignal(GetTree().CreateTimer(0.2), Timer.SignalName.Timeout);
await ToSignal(_anim, AnimationPlayer.SignalName.AnimationFinished);
```

`ToSignal` returns an awaitable. `async void` is as dangerous here as anywhere in .NET —
an exception in one is unobservable — so prefer `async Task` and await it, or keep the
continuation in a signal handler. Awaiting inside `_Ready()` has the same consequence as
in GDScript: `_Ready()` returns immediately and the rest of the tree continues.

## Lifetime and disposal

`QueueFree()` and `Free()` behave exactly as in GDScript: `Free()` destroys immediately,
`QueueFree()` defers to the end of the frame, and one frame of waiting is not enough for
the instance to be gone. C# adds a second failure mode: touching a freed object throws
`ObjectDisposedException` rather than printing an engine error, and a C# reference keeps
the wrapper alive while the native object is gone. `GodotObject.IsInstanceValid(obj)` is
the check.

An `IDisposable` that wraps engine resources (`Image`, `FileAccess`, RIDs) still needs
disposing; the GC does not know about native lifetimes.

## Calling into GDScript

```csharp
Node gd = GetNode("GDScriptNode");
gd.Call("take_damage", 10);
int score = (int)gd.Get("score");
gd.Set("score", score + 5);
gd.Connect("died", Callable.From(OnDied));
```

`Call`/`Get`/`Set` are dynamic and unchecked: a renamed GDScript method is a runtime
error, not a build error. Keep the boundary narrow and typed — a GDScript node that
emits signals with primitive payloads, consumed by C#, is far more maintainable than
mutual `Call` chains. Note the direction limit: a GDScript script cannot see a C# type by
`class_name` unless that C# class is registered as a global class.

## Logging

`GD.Print` and `GD.PrintErr` reach Godot's output panel and the engine log.
`Console.WriteLine` may not appear at all depending on the host. Use `GD.PushError` and
`GD.PushWarning` for anything that should show up in the editor's diagnostics.

## What does not change

Everything engine-level is language-neutral and is covered by the other references here:
the scene tree and node lifetime rules, the `Container` layout ownership rules,
`mouse_filter` defaults, collision layers and masks, `move_and_slide()` belonging to the
physics tick, `Velocity` already being per-second, renderer selection, `res://` being
unwritable in an export, and multiplayer authority and `@rpc` id ordering (`[Rpc]` in C#,
with the same sorted-name id mechanism). Translating a defect from GDScript to C# does not
fix it.

## Platform limits

The .NET builds need their own export templates, and platform support for .NET lags the
standard build — check the current platform notes before promising a target. Web and some
AOT targets in particular have extra requirements or are unsupported depending on the
release. Android needs the .NET SDK tooling that matches the engine's target framework.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, godot-prompter -->
