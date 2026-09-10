# Network requests and declarativeNetRequest

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [Where a request should originate](#where-a-request-should-originate)
- [The relay pattern](#the-relay-pattern)
- [declarativeNetRequest instead of blocking webRequest](#declarativenetrequest-instead-of-blocking-webrequest)
- [Rule limits](#rule-limits)
- [Header modification](#header-modification)
- [Debugging rules](#debugging-rules)
- [What webRequest is still for](#what-webrequest-is-still-for)

## Where a request should originate

| Origin of the call | Behaviour |
|---|---|
| Service worker | Extension origin. Needs `host_permissions` for the target; not subject to any page's CSP |
| Popup, options page, side panel, offscreen document | Same as the worker |
| Content script | The **page's** origin: the page's CSP `connect-src` applies, CORS applies, and the page's cookies are attached |

The asymmetry in the last row is the source of most "it works in the popup but not in the
content script" reports. A content-script `fetch()` to your own API is blocked by a strict
site CSP no matter what permissions the extension holds.

## The relay pattern

Move the request to the worker and pass the result back:

```js
// content script
const result = await chrome.runtime.sendMessage({ type: 'API', path: '/coupons' });

// service worker
const ALLOWED = 'https://api.example.com';
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== 'API') return;
  const url = new URL(msg.path, ALLOWED);
  if (url.origin !== ALLOWED) { sendResponse({ error: 'blocked' }); return true; }
  fetch(url).then((r) => r.text()).then((body) => sendResponse({ body }),
                                         (e) => sendResponse({ error: e.message }));
  return true;
});
```

Validate the destination in the worker. A relay that forwards any URL the content script
hands it turns a compromised page into a proxy with your extension's host permissions —
that is a real privilege escalation, not a theoretical one. Build the URL against a fixed
base and compare origins; never string-concatenate.

Note the worker's own limits apply: a response taking longer than 30 seconds kills the
worker mid-request (see `service-worker.md`), so set your own timeout with `AbortSignal`
and treat the failure as expected.

## declarativeNetRequest instead of blocking webRequest

`webRequestBlocking` is not available to Manifest V3 extensions. Blocking, redirecting and
header rewriting are declarative: you ship rules, Chrome evaluates them, and your code
never sees the request. That is the point — the rules work while the worker is asleep.

```jsonc
// manifest.json
"permissions": ["declarativeNetRequest"],
"declarative_net_request": {
  "rule_resources": [{ "id": "ads", "enabled": true, "path": "rules/ads.json" }]
}
```

```jsonc
// rules/ads.json
[{
  "id": 1,                     // unique within the ruleset, >= 1
  "priority": 1,
  "action": { "type": "block" },
  "condition": { "urlFilter": "||tracker.example.com", "resourceTypes": ["script", "xmlhttprequest"] }
}]
```

Three rule sets with different trade-offs:

- **Static** rules ship in the package. Cheapest and reviewable — use them for anything
  known at build time. The `declarativeNetRequest` permission itself carries implicit
  access for `block`, `allow` and `allowAllRequests` actions, so those need no host
  permission at all.
- **Dynamic** rules persist across sessions and are set with `updateDynamicRules()`. Use
  them for user-configured filters.
- **Session** rules live until the browser closes, set with `updateSessionRules()`. Use
  them for temporary per-tab behaviour.

Prefer `declarativeNetRequestWithHostAccess` over the broad `declarativeNetRequest`
permission when your rules only need to act on hosts the user already granted; it avoids
the extra install warning. Redirect and header actions need host access to both the
initiator and the request URL regardless.

A redirect target inside the extension must be listed in `web_accessible_resources`, or
the rule errors out — even when the extension owns the resource.

## Rule limits

| Limit | Value |
|---|---|
| Static rulesets declared in the manifest | 100 |
| Static rulesets enabled at once | 50 |
| Static rules guaranteed across enabled rulesets | 30,000 |
| Session rules | 5,000 |
| Dynamic rules, "unsafe" | 5,000 |
| Dynamic rules, safe (Chrome 121+) | 30,000, with unsafe ones counting inside it |
| Regex rules, per type | 1,000, each under 2 KB compiled |

The static guarantee is a floor shared with every other installed extension; call
`getAvailableStaticRuleCount()` at runtime rather than assuming headroom. A regex that
compiles over 2 KB is ignored with a warning naming the rule id, so an over-clever
`regexFilter` silently does nothing. Reach for `urlFilter` first — it is both faster and
not subject to the regex cap.

## Header modification

`modifyHeaders` actions need host access. `append` is only supported for a fixed list of
request headers (`accept`, `accept-encoding`, `accept-language`, `cache-control`,
`cookie`, `if-match`, …) and a fixed list of response headers; anything else must use
`set` or `remove`. Trying to append an unsupported header fails rule registration rather
than being ignored at request time.

## Debugging rules

A declarative rule gives no feedback by design, so add the observability yourself:

- `chrome.declarativeNetRequest.getMatchedRules()` reports which rules matched, per tab.
- The `declarativeNetRequestFeedback` permission plus an unpacked build logs matches to the
  console.
- `updateDynamicRules()` rejects the whole batch on one malformed rule; the rejection
  message names the offending id.

Rules only apply to requests that reach the network stack. A response produced by a page's
own service worker or served from `CacheStorage` is not affected; a `fetch()` made inside
such a worker is.

## What webRequest is still for

Non-blocking observation. `chrome.webRequest.onCompleted`, `onErrorOccurred` and friends
still fire, with host permissions, and are useful for telemetry or for noticing that a
request happened. If all you kept was observation, say so in the store justification —
`webRequest` reads as a heavy permission and reviewers will look for the blocking use that
is no longer possible.

<!-- sources: chrome-docs, samber-cc-skills, dot-skills, quangpl-ext -->
