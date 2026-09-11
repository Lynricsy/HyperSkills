---
name: chrome-extension
description: "Guides Chrome and Chromium browser extension work end to end: Manifest V3 manifests, the permissions and host-permissions model, activeTab and optional permissions, service worker lifecycle and event-driven design, content scripts across the isolated and MAIN worlds, injection timing and single-page-app re-injection, chrome.runtime messaging and ports, chrome.storage areas with their quotas and schema migrations, declarativeNetRequest, the side panel, action, offscreen and DevTools surfaces, WXT project structure and cross-browser builds, unit tests against a fake browser plus Playwright end-to-end runs, extension CSP and the remotely-hosted-code ban, and Chrome Web Store packaging, permission justifications and review. Use when creating, reviewing, debugging or shipping an extension, when reading manifest.json, wxt.config.ts or a background service worker, or when a chrome.* API fails silently. Do not use for driving a browser to test an ordinary website, or for the visual and UX design of pages."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# chrome-extension

## Scope

Covers browser extensions built on Manifest V3 for Chrome and other Chromium browsers:
the manifest and its permission model, the service worker and its lifecycle, content
scripts and the worlds they run in, message passing between contexts, `chrome.storage`
and state that must survive termination, request filtering with `declarativeNetRequest`,
the user-facing surfaces (action and popup, side panel, options, context menus,
notifications, DevTools panels, injected UI), project tooling with WXT including
cross-browser output, testing and debugging each context, and Chrome Web Store packaging,
policy and review.

Not covered: driving a browser to test an ordinary website — use the `web-testing` skill;
this skill only covers Playwright and Puppeteer
insofar as they load an extension. Visual and UX design of the popup or injected UI —
use the `frontend-design` skill; this skill covers which surface to use and how to
isolate it, not how it should look. React component structure and hooks — use the `react`
skill. Type-layer modelling, `tsconfig` and build-type questions — use the `typescript`
skill. Also not covered: Firefox-only and Safari-only add-on work beyond what a
cross-browser WXT build handles, native messaging host deployment, and extension
monetisation.

Paths below are relative to this skill's directory.

## Core rules

1. Read `manifest.json` (or `wxt.config.ts` plus `entrypoints/`) before anything else.
   Which permissions, surfaces and content-script matches exist decides what every
   suggestion below can legally do.
2. Manifest V3 is the only form Chrome runs. A V2 codebase is a rewrite of the plumbing,
   not a compatibility flag, and no `chrome.browserAction`, `background.scripts` or
   blocking `webRequest` should appear in new code.
3. Treat the contexts as separate processes that share no memory: worker, content script,
   page realm, popup, side panel, offscreen document. Almost every inexplicable extension
   bug is code assuming two of them share state.
4. Register every `chrome.*` event listener in the worker's top-level synchronous pass.
   A listener added after an `await`, inside a callback, or inside `runtime.onInstalled`
   does not exist when the event that restarts the worker is dispatched, and the event is
   lost with no error.
5. Keep no state in worker module scope that the user would notice losing. The worker is
   terminated after 30 seconds of inactivity, after any single request exceeding
   5 minutes, and when a `fetch()` response takes over 30 seconds.
6. `localStorage` and `sessionStorage` do not exist in a service worker, so a call is a
   `TypeError` rather than a style problem. Use `chrome.storage`, IndexedDB or
   `CacheStorage`.
7. Schedule with `chrome.alarms`, not `setTimeout`/`setInterval`, and never below the
   30-second floor: `periodInMinutes` under `0.5` is refused with a warning. The clamp
   does not apply to unpacked builds, so a too-frequent alarm works in development and
   stops working once installed.
8. Never keep the worker alive artificially. Split long work into alarm-driven steps with
   a persisted cursor; a keep-alive ping hides the bug instead of fixing it.
9. Return a literal `true` from a `runtime.onMessage` listener that answers
   asynchronously, and `return` early from one that does not recognise the message. An
   `async` listener returns a `Promise`, which is truthy but not `true`, so the sender's
   `sendMessage` resolves with `undefined` and nothing reports an error.
10. A content script cannot see page JavaScript: its world is isolated and only the DOM is
    shared. To read a page global, either declare `world: "MAIN"` (which loses every
    `chrome.*` API) or inject a small page-world bridge and post the value back.
11. Load an injected script through `chrome.runtime.getURL()` and list it in
    `web_accessible_resources`. A bare relative `src` resolves against the page's origin
    and 404s.
12. Validate every `window` `message` event on `event.source`, `event.origin` and a
    channel marker before forwarding it into the extension, and validate the destination
    of any request the worker relays for a content script. Both are the paths by which a
    compromised page borrows your host permissions.
13. Use `document_idle` unless the script must run before page scripts. At
    `document_start` there is no `document.body`, so DOM queries return `null`.
14. Declare content scripts statically in the manifest for URL patterns known at build
    time; use `chrome.scripting` only when the patterns are runtime-dependent or the
    injection follows a user action.
15. Re-inject on single-page-app route changes and tear down on context invalidation.
    A client-side navigation neither re-runs nor unloads the script, and an extension
    reload orphans it so every `chrome.runtime` call throws until it checks
    `chrome.runtime?.id`.
16. Pick the storage area by what must survive what: `session` for hot state that outlives
    a worker restart but not the browser session, `local` for user data, `sync` for
    preferences (about 100 KB total, 8 KB per item). `session` is not exposed to content
    scripts until the worker calls `setAccessLevel`.
17. Version stored shapes and migrate forward from `runtime.onInstalled` with
    `reason === 'update'`. A user who skipped four releases still holds the oldest shape.
18. Filter and rewrite requests with `declarativeNetRequest`; `webRequestBlocking` is
    unavailable in Manifest V3, and declarative rules keep working while the worker
    sleeps.
19. Ask for the narrowest permissions that work and move the rest to
    `optional_permissions`. Broad host patterns and sensitive permissions drive both the
    install-time warning and the length of store review.
20. Exactly four gestures grant `activeTab`: executing the action, a context-menu item, a
    `commands` shortcut, an omnibox suggestion — and the grant stays on the tab that was
    active then. A popup opened from the toolbar therefore already has it; a side panel,
    which is not one of those gestures and stays open across tab switches, does not, so a
    panel acting on the front tab needs `tabs` plus host permissions.
21. The `extension_pages` CSP cannot be relaxed past
    `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'`. Adding `'unsafe-eval'` or
    a remote origin makes Chrome refuse to install the extension. Evaluate untrusted code
    in a sandboxed page, a `blob:` iframe or `srcdoc` instead.
22. Ship every line of executable code inside the package. A CDN `<script>`, an
    `import()` of an http URL, or a dependency that fetches code is remotely hosted code:
    a store rejection labelled Blue Argon, and usually hiding inside a dependency rather
    than your own file.
23. Declaring a surface does not activate it. `side_panel` needs an explicit open trigger,
    and `chrome.action.*` is `undefined` unless the manifest carries an `action` key, even
    an empty one. Both failures present as "nothing in my extension works", because the
    `TypeError` aborts the worker's turn.
24. Reference only image files that exist, at the declared pixel sizes. A missing icon
    path falls back silently, while `chrome.notifications` fails with
    `Unable to download all specified images`; generate a data URL with `OffscreenCanvas`
    when no file fits.
25. Reproduce lifecycle bugs with the worker's DevTools closed. An open debugger session
    extends the worker's lifetime, so the bug disappears exactly while you are looking
    for it.

## Workflows

### build-extension

- [ ] Decide the surface from the interaction, not from habit: popup for one glance and one
      action (it dies on blur), side panel when the user works alongside the page,
      injected UI when the feature belongs to the page.
- [ ] Pick the skeleton — WXT for anything with TypeScript, a framework UI or a second
      browser; raw files only for a single-file experiment. Keep an existing
      Vite + CRXJS setup rather than converting it.
- [ ] Write the manifest with the narrowest permission set that works, `activeTab` before
      host permissions, and everything else under `optional_permissions`.
- [ ] Implement the worker: listeners at the top level, state in `chrome.storage`,
      scheduling through `chrome.alarms`.
- [ ] Add content scripts only if the feature needs the page. Static declaration, narrow
      `matches`, `document_idle`, teardown on context invalidation.
- [ ] Wire the channels: one-shot `sendMessage` for request/response, a port for streams,
      `chrome.storage.onChanged` for anything several surfaces must all see.
- [ ] Build the UI last, rendering immediately from cached storage.
- [ ] **Gate:** load the build unpacked, then stop the service worker from
      `chrome://extensions` and exercise every entry point again; `chrome://extensions`
      shows no errors.

### review

- [ ] Establish the diff scope and read `manifest.json` first — a permission or CSP change
      outranks everything else in the diff.
- [ ] Walk the Core rules in order; they are ordered by how often each one is the actual
      defect.
- [ ] Check the worker for module-scope state, late listener registration, timers, and
      keep-alive tricks.
- [ ] Check content scripts for isolated-world assumptions, `document_start` DOM access,
      missing teardown, and unvalidated `postMessage` handlers.
- [ ] Check every async `onMessage` listener for the literal `return true` and for an
      early `return` on unrecognised messages.
- [ ] Check each surface against the access its code actually needs, per surface rather
      than per manifest key: which `chrome.*` namespace requires which manifest key, which
      field is `undefined` without `tabs`, and whether the surface can reach the tab it
      operates on — `activeTab` reaches the popup's tab but not a side panel's.
- [ ] Check the security surface separately: relay endpoint validation,
      `web_accessible_resources` breadth, CSP additions, anything executing a string.
- [ ] Report with the Output format below.
- [ ] **Gate:** every finding carries `path:line`, one line of reasoning, and a concrete
      fix.

### debug-silent-failure

- [ ] Name the context first — worker, content script, popup, offscreen — and open *its*
      console; "there is no error" is usually the wrong console. See
      `references/testing-and-debugging.md` for where each one lives.
- [ ] Check `chrome://extensions` → Errors for a manifest or registration failure before
      reading any application code.
- [ ] If the whole extension is dead, look for a synchronous `TypeError` in the worker's
      first pass: a misspelled API property or a `chrome.*` namespace that is `undefined`
      because its manifest key is missing.
- [ ] If a handler works once and then never again, close DevTools, stop the worker, and
      retry — that is the late-registration signature.
- [ ] If a value is `undefined` with no error, suspect a missing permission
      (`tab.url` without `tabs`) before suspecting your own code.
- [ ] If it works unpacked but not when installed, check the alarm floor and anything bound
      to the extension id.
- [ ] **Gate:** the failure is reproduced deliberately — worker stopped, or extension
      reloaded with the page still open — and then does not reproduce after the fix.

### harden-permissions

- [ ] List every permission and host pattern next to the code that uses it; delete the ones
      with no caller.
- [ ] Replace `<all_urls>` and `*://*/*` with the specific origins the feature needs, and
      move anything genuinely open-ended to `optional_host_permissions` requested from a
      user gesture.
- [ ] Replace blocking `webRequest` with `declarativeNetRequest`, preferring
      `declarativeNetRequestWithHostAccess` and static rulesets.
- [ ] Narrow `web_accessible_resources` from a wildcard to named files with narrow
      `matches`.
- [ ] Remove every CSP relaxation and move code evaluation into a sandboxed page.
- [ ] Write one plain-language justification per remaining permission, checkable against
      the code.
- [ ] **Gate:** the extension still passes the `build-extension` gate with the reduced set,
      and each remaining permission has a justification a non-engineer could verify.

### migrate-to-wxt

- [ ] Get the current build green and loading unpacked first; migrating a broken build
      hides which change broke it.
- [ ] Scaffold WXT alongside the existing source, then move one entrypoint at a time into
      `entrypoints/`, starting with the background worker.
- [ ] Move static manifest keys into `wxt.config.ts` and delete `manifest.json`; the
      manifest is generated from the config plus the entrypoint files.
- [ ] Switch `chrome.*` to the `browser` object from `#imports`, and runtime helpers to
      `#imports` rather than the pre-0.20 `wxt/storage` and `wxt/client` paths.
- [ ] Adopt `ctx` in content scripts so listeners, intervals and injected UI unregister on
      invalidation, and delete the hand-written teardown it replaces.
- [ ] Convert storage access to `storage.defineItem` with `version` and `migrations`,
      keeping the existing keys and area prefixes so installed users migrate rather than
      reset.
- [ ] **Gate:** `npm run build` then load `.output/chrome-mv3` unpacked and pass the
      `build-extension` gate; an existing user's stored data still reads correctly.

### prepare-for-store

- [ ] Confirm one narrow purpose, stated the same way in the listing and the code.
- [ ] Search the *built* package for `http://` and `https://` and remove every path that
      executes fetched code, dependencies included.
- [ ] Write a justification per permission and per host pattern, and delete permissions
      whose feature is gone.
- [ ] Make the data-use disclosure, the privacy policy and the actual network destinations
      agree.
- [ ] Zip the build output only — no `.git/`, `node_modules/`, `.env`, source maps or test
      fixtures — with a version above the published one.
- [ ] Write listing copy in terms of what the user gets, with no implementation detail, and
      screenshots that match the build.
- [ ] **Gate:** the zip loads unpacked from a fresh extraction and passes the
      `build-extension` gate; see `references/web-store.md` for the review-time factors to
      expect.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Service worker | Lifecycle, listener registration, alarms, offscreen documents, gesture-bound APIs | `references/service-worker.md` |
| Content scripts | Isolated versus MAIN world, injection timing, page bridges, SPA re-injection, teardown, user scripts | `references/content-scripts.md` |
| Messaging | Choosing a channel, async replies, ports, pushing to a popup, the errors each mistake produces | `references/messaging-and-contexts.md` |
| Manifest and permissions | Manifest keys, permission minimisation, `activeTab`, optional permissions, CSP, web-accessible resources, stable extension id | `references/manifest-and-permissions.md` |
| Storage and state | Choosing an area, quotas, content-script exposure, schema migrations, write patterns | `references/storage-and-state.md` |
| Network and filtering | Where a request should originate, the relay pattern, `declarativeNetRequest` rules and limits, header modification | `references/network-and-dnr.md` |
| UI surfaces | Popup, side panel, options, context menus, commands, omnibox, notifications, DevTools panels, injected UI | `references/ui-surfaces.md` |
| Project and WXT | Skeleton choice, WXT entrypoints and storage, cross-browser builds, bundling constraints, inheriting a V2 codebase | `references/wxt-and-tooling.md` |
| Testing and debugging | Which layer to test, fake-browser unit tests, Playwright E2E, headless CI, where each console lives, symptom-to-cause table | `references/testing-and-debugging.md` |
| Chrome Web Store | Packaging, remotely hosted code, permission justifications, privacy disclosure, listing copy, review and rejections | `references/web-store.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
src/background.js
  L14 blocking - localStorage does not exist in a service worker; this line throws a
       TypeError and aborts the worker's first pass, so no listener below it registers.
       before: const raw = localStorage.getItem('secondsPerHost');
       after:  const { secondsPerHost = {} } = await chrome.storage.local.get('secondsPerHost');
  L22 blocking - tabs.onActivated is registered after an await, so it does not exist when
       a restarted worker is handed the queued event. Register at the top level and read
       settings inside the handler.
  L47 important - alarms.create with periodInMinutes 0.1 is below the 30-second floor;
       Chrome refuses it with a warning. Unpacked builds have no clamp, which is why this
       looks fine in development.
  L52 minor - the onMessage listener does not return early for unknown types, so it
       answers messages meant for other listeners.

src/manifest.json
  ✓ pass
```

Severities: `blocking` (does not load, does not run, data loss, store rejection),
`important` (silent failure, lost events, over-broad permission, security exposure),
`minor` (naming, ordering, dead permission with no caller). End with a one-line verdict:
ship, ship after blocking fixes, or rework.

## Environment

Chrome or another Chromium browser with developer mode enabled, and Node.js for any
build tooling. Commands used by the workflows:

```bash
npm create wxt@latest                    # scaffold a WXT project
npm run dev                              # WXT dev server with reload
npm run build                            # produces .output/chrome-mv3
npm run zip -- --browser chrome          # store-ready package
npx playwright test                      # end-to-end suite
```

Loading unpacked, stopping the service worker, and reading each context's console are all
manual steps in the browser; `chrome://extensions` with developer mode on is the entry
point for every one of them. End-to-end runs on a machine with no display need Chrome
started with `--headless=new`; the old headless mode cannot load an extension at all.
