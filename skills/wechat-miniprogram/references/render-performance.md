# Render performance

Verified against: base library 3.x, `glass-easel` 1.2.0.

## Contents

- [Node budgets](#node-budgets)
- [wx:key is conditional, not mandatory](#wxkey-is-conditional-not-mandatory)
- [List mutation patterns](#list-mutation-patterns)
- [Long lists](#long-lists)
- [Scroll events are a standing cost](#scroll-events-are-a-standing-cost)
- [Exposure tracking with IntersectionObserver](#exposure-tracking-with-intersectionobserver)
- [Choosing an animation mechanism](#choosing-an-animation-mechanism)
- [Slot modes](#slot-modes)
- [virtualHost](#virtualhost)
- [Images](#images)
- [Background pages and memory](#background-pages-and-memory)
- [Diagnosing, in order](#diagnosing-in-order)

## Node budgets

The platform's stated ceilings for one page:

- fewer than **1000** WXML nodes,
- tree depth under **30**,
- no more than **60** children on one node.

These are not stylistic. Node count drives memory, layout time, and — because the
default update algorithm is a depth-first walk — the cost of every data update on that
page. A page that renders 600 rows of a dozen nodes each is six to ten times over the
budget, which is what turns "the list got longer" into "the page became unusable".

The way back under budget is component boundaries, not fewer features: a row component
holds its own small Shadow tree and updates itself.

## wx:key is conditional, not mandatory

The universal "always add `wx:key`" advice is wrong in one direction and right in three.

Specify `wx:key` when:

- items are reordered, or inserted/removed anywhere but the end;
- items contain stateful child components — without a key, state gets attached to the
  wrong item.

Omit it when:

- the list only ever appends or truncates at the end, where the framework can use a
  faster comparison sub-algorithm;
- items are purely presentational and hold no components.

Also true:

- keys are compared as strings, and must be unique within the list; duplicates are
  disambiguated with suffixes (`a--0`, `a--1`) plus a warning and extra work;
- a key must be stable for the item's lifetime — an index key is no key at all once
  items move;
- `wx:key="*this"` means "the item itself is the key", which is only valid for a list of
  unique primitives.

A separate, very common bug: keying by `id` while handlers carry `data-index`. After a
sort or filter the index no longer identifies the row the user tapped. Carry `data-id`
and look the item up.

## List mutation patterns

Under glass-easel, express list changes as splices rather than array rebuilds:

| Pattern | Call | Key needed? |
|---|---|---|
| Infinite scroll (append) | `spliceArrayDataOnPath(['list'], undefined, 0, newItems)` | No — append-only is the fast path |
| Rolling window (drop head, add tail) | two splices inside `groupUpdates` | Yes |
| Pin / drag reorder (move one) | remove at `from`, insert at adjusted `to`, inside `groupUpdates` | Yes |
| Replace a contiguous range | one splice with `del` and `inserts` | Yes |

Under exparser the equivalent is path-addressed `setData`:

```javascript
this.setData({ [`list[${i}].liked`]: true, [`list[${i}].likeCount`]: n })
```

Both beat `this.setData({ list })` by a wide margin, because rebuilding the array makes
the framework re-diff every row.

## Long lists

Ordered by how much they buy:

1. **Row components.** Each row owns a small tree; a like-button tap updates one row's
   tree instead of the page's.
2. **Do not keep everything rendered.** Under Skyline, `<scroll-view type="list">`
   renders its *direct* children on demand — a wrapper `<view>` between the
   `scroll-view` and the rows defeats it. Adding `list-item` to the repeated child
   enables style sharing so styles are computed once.
3. **Cap what you hold.** A rolling window of a few hundred items plus a "load more"
   affordance beats a 5000-item array in `data`, which costs memory on both threads.
4. **Keep `data` clean.** A field no binding reads still participates in updates.

## Scroll events are a standing cost

Declaring `onPageScroll` in the `Page` options turns on a high-frequency view→logic
event stream for the whole page. An empty function does not disable it:

```javascript
Page({ onPageScroll () {} })   // wrong: still streaming
Page({ /* no onPageScroll */ }) // right
```

The same applies to `bindscroll` on `<scroll-view>` and `<page-meta>`. If scroll
position is only needed for restore-on-return, the framework already restores it.

Inside a scroll handler, never run a `SelectorQuery` over many nodes and never call an
update API. Both cross the thread boundary at frame rate and saturate the single logic
thread, which is why the whole app — not just the list — stops responding to taps.

## Exposure tracking with IntersectionObserver

```javascript
Component({
  attached() {
    this._io = this.createIntersectionObserver({ observeAll: true })
      .relativeToViewport({ bottom: 0 })
      .observe('.feed-card', (res) => {
        if (res.intersectionRatio > 0) report(res.dataset.id)
      })
  },
  detached() { this._io && this._io.disconnect() },
})
```

The observer runs on the view side and calls back only on boundary crossings, so a
1000-row list costs nothing while the user is not scrolling. `observeAll: true` is
needed to watch every match rather than the first. Disconnect in `detached` — an
observer outliving its component is a leak with no error message.

## Choosing an animation mechanism

| Mechanism | Where frames are computed | Use for |
|---|---|---|
| CSS transition / animation | View layer | Almost everything |
| WXS event handlers | View layer | Gesture-driven animation that must follow the finger |
| Scroll-driven animation (`scroll-view`) | View layer | Parallax, sticky headers |
| Skyline worklets (`wx.worklet`, `applyAnimatedStyle`) | Render thread | Complex animation under Skyline |
| `this.animate()` keyframes (2.9.0+) | Framework | Declarative keyframes on WebView |
| `wx.createAnimation` + `animation="{{ … }}"` | Logic layer | Legacy; each step crosses the bridge |
| `setData` in a timer | Logic layer | Never |

Driving frames from the logic layer means every frame pays a thread crossing, and it
competes with taps for the same single thread. Under Skyline, `this.animate()` is not
available at all and worklets are the replacement.

## Slot modes

| Mode | Option | Cost | Slot content creation |
|---|---|---|---|
| Single slot | default | lowest | Always created, even without a `<slot/>` tag |
| Multiple slots | `multipleSlots: true` | medium | Always created, even with no matching named slot |
| Dynamic slots | `dynamicSlots: true` | highest per slot | Created and destroyed with the `<slot/>` tag |

Turning on `multipleSlots` for a component that does not need named slots disables the
single-slot optimisation for nothing. Note that in the first two modes slot content is
created whether or not the component renders a `<slot/>`: passing an expensive subtree
into a component that conditionally shows it still mounts that subtree, and its
components still get `attached`. That is the case for `dynamicSlots`.

## virtualHost

`options: { virtualHost: true }` makes the component produce no host node, so its
children participate directly in the parent's flex or grid layout and the tree loses a
level. Costs:

- `class` and `style` on the component tag stop working; re-expose them as an external
  class and a `style` property applied to an inner node;
- `getBackendElement()` / `$$` return `null`;
- multiple root children are exposed directly to the parent container, which sometimes
  forces a wrapper back in.

Worth it for layout wrappers and list rows; not worth it for leaf widgets.

## Images

- Give every `<image>` explicit dimensions. Without them each decoded image triggers a
  reflow as it arrives.
- Use `lazy-load` for images inside a long list.
- `mode="aspectFill"` plus a server-side resize beats shipping a 2000px asset to a 200px
  slot; image decoding is a real cost on low-end Android.
- Local images in the main package count against the 2 MB cap; move decorative assets to
  a CDN or a subpackage.

## Background pages and memory

The logic layer is single-threaded and shared. A hidden page that keeps a `setInterval`
running steals time from the visible page and renders something nobody sees. On some
platforms the view-layer WebViews share a thread too, so a background render can stall
the foreground one.

```javascript
onHide() { clearInterval(this._t); this._t = null; this._hiddenAt = Date.now() },
onShow() { this.syncFromTimestamp(); this.startTicker() },
```

Recompute a countdown from a target timestamp in `onShow` rather than keeping a ticker
alive to stay accurate.

Also release in `onUnload`/`detached`: `wx.onXxx` listeners, `IntersectionObserver`s,
`MediaQueryObserver`s, `InnerAudioContext`s, `MapContext` callbacks, and any
`createSelectorQuery` loop.

## Diagnosing, in order

1. Which symptom: slow update, or the whole app unresponsive? The second means the logic
   thread is saturated — look for scroll handlers, timers and background pages first.
2. Attach `setUpdatePerformanceListener` to the suspect component and reproduce.
3. Count nodes for the page against the 1000/30/60 budget.
4. Only then look at payload size.

<!-- sources: wx-official-docs, wx-glass-easel, wx-skyline-skills, wx-api-typings -->
