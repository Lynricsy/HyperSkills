# Skyline

Verified against: base library 3.x, devtools Stable 1.06.2307260+.

## Contents

- [What Skyline is](#what-skyline-is)
- [Turning it on](#turning-it-on)
- [rendererOptions](#rendereroptions)
- [Migration granularity](#migration-granularity)
- [The local-scrolling layout](#the-local-scrolling-layout)
- [Behaviour differences from WebView](#behaviour-differences-from-webview)
- [Text and ellipsis](#text-and-ellipsis)
- [Long lists under Skyline](#long-lists-under-skyline)
- [Animation with worklets](#animation-with-worklets)
- [Conditional code for both renderers](#conditional-code-for-both-renderers)
- [Preloading](#preloading)
- [Migration checklist](#migration-checklist)

## What Skyline is

A renderer that runs on its own thread and shares a rendering instance across pages,
instead of giving each page a WebView. It drops a set of web behaviours that were
WebView implementation details rather than mini program semantics, and adds gesture,
route and scroll capabilities that the WebView renderer cannot offer.

It is selected per page or per subpackage, so adoption is incremental; pages left on
WebView keep working. Skyline requires the glass-easel component framework. The reverse
does not hold — glass-easel runs on WebView too, from base library 3.8.12 — so
modernising the component framework and switching renderer are two separate decisions.

## Turning it on

```json
// app.json — all three keys, not just the first
{
  "renderer": "skyline",
  "componentFramework": "glass-easel",
  "lazyCodeLoading": "requiredComponents"
}
```

```json
// every Skyline page's .json
{
  "navigationStyle": "custom",
  "disableScroll": true
}
```

`navigationStyle: "custom"` is mandatory, not stylistic: Skyline has no native
navigation bar, and the compiler rejects a Skyline page without it
(`getAppConfig error: the "navigationStyle" configuration for the page should be set to
"custom"`). You supply your own bar, sized from the safe-area insets.

`disableScroll: true` goes with moving scrolling into `scroll-view`; leaving page-level
scroll enabled alongside a `scroll-view` produces conflicting gestures.

The devtools `setting.skylineRenderEnable` in `project.config.json` only affects the
simulator. It does not decide what a real client does.

## rendererOptions

```json
{
  "rendererOptions": {
    "skyline": {
      "defaultDisplayBlock": true,
      "defaultContentBox": true,
      "tagNameStyleIsolation": "legacy",
      "enableScrollViewAutoSize": true,
      "keyframeStyleIsolation": "legacy"
    }
  }
}
```

| Option | Without it |
|---|---|
| `defaultDisplayBlock` | Nodes default to `display: flex`, so every WebView layout shifts |
| `defaultContentBox` | Nodes default to `border-box`, so every sized element changes size |
| `tagNameStyleIsolation: "legacy"` | Tag selectors stop matching across component boundaries |
| `keyframeStyleIsolation: "legacy"` | Keyframes stop being visible across component boundaries |
| `enableScrollViewAutoSize` | `scroll-view` does not size itself from content |

The first two are the cause of "I turned on Skyline and the whole app's layout broke".
Set them when migrating an existing WebView app; a new Skyline-only app can leave them
off and use the Skyline defaults deliberately.

## Migration granularity

| Situation | Granularity |
|---|---|
| Large existing app | Page by page, starting with a high-traffic leaf page |
| New pages in an existing app | Page-level `renderer: "skyline"` |
| A whole new feature | Subpackage-level, in `subPackages[].renderer` |
| New app | App-level |

```json
{
  "subPackages": [
    { "root": "packageNew", "pages": ["pages/a/a"],
      "renderer": "skyline", "componentFramework": "glass-easel" }
  ]
}
```

## The local-scrolling layout

Skyline has no page-level scroll. The standard page shape is a fixed header plus a
`scroll-view` that takes the remaining space:

```html
<view class="page">
  <custom-navbar title="标题" />
  <scroll-view type="list" scroll-y class="content">
    <view wx:for="{{list}}" wx:key="id" list-item>{{item.title}}</view>
  </scroll-view>
</view>
```

```css
.page    { height: 100vh; display: flex; flex-direction: column; }
.content { flex: 1; height: 0; }   /* height:0 is required for flex:1 to take effect */
```

This layout also works correctly under WebView, so it is the right shape to adopt before
switching renderer — it makes the migration a configuration change rather than a
rewrite.

Horizontal scrolling needs more than `scroll-x`:

```html
<scroll-view type="list" scroll-x enable-flex style="display:flex; flex-direction:row;">
  <view wx:for="{{list}}" wx:key="id" style="flex-shrink: 0;">{{item}}</view>
</scroll-view>
```

## Behaviour differences from WebView

| WebView feature | Skyline | Replacement |
|---|---|---|
| Native navigation bar | Not supported | Custom navbar, `navigationStyle: "custom"` |
| Page-level scroll, `Page.onPageScroll` | Not supported | `scroll-view` and its scroll events |
| `display: inline` | Not supported | `<text>` nesting, `<span>`, or flex |
| `display: grid` | Not supported | `grid-view` |
| `position: sticky` | Not supported | `sticky-header` / `sticky-section` |
| `overflow: scroll` | Not supported | `scroll-view` |
| `z-index` stacking contexts | Only orders siblings | Restructure the tree |
| `this.animate()` | Not supported | Worklet animation |
| `web-view` | Not supported | Keep that page on WebView |
| Hot reload | Not supported | Recompile and preview |

Two positioning traps:

- Every Skyline node defaults to `position: relative`, so an `absolute` child resolves
  against a different ancestor than it did under WebView. Set the intended containing
  block explicitly.
- SVG does not honour `<style>` selectors; inline the attributes, and express `rgba`
  fills as `fill` plus `fill-opacity`.

Native components (`map`, `canvas`, `video`) may not render in the devtools simulator
under Skyline at all — verify them on a device.

## Text and ellipsis

`text-overflow: ellipsis` only applies to `<text>`, not to `<view>`. Multi-line
truncation is the `max-lines` attribute of `<text>`, not `-webkit-line-clamp`:

```html
<text style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">…</text>
<text max-lines="2" style="overflow: hidden;">…</text>
```

Bare text nodes should be wrapped in `<text>`; outside one, text styling is not
guaranteed.

## Long lists under Skyline

`<scroll-view type="list">` renders its **direct** children on demand. A wrapper node
between the `scroll-view` and the repeated rows turns that off:

```html
<!-- on-demand rendering works -->
<scroll-view type="list" scroll-y>
  <view wx:for="{{list}}" wx:key="id" list-item>{{item.name}}</view>
</scroll-view>

<!-- wrapper defeats it: the wrapper is the only direct child -->
<scroll-view type="list" scroll-y>
  <view class="list-wrapper"><view wx:for="{{list}}" wx:key="id">{{item.name}}</view></view>
</scroll-view>
```

The `list-item` marker enables style sharing across similar nodes, so styles are
computed once rather than per row.

A side effect: nodes outside the viewport do not exist, so a `selectAll` +
`boundingClientRect` over the whole list returns nothing for them. Query nodes
individually, when they are on screen.

## Animation with worklets

```javascript
const offset = wx.worklet.shared(0)

this.applyAnimatedStyle('.box', () => {
  'worklet'
  return { transform: `translateX(${offset.value}px)` }
})

offset.value = wx.worklet.timing(100, { duration: 300 })
```

The `'worklet'` directive is what moves the function onto the render thread; without it
the function runs in the logic layer and the animation goes back to crossing the thread
boundary every frame. `applyAnimatedStyle` needs base library 2.29.0+.

Gesture handling pairs with it: Skyline's gesture components negotiate between
competing gestures, which is what makes a draggable sheet inside a scroll view behave.

## Conditional code for both renderers

```javascript
Page({
  data: { isSkyline: false },
  onLoad() { this.setData({ isSkyline: this.renderer === 'skyline' }) },
})
```

```html
<view class="panel {{isSkyline ? 'sk' : ''}}">…</view>
```

```css
.panel     { position: fixed; }
.panel.sk  { position: absolute; }
```

Enhanced Skyline features degrade on their own: a custom route falls back to the default
animation, a shared element transition falls back to no animation. Do not branch on
those; branch only where the WebView behaviour would be wrong.

## Preloading

The client preloads the WebView environment, not Skyline. Before navigating to a Skyline
page, warm it up:

```javascript
onShow() { setTimeout(() => wx.preloadSkylineView(), 500) },
```

In `onShow` rather than `onLoad`, so returning to the page warms it again; delayed, so
it does not compete with the current page's own startup.

## Migration checklist

- [ ] `renderer`, `componentFramework` and `lazyCodeLoading` all present in `app.json`.
- [ ] `rendererOptions.skyline.defaultDisplayBlock` and `defaultContentBox` set when
      migrating existing WebView layout.
- [ ] Every Skyline page's JSON has `navigationStyle: "custom"`, and a custom navbar
      exists.
- [ ] Page-level scroll and `enablePullDownRefresh` replaced by `scroll-view`
      (`refresher-enabled` for pull-to-refresh).
- [ ] `onPageScroll` removed; scroll logic moved to the `scroll-view`.
- [ ] `this.animate()` calls converted to worklets.
- [ ] Any `web-view` page left on the WebView renderer.
- [ ] Text truncation moved onto `<text>` with `max-lines`.
- [ ] Verified on a device on both renderers, including the WebView fallback for older
      clients.

<!-- sources: wx-skyline-skills, wx-official-docs, wx-glass-easel -->
