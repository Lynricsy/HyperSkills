# Modern CSS and HTML platform features

Verified against: `modern-web-guidance` (Google Chrome), 143 guides across 14 categories, queried
through the published npm package.

The point of this file is not to list which features are supported. Support moves, and any list
written down here would be wrong within months. The point is to make the tool the source of truth
and to describe the shapes of the answers it gives, so a plan can be made before the tool is called.

## Contents

- [The workflow](#the-workflow)
- [Reading a Baseline verdict](#reading-a-baseline-verdict)
- [Browser support policy](#browser-support-policy)
- [Goal to guide map](#goal-to-guide-map)
- [Fallback shapes](#fallback-shapes)
- [What not to do](#what-not-to-do)

## The workflow

```bash
# 1. Phrase the goal as an action, not as a feature name.
npx -y modern-web-guidance@latest search "change layout based on the component's own width"

# 2. Retrieve the best match. Multiple ids can be comma-separated.
npx -y modern-web-guidance@latest retrieve "size-aware-styling"

# 3. Browse when search similarity is low or results look vague.
npx -y modern-web-guidance@latest list
```

`search` returns JSON: `id`, `description`, `category`, `featuresUsed`, `tokenCount`, `similarity`.
Low `similarity` across all rows means the query was phrased as a feature rather than a goal; rephrase
it as what the interface should do.

`retrieve` returns the full markdown guide, which ends with a **Fallback strategies** section
carrying the Baseline verdict and the per-engine support versions. If the output is truncated,
redirect it to a file and read the file.

Where `pnpm` is available, `pnpx modern-web-guidance@latest ...` works the same and takes no `-y`
flag. Where `~/.npm` is not writable, set `NPM_CONFIG_CACHE=/tmp/npm-cache`. The call needs outbound
network access, so request approval before the first invocation in a gated environment.

## Reading a Baseline verdict

The guide states the status in prose, for example:

```text
Baseline status for Container queries: Widely available. It's been Baseline since 2023-02-14.
Supported by: Chrome 105 (Sep 2022), Edge 105 (Sep 2022), Firefox 110 (Feb 2023), Safari 16 (Sep 2022).
```

Interpretation:

| Verdict | Default action |
|---|---|
| Widely available | Use it directly. No fallback, no `@supports`, no polyfill. |
| Newly available | Ship the fallback the guide prescribes, unless the project's stated policy allows newly available features. |
| Limited availability | Treat as an enhancement only. The interface must work fully without it. |

For a `Baseline YYYY` target, a feature satisfies the target when its "Baseline since" year is less
than or equal to `YYYY`.

## Browser support policy

Most projects have no written policy, and the absence is the reason fallback decisions get made
inconsistently. Look for one in `AGENTS.md` or the project's contributing docs before assuming.

Policy shapes that actually resolve decisions:

- "Do not implement feature fallbacks." Suitable for prototypes of the cutting-edge web.
- "Safari 17.4+." Suitable for internal tools targeting one platform, or Tauri and Electron shells.
- "Never polyfill. If a newly available feature is required for core functionality, write a
  lightweight custom fallback or redesign the approach."
- "Newly available features are allowed when strictly feature-detected and degrading gracefully."

Signals that a policy should be proposed: the project targets a restricted runtime, explicitly
excludes a browser, expresses concern about polyfill weight, or asks whether a feature is safe. When
one of those appears, propose a single line for the project to adopt rather than deciding silently.

## Goal to guide map

Common design goals and the guide ids that answer them. Search anyway; ids change less often than
support does, but this list is a shortcut, not a substitute.

| Goal | Guide id |
|---|---|
| Component adapts to its own width, not the viewport | `size-aware-styling` |
| Style a parent based on its children | `style-parent-with-has`, `content-based-styling` |
| Style an element based on a sibling's state | `dynamic-sibling-styling`, `child-state-based-styling` |
| Type and spacing that scale smoothly between breakpoints | `fluid-scaling` |
| Animate to or from `auto` height | `animate-to-intrinsic-sizes` |
| Animate entry and exit, including from the top layer | `animate-element-entry-exit`, `animate-to-from-top-layer` |
| Page or view transitions | `same-document-transitions`, `cross-document-transitions`, `faster-spa-view-transitions` |
| Scroll-driven reveals and parallax | `scroll-entry-exit-effects`, `parallax-scroll-effects`, `scrollytelling` |
| Scroll progress indicator | `scroll-progress-indicator` |
| Tooltip or menu anchored to a trigger | `position-aware-tooltips`, `anchor-positioning-tab-underline` |
| Dialog and popover behavior without JavaScript | `declarative-dialog-popover-control`, `light-dismiss-a-dialog` |
| Sticky header that reacts to scroll state | `state-aware-sticky-headers`, `shrinking-header-on-scroll` |
| Defer rendering of offscreen content | `defer-rendering-heavy-content` |
| Find and fix interaction latency | `identify-inp-causes`, `break-up-long-tasks`, `interactions-in-complex-layouts` |
| Prioritize the hero image or a critical script | `optimize-image-priority`, `optimize-script-priority`, `optimize-preload-priority` |
| Font swap without layout shift | `visually-stable-font-fallbacks`, `visually-stable-mixed-fonts` |
| Dark mode, including per-component | `dark-mode`, `component-specific-light-dark-theme` |
| Style native scrollbars | `customize-scrollbar-color-and-thickness`, `adapt-scrollbar-to-contrast-preferences` |
| Styleable select, autofill-friendly forms | `branded-select-styling`, `brand-consistent-forms`, `autofill-sign-in-form` |
| Validate only after the person has interacted | `validate-input-after-interaction` |
| Announce a form error to assistive technology | `accessible-error-announcement` |
| Locale-aware durations, calendars, relative time | `format-human-readable-durations`, `support-global-calendar-systems` |
| Broad overviews | `css`, `css-layout`, `html`, `performance`, `accessibility`, `forms` |

## Fallback shapes

Three shapes cover nearly every case. The guide names which one applies; these are the patterns to
recognize.

**Safe default, then enhance.** The base rule is the older layout; the new feature refines it inside
`@supports`. This is the shape to prefer, because the base case needs no detection.

```css
.card { display: flex; flex-direction: column; }

@media (min-width: 600px) { .card { flex-direction: row; } }

@supports (container-type: inline-size) {
  .card-container { container-type: inline-size; }
  @container (min-width: 400px) { .card { flex-direction: row; } }
}
```

**Progressive no-op.** The feature degrades to nothing and the interface is still correct, so no
fallback is written at all: `text-wrap: balance`, `text-wrap: pretty`, `overscroll-behavior`,
`scrollbar-color`, most `@starting-style` entrances. Do not wrap these in `@supports`; the extra
block is dead weight.

**Feature-detected behavior swap.** JavaScript checks for the API and takes a different path. Keep
the check at the call site, not behind a global flag set at startup, so the fallback path stays
exercised.

```js
if (document.startViewTransition) {
  document.startViewTransition(() => render(next));
} else {
  render(next);
}
```

## What not to do

- Do not assert from memory that a feature is or is not usable. That is exactly the knowledge that
  goes stale, and the tool answers it in under two seconds.
- Do not adopt a feature the goal did not ask for. The guides describe options; a container query
  added to a component that has one fixed context is complexity with no payoff.
- Do not pin the guide corpus version into project documentation. The package self-updates, and a
  pinned version only produces a stale-warning later.
- Do not reach for a polyfill before checking whether a plain CSS fallback exists. It usually does,
  and it costs nothing at runtime.

<!-- sources: chrome-mwg -->
