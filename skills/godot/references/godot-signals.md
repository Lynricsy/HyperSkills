# Signals and groups

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`)

## Contents

- [Direction of a signal](#direction-of-a-signal)
- [Declaring, emitting, connecting](#declaring-emitting-connecting)
- [What a duplicate connection actually does](#what-a-duplicate-connection-actually-does)
- [`Callable` identity](#callable-identity)
- [Connect flags](#connect-flags)
- [Disconnection and lifetime](#disconnection-and-lifetime)
- [Awaiting a signal](#awaiting-a-signal)
- [Event bus versus direct connection](#event-bus-versus-direct-connection)
- [Signals versus calls](#signals-versus-calls)
- [Old patterns](#old-patterns)

## Direction of a signal

A reusable sub-scene emits **upward** and never holds a reference to its listeners; the
parent that instanced it connects. A coin knows it was collected, not that a HUD exists:

```gdscript
# coin.gd
extends Area2D
signal collected(value: int)

func _on_body_entered(body: Node2D) -> void:
    if body.is_in_group("player"):
        collected.emit(10)
        queue_free()
```

```gdscript
# level.gd
func _ready() -> void:
    for coin in get_tree().get_nodes_in_group("coins"):
        coin.collected.connect(_on_coin_collected)
```

A sub-scene that reaches up a node path to find its listener cannot be dropped into a
second level. A signal is not a decoration on that design; it is the design.

## Declaring, emitting, connecting

```gdscript
signal health_changed(current: int, maximum: int)      # typed parameters

health_changed.emit(hp, MAX_HP)                        # 4.x: a method on the signal
health_changed.connect(_on_health_changed)             # 4.x: a Callable, not a name
health_changed.is_connected(_on_health_changed)
health_changed.disconnect(_on_health_changed)
health_changed.get_connections()                       # Array[Dictionary]
```

Argument count and types must match the declaration; emitting with the wrong count
raises `Error calling from signal 'x' to callable: ...: Method expected N argument(s),
but called with M` at emit time, not at connect time. Declaring the parameter types puts
the failure in the editor's diagnostics instead of in a playtest.

## What a duplicate connection actually does

The widely repeated claim is that connecting twice makes the handler run twice. That is
true only for a specific case. For the same `Callable`, the engine refuses:

```gdscript
var e1 := ping.connect(_on_ping)   # 0   (OK)
var e2 := ping.connect(_on_ping)   # 31  (ERR_INVALID_PARAMETER)
# ERROR: Signal 'ping' is already connected to given callable
#        'Node(main.gd)::_on_ping' in that object.
ping.get_connections().size()      # 1
ping.emit(1)                       # handler runs once
```

So a `_ready()` that re-connects a method after the node is re-added produces a noisy
error log and correct behaviour — annoying, not a bug. What genuinely stacks is a
`Callable` that is **built fresh on each call**:

```gdscript
ping.connect(func(_n): hits += 1)
ping.connect(func(_n): hits += 1)
ping.get_connections().size()      # 2   <- two distinct Callable objects
ping.emit(1)                       # hits == 2
```

Two lambdas with identical text are two objects. Bound callables, by contrast, compare
equal by target plus bound arguments, so the engine does deduplicate them:

```gdscript
ping.connect(_on_ping.bind(0))     # 0
ping.connect(_on_ping.bind(0))     # 31, rejected
```

The review rule follows directly: guard lambda and closure connections with your own
bookkeeping (or connect them once, from a place that runs once); do not bother guarding
method connections, and do not report them as duplicate-handler bugs.

## `Callable` identity

| Form | Equality | Deduplicated by `connect` |
|---|---|---|
| `_on_x` (method on `self`) | object + method name | yes |
| `other._on_x` | object + method name | yes |
| `_on_x.bind(1)` | target + bound args | yes |
| `func(a): ...` | object identity | **no** |
| `Callable(self, "_on_x")` | object + method name | yes |

`bind()` **appends** arguments after the signal's own, so binding onto a handler that
already takes every signal argument produces an arity error at emit time:

```gdscript
$RedButton.pressed.connect(_on_button.bind("red"))
func _on_button(color: String) -> void: ...        # pressed has no args, so one arg total
```

## Connect flags

```gdscript
$Door.opened.connect(_on_opened, CONNECT_ONE_SHOT)
$Bus.changed.connect(_on_changed, CONNECT_DEFERRED)
$Hp.changed.connect(_on_changed, CONNECT_REFERENCE_COUNTED)
```

| Flag | Effect |
|---|---|
| `CONNECT_DEFERRED` | The callable runs on idle time at the end of the frame rather than inside the emit. Use it when the handler mutates the tree (`add_child`, `queue_free`) during a physics callback |
| `CONNECT_ONE_SHOT` | Disconnects itself after the first emission |
| `CONNECT_PERSIST` | The connection is serialised into the scene file |
| `CONNECT_REFERENCE_COUNTED` | The only way to register the same `Callable` twice. It still fires **once** per emission; the connection survives until as many `disconnect` calls as `connect` calls have happened |

`CONNECT_REFERENCE_COUNTED` exists for library code that cannot know whether a caller
already connected. It is not a fix for a double-connect bug — it hides the bug and
changes the disconnect arithmetic.

## Disconnection and lifetime

A connection is dropped automatically when the **connected object** is freed, so a
listener node going away needs no explicit `disconnect`, and emitting afterwards does not
error:

```gdscript
boom.connect(Callable(recv, "hit"))
boom.get_connections().size()    # 2
recv.free()
boom.get_connections().size()    # 1
boom.emit()                      # no error
```

Explicit `disconnect` is still needed in three cases: a listener that outlives the thing
it listens to and must stop reacting (a paused menu, an autoload connected to a level), a
connection whose `Callable` targets a `RefCounted` or a lambda capturing one — the
connection is what keeps it alive — and anything connected inside a loop where you cannot
prove the loop runs once.

Connecting to an already-freed object errors immediately; check `is_instance_valid()`
before connecting to anything you did not just create.

## Awaiting a signal

```gdscript
$AnimationPlayer.play("open")
await $AnimationPlayer.animation_finished
spawn_loot()
```

There is no built-in timeout. For "whichever comes first", race the signal against a
timer with a one-shot connection and a flag, or restructure to an explicit state machine.
And check validity after the `await`: if the emitter was freed while suspended, the
coroutine never resumes, and code that assumed it did silently stops running.

## Event bus versus direct connection

Direct connection is the default: parent connects to child, one hop, visible in the
scene. An autoload event bus is the escape hatch for events that genuinely cross scene
boundaries (run finished, settings changed, achievement unlocked).

The cost of a bus is that the connection graph disappears from the scene tree, so nothing
tells you who listens. Keep bus signals few and coarse, name them as facts rather than
commands (`run_finished`, not `show_game_over`), and never route a per-frame value
through one.

## Signals versus calls

A signal is right when the emitter should not know the listener, when there may be zero
or many listeners, or when the event is genuinely asynchronous. A direct call is right
when there is exactly one collaborator, when you need a return value, and when the order
of effects matters — an emit gives no ordering guarantee across listeners beyond
connection order, and `CONNECT_DEFERRED` breaks even that.

Groups are the broadcast form of the same idea, with a weaker contract: `call_group`
silently ignores nodes whose method is missing or mismatched, so it is fine for "pause
everything" and wrong for anything whose failure you need to notice.

## Old patterns

<details>
<summary>Godot 3.x signal API</summary>

```gdscript
# 3.x
connect("died", self, "_on_died")
emit_signal("died", cause)
yield(self, "died")
disconnect("died", self, "_on_died")

# 4.x
died.connect(_on_died)
died.emit(cause)
await died
died.disconnect(_on_died)
```

`Object.connect("died", Callable(self, "_on_died"))` still works; the three-argument
string form does not. `emit_signal("died")` also still works, but `died.emit()` is
checked at parse time, which is the point.

</details>

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, wshobson-godot -->
