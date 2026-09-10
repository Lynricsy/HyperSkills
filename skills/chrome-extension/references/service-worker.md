# Extension service worker

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [When Chrome terminates it](#when-chrome-terminates-it)
- [Registering listeners](#registering-listeners)
- [State that must survive termination](#state-that-must-survive-termination)
- [Scheduling work](#scheduling-work)
- [Install, update and startup](#install-update-and-startup)
- [Web APIs the worker does not have](#web-apis-the-worker-does-not-have)
- [Offscreen documents](#offscreen-documents)
- [Long-running and gesture-bound calls](#long-running-and-gesture-bound-calls)

## When Chrome terminates it

Three conditions, all worth knowing by number because each produces a different symptom:

| Condition | Symptom |
|---|---|
| 30 seconds with no event and no extension API call | State in module scope disappears between two user actions |
| One event or API call takes longer than 5 minutes | The handler is killed mid-way; partial writes stay partial |
| A `fetch()` response takes longer than 30 seconds | The request rejects even though the server was going to answer |

Receiving an event or calling an extension API resets the idle timer. A dormant worker is
revived by an incoming event, so the worker restarting is normal operation, not a fault.

Some things extend the lifetime and are easy to mistake for a leak: an active
`chrome.debugger` session, an open WebSocket that is sending or receiving, a
`runtime.connectNative()` port, and long-lived message ports while a message is in flight.

`chrome.debugger` keeping the worker alive is also why "it works while DevTools is open"
is not evidence: reproduce with DevTools closed, or force termination from
`chrome://serviceworker-internals` before concluding anything.

## Registering listeners

Every `chrome.*.addListener` call must run in the worker's top-level synchronous pass.
After a restart the worker is re-evaluated from the top and then the queued event is
dispatched; a listener that is registered after an `await`, inside a callback, or inside
`runtime.onInstalled`, does not exist yet when that dispatch happens. The event is lost
silently — there is no error.

```js
// Wrong: the listener only exists after the storage read resolves.
async function init() {
  const { settings } = await chrome.storage.local.get('settings');
  chrome.tabs.onActivated.addListener((info) => track(info, settings));
}
init();

// Right: register at the top level, read configuration inside the handler.
chrome.tabs.onActivated.addListener(async (info) => {
  const { settings } = await chrome.storage.local.get('settings');
  track(info, settings);
});
```

The same rule applies to `chrome.runtime.onMessage`, `chrome.alarms.onAlarm`,
`chrome.contextMenus.onClicked` and every other event: declare the handler at the top
level, do the async work inside it.

Filter early inside the handler instead of registering broadly and branching later — an
event you do not care about still wakes the worker and costs the user battery.

## State that must survive termination

Module-scope variables are a cache with a lifetime you do not control. Anything a user
would notice losing goes to storage; see `storage-and-state.md` for which area.

The practical shape is: read at the start of the handler, mutate, write before returning.
Two handlers running concurrently can both read-modify-write the same key, so for counters
and lists either keep the mutation inside one handler or serialise through a promise chain
the worker holds in module scope (that chain is allowed to be lost — losing it only costs
you the serialisation, not the data).

`chrome.storage.session` is the right home for "hot" state that must not outlive the
browser session: an in-progress recording, a capture state machine, an auth nonce.

## Scheduling work

`setTimeout` and `setInterval` are unreliable here: the worker can be gone before the
callback fires. Use `chrome.alarms`, which wakes the worker.

Chrome clamps alarms to at most once every 30 seconds and may delay them further.
`periodInMinutes` or `delayInMinutes` below `0.5` is not honoured and logs a warning;
`when` may be less than 30 seconds away but still will not fire sooner than that. Unpacked
extensions have no clamp at all, which is why a too-frequent alarm looks fine in
development and stops working once installed from the store.

For a job that legitimately takes minutes, do not try to hold the worker open. Split it
into steps, persist a cursor, and drive the steps from a repeating alarm; each step then
starts from the cursor whether or not the worker survived.

## Install, update and startup

```js
chrome.runtime.onInstalled.addListener(({ reason, previousVersion }) => {
  if (reason === 'install') seedDefaults();
  if (reason === 'update') migrate(previousVersion);
});
chrome.runtime.onStartup.addListener(rebuildEphemeralState);
```

`onInstalled` fires once per install or update, so it is where defaults and storage-schema
migrations belong — but never where listeners belong. `onStartup` fires when the profile
starts, before any other worker event.

Things that do not survive an update and must be re-created from `onInstalled`
with `reason === 'update'`: dynamically registered content scripts without
`persistAcrossSessions`, and registered user scripts, which are always cleared. Context
menus are in the same family: the official guide creates them from `onInstalled` rather
than at the top level, so an update re-creates them.

## Web APIs the worker does not have

- No DOM, no `window`, no `document`. `DOMParser`, `Canvas`, `Audio` and
  `MediaRecorder` are unavailable — that is what an offscreen document is for.
- No Web Storage API: `localStorage` and `sessionStorage` do not exist, so calling them is
  a `TypeError`, not a style problem. `chrome.storage`, IndexedDB and `CacheStorage` are
  available.
- `chrome.extension.getBackgroundPage()` is gone; there is no persistent page to reach.

## Offscreen documents

An offscreen document is a hidden DOM context for exactly the Web APIs above. An installed
extension can have only one open at a time (a split-mode incognito profile gets its own).

```js
await chrome.offscreen.createDocument({
  url: 'offscreen.html',
  reasons: ['CLIPBOARD'],           // determines the document's lifespan
  justification: 'read HTML from the clipboard to parse a recipe',
});
```

`AUDIO_PLAYBACK` closes the document 30 seconds after audio stops; every other reason
imposes no lifetime limit, so close it yourself when the work is done. Creating a second
one throws, so check for an existing document with `chrome.runtime.getContexts()` and
guard concurrent creation with a module-scope promise.

Inside the document, almost the whole `chrome.*` surface is undefined — only
`chrome.runtime` messaging and `chrome.runtime.getURL()` are usable. So
`chrome.downloads.download()`, `chrome.action.setBadgeText()` and `chrome.tabs.*` all fail
with `TypeError` there. Split the work: the offscreen document does the Web API part and
messages the result back; the worker does everything that needs an extension API.

## Long-running and gesture-bound calls

A handful of APIs show a user prompt and are allowed past the five-minute ceiling:
`desktopCapture.chooseDesktopMedia()`, `identity.launchWebAuthFlow()`,
`management.uninstall()` and `permissions.request()`.

`permissions.request()` also needs a live user gesture. A gesture does propagate from a
popup or side panel into the worker's `onMessage` listener, but only for that one
synchronous turn: any `await` before the call loses it and the call throws
`This function must be called during a user gesture`. Call it first in the listener, with
nothing awaited before it.

APIs that own an exclusive resource — `chrome.tabCapture`, `chrome.desktopCapture`,
`chrome.offscreen.createDocument` — fail on a second concurrent start. A double click on
the toolbar icon is enough to trigger it, so drive them from an explicit state machine
(`idle → starting → running → stopping`) kept in `chrome.storage.session`, and return
early while a transition is in flight.

<!-- sources: chrome-modern-web-guidance, samber-cc-skills, chrome-docs, dot-skills, chrome-samples -->
