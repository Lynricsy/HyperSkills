---
name: unreal
description: "Guides Unreal Engine 5 gameplay work in C++ and Blueprint: the UCLASS/UPROPERTY/UFUNCTION reflection contract and what the garbage collector can and cannot see (TObjectPtr, TWeakObjectPtr::Pin, TStrongObjectPtr, AddToRoot), Gameplay Framework class roles, actor lifecycle, tick groups and intervals, Enhanced Input contexts and priorities, network authority with GetLifetimeReplicatedProps, DOREPLIFETIME conditions, RepNotify and the four RPC types, Gameplay Ability System boundaries, Lumen and Nanite limits, UMG update strategy, Chaos sub-stepping, Niagara, modules and .Build.cs dependencies, Live Coding, packaging, and automation tests. Use when reading or writing .h/.cpp under a Source tree that uses UCLASS or a .Build.cs, or when the user names UE5, Unreal, GENERATED_BODY, GameMode, ACharacter, UMG, Lumen, Nanite, Chaos or GAS. Do not use for general C++ or std/CMake ownership questions, for Unity or Godot projects, for visual design principles, or for TDD methodology."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# unreal

## Scope

Covers Unreal Engine 5 game and gameplay development: the UObject reflection system
(`UCLASS`/`UPROPERTY`/`UFUNCTION`/`USTRUCT`) and the garbage collector that depends on it,
pointer and ownership types, the Gameplay Framework class roles, actor and component
lifecycle and ticking, subsystems, Blueprint and C++ division of labour, Enhanced Input,
network authority and replication, the Gameplay Ability System, rendering with Lumen and
Nanite, Niagara, UMG and Slate, Chaos physics, modules and `.Build.cs`, Live Coding,
cooking, packaging and release, and the Automation Test framework.

Targets **UE 5.8** — the version the official documentation currently ships — and marks
every rule that only holds from a specific release. Rules without a version gate have held
across UE 5.x.

Not covered: the general C++ language, the standard library, CMake, and ownership questions
in engine-free C++ code. **No skill in this library covers general C++**; answer those
directly instead of reaching for an engine idiom. Unity is the `unity` skill and Godot is
the `godot` skill; this skill never answers for them and cross-engine comparison stays to
one sentence where it is unavoidable. Game UI *implementation* is here, but visual design
principles — hierarchy, typography, colour, spacing — use the `frontend-design` skill.
Unreal's own test frameworks are here; test-first methodology uses the
`test-driven-development` skill and browser end-to-end testing uses the `web-testing`
skill.

Paths below are relative to this skill's directory.

## Read first

`references/unreal-scripting.md` before writing or reviewing any `.h` under `Source/`. The
reflection macros are not annotations: they are the only channel through which the garbage
collector, the serializer, the editor and the network see your data. A member the reflection
system cannot see is a dangling pointer with a delay fuse, and the compiler will not say a
word.

## Core rules

1. A `UObject` stays alive only while something reachable from the root set holds it through
   a reflected reference — a `UPROPERTY`, or a UObject pointer inside an Unreal container.
   A raw `UObject*` member without `UPROPERTY` is invisible to the collector and to the
   engine's automatic null-out, so it becomes a pointer into freed memory. `[official]`
2. Automatic null-out is narrower than it sounds: destroying an `AActor` or `UActorComponent`
   nulls the references the reflection system can see. That is what makes null checks
   meaningful — and what makes an unreflected pointer a silent use-after-free. `[official]`
3. Use `UPROPERTY() TObjectPtr<T>` for owned UObject members (UE5). `TObjectPtr` is only
   GC-safe when it is a `UPROPERTY`, and it is what enables the GC write barrier that
   incremental garbage-collection marking needs plus cook-time dependency tracking. Raw
   `UPROPERTY` pointers still work and buy none of that. `[official]`
4. Never dereference a UObject through a `TObjectPtr` from a worker thread unless the object
   is already rooted. The documented pattern is a `TWeakObjectPtr` plus
   `TWeakObjectPtr::Pin()`, which yields a `TStrongObjectPtr` that holds the object for the
   duration of the access. `[official]`
5. `TStrongObjectPtr` does not support `UPROPERTY`, is expensive to create and destroy, and
   is always a strong reference — so it belongs in non-UObject owners only. Inside a UObject
   it produces cycles the collector cannot break; a `TObjectPtr` self-reference does not.
   `[official]`
6. A UObject is never `delete`d and never wrapped in an Unreal or standard shared pointer.
   Actors are removed with `Destroy()`, other objects with `MarkAsGarbage()`, and the
   collector owns destruction. A ref-counted wrapper's count is not a reflected reference.
   `[official]`
7. `AddToRoot()` pins an object in the root set permanently. Without a paired
   `RemoveFromRoot()` it is a leak for the life of the process, and it keeps everything the
   object references alive with it. `[official]`
8. `GENERATED_BODY()` goes at the very beginning of the class body, and the generated header
   must be included in the class header. Get either wrong and Unreal Header Tool fails
   before the compiler ever runs. `[official]`
9. Class prefixes are part of the contract, not a style: `A` for actor-derived spawnable
   classes, `U` for the rest of the UObject tree, `F` for plain structs, `E` for enums,
   `I` for interfaces, `T` for templates, `S` for Slate widgets. `[official]`
10. `Transient` means never saved and zero-filled at load. Combining it with `EditAnywhere`
    throws away every value a designer sets, with no warning anywhere. `[official]`
11. Marking a property `Replicated` or `ReplicatedUsing` is half a contract. The property
    must also be registered in `GetLifetimeReplicatedProps` (`DOREPLIFETIME`, or
    `DOREPLIFETIME_CONDITION` with a condition), and the owning actor needs `bReplicates`
    while a replicating component needs `SetIsReplicatedByDefault` in its constructor or
    `SetIsReplicated` at runtime. Miss any one and the value never leaves the server.
    `[official]`
12. Replicated state changes on the authority only. A client write is local, gets
    overwritten by the next update from the server, and — when it drives gameplay — is a
    cheat surface. Hand-calling an `OnRep_` function fabricates a replication event the
    server never sent. `[official]`
13. RPCs are unreliable by default and reliable ones cost bandwidth, so cosmetic events stay
    unreliable. A reliable RPC bound to player input can be spammed until the reliable
    queue overflows, which drops the connection. `[official]`
14. A `Server` RPC must be called from a client that owns the actor, and a `NetMulticast`
    RPC executes on the server plus every client the actor is currently relevant for — a
    client that calls one only runs it locally. Ownership, not the function name, decides
    where a call lands. `[official]`
15. A `Server` RPC that takes client-supplied values gets `WithValidation` and a `_Validate`
    function: passing runs the implementation, failing disconnects the caller. That is the
    whole point of a trust-and-verify boundary. `[official]`
16. A RepNotify fires only when the value changes unless the property is registered with
    `DOREPLIFETIME_CONDITION_NOTIFY(..., REPNOTIFY_Always)`, and in Blueprint — unlike C++ —
    a `Set` node on a replicated property calls the RepNotify locally. Assuming C++
    semantics in Blueprint, or `Always` semantics by default, produces state that is right
    on the wire and wrong on screen. `[official]`
17. Ticking is a budget, not a default. Leave `bCanEverTick` false unless the work really is
    per-frame, use a minimum tick interval or a timer for anything that only needs a
    cadence, and put work that reads this frame's physics results in `TG_PostPhysics` —
    `TG_PrePhysics` sees physics data that is one frame old. `[official]`
18. Enhanced Input resolves collisions by mapping-context priority: when two contexts map the
    same Input Action, the highest-priority context wins and the others are ignored. Adding
    a context without a priority plan produces input that works until the second context
    appears. `[official]`
19. In the Gameplay Ability System, an Ability System Component does not replicate Abilities
    and Gameplay Effects to all clients — only the Gameplay Attributes and Tags they affect
    — and Gameplay Cues are not reliably replicated, so a Cue is cosmetic feedback only.
    Gameplay-relevant feedback goes through Ability Tasks. `[official]`
20. Lumen ignores lights whose Mobility is `Static`, because static light contribution lives
    in lightmaps and is disabled when Lumen is on. A project upgraded from UE4 does not get
    Lumen enabled automatically, and Lumen's hardware ray tracing carries significant scene
    update cost past roughly 100,000 instances. `[official]`
21. Nanite renders `Opaque` and `Masked` materials only — anything else is replaced by the
    default material with a log warning — does not support morph-target deformation, MSAA,
    forward rendering or VR stereo, and caps the scene at 16 million streamed-in instances.
    `[official]`
22. Drive UI from events, not from Bindings or Tick; Unreal's own UMG guidance says so.
    Per-frame property bindings and per-frame text formatting pay layout and allocation
    costs on every frame for data that changes rarely. `[official]`
23. Physics sub-stepping buys stability with CPU, and it changes callback timing: collision
    callbacks are delayed until the final sub-step, so one frame can deliver both an overlap
    and its matching end-overlap for the same pair. Logic that assumes one callback per
    frame breaks under sub-stepping, not under load. `[official]`
24. Unreal Build Tool compiles only the modules in your project's dependency chain, so a
    symbol from an unlisted module is an unresolved external at link time. Public dependency
    means "used in this module's public headers" and propagates to dependents; private is
    preferred because it cuts compile times. Regenerate project files after editing a
    `.Build.cs`. `[official]`
25. The Automation Test framework depends on engine systems and is explicitly not the tool
    for pure unit tests — that is Low-Level Tests. Tests may run out of order or in parallel
    across machines, so a test that assumes editor or game state is a flake by construction,
    and a Smoke test must finish inside one second. `[official]`

## Workflows

### implement

- [ ] Read the `.uproject` (engine version, enabled plugins) and the target module's
      `.Build.cs` before writing code. Every rule above that names a module, plugin or
      engine version depends on those two files.
- [ ] Place the type in the framework: rules and spawn classes on the GameMode, session
      state on GameState, per-player state on PlayerState, intent on the PlayerController,
      the body on the Pawn or Character, reusable behaviour in a component, and process-wide
      services in a subsystem. See `references/unreal-gameplay-framework.md`.
- [ ] Declare the header: `UCLASS`, `GENERATED_BODY()` first in the body,
      `UPROPERTY() TObjectPtr<T>` for owned objects, `TWeakObjectPtr` for observers,
      `TSoftObjectPtr` for assets that must not force a load (rules 1–10).
- [ ] Decide the update model before writing `Tick`: event, delegate, timer, tick interval,
      or a subsystem that updates many actors once (rule 17).
- [ ] For multiplayer, decide authority first, then the wire shape: replicated property with
      a RepNotify by default, RPC only for events (rules 11–16, and
      `references/unreal-replication.md`).
- [ ] Add any new module dependency to the `.Build.cs`, private unless it appears in a public
      header, and regenerate project files (rule 24).
- [ ] **Gate:** the module compiles and links from a clean build (not an incremental one),
      and the class, its properties and its Blueprint-exposed functions appear in the editor
      as intended.

### review

- [ ] Establish the engine version and enabled plugins first. A finding that depends on a
      version is not a finding until the version is known.
- [ ] Walk the headers for reflection and ownership defects (rules 1–10). These are the ones
      that compile, pass review and crash later.
- [ ] Walk the network boundary: where does each replicated write happen, is it registered,
      who owns the actor, and is every RPC's direction and reliability deliberate
      (rules 11–16)?
- [ ] Walk the per-frame budget: every `Tick`, every per-frame query or trace, every
      per-frame UI update, every `Cast` in a loop (rules 17, 22).
- [ ] Check that editor-only code is behind an editor module or `WITH_EDITOR`, and that no
      runtime module depends on an editor module (rule 24).
- [ ] Report only findings with a reachable trigger and a concrete consequence. A text match
      is a lead, not a finding.
- [ ] **Gate:** every finding carries `path:line`, the trigger, the consequence and a fix,
      and any engine claim names the version it holds for.

### debug-a-crash

- [ ] Classify first: a crash seconds after spawn or after a level load is the garbage
      collector reclaiming something nothing reflected was holding (rules 1–7); a crash on
      editor shutdown after a Live Coding patch is a stale pointer to a reinstanced object.
- [ ] Search for the ownership hole rather than the crash site. The stack usually points at
      the collector or the allocator, not at the code that failed to hold the reference.
- [ ] Check worker threads and lambdas for captured raw pointers and `TObjectPtr` access
      off the game thread (rule 4).
- [ ] Reproduce with a forced collection rather than waiting: `gc.CollectGarbageEveryFrame`
      and `obj gc` make a lifetime bug deterministic.
- [ ] **Gate:** the fix is an ownership change — a reflected reference, a weak pointer plus a
      validity check, or a lifetime moved to an owner — not a null check added at the crash
      site.

### optimize-a-frame

- [ ] Measure before changing anything: `stat unit` to split game / draw / GPU, then
      `stat game`, `stat collision` or an Unreal Insights capture on the scene that is slow.
      See `references/unreal-build.md` for the capture commands.
- [ ] Attribute the cost to a thread. Game-thread cost is usually tick work, per-frame
      queries, or UI updates (rules 17, 22); GPU cost is usually Lumen and Nanite settings
      (rules 20, 21) or overdraw from VFX.
- [ ] Remove the work, then reduce its frequency, then optimize what is left. Deleting a
      per-frame full-world query beats making it cheaper.
- [ ] Changing *when* work runs changes its answer, so state the new timing explicitly:
      anything that reads physics results (traces, attachment, contact queries) must still
      run after the simulation, whether it now lives in `TG_PostPhysics`, on a timer, or in
      a subsystem update (rule 17). A rewrite that never says where the query happens has
      moved the correctness question, not answered it.
- [ ] Re-measure on the same scene and the same build configuration, and report the before
      and after numbers rather than the change list.
- [ ] **Gate:** a before/after measurement from the same capture type on the same scene, with
      the build configuration named.

### ship-a-build

- [ ] Package through the Project Launcher with a custom profile rather than by hand:
      Shipping build configuration, cook By the Book, and "create a release version" with a
      version number when the build is a release.
- [ ] Keep the release's asset registry and pak from the `Releases/<version>/<platform>`
      directory; patches and DLC are diffed against them.
- [ ] Confirm no runtime module depends on an editor module before packaging — this is the
      failure that only appears outside the editor (rule 24).
- [ ] Run the automation suite for the packaged target, and treat a state-dependent test
      failure as a test defect until proven otherwise (rule 25).
- [ ] **Gate:** the staged build launches from `Saved/StagedBuilds/<platform>` on the target
      platform, not just in the editor.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Reflection, GC and ownership | Writing or reviewing any header; a crash after a collection; choosing a pointer type | `references/unreal-scripting.md` |
| Gameplay Framework | Placing a class; GameMode/GameState/Controller/Pawn roles; lifecycle, ticking, timers, tags | `references/unreal-gameplay-framework.md` |
| Blueprint and C++ | Splitting work between designers and code; exposing C++ to Blueprint; Live Coding iteration | `references/unreal-blueprints.md` |
| Replication | Any multiplayer work: authority, properties, RPCs, components, bandwidth | `references/unreal-replication.md` |
| Gameplay Ability System | Deciding whether to adopt GAS; attributes, effects, cues, prediction | `references/unreal-gas.md` |
| Enhanced Input | Binding input; mapping contexts, triggers, modifiers, priorities | `references/unreal-input.md` |
| Rendering and VFX | Lumen, Nanite, material and mesh limits, Niagara cost | `references/unreal-rendering.md` |
| UI | UMG widgets, update strategy, Slate, per-frame UI cost | `references/unreal-ui.md` |
| Physics | Chaos, collision queries, sub-stepping, networked physics | `references/unreal-physics.md` |
| Modules, build and tests | `.Build.cs`, plugins, Live Coding, cooking, packaging, automation tests, profiling | `references/unreal-build.md` |

## Output format

For `review` and any other report on existing code, group findings by file, ordered by
severity, with no preamble:

```
Source/ArenaGame/Public/ArenaPickup.h
  L20 blocking - raw UArenaPickupData* member with no UPROPERTY. The collector cannot see
       it and will not null it, so it dangles after the next collection - the "crashes a
       few seconds after spawn" signature.
       before: UArenaPickupData* CachedData = nullptr;
       after:  UPROPERTY() TObjectPtr<UArenaPickupData> CachedData;
  L29 important - EditAnywhere with Transient discards every value a designer sets, because
       Transient properties are never saved and are zero-filled at load.

Source/ArenaGame/Private/HealthComponent.cpp
  L20 blocking - Health is written on a machine with no authority; the next server update
       overwrites it and the value is a cheat surface in the meantime.
  ✓ OnRep_Health only reads replicated state, so it is safe on clients.
```

Severities: `blocking` (does not compile or link, crashes, corrupts state, breaks
replication, or fails packaging), `important` (leaks, per-frame cost, lost designer data,
cheatable authority, unreliable-when-it-matters), `minor` (naming, ordering, dead code).
End with a one-line verdict: ship, ship after blocking fixes, or rework. Name the engine
version every engine claim holds for, and list unrun checks separately from findings.

## Environment

Unreal Engine is installed through the Epic Games Launcher or built from the source
distribution, which requires a linked Epic account; the engine is tens of gigabytes and is
frequently absent from CI and from review machines. Commands referenced by the workflows:

```bash
# Windows paths shown; on Linux and macOS use RunUAT.sh and UnrealEditor
Engine/Build/BatchFiles/RunUAT.bat BuildCookRun -project=MyProject.uproject -clientconfig=Shipping
UnrealEditor-cmd.exe MyProject.uproject -run=cook -targetplatform=Windows
UnrealEditor-cmd.exe MyProject.uproject -ExecCmds="Automation RunTests Project.Functional" -unattended -nopause
```

In-editor: `Ctrl+Alt+F11` triggers a Live Coding build, `Window > Test Automation` runs the
automation suite once a testing plugin is enabled and the editor restarted, and
`stat unit` / `stat game` / Unreal Insights measure a frame.

When the engine is not installed, say so and keep the reasoning at the level of the source
and the official documentation. Never describe a build, a packaged run or a profiling
capture that was not produced.
