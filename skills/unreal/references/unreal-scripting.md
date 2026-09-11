# Reflection, garbage collection and ownership (UE 5.8 C++)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]`; nothing
in this file was checked against a running engine.

## Contents

- [What the macros actually buy](#what-the-macros-actually-buy)
- [Header shape and Unreal Header Tool](#header-shape-and-unreal-header-tool)
- [Garbage collection: the reachability contract](#garbage-collection-the-reachability-contract)
- [Choosing a pointer type](#choosing-a-pointer-type)
- [Worker threads](#worker-threads)
- [Creating and destroying objects](#creating-and-destroying-objects)
- [Property specifiers that change data lifetime](#property-specifiers-that-change-data-lifetime)
- [UFUNCTION exposure and its costs](#ufunction-exposure-and-its-costs)
- [Subsystems instead of god classes](#subsystems-instead-of-god-classes)
- [Failure symptom table](#failure-symptom-table)

## What the macros actually buy

Marking classes, properties and functions with the reflection macros turns them into
`UClass`, `UProperty` and `UFunction` metadata, and that metadata is the only channel through
which the engine offers:

- **Automatic zero-initialization.** UObjects are zeroed before the constructor runs, for
  reflected and native members alike.
- **Automatic reference null-out.** When an `AActor` or `UActorComponent` is destroyed, the
  references the reflection system can see — `UPROPERTY` pointers and pointers inside Unreal
  containers such as `TArray` — are nulled. This is what makes a null check trustworthy.
  A pointer stored outside reflection is neither nulled nor kept alive.
- **Serialization.** Reflected properties are written and read automatically unless marked
  `Transient` or unchanged from the post-constructor default. Adding or removing a property
  does not break existing content: new properties take the new Class Default Object's value,
  removed ones are ignored.
- **Class-default propagation.** When the CDO changes, instances still holding the *old*
  default are updated to the new one; instances with any other value keep it, because that
  value was set deliberately.
- **Editor and Blueprint exposure**, runtime type information, `Cast<T>` and `IsA`.
- **Replication.** Properties can be tagged to replicate and functions tagged to execute on
  a remote machine.

The practical consequence: data the reflection system cannot see does not participate in any
of this, and nothing warns you.

## Header shape and Unreal Header Tool

```cpp
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ArenaPickup.generated.h"   // generated header include

UCLASS(Blueprintable)
class ARENAGAME_API AArenaPickup : public AActor
{
    GENERATED_BODY()                 // very first thing in the class body

public:
    AArenaPickup();
};
```

- The generated header must be included in every gameplay class header, and
  `GENERATED_BODY()` must be placed at the very beginning of the class body. Both are Unreal
  Header Tool requirements, checked before the C++ compiler runs, so a violation produces a
  UHT error with no compiler diagnostic to help.
- Keep the `.generated.h` include last in the header. The documentation's own samples all
  place it last; a header that declares reflected types after it does not build. `[community]`
- Prefixes are enforced by the tooling and read by everyone: `A` extends the spawnable actor
  base, `U` is the rest of the UObject tree (components, data objects, subsystems), `F` is a
  plain struct, `E` an enum, `I` an interface, `T` a template, `S` a Slate widget. Naming an
  actor `UFoo` is a UHT failure, not a lint warning.
- Header and source files are conventionally named after the class minus the `A`/`U` prefix
  (`AActor` lives in `Actor.h`), though the engine enforces no relationship.
- Constructor code runs on the CDO first, so whatever a constructor assigns becomes the
  default that every new instance and every Blueprint subclass inherits.

## Garbage collection: the reachability contract

The collector builds a reference graph from the **root set** and reclaims everything it
cannot reach. The root set contains the engine object, loaded worlds and packages, anything
added with `AddToRoot()`, and objects reported by `FGCObject`/`TStrongObjectPtr` holders.
From there it follows reflected references transitively.

What the collector cannot see:

- a raw `UObject*` member that is not a `UPROPERTY`;
- a UObject held by a reference-counted smart pointer, Unreal's or the standard library's —
  the count is not a reflected reference;
- a raw pointer captured in a lambda.

Actors and components are usually the exception to the "you must hold a `UPROPERTY`" rule:
an actor is referenced by the level that owns it, and a component by its actor. Data objects,
data assets and helper UObjects are not, and they are where lifetime bugs live.

Tuning lives in *Project Settings > Engine - Garbage Collection*. Two settings change
behaviour rather than speed:

- **Clusters** (on by default) group related objects so reachability treats the cluster as one
  object. The cluster is also unhashed and destroyed in one frame, so a large cluster trades
  steady-state cost for a hitch.
- **Merge GC Clusters** joins clusters when one references another, and clearing that
  reference does not split them again — so a merged cluster can stay alive because of a
  reference to any member.
- **Time Between Purging Pending Kill Objects** sets collection frequency. Shortening it
  reduces the amount reclaimed per pass, which is the lever against hitches.

`TObjectPtr` members additionally enable the GC write barrier that incremental marking
requires, which is why UE5 code uses them instead of raw `UPROPERTY` pointers.

## Choosing a pointer type

| Need | Type | Notes |
|---|---|---|
| Local variable, parameter, short-lived reference | `T*` | Raw pointers do not support `UPROPERTY` by default, do not impact GC, and are not serialized or replicated |
| Owned, persistent member of a `UCLASS`/`USTRUCT` | `UPROPERTY() TObjectPtr<T>` | GC-safe **only** as a `UPROPERTY`; serialized; replicable; enables incremental-GC barriers and cook-time dependency tracking |
| Reference that may vanish independently | `TWeakObjectPtr<T>` | Does not keep the target alive, auto-nulls after collection, supports `UPROPERTY` but does not need it; not usable as a `TMap` key or `TSet` element — use `TObjectKey` |
| Asset that must not force a load | `TSoftObjectPtr<T>` | Stores a path; flips between valid and pending as the asset loads; load it explicitly before use |
| Strong reference from a non-UObject class | `TStrongObjectPtr<T>` | Cannot be a `UPROPERTY`; affects GC everywhere including stack and lambdas |
| Deprecated | `TLazyObjectPtr<T>` | Marked for removal; migrate to `TSoftObjectPtr` |

`TStrongObjectPtr` deserves its "use caution" label:

- creating and destroying one is expensive, so it suits long-lived references that rarely
  change, not per-frame or per-entity use;
- it is always strong, keeping the target alive even when the object is otherwise
  unreachable;
- inside a UObject it produces uncollectable cycles — an object holding a
  `TStrongObjectPtr` to itself never dies, while a `TObjectPtr` self-reference is collected
  normally.

For owning references inside a UObject use `UPROPERTY() TObjectPtr<T>`; for non-owning or
asset references use `TWeakObjectPtr`.

## Worker threads

Never dereference a UObject through a `TObjectPtr` from a worker thread unless the object is
already rooted and cannot be collected during the access. The documented pattern:

```cpp
FSimpleDelegate Delegate;
TObjectPtr<UMyObject> MyObject;

Delegate.BindLambda(
    [WeakObject = MakeWeakObjectPtr(MyObject)]()
    {
        if (TStrongObjectPtr<UMyObject> Strong = WeakObject.Pin())
        {
            // Safe for this scope: Pin() holds the object
        }
    });
```

`TWeakObjectPtr::Pin()` returns a `TStrongObjectPtr` when the target is still valid, which is
both the validity check and the lifetime guarantee. Capturing `this` or a raw pointer into a
task gives neither.

## Creating and destroying objects

```cpp
// Constructor only, for default subobjects that Blueprint subclasses inherit
Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
RootComponent = Mesh;

// Anywhere else
UMyData* Data = NewObject<UMyData>(this);   // 'this' is the outer

// Removal
MyActor->Destroy();          // actors
MyComponent->DestroyComponent();
Data->MarkAsGarbage();       // other UObjects; collected on a later pass
```

- `Destroy()` is the standard way to remove an actor from a running game; components are
  usually destroyed with their actor.
- Never `delete` a UObject and never let a shared pointer's deleter do it: destruction runs
  through the collector.
- `AddToRoot()` must be paired with `RemoveFromRoot()`. An unpaired root is a permanent leak
  that also pins everything the object references, including a world that then cannot unload.

## Property specifiers that change data lifetime

| Specifier | Effect worth remembering |
|---|---|
| `Transient` | Never saved or loaded; zero-filled at load. With `EditAnywhere` it silently discards designer values |
| `Config` / `GlobalConfig` | Value read from and written to an `.ini`; cannot be given a value in default properties; implies `BlueprintReadOnly` |
| `EditDefaultsOnly` / `EditInstanceOnly` | Restricts editing to the archetype or to placed instances — the usual fix when designers edit the wrong copy |
| `BlueprintReadOnly` | Incompatible with `BlueprintReadWrite`; the pair is a UHT error, not a precedence rule |
| `Replicated` / `ReplicatedUsing` | Declares intent only; the property must still be registered in `GetLifetimeReplicatedProps` |
| `BlueprintGetter` / `BlueprintSetter` | A `BlueprintGetter` without `BlueprintSetter` or `BlueprintReadWrite` is implicitly read-only; a `BlueprintSetter` implies `BlueprintReadWrite` and its mutator must live in the same class |

## UFUNCTION exposure and its costs

- `BlueprintCallable` adds a callable node; `BlueprintPure` marks a function with no side
  effects, so Blueprint may call it more than once per graph evaluation.
- `BlueprintImplementableEvent` has no C++ body at all — the implementation is the Blueprint
  override. `BlueprintNativeEvent` has a C++ `_Implementation` that the Blueprint may
  override.
- Every exposed function is a reflected entry point and a compatibility promise: renaming it
  breaks every Blueprint that calls it, silently, until the asset is opened.
- Expose the minimum. Helpers that designers never call stay plain C++ and cost nothing.

## Subsystems instead of god classes

Subsystems are automatically instanced classes with managed lifetimes and free Blueprint and
Python exposure — the right home for a system that would otherwise be bolted onto
`UGameInstance` or an engine class.

| Lifetime | Base class | Access |
|---|---|---|
| Engine | `UEngineSubsystem` | `GEngine->GetEngineSubsystem<T>()` |
| Editor | `UEditorSubsystem` | `GEditor->GetEditorSubsystem<T>()` |
| Game instance | `UGameInstanceSubsystem` | `GameInstance->GetSubsystem<T>()` |
| Local player | `ULocalPlayerSubsystem` | `LocalPlayer->GetSubsystem<T>()` |

`Initialize()` runs after the owner is created and `Deinitialize()` when it shuts down; the
reference is then dropped and the subsystem is collected like any other UObject. Engine and
editor subsystems initialize after their module's startup returns and deinitialize after its
shutdown returns. For plugins this matters: a consumer adds the plugin and gets a system with
a known creation point, with no setup instructions.

## Failure symptom table

| Symptom | Cause to check first |
|---|---|
| Crash a few seconds after spawn, or after a level load | A UObject held only by an unreflected pointer (rules 1–3) |
| Crash inside the collector or the allocator, stack unrelated to your code | A UObject `delete`d or wrapped in a shared pointer |
| Pointer is suddenly null | Auto-null-out after the target actor or component was destroyed — the intended behaviour; check validity before use |
| Memory grows across level loads | `AddToRoot` without `RemoveFromRoot`, or a long-lived strong reference to an actor |
| Designer's value keeps reverting | `Transient`, or editing the instance while the value lives on the archetype |
| Object never collected even though nothing references it | `TStrongObjectPtr` cycle inside a UObject |
| UHT error before any compiler output | Missing generated header, `GENERATED_BODY()` not first, or a prefix that does not match the base class |

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue, unrealxu-ue5 -->
