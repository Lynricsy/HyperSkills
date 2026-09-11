# Runtime architecture

Verified against: base library 3.x, `miniprogram-api-typings` 5.2.3, `glass-easel` 1.2.0.

## Contents

- [Two threads, four layers](#two-threads-four-layers)
- [Component framework: exparser and glass-easel](#component-framework-exparser-and-glass-easel)
- [Renderer: WebView and Skyline](#renderer-webview-and-skyline)
- [Which combination a page is running](#which-combination-a-page-is-running)
- [Where WXS runs, and why it differs](#where-wxs-runs-and-why-it-differs)
- [What crosses the thread boundary](#what-crosses-the-thread-boundary)
- [The four files of a page](#the-four-files-of-a-page)
- [Component options that change the runtime](#component-options-that-change-the-runtime)
- [Reading a base library version gate](#reading-a-base-library-version-gate)

## Two threads, four layers

A mini program runs its JavaScript in a logic layer (a JSCore-style engine) and its
interface in a view layer, on two separate threads. The logic layer is **single
threaded and shared by every page**, including pages that are currently hidden — a
background page's timer competes with the foreground page for the same thread. On some
platforms the view layer's WebViews also share one thread, so a hidden page's rendering
can stall the visible one.

The layer split is not the whole picture. Inside it, two pieces are independently
swappable **per page**:

```
logic layer (JS)                 view layer
┌──────────────────────┐         ┌───────────────────────────┐
│ App / Page / Component│  data  │ component framework        │
│ business JS           │ ─────► │   exparser | glass-easel   │
│ wx.* APIs             │        │        ▼                   │
│                       │ ◄───── │ renderer                   │
└──────────────────────┘  events │   WebView  | Skyline       │
                                  └───────────────────────────┘
```

- The **component framework** owns `Page`, `Component`, `setData`, the event system and
  WXML semantics.
- The **renderer** owns the built-in components and which WXSS rules actually apply.

Two consequences that get missed: a symptom described as "setData is slow" is almost
always a component-framework cost, while one described as "the style does not apply" is
almost always a renderer difference. And the renderer constrains the framework — Skyline
requires glass-easel, but glass-easel does not require Skyline.

## Component framework: exparser and glass-easel

`exparser` is the traditional framework and is still the default. `glass-easel` is the
newer one; it is an open-source project (MIT) and ships extra APIs plus a different
update algorithm. It is selected with `componentFramework: "glass-easel"` in `app.json`,
or per page.

glass-easel additions that do not exist under exparser:

| API | Purpose |
|---|---|
| `updateData(obj)` | Same shape as `setData` but does not apply to the template yet |
| `replaceDataOnPath(pathArray, value)` | Update one field addressed by an array path |
| `spliceArrayDataOnPath(pathArray, index, del, inserts)` | Array splice without rebuilding the array |
| `applyDataUpdates()` | Flush accumulated `updateData`/`replace`/`splice` calls |
| `groupUpdates(cb)` | Accumulate inside the callback and flush once on return |
| `dataDeepCopy`, `propertyPassingDeepCopy`, `propertyEarlyInit` options | Trade copying safety for update cost |
| `dynamicSlots` | Slot content created on demand rather than always |

`groupSetData(cb)` exists on both and does something different: it keeps several real
`setData` calls from showing an intermediate frame.

glass-easel supports the **WebView** renderer from base library **3.8.12**, so adopting
it is no longer coupled to a Skyline migration. Switching framework changes WXML
compilation subtly; enable it per page first and compare, rather than flipping the
whole app.

## Renderer: WebView and Skyline

WebView is the default. Skyline renders on its own thread, shares one rendering instance
across pages instead of one WebView per page, and drops a set of web behaviours that
were only ever WebView implementation details (page-level scrolling, the native
navigation bar, `display: inline`, `position: sticky`, standard stacking contexts).

Enabling Skyline is three keys in `app.json`, not one:

```json
{
  "renderer": "skyline",
  "componentFramework": "glass-easel",
  "lazyCodeLoading": "requiredComponents"
}
```

plus `"navigationStyle": "custom"` on every Skyline page. Missing
`componentFramework` is the usual cause of "I set the renderer and nothing changed".

## Which combination a page is running

Three ways, in increasing reliability:

```javascript
// 1. inside a page or component instance
Page({
  onLoad() {
    console.log(this.renderer)   // 'webview' | 'skyline'
  },
})

// 2. asynchronously, anywhere
wx.getSkylineInfo({ success: (res) => console.log(res) })

// 3. on device: menu > 开发调试 > Switch Render to force Auto / WebView / Skyline
```

`this.renderer` is declared on the page instance in the official typings, so it is
type-safe and needs no feature detection. Do not infer the renderer from a base library
version — renderer selection is per page and can be overridden at run time.

## Where WXS runs, and why it differs

WXS is the one piece of code whose *thread* depends on the component framework:

- Under **glass-easel**, WXS runs in the **logic layer**. On each update the framework
  works out which data-binding expressions need re-evaluating and calls only the WXS
  functions inside them. Updating `s` in `{{ foo.f1(s) }} {{ foo.f2(t) }}` calls `f1`
  and not `f2`.
- Under **exparser**, WXS runs in **both** layers, and every WXS function in the Shadow
  tree is executed once per layer on every update.

WXS event handlers (`bindtap="{{ mod.handler }}"`) are the exception: they run only in
the view layer under both frameworks and share no globals with the rest of the WXS code.
That isolation is what makes them useful for gesture-driven animation — they respond
without a round trip to the logic layer.

## What crosses the thread boundary

Only JSON-serialisable data. Practical consequences:

- A `Date`, a `Map`, a class instance or a function placed in `data` does not survive.
- A key whose value is `undefined` is skipped entirely, leaving the previous value in
  place with no error.
- Event objects arrive from the view layer already serialised, so a handler cannot get
  a live DOM-like node out of `event.target`; use `SelectorQuery` or
  `IntersectionObserver`, both of which are asynchronous because they too cross threads.
- `wx.createSelectorQuery()` called at page scope selects across the page; inside a
  component you must scope it with `this.createSelectorQuery()` or `.in(this)`, or the
  selectors silently match nothing.

## The four files of a page

`page.js`, `page.wxml`, `page.wxss`, `page.json`. The `.json` is not optional
decoration: it carries `usingComponents`, `navigationStyle`, `disableScroll`, `renderer`
and `componentFramework`, all of which are page-scoped overrides of `app.json`. A page
directory missing its `.json` inherits every global default, which is how a single
Skyline page ends up rendering under WebView.

A custom component is the same four files plus `"component": true` in the `.json`.

## Component options that change the runtime

Declared under `options` in `Component({ … })`:

| Option | Effect | Since |
|---|---|---|
| `multipleSlots` | Enables named slots; disables the single-slot fast path | — |
| `styleIsolation` | `isolated` \| `apply-shared` \| `shared` \| `page-isolated` \| `page-apply-shared` \| `page-shared` | — |
| `addGlobalClass` | Shorthand for letting page styles reach in | — |
| `pureDataPattern` | RegExp; matching `data` fields never reach the template | 2.8.2 |
| `virtualHost` | The component produces no host node of its own | 2.11.2 |

`virtualHost` removes a layout box, which is usually what you want for a wrapper
component, but it also makes `class` and `style` on the component tag do nothing —
re-expose them as an external class and a property. Under glass-easel it additionally
makes `getBackendElement()` return `null`.

## Reading a base library version gate

Every version-sensitive API in the official typings carries its minimum base library
version in its doc comment. Install the declarations and let the editor show them rather
than guessing:

```bash
npm i -D miniprogram-api-typings
```

Then in `tsconfig.json`:

```json
{ "compilerOptions": { "types": ["miniprogram-api-typings"] } }
```

When a rule must hold on older clients, gate it with `wx.canIUse('…')` rather than a
version comparison — `canIUse` accepts an API, a parameter, a return field, a component
or a component property, and is the only check that stays correct as the platform
changes what a given version supports.

<!-- sources: wx-official-docs, wx-api-typings, wx-glass-easel, wx-skyline-skills -->
