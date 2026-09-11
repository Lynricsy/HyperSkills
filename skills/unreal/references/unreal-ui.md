# UI: UMG and Slate (UE 5.8)

Verified against: Unreal Engine 5.8 documentation. Every claim here is `[official]` unless
marked otherwise; nothing in this file was checked against a running engine.

## Contents

- [Two frameworks, one boundary](#two-frameworks-one-boundary)
- [The update model decides the cost](#the-update-model-decides-the-cost)
- [Resolution and scale](#resolution-and-scale)
- [Layout: Fill versus Auto](#layout-fill-versus-auto)
- [Render transforms are not layout](#render-transforms-are-not-layout)
- [Art for UI](#art-for-ui)
- [Reuse](#reuse)
- [Optimizations the documentation actually lists](#optimizations-the-documentation-actually-lists)
- [Widgets from C++](#widgets-from-c)
- [Review checklist](#review-checklist)

## Two frameworks, one boundary

UMG (Unreal Motion Graphics) is the designer-facing widget system: Widget Blueprints with a
Designer tab and a graph. Slate is the C++ UI framework beneath it, and it is what the editor
itself is built from. Game HUDs and menus are UMG; editor tooling and custom detail panels are
Slate. Mixing them is normal — a UMG widget can host a Slate widget — but a game feature
should not be authored in Slate because C++ feels tidier: it loses the designer workflow that
UMG exists to provide.

Widget visuals are the engine's concern here. Visual design decisions — hierarchy, type
scale, colour, spacing, motion language — belong to the `frontend-design` skill.

## The update model decides the cost

Epic's own guidance: **use events to drive UI updates whenever possible, instead of Bindings
or Tick events.**

- A **Property Binding** is evaluated every frame to see whether it should change. That is
  acceptable for a small screen with a handful of frequently changing values; it is the wrong
  default for a complex screen where several properties change at specific moments.
- An **event-driven** update writes to the widget when the underlying value changes — a
  delegate on the gameplay object, a RepNotify on a replicated property, or a tag-based
  message.
- A per-frame `SetText` with a freshly formatted string pays layout invalidation plus string
  and `FText` allocation on every frame, for a label a player reads once a second.

The decision rule the documentation gives: few values changing frequently → a binding is
defensible; several values changing at specific times → events.

## Resolution and scale

- Pick a target resolution and author every Widget Blueprint at it, using the ScreenSize
  drop-down. Previewing other sizes is fine; *authoring* across different sizes produces
  screens where some elements scale and others do not.
- Author at a DPI Scale of 1.0 so that everything is created at the same scale and scales
  uniformly later. Two widgets authored at different scales will not scale together.

## Layout: Fill versus Auto

In box panels, a slot's size rule changes who decides the size:

- **Auto** — the widget asks for exactly the room it needs, and the panel inspects each child
  to size it. This is what lets a Scale Box scale a group of children so they all fit.
- **Fill** — the widget takes as much space as it can. The standard main-menu shape is Auto
  rows at the top and bottom with a Fill container between them, which pushes the rows to the
  screen edges at any resolution.

## Render transforms are not layout

Render Transforms are for temporary transforms — animating a pulse, a nudge, a shake. They
are not computed as part of layout, so using one for a permanent size change produces a widget
that does not scale correctly for other resolutions. To change a widget's size permanently,
wrap it in a Scale Box, which performs layout scale.

## Art for UI

- Decide the target resolution and scale **before** authoring art, or textures end up larger
  or smaller than needed and have to be stretched or skewed to fit.
- Minimize built-in padding inside imported textures: scaling is based on the texture size, so
  a frame with baked-in padding scales by the wrong reference. Use UMG's padding instead.
- Split art that should tile — corners separate from panels — and use the `Border` draw mode,
  which supports tiling, rather than stretching one image.

## Reuse

Any Widget Blueprint you author is a User Widget and appears in the Palette under User
Created, so it can be dropped into other widgets. Functionality used in several screens
belongs in its own widget rather than being rebuilt per screen. On the Designer tab,
right-clicking a widget in the Hierarchy wraps or replaces it without re-parenting by hand.

## Optimizations the documentation actually lists

- Use textures instead of materials for UI art wherever possible.
- Drive updates from events rather than Bindings or Tick.
- Cache widgets that rarely change (an invalidation/retainer strategy).
- Use the Widget Reflector (`Ctrl+Shift+W`) for statistics about the live widget tree — the
  tool that answers "how many of these widgets are actually in the viewport".

## Widgets from C++

```cpp
// In an owning PlayerController or HUD, not in every actor that wants to show something
if (UUserWidget* Widget = CreateWidget<UUserWidget>(PlayerController, ThreatWidgetClass))
{
    Widget->AddToViewport();
}
```

Practical constraints:

- `CreateWidget` returns null when the class is unset; `AddToViewport` on an unchecked pointer
  is a crash waiting for one unassigned Blueprint property.
- Look up child widgets once and cache the result. Resolving a widget by name every frame
  pays the lookup and then crashes when the widget is renamed in the Designer.
- UI is local. Creating a widget on a dedicated server, or once per actor instead of once per
  local player, produces either wasted work or a stack of identical overlapping widgets —
  which looks like flicker, not like a leak.
- The widget lifetime belongs to whatever owns the screen. A widget created by a transient
  actor outlives it unless something removes it.

## Failure symptom table

| Symptom | Cause to check first |
|---|---|
| Label flickers or fights itself | More than one instance of the widget in the viewport — count them in the Widget Reflector before touching the logic |
| Game-thread cost grows with the number of on-screen values | Property Bindings evaluated every frame, or a `Tick`-driven update |
| Widget looks right in the Designer and wrong in game | Authored at a different screen size or DPI scale than the project targets |
| Widget does not scale with resolution | A Render Transform used for a permanent size change instead of a Scale Box |
| Background image stretches at other resolutions | One baked texture instead of tiled pieces with the `Border` draw mode |
| Crash the first time the screen opens | Unset widget class, or a `GetWidgetFromName` result used unchecked after a rename |

## Review checklist

- [ ] Is any widget value driven by a Binding or by `Tick` that an event could drive?
- [ ] Is any per-frame string formatted for a label that changes rarely?
- [ ] Was every Widget Blueprint authored at the project's target resolution and DPI scale 1.0?
- [ ] Is any permanent size change implemented with a Render Transform instead of a Scale Box?
- [ ] Are `CreateWidget` results and `GetWidgetFromName` lookups checked, and cached?
- [ ] Is the widget created once per local player, by an owner that outlives it?
- [ ] Does the viewport contain the number of widget instances you expect (Widget Reflector)?

<!-- sources: epic-ue-docs, gamedev-unreal, kevinpbuckley-ue -->
