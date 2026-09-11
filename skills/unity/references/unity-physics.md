# Unity built-in 3D physics

Verified against: Unity 6.3 LTS (6000.3).

## Contents

- [The fixed timestep](#the-fixed-timestep)
- [Body types](#body-types)
- [The collision and trigger matrix](#the-collision-and-trigger-matrix)
- [Moving a body correctly](#moving-a-body-correctly)
- [Unity 6 renames](#unity-6-renames)
- [Layers and the collision matrix](#layers-and-the-collision-matrix)
- [Queries](#queries)
- [Tunnelling and continuous collision detection](#tunnelling-and-continuous-collision-detection)
- [Colliders and scale](#colliders-and-scale)
- [Character movement](#character-movement)
- [Determinism and manual simulation](#determinism-and-manual-simulation)
- [2D physics](#2d-physics)
- [Debugging a physics bug](#debugging-a-physics-bug)

## The fixed timestep

Physics advances on its own clock. `Time.fixedDeltaTime` defaults to 0.02 s (50 Hz), and
the engine runs as many `FixedUpdate` + solver steps per frame as needed to catch up, capped
by `Time.maximumDeltaTime`. So in one rendered frame `FixedUpdate` may run zero times or
several.

- Forces, torques, `linearVelocity` writes and `MovePosition`/`MoveRotation` go in
  `FixedUpdate`.
- Input polling goes in `Update`; store the intent in a field and consume it in
  `FixedUpdate`. Reading `Input.GetKeyDown` from `FixedUpdate` misses or repeats presses,
  because the input state is per frame, not per step.
- Camera work goes in `LateUpdate` so it sees the final transforms.
- Set Rigidbody `Interpolate` on anything the player watches: without it a 50 Hz body
  rendered at 120 Hz visibly steps.
- Raising the timestep frequency multiplies solver cost linearly; it is the last knob, not
  the first.

## Body types

There are three meaningful body states, and the vocabulary matters because the message
matrix is expressed in them:

- **static collider** — a collider with no Rigidbody. Cannot move (moving its Transform
  rebuilds the collider and is expensive).
- **dynamic collider** — a collider on a non-kinematic Rigidbody. Driven by the solver.
- **kinematic collider** — a collider on a Rigidbody with `isKinematic = true`. Moved by
  script, pushes nothing by force but reports contacts and carries resting bodies via
  `MovePosition`.

## The collision and trigger matrix

Which callbacks fire is a table, not a guess `[official]`:

**Collision messages** (`OnCollisionEnter/Stay/Exit`) require:

- at least one **dynamic** collider in the pair, and
- the other collider being static, kinematic or dynamic.

So: dynamic↔static ✓, dynamic↔kinematic ✓, dynamic↔dynamic ✓; static↔static ✗,
static↔kinematic ✗, kinematic↔kinematic ✗. Trigger colliders never send collision
messages.

**Trigger messages** (`OnTriggerEnter/Stay/Exit`) occur when:

- a dynamic or kinematic **trigger** collider meets any collider type, or
- a **static trigger** collider meets a dynamic or kinematic collider.

So a static trigger volume and a static collider report nothing. The practical upshot: a
trigger zone that "never fires" almost always has neither side carrying a Rigidbody. Add a
kinematic Rigidbody to the trigger, or to the thing passing through it.

Also note that forces are applied only to colliders that have a physics body (`Rigidbody`
or `ArticulationBody`). When a body hits a static collider, only the body's motion changes.

## Moving a body correctly

| Intent | Do this | Why not the obvious thing |
|---|---|---|
| dynamic body should move | `AddForce`, `AddTorque`, or set `linearVelocity` in `FixedUpdate` | writing `transform.position` teleports it, skipping collision detection and interpolation |
| kinematic platform should carry riders | `MovePosition`/`MoveRotation` in `FixedUpdate` | `transform.position` does not generate the swept motion the solver needs to carry resting bodies |
| teleport a dynamic body | set `transform.position`, then zero `linearVelocity`/`angularVelocity` | leaving the old velocity makes it shoot off on arrival |
| stop a body dead | set both `linearVelocity` and `angularVelocity` to zero | `Sleep()` is a hint and the solver may wake it next contact |

Writing `transform.position` on a Rigidbody every frame from `Update` — the pattern that
looks like it works in the Editor — produces jitter, timestep-dependent speed, and missed
collisions at speed.

## Unity 6 renames

Unity 6 renamed three `Rigidbody` members `[verified]`:

| Old | New |
|---|---|
| `velocity` | `linearVelocity` |
| `drag` | `linearDamping` |
| `angularDrag` | `angularDamping` |

The old names still exist and still compile: each carries
`[Obsolete("Please use Rigidbody.linearVelocity instead. (UnityUpgradable) -> linearVelocity")]`.
They are **warnings**, and the `(UnityUpgradable)` marker means the API Updater rewrites
call sites automatically when it runs. Claims that the old members "do not exist in Unity 6"
are wrong and lead teams to over-budget an upgrade. `ArticulationBody.velocity` moved the
same way. `angularVelocity` was not renamed.

Two more deprecations in the same area: `Physics.autoSimulation` is replaced by
`Physics.simulationMode`, and `Physics.autoSyncTransforms` by an explicit
`Physics.SyncTransforms()` call when you need transforms pushed into the solver.
`[verified]`

## Layers and the collision matrix

- Layers are the cheap way to stop pairs from being considered at all. Prune the Layer
  Collision Matrix (Project Settings > Physics) rather than filtering in callbacks: a
  callback that returns early has already paid for the contact.
- `LayerMask` values in code are **bit masks**, not layer indices. `LayerMask.GetMask("Ground")`
  or `1 << LayerMask.NameToLayer("Ground")`; passing the index directly silently tests the
  wrong layer (index 8 becomes layer 3).
- `Physics.DefaultRaycastLayers` excludes `Ignore Raycast`; `Physics.AllLayers` does not.
- `queryTriggerInteraction` on a query overrides `Physics.queriesHitTriggers`. A raycast
  that "hits nothing" often hit a trigger that the global setting filtered out, or hit the
  trigger you meant to ignore.

## Queries

```csharp
private readonly RaycastHit[] _hits = new RaycastHit[8];   // owned buffer, allocated once

private int GroundHits()
    => Physics.RaycastNonAlloc(transform.position, Vector3.down, _hits, 1.1f, _groundMask);
```

- `Physics.Raycast(out RaycastHit)` returns the **nearest** hit and allocates nothing. Use
  it whenever one hit is enough — which is most of the time.
- `RaycastAll`, `OverlapSphere`, `OverlapBox`, `SphereCastAll` return fresh arrays on every
  call. The `NonAlloc` variants fill a buffer you own and return a count; results beyond
  the buffer length are dropped, so size the buffer and check for saturation.
- `RaycastCommand.ScheduleBatch(NativeArray<RaycastCommand>, NativeArray<RaycastHit>, minCommandsPerJob, maxHits)`
  runs many raycasts across worker threads and returns a `JobHandle` `[verified]`; that is
  the tool for hundreds of queries per frame, not a bigger buffer.
- A raycast that starts inside a collider does not hit it. Offset the origin or exclude the
  own layer, do not increase the distance.
- `Physics.Raycast` does not hit a collider whose GameObject is disabled, and does not hit
  a `MeshCollider` from the back face unless the mesh is double-sided.

## Tunnelling and continuous collision detection

A fast body passes through a thin collider because between two steps it never overlapped.
Options, cheapest first:

1. make the collider thicker, or the body slower;
2. set the Rigidbody's `collisionDetectionMode` to `Continuous` (against static geometry)
   or `ContinuousDynamic` (also against other CCD bodies) — CCD costs measurably more;
3. for bullets, do not simulate at all: `Physics.Raycast` along the travel segment each
   step and never give the projectile a Rigidbody.

## Colliders and scale

- Primitive colliders (box, sphere, capsule) are an order of magnitude cheaper than a
  `MeshCollider`. Approximate with primitives first.
- A non-convex `MeshCollider` cannot be on a moving body; a convex one is capped at 255
  faces and is cooked at import or at runtime (`MeshColliderCookingOptions`).
- Non-uniform scale on a collider — especially capsule and mesh — produces wrong contact
  normals. Keep collider hierarchies at uniform scale and bake scale into the mesh instead.
- Changing a collider's size or a Transform's scale at runtime rebuilds it. Scaling a
  collider every frame is a hidden cost with no Profiler marker of its own.

## Character movement

Three options, in the order most projects should consider them:

1. **`CharacterController`** — a capsule with `Move`/`SimpleMove`, built-in step offset and
   slope limit. Not a Rigidbody: it is not pushed by forces and its callbacks are
   `OnControllerColliderHit`, not `OnCollision*`. Best default for a bipedal player.
2. **Kinematic Rigidbody** with your own collide-and-slide using `CapsuleCast` — full
   control, more code, predictable.
3. **Dynamic Rigidbody** with forces — good for physics-driven games (vehicles, ragdolls,
   Human Fall Flat-likes), bad for precise platforming because the solver fights you.

Do not add a dynamic Rigidbody to a `CharacterController` to "make it physical"; the two
movement models then fight each other every step.

## Determinism and manual simulation

Unity's built-in physics is **not** deterministic across platforms or Unity versions; float
behaviour, solver iteration order and CPU differ. Do not build lockstep multiplayer on it.
Within one build and one platform it is reproducible enough for replays if you also fix the
timestep and the input order.

For turn-based or server-authoritative stepping, set
`Physics.simulationMode = SimulationMode.Script` and call `Physics.Simulate(dt)` yourself.
`Physics.autoSimulation = false` is the deprecated spelling of the same thing.

## 2D physics

2D is a separate engine (`Rigidbody2D`, `Collider2D`, `Physics2D`) with separate settings
and a separate layer matrix. The callbacks are the `*2D` variants and do not interoperate
with 3D: a `Collider` never triggers `OnTriggerEnter2D`. Mixing the two in one project is
fine; mixing them on one object is a bug.

## Debugging a physics bug

1. Which body type is each side? Consult the message matrix before reading code.
2. Is the layer pair even enabled in the Physics collision matrix?
3. Is the motion applied in `FixedUpdate`, and through the solver rather than the
   Transform?
4. Turn on the Physics Debugger (Window > Analysis > Physics Debugger) and look at the
   actual collider shapes — a mis-scaled or offset collider is visible in one glance and
   invisible in code.
5. For "it works at low speed", suspect tunnelling; for "it works in the Editor", suspect
   a frame-rate-dependent write.

<!-- sources: gamedev-unity, nicewolf-unity, unity-official-skills, unity-docs, unity-cs-reference -->
