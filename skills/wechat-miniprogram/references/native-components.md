# Native components

Verified against: base library 3.x.

## Contents

- [Which components are native](#which-components-are-native)
- [Same-layer rendering: what changed](#same-layer-rendering-what-changed)
- [The limits that survived](#the-limits-that-survived)
- [Event binding is the big one](#event-binding-is-the-big-one)
- [bindrendererror and the fallback path](#bindrendererror-and-the-fallback-path)
- [cover-view and cover-image today](#cover-view-and-cover-image-today)
- [Overlays over a native component](#overlays-over-a-native-component)
- [The simulator lies](#the-simulator-lies)
- [canvas specifics](#canvas-specifics)
- [Review checklist](#review-checklist)

## Which components are native

These are created by the WeChat client rather than by the renderer:

- `camera`
- `canvas`
- `input` — **only while focused**
- `live-player`
- `live-pusher`
- `map`
- `textarea`
- `video`

`cover-view` and `cover-image` are also native components, with their own rules.

## Same-layer rendering: what changed

Historically a native component was painted above everything by the client, so no
`z-index` could beat it and overlays had to be built from `cover-view`. That era is
over: **all native components except `input` in its focused state now support
same-layer rendering**, and on HarmonyOS only same-layer rendering exists.

With same-layer rendering on, the following are no longer true:

- ~~native components are always on top regardless of `z-index`~~
- ~~a later native component covers an earlier one~~
- ~~`cover-view` is required to draw above `map`/`video`/`canvas`~~
- ~~native components cannot be used inside `scroll-view`, `swiper`, `movable-view`~~
  (that restriction applied below base library 2.4.4)

What the component draws internally is still native, so WXSS still does not reach
inside it — styling the inside of a `video` control bar is not a thing.

## The limits that survived

Same-layer rendering removed the layering limits. It did not remove these:

| Limit | Effect |
|---|---|
| Only the `bindeventname` form binds | `bind:eventname`, `catch…`, `capture-…` do nothing |
| No `catch` or `capture` binding at all | Cannot stop propagation at a native component |
| `position: fixed` unsupported | Element lands somewhere unintended |
| CSS animation unsupported | Animation silently does not play |
| Ancestor `overflow: hidden` does not clip it | It draws outside the rounded card you designed |
| Not usable inside `picker-view` | — |
| Occludes the vConsole panel | Debug output hidden behind the video |

## Event binding is the big one

```html
<!-- wrong: the colon form, catch, and capture all fail silently on a native component -->
<map bind:markertap="onMarkerTap" catchtap="onMapTap" />
<video bind:play="onPlay" catch:error="onVideoError" />
<canvas type="2d" bind:touchstart="onChartTouch" />

<!-- right -->
<map bindmarkertap="onMarkerTap" bindtap="onMapTap" />
<video bindplay="onPlay" binderror="onVideoError" bindrendererror="onRenderError" />
<canvas type="2d" bindtouchstart="onChartTouch" bindrendererror="onRenderError" />
```

Component reference pages show attributes as `bind:tap` because that is the generic
notation for ordinary components. For native components the restriction wins. The
failure mode is the worst kind: the build succeeds, the page renders, and the handler
is simply never called — which reads like a device or permission problem rather than a
syntax problem.

## bindrendererror and the fallback path

Same-layer rendering can fail at run time:

- on Android, when the device's webview kernel does not support it;
- on iOS, probabilistically, when the page's node tree is unstable while the component
  mounts.

Every native component should therefore carry `bindrendererror` and a degradation path:

```javascript
Page({
  data: { mapFallback: false },
  onMapRenderError(e) {
    // log e.detail, then fall back to something that does not need same-layer rendering
    this.setData({ mapFallback: true })
  },
})
```

A sensible fallback is a static image plus a "open in map" action, not a `cover-view`
rebuild of the overlay — `cover-view` does not fix a failed same-layer render, it adds
another native component to the same page.

## cover-view and cover-image today

They still exist and still work, and the component reference now recommends plain
`view` instead. Reasons to stop reaching for them:

- They are native components themselves, so the overlay inherits every limit in the
  table above instead of escaping it.
- They accept a small subset of WXSS: basic positioning, box model and text styling. No
  `background-image`, no per-side borders, no shadows — which is why overlays built
  from them end up with a `cover-image` as a background hack.
- Nesting rules are restrictive: only `cover-view` and `cover-image` inside a
  `cover-view`.

Keep them only for a code path that must still work on a client where same-layer
rendering is unavailable, and drive that path from `bindrendererror`.

## Overlays over a native component

The modern shape is ordinary components with ordinary stacking:

```html
<view class="screen">
  <map class="map" longitude="{{c.lng}}" latitude="{{c.lat}}" bindmarkertap="onMarkerTap"
       bindrendererror="onRenderError" />

  <view class="mask" wx:if="{{showCoupon}}" catchtouchmove="noop">
    <view class="coupon-card">
      <image class="coupon-bg" src="/img/coupon-bg.png" />
      <text class="coupon-title">{{coupon.title}}</text>
      <view class="btn primary" bindtap="onClaim">领取</view>
    </view>
  </view>
</view>
```

```css
.screen { position: relative; height: 100vh; }
.map    { position: absolute; inset: 0; }   /* not fixed: native components ignore fixed */
.mask   { position: absolute; inset: 0; z-index: 10; }
```

Note `catchtouchmove` on the mask — that is an ordinary `view`, so `catch` works there;
it is the `map` underneath that cannot take `catch`.

For a bottom dock that slides in, use a CSS transition on the `view`, not the
`animation="{{ … }}"` attribute: the animation-object API drives frames from the logic
layer across the thread boundary, and under Skyline it is replaced by worklets.

## The simulator lies

In the devtools simulator native components are drawn with web elements. Layering,
gesture handling, video playback, map interaction and same-layer failures are all
different there. Under Skyline, `map`/`canvas`/`video` may not render in the simulator
at all.

Any claim about native-component behaviour needs a real-device preview. If no device is
available, say so rather than reporting the simulator's behaviour as the answer.

## canvas specifics

Use `<canvas type="2d">` with `Canvas.getContext('2d')`; the old `canvas-id` + `wx.
createCanvasContext` form is the deprecated path, and the old `CanvasContext` drawing
API has been superseded by the standard `RenderingContext` since base library 2.9.0.

Retrieve the node through a selector query scoped to the component:

```javascript
this.createSelectorQuery()
  .select('#trendChart')
  .fields({ node: true, size: true })
  .exec((res) => {
    const canvas = res[0].node
    const ctx = canvas.getContext('2d')
    const dpr = wx.getWindowInfo().pixelRatio
    canvas.width = res[0].width * dpr
    canvas.height = res[0].height * dpr
    ctx.scale(dpr, dpr)
  })
```

Skipping the `pixelRatio` scaling is the standard cause of "the chart is blurry on
device but fine in the simulator".

## Review checklist

- [ ] Every native component uses `bindeventname`, with no colon, no `catch`, no
      `capture`.
- [ ] No native component is `position: fixed`, animated by CSS, or inside a clipping
      ancestor that is expected to clip it.
- [ ] Every native component has `bindrendererror` and a fallback that does not depend
      on same-layer rendering.
- [ ] Overlays use `view`/`image`/`text`, not `cover-view`/`cover-image`, unless they
      are the degraded path.
- [ ] `canvas` uses `type="2d"` and scales by `pixelRatio`.
- [ ] The layout has been checked on a real device, and the report says which device.

<!-- sources: wx-official-docs, wx-api-typings -->
