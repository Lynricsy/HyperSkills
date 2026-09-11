# Unity UI: choosing and implementing uGUI, UI Toolkit and IMGUI

Verified against: Unity 6.3 LTS (6000.3); the recommendation table was cross-checked on the
Unity 6.6 (6000.6) manual and is identical.

## Contents

- [Unity's own recommendation](#unitys-own-recommendation)
- [Feature gaps that decide the choice](#feature-gaps-that-decide-the-choice)
- [uGUI: what costs frame time](#ugui-what-costs-frame-time)
- [UI Toolkit: the runtime shape](#ui-toolkit-the-runtime-shape)
- [Custom elements and UXML registration](#custom-elements-and-uxml-registration)
- [USS versus CSS](#uss-versus-css)
- [Data binding](#data-binding)
- [Text](#text)
- [Input and event routing](#input-and-event-routing)
- [IMGUI](#imgui)
- [Testing UI](#testing-ui)

## Unity's own recommendation

Three systems ship with the engine. Unity's documented recommendation `[official]`:

| Context | Recommended | Alternative |
|---|---|---|
| Runtime (game UI) | **uGUI (Unity UI)** | UI Toolkit |
| Editor | **UI Toolkit** | IMGUI |

This is unchanged from Unity 6.3 LTS through 6.6, so "the docs are behind" is not an
explanation. The widespread belief that UI Toolkit is the default for runtime UI and uGUI
is legacy is wrong on both halves: **IMGUI** is the legacy system, and it is the one Unity
says not to use for runtime UI.

Choose UI Toolkit for runtime when the project has:

- a lot of UI, authored by designers who want a document/stylesheet workflow;
- many target resolutions;
- textureless UI rendering;
- UI positioned and lit inside the 3D world;
- advanced visuals with custom shaders and materials.

Stay on uGUI when you need in-scene authoring, Inspector-serialized events, keyframed UI
animation, or straightforward referencing from MonoBehaviours. Mixing both in one project
is normal (HUD in one, menus in the other); mixing both in one screen is not.

## Feature gaps that decide the choice

From Unity's own comparison table `[official]` — the entries where the two differ:

| Feature | UI Toolkit | uGUI |
|---|---|---|
| In-scene authoring | no | yes |
| Serialized events (wire a callback in the Inspector) | no | yes |
| Keyframed animation | not the recommended path | yes |
| Easy referencing from MonoBehaviours | indirect (query by name/class) | direct |

Everything else in that table — WYSIWYG authoring, nested reusable components, rich text,
scalable text, font fallbacks, adaptive layout, Input System support, render-pipeline
compatibility, screen-space and world-space rendering — is supported by both.

"No serialized events" is the one that bites mid-project: a team that wired 200 buttons to
`UnityEvent`s in the Inspector cannot port them to UI Toolkit without rewriting the wiring
in C#.

## uGUI: what costs frame time

uGUI's cost is concentrated in **canvas rebuilds**. A canvas batches its children into
meshes; changing anything that affects geometry marks the canvas dirty and rebuilds the
whole thing.

- Split canvases by update frequency. One canvas for the static frame, one for the
  per-frame HUD numbers. A single canvas containing both rebuilds everything whenever a
  number changes.
- Setting `Text.text` to the *same* string still dirties the element in older uGUI
  versions; compare before assigning regardless, because it also avoids the string
  allocation.
- Disable `Raycast Target` on everything that is not interactive. Every raycast target is
  tested on every pointer event, and a full-screen decorative image is the usual culprit
  behind "my button stopped working".
- Prefer disabling a `CanvasGroup`'s `alpha`/`interactable` or the `Canvas` component over
  `SetActive(false)` on a large subtree: deactivation destroys the batch and the next
  activation rebuilds it.
- Layout groups (`VerticalLayoutGroup`, `ContentSizeFitter`) are recomputed on rebuild and
  nest expensively. For long lists use a pooled scroll view, not a layout group with 500
  children.
- `Screen Space - Overlay` canvases do not render through the camera and ignore
  post-processing; `Screen Space - Camera` and `World Space` do. Choosing the wrong one is
  why "my UI is not affected by the bloom".

## UI Toolkit: the runtime shape

Runtime UI Toolkit needs a `UIDocument` component referencing a `PanelSettings` asset and a
`VisualTreeAsset` (UXML). The tree is not GameObjects; nothing about it appears in the scene
hierarchy.

```csharp
public class HudController : MonoBehaviour
{
    [SerializeField] private UIDocument _document;
    private Label _score;

    private void OnEnable()
    {
        var root = _document.rootVisualElement;
        _score = root.Q<Label>("score");          // by name, from the UXML
        root.Q<Button>("pause").clicked += Pause; // unsubscribed below
    }

    private void OnDisable() => _document.rootVisualElement.Q<Button>("pause").clicked -= Pause;
}
```

Points that cause real bugs:

- `rootVisualElement` is only valid once the `UIDocument` is enabled. Querying it in
  `Awake` returns null.
- `Q<T>(name)` is a tree search. Cache the elements in `OnEnable`; do not query per frame.
- Elements are pure C# objects; `Destroy` does not apply and neither does the GameObject
  lifecycle. Removal is `parent.Remove(element)`.
- Panel sort order across several `UIDocument`s comes from `PanelSettings` /
  `UIDocument.sortingOrder`, not from hierarchy order.

## Custom elements and UXML registration

Custom `VisualElement` types are registered with attributes, and the old pattern is
deprecated `[verified]`:

```csharp
[UxmlElement]                                  // replaces the UxmlFactory nested class
public partial class HealthBar : VisualElement
{
    [UxmlAttribute] public float value { get; set; }   // replaces UxmlTraits
}
```

`UxmlFactory` and `UxmlTraits` carry `[Obsolete("... will be removed. Use
UxmlElementAttribute instead.")]` in Unity 6.3. The class must be `partial` — the attribute
generates the registration code. Code written against tutorials older than Unity 2023.2
will compile with warnings and then stop compiling.

## USS versus CSS

USS is CSS-*like*, not CSS. The differences that waste the most time:

- lengths are `px` and `%` only — no `em`, `rem`, `vh`, `vw`;
- the layout engine is Flexbox, and `display: flex` is the **default**; there is no CSS
  Grid, no `float`, no `position: fixed`/`sticky` (only `relative` and `absolute`);
- selectors support type, class (`.name`), name (`#name`), descendant and a limited
  pseudo-state set (`:hover`, `:active`, `:focus`, `:checked`, `:disabled`); no
  `:nth-child`, no attribute selectors, no media queries;
- custom properties exist (`--my-color`) but `calc()` support is limited;
- transitions animate a documented subset of properties; there are no `@keyframes`.

Reaching for a CSS idiom and finding it silently ignored — USS drops unknown properties
with a console warning at import, which is easy to miss — is the standard first day.

## Data binding

Runtime binding (Unity 6+) connects a `VisualElement` property to a data source without
per-frame polling:

- set `dataSource` on an element (or in UXML) and declare bindings with
  `SetBinding` / the UXML binding syntax;
- the source should implement `INotifyBindingPropertyChanged` (or be a
  `ScriptableObject`/`MonoBehaviour` whose changes you publish) so updates propagate;
- without change notification, bindings update on the binding system's own cadence, which
  looks like "my label lags one frame" rather than an error.

If the project predates this, the older pattern is an explicit `schedule.Execute(...)`
refresh or a C# event raising a setter. Do not poll in `Update`.

## Text

- **TextMeshPro** is the text renderer for uGUI (`TextMeshProUGUI`) and for world-space
  text (`TextMeshPro`). It is SDF-based, so it stays crisp at any scale, unlike the legacy
  `Text` component.
- A TMP font asset has a fixed atlas. A glyph outside it either falls back (if a fallback
  list is configured) or renders as a box. CJK and user-generated text need dynamic
  atlases or a fallback chain — this is the "Chinese text shows squares in the build" bug.
- UI Toolkit has its own text backend and uses TMP font assets through `PanelSettings`;
  the uGUI TMP components do not apply there. "Always use TextMeshPro" is uGUI advice, not
  a universal rule.
- Rich text tags work in both systems but the supported tag sets differ.

## Input and event routing

- uGUI needs an `EventSystem` in the scene plus an input module. With the Input System
  package that is `InputSystemUIInputModule`; leaving the legacy `StandaloneInputModule`
  in place while the project uses the new Input System is why "nothing is clickable".
- UI Toolkit runtime panels also route through the `EventSystem` and the same input module.
- A UI element consuming a click does not automatically stop gameplay input. Gate gameplay
  input explicitly on UI state; relying on event bubbling to do it produces
  shoot-through-the-menu bugs.

## IMGUI

`OnGUI` is immediate-mode: it runs several times per frame (layout and repaint events), so
every allocation and every `Find` in it is multiplied. Use it for Editor tooling and
in-development debug overlays only — Unity explicitly does not recommend it for runtime UI.
For Editor UI, prefer UI Toolkit; IMGUI remains the fallback where UI Toolkit lacks a
control.

## Testing UI

Drive the UI through the same public methods the buttons call, and assert on state rather
than on pixels. For uGUI, `EventSystem`-level simulation in a Play-mode test is workable;
for UI Toolkit, query the element and invoke its event
(`element.SendEvent(ClickEvent.GetPooled())`). Screenshot comparison is brittle across
resolutions and should be reserved for a deliberate visual-regression suite.

<!-- sources: nicewolf-unity, unity-official-skills, unity-docs, unity-cs-reference -->
