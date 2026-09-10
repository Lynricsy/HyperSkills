# View transitions and client-side routing

Verified against: Astro 7.3

## Contents

- [Two different features](#two-different-features)
- [Enabling `<ClientRouter />`](#enabling-clientrouter)
- [Transition directives](#transition-directives)
- [Persisting state and islands](#persisting-state-and-islands)
- [Script re-execution](#script-re-execution)
- [Lifecycle events](#lifecycle-events)
- [Controlling navigation](#controlling-navigation)
- [Forms](#forms)
- [Fallback and accessibility](#fallback-and-accessibility)
- [Debugging checklist](#debugging-checklist)

## Two different features

**Native cross-document view transitions** are pure CSS
(`@view-transition { navigation: auto }` plus `view-transition-name`). They
animate real multi-page navigations, add no JavaScript, and change nothing about
how the page loads. Where they suffice, they are the better default.

**`<ClientRouter />`** intercepts navigation and swaps the DOM in the browser.
That is what buys persisted islands, lifecycle hooks, scroll control, form
transitions and a fallback for browsers without the View Transitions API — and
it costs a client-side router with its own failure modes. `[official]`

Choose `<ClientRouter />` for a specific capability from the second list, not
for animation alone.

## Enabling `<ClientRouter />`

```astro
---
// src/components/CommonHead.astro
import { ClientRouter } from "astro:transitions";
---
<ClientRouter />
```

Put it in the shared `<head>`. Both the source and destination page must render
it — a link into a page without it performs a full reload, which is a legitimate
way to opt a section out.

The component is `ClientRouter`. `<ViewTransitions />` was removed.

## Transition directives

| Directive | Effect |
|---|---|
| `transition:name="hero"` | Pairs two elements across pages when Astro's automatic matching guesses wrong; each name may be used once per page |
| `transition:animate="fade \| initial \| slide \| none"` | Overrides the animation, per element or on `<html>` for the whole page |
| `transition:persist` | Moves the existing DOM node to the new page instead of replacing it |
| `transition:persist-props` | With `persist`, also keeps the original props instead of re-rendering with the new page's props |

`transition:animate` also accepts a configured built-in
(`fade({ duration: "0.4s" })`) or a full custom object with `forwards` /
`backwards` and `old` / `new` keyframes.

## Persisting state and islands

`transition:persist` keeps a `<video>` playing or an island's state alive across
navigation:

```astro
<Counter client:load transition:persist initialCount={5} />
<video controls autoplay transition:persist="media-player" />
```

Behaviour worth knowing before relying on it:

- The element must exist on both pages. If it lives in a different component on
  the destination, pair the two with a matching `transition:name`, or pass the
  name as the value of `transition:persist`.
- A persisted island keeps its state but **re-renders with the new page's
  props** — deliberate, so page-specific props stay correct. Add
  `transition:persist-props` to freeze the props too. `[official]`
- CSS animations restart and iframes reload regardless. `[official]`

## Script re-execution

This is the most common regression when adding `<ClientRouter />` to an existing
site.

Bundled module scripts — Astro's default `<script>` — execute **once per
session**. After the first execution they are ignored even if the destination
page contains them, because the module is already in the module registry. A
`DOMContentLoaded` listener therefore never fires again, and the mobile menu
stops working on the second page. `[official]`

Fixes, in order of preference:

```astro
<script>
  // 1. Re-run setup after every navigation.
  document.addEventListener("astro:page-load", () => {
    document.querySelector(".hamburger")?.addEventListener("click", toggle);
  });
</script>

<script is:inline data-astro-rerun>
  // 2. Force an inline (unbundled) script to re-execute on every swap.
</script>
```

`data-astro-rerun` only applies to inline scripts, and any attribute besides
`src` already implies `is:inline`. Because `window` survives a swap, code that
initialises global state must be idempotent — guard on a flag rather than
assuming one execution.

Scripts run in the order they are written, matching browser behaviour.

## Lifecycle events

Fired on `document`, in order: `astro:before-preparation` →
`astro:after-preparation` → `astro:before-swap` → `astro:after-swap` →
`astro:page-load`. `before-` events can modify what is about to happen;
`after-` events report completion.

Where each one earns its place:

- `astro:page-load` — the general "run this on every page" hook. It also fires
  on the very first load, so one listener covers initial render and navigation.
- `astro:after-swap` — the new DOM is in place but not yet painted, and history
  and scroll are already updated. This is where a theme is re-applied to avoid a
  flash of the wrong colour scheme, and where custom scroll restoration goes.
- `astro:before-swap` — the last chance to alter the incoming document or
  replace the swap implementation.

## Controlling navigation

```astro
<a href="/report.pdf" data-astro-reload>                 <!-- force a full page load -->
<a href="/main" data-astro-history="replace">            <!-- replace instead of push -->
```

```ts
import { navigate } from "astro:transitions/client";
navigate("/blog");            // works in scripts and in hydrated islands
```

`navigate()` does not sanitise its argument. Passing a `?redirect=` parameter
straight through allows navigation off-site and `javascript:` execution —
validate against an allow-list first. `[official]`

`navigate()` is a no-op during server rendering, and combining it with
`history.back()` / `history.forward()` covers back-and-forward control.

## Forms

`<ClientRouter />` transitions `GET` and `POST` form submissions. It submits
`POST` as `multipart/form-data` by default; add
`enctype="application/x-www-form-urlencoded"` to match plain browser behaviour.
Opt a single form out with `data-astro-reload`. The old `handleForms` prop was
removed — form handling is unconditional.

## Fallback and accessibility

`fallback` controls behaviour in browsers without the View Transitions API:
`animate` (default, simulates transitions with custom attributes), `swap`
(replace with no animation), `none` (full page loads). Under a fallback, only
elements with explicit `transition:name` or `transition:animate` animate, so a
page relying entirely on Astro's automatic matching looks different there.

The router announces the new page title to assistive technology through an
`aria-live` region — no configuration needed — and disables every animation,
including the fallback, under `prefers-reduced-motion`. `[official]`

## Debugging checklist

| Symptom | Cause |
|---|---|
| A link does a full reload | Destination page does not render `<ClientRouter />`, or the link has `data-astro-reload` |
| Script works on first load, dead afterwards | Bundled module script executed once; move setup into `astro:page-load` |
| Theme flashes on navigation | Theme applied on load rather than in `astro:after-swap` |
| Island loses its state | Missing `transition:persist`, or the element is not matched across pages |
| Island keeps state but props reset | Expected; add `transition:persist-props` |
| Animation missing in Firefox/Safari | Fallback path animates only explicitly named elements |
| Duplicate global state after navigating | Inline script re-ran; make initialisation idempotent |

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev -->
