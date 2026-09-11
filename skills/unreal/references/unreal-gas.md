# Gameplay Ability System (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]` unless
marked otherwise; nothing in this file was checked against a running engine.

## Contents

- [When GAS is the right answer](#when-gas-is-the-right-answer)
- [The pieces](#the-pieces)
- [Attributes and attribute sets](#attributes-and-attribute-sets)
- [Gameplay Effects](#gameplay-effects)
- [Gameplay Cues are cosmetic only](#gameplay-cues-are-cosmetic-only)
- [What replicates and what does not](#what-replicates-and-what-does-not)
- [Prediction and rollback](#prediction-and-rollback)
- [Server-owned actors](#server-owned-actors)
- [Setup](#setup)
- [Review checklist](#review-checklist)

## When GAS is the right answer

GAS is a framework for abilities and interactions that actors own and trigger, designed mainly
for RPGs, action-adventure games, MOBAs and other games where characters have abilities that
must coordinate mechanics, VFX, animation, sound and data. It also supports replication, and
saves substantial work when a design scales up to multiplayer.

The corollary: a game with three abilities, no modifiers, no stacking and no multiplayer pays
GAS's concept count for nothing. The decision is about whether abilities are *data* that
designers compose — costs, cooldowns, tags, stacking, buffs and debuffs, cue libraries — or
three functions on a character. Adopt it for the former; the framework does not shrink for the
latter.

A term to keep straight before reading anything else: the **"Owner" of a Gameplay Ability is
not the same thing as ownership in network replication terms.**

## The pieces

- **Ability System Component (ASC)** — the component that owns abilities, attributes, tags and
  active cues, and does the replication work in multiplayer. It is also responsible for
  communicating player actions to the server and verifying that clients are authorized to
  change its state.
- **Gameplay Ability** — an activatable unit with Activate, EndAbility, Cancel and OnRemove
  points. Most `UGameplayAbility` functions have a counterpart on the ASC, so behaviour can be
  chosen per ability or per ASC class.
- **Gameplay Attributes and Attribute Sets** — enhanced float properties supporting predictive
  changes, replication and temporary modification.
- **Gameplay Effects** — how abilities change a target: instant, duration-based or infinite,
  built from Gameplay Effect Components, with Effect Calculations for anything non-trivial.
- **Gameplay Cues** — the audio/visual layer, tag-addressed.
- **Ability Tasks** — asynchronous steps inside an ability, and the replication-safe way to
  drive gameplay-relevant feedback (the Play Montage task is the canonical example).
- **Gameplay Tags** — the addressing system that ties all of the above together (see
  `unreal-gameplay-framework.md`).

## Attributes and attribute sets

An attribute tracks a **base value** and a **current value** separately, which is what makes
temporary buffs and debuffs expressible: an instant effect modifies the base value, while any
effect with a duration modifies the current value and is undone when the effect ends. Getting
this backwards produces buffs that never expire or damage that heals itself when a buff
falls off.

Attributes replicate their value to all clients and are safe for local UI such as enemy
health bars.

One documented trap in the data: the **"Min Value" and "Max Value" columns are not implemented
in the default plugin and have no effect.** Clamping is your code's job, in the attribute set,
not a checkbox in the table.

## Gameplay Effects

- Instant effects modify base values; duration effects modify current values and revert on
  removal; persistent effects attach to the target until removed or expired, and clean up
  their own attribute changes.
- Effect Calculations can read both the ability's owner and the target, so shared damage or
  healing formulas live in one reusable place rather than in every ability.
- Applying tags, cues and attribute changes **through** Gameplay Effects — rather than
  directly — is what makes them participate in rollback (see below).

## Gameplay Cues are cosmetic only

Gameplay Cues are actors and UObjects that run visual and sound effects, and are the preferred
way to replicate cosmetic feedback. They are tag-addressed: adding the tag
`Ability.Magic.Fire.Weak` to a cue means any Gameplay Effect carrying that tag spawns and runs
it, which is how a project builds a reusable VFX library without per-ability wiring. Cues can
also be triggered without an effect association.

**Cues do not use reliable replication.** Some clients will not receive a cue, so tying
gameplay logic to a cue creates desyncs. Gameplay-relevant feedback that must reach every
client goes through Ability Tasks instead.

## What replicates and what does not

To save bandwidth and prevent cheating, an ASC **does not replicate its full state to all
clients**: abilities and gameplay effects are not replicated to all clients, only the
gameplay attributes and tags they affect. Any client-side system that wants to know "which
ability is running on that other player" must infer it from attributes, tags or cues — not
from an ability list it does not have.

## Prediction and rollback

Abilities normally run on the server and replicate, which shows up as activation lag. To mask
it, activate locally and tell the server, which then catches up — with the possibility that
the server **rejects** the activation and the local changes must be undone.

Rollback support is not uniform: most non-instant Gameplay Effects support it, but
instantaneous attribute and tag changes — damage, notably — do not. This is the concrete
reason to apply tags, cues and attribute changes through Gameplay Effects: it is what gives
them a chance to roll back. Predicting damage directly and hoping is how a rejected activation
leaves a client with a wrong health bar.

## Server-owned actors

Remote activation requires the ASC's parent actor to be owned by a locally controlled player:
you can only execute abilities on actors you control. Interacting with bots, NPCs and other
server-owned actors goes through a locally owned actor — usually the player's pawn — plus a
replicated ability or another server call; the server then has authority to change the NPC.

## Setup

GAS ships as a plugin that must be enabled for the project, and its modules must be listed in
the consuming module's `.Build.cs` (see `unreal-build.md` for the dependency rules). Attribute
sets, abilities and effects are then authored as C++ classes and data assets. The Lyra sample
is Epic's reference implementation of the whole stack. `[community]`

## Review checklist

- [ ] Does this game actually need composable, data-driven abilities, or is GAS being adopted
      because it is the "modern" answer?
- [ ] Is any gameplay consequence attached to a Gameplay Cue instead of an Ability Task?
- [ ] Are attribute clamps implemented in code rather than trusted to the unimplemented
      Min/Max columns?
- [ ] Do instant effects target base values and duration effects current values, deliberately?
- [ ] Are tags, cues and attribute changes applied through Gameplay Effects so rollback can
      work?
- [ ] Does any client-side code assume it can see remote actors' abilities or effects?
- [ ] Does any ability activate on an actor the calling client does not control?

<!-- sources: epic-ue-docs, maystudios-unreal, kevinpbuckley-ue -->
