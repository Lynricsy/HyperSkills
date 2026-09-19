# Presenter mode, speaker notes, and live recovery

## Contents

- [Picking the two-window transport](#picking-the-two-window-transport)
- [Two-window architecture](#two-window-architecture)
- [What belongs on each surface](#what-belongs-on-each-surface)
- [Writing the notes](#writing-the-notes)
- [Live failure recovery](#live-failure-recovery)
- [Keyboard contract](#keyboard-contract)

## Picking the two-window transport

A deck opened from `file://` plays in one window and exports fine. Whether a *second* window can
follow it depends entirely on how that window is opened, and the two options fail in opposite ways.

**Child window the deck renders into — works from `file://`.** `window.open('')` yields an
`about:blank` document that inherits the opener's origin, so the presenter window keeps full DOM
access to it: writing `child.document.body.innerHTML` and reading it back across the two windows
succeeds under `file://` [verified: `sameOriginDom: true`, value written by the opener read back
from the child]. There is no channel, no storage and no receipt to get wrong, because there is only
one copy of the state — the presenter window owns it and paints the audience window. Cost: the
audience window is built by script, so the deck's own stylesheet has to be injected into it.

**Second window loading the deck URL — needs a server.** Open `deck.html?view=audience` from
`file://` and the handle comes back live but inert: reading `handle.location.href` or
`handle.document` throws `SecurityError`, while identical code served from `http://localhost`
returns both [verified]. Every local file is its own document for DOM-access purposes, so the
presenter can neither read what the audience is showing nor re-point it. An `?preview=N` iframe of
the same file is unreadable for the same reason.

Messaging between two `file://` documents is not the deciding factor, and assuming it is leads to
the wrong fix:

- `localStorage` and `BroadcastChannel` do work between two `file://` documents in a current
  Chromium — storage shared, messages delivered, `storage` events fired, `location.origin` reading
  `file://` in both [verified]. Browser documentation still records `localStorage` behaviour on
  `file:` URLs as undefined and browser-dependent, with the getter throwing `SecurityError` when the
  origin is not a valid scheme/host/port tuple [official], so this is a Chromium observation, not a
  guarantee to build on.
- That single shared `file://` origin is itself the hazard: every deck on disk lands in the same
  storage and the same channel namespace. Namespace both by `location.pathname`, or two decks open
  at once drive each other's slides.
- Framework presenter modes decline rather than degrade: marp-cli registers the `p` shortcut only
  when `storage.available` is true, so the key silently does nothing otherwise [official], and
  reveal.js documents that speaker view used locally requires a local web server [official].
- Notes kept in a side file cannot be loaded at all: Chromium rejects `fetch()` of a `file:` URL
  outright, and no CORS setting relaxes it [verified].

Pick by how the deck is delivered. A deck that gets emailed and double-clicked uses the child-window
transport. A deck presented from a checkout, or one that needs `?view=` deep links, is served:

```bash
python3 -m http.server 8000 --directory ./deck
# open http://localhost:8000/deck.html
```

Say which one the recipient has, because they will double-click the file: "Double-click `deck.html`
to present — press P for presenter view, notes and timer included. Navigation, fullscreen and PDF
export all work from the file. The `?view=presenter` deep link needs `python3 -m http.server 8000`
in this folder."

Do not over-claim the limit. Single-window playback, keyboard navigation, fullscreen and
print-to-PDF are unaffected by `file://`, and Chromium reports `isSecureContext` as `true` there
[verified], so secure-context APIs are not the reason a server is ever needed. DOM access across
two separately loaded local files is.

## Two-window architecture

Two shapes exist; the transport decision above picks one.

**Served deck: one file, role chosen by query string.** The audience window is the deck at
`?view=audience`, the presenter panel is the same file at `?view=presenter`, and the panel's slide
previews come from the same DOM. Everything below about channels and heartbeats belongs to this
shape.

**Double-clicked deck: one window owns the state, the other is painted.** The presenter window
renders the audience window's DOM directly, so there is no second copy to synchronise, no channel,
and no heartbeat — `audience.closed` is the entire connection model. Inject the deck's own
stylesheet rather than writing new rules, or the room sees different type than the review did:

```js
function openAudience() {                        // from a click or keydown handler only
  const w = window.open('', 'deck-audience');    // '' inherits this document's origin
  if (!w) return banner('Popup blocked. Allow popups for this page, then press A again.');
  w.document.title = 'Audience';                 // about:blank already has head and body;
                                                 // document.write() runs before body exists
  for (const sheet of document.querySelectorAll('style, link[rel=stylesheet]')) {
    w.document.head.append(sheet.cloneNode(true));
  }
  w.document.body.dataset.view = 'audience';
  return w;
}
function paint(w, n) {                           // called on every slide change
  if (!w || w.closed) return false;
  w.document.body.replaceChildren(slides[n].cloneNode(true));
  return true;
}
```

Whichever shape is in play, the audience pixels come from the deck's own markup and stylesheet. A
separately built preview drifts — a different font fallback, an accent colour fixed in one place
only, a layout change that landed on one side — and the drift surfaces on stage rather than in
review, because nobody reviews the preview.

**`BroadcastChannel`, namespaced by path.** The channel is scoped to the origin, and every deck on
disk shares the single origin `file://` [verified]. Two decks open at once under a channel named
`deck` drive each other's slides. Derive the name from `location.pathname`.

**The sender never receives its own message** [official; verified: the posting window's handler did
not run while the other window's did]. Update the local view directly and broadcast as a separate
step. A presenter that waits for its own message to come back stays on slide 1.

```html
<script>
const slides = [...document.querySelectorAll('.slide')];
const render = n => slides.forEach((s, i) => s.classList.toggle('is-current', i === n));
const bus = new BroadcastChannel('deck@' + location.pathname);
const role = new URLSearchParams(location.search).get('view') || 'audience';
let current = 0, lastPong = 0;

function goTo(n, announce = true) {
  current = Math.min(Math.max(n, 0), slides.length - 1);
  render(current);                      // always local: the bus does not echo
  if (announce) bus.postMessage({ t: 'goto', n: current });
}

bus.onmessage = ({ data }) => {
  if (data.t === 'goto') goTo(data.n, false);
  if (data.t === 'hello' && role === 'presenter') bus.postMessage({ t: 'goto', n: current });
  if (data.t === 'ping' && role === 'audience') bus.postMessage({ t: 'pong' });
  if (data.t === 'pong') lastPong = Date.now();
};

if (role === 'audience') bus.postMessage({ t: 'hello' });     // a late window catches up
if (role === 'presenter') setInterval(() => {
  bus.postMessage({ t: 'ping' });
  document.body.dataset.audience = Date.now() - lastPong < 3000 ? 'live' : 'lost';
}, 1000);
</script>
```

**The heartbeat is load-bearing.** `BroadcastChannel.postMessage()` returned `undefined` and threw
nothing after the only other window had been closed [verified]. There is no delivery receipt at any
layer, so without `ping`/`pong` the presenter advances a deck nobody is watching and learns about it
from the audience. Bind a visible indicator to `data-audience`; a console log is not a stage signal.

Measured behaviour of the loop above, with the audience window opened and then closed [verified]:
the indicator reads `lost` for the first period (status is computed in the same tick that sends the
ping, so the first reply arrives after it), flips to `live` at the second tick (~2.4 s), and returns
to `lost` 2.4 s after the audience window closes. Keep the threshold at three or more ping periods
so one dropped tick does not flash a false `lost` mid-talk.

Opening and closing the audience window:

```js
let audience = null;
function openAudience() {                        // call from a click or keydown handler only
  audience = window.open(location.pathname + '?view=audience', 'deck-audience');
  if (!audience) return banner('Popup blocked. Allow popups for this page, then press A again.');
  bus.postMessage({ t: 'goto', n: current });    // covers a load that races its own hello
}
function closeAudience() {
  if (audience && !audience.closed) audience.close();
  else banner('Audience window is not ours to close — close it by hand.');
}
```

`window.open()` returns `null` when a blocker stops it, and blockers permit it only during user
activation [official]: calling it on `DOMContentLoaded` or from a timer yields `null` and no dialog,
so the presenter sees nothing happen. Handle the `null` with an on-screen banner naming the key to
press again. `audience.closed` remains readable even across `file://` documents [verified], so the
closed check is safe everywhere; everything richer than `closed` and `close()` needs the served URL.

## What belongs on each surface

| Element | Audience window | Presenter window | Why the split |
|---|---|---|---|
| Current slide | full-bleed, the only content | small, rendered from the same deck | the presenter must see the pixels the room sees, not a proxy |
| Next slide | never | preview, visibly dimmed | showing the next slide early removes the reason to keep listening |
| Speaker notes | never rendered | largest text in the panel | notes are read at a glance from a metre away; shrinking them makes them decorative |
| Elapsed and remaining | never | both, remaining as the primary figure | elapsed alone forces arithmetic under pressure; a clock facing the room competes with the speaker |
| Slide number / total | small, low-contrast corner | large, next to remaining time | the room uses it to ask questions, the presenter to pace |
| Audience connection | n/a | explicit `live` / `lost` indicator | the only thing that turns a dropped window into a recoverable event |
| Wall clock | never | yes | the room's hard end time is not the deck's elapsed time |

Notes stay inside the slide markup so a slide and its script never separate, and the audience path
never renders them:

```html
<section class="slide">
  <h2>Throughput regression</h2>
  <template data-notes>
    Purpose: the regression is in the scheduler, not the model.
    Beats: p99 1.8s -> 4.1s (bench/run-114.json); only batch>8; rollback fixed it in 3 min.
    Transition: "so the question is what changed in batching."
    Planned: 90
  </template>
</section>
```

A `<template>` beats a `display:none` container: a later layout rule such as `.slide > * { display:
flex }` overrides `display:none` and puts the notes on the projector — the same override that makes
`display`-based slide switching reveal every slide at once — while template content is not rendered
by any stylesheet. Read it with
`slide.querySelector('[data-notes]').content.textContent` [official; verified: the notes text is
absent from `document.body.innerText` and still readable through `.content`].

Never park notes as visible stage text "for now", and never hide them with `color: transparent` or
`opacity: 0`: both keep the text in the PDF export, in text selection, and in the accessibility tree.

## Writing the notes

Four fields per slide, in this order, inside the notes container:

| Field | Content | Length |
|---|---|---|
| Purpose | the one thing the audience keeps after this slide | one sentence |
| Beats | 3–5 cues: keyword, figure with its source file, the name of the example | fragments |
| Transition | the sentence that hands over to the next slide | one sentence, written out |
| Planned | intended duration in seconds | a number |

Rules that decide whether the notes survive contact with a stage:

- Budget 150–300 words per slide, which runs about 2–3 minutes spoken [community]. Past 300 words the
  presenter reads instead of speaking, and the reading voice is audible from the back of the room.
- Write cues, not prose to be recited. "p99 1.8s -> 4.1s, only batch>8" is scannable in one glance;
  the same fact in a full sentence is not.
- Write the transition out in full. It is the one sentence people fluff, and it is the one place
  where a wrong hand-over makes the next slide look unmotivated.
- Attach a source to every figure in the notes — file, query or report name. A number a presenter
  cannot attribute when challenged costs more than the slide gained.
- Invent nothing the source material does not contain. Audience interaction, room logistics, demo
  timing, name pronunciation and anecdotes are not derivable from a document. Leave the field as
  `[unknown: pronunciation of the customer name]` so the gap is visible and fillable, and say in the
  handover which slides carry unknowns.
- Sum the planned durations before delivery and compare against the slot. 18 slides at 90 s is 27
  minutes and does not fit a 20-minute slot; remove slides rather than plan to talk faster.
- Mark deliberate silence. A full-bleed image held without commentary gets `Planned: 15` and one
  beat, so the presenter does not read it as a hole in the script.

## Live failure recovery

Every remedy below is one or two keystrokes and needs no other tool.

**Audience screen goes black or white.** Check the connection indicator first: `lost` means the
window is gone (reopen it), `live` means the browser is still there and the display path is at
fault. Press the fullscreen key on the audience window to force a repaint, then re-send the current
slide. A deck that entered fullscreen and then lost the external display frequently repaints on the
wrong screen; leaving and re-entering fullscreen on the correct window fixes it faster than any
display-settings dialog.

**Audience window frozen on an old slide.** The indicator says `live` but the content lags: press the
resend key, which posts `{ t: 'goto', n: current }` without changing `current`. If the slide still
does not move, the window has a rendering fault rather than a sync fault — close it and reopen.

**Audience window lost.** Closed by hand, killed with the projector, or crashed. The indicator flips
within one ping period plus the threshold (2.4 s measured for a 1 s ping and a 3 s threshold
[verified]). Press the open key: the new window posts `hello`, the presenter answers with the current
slide number, and playback resumes at the right slide with nothing to click through. This is the
whole reason `hello` exists — without it, recovery means arrowing through the deck in front of the
room.

**Leaving at the end.** Call `close()` on the audience window from the presenter before unloading.
`window.close()` only closes a window that script opened [official]; a window the presenter opened by
hand from the address bar fails silently, so fall back to a banner that tells the presenter to close
it rather than claiming success.

Pre-flight checklist — run it once with the projector attached, not in the hotel room:

- Popups allowed for the deck's origin: press the audience-open key once, confirm a second window
  appears instead of a `null` banner.
- Server still running and reachable at the served URL; reload both windows after any restart,
  because a restarted server does not reconnect the channel by itself.
- Fullscreen applied to the audience window only; confirm the presenter window keeps its panel.
- Fonts verified offline: load the deck with networking disabled and confirm no fallback face
  appears, since a font that loads at the desk and not in the room changes every line break.
- External display geometry checked: a 16:10 or 16:9 projector letterboxes the 1920x1080 stage
  differently; confirm the bars are symmetrical and nothing is cropped at the edges.
- Sleep, screensaver and notifications disabled, machine on mains power. A notification banner is
  rendered on the projector, not on the presenter's panel.
- Connection indicator observed going `live` before the room fills, so its `lost` state is
  trustworthy later.

## Keyboard contract

| Key | Action | Registered in |
|---|---|---|
| Right / Space | next slide | both windows |
| Left | previous slide | both windows |
| Home / End | first / last slide | both windows |
| O | overview grid | both windows |
| F | fullscreen the focused window | both windows |
| A | open or reopen the audience window | presenter only |
| R | re-send the current slide | presenter only |
| Esc | leave fullscreen (browser-owned) | bind in neither |

Register navigation in both windows because `keydown` is delivered only to the focused window, and
focus follows the last click. The presenter clicks the audience window once — to drag it onto the
projector, or to make fullscreen apply to it — and from that moment the arrow keys arrive there. A
deck that binds keys only in the presenter panel stops responding, and from the stage that is
indistinguishable from a crash. Route every key through `goTo()` so the bus keeps the other window in
step regardless of which one received it.

Two exclusions. Ignore keys while `document.activeElement` is an input, textarea or
`isContentEditable` element, or editing notes advances the deck on every space. Leave `Esc` unbound:
the browser owns it for exiting fullscreen, and a handler that also navigates turns one exit press
into an unintended slide change.

<!-- sources: lewislulu-html-ppt, marp-cli, revealjs, slidev, event4u-html-deck -->
