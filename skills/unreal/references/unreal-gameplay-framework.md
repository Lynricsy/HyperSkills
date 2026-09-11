# Gameplay Framework, lifecycle and ticking (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]`; nothing
in this file was checked against a running engine.

## Contents

- [Who owns what](#who-owns-what)
- [Choosing where code goes](#choosing-where-code-goes)
- [Actor lifecycle](#actor-lifecycle)
- [Ticking](#ticking)
- [Tick groups](#tick-groups)
- [Tick dependency](#tick-dependency)
- [Timers instead of ticks](#timers-instead-of-ticks)
- [Gameplay Tags](#gameplay-tags)
- [Common structural mistakes](#common-structural-mistakes)

## Who owns what

| Class | Lifetime and role | Replicated? |
|---|---|---|
| Game instance | Created at engine launch, alive until shutdown, survives level travel. Manager with no presence in the world; the home for save games and for game-instance subsystems | Not replicated; exists independently on server and every client |
| Game mode | Created immediately after the level loads, per map. Server-side manager: the rules, the classes to spawn, and the actor that instantiates the rest of the framework | Server-only authority |
| Game state | Data relevant to all players: scores, objectives, the list of player states | Replicated to all clients |
| Player state | Data relevant to one player: health, ammo, inventory. One per player, created on join | Replicated to all clients |
| Player controller | The player's will: input, HUD, possession of a pawn. No physical presence | Owning connection |
| AI controller | Same role for a non-player pawn, driven by behaviour trees, state trees and navigation | Server |
| Pawn / Character | The physical body in the world. `ACharacter` adds a character movement component, a skeletal mesh and a capsule | Replicated |
| HUD | Per-human-player screen overlay, drawn to that player's viewport | Local |
| Actor component | Reusable behaviour attached to an actor: movement, audio, meshes, custom systems | With its actor |

The game mode is the first actor to instantiate on level load and creates the game state and
the player states. Because it is created per level it is not the place for anything that must
survive travel — that is the game instance or a game-instance subsystem.

## Choosing where code goes

Ask what the data's lifetime and authority are, then place it:

- Survives level travel → game instance or game-instance subsystem.
- Rules, spawn classes, win conditions → game mode (server authority).
- Visible to everyone, one copy → game state.
- Visible to everyone, one copy per player → player state. Health on the player state
  survives the pawn; health on the pawn does not survive a respawn.
- Input, camera, UI ownership, "what this player wants" → player controller. A player
  controller persists across pawn possession, which makes it the right owner for anything
  that must outlive the body.
- The body, its movement and its collision → pawn or character.
- Behaviour reused across unrelated actors → component.
- A service with no presence in the world → subsystem (see `unreal-scripting.md`).

## Actor lifecycle

An actor reaches play through one of several paths — placed in a level, spawned at runtime,
or loaded from a save — and the callbacks differ. The ones that matter for correctness:

- The **constructor** runs on the Class Default Object first. It is for default subobjects
  (`CreateDefaultSubobject`) and default values, not for world queries: nothing else in the
  world is guaranteed to exist.
- `PostActorCreated` is where spawn-time construction logic belongs, and it is mutually
  exclusive with `PostLoad`, which the same class runs instead when it is loaded from disk
  rather than spawned. Put versioning and fix-up in `PostLoad`.
- `PostInitializeComponents` runs after the actor's components have been initialized — the
  right place to cache component pointers.
- `BeginPlay` runs when the level starts. Tick functions are registered here.
- `EndPlay` is the single cleanup point: release timers, delegate bindings and subscriptions
  there. It is called by `Destroy`, by streaming-level unload, by ending Play-In-Editor and
  at application shutdown. `OnDestroyed` is a legacy response to `Destroy` and Epic
  recommends moving its logic into `EndPlay`, which the other paths also hit. A stale
  delegate binding into a destroyed actor is a crash on the next broadcast.
- `EndPlay` does not guarantee destruction. With `s.ForceGCAfterLevelStreamedOut` false, a
  sublevel that reloads quickly can resurrect the *same* actor with its member variables
  still holding their old values — so `EndPlay` must reset state, not only release it.
- `BeginDestroy` and `FinishDestroy` run much later, on the collector's schedule. Gameplay
  cleanup that waits for them runs after the world has moved on.
- Runtime-created components need `RegisterComponent()`; an unregistered component exists but
  does not tick or render.

Always call `Super::` in an overridden lifecycle function. Skipping it skips engine setup for
that phase — and the failure appears later, somewhere else.

## Ticking

Ticking runs code at regular intervals, usually once per frame. Actors and components can
tick every frame, at a minimum interval, or not at all. The controls live on
`PrimaryActorTick` (actors, driving `Tick()`) and `PrimaryComponentTick` (components, driving
`TickComponent()`), and are normally set in the constructor so they are correct before
`BeginPlay`:

```cpp
PrimaryActorTick.bCanEverTick = true;
PrimaryActorTick.bTickEvenWhenPaused = true;
PrimaryActorTick.TickGroup = TG_PrePhysics;
```

At runtime, `AActor::SetActorTickEnabled` and `UActorComponent::SetComponentTickEnabled`
switch ticking off and on. An actor or component can also own additional tick functions by
deriving from `FTickFunction`.

The cheapest optimization available is not ticking: a sensor that needs a decision ten times
a second does not need sixty frames of work, and an idle actor needs none.

## Tick groups

Groups run in a fixed order within the frame, and each group finishes every member before the
next begins:

| Group | Guarantee |
|---|---|
| `TG_PrePhysics` | Start of frame. Physics data read here is one frame old. Correct for actors that must move *before* physics so the simulation follows them |
| `TG_DuringPhysics` | Runs alongside the simulation; physics data may be from either frame with no way to tell. Only for logic that does not care — inventory screens, coarse minimaps |
| `TG_PostPhysics` | This frame's simulation results are final. Correct for weapon and movement traces, laser sights, anything that must agree with what is rendered |
| `TG_PostUpdateWork` | After `TG_PostPhysics` and after cameras update. For effects that depend on the final camera, and for logic that must run after everything else |

Between `TG_PostPhysics` and `TG_PostUpdateWork` the engine processes latent actions, ticks
the world timer manager, updates cameras and handles level streaming; deferred actor spawning
happens after `TG_PostUpdateWork`.

A trace in `TG_PrePhysics` that "randomly" disagrees with the picture is not random: it is
reading last frame's transforms.

## Tick dependency

`AddTickPrerequisiteActor` and `AddTickPrerequisiteComponent` make one tick wait for another
to finish. Prefer them over moving an actor to a later group when the dependency is on one or
two specific actors: actors in the same group can tick in parallel, and moving to another
group serializes against an entire group. Two objects already in different groups need no
prerequisite — group order already guarantees it.

## Timers instead of ticks

The world timer manager runs delayed and repeating work without a tick function, and it ticks
between `TG_PostPhysics` and `TG_PostUpdateWork`. Use it for cadence-based work — respawns,
cooldowns, periodic sensing — and clear handles in `EndPlay`. A timer that outlives its owner
fires into a destroyed object.

## Gameplay Tags

Gameplay Tags are hierarchical, user-defined labels (`Event.Movement.Dash` has three levels)
used instead of enums, booleans and strings for state, classification and cross-system
matching.

- Tags come from `.ini` sources: `Config/DefaultGameplayTags.ini` plus files under
  `Config/Tags`. Separate source files per feature keep large projects mergeable.
- Editing a tag `.ini` by hand requires an editor restart before the change is visible.
- Tags defined outside `.ini` sources cannot be renamed or deleted in the Gameplay Tag
  Manager.
- C++ can declare native tags with the macros in `NativeGameplayTags.h`, including
  `UE_DEFINE_GAMEPLAY_TAG_STATIC` for a tag private to one translation unit. Native tags give
  compile-time names instead of stringly-typed lookups.
- Restricted tags can be confined to named owners and cannot be deleted in the editor once
  created — only by editing the `.ini`.

Prefer a `FGameplayTagContainer` over an array of tags when matching sets, and prefer tag
matching over string comparison: the hierarchy is the feature.

## Common structural mistakes

| Mistake | What it costs |
|---|---|
| Gameplay rules on the pawn instead of the game mode | Rules die and respawn with the body, and clients hold a copy of logic that must be server-authoritative |
| Player progress on the pawn instead of the player state | Everything resets on respawn |
| Level-spanning data on the game mode | It is destroyed by level travel; use the game instance |
| Caching component pointers in the constructor | Components are not yet registered; cache in `PostInitializeComponents` or `BeginPlay` |
| Work in `Tick` that only needs a cadence | Frame budget spent for nothing; use a tick interval or a timer |
| Traces in `TG_PrePhysics` | Results disagree with the rendered frame |
| Not clearing timers and delegate bindings in `EndPlay` | A crash on the next broadcast or timer fire |
| One actor per screen-sized concern, each ticking | Tens of tick functions where one subsystem update would do |

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue, maystudios-unreal -->
