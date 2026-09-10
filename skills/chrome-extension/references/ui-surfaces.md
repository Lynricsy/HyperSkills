# UI surfaces

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [Choosing a surface](#choosing-a-surface)
- [Toolbar action and popup](#toolbar-action-and-popup)
- [Side panel](#side-panel)
- [Options page](#options-page)
- [Context menus, commands and omnibox](#context-menus-commands-and-omnibox)
- [Notifications and the badge](#notifications-and-the-badge)
- [DevTools panels](#devtools-panels)
- [Injected UI on a page](#injected-ui-on-a-page)

## Choosing a surface

| Surface | Lifetime | Use when |
|---|---|---|
| Popup | Destroyed on blur | One glance, one action, then done |
| Side panel | Persists while open, follows the user across tabs | The user works alongside the page for minutes |
| Options page | A normal tab or embedded dialog | Settings, rarely visited |
| Injected UI | Lives with the page | The feature belongs visually to the page |

The deciding question is whether the user needs to interact with the page while your UI is
visible. If they do, a popup is wrong — it closes the moment they click the page.

## Toolbar action and popup

`chrome.action.*` needs the `action` key in the manifest, even empty (see
`manifest-and-permissions.md`). `chrome.action.onClicked` only fires when there is **no**
`default_popup`; declaring both means the click opens the popup and your listener never
runs.

A popup gets a few hundred milliseconds of attention, and it starts from nothing every
time. Render immediately from whatever is already in `chrome.storage`, then refresh
asynchronously — a popup that awaits a network call before its first paint reads as broken.
Keep its bundle small for the same reason.

Because the popup dies on blur, never hold in-progress work in it. Hand the work to the
service worker and let the popup subscribe to the result through `chrome.storage.onChanged`
or a port, so reopening it shows the current state.

`chrome.action.openPopup()` is available from Chrome 127 (Chrome 118-126 restricted it to
policy-installed extensions), so it needs a `minimum_chrome_version` or a fallback. For
surfacing something after a background event, a badge plus a notification is still the
more reliable route.

## Side panel

Declaring the panel does not make it openable:

```jsonc
"side_panel": { "default_path": "panel.html" }
```

Add exactly one trigger, and note that the two options are mutually exclusive with a popup:

```js
// Option A: the toolbar icon opens the panel. Requires NO default_popup in the manifest.
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

// Option B: open it from a user gesture elsewhere (a popup button, a context menu).
await chrome.sidePanel.open({ windowId: tab.windowId });
```

The property is `openPanelOnActionClick`. The plausible-looking
`openPanelOnActionIconClick` is not a property, so the call throws a synchronous
`TypeError` that aborts the worker's current turn — and because it happens during
initialisation, the symptom is "nothing in my extension works".

Panels can be per-tab (`chrome.sidePanel.setOptions({ tabId, path })`) or global. Per-tab
panels need their state keyed by tab id, or switching tabs shows the previous tab's data.
The panel keeps running as the user switches tabs, so re-read the active tab on
`chrome.tabs.onActivated` instead of caching it at load.

Opening a panel is not one of the gestures that grant `activeTab`, and a grant made
earlier stays on the tab that was active then rather than following the user, so a panel
that acts on the front tab needs `tabs` plus host permissions.

## Options page

```jsonc
"options_page": "options.html"                              // opens in a tab
"options_ui": { "page": "options.html", "open_in_tab": false }  // embedded dialog
```

Prefer the embedded dialog for a short settings form and a tab for anything with sections.
Save on change rather than behind a Save button — there is no unload event you can trust
in the embedded dialog, so a Save button is a way to lose the user's edits. Ship sensible
defaults from `runtime.onInstalled` so the page never shows empty fields.

## Context menus, commands and omnibox

Create context menus from `runtime.onInstalled`, which is the documented pattern and fires
for both a fresh install and an update:

```js
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: 'save-selection', title: 'Save selection',
                               contexts: ['selection'] });
});
chrome.contextMenus.onClicked.addListener((info, tab) => { /* … */ });
```

Creating the same id twice throws, so create only from `onInstalled` (or call
`removeAll()` first). Narrow `contexts` — a menu item on every right-click anywhere is
noise. A context-menu click is a direct user gesture, so it does grant `activeTab`.

`commands` in the manifest gives keyboard shortcuts; leave `suggested_key` off the
combinations Chrome already owns and expect users to rebind from
`chrome://extensions/shortcuts`. The `_execute_action` reserved command opens the popup
without any listener.

`omnibox` gives a keyword mode. `onInputChanged` fires per keystroke, so debounce before
doing any work, and always call the suggestion callback even when the result set is empty.

A menu-item action that changes something must confirm it — a badge flash, a notification,
or a toast in the page. Silent success reads as failure and the user clicks again.

## Notifications and the badge

The badge is the cheapest feedback channel and survives the worker restarting because it
is browser state, not extension memory. Keep the text to a few characters and set the
background colour explicitly for contrast.

`chrome.notifications.create()` needs a real image at `iconUrl` or it fails with
`Unable to download all specified images`. When no packaged file fits, generate a data URL
with `OffscreenCanvas` in the worker instead of pointing at a file that is not there.

## DevTools panels

```jsonc
"devtools_page": "devtools/devtools.html"
```

```js
// devtools/devtools.js
chrome.devtools.panels.create('My Panel', '', 'devtools/panel/panel.html');
```

The panel path resolves from the **extension root**, not from the directory of the page
calling `create()`. A relative-looking `'panel/panel.html'` from inside `devtools/`
silently produces an empty panel.

A devtools page also disables promise-returning `onMessage` listeners for the whole
extension, so keep to `return true` (see `messaging-and-contexts.md`).

## Injected UI on a page

Mount inside a shadow root on a container you own, so page CSS cannot restyle your UI and
your CSS cannot leak into the page. Give the container one stable id, so a second injection
is detectable, and remove it in the teardown path described in `content-scripts.md`.

Choose position deliberately: an element in the page flow moves with the content, a fixed
overlay needs a `z-index` high enough to beat the site's own overlays but should not be
`2147483647` as a reflex, and an iframe gives full style and event isolation at the cost of
not being able to read the page's DOM.

<!-- sources: chrome-modern-web-guidance, samber-cc-skills, chrome-docs, dot-skills, wxt-docs -->
