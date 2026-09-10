# Chrome Web Store submission and review

Verified against: Chrome 148 documentation on developer.chrome.com.

## Contents

- [What the package contains](#what-the-package-contains)
- [Remotely hosted code](#remotely-hosted-code)
- [Permission justifications](#permission-justifications)
- [Single purpose](#single-purpose)
- [Privacy disclosure](#privacy-disclosure)
- [Listing copy](#listing-copy)
- [What lengthens review](#what-lengthens-review)
- [Handling a rejection](#handling-a-rejection)
- [Updates](#updates)

## What the package contains

Zip the build output, not the repository. Excluding `.git/`, `node_modules/`, `.env`,
source maps and test fixtures is not just hygiene: reviewers assess the code they receive,
and a package full of dependencies is slower to review and more likely to contain
something that trips a policy check.

Obfuscation is disallowed outright. Minification is allowed, but the documented preference
is to submit code as authored where that is practical, because unreadable code lengthens
review. A build that minifies but keeps structure and ships no source maps is the
comfortable middle.

Version numbers must increase monotonically; the store rejects a re-upload of an existing
version. Keep the manifest `version` as the single source of truth.

## Remotely hosted code

Anything the browser executes that did not come from the package is remotely hosted code:
a `<script src="https://…">`, a dynamic `import()` of an http URL, a `fetch` whose result
is evaluated, WebAssembly pulled at runtime. JSON, CSS and data are fine; code is not.

A rejection for this arrives under the label **Blue Argon**. To find the cause, search the
*built* package — not the source — for `http://` and `https://`, since the offender is
usually inside a dependency rather than your own file. A first-party Google library is not
an exception: Firebase Auth was a well-known case, and the fix was configuring the library
to stop, not appealing.

If a dependency insists on fetching code, the options are: configure it not to, replace it,
or vendor the specific build that does not. There is no manifest key that permits it, and
relaxing the CSP is impossible anyway (see `manifest-and-permissions.md`).

## Permission justifications

Every `permissions` entry and every `host_permissions` pattern needs its own justification
field in the dashboard, in plain language a non-engineer can check against the code.

```
tabs           - We read the URL of the active tab to look up coupon codes for that
                 shop. We do not read tab contents and do not store URLs.
host_permissions
https://*.shop.example.com/*
               - The extension inserts the coupon banner into product pages on this
                 retailer's sites.
```

"Needed for the extension to work" is a rejection. So is a justification that describes a
narrower use than the code performs — reviewers compare the two, and a mismatch is worse
than an honest broad justification.

If a permission is only there for a feature you removed, delete the permission. That is
the cheapest review-time win available.

## Single purpose

An extension must have one narrow purpose, stated in the listing and reflected in the code.
A bundle of unrelated features gets rejected even when each feature is individually fine.
When a project genuinely has two purposes, ship two extensions.

This also constrains the permission set: a coupon finder does not need `history`, and a
reviewer asking "why does a coupon finder read browsing history" is a rejection in
progress.

## Privacy disclosure

The data-use form in the dashboard must match what the code does and what the privacy
policy says. Three consistency checks before submitting:

1. Every `fetch` destination in the package is accounted for by a disclosed data flow.
2. The privacy policy URL is live and reachable, and describes this extension.
3. What you store locally versus transmit is stated correctly — "data stays on your
   device" is a claim reviewers can test.

Handling authentication tokens, page content or anything a user would call personal
requires the disclosure regardless of whether it leaves the device.

## Listing copy

Write function, not feeling. "Enjoy searching again" is the kind of vague copy that gets
rejected; "Highlights your search terms on any page and saves the highlights to a local
list" is checkable against the code, which is exactly what the reviewer needs.

Cut implementation detail from user-facing text — a `MutationObserver`, a service worker
or `chrome.storage.sync` means nothing to a user and reads as filler. Say what the user
gets: settings sync across devices, works without slowing the page.

Assets: at least one screenshot at 1280×800 or 640×400, and a 128 px icon. Screenshots
showing UI that is not in the build are a rejection.

## What lengthens review

Most reviews finish in a few days; some take weeks. Documented factors that add time:

- broad host permissions — `<all_urls>`, `*://*/*`, `https://*/*`;
- sensitive permissions, alone (`tabs`, `downloads`) or in combination with host access
  (`cookies`, `webRequest`);
- a large or hard-to-review code base;
- being a new developer or a new extension;
- a significant code change relative to the previous version;
- a prior rejection or warning on the item.

None of these are faults, but each is a reason to submit the narrow permission set and
request the rest through `optional_permissions` at runtime.

If an item has been pending for more than three weeks with no significant change, the
documented step is to contact developer support rather than resubmit.

## Handling a rejection

Read which policy was cited and fix that, in the code, before resubmitting. Resubmitting
with only a reworded justification is how items accumulate a rejection history, which
itself slows later reviews.

Published items are also re-reviewed periodically and independently of any submission. A
minor violation produces a warning with a deadline; a serious one is an immediate takedown
with notice; malware is a takedown without notice. So a passing review is not permanent
approval — a policy change can make a shipped extension non-compliant.

## Updates

An update goes through the same review as a new submission. Two habits that keep this
cheap: never add a permission and a feature in the same submission if you can help it
(the permission is what triggers scrutiny, and separating them makes the diff obvious),
and keep a changelog entry per version that a reviewer could read alongside the diff.

Handle the update on the client side too: `runtime.onInstalled` with
`reason === 'update'` is where storage migrations run and where context menus, dynamic
content scripts and user scripts must be re-registered (see `service-worker.md`), and
already-injected content scripts from the previous version are orphaned at that moment
(see `content-scripts.md`).

<!-- sources: chrome-modern-web-guidance, chrome-docs, samber-cc-skills, quangpl-ext -->
