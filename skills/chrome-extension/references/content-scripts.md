# Content scripts

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [The isolated world](#the-isolated-world)
- [Reaching page JavaScript](#reaching-page-javascript)
- [Injection timing](#injection-timing)
- [Static, dynamic and programmatic injection](#static-dynamic-and-programmatic-injection)
- [Single-page-app navigation](#single-page-app-navigation)
- [Orphaning and teardown](#orphaning-and-teardown)
- [Injected UI](#injected-ui)
- [User scripts](#user-scripts)

## The isolated world

A content script shares the page's DOM and nothing else. Its JavaScript realm is separate
from the page's and from every other extension's, so `window.someAppGlobal` set by the
page is `undefined` in the content script, and a library the page loaded is not visible
either. `world` defaults to `ISOLATED`; the DOM is the only shared surface.

What a content script *does* get: `chrome.runtime` messaging, `chrome.storage`,
`chrome.i18n`, and — because it runs in the page's origin — the page's cookies, CSP and
CORS rules for any network request it makes itself.

## Reaching page JavaScript

Two ways, and they trade opposite things:

**`world: "MAIN"`** puts the script in the page's realm, so page globals are readable —
but a MAIN-world script has no `chrome.*` APIs at all, and it is also visible to the page,
which can tamper with it. Use it only for the smallest possible shim.

**A page-world bridge**, which is the default choice: keep the logic in the isolated
content script and inject a tiny script into the page that reads the global and posts it
back through the DOM.

```js
// content script (isolated world)
const url = chrome.runtime.getURL('bridge.js');   // must be web-accessible
const el = document.createElement('script');
el.src = url;
el.onload = () => el.remove();
document.documentElement.append(el);

window.addEventListener('message', (event) => {
  if (event.source !== window) return;             // reject other frames
  if (event.origin !== location.origin) return;
  if (event.data?.channel !== 'price-watcher') return;
  chrome.runtime.sendMessage({ type: 'PRICE_SEEN', price: event.data.price });
});
```

Two failures cluster here. A bare `src = 'bridge.js'` resolves against the *page's*
origin, so the page 404s — always go through `chrome.runtime.getURL()`. And the file must
be listed in `web_accessible_resources`, which also exposes it to every script on the
matched sites, so keep bridges tiny and list them individually rather than with a
wildcard.

Never trust a `message` event without checking `event.source`, `event.origin` and a
channel marker: any script on the page, including a third-party ad frame, can post to
`window` and reach your handler.

## Injection timing

| `run_at` | Document state |
|---|---|
| `document_start` | Before any DOM is built — `document.body` is `null`, `document.head` may be too |
| `document_end` | DOM parsed, subresources may still be loading |
| `document_idle` | Default; between `document_end` and `window.onload`, whichever comes first |

Use `document_idle` unless you must run before page scripts (for example to shadow a
global or block a redirect). At `document_start`, anything touching `document.body` or
`querySelector` on page content is a null dereference; attach to
`document.documentElement`, or wait for `DOMContentLoaded`, before doing DOM work.

## Static, dynamic and programmatic injection

Declare statically in `manifest.json` when the URL patterns are known — that is the
documented default, it survives worker restarts, and it applies before every other
injection mechanism at each document stage.

```jsonc
"content_scripts": [{
  "matches": ["https://shop.example.com/product/*"],
  "js": ["content.js"],
  "run_at": "document_idle"        // world defaults to ISOLATED
}]
```

Reach for `chrome.scripting.registerContentScripts()` when the patterns are not known
until runtime (a user-configured site list), and for
`chrome.scripting.executeScript()` when injection should follow a user action. Give
dynamic registrations `persistAcrossSessions: true` unless you intend to re-register them
on every startup, and remember that they are cleared by an extension update either way.

Narrow `matches` as far as the feature allows. `<all_urls>` and `*://*/*` are the single
biggest driver of both permission warnings and review time, and a content script on every
page is also a performance cost on every page.

## Single-page-app navigation

A content script is injected once per document load. A client-side route change does not
reload the document, so the script neither re-runs nor gets torn down: the feature works
on first load and silently stops after the user navigates.

Watch for it instead of relying on injection. In the content script, a `MutationObserver`
on the container plus a `popstate`/`navigate` listener covers most apps; from the service
worker, `chrome.tabs.onUpdated` with a URL check works when the SPA updates the address
bar. Guard against double-mounting: check for your own marker node first, and make the
observer ignore mutations your own DOM writes caused, or the observer's own reaction
becomes an infinite loop.

## Orphaning and teardown

Reloading or updating the extension kills the message channel of every already-injected
content script while the script keeps running in the page. Every `chrome.runtime` call
then throws `Extension context invalidated`.

```js
const alive = () => {
  try { return Boolean(chrome.runtime?.id); } catch { return false; }
};
```

Check before messaging, and when it returns false, disconnect observers, remove injected
nodes and event listeners, and stop. If the user needs the feature back, say so in the
injected UI rather than throwing on every mutation. Content scripts do not survive an
update, so the reload prompt is the honest answer, not a bug.

## Injected UI

Page CSS will style anything you insert into the page, and your CSS will leak back into
the page. Mount injected UI inside a shadow root attached to a container element you own,
keep a single stable id on that container so re-injection is detectable, and remove it in
the teardown path above.

Do the DOM work in batches. A content script writing to hundreds of nodes in one
synchronous pass blocks the page's main thread, which the user experiences as the site
being slow. Chunk the work across `requestAnimationFrame` callbacks and read before you
write to avoid layout thrashing.

## User scripts

`chrome.userScripts` runs code the *user* supplies at runtime — script managers and user
automation. It is not the mechanism for shipping your own scripts; use content scripts
for those.

Four things bite:

1. The API throws on property access until the user enables it: from Chrome 138 with the
   "Allow user scripts" toggle on the extension's details page, and before that with
   developer mode. Probe it in a `try`/`catch` around a harmless call such as
   `chrome.userScripts.getScripts()` and render an onboarding path when it fails.
2. Registrations are cleared on extension update. Persist the configuration in
   `chrome.storage` and re-register from `runtime.onInstalled` on `reason === 'update'`.
3. Messaging needs explicit opt-in: call
   `chrome.userScripts.configureWorld({ messaging: true })`, then listen on
   `chrome.runtime.onUserScriptMessage` — not `onMessage`. The separate event exists
   because user-script code is less trusted than your own.
4. Each `js` entry must carry exactly one of `code` or `file`, and a script `id` may not
   start with `_`.

<!-- sources: chrome-modern-web-guidance, samber-cc-skills, chrome-docs, dot-skills, wxt-docs -->
