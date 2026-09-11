---
name: wechat-miniprogram
description: "Guides WeChat Mini Program work: the two-thread runtime, exparser vs glass-easel frameworks, WebView vs Skyline renderers, the data-update cost model (the calling component's Shadow tree before payload size), setData/updateData/groupUpdates, lifecycle ordering, routing and the page stack, native components under same-layer rendering, subpackages and package-size caps, lazyCodeLoading, storage quotas, wx.login and authorization scopes, privacy consent, uni-app conditional compilation, Taro builds, and miniprogram-ci upload. Use when reading or writing .wxml, .wxss, .wxs, app.json, project.config.json, pages.json or manifest.json, or when a mini program stutters, fails to build, or is rejected in review. Do not use for Vue 3 or Vite single-page apps (use the `vue` skill), browser and H5 pages or web rendering performance and visual design (use the `frontend-design` skill), TypeScript and tsconfig (use the `typescript` skill), or CloudBase cloud development (wx.cloud, cloud functions)."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# wechat-miniprogram

## Scope

Covers WeChat Mini Program applications: the two-thread runtime and the two swappable
layers inside it (component framework — exparser or glass-easel; renderer — WebView or
Skyline), data updates and their cost model, page and component lifecycles, routing and
the page stack, WXML/WXSS/WXS, custom components, native components and same-layer
rendering, subpackages and startup performance, storage quotas, login, authorization
scopes and the privacy-agreement flow, the `uni-app` and `Taro` cross-platform
toolchains as they compile to `mp-weixin`, `miniprogram-ci` uploads in CI,
`miniprogram-simulate` unit tests, and the version/review/release flow.

Base library **3.x** is the default baseline; every version-sensitive rule names the
base library or tool version it holds from. Mini games (`wx.createCanvas`, the
`minigame-*` packages) are a different runtime and are not covered.

Not covered: Vue 3 itself — components, Composition API, Pinia, Vue Router — use the
`vue` skill; only the mini program side of a uni-app project is here. Browser and H5
pages, general web rendering performance, CSS layout and visual design — use the
`frontend-design` skill. The TypeScript language, `tsconfig`, and type-level modelling —
use the `typescript` skill. Browser end-to-end testing — use the `web-testing` skill.
Also out of scope: CloudBase cloud development (`wx.cloud`, cloud functions, cloud
database, cloud storage), WeChat Pay and other merchant product APIs, Official Account
and Work WeChat development, and the WeChat AI-mode `wx.modelContext` skill packaging.

Paths below are relative to this skill's directory.

## Read first

`references/data-updates.md` before diagnosing any performance complaint. The cost model
documented by the platform is the opposite of the common assumption: the dominant factor
is the node count of the Shadow tree belonging to the component that calls the update,
not the number of bytes in the payload. Advice derived from "setData serialises across
the bridge, so send less" optimises the second-order term and leaves the first one alone.

## Core rules

1. A data update's cost is driven first by the Shadow-tree node count of the component
   that calls it, and only then by how much data changed. Splitting a page into
   per-row components that update themselves beats any amount of payload diffing on a
   page whose tree stays whole. `[official]`
2. The cheap binding-map update is selected only when exactly one data field is updated
   **and** that field is not used by a `wx:if` / `wx:for` / `let:` node or any of their
   descendants (glass-easel). Everything else takes a depth-first walk of the whole
   Shadow tree — so merging five fields into one `setData` forfeits the fast path, and a
   list bound with `wx:for` never qualifies. `[official]`
3. One `setData` call carries at most 1024 kB, accepts only JSON-serialisable values, and
   silently skips any key whose value is `undefined` — the stale value survives and no
   error is raised. `[verified]`
4. `data` holds only what WXML reads. Render-irrelevant state goes on the instance
   (`this.userData = …`); render-indirect state goes in pure data fields
   (`options.pureDataPattern`, base library 2.8.2+) and is watched with `observers`.
   A field in `data` that no binding reads still pays for a render pass. `[official]`
5. Non-function fields passed in the `Page`/`Component` constructor object are deep-copied
   once per instance. A large object declared there is copied at page creation; assign it
   to `this` inside `onLoad`/`created` instead. `[official]`
6. Declaring `onPageScroll` at all makes the view layer stream scroll events to the logic
   layer at high frequency; an empty `onPageScroll () {}` costs the same as a real one.
   Omit the key, and use `IntersectionObserver` rather than polling `SelectorQuery` from a
   scroll callback. `[official]`
7. Component `attached` runs before page `onLoad`. The creation order is
   `created` (bottom-up) → `attached` (top-down) → `pageLifetimes.show` (top-down) →
   `onLoad` → `onShow`; destruction is `beforeDetach` → `detached` → `onUnload`. A child
   that reads page state written in `onLoad` reads it before it exists. `[official]`
8. The page stack holds at most ten pages. `navigateTo`/`redirectTo` cannot target a
   tabBar page, a tabBar page is therefore always the stack bottom and exists at most
   once, and `navigateBack` on a single-page stack fails regardless of `delta`. `[official]`
9. `reLaunch` is a route, not a restart: the AppService keeps running, code is not
   re-injected, and JS globals are not reset. Using it to "reset the app" leaves stale
   module state behind. `[official]`
10. Same-layer rendering now covers every native component except `input` in its focused
    state, so `z-index` works and `cover-view`/`cover-image` are no longer the way to draw
    above `map`, `video` or `canvas` — wrapping an overlay in `cover-view` adds a second
    native component instead of removing a constraint. `[official]`
11. Native components accept only the `bindeventname` form. `bind:eventname`, `catch…`
    and `capture-…` do not bind at all on a native component, which looks like a handler
    that never fires rather than a syntax error. `[official]`
12. A native component cannot be `position: fixed`, cannot take a CSS animation, and
    cannot be clipped by an ancestor's `overflow: hidden`. Same-layer rendering can also
    fail at runtime — a missing kernel on Android, an unstable node tree on iOS — so give
    each one `bindrendererror` and a fallback. `[official]`
13. The devtools simulator draws native components with web elements, so layering,
    gestures and playback there prove nothing. Verify native-component layout on a real
    device before believing it. `[official]`
14. Package caps: the main package and each individual subpackage are limited to 2 MB, and
    the whole mini program to 30 MB (20 MB when developed by a service provider). tabBar
    pages must live in the main package, and a `subPackages` root may not sit inside
    another one. `[official]`
15. An independent subpackage may not define `App`, may not depend on the main package or
    other subpackages, and does not receive `app.wxss`. When the user enters through it,
    `getApp()` is `undefined` unless called as `getApp({ allowDefault: true })`, and
    `App.onLaunch` plus the first `onShow` are deferred until the user reaches the main
    package. `[official]`
16. `lazyCodeLoading: "requiredComponents"` is an **app.json** field, not a
    `project.config.json` `setting` key; in the wrong place it is silently ignored. Once
    it is on, every component declared in app.json `usingComponents` counts as a
    dependency of every page, so global declarations must be rare. `[official]`
17. `getSystemInfo` is synchronous despite the name, and `use asm` disables V8 code
    caching. Keep synchronous APIs and heavy computation out of module scope,
    `App.onLaunch`, `App.onShow`, `Page.onLoad` and `Page.onShow` — they run in series on
    the startup path. `[official]`
18. Storage allows 1 MB per key and 10 MB in total, and is for persistence only.
    `getStorageSync`/`setStorageSync` used for state passing or a global store add
    measurable time to code injection at startup. `[verified]`
19. The `wx.login` code is single-use and valid for five minutes; it is exchanged for
    `openid`/`unionid`/`session_key` on your server. `session_key` must never be returned
    to the mini program or to any third party. `[official]`
20. Once a user has refused a scope, the dialog never appears again — the API goes
    straight to `fail`. Recover through `wx.getSetting` plus `wx.openSetting`, never by
    calling `wx.authorize` in a loop. Location scopes additionally require
    `requiredPrivateInfos` and a purpose description in app.json. `[official]`
21. An interface not declared in the platform's privacy guideline is disabled outright,
    not merely un-prompted. From base library 2.32.3 the flow is `wx.getPrivacySetting`
    or `wx.onNeedPrivacyAuthorization`, then a
    `<button open-type="agreePrivacyAuthorization">`; `<input type="nickname">` silently
    degrades to `type="text"` while consent is missing. `[official]`
22. Skyline requires the glass-easel component framework and `navigationStyle: "custom"`
    on every Skyline page, and has no page-level scrolling — scrolling moves into
    `scroll-view`. glass-easel by itself is not Skyline-only: it supports the WebView
    renderer from base library 3.8.12. `[official]`
23. `wx:key` is not unconditionally right. Specify it when items are reordered, inserted
    or removed in the middle, and whenever items contain stateful components; omit it on
    append-only lists, where the framework can use a faster comparison sub-algorithm.
    Duplicate keys are suffixed (`a--0`, `a--1`) at extra cost, and an index key does
    nothing when items move. `[official]`
24. In uni-app, an unrecognised `%PLATFORM%` — a typo, or a platform an older HBuilderX
    does not know — makes `#ifdef` drop the block and `#ifndef` keep it. The build
    succeeds and ships the wrong branch. `[official]`
25. `miniprogram-ci`: `robot` is 1–30, `type` is one of
    `miniProgram`/`miniProgramPlugin`/`miniGame`/`miniGamePlugin`, `privateKey` takes key
    **contents** while `privateKeyPath` takes a path, and there is no submit-for-review
    call — review submission happens on the mini program platform. `[verified]`

## Workflows

### implement

- [ ] Read `app.json` and `project.config.json` first: `renderer`, `componentFramework`,
      `lazyCodeLoading`, `subPackages`, `preloadRule`, `libVersion`. Rules 14–16 and 22
      all depend on these values.
- [ ] Decide the component boundary before writing the template. A repeated row, a
      frequently updating widget and a countdown are each their own component, because
      that is what bounds the Shadow tree an update walks (rule 1).
- [ ] Put only render data in `data`; everything else on `this` or in a pure data field
      (rule 4). Declare `observers` for derived fields rather than recomputing in the
      page.
- [ ] Bind events with `bind`/`catch` on ordinary components and with `bindeventname`
      only on native ones (rule 11); give every native component `bindrendererror`.
- [ ] Register components per page, not in app.json, unless the component really is on
      every page (rule 16).
- [ ] **Gate:** `npx tsc --noEmit` over the project's `.ts`/`.js` with
      `miniprogram-api-typings` in scope reports no unknown `wx.*` member, and every new
      API used carries its minimum base library version in a comment.

### review

- [ ] Establish the base library and renderer from `app.json`/`project.config.json`
      before judging anything version-gated.
- [ ] Walk the Core rules in order; they are ordered by how often each is the real defect.
- [ ] For every `setData` call site ask three questions: which component owns the tree
      being walked, how many fields the call touches, and whether any of them feeds a
      `wx:if`/`wx:for` (rules 1–2).
- [ ] Check `data` for fields no binding reads, `Page({…})` for large constructor-time
      objects, and the page options for a stray `onPageScroll` (rules 4–6).
- [ ] Check every native component for the colon event form, `position: fixed`, CSS
      animation and a clipping ancestor (rules 11–12).
- [ ] Check timers, `wx.onXxx` listeners and `IntersectionObserver` instances for a
      matching teardown in `onUnload`/`detached`.
- [ ] Report only findings with a reachable trigger and a concrete impact. A text match is
      a lead, never a finding.
- [ ] **Gate:** every finding carries `path:line`, the trigger, the impact and a fix, and
      every platform claim names the base library version it holds from.

### diagnose-stutter

- [ ] Reproduce with the interaction named by the reporter, and separate "the page is slow
      to update" from "the whole app stops responding". The second is the logic thread
      being saturated — scroll callbacks, a timer, or a background page still updating.
- [ ] Instrument before rewriting: `this.setUpdatePerformanceListener(...)` on the
      suspect component reports per-update statistics, which attributes cost to a
      component instead of to a guess.
- [ ] Apply the ranking from rule 1: split the tree first, then remove render-irrelevant
      data, then reduce what each update sends.
- [ ] Replace scroll-driven measurement with `IntersectionObserver`, and
      `setData`-driven animation with CSS animation, WXS event handlers, or Skyline
      worklets (see `references/render-performance.md`).
- [ ] Stop background-page updates in `onHide` and recompute from a timestamp in `onShow`
      rather than keeping a timer alive.
- [ ] **Gate:** the changed component reports a lower update cost through
      `setUpdatePerformanceListener` than before, measured on the same interaction — not
      "this should be faster now".

### configure-subpackages

- [ ] Measure first: `ci.upload` returns `subPackageInfo`, where `__APP__` is the main
      package and `__FULL__` is the whole mini program. Compare against rule 14's caps
      before moving files.
- [ ] Move whole features, not files: a subpackage cannot reach into another subpackage,
      and pulling one page out while leaving its components in the main package moves
      nothing.
- [ ] Make a subpackage independent only when it can start with no main package at all,
      and then audit it for `getApp()`, `app.wxss` and shared components (rule 15).
- [ ] Turn on `lazyCodeLoading`, then delete unused `usingComponents` declarations —
      leaving them on cancels most of the benefit (rule 16).
- [ ] Add `preloadRule` for the package the next tap will need, keyed by the page the user
      is on.
- [ ] **Gate:** a fresh `ci.upload` shows `__APP__` and every subpackage under 2 MB and
      `__FULL__` under the total cap, with the numbers quoted from the upload result.

### ship

- [ ] Build npm first when the project has dependencies: `ci.packNpm` produces the
      `miniprogram_npm` directory that actually ships.
- [ ] Upload with an explicit robot number reserved for this pipeline, a version derived
      from the tag or commit, and a `desc` that identifies the build (rule 25).
- [ ] Keep the upload key out of the repository, write it to a temporary file with
      restricted permissions, and delete it in a `finally`. Decide explicitly whether the
      IP allowlist is on — a hosted CI runner has no stable egress IP.
- [ ] Submit for review from the platform, not from CI, and remember only one version can
      be in review at a time.
- [ ] Release in stages for anything user-facing; full release only for small mini
      programs.
- [ ] **Gate:** `node ci/upload.js` exits zero and prints the returned
      `subPackageInfo`/`pluginInfo`, and the version number appearing in the platform's
      version list matches the commit that produced it.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Runtime architecture | Choosing or identifying the component framework and renderer; WXS behaviour; why a thing behaves differently on device | `references/runtime-architecture.md` |
| Data updates | Any `setData`, `updateData`, observer, pure data field, or performance complaint | `references/data-updates.md` |
| Lifecycle and routing | Ordering bugs, page stack, tabBar, `getCurrentPages`, exit state | `references/lifecycle-routing.md` |
| Native components | `map`/`video`/`canvas`/`camera`/`live-*`/`textarea`/`input`, overlays, `cover-view`, layering | `references/native-components.md` |
| Render performance | Long lists, `wx:key`, slots, `virtualHost`, animation choice, node budgets | `references/render-performance.md` |
| Subpackages and startup | Package size, independent subpackages, preload, `lazyCodeLoading`, cold-start cost | `references/subpackages-startup.md` |
| Storage, login and privacy | `wx.login`, `code2Session`, scopes, `openSetting`, privacy guideline APIs, storage quotas | `references/storage-login-privacy.md` |
| Skyline | Turning Skyline on, WebView-to-Skyline differences, local scrolling, worklets | `references/skyline.md` |
| uni-app and Taro | A cross-platform project targeting `mp-weixin`; conditional compilation; escape hatches | `references/cross-platform.md` |
| CI, testing and release | `miniprogram-ci`, `miniprogram-simulate`, version flow, review and rejection causes | `references/ci-testing-release.md` |

## Output format

For `review` and any other report on existing code, group findings by file, ordered by
severity, with no preamble:

```
pages/feed/feed.js
  L28 blocking - onPageScroll is declared, so every scroll frame crosses to the logic
       layer, and the callback then runs selectAll().boundingClientRect() over ~600
       nodes. This is why taps stop responding, not the list size.
       before: onPageScroll(e) { this.setData({ scrollTop: e.scrollTop }); … }
       after:  remove onPageScroll; drive exposure from wx.createIntersectionObserver
  L54 important - cursor: res.cursor === null ? undefined : res.cursor. setData skips
       undefined values, so the stale cursor survives with no error.
  L8  important - categoryTree (~400 KB) sits in data and is echoed back on every page
       load, although no binding reads it. Move it to this.categoryTree in onLoad.

app.json
  L17 blocking - subPackages root "packageGoods/promo" nests inside "packageGoods";
       packaging rejects this.
  ✓ preloadRule is keyed on the page the user is on, which is the intended shape.
```

Severities: `blocking` (does not build, breaks at runtime, loses data, exceeds a package
cap, or fails review), `important` (stutter, leaked listener or timer, silently dropped
update, unhandled authorization refusal), `minor` (naming, dead config, ordering). End
with a one-line verdict: ship, ship after blocking fixes, or rework. Name the base
library version every platform claim holds from, and list unrun checks separately from
findings.

## Environment

The WeChat Developer Tools are Windows/macOS only, so compilation, the simulator and
real-device preview cannot be reproduced on Linux. What does run headlessly:

```bash
npm i -D miniprogram-api-typings     # official wx.* / Page / Component declarations
npm i -D miniprogram-simulate        # custom-component unit tests under jest
npm i -D miniprogram-ci              # upload / preview / packNpm, no IDE required
npm i -D glass-easel                 # component-framework runtime, for API checks
npx tsc --noEmit                     # type-check against the official declarations
npx jest test/components             # miniprogram-simulate load/render/attach
node ci/upload.js                    # ci.packNpm + ci.upload with a robot number
```

`miniprogram-simulate` runs components in a single Node thread with a jsdom tree: `wx.*`
and the built-in components are stubs, and features such as abstract nodes are not
emulated, so it proves component logic and rendered output, never runtime behaviour.
Anything involving native components, gestures, real network domains or the two-thread
scheduler needs a real device. When a device is unavailable, report that boundary rather
than describing an unrun check as passed.
