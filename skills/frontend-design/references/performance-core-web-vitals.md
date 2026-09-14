# Core Web Vitals and asset cost

Verified against: web.dev Core Web Vitals definitions.

Performance is a design constraint, not a separate discipline. A hero that shifts, a font that swaps
late and a list that janks are visual defects with numeric names.

## Contents

- [Targets](#targets)
- [Measure before changing anything](#measure-before-changing-anything)
- [Where to start, by symptom](#where-to-start-by-symptom)
- [Layout shift](#layout-shift)
- [Largest contentful paint](#largest-contentful-paint)
- [Interaction latency](#interaction-latency)
- [Images and media](#images-and-media)
- [Long lists](#long-lists)
- [Verify, then guard](#verify-then-guard)
- [Checkable rules](#checkable-rules)

## Targets

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint), loading | 2.5s or less | 4.0s or less | over 4.0s |
| INP (Interaction to Next Paint), interactivity | 200ms or less | 500ms or less | over 500ms |
| CLS (Cumulative Layout Shift), visual stability | 0.1 or less | 0.25 or less | over 0.25 |

Judge at the **75th percentile of page loads, segmented across mobile and desktop**. A page passes
only when all three metrics meet their target at that percentile. A median on a developer laptop
proves nothing.

## Measure before changing anything

Type the evidence before acting on it. Four kinds, and they are not interchangeable:

- **Synthetic** (Lighthouse, the browser's performance panel): controlled and reproducible. Good for
  isolating a specific issue and for regression detection in CI.
- **Single-session observation**: a `PerformanceObserver` reading taken from one page in one
  browser. It is a lab measurement with a sample size of one, whichever API produced it.
- **Field (RUM)**: values from real sessions, reported to a collector and aggregated.
- **CrUX**: field data already aggregated for the origin or the URL.

```js
import { onLCP, onINP, onCLS } from 'web-vitals';
onLCP(report); onINP(report); onCLS(report);
```

That snippet is field data only where `report` ships the value to a collector and the values are
aggregated across real sessions. Run once in your own browser it is a single-session lab reading,
and treating it as field evidence is the most common way a performance claim goes wrong.

Cite metric values, never a Lighthouse category score. The score is a weighted summary whose
weights and audit set change between versions: an accessibility score of 100 is not WCAG
conformance, and a performance score of 100 is not a passing field metric.

Prefer page-level CrUX for the audited URL. Origin-level CrUX is context for a route, never proof
about it, and **missing CrUX data means unavailable, never passing**: localhost, staging, new and
low-traffic pages routinely have no record.

When lab and field disagree, the reading is fixed rather than a matter of preference.

| Lab | Field | Reading |
|---|---|---|
| Poor | Good | The local run missed the real device, route and cache distribution. Segment the field data before optimizing the synthetic case. |
| Good | Poor | Users are failing on conditions the synthetic run did not reproduce. Find the failing segment; a passing lab run is not a defence. |
| Poor | Poor | Diagnose in the lab, confirm in the field. |
| Any | Unavailable | Diagnose in the lab and say so. Recommend field collection before claiming production impact either way. |

Without a runnable page, static inspection produces hypotheses, not measurements. Label each one a
hypothesis and name the measurement that would confirm it. Stating that LCP, INP or CLS is failing
from source alone is fabrication, not review.

The loop is fixed: measure, identify the actual bottleneck, fix that one thing, measure again, keep
or revert, then add a guard. Skipping to the fix is how a codebase acquires three optimizations that
each cost complexity and none of which moved a metric.

## Where to start, by symptom

```text
What is slow?
├── First load
│   ├── Large bundle            -> measure bundle size, check route-level splitting
│   ├── Slow server response    -> read TTFB in the network waterfall
│   │   ├── DNS or connection   -> preconnect to known third-party origins
│   │   └── Server wait         -> not a frontend problem; profile the backend
│   └── Render-blocking assets  -> find blocking CSS and synchronous scripts
├── Interaction feels sluggish
│   ├── Freeze on click         -> profile the main thread, look for tasks over 50ms
│   ├── Input lag while typing  -> controlled input doing work per keystroke
│   └── Animation jank          -> layout thrashing, or animating a layout property
├── Content jumps while loading -> unsized media, late fonts, injected banners
└── Slow after navigation
    ├── Data waterfall          -> requests that could have started in parallel
    └── Client render cost      -> too much rendered at once; defer offscreen work
```

## Layout shift

The three causes, in order of how often they occur:

1. **Media without intrinsic size.** Every `<img>`, `<video>`, `<iframe>` and embed carries `width`
   and `height` attributes, or an `aspect-ratio` in CSS. This single rule removes most CLS.
2. **Late fonts.** Use `font-display: swap` and reserve the space, so the swap changes glyphs but not
   line count. A fallback face with mismatched metrics reflows the whole page on arrival. Where the
   swap itself is the shift, match the fallback to the real face with `size-adjust`,
   `ascent-override`, `descent-override` and `line-gap-override`, deriving the percentages from the
   actual font pair: values copied from an example describe a different pair and reintroduce the
   shift. These descriptors are not Baseline Widely available; where unsupported they are ignored,
   which degrades to the unmatched-metrics behaviour rather than breaking, so they need no separate
   fallback.
3. **Async content injected into flow.** Reserve space for anything that arrives late: ad slots,
   consent banners, skeletons, "N new items" bars. A skeleton that is not the same size as the
   content it replaces causes the shift it was supposed to prevent.

Also: never animate a layout property. Anything that moves uses `transform`.

## Largest contentful paint

- Identify the LCP element first. It is usually the hero image or the headline, and optimizing
  anything else is wasted work.
- The critical image gets `fetchpriority="high"` and is **not** lazy-loaded. Everything below the
  fold gets `loading="lazy"`.
- Preload only the fonts used above the fold, and `preconnect` to the font or asset origin.
  Preloading everything competes with the LCP resource for bandwidth.
- Keep render-blocking CSS small; inline what the first viewport needs when the tooling supports it.
- Defer or `async` third-party scripts, and audit them periodically. A tag manager is frequently the
  largest single cost on a page nobody has measured.

## Interaction latency

- Aim for visible feedback within about 100ms of a press. That is a perception threshold, separate
  from the INP target.
- Keep per-frame work under about 16ms for 60fps. Break long tasks into chunks and yield.
- Never read layout during render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`,
  `scrollTop`). Batch reads, then batch writes; interleaving them forces a synchronous reflow per
  pair.
- Prefer uncontrolled inputs. A controlled input must be cheap per keystroke; anything expensive is
  debounced or moved off the keystroke path.
- Debounce or throttle high-frequency events (scroll, resize, pointermove, input).

## Images and media

- Modern formats (AVIF, WebP) with `srcset` and `sizes` so a phone does not download a desktop
  asset.
- Compressed video in place of an animated GIF: `<video autoplay muted loop playsinline>` with a
  still fallback. A GIF is typically an order of magnitude larger for worse quality.
- Short decorative loops additionally need an H.264 MP4 source for Safari, a
  `prefers-reduced-motion` media condition on the source, and a still image fallback.
- Decorative background imagery belongs in CSS with resolution switching, not in the DOM.

## Long lists

- Over about 50 items, virtualize, or use `content-visibility: auto` with a
  `contain-intrinsic-size` hint so the browser can skip offscreen rendering without breaking
  scrollbar length.
- `content-visibility` is the cheaper first move: no library, no changed markup. Virtualization is
  the answer when rows are expensive rather than merely numerous.
- Paginate or aggregate rather than rendering thousands of rows and hoping.

## Verify, then guard

- Measure again after the fix, in the field where possible. If the metric did not move, revert the
  change; an unproven optimization is complexity with no payoff.
- Add the guard that stops the regression: a bundle-size budget in CI, a Lighthouse assertion, or
  field monitoring with an alert. Without a guard the same regression returns in a quarter.

## Checkable rules

- `<img>`, `<video>` or `<iframe>` without `width`/`height` or `aspect-ratio`.
- The LCP image lazy-loaded, or lacking `fetchpriority="high"`.
- Below-fold images without `loading="lazy"`.
- Missing `preconnect` for a font or CDN origin that the critical path depends on.
- Fonts without `font-display`.
- Layout read inside render.
- More than about 50 items mapped with neither virtualization nor `content-visibility`.
- Animated GIF where a compressed video would do.
- An animation on `width`, `height`, `top`, `left`, `margin` or `padding`.
- A third-party script loaded synchronously in `<head>`.
- `decoding="sync"` or `decoding="async"` introduced as a performance fix. It schedules when the
  image is presented relative to other content; it does not make decoding faster.

<!-- sources: addy-performance, addy-web-quality, web-dev-vitals, vercel-wig, uiux-pro-max, chrome-mwg -->
