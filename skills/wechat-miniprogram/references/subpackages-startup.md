# Subpackages and startup

Verified against: base library 3.x.

## Contents

- [The size caps](#the-size-caps)
- [Declaring subpackages](#declaring-subpackages)
- [Packing and reference rules](#packing-and-reference-rules)
- [Independent subpackages](#independent-subpackages)
- [Preloading](#preloading)
- [Async subpackage access](#async-subpackage-access)
- [The startup sequence](#the-startup-sequence)
- [lazyCodeLoading](#lazycodeloading)
- [Synchronous APIs on the startup path](#synchronous-apis-on-the-startup-path)
- [First-screen rendering](#first-screen-rendering)
- [Splitting an existing app](#splitting-an-existing-app)

## The size caps

| Scope | Cap |
|---|---|
| Main package | 2 MB |
| Each individual subpackage | 2 MB |
| Whole mini program, all packages together | 30 MB |
| Whole mini program, service-provider-developed | 20 MB |

The 2 MB figure is per package, never a total, and the total is 30 MB rather than the
20 MB that is often quoted — 20 MB applies only to mini programs developed by a service
provider on someone else's behalf. Getting this backwards turns a CI size gate into
either a false alarm on every build or a gate that never fires.

`ci.upload` returns the real numbers:

```javascript
const res = await ci.upload({ project, version, robot: 3 })
// res.subPackageInfo: [{ name: '__FULL__', size }, { name: '__APP__', size }, { name: 'packageGoods', size }, …]
```

`__FULL__` is the whole mini program; `__APP__` is the main package; any other name is
a subpackage.

## Declaring subpackages

```json
{
  "pages": ["pages/index/index", "pages/mine/mine"],
  "subPackages": [
    { "root": "packageGoods", "pages": ["pages/detail/detail"], "entry": "index.js" },
    { "root": "packageLive", "name": "live", "independent": true,
      "pages": ["pages/room/room"] }
  ]
}
```

| Field | Meaning |
|---|---|
| `root` | Subpackage root directory |
| `name` | Alias, usable in `preloadRule` |
| `pages` | Page paths relative to `root` |
| `independent` | Independent subpackage |
| `entry` | A JS file inside the subpackage executed first when the package is injected |

`subpackages` is accepted as a spelling of `subPackages`.

## Packing and reference rules

- Anything outside every declared `root` ends up in the main package. There is no
  "unpackaged" state — files you forgot are main-package weight.
- A `root` may not be inside another `root`. `packageGoods` plus `packageGoods/promo` is
  rejected at packaging time.
- **tabBar pages must be in the main package.** A tabBar entry pointing into a
  subpackage fails the build, and `wx.switchTab` to it cannot work.
- Subpackage A cannot `require` JS from subpackage B, `import` B's templates, or use B's
  assets. It can use the main package and its own contents. Async subpackage access
  lifts the JS restriction.
- The main package cannot reference a subpackage's assets either, which makes a global
  `usingComponents` entry pointing into a subpackage a build error.

## Independent subpackages

An independent subpackage starts with no main package at all — the point is a fast entry
for a self-contained flow (a live room, a lottery page, a shared card).

Everything ordinary subpackages cannot do, plus:

- it must not depend on the main package or any other subpackage — JS, templates, WXSS,
  custom components, plugins (async subpackage access lifts this for JS, components and
  plugins);
- `app.wxss` does not apply to it;
- `App` must not be defined in it;
- plugins are not supported in it.

And the timing changes:

```javascript
// inside an independent subpackage
const app = getApp({ allowDefault: true })   // 2.2.4+: placeholder when App is absent
app.pendingOrderId = orderId                 // merged into the real App once it registers
```

Without `allowDefault`, `getApp()` is `undefined` when the user entered through the
independent subpackage. `App.onLaunch` and the first `App.onShow` run only when the user
first reaches a main-package or ordinary-subpackage page. App-level events must come
from `wx.onAppShow` / `wx.onAppHide` / `wx.onError` / `wx.onPageNotFound`.

On clients older than WeChat 6.7.2 an independent subpackage degrades to an ordinary
one, and in that mode `app.wxss` may leak into it — so do not rely on its absence for
correctness of layout either way.

## Preloading

```json
{
  "preloadRule": {
    "pages/index/index": { "network": "all", "packages": ["packageGoods"] }
  }
}
```

Keyed by the page the user is on, listing packages to fetch in the background.
`network` is `all` or `wifi` (default `wifi`). `__APP__` names the main package, which
is how you preload it from an independent subpackage — usually the right move, because
it restores the main package before the user taps through.

Preloading an independent subpackage from the home page trades away the independence you
paid for; preload it only if entry through it is rare and entry from the home page is
common.

## Async subpackage access

`require` with a callback, or `wx.preloadSubpackage`, lets a page use JS, custom
components and plugins from a package it could not otherwise reach, downloading on
demand. The placeholder rendering while the package arrives comes from
`componentPlaceholder`. Use it to move a rarely used heavy dependency out of the main
package without reorganising pages.

## The startup sequence

```
1  environment preparation   (client-controlled; preloaded when the device allows)
2  mini program info         (sync request on first use / forced update, else async)
3  code package download     (sync on first use or version update, else async)
4  logic-layer injection     → App.onLaunch, App.onShow
5  view-layer injection      (parallel with 4)
6  first render              → Page.onLoad, Page.onShow, then Page.onReady
7  content appears           (your own network requests happen after this)
```

Steps 1–3 are not yours to optimise; 4–6 are. `Page.onReady` marks the end of startup
as far as the framework is concerned, which is why a page that shows a spinner until its
first `wx.request` returns scores well on startup and still feels slow. Use a skeleton
screen, and consider the initial render cache for the static shell.

## lazyCodeLoading

```json
{ "lazyCodeLoading": "requiredComponents" }
```

An **app.json** field (2.11.1+). Putting it under `project.config.json`'s `setting` is a
silent no-op — the key is accepted and ignored, and the feature stays off.

Without it, every page and every custom component in the packages used at startup is
injected and executed, including ones the user will never open. With it, only what the
first page needs is injected.

The catch: once it is on, **every** component declared in `app.json`'s
`usingComponents`, and every component declared in a page's JSON, counts as a dependency
of that page. Five globally declared components mean five components injected for every
page in the app. Declare components per page, and delete declarations for components the
page no longer uses.

"Injection on demand" (a further step on top) defers some component injection until the
component actually renders.

## Synchronous APIs on the startup path

Module scope, `App.onLaunch`, `App.onShow`, `Page.onLoad` and `Page.onShow` run in
series while the app starts. Anything synchronous there is added to the startup time.

- Most synchronous APIs end in `Sync`, but **`getSystemInfo` is synchronous despite the
  name**. Call it at most once during startup, cache the result, or use the split
  accessors — `getSystemSetting`, `getAppAuthorizeSetting`, `getDeviceInfo`,
  `getWindowInfo`, `getAppBaseInfo` — or `getSystemInfoAsync`.
- `getStorageSync`/`setStorageSync` are for persistence. Using storage as a state bus
  adds measurable time to injection; put shared state on `App.globalData` or in a module.
- Heavy computation at module scope (building an index, parsing a big constant) runs
  during injection. Compute it lazily on first use.
- `use asm` anywhere in your code disables V8 code caching, so every launch re-compiles.

## First-screen rendering

- Ship a skeleton, not a spinner.
- Reduce the number of custom components involved in the first screen; each one costs
  view-layer injection and initialisation.
- The initial render cache renders the static part of the first screen from a cache
  before the logic layer has produced data.
- Do not chain first-screen requests. One request that returns everything the first
  screen needs beats three dependent ones.

## Splitting an existing app

- [ ] Upload once and read `subPackageInfo` — split against measurements, not intuition.
- [ ] Move whole features. A page moved out while its components stay behind moves
      nothing.
- [ ] Keep tabBar pages and anything they import in the main package.
- [ ] Make a package independent only if it can start with no main package; then audit
      it for `getApp()`, `app.wxss` and shared components.
- [ ] Turn on `lazyCodeLoading` and prune `usingComponents`.
- [ ] Add `preloadRule` for the package the next tap needs.
- [ ] Re-upload and compare the numbers.

<!-- sources: wx-official-docs, wx-skyline-skills, miniprogram-ci -->
