# Lifecycle and routing

Verified against: base library 3.x, `miniprogram-api-typings` 5.2.3.

## Contents

- [The orderings that matter](#the-orderings-that-matter)
- [App lifecycle](#app-lifecycle)
- [Page lifecycle callbacks](#page-lifecycle-callbacks)
- [Component lifetimes and pageLifetimes](#component-lifetimes-and-pagelifetimes)
- [The page stack](#the-page-stack)
- [Route types and what each does to the stack](#route-types-and-what-each-does-to-the-stack)
- [switchTab, the awkward one](#switchtab-the-awkward-one)
- [Passing data between pages](#passing-data-between-pages)
- [Independent subpackages change App timing](#independent-subpackages-change-app-timing)
- [Saving and restoring state](#saving-and-restoring-state)
- [Common ordering bugs](#common-ordering-bugs)

## The orderings that matter

Creating a page:

```
component created   (bottom-up through the component tree)
component attached  (top-down)
component pageLifetimes.show   (top-down)
Page onLoad
Page onShow
```

Destroying a page:

```
component beforeDetach  (top-down)
component detached      (bottom-up)
Page onUnload
```

Hiding: `pageLifetimes.hide` (top-down) then `Page onHide`.
Re-showing: `pageLifetimes.show` (top-down) then `Page onShow`.

The consequence people trip over: **`attached` runs before the page's `onLoad`**. A
component that reads page state assigned in `onLoad`, or calls a page method that
`onLoad` installs, sees nothing. Pass the value in as a property, or have the component
wait for the property's observer.

The second consequence: `show`/`onShow` fire on every re-entry, not just the first, so
one-time initialisation belongs in `attached`/`onLoad`, and data refresh belongs in
`show`/`onShow`.

## App lifecycle

`App({ onLaunch, onShow, onHide, onError, onPageNotFound, onUnhandledRejection })`.
There is exactly one `App` instance, shared by every page, reachable with `getApp()`.

`onLaunch` and the first `onShow` run during main-package code injection, in series with
`Page.onLoad`/`onShow` of the entry page. Everything synchronous there is on the cold
start path.

Do not call `getCurrentPages()` in `onLaunch`: no page exists yet.

## Page lifecycle callbacks

| Callback | Fires |
|---|---|
| `onLoad(query)` | Once, with the launch query, all values `string \| undefined` |
| `onShow()` | Every time the page becomes visible |
| `onReady()` | Once, after the first render; UI APIs such as `wx.setNavigationBarTitle` belong after it |
| `onHide()` | Page hidden — `navigateTo` away, tab switch, app backgrounded |
| `onUnload()` | Page destroyed — `redirectTo`, `navigateBack` past it, `reLaunch` |
| `onRouteDone()` | The route animation finished |
| `onPullDownRefresh()` | Needs `enablePullDownRefresh`; end it with `wx.stopPullDownRefresh` |
| `onReachBottom()` | Fires once per approach inside `onReachBottomDistance` |
| `onPageScroll(e)` | See the warning below |
| `onShareAppMessage(opts)` | Defining it is what makes the share menu item appear |
| `onShareTimeline()` | 2.11.3+, Android only |
| `onTabItemTap(e)` | 1.9.0+ |
| `onResize(e)` | 2.4.0+ |
| `onAddToFavorites(e)` | 2.10.3+, Android only |
| `onSaveExitState()` | 2.7.4+ |

`onPageScroll` is not an ordinary callback. Its mere presence in the options object
makes the framework stream scroll events from the view layer to the logic layer at a
high rate. `onPageScroll () {}` costs what a real handler costs; the only way to switch
it off is to not declare the key. The same applies to `bindscroll` on `<scroll-view>`
and `<page-meta>`.

Page instance fields worth knowing: `this.route` (current path), `this.options` (launch
query), `this.renderer` (`'webview' | 'skyline'`), `this.router` / `this.pageRouter`,
`this.exitState`.

## Component lifetimes and pageLifetimes

```javascript
Component({
  lifetimes: {
    created() {},   // instance exists; setData is NOT allowed yet
    attached() {},  // in the node tree
    ready() {},     // laid out in the view layer
    moved() {},
    detached() {},  // removed; release timers and listeners here
    error(err) {},  // 2.4.1+, any component method that threw
  },
  pageLifetimes: {
    show() {}, hide() {}, resize(size) {}, routeDone() {},
  },
})
```

Declaring these at the top level of the options object still works but is the old form;
`lifetimes` wins when both are present (2.2.3+). `created` cannot call `setData` —
initialise fields there and set data in `attached`.

`pageLifetimes` is how a component learns its page was hidden. A component that starts a
timer in `attached` and stops it only in `detached` keeps running while the page is
merely hidden.

## The page stack

- At most **ten** pages.
- `getCurrentPages()` returns the stack, first element the bottom, last the current
  page. Never mutate it.
- Besides the stack there are **dangling pages**: created-but-inactive tabBar pages and
  pages in picture-in-picture mode (`video`, `live-player`). They are alive and their
  components still run.
- A tabBar page is always the bottom of the stack, because `navigateTo`/`redirectTo`
  cannot target one, and at most one instance of each tabBar page exists.
- Once a route is confirmed it cannot be cancelled. Routes issued while one is in flight
  queue up: calling `wx.redirectTo` from `onUnload` during a back navigation does not
  redirect the dying page, it redirects the page that ends up on top afterwards.

## Route types and what each does to the stack

| API | openType | Stack effect | Lifecycle triggered |
|---|---|---|---|
| cold start | `appLaunch` | Stack empty → target pushed | target: create |
| `wx.navigateTo` | `navigateTo` | Top hidden, target pushed | top: hide; target: create |
| `wx.redirectTo` | `redirectTo` | Top popped and destroyed, target pushed | top: destroy; target: create |
| `wx.navigateBack` | `navigateBack` | Pop `delta` pages | each popped: destroy |
| `wx.switchTab` | `switchTab` | See below | see below |
| `wx.reLaunch` | `reLaunch` | Everything destroyed, target pushed | all: destroy; target: create |

`navigateBack` fails outright when the stack holds one page, whatever `delta` says; with
a `delta` larger than the stack it pops down to one page rather than failing.

`reLaunch` is a route, not a restart. The AppService keeps running, code is not
re-injected, and module-level globals keep their values. Anything that must be reset has
to be reset explicitly.

## switchTab, the awkward one

`switchTab` first destroys everything above the bottom page, then moves the bottom page
out of the stack as a dangling page, then either shows a previously created tab page or
creates it:

| Current | Target | Lifecycles, in order |
|---|---|---|
| tabA | tabA | nothing |
| tabA | tabB (first time) | tabA hide; tabB create |
| tabA | tabB (again) | tabA hide; tabB show |
| C (opened from tabA) | tabA | C destroy; tabA show |
| C (opened from tabA) | tabB (first time) | C destroy; tabB create |

Because a tab page is created once and then only shown, its `onLoad` will not run again.
Refresh logic belongs in `onShow`.

## Passing data between pages

| Direction | Mechanism |
|---|---|
| Opener → opened | URL query (`onLoad(query)`, values are strings) |
| Opened → opener | `EventChannel` from `wx.navigateTo({ events })` / `this.getOpenerEventChannel()` |
| Anywhere → anywhere | `getApp().globalData`, or a plain module holding state |
| Across launches | `wx.setStorage` |

`getCurrentPages()[len - 2].setData(...)` reaches into another page's internals and
breaks as soon as the navigation path changes; the event channel expresses the same
thing without the coupling.

## Independent subpackages change App timing

When the user enters through an independent subpackage the main package is not
downloaded, so:

- `App` is not registered; `getApp()` returns `undefined`. Use
  `getApp({ allowDefault: true })` (2.2.4+) to get a placeholder whose properties are
  merged into the real `App` once the main package loads.
- `App.onLaunch` and the first `App.onShow` are deferred until the user reaches a main
  package or ordinary subpackage page.
- App-level events must come from `wx.onAppShow` / `wx.onAppHide` / `wx.onError` /
  `wx.onPageNotFound` instead of `App` callbacks.

## Saving and restoring state

`onSaveExitState()` (2.7.4+) returns `{ data, expireTimeStamp }`; the next launch
exposes it as `this.exitState`. Only JSON-compatible data survives, and the default
expiry is one day. Use it for "restore the form the user was filling in", not as a
cache.

## Common ordering bugs

| Symptom | Cause |
|---|---|
| Child component reads `undefined` page state | `attached` runs before `onLoad` |
| Data refreshes only the first time a tab is opened | Logic in `onLoad` instead of `onShow` |
| `wx.setNavigationBarTitle` has no effect | Called before `onReady` |
| Timer keeps firing after leaving the page | Cleared in `detached` only, not in `pageLifetimes.hide` |
| Redirect from `onUnload` lands on the wrong page | Route queued behind the in-flight one |
| Back button does nothing on the first page | `navigateBack` fails on a one-page stack |
| "Reset the app" leaves stale state | `reLaunch` does not re-inject code |
| Eleventh `navigateTo` fails | Page stack cap |

<!-- sources: wx-official-docs, wx-api-typings -->
