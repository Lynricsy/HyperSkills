# Network authority and replication (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]`; nothing
in this file was checked against a running engine.

## Contents

- [The model](#the-model)
- [Net modes and what they change](#net-modes-and-what-they-change)
- [Property replication: the full contract](#property-replication-the-full-contract)
- [RepNotify semantics that surprise people](#repnotify-semantics-that-surprise-people)
- [Replication conditions](#replication-conditions)
- [RPCs](#rpcs)
- [Server RPC validation](#server-rpc-validation)
- [Components and subobjects](#components-and-subobjects)
- [Bandwidth and relevancy](#bandwidth-and-relevancy)
- [Iris](#iris)
- [Review checklist](#review-checklist)

## The model

One machine has authority; every other machine holds a replica it renders and predicts from.
Replication is **not** automatic: you choose what crosses the wire and to whom, and the two
competing goals are a consistent experience for every player and a link that is not
saturated. The three categories the documentation draws are worth keeping in mind when
deciding the wire shape:

- essential gameplay interactions (collision, movement, damage) — must be authoritative;
- cosmetic effects (VFX, sounds) — may be lost;
- player information (HUD) — relevant to one connection.

## Net modes and what they change

| Mode | Enum | Consequence |
|---|---|---|
| Dedicated server | `NM_DedicatedServer` | No local player; discards graphics, sound and input, so anything guarded only by a client-side callback never runs |
| Listen server | `NM_ListenServer` | Host plays on the server, which gives the host a latency advantage and adds server load to a machine that is also rendering |
| Client | `NM_Client` | Runs no server-side logic |
| Standalone | — | Everything is authoritative, which is why single-player testing hides every replication bug |

A dedicated server build is the honest test. Code that works in Play-In-Editor with one
process routinely fails there, because PIE hides ownership and relevancy mistakes.

## Property replication: the full contract

Four things must all be true before a value moves:

1. the property carries `Replicated` or `ReplicatedUsing=OnRep_X`;
2. the property is registered in `GetLifetimeReplicatedProps` with a `DOREPLIFETIME` macro,
   after calling `Super::GetLifetimeReplicatedProps`;
3. the owning actor replicates (`bReplicates = true`, set in the constructor);
4. for a component, the component itself replicates —
   `SetIsReplicatedByDefault(true)` in the constructor, or `SetIsReplicated(true)` at
   runtime.

```cpp
// HealthComponent.h
UPROPERTY(ReplicatedUsing = OnRep_Health, BlueprintReadOnly, Category = "Health")
float Health = 100.f;

UFUNCTION()
void OnRep_Health(float OldHealth);   // optional parameter = previous value

virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
```

```cpp
// HealthComponent.cpp
#include "Net/UnrealNetwork.h"       // required for the DOREPLIFETIME macros

UHealthComponent::UHealthComponent()
{
    SetIsReplicatedByDefault(true);
}

void UHealthComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UHealthComponent, Health);
}
```

Writes happen on the authority. A client write to a replicated property is local only, gets
overwritten by the next update, and — if gameplay depends on it — is exactly the hole a
modified client walks through. `OnRep_` functions are called on clients when the value
arrives; they are not called on the authority, so the server must call the shared handler
itself rather than relying on the notify.

Structs replicate as a unit, and an array marks the whole property dirty, so an unbounded
`TArray` of records is a growing per-change cost. Keep logs server-side, or narrow them with
a condition.

## RepNotify semantics that surprise people

- A RepNotify may declare a parameter of the property's type; the system passes the
  **previous** value.
- By default the notify runs when the property is replicated; register with
  `DOREPLIFETIME_CONDITION_NOTIFY(Class, Prop, REPNOTIFY_Always)` to run it on every
  replication even when the value is unchanged, or `REPNOTIFY_OnChanged` to run it only on a
  change. Code that "misses" an event — the same value re-sent, a re-join that resends the
  current value — usually wants `REPNOTIFY_Always`.
- Blueprint differs from C++: in Blueprint a `Set` node on a replicated property calls that
  property's RepNotify locally, while C++ does not. Blueprint macros and functions that take
  the property by reference generally do not call it even when they change the value. A
  system half in C++ and half in Blueprint therefore fires notifies asymmetrically.

## Replication conditions

`DOREPLIFETIME_CONDITION(Class, Prop, COND_OwnerOnly)` restricts a property to a subset of
connections. Conditions apply to both `Replicated` and `ReplicatedUsing` properties. Using
them is the cheapest bandwidth win available: inventory, ammo and HUD-only values rarely need
to reach every connection.

## RPCs

RPCs are unidirectional and cannot return a value. Their type decides where they run:

| Specifier | Executes on |
|---|---|
| `Client` | The owning client connection for this actor |
| `Server` | The server; must be called from the client that owns the actor |
| `Remote` | The remote side of the connection, never locally; the actor must be client-owned |
| `NetMulticast` | The server and every connected client the actor is currently relevant for |

Consequences that cause real incidents:

- **Ownership decides delivery, not the name.** A function called `ServerX` but declared
  `UFUNCTION(Client)` runs locally when a client calls it: the state change happens on a
  machine with no authority and the server never hears about it.
- A `NetMulticast` called from a client executes locally only — nothing is broadcast.
- A multicast reaches every relevant connection, which is why a "local" effect is heard
  across the map.
- Declaration and implementation are split: declare `void ServerApplyDamage(float Amount);`
  and implement `ServerApplyDamage_Implementation`. The engine generates the dispatcher.
- Prefix names with their type (`Server`, `Client`, `Multicast`) so the call site reads
  correctly.

Reliability:

- RPCs are **unreliable by default**; `Reliable` guarantees delivery and in-order execution
  at the cost of bandwidth.
- An unreliable RPC is dropped with its packet and has no ordering guarantee — correct for
  sounds, particles and animation triggers.
- A reliable RPC bound to player input can be spammed faster than the queue drains, and
  overflowing the reliable queue drops the connection. Rate-limit input-driven RPCs.
- Make RPCs called from a tick function unreliable.
- Prefer a replicated property with a RepNotify over an RPC when both would work, and use
  multicasts sparingly — each one is traffic per connection.

## Server RPC validation

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void ServerApplyDamage(float Amount);

bool UHealthComponent::ServerApplyDamage_Validate(float Amount)
{
    return Amount > 0.f && Amount <= MaxSingleHit;   // reject the impossible
}

void UHealthComponent::ServerApplyDamage_Implementation(float Amount)
{
    // runs only if _Validate returned true
}
```

The server trusts the client's message and then verifies it. If validation fails, the
**calling client is disconnected** — which is the intended signal for an impossible value,
and the reason validation logic must reject only what the game genuinely forbids.

## Components and subobjects

- A component replicates as part of its owning actor once both are set to replicate;
  properties and RPCs inside it then behave as they would on the actor.
- Server-only logic does not have to live in a server RPC: a plain function that provably
  runs only on the server is cheaper and clearer.
- Check `HasAuthority()` in any function that can execute on both sides, and
  `IsLocallyControlled()` on a pawn when the question is "is this the owning client".

## Bandwidth and relevancy

The generic replication system offers three levers beyond conditions:

- **Dormancy** — whether an actor is even considered for replication on a connection. The
  documentation calls it one of the most significant optimizations available; an actor that
  changes rarely should be dormant and flushed when it changes.
- **Priority** — which actors win when bandwidth runs short in a frame.
- **Relevancy** — whether an actor matters to a given connection at all.

Testing tools: network emulation for latency and loss, the network profiler for per-property
cost, and `p.NetShowCorrections`-style console commands documented under network debugging.
Never conclude a replication design is fine because it worked on a LAN.

## Iris

Iris is the newer replication system and runs alongside the generic one, so existing actor
replication and RPCs behave as before. It replaces parts of the generic system with its own
filtering and prioritization. Adopting it is a project-level decision with a documented
migration path; do not mix advice about the two systems' filtering models in the same
explanation.

## Review checklist

- [ ] Every `Replicated`/`ReplicatedUsing` property appears in `GetLifetimeReplicatedProps`,
      which calls `Super`.
- [ ] The actor sets `bReplicates`; replicating components set
      `SetIsReplicatedByDefault`/`SetIsReplicated`.
- [ ] `Net/UnrealNetwork.h` is included where `DOREPLIFETIME` is used.
- [ ] Every write to a replicated property is on the authority.
- [ ] Every RPC's specifier matches its intent, and every server RPC is called on an actor
      the calling client owns.
- [ ] Cosmetic RPCs are unreliable; input-driven reliable RPCs are rate-limited.
- [ ] Server RPCs taking client values have `WithValidation` and a `_Validate` that rejects
      only genuinely illegal input.
- [ ] Death, scoring and other consequences run on the server path, not only inside an
      `OnRep_`.
- [ ] Anything that does not need to reach every connection carries a condition, dormancy or
      relevancy limit.
- [ ] The design was tested against a dedicated server build, not only in Play-In-Editor.

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue, unrealxu-ue5 -->
