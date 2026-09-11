# Blueprint and C++ (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]` unless
marked otherwise; nothing in this file was checked against a running engine.

## Contents

- [The division that works](#the-division-that-works)
- [What the documentation says about Blueprint cost](#what-the-documentation-says-about-blueprint-cost)
- [Exposing C++ to Blueprint](#exposing-c-to-blueprint)
- [Blueprint communication](#blueprint-communication)
- [Hard references](#hard-references)
- [Replication differences in Blueprint](#replication-differences-in-blueprint)
- [Debugging Blueprints](#debugging-blueprints)
- [Iterating with Live Coding](#iterating-with-live-coding)
- [Review checklist](#review-checklist)

## The division that works

The shape the engine is designed around: an **abstract C++ base class** holding systems,
algorithms, networking and performance-critical code, with a **Blueprint subclass** holding
asset references, tuning values and one-off event responses. Most classes in Unreal are
customized in both, and the documentation says so explicitly: you can use most Gameplay
Framework classes from C++, Blueprint, or — most commonly — a combination.

Put in C++: base classes, systems, replication, anything that runs per frame or per entity,
editor tooling, and anything a designer should not be able to break.

Put in Blueprint: which asset, which value, which montage, what happens when this specific
door opens, and UI layout.

The signal that the split is wrong is a Blueprint doing complex math every tick, or a C++
class hard-coding an asset path that a designer will want to change.

## What the documentation says about Blueprint cost

Blueprints are best suited to **event-driven** functionality — damage handling, controls,
things that are not called every frame. A Blueprint doing a lot of operations and complex
math every tick is the documented case for moving that work into native C++.

Two consequences worth stating in a review:

- Moving a hot Blueprint graph to C++ is a real optimization; moving a cold one is churn.
- Blueprint nativization is not a rescue plan — it was removed in UE 5.0, so hot paths are
  converted by hand. `[community]`

## Exposing C++ to Blueprint

| Specifier | Use |
|---|---|
| `UCLASS(Blueprintable)` | This class can be the parent of a Blueprint. The default is not Blueprintable unless inherited |
| `UCLASS(BlueprintType)` | The class can be used as a Blueprint variable type |
| `UFUNCTION(BlueprintCallable)` | Callable node with an execution pin |
| `UFUNCTION(BlueprintPure)` | No side effects; Blueprint may call it more than once per evaluation, so it must be cheap and idempotent |
| `UFUNCTION(BlueprintImplementableEvent)` | Declared in C++, implemented only in Blueprint — no C++ body exists |
| `UFUNCTION(BlueprintNativeEvent)` | C++ `_Implementation` that a Blueprint may override |
| `UPROPERTY(BlueprintReadWrite)` / `BlueprintReadOnly` | Variable access. The two are mutually incompatible |
| `UPROPERTY(EditDefaultsOnly)` | Tunable on the Blueprint class, not per placed instance — the usual choice for design tuning |
| `USTRUCT(BlueprintType)` / `UENUM(BlueprintType)` | Makes the struct or enum usable as a Blueprint variable |
| `meta = (BlueprintSpawnableComponent)` | Lets Blueprints add this component class |

Every exposed name is an interface promise. Renaming an exposed function or property breaks
the Blueprints that reference it, and the breakage surfaces when someone opens the asset, not
when you compile. Expose the minimum, and prefer `BlueprintReadOnly` for state that gameplay
code owns so level Blueprints cannot trample it. `[community]`

## Blueprint communication

Three mechanisms, in the order to prefer them:

1. **Direct communication** — a reference to the other object and a call on it. Simplest, and
   creates a hard dependency.
2. **Blueprint Interfaces** — call a function on anything that implements the interface, with
   no need to know or load the concrete class.
3. **Event Dispatchers** — one broadcaster, many subscribers; the broadcaster knows nothing
   about who is listening.

Reach for an interface or a dispatcher when direct communication would require a cast to a
class the caller should not know about. That is both a coupling and a loading decision: see
below.

## Hard references

A hard reference to an asset or class pulls it into memory whenever the referencing asset
loads, which is how one small Blueprint ends up loading a chain of meshes, sounds and other
Blueprints. `TSoftObjectPtr` and `TSoftClassPtr` store a path instead and load on demand, so
they break the chain — at the price of an explicit load step before use. Use the Reference
Viewer to see what a Blueprint actually drags in. `[community]`

## Replication differences in Blueprint

Blueprint and C++ do not behave identically at the replication boundary:

- In Blueprint, a `Set` node on a replicated property automatically calls that property's
  RepNotify if one is defined in Blueprint. C++ does not.
- Blueprint macros and functions that take a property **by reference** generally do not call
  the RepNotify even though they modify the value.

A system written half in each therefore fires notifies asymmetrically. Keep the authoritative
write path in one language, and see `unreal-replication.md` for the rest of the contract.

## Debugging Blueprints

- The Blueprint Debugger inspects a running graph: breakpoints on nodes, the call stack and
  watched values.
- Blueprint Namespaces limit which types appear in a graph's context menu, which is the
  documented lever against a type picker with thousands of entries in a large project.
- The Blueprint Editor cheat sheet documents the graph shortcuts; use it rather than inventing
  a workflow.

## Iterating with Live Coding

Live Coding patches C++ into the running editor, which is how a C++/Blueprint project stays
iterable. Two facts change how you work:

- A default value changed in a **constructor in a `.cpp`** does not update existing
  instances; the same change in the **header** does.
- Object Reinstancing replaces instances so structural changes (new functions, new variables,
  refactors) take effect, and it covers everything declared with the reflection macros
  including generated Blueprint nodes.

Details and the shutdown-crash failure mode are in `unreal-build.md`.

## Review checklist

- [ ] Is any Blueprint doing per-frame math or per-frame queries that belong in C++?
- [ ] Is any C++ class hard-coding what a designer will want to tune?
- [ ] Is anything exposed to Blueprint that no Blueprint needs?
- [ ] Are casts to concrete classes used where an interface or dispatcher would remove the
      dependency?
- [ ] Do hard references pull a load chain that a soft reference would break?
- [ ] Does the replicated write path live in one language, with RepNotify semantics stated?

<!-- sources: epic-ue-docs, gamedev-unreal, maystudios-unreal, unrealxu-ue5 -->
