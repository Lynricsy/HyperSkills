# Navigation and UI context

Verified against: OpenHarmony application-dev docs, `ui/arkts-navigation-introduction`, `arkts-navigation-architecture`, `arkts-navigation-jump`, `arkts-router-to-navigation`, `ui/arkts-global-interface`, `reference/apis-arkui/js-apis-router`; API availability cross-checked against `openharmony/interface_sdk-js` `api/@ohos.router.d.ts` and `api/@ohos.arkui.UIContext.d.ts`.

## Contents

- [Which mechanism](#which-mechanism)
- [Navigation anatomy](#navigation-anatomy)
- [Stack operations](#stack-operations)
- [NavDestination lifecycle](#navdestination-lifecycle)
- [Router to Navigation mapping](#router-to-navigation-mapping)
- [UIContext instead of global APIs](#uicontext-instead-of-global-apis)
- [Cross-package routes](#cross-package-routes)
- [Old patterns](#old-patterns)

## Which mechanism

Two page-navigation frameworks exist and only one is current.

| | `Navigation` | `@ohos.router` |
|---|---|---|
| Page unit | `NavDestination` inside a `Navigation` | `@Entry` component listed in `main_pages.json` |
| Status | current | **"Not Recommended"** in the API reference |
| Multi-device single/double column | `Auto` mode built in | not supported |
| Read a specific page's params | supported | not supported |
| Params may contain functions | object params | object params, **no methods inside** |
| Remove a specific route | `removeByIndexes`, `removeByName` | not supported |
| Route interception | `setInterception` | not supported |
| Access the stack object | yes | not supported |
| Shared-element transition | `geometryTransition` between `NavDestination`s | not supported |
| Title bar / toolbar | part of the component | not supported |
| Immersive pages | supported | needs window configuration |
| Lifecycle observation | `UIObserver.on('navDestinationUpdate')` | `UIObserver.on('routerPageUpdate')` |

On top of the module being not recommended, the **global** `router` API form is
**deprecated since API version 18**: `router.pushUrl`, `router.pushNamedRoute` and their
siblings were deprecated in favour of the `UIContext`-scoped `Router` obtained with
`UIContext.getRouter()` (available since API 10).

So there are two separate decisions in any "we use router" codebase:

1. Move off the global form onto `UIContext.getRouter()` — mechanical, do it immediately.
2. Move off `router` onto `Navigation` — structural, do it per feature.

New code goes straight to `Navigation`.

## Navigation anatomy

```ts
@Entry
@Component
struct Index {
  @Provide('pathStack') pathStack: NavPathStack = new NavPathStack();

  @Builder
  routeMap(name: string, param: object) {
    if (name === 'detail') { DetailPage({ param: param }) }
  }

  build() {
    Navigation(this.pathStack) {
      // home content
    }
    .navDestination(this.routeMap)
    .mode(NavigationMode.Auto)     // single or double column by width
    .titleMode(NavigationTitleMode.Mini)
  }
}
```

- `NavPathStack` is the stack object. Own exactly one per `Navigation` and share it through
  `@Provide`/`@Consume` (V1) or `@Provider`/`@Consumer` (V2) rather than passing it down by
  hand.
- The route map can be a `@Builder` branch as above, or a declarative
  `route_map.json` + `router_map` metadata entry, which is what you want for
  cross-package routes.
- `Navigation` can be nested and can live inside a modal, sheet or dialog, because it is an
  ordinary component. That is the structural advantage over `router`, whose pages sit under
  a fixed page-stack node.
- `NavigationMode.Auto` gives you single-column on narrow screens and split on wide ones
  without a second layout.

## Stack operations

| Operation | API |
|---|---|
| push by path / by destination | `pushPath`, `pushDestination` |
| replace | `replacePath`, `replacePathByName` |
| pop | `pop`, `popToName`, `popToIndex` |
| clear | `clear` |
| remove specific | `removeByIndexes`, `removeByName` |
| move | `moveToTop`, `moveIndexToTop` |
| inspect | `getAllPathName`, `getParamByName`, `getIndexByName`, `size` |
| intercept | `setInterception` |

`pushDestination` returns a promise that rejects when the target cannot be created, which
is the difference from `pushPath`: a typo in a route name surfaces as a rejected promise
instead of a silent no-op. Prefer it, and handle the rejection.

Use `setInterception` for login gates and "unsaved changes?" confirmations — it is the
supported replacement for `router`'s `showAlertBeforeBackPage`, and unlike an
`onBackPress` handler it also covers programmatic navigation.

**The router page stack holds at most 32 pages.** Pushing past that fails with error
`100003` ("Page stack error. Too many pages are pushed."). Any loop the user can walk —
product → detail → related product → detail — reaches it, and the default router mode
pushes a new instance even for the same URL. `Navigation` does not impose that ceiling, but
an unbounded stack is still a leak: use `replacePath` for same-level moves and
`popToName`/`removeByName` to collapse loops.

## NavDestination lifecycle

A `NavDestination` has its own lifecycle, and it is the one to use — page-level
`onPageShow`/`onPageHide` belong to `@Entry` components under the router framework:

```
onWillAppear → onAppear → onWillShow → onShown
             → onWillHide → onHidden → onWillDisappear → onDisappear
```

`onShown`/`onHidden` fire on every stack transition, including a push on top of you.
`onAppear`/`onDisappear` fire once per stack entry. Subscriptions belong to
`onAppear`/`onDisappear`; refresh-on-return belongs to `onShown`. Putting a data reload in
`onAppear` is the reason a screen shows stale data after the user pops back to it.

Intercept system back with `NavDestination`'s `onBackPressed` (return `true` to consume).

## Router to Navigation mapping

| Router | Navigation |
|---|---|
| `@Entry` page + `main_pages.json` entry | `NavDestination` + route map entry |
| `pushUrl({ url, params })` | `pathStack.pushPath({ name, param })` |
| `pushNamedRoute` | `pathStack.pushPathByName(name, param)` |
| `replaceUrl` / `replaceNameRoute` | `replacePath` / `replacePathByName` |
| `back()` / `back({ url })` | `pop()` / `popToName(name)` |
| `clear()` | `clear()` |
| `getParams()` | `param` on the `NavDestination`, or `getParamByName` |
| `getState()` / `getLength()` | `getAllPathName()`, `size`, `getIndexByName` |
| `showAlertBeforeBackPage` | `setInterception`, or `onBackPressed` |
| `pageTransition` with `duration: 0` | `Navigation`'s transition settings, global or one-shot |
| `onPageShow` / `onPageHide` | `onShown` / `onHidden` on `NavDestination` |

Migrate one feature at a time: wrap the feature's entry page in a `Navigation`, convert its
screens to `NavDestination`s, and leave the rest of the app on the router until its turn.
Both can coexist; a `Navigation` lives inside a page that the router still owns.

**Params cannot carry functions.** A `router` or `NavPathStack` param object is serialized,
so `{ onDone: () => … }` does not arrive. Pass a result back with `pop(result)` and read it
with the pop callback, or hold the callback in shared state keyed by an id you do pass.

## UIContext instead of global APIs

In the Stage model **one ArkTS engine can host several UI instances** — a single engine can
back two abilities and three windows. ArkUI's global APIs infer which UI instance they
belong to by inspecting the call chain. That inference works for synchronous UI code and
fails for asynchronous APIs and non-UI APIs: the operation then lands on the wrong window
or silently does nothing.

Replace the global forms with `UIContext` methods. Be careful with the versions here,
because the prose guide and the SDK declarations say different things and the declarations
win: `UIContext.getRouter()` and `getPromptAction()` are `@since 10` in
`api/@ohos.arkui.UIContext.d.ts`, and `UIContext.isAvailable()` is `@since 20`. **API 18 is
when the global `router` functions were deprecated**, not when the replacements appeared —
so "the UIContext API is too new for us" is never a valid objection.

| Global | `UIContext` |
|---|---|
| `@ohos.router` | `getRouter()` |
| `@ohos.promptAction` | `getPromptAction()` |
| `AlertDialog` | `showAlertDialog()` |
| `ActionSheet` | `showActionSheet()` |
| `DatePickerDialog` / `TimePickerDialog` / `TextPickerDialog` | `showDatePickerDialog()` / `showTimePickerDialog()` / `showTextPickerDialog()` |
| `ContextMenu` | `getContextMenuController()` |
| `@ohos.animator` | `createAnimator()` |
| `@ohos.mediaquery` | `getMediaQuery()` |
| `@ohos.font` | `getFont()` |
| `@ohos.measure` | `getMeasureUtil()` |
| `@ohos.arkui.componentSnapshot` / `componentUtils` / `dragController` / `inspector` / `observer` | `getComponentSnapshot()` / `getComponentUtils()` / `getDragController()` / `getUIInspector()` / `getUIObserver()` |
| `focusControl` / `cursorControl` | `getFocusControl()` / `getCursorControl()` |
| `getContext()` | `getHostContext()` |
| `LocalStorage.getShared()` | `getSharedLocalStorage()` |
| `vp2px` / `px2vp` / `fp2px` / `px2fp` / `lpx2px` / `px2lpx` | same names on `UIContext` |

`CalendarPickerDialog` has no `UIContext` equivalent.

Be precise about status: the **global `router` API form is deprecated** (since API 18),
while `@ohos.promptAction`, `AlertDialog` and the rest are **not deprecated** — the
documentation recommends the `UIContext` form because of the ambiguity above. Claiming
they are deprecated is wrong and gets corrected by whoever checks the reference.

`@ohos.promptAction` additionally cannot be used in a UIAbility file declaration or inside
a UIAbility lifecycle callback at all: its APIs require a component instance to exist. A
toast in `onCreate` does not appear.

Get the context from the component (`this.getUIContext()`) and keep it, rather than
reaching for a global helper deep inside a callback. If a utility module needs to show a
toast, pass the `UIContext` in — a shared utility that calls
`promptAction.showToast` directly is exactly the case the inference cannot resolve.

The framework does propagate a UI-instance identifier across async boundaries (including
Node-API calls, promises and Worker messages) so that a task dispatched from one window and
resumed later is still attributed correctly. That mechanism is what makes `UIContext`
reliable; it is not a reason to keep using the global APIs.

## Cross-package routes

`Navigation` can route to pages inside an HSP or a HAR. Declare the destinations in the
package's `route_map.json` and reference it from `module.json5` metadata, then push by name.
That keeps the host module from importing the feature package's components directly, which
is what allows the feature to be loaded on demand.

## Old patterns

<details><summary>Global router calls</summary>

```ts
import { router } from '@kit.ArkUI';
router.pushUrl({ url: 'pages/Detail', params: { id } });   // deprecated since API 18
```

Minimum fix while still on the router framework:

```ts
this.getUIContext().getRouter().pushUrl({ url: 'pages/Detail', params: { id } });
```

Target state:

```ts
this.pathStack.pushPath({ name: 'detail', param: new DetailParam(id) });
```

Also note the router's own caveats while it remains: its APIs may only be called after page
rendering completes, and the stack information returned inside a `pushUrl` callback is an
intermediate state that can differ from the settled stack.

</details>

<!-- sources: openharmony-docs, openharmony-sdk-js, corey-harmonyos, oh-insight-migration, huawei-docs -->
