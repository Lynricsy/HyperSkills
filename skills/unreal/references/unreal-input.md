# Enhanced Input (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]` unless
marked otherwise; nothing in this file was checked against a running engine.

## Contents

- [The four concepts](#the-four-concepts)
- [Input Actions and value types](#input-actions-and-value-types)
- [Trigger states](#trigger-states)
- [Binding in C++](#binding-in-c)
- [Mapping contexts and priority](#mapping-contexts-and-priority)
- [Modifiers](#modifiers)
- [Triggers](#triggers)
- [Review checklist](#review-checklist)

## The four concepts

Enhanced Input has exactly four moving parts, and most confusion comes from conflating them:

1. **Input Action** — a data asset representing something the player can do ("Crouch", "Fire
   Weapon"). It is the conceptual replacement for an action or axis mapping *name*.
2. **Input Mapping Context** — a collection of Input Actions plus the rules for what triggers
   them, added to and removed from a local player at runtime and prioritized against other
   contexts.
3. **Input Modifier** — a pre-processor that alters raw input values before triggers see them.
4. **Input Trigger** — the requirement an input must satisfy to drive its action.

## Input Actions and value types

The action's type decides the value its listeners receive: a boolean action carries a `bool`,
`Axis1D` a `float`, `Axis2D` an `FVector2D`, and `Axis3D` an `FVector`. Pick the type from the
gameplay meaning, not from the hardware — a WASD movement action is an `Axis2D` even though
each key is digital.

## Trigger states

An action reports a state rather than a single event:

| State | Meaning |
|---|---|
| `Triggered` | All trigger requirements are satisfied. For a "press and release" trigger, this fires on release |
| `Started` | Trigger evaluation began — the first press of a double-tap calls this once |
| `Ongoing` | Evaluation is still in progress; a press-and-hold is ongoing while the hold has not yet reached its duration. Depending on the trigger, this can fire every tick while the action is being evaluated |
| `Completed` | Evaluation finished |
| `Canceled` | Triggering was abandoned — the player released before a hold completed |

Binding everything to `Triggered` and then wondering why a hold feels late is the usual
mistake: the state you want for "the player is currently holding" is `Ongoing`, and for "they
gave up" it is `Canceled`.

## Binding in C++

```cpp
void AArenaCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        // Any ETriggerEvent value can be bound, not just Triggered
        Input->BindAction(AimInputAction, ETriggerEvent::Triggered, this, &AArenaCharacter::OnAim);
        Input->BindAction(MoveInputAction, ETriggerEvent::Triggered, this, &AArenaCharacter::OnMove);
    }
}
```

```cpp
// Adding a mapping context for a local player
APlayerController* PC = Cast<APlayerController>(GetController());
if (ULocalPlayer* LocalPlayer = PC ? PC->GetLocalPlayer() : nullptr)
{
    if (UEnhancedInputLocalPlayerSubsystem* InputSystem =
            LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
    {
        InputSystem->AddMappingContext(InputMapping.LoadSynchronous(), Priority);
    }
}
```

The subsystem is per **local player**, which is also the answer for split-screen: two local
players have two independent context stacks.

`EnhancedInput` must be listed in the module's `.Build.cs` — the unresolved external for
`UEnhancedInputComponent` is a missing module dependency, not a missing include.

## Mapping contexts and priority

A context is a hierarchy: Input Actions at the top, the user inputs that can trigger each one
below, and the triggers and modifiers per input at the bottom.

The rule that decides runtime behaviour: **when several contexts map the same Input Action,
the context with the highest priority is considered and the others are ignored.** Priority is
supplied when the context is added.

The designed shape is mutually exclusive contexts per mode: one common context always mapped,
plus one per mode of travel — on foot, swimming, driving — added on entry and removed on exit.
That is not tidiness; it is what makes inappropriate actions unreachable and prevents one
input from accidentally driving the wrong action.

Debugging a "the key works until I enter the vehicle" report starts with which contexts are
currently added and at what priorities.

## Modifiers

Modifiers run before triggers and rewrite the raw value: reordering axes, dead zones, axis
negation, converting axial input to world space, sensitivity, smoothing across frames.
Because a modifier receives the `UPlayerInput` object, it can reach the owning player
controller and vary its behaviour with game state.

Custom modifiers subclass `UInputModifier` and override `ModifyRaw_Implementation`, in C++ or
as a Blueprint child class. The function receives the player input object, the current value
(from hardware or the previous modifier) and a delta time, and returns an Input Action Value
of three floats, which flows to the next modifier or to the first trigger.

The canonical use is one two-dimensional action from one-dimensional keys: `Negate` makes some
keys register as negative, and `Swizzle Input Axis Values` maps a key to the Y axis instead of
the default X. That is how WASD becomes a single `Axis2D` action rather than four bindings.

## Triggers

Triggers express the requirement — pressed, released, held for a duration, tapped twice,
actuated past a threshold — and are configured per input inside the mapping context. Two
inputs mapped to the same action can carry different triggers, which is how a gamepad's hold
and a keyboard's tap drive the same gameplay action.

## Review checklist

- [ ] Is `EnhancedInput` a dependency in the module's `.Build.cs`?
- [ ] Is each Input Action's value type the gameplay type, with modifiers making the hardware
      fit rather than the reverse?
- [ ] Is each binding on the trigger state the gameplay actually needs (`Ongoing` and
      `Canceled`, not only `Triggered`)?
- [ ] Are contexts added and removed per mode, with deliberate priorities?
- [ ] For split-screen, is every context added through the *local player's* subsystem?
- [ ] Are there two contexts mapping the same action where only the higher priority will ever
      run?

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue, unrealxu-ue5 -->
