# High-level multiplayer

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`). API shapes and the RPC
wire mechanism were read from the engine source and class reference; two-peer behaviour
was not reproduced on this machine, so it is marked `[official]`.

## Contents

- [Peers and ids](#peers-and-ids)
- [Authority](#authority)
- [`@rpc`](#rpc)
- [How an RPC is actually routed](#how-an-rpc-is-actually-routed)
- [What an RPC can carry](#what-an-rpc-can-carry)
- [Node names must match across peers](#node-names-must-match-across-peers)
- [Replication](#replication)
- [The server-authoritative shape](#the-server-authoritative-shape)
- [Transfer modes and channels](#transfer-modes-and-channels)
- [Authentication](#authentication)
- [Disconnecting](#disconnecting)
- [What high-level multiplayer is not for](#what-high-level-multiplayer-is-not-for)

## Peers and ids

```gdscript
const PORT := 7000
const MAX_PLAYERS := 8

func host() -> Error:
    var peer := ENetMultiplayerPeer.new()
    var err := peer.create_server(PORT, MAX_PLAYERS)
    if err != OK:
        return err
    multiplayer.multiplayer_peer = peer
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)
    return OK

func join(ip: String) -> Error:
    var peer := ENetMultiplayerPeer.new()
    var err := peer.create_client(ip, PORT)
    if err != OK:
        return err
    multiplayer.multiplayer_peer = peer
    return OK
```

The server is always peer id **1**; clients get random positive ids.
`multiplayer.get_unique_id()` is this peer's id, and inside an RPC body
`multiplayer.get_remote_sender_id()` is the caller's. Outside an RPC it returns 0, so a
helper that reads it from ordinary code is reading nothing.

Signals on `multiplayer`: `peer_connected(id)`, `peer_disconnected(id)`,
`connected_to_server`, `connection_failed`, `server_disconnected`. Check the `Error`
returns from `create_server`/`create_client` — an unchecked failure leaves
`multiplayer_peer` set to a dead peer and every later RPC fails with
`Trying to call an RPC while no multiplayer peer is active` or a connection error.

## Authority

Authority is per node, and it must be derived from something **identical on every peer**.
The spawner names the avatar after the owning peer, and every peer computes the same
answer from the name:

```gdscript
func _ready() -> void:
    set_multiplayer_authority(name.to_int())     # name was set by the spawner

func _physics_process(_delta: float) -> void:
    if not is_multiplayer_authority():
        return
    velocity = Input.get_vector("left", "right", "up", "down") * SPEED
    move_and_slide()
```

The common mistake is `set_multiplayer_authority(multiplayer.get_unique_id())` in
`_ready()`. The script runs on every peer for every avatar, so each peer claims authority
over all of them locally. Everyone then thinks they own everything, and every client
happily drives every avatar.

Three properties of `set_multiplayer_authority()` from the class reference:

- It defaults to peer 1.
- `recursive` defaults to `true`, so it re-parents authority for the whole existing
  subtree — but a child **added later** does not inherit it.
- It does **not** replicate itself. Other peers do not learn about the change unless you
  tell them, through `MultiplayerSpawner.spawn_function`, an RPC, or a
  `MultiplayerSynchronizer`.

## `@rpc`

```gdscript
@rpc("any_peer", "call_local", "reliable", 0)
func request_fire(target_path: NodePath) -> void:
    if not multiplayer.is_server():
        return
    var sender := multiplayer.get_remote_sender_id()
    ...
```

| Argument | Values | Default |
|---|---|---|
| mode | `"authority"`, `"any_peer"` | `"authority"` |
| sync | `"call_remote"`, `"call_local"` | `"call_remote"` |
| transfer | `"reliable"`, `"unreliable"`, `"unreliable_ordered"` | `"reliable"` |
| channel | integer | `0` |

Two defaults cause most confusion. `"authority"` means a non-authority caller's call is
simply **not executed** on the receiver — an error is printed on whichever side can detect
it, which may be the sender or the remote. And `"call_remote"` means `rpc()` does not run
the function on the caller, so a listen-server host that is also a player sees nothing
happen locally; that is what `"call_local"` is for.

Call sites:

```gdscript
some_method.rpc(args)          # every connected peer (plus self with call_local)
some_method.rpc_id(1, args)    # only the server
some_method.rpc_id(0, args)    # every peer except self
```

`@rpc` methods must be on `Node`-derived classes; on a `Resource` or `RefCounted` they do
nothing.

## How an RPC is actually routed

This is the part no prose documentation states, and it explains the "a completely
different function ran" class of bug.

The engine builds the node's RPC config, sorts the method names, and assigns each one a
`uint16` id equal to its **position in that sorted list**. The packet carries that id,
not the name. So adding, removing or renaming **any** `@rpc` method in a script shifts
the ids of every method that sorts after it. Two peers built from different source
therefore agree on the id and disagree on which function it means, and if the argument
count happens to match, the wrong function just runs.

The only guard is a checksum carried once, in the packet that establishes a node-path
cache entry: `get_rpc_md5()` concatenates the method names in id order and takes the MD5.
On mismatch the receiver prints

```
ERROR: The rpc node checksum failed. Make sure to have the same methods on both nodes. Node path: <path>
```

and **keeps running**. It is a print, not a failure — so the session continues with
mismatched dispatch. Treat that line as fatal in your own logging, and make "all peers
run the same build" an explicit deployment invariant rather than an assumption.

## What an RPC can carry

Arguments are serialised as plain data: `int`, `float`, `String`, `StringName`,
`NodePath`, `Vector*`, `Color`, `Array`, `Dictionary` and the `Packed*Array` types.
`Object`, `Node`, `Resource` and `Callable` cannot be encoded. Passing a node is a
guaranteed encode failure:

```gdscript
@rpc("authority", "call_local", "reliable")
func award_kill(victim: Node) -> void: ...     # cannot work

@rpc("authority", "call_local", "reliable")
func award_kill(victim_peer_id: int) -> void: ...   # send the id, resolve locally
```

Keep payloads small. Reliable ENet packets are re-sent until acknowledged, so a large
dictionary broadcast every tick both costs bandwidth and head-of-line-blocks the channel.

## Node names must match across peers

RPC routing and `MultiplayerSynchronizer` both address nodes by path, so the paths must
be identical on every peer. `add_child(node)` does not guarantee that: on a name
collision the engine replaces the name with a generated `@`-prefixed one derived from a
per-process counter.

```gdscript
add_child(a)            # "Bullet"
add_child(b)            # "@Node@3"   <- depends on how many nodes this process made
add_child(c, true)      # "Bullet2"
```

So spawn replicated nodes through `MultiplayerSpawner`, or with
`add_child(node, true)` after assigning a deterministic name (the owning peer id is the
conventional choice for avatars).

## Replication

`MultiplayerSpawner` sits on the parent node, lists the scenes it may spawn, and
auto-instantiates them on clients when the authority adds one under its spawn path. Use
`spawn_function` when a spawn needs custom data — the return value is what gets added, and
the argument is replicated to the clients.

`MultiplayerSynchronizer` is a child of the node being replicated and lists the properties
to sync in its `SceneReplicationConfig`. Each property has a spawn flag (sent once, with
the spawn) and a sync flag (sent continuously). This is the right tool for transform and
animation state; a per-tick RPC broadcasting position is not.

```gdscript
@onready var sync: MultiplayerSynchronizer = $MultiplayerSynchronizer

func _ready() -> void:
    sync.set_visibility_for(other_peer_id, false)   # hide this node's state from one peer
```

Visibility filters (`set_visibility_for`, `add_visibility_filter`) are how you avoid
sending a peer information it should not have — fog of war, hidden hands, another team's
positions. Anything a client is sent, a modified client can read.

## The server-authoritative shape

Clients send **intent**; the server validates, mutates and broadcasts **results**.

```gdscript
# Client side: ask.
func fire() -> void:
    if is_multiplayer_authority():
        request_fire.rpc_id(1, aim_direction)

# Server side: decide.
@rpc("any_peer", "call_local", "reliable")
func request_fire(direction: Vector2) -> void:
    if not multiplayer.is_server():
        return                                   # a client received it: ignore
    var sender := multiplayer.get_remote_sender_id()
    if not _owns_this_avatar(sender) or not _can_fire(sender):
        return
    _spawn_projectile(sender, direction)         # replicated by MultiplayerSpawner

# Results: authority-only, so a client calling it is ignored.
@rpc("authority", "call_local", "reliable")
func apply_damage(amount: int) -> void:
    hp -= amount
```

Every `"any_peer"` method is an entry point an arbitrary client can call with arbitrary
arguments. The checklist for each one: does it verify `multiplayer.is_server()`, does it
verify the sender owns the thing being acted on, and does it validate the arguments? A
script where damage, score and death are all `"any_peer"` with no checks lets any client
kill anyone and set any score — which is the same defect three times, not three defects.

Never let a client be the source of truth for position either: accepting a client's
position lets it teleport. Accept input, simulate on the server, and reconcile.

## Transfer modes and channels

| Mode | Use for |
|---|---|
| `reliable` | Anything whose loss changes the game state: spawns, damage, score, chat |
| `unreliable` | High-frequency state that the next packet supersedes: transforms |
| `unreliable_ordered` | The same, but never applied out of order |

Plain `unreliable` packets can arrive out of order, so putting authoritative state such
as health in an unreliable packet lets a late packet resurrect a stale value. Split the
channels: transforms unreliable, state changes reliable. `channel` separates streams so a
large reliable transfer does not block small frequent ones.

## Authentication

`SceneMultiplayer.auth_callback` plus `complete_auth()` runs a handshake before a peer is
considered connected, with `auth_timeout` bounding it. Use it for a session token check;
without it, anything that can reach the port is a player. `peer_authenticating` and
`peer_authentication_failed` are the signals to observe.

## Disconnecting

```gdscript
func leave() -> void:
    multiplayer.multiplayer_peer.close()
    multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
```

Setting `multiplayer_peer` to `null` leaves the API in a state where every RPC errors.
`OfflineMultiplayerPeer` is the documented "single player again" state, and it makes
`is_multiplayer_authority()` true everywhere so single-player code paths work unchanged.

Android builds need the `INTERNET` permission in the export preset or all networking is
silently blocked.

## What high-level multiplayer is not for

It is a scene-tree replication layer over ENet. It is not a lobby service, not a NAT
traversal solution, and not a rollback netcode framework. Split-screen needs no
networking at all. Raw protocol work (`PacketPeerUDP`, `WebSocketPeer`, `StreamPeerTCP`)
and HTTP are separate APIs and do not interact with `@rpc`.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot -->
