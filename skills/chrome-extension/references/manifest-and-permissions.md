# Manifest and the permissions model

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [Minimum viable manifest](#minimum-viable-manifest)
- [Permissions versus host permissions](#permissions-versus-host-permissions)
- [activeTab and its limits](#activetab-and-its-limits)
- [Optional permissions](#optional-permissions)
- [Content security policy](#content-security-policy)
- [Web-accessible resources](#web-accessible-resources)
- [Icons and the action key](#icons-and-the-action-key)
- [Keeping a stable extension id](#keeping-a-stable-extension-id)

## Minimum viable manifest

```jsonc
{
  "manifest_version": 3,
  "name": "Tab Time",
  "version": "1.2.0",                  // 1-4 dot-separated integers, each < 65536
  "description": "Shows how long you spend on each site today.",
  "minimum_chrome_version": "120",     // only when you rely on a newer API
  "permissions": ["storage", "activeTab", "alarms"],
  "host_permissions": [],
  "background": { "service_worker": "sw.js", "type": "module" },
  "action": { "default_popup": "popup.html" },
  "icons": { "16": "icons/16.png", "48": "icons/48.png", "128": "icons/128.png" }
}
```

`"type": "module"` is what lets the worker use `import`; without it a bare `import`
statement is a syntax error at registration time and the worker never starts.

`minimum_chrome_version` is how you depend on a recent API, but it is a bigger commitment
than it looks: the store stops delivering *any* future version of the extension to users
below that number, so they stay frozen on whatever they have — no bug fixes, no security
patches. Raise it deliberately and with a staged rollout, and prefer a runtime capability
check when only one feature needs the newer Chrome.

## Permissions versus host permissions

`permissions` are API capabilities (`storage`, `alarms`, `tabs`, `scripting`,
`declarativeNetRequest`, `notifications`, …). `host_permissions` are origins the extension
may read, script and send credentialed requests to. They are separate keys in Manifest V3
and neither implies the other.

Two consequences people trip over:

- Reading `tab.url` or `tab.title` from a `Tab` object requires the `tabs` permission (or
  a host permission matching that tab). Without it the field is simply `undefined` — no
  error, no warning.
- `cookies`, `webRequest` and similar only do anything when paired with a host permission
  for the origin in question.

Minimise both, and prefer the narrowest pattern that works:
`https://*.example.com/*` over `https://*/*` over `<all_urls>`. This is not hygiene
theatre: the install-time warning text a user sees is derived from the permission set, and
broad host patterns plus sensitive permissions (`tabs`, `cookies`, `history`, `downloads`,
`webRequest`) are documented drivers of longer, more manual store review.

Every permission also needs a specific plain-language justification in the developer
dashboard. See `web-store.md`.

## activeTab and its limits

`activeTab` grants temporary host access to one tab with no install warning at all — the
cheapest way to script a page. Exactly four gestures grant it: executing the action,
executing a context-menu item, executing a `commands` keyboard shortcut, and accepting an
omnibox suggestion. While it holds, the extension may `scripting.executeScript` and
`insertCSS` on that tab (with the `scripting` permission), read its `url`, `title` and
`favIconUrl`, and intercept `webRequest` for its main-frame origin.

The grant is bound to the tab that was active at the moment of invocation, and it survives
same-origin navigation but is revoked on a cross-origin navigation or when the tab closes.

That gives the popup and the side panel opposite answers:

- A popup opened by clicking the toolbar icon **is** the action being executed, so the
  grant already exists and a button inside the popup can use it on that tab.
- Opening a side panel is not one of the four gestures. A panel can only consume a grant
  that some other gesture created, and because the panel stays open while the user
  switches tabs, that grant stays on the original tab rather than following them. A panel
  that must act on whatever tab is in front needs `tabs` plus host permissions, or an
  `optional_host_permissions` request from a button click.

## Optional permissions

```jsonc
"optional_permissions": ["downloads"],
"optional_host_permissions": ["https://*/*"]
```

Declaring a capability as optional keeps it out of the install-time warning and lets the
user grant it when they first use the feature. Request it from a real user gesture:

```js
const granted = await chrome.permissions.request({ origins: ['https://example.com/*'] });
```

The call must be reached with no `await` before it in the gesture's synchronous turn (see
`service-worker.md`). Check with `chrome.permissions.contains()` before using the
capability every time — the user can revoke it from the extension's details page, and
`chrome.permissions.onRemoved` fires when they do.

This is also the migration path away from `<all_urls>`: ship the narrow set, ask for the
wide set on demand.

## Content security policy

The default policy for extension pages is
`script-src 'self'; object-src 'self';`, and the minimum Chrome will accept is
`script-src 'self' 'wasm-unsafe-eval'; object-src 'self';`. **It cannot be relaxed past
that.** Adding `'unsafe-eval'`, `'unsafe-inline'` or a remote origin makes Chrome refuse
the extension at install time with `Insecure CSP value "…" in directive 'script-src'` —
this is a hard failure, not a warning.

So, in every extension page:

- no inline `<script>` blocks and no `onclick=` attributes — external file plus
  `addEventListener`;
- no `eval()`, no `new Function()`, no `setTimeout('string')`;
- no `<script src="https://cdn…">`. That is remotely hosted code, which is separately
  banned by store policy (see `web-store.md`). Bundle the dependency.

`'wasm-unsafe-eval'` is the one addition you may make, and only for WebAssembly.

When you genuinely must evaluate code the user supplied, use a sandboxed page, whose
policy *is* customisable:

```jsonc
"sandbox": { "pages": ["sandbox.html"] }
```

A sandbox page has no extension APIs and no access to non-sandboxed pages; you talk to it
with `postMessage` through an iframe. A `blob:` URL or `iframe.srcdoc` gives you a
separate origin with the same trade-off. Reaching into `iframe.contentDocument` directly
throws a `SecurityError` — the isolation is the point.

## Web-accessible resources

```jsonc
"web_accessible_resources": [{
  "resources": ["bridge.js", "icons/badge.svg"],
  "matches": ["https://shop.example.com/*"]
}]
```

List individual files and narrow `matches`. `"resources": ["*"]` publishes the whole
package to every matched page: any script there can read your code, and probing for a
known resource is how sites fingerprint installed extensions. It is also a prerequisite
for a `declarativeNetRequest` redirect target — a rule cannot redirect to a resource that
is not declared web-accessible, even its own.

## Icons and the action key

Provide real 16, 48 and 128 pixel PNGs at those exact dimensions. One file reused for all
three sizes renders blurry; a path that does not exist makes Chrome fall back to a default
icon with no error. If you cannot produce real files, omit the `icons` key entirely rather
than referencing files that are not there. The same applies to every runtime image path —
`chrome.action.setIcon`, `chrome.notifications.create`'s `iconUrl`, context-menu icons —
where a missing file surfaces as `Unable to download all specified images`.

`chrome.action.*` requires the `action` key to be present in the manifest, even as `{}`.
Without it, `chrome.action` is `undefined` and the first call is a `TypeError` that aborts
the worker's current turn.

## Keeping a stable extension id

The id is derived from the packaging key, so an unpacked build and the published build
have different ids. Anything bound to the id — an OAuth client, a server allow-list, a
`chrome-extension://` URL in a test — breaks between the two.

Pin it by adding the public `"key"` field from a packed build to `manifest.json`. Keep the
private key out of the repository, and remember that after publishing you must update
whatever was bound to the development id with the store-assigned one.

<!-- sources: chrome-modern-web-guidance, samber-cc-skills, chrome-docs, quangpl-ext -->
