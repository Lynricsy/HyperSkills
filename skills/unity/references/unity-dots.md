# Unity DOTS: whether to use it, and how

Verified against: Unity 6.3 LTS (6000.3) with `com.unity.entities` 1.x.

## Contents

- [Decide before you architect](#decide-before-you-architect)
- [The three pieces, used separately](#the-three-pieces-used-separately)
- [Vocabulary](#vocabulary)
- [Systems: ISystem versus SystemBase](#systems-isystem-versus-systembase)
- [Queries](#queries)
- [Structural change and the EntityCommandBuffer](#structural-change-and-the-entitycommandbuffer)
- [Baking: GameObjects to entities](#baking-gameobjects-to-entities)
- [Jobs and native collections](#jobs-and-native-collections)
- [Burst](#burst)
- [Chunk utilisation](#chunk-utilisation)
- [Debugging DOTS](#debugging-dots)
- [Interop with GameObjects](#interop-with-gameobjects)

## Decide before you architect

DOTS is worth it when the problem is **mass simulation**: thousands of similar entities
updated every frame, where memory layout and parallelism dominate. It is not worth it for a
game whose entity count is in the hundreds, or whose per-entity logic is complex and
branchy, or whose team has not used it before and is on a deadline.

| | GameObject/MonoBehaviour | DOTS/ECS |
|---|---|---|
| Memory layout | scattered heap objects | contiguous chunks by archetype |
| Update | per object, virtual dispatch | batched over matching chunks |
| Scaling with count | degrades | close to linear |
| Fits | complex, individual behaviour | uniform behaviour over many instances |
| Tooling maturity | complete | improving; Editor workflows are thinner |
| Debuggability | breakpoints, Inspector | Entities Hierarchy, Systems window, Burst inspector |

The realistic and common answer is **hybrid**: keep the game in GameObjects and move the one
subsystem with 20 000 instances (crowd, bullets, foliage, grid simulation) to ECS, or move
only the hot loop to Jobs + Burst without adopting Entities at all. Converting a working
GameObject game to ECS wholesale because ECS is faster is how projects lose a quarter.

## The three pieces, used separately

DOTS is three independent packages, and adoption does not have to be all three:

1. **Burst** (`com.unity.burst`) — compiles annotated jobs to SIMD native code. Usable with
   plain `IJob` and no ECS at all. Cheapest win available.
2. **Jobs / C# Job System** — safe multithreading with a dependency graph, `NativeArray`
   and the safety system. Usable from MonoBehaviours.
3. **Entities** (`com.unity.entities`) — the ECS data model, systems, baking and the
   Entities Graphics renderer. This is the invasive one.

Start at 1, then 2. Only reach 3 when the data model itself is the bottleneck.

## Vocabulary

```
Entity     an id, no data
Component  data, no behaviour (IComponentData = unmanaged struct)
System     logic that runs over components
World      container for entities and systems
Archetype  a distinct set of component types
Chunk      a fixed-size memory block holding entities of one archetype
```

The performance model follows from the last two: a system iterates chunks whose archetype
matches its query, and the per-entity cost is a sequential read over contiguous memory.
Anything that changes an entity's archetype moves it to a different chunk — which is why
structural change is expensive and restricted.

## Systems: ISystem versus SystemBase

Prefer `ISystem`. It is an unmanaged struct, can be Burst-compiled in full, and has no
managed overhead. Use `SystemBase` only when the system itself needs managed state —
holding a `Dictionary`, calling a managed API, or interacting with GameObject-land.

```csharp
[BurstCompile]
public partial struct MoveSystem : ISystem
{
    [BurstCompile]
    public void OnCreate(ref SystemState state)
        => state.RequireForUpdate<SimulationSettings>();

    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        foreach (var (transform, velocity) in
                 SystemAPI.Query<RefRW<LocalTransform>, RefRO<Velocity>>())
        {
            transform.ValueRW.Position += velocity.ValueRO.Value * dt;
        }
    }
}
```

Notes on the shape above:

- the system must be `partial`; source generation supplies the `SystemAPI` plumbing;
- `RefRW<T>` declares a write, `RefRO<T>` a read. Declaring a write you do not perform
  serialises the system against others for nothing;
- `state.RequireForUpdate<T>()` stops `OnUpdate` running before the data exists, which is
  the fix for "my system throws on frame one";
- system update order is controlled by `[UpdateInGroup]`, `[UpdateBefore]`,
  `[UpdateAfter]` — not by class name or file order.

## Queries

- `SystemAPI.Query<...>()` in a `foreach` is the idiomatic per-entity form.
- `EntityQuery` with `WithAll`/`WithAny`/`WithNone` is the explicit form, and the one to use
  when the query is reused, counted, or passed to a job.
- Tag components (empty `IComponentData`) are free filters — one bit of archetype, no data.
  This is the right way to express state (`Dead`, `Stunned`) instead of a bool field, which
  would keep the entity in the same chunk and force a branch.
- Change filtering (`SetChangedVersionFilter`) skips chunks nothing has written to. It
  operates per chunk, not per entity: one write dirties the whole chunk.

## Structural change and the EntityCommandBuffer

Creating or destroying an entity, and adding or removing a component, are **structural
changes**. They invalidate chunk layout, so they cannot happen inside a job and cannot
happen while iterating a query.

Record them into an `EntityCommandBuffer` and let a sync point play them back:

```csharp
var ecb = SystemAPI.GetSingleton<BeginSimulationEntityCommandBufferSystem.Singleton>()
                   .CreateCommandBuffer(state.WorldUnmanaged);

foreach (var (hp, entity) in SystemAPI.Query<RefRO<Health>>().WithEntityAccess())
    if (hp.ValueRO.Value <= 0)
        ecb.DestroyEntity(entity);        // applied at the group's playback point
```

- Pick the ECB system matching when you want the change visible (`BeginSimulation`,
  `EndSimulation`, `BeginFixedStepSimulation`, …). Playback is a sync point — it stalls the
  job graph, so batch changes rather than sprinkling them.
- Inside a parallel job use `ecb.AsParallelWriter()` and pass the chunk index as the sort
  key. Sharing a non-parallel writer across threads is a data race the safety system will
  catch in the Editor and not in a Burst release build.
- `EntityManager.AddComponent`/`DestroyEntity` called directly from `OnUpdate` is a
  structural change *now*: legal outside a job, but it invalidates any query iteration in
  progress.

## Baking: GameObjects to entities

Authoring stays in GameObjects; a subscene is baked into entities.

```csharp
public class EnemyAuthoring : MonoBehaviour { public float speed = 3f; }

public class EnemyBaker : Baker<EnemyAuthoring>
{
    public override void Bake(EnemyAuthoring authoring)
    {
        var entity = GetEntity(TransformUsageFlags.Dynamic);
        AddComponent(entity, new Velocity { Value = authoring.transform.forward * authoring.speed });
    }
}
```

- `TransformUsageFlags` decides which transform components the entity gets. `None` on
  something that moves leaves it without a `LocalTransform` — the usual "my entity exists
  but never renders" bug.
- Bakers must be deterministic and must declare every dependency they read
  (`DependsOn(asset)`), or incremental baking serves stale data.
- Baking runs in the Editor and at build time; a baker that reads `Time` or a random seed
  produces different content per build.

## Jobs and native collections

- Managed types cannot appear in an `IComponentData` intended for Burst or in a job struct.
  A `string`, a `List<T>`, a class reference — each one breaks Burst compilation, which
  falls back to slow managed execution with only a warning.
- `NativeArray`, `NativeList`, `NativeHashMap` require an `Allocator` and must be disposed.
  `Allocator.Temp` is frame-scoped and needs no dispose; `TempJob` must be disposed within
  four frames; `Persistent` must be disposed by you. A leaked persistent collection is
  reported at domain reload, long after the cause.
- Schedule with the dependency handle, complete once: `handle.Complete()` at the point you
  actually need the result, not immediately after scheduling — an immediate `Complete` makes
  the job single-threaded work with extra overhead.
- `[ReadOnly]` on a job field lets several jobs run in parallel over the same data. Omitting
  it serialises them for no reason.

## Burst

- `[BurstCompile]` on the job or system struct, and on the entry-point methods for
  `ISystem`.
- Burst requires unmanaged code: no exceptions in release, no managed allocation, no
  try/catch, no virtual dispatch. Use the Burst Inspector to confirm a method actually
  compiled — the failure mode is a silent fallback, not an error.
- `math` from `Unity.Mathematics` (`float3`, `quaternion`, `math.normalize`) vectorises;
  `UnityEngine.Vector3` and `Mathf` generally do not.
- `[BurstCompile(FloatPrecision.Low, FloatMode.Fast)]` enables reassociation — faster and
  not bit-identical, which matters if you depend on determinism.

## Chunk utilisation

A chunk is a fixed-size block, so the number of entities per chunk depends on the archetype's
component size. Consequences:

- fewer, larger archetypes pack better than many nearly-identical ones. A component added to
  only some entities splits the archetype and halves the iteration density.
- adding or removing components at runtime migrates entities between chunks. Frequent
  toggling is the single most common DOTS performance mistake — use a tag plus enableable
  components (`IEnableableComponent`) instead, which changes a bit rather than the
  archetype.
- the Entities Hierarchy and the Archetypes window show actual chunk utilisation; guessing
  it from the component list is unreliable.

## Debugging DOTS

- **Entities Hierarchy** window: the live entity list per world, with components.
- **Systems** window: system order inside groups and per-system timing — the first place to
  look when a system "does not run" (usually `RequireForUpdate` or a group it is not in).
- **Archetypes** window: chunk counts and utilisation.
- The **safety system** catches races and disposal errors in the Editor. A Burst release
  build does not; anything only reproducible in a build should be re-run in the Editor with
  jobs debugger enabled before you theorise.

## Interop with GameObjects

- Entities Graphics renders entities; a GameObject-based effect attached to an entity does
  not follow it. Bridging needs an explicit sync system copying `LocalTransform` to the
  GameObject's `Transform` (or `CompanionLink` for hybrid components), and that sync is a
  main-thread cost per object.
- Built-in `Physics` does not simulate entities; that is Unity Physics (a separate package)
  with its own colliders and its own query API. Objects in one system do not collide with
  objects in the other.
- Two physics systems, two renderers and two transform hierarchies in one project is a real
  cost. Draw the boundary at one subsystem and keep the bridge one-directional.

<!-- sources: wshobson-unity-ecs, nicewolf-unity, unity-docs -->
