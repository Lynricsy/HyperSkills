# Chaos physics, queries and sub-stepping (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]` unless
marked otherwise; nothing in this file was checked against a running engine.

## Contents

- [What Chaos covers](#what-chaos-covers)
- [Traces and queries](#traces-and-queries)
- [Sub-stepping](#sub-stepping)
- [Callback timing under sub-stepping](#callback-timing-under-sub-stepping)
- [Physics and the frame](#physics-and-the-frame)
- [Networked physics](#networked-physics)
- [Destruction](#destruction)
- [Cloth and character physics](#cloth-and-character-physics)
- [Debugging](#debugging)
- [Review checklist](#review-checklist)

## What Chaos covers

Chaos is Unreal's physics solution and is organized into separable systems: rigid-body
dynamics with collision response, constraints, damping and friction; asynchronous simulation;
networked physics; Chaos Destruction with Geometry Collections; Chaos Cloth; hair; fluid and
flesh simulation; vehicles; and Physics Fields for affecting a simulation in a region of
space. Character physics uses the Physics Asset Editor to build the bodies and constraints
attached to a skeletal mesh, so that simulated bodies can be blended with animation.

## Traces and queries

Traces are the part of physics that most gameplay code touches, and they are where per-frame
cost accumulates.

- **Simple versus complex collision.** Simple collision is the default for gameplay queries;
  complex collision traces the render geometry per triangle. Setting `bTraceComplex` on a
  trace against a skeletal mesh, every frame, for every candidate, multiplies per-triangle
  work by candidates by frame rate.
- Collision responses are configured per channel and per object type; a trace that returns
  nothing is usually a channel or response setting, not a broken trace.
- Ignore the tracing actor and, usually, the target: a trace that starts inside the owner's
  own capsule hits the owner and reports "blocked" before it travels anywhere.
- Where in the frame a trace runs changes its answer: see
  `unreal-gameplay-framework.md` for tick groups. A trace that must agree with the rendered
  frame belongs after the simulation (`TG_PostPhysics`).

## Sub-stepping

UE5 runs a variable frame rate; the solver prefers small fixed steps. Sub-stepping divides the
frame's time and ticks the simulation several times per frame. It is enabled in
*Project Settings > Physics*:

| Setting | Meaning |
|---|---|
| Substepping | On/off for the project |
| Substepping Async | Whether the async simulation sub-steps too |
| Max Substep Delta Time | Longest time a single sub-step may cover. A 0.05 s frame with a 0.025 s maximum becomes two sub-steps |
| Max Substeps | Hard cap on sub-steps per frame; a very long frame is split evenly into this many rather than into however many the delta implies |

Smaller max sub-step time means a more stable simulation at greater CPU cost. The visible
benefit is in complex physics assets — ragdoll jitter is the canonical case. Sub-stepping is
otherwise hidden: forces applied for one frame are applied across each sub-step, and target
locations are interpolated, so the *result* matches naive expectations at a bookkeeping cost
in CPU and memory.

Note the separate limit: Max Physics Delta Time caps how long a physics step may be at all.

## Callback timing under sub-stepping

Sub-stepping runs on a separate physics thread, and collision callbacks are deliberately
delayed until the final sub-step completes. Consequences:

- One frame can deliver **several callbacks for the same collision pair** — for example an
  overlap and its matching end-overlap in the same frame, when A hit B and bounced off.
- Callbacks are queued in sub-step order, so sub-step 1's callbacks arrive before sub-step
  2's.

Gameplay logic that assumes "one overlap event means the object is now overlapping" breaks
here — not under load, but as soon as sub-stepping is switched on. Write overlap handlers as
state transitions with a counter or a validity check, not as toggles.

## Physics and the frame

- Movement that must be picked up by the simulation happens before it (`TG_PrePhysics`);
  anything reading simulation results happens after it (`TG_PostPhysics`).
- `TG_DuringPhysics` gives no way to know whether the physics data is from this frame or the
  last, so only use it for logic that tolerates a frame of error.
- Large worlds use double-precision coordinates (Large World Coordinates); code that assumes
  `float`-sized world positions is a precision bug waiting for a big map. `[community]`

## Networked physics

Physics replication applies to actors that replicate movement and whose root component
simulates physics; the simulation runs on the client machine. The Default replication mode is
the legacy path, and other modes exist for physics-driven gameplay. Treat networked physics as
a deliberate design decision with its own mode selection, not as "replicate movement and hope
the simulations agree" — two machines simulating independently will not produce identical
results.

## Destruction

Chaos Destruction is built on Geometry Collections fractured from static meshes. Connection
Graphs shape how a structure collapses; World Support marks parts as kinematic and reduces the
need for anchor fields. The Cache System records per-frame transforms and events so complex
destruction can be replayed cheaply at runtime, and cached simulations can still go live on
interaction. Niagara consumes Chaos break and collision events, so destruction VFX is
data-driven rather than hand-triggered.

## Cloth and character physics

Chaos Cloth simulates with runtime-tunable parameters exposed to Blueprint (wind, and an
Animation Drive that deforms the cloth toward its parent skeletal mesh's animation), ships
visualization tools and console commands for debugging, and offers a machine-learning
simulation path for higher fidelity than a traditional solver. The Cloth Panel node editor
(UE 5.3+) authors a cloth asset usable with any skeletal or static mesh through the Chaos
Cloth component.

## Debugging

The Chaos Visual Debugger records the physics scene during gameplay and replays it in the
tool, letting you inspect any frame **or sub-step**. For a simulation that misbehaves once in
twenty attempts, a CVD recording is the difference between a repro and a guess.

## Review checklist

- [ ] Is any per-frame trace using complex collision where simple collision would answer?
- [ ] Does every trace ignore the actors it must ignore?
- [ ] Do traces that must match the rendered frame run after the simulation?
- [ ] Are overlap handlers written as state transitions, so duplicate callbacks in one
      sub-stepped frame are harmless?
- [ ] Is sub-stepping enabled deliberately, with Max Substeps chosen, rather than left at a
      value nobody picked?
- [ ] Does any networked-physics feature name the replication mode it relies on?
- [ ] Was a misbehaving simulation recorded with the Chaos Visual Debugger before being
      "fixed"?

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue -->
