# UI: Control nodes, containers, themes, focus

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`)

## Contents

- [Control, not Node2D](#control-not-node2d)
- [Anchors and offsets](#anchors-and-offsets)
- [Containers own their children](#containers-own-their-children)
- [Size flags](#size-flags)
- [`mouse_filter` defaults decide who gets the click](#mouse_filter-defaults-decide-who-gets-the-click)
- [Focus and gamepad navigation](#focus-and-gamepad-navigation)
- [Themes versus per-node overrides](#themes-versus-per-node-overrides)
- [Scene as the source of truth](#scene-as-the-source-of-truth)
- [HUDs and CanvasLayer](#hudsand-canvaslayer)
- [Version gates](#version-gates)
- [Old patterns](#old-patterns)

Describing a UI means node types, Inspector property names and exported-variable wiring.
It does not mean menu paths, dock positions or toolbar locations: those move between
Godot versions and are the least reliable thing to state.

## Control, not Node2D

UI belongs to the `Control` tree. A `Control` has a rect (`position`, `size`,
`custom_minimum_size`), anchors, a `Theme` chain, a focus mode and a `mouse_filter`.
Parenting a `Button` under a `Node2D` gives up theming inheritance and focus routing;
the button still draws, which is why the mistake survives.

## Anchors and offsets

Anchors are fractions of the parent's rect that each edge sticks to; offsets are pixel
deltas from the anchored point. Setting `position` while all four anchors sit at 0 pins
the control to the top-left and it does not move when the window resizes.

Set anchors with the **method**:

```gdscript
c.set_anchors_preset(Control.PRESET_FULL_RECT)          # anchor_right/bottom become 1.0
c.set_anchors_and_offsets_preset(Control.PRESET_CENTER) # anchors plus offsets in one call
```

Assigning the `anchors_preset` property from code does nothing:

```gdscript
c.set("anchors_preset", Control.PRESET_FULL_RECT)
c.anchor_right      # still 0.0
```

`anchors_preset` is an internal, editor-facing property; its setter returns early unless
`layout_mode` is already Anchors or Uncontrolled, and a `Control` created from code is in
Position mode. There is no error — the anchors are simply never touched. `PRESET_FULL_RECT`
is `15`, and `set_anchors_preset(15)` sets `anchor_right`/`anchor_bottom` to `1.0` as
expected.

`grow_horizontal`/`grow_vertical` decide which way a control grows when its minimum size
exceeds its rect — relevant for labels with dynamic text inside a fixed layout.

## Containers own their children

A `Container` recomputes its children's `position` and `size` on every sort. A child's
own `position`, `size` and anchors are discarded:

```gdscript
var vb := VBoxContainer.new()
vb.size = Vector2(200, 200)
add_child(vb)
var child := Control.new()
child.custom_minimum_size = Vector2(50, 50)
vb.add_child(child)
child.position = Vector2(999, 999)
child.set_anchors_preset(Control.PRESET_FULL_RECT)
# two frames later:
child.position      # (0, 0)      - overwritten by the sort
child.size          # (200, 50)   - container width, minimum height
child.anchor_right  # 0.0         - preset had no effect
```

So the fix for "my controls all pile up at the origin" is a container, and the fix for
"the container ignores my position" is to stop setting it. The levers you do have inside
a container are `custom_minimum_size`, `size_flags_horizontal`/`vertical`, and the
container's own separation and alignment properties. To free-place a node, take it out of
the container, or give it a plain `Control`/`PanelContainer` parent.

Container choice:

| Container | Use for |
|---|---|
| `VBoxContainer` / `HBoxContainer` | stacks; the default for menus and rows |
| `GridContainer` | inventories, fixed-column grids |
| `MarginContainer` | padding around a single child, including safe areas |
| `CenterContainer` | centring one child at its minimum size |
| `PanelContainer` | a themed background sized to its child |
| `ScrollContainer` | scrolling; the child needs a minimum size larger than the viewport |
| `AspectRatioContainer` | letterboxing a child |
| `SubViewportContainer` | embedding a `SubViewport`, e.g. 3D inside UI |

Layout is computed bottom-up from minimum sizes, so a `ScrollContainer` whose child has
no minimum size scrolls nowhere, and a `Label` with `autowrap_mode` set reports a
minimum size that depends on the width it is given — which is why a wrapping label inside
a shrinking container can oscillate.

## Size flags

`size_flags_horizontal`/`size_flags_vertical` are bitfields telling the parent container
how to distribute leftover space. Default is `SIZE_FILL` (`1`).

| Flag | Effect |
|---|---|
| `SIZE_FILL` | Take the space the container assigns |
| `SIZE_EXPAND` | Claim a share of the leftover space |
| `SIZE_EXPAND_FILL` | Both; the usual choice for "this one grows" |
| `SIZE_SHRINK_BEGIN` / `SIZE_SHRINK_CENTER` / `SIZE_SHRINK_END` | Stay at minimum size, aligned within the assigned space |

`size_flags_stretch_ratio` divides the leftover space among several expanding siblings.
A row where every child expands equally is the default; a 2:1 split is two expanding
children with ratios `2.0` and `1.0`.

## `mouse_filter` defaults decide who gets the click

`Control.mouse_filter` defaults to `MOUSE_FILTER_STOP` (`0`), and most container-ish and
decorative nodes inherit that default:

| Node | Default |
|---|---|
| `Control`, `Panel`, `ColorRect`, `Button` | `STOP` (0) |
| `TextureRect` | `PASS` (1) |
| `Label` | `IGNORE` (2) |

`STOP` marks the event handled and blocks propagation, so a full-rect `ColorRect` used as
a tint, or a `Panel` used as a backdrop, swallows every click beneath it — the buttons
are there, they receive nothing. Set `MOUSE_FILTER_IGNORE` on anything purely decorative.
`PASS` receives the event and bubbles it to the parent control if unhandled, which is
what you want for a clickable card that also wants hover on its children.

`IGNORE` does not block anything and does not get `mouse_entered`/`mouse_exited`. One
sharp edge: switching a control to `IGNORE` while it is hovered emits `mouse_exited`.

For gameplay input under a HUD, the reliable pattern is `_gui_input` on controls and
`_unhandled_input` on the gameplay node — `_unhandled_input` only sees what no control
consumed, so a correctly filtered HUD needs no explicit "is the mouse over UI" check.

## Focus and gamepad navigation

Directional input does nothing when nothing has focus, so a menu opened by controller
must claim it:

```gdscript
func _ready() -> void:
    ($Menu/PlayButton as Control).grab_focus()
```

`focus_mode` must not be `FOCUS_NONE` (buttons default to `FOCUS_ALL`, most other
controls to none). Auto-neighbour resolution works for simple grids; for anything
irregular set `focus_neighbor_left/top/right/bottom`, plus `focus_next`/`focus_previous`
for tab order. When a focused control is hidden or freed, focus is lost and navigation
dies silently — re-grab it when closing a submenu.

## Themes versus per-node overrides

A `Theme` resource assigned to a top-level `Control` is inherited by the whole subtree
and keyed by node type plus optional type variation. Per-node overrides are the escape
hatch:

```gdscript
$Title.add_theme_font_size_override("font_size", 32)
$Title.add_theme_color_override("font_color", Color.GOLD)
$Panel.add_theme_stylebox_override("panel", preload("res://ui/panel.tres"))
```

Use the `Theme` for anything that appears more than once; overrides are per-instance
exceptions. A project that styles every button with `add_theme_*` has no theme, and
restyling it means touching every scene. `theme_type_variation` on a control selects a
named variant from the theme ("DangerButton") without a second theme resource.

## Scene as the source of truth

The `.tscn` holds the layout. Opening a screen's scene should show its real composition
before any script runs. Runtime code populates text, textures, counts, availability and
transient feedback; it does not build or relocate the primary hierarchy. A menu assembled
in `_ready()` cannot be reviewed, cannot be edited by a designer, and regresses on every
refactor because nothing visual is under version control.

The corollary for generated scenes: a `.tscn` where every node carries `parent="."` loads
with no errors at all and stacks every `Control` at the origin. Build scene trees through
the scene API, not by writing `.tscn` text.

## Version gates

| Version | Change |
|---|---|
| `(Godot 4.7)` | `Control.accessibility_live` moved from `DisplayServer.AccessibilityLiveMode` to `AccessibilityServer.AccessibilityLiveMode` |
| `(Godot 4.7)` | `RichTextLabel.add_image`/`update_image` take `float` width and height, and `width_in_percent`/`height_in_percent` became `width_unit`/`height_unit` taking `RichTextLabel.ImageUnit`; the `UPDATE_WIDTH_IN_PERCENT` enum field was renamed `UPDATE_WIDTH_UNIT` |
| `(Godot 4.7+)` | `Control` gained `offset_transform_*` properties that translate, rotate and scale a control without disturbing container layout |

## Old patterns

<details>
<summary>Godot 3.x Control properties</summary>

`rect_size` → `size`, `rect_position` → `position`, `rect_min_size` →
`custom_minimum_size`, `rect_pivot_offset` → `pivot_offset`. `margin_*` became
`offset_*`. `Popup`-based menus were reworked into `Window` subclasses, so a 3.x
`popup_centered` flow needs revisiting rather than renaming.

</details>

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, haxqer-godot, godot-prompter, zimo-godot-ui -->
