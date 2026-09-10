# Messaging and execution contexts

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [What each context can do](#what-each-context-can-do)
- [Choosing a channel](#choosing-a-channel)
- [Async replies](#async-replies)
- [Ports](#ports)
- [Pushing to a popup or side panel](#pushing-to-a-popup-or-side-panel)
- [Typed protocols](#typed-protocols)
- [Errors you will see](#errors-you-will-see)

## What each context can do

```
 extension process
 ┌───────────────┐  ┌───────┐  ┌─────────┐  ┌────────────┐  ┌───────────┐
 │ service worker│  │ popup │  │ options │  │ side panel │  │ offscreen │
 │ all chrome.*  │  │ all chrome.*, full DOM, lifetime │  │ runtime   │
 │ no DOM        │  │ tied to the surface being open   │  │ only, DOM │
 │ ephemeral     │  └───────┘  └─────────┘  └────────────┘  └───────────┘
 └───────┬───────┘        │          │             │              │
         │ chrome.runtime.sendMessage / connect (all of the above) │
         │                                                        │
 tab ────┴── chrome.tabs.sendMessage(tabId) ──┐                   │
 ┌──────────────────────┐    ┌────────────────▼────────┐          │
 │ content script       │    │ page / MAIN-world script│          │
 │ isolated world       │◄──►│ page realm              │          │
 │ runtime + storage    │ DOM│ no chrome.* at all      │          │
 │ page origin & CSP    │ msg│ page origin & CSP       │          │
 └──────────────────────┘    └─────────────────────────┘          │
```

The one thing to internalise: **no two boxes share memory.** A value read in the popup is
not visible to the worker, and a page global is not visible to a content script. Every
extension bug that "makes no sense" is usually someone assuming otherwise.

Lifetimes differ too. A popup is destroyed the moment it loses focus, so anything it was
mid-way through is gone. A side panel persists while it is open. The worker comes and goes
on its own schedule (see `service-worker.md`).

## Choosing a channel

| Need | Use |
|---|---|
| One request and one reply, from any extension context to the worker | `chrome.runtime.sendMessage` |
| Worker or UI page → a specific tab's content script | `chrome.tabs.sendMessage(tabId, …)` |
| A stream, progress updates, or a session that outlives one exchange | `chrome.runtime.connect` port |
| Page realm ↔ content script on the same page | `window.postMessage`, validated |
| One value that several contexts must all see | write it to `chrome.storage`; every context gets `onChanged` |

Prefer `chrome.storage` + `onChanged` for shared settings: it removes the need to push the
same update to three surfaces, and it works even when a surface was closed at the time.

Do not broadcast to every tab to reach one of them. Query for the tab you mean, or have
the content script initiate; a broadcast wakes every injected script and every one of them
answers.

## Async replies

The listener signature is `(message, sender, sendResponse)`. By default `sendResponse`
must be called synchronously; returning a literal `true` keeps the channel open so it can
be called later.

```js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== 'GET_REPORT') return;      // let other listeners see it
  buildReport().then(sendResponse, (err) => sendResponse({ error: err.message }));
  return true;                                    // literal true, not a truthy value
});
```

Without the `return true`, the channel closes when the listener returns and the sender's
`await chrome.runtime.sendMessage(...)` resolves with `undefined` — no error anywhere. An
`async` listener is the same trap in disguise: it returns a `Promise`, which is truthy but
is not `true`, so use the wrapper shape above instead of marking the listener `async`.

From Chrome 148 a listener may return a promise directly, but the capability is rolling
out gradually and is disabled for extensions that declare a `devtools_page`. `return true`
works either way, so make it the default and treat promise return as an optimisation you
do not depend on.

Also reject early: a listener that does not recognise the message must `return` without
calling `sendResponse`, or it will answer messages meant for another listener.

## Ports

```js
// content script
const port = chrome.runtime.connect({ name: 'sync' });
port.onMessage.addListener(onProgress);
port.onDisconnect.addListener(() => { /* worker restarted or tab closed */ });

// worker
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== 'sync') return;
  port.onMessage.addListener((msg) => port.postMessage(step(msg)));
});
```

A port carries many messages in both directions, which is what you want for progress
reporting or a long dialogue. It is not a keep-alive: opening a port no longer resets the
idle timer, though a message crossing it does. Always handle `onDisconnect` and be able to
reconnect — the worker restarting is expected.

## Pushing to a popup or side panel

The worker cannot call into a popup or side panel out of the blue; those pages are only
reachable while they are open. Either the page opens a port and the worker pushes down it,
or the worker writes to `chrome.storage` and the page reacts to `onChanged`. The second
option is the one that also works when the page is closed and opened later.

## Typed protocols

Message payloads are structured-clone JSON: no `Map`, `Set`, `Date`-as-`Date`, class
instance or function survives the hop. Keep payloads small — a large blob is copied, and
copying it on every mutation is a real cost.

Give every message a `type` from a shared union and route on it in one place. In a
TypeScript project this is worth a discriminated union and one `sendMessage` wrapper per
direction; that turns "the worker silently ignored my message" into a compile error. In a
WXT project, use one of the messaging libraries WXT recommends rather than writing the
wrapper by hand (see `wxt-and-tooling.md`).

## Errors you will see

| Message | Meaning |
|---|---|
| `Could not establish connection. Receiving end does not exist.` | No content script in that tab (never injected, injected before the extension reloaded, or the tab is a `chrome://` page). Inject on demand, or treat it as a normal outcome |
| `Extension context invalidated` | The content script is orphaned after an extension reload; see `content-scripts.md` |
| `The message port closed before a response was received.` | The listener returned without `return true`, or threw before replying |
| `Cannot access contents of the page.` | Missing host permission for that origin |

`chrome.runtime.lastError` must be read inside the callback that received it; reading it
afterwards gets `undefined` and Chrome logs the unchecked error itself.

<!-- sources: chrome-modern-web-guidance, samber-cc-skills, chrome-docs, dot-skills, rsc-harness -->
