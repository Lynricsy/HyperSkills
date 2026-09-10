# Testing and debugging an extension

Verified against: WXT v0.21.4; Chrome 148 documentation on developer.chrome.com.

## Contents

- [What to test at which layer](#what-to-test-at-which-layer)
- [Unit tests](#unit-tests)
- [End-to-end tests](#end-to-end-tests)
- [Headless in CI](#headless-in-ci)
- [Where the logs are](#where-the-logs-are)
- [Reproducing lifecycle bugs](#reproducing-lifecycle-bugs)
- [Symptom to cause](#symptom-to-cause)

## What to test at which layer

| Layer | Runner | Worth testing |
|---|---|---|
| Unit | Vitest (or Jest in an existing suite) with a fake `chrome`/`browser` | Message routing, storage schema migrations, rule generation, parsing, anything with branches |
| Component | The same runner plus a DOM environment | Popup, options and side-panel components, as ordinary UI tests |
| End-to-end | Playwright with a real Chrome and the built extension | That the pieces are wired together at all: manifest loads, worker registers, content script injects, the surfaces open |

Do not write end-to-end tests for logic a unit test can cover — an extension E2E run
costs seconds per case and is the flakiest thing in the suite. Do write at least one that
loads the built extension, because most extension breakage is wiring: a bad manifest path,
a missing permission, a worker that throws on registration.

Skip tests entirely for manifest content (assert it by loading the build) and for
`chrome.*` call forwarding (that asserts the fake).

## Unit tests

In a WXT project, use the provided plugin and its in-memory browser:

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';
export default defineConfig({ plugins: [WxtVitest()] });
```

```ts
import { fakeBrowser } from 'wxt/testing/fake-browser';

beforeEach(() => fakeBrowser.reset());

it('migrates v1 hosts', async () => {
  await fakeBrowser.storage.local.set({ ignoredHosts: ['a.example'] });
  expect(await ignoredHosts.getValue()).toEqual([{ host: 'a.example', mutedUntil: 0 }]);
});
```

The fake implements `browser.storage` in memory, so storage-backed code needs no mocking at
all — which matters, because hand-written storage mocks are where these suites usually go
wrong (a `jest.fn()` that returns a fixed object cannot catch a read-modify-write bug).
Reset it between tests or state leaks across cases.

Outside WXT, `@webext-core/fake-browser` gives the same object standalone, and
`jest-chrome` is the equivalent for an existing Jest suite:

```ts
// jest.setup.ts
import chrome from 'jest-chrome';
Object.assign(globalThis, { chrome });
```

With either, assert on the effect (what ended up in storage, which rules were registered)
rather than on the fact that a `chrome.*` function was called.

## End-to-end tests

Extensions require a persistent context, and the path you pass is the **build output**, not
the source tree.

```ts
import { test as base, chromium, type BrowserContext } from '@playwright/test';
import path from 'node:path';

const EXT = path.resolve('.output/chrome-mv3');   // WXT output; adjust for other builders

export const test = base.extend<{ context: BrowserContext; extensionId: string }>({
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      channel: 'chromium',           // required: see the headless note below
      args: [`--disable-extensions-except=${EXT}`, `--load-extension=${EXT}`],
    });
    await use(context);
    await context.close();
  },
  extensionId: async ({ context }, use) => {
    let [worker] = context.serviceWorkers();
    worker ??= await context.waitForEvent('serviceworker');
    await use(worker.url().split('/')[2]);
  },
});
```

Extension pages are ordinary pages at `chrome-extension://<id>/popup.html`, so navigate to
them directly. `chrome.action.openPopup()` can open the real popup when you need to test
that path; otherwise opening the popup URL in a tab is simpler, and worth designing for by
letting the popup accept a tab id as a URL parameter instead of always reading the active
tab.

Pin the extension id with the manifest `key` field (see `manifest-and-permissions.md`) if
tests hard-code URLs or a server needs to allow-list the origin.

With Puppeteer the same launch arguments apply and the extension id comes from the
`service_worker` target in `browser.targets()`. Keep whichever one the project already
uses; do not add the second.

## Headless in CI

Extensions do load headlessly, but only in Chrome's new headless mode: start Chrome with
`--headless=new`, because the old headless mode cannot load an extension at all. That is
the origin of the widespread claim that extensions cannot be tested headlessly.

Under Playwright there are two further constraints. Extensions only work in a persistent
context, and Google Chrome and Microsoft Edge have removed the side-loading command-line
flags — so use the bundled Chromium with `channel: 'chromium'`, which is also what allows
headless runs. Playwright additionally keeps the same `Worker` handle across a service
worker's idle suspension and restart, so no second `serviceworker` event arrives and
`evaluate()` calls made during the restart window stall and then resume.

Run extension E2E serially. Two persistent contexts fighting over the same profile
directory produce failures that look like application bugs.

## Where the logs are

Each context logs somewhere different, which is why "there is no error" is usually "you
are looking at the wrong console":

| Context | Where |
|---|---|
| Service worker | `chrome://extensions` → the extension → "service worker" link |
| Content script | The page's own DevTools console (select the extension's context in the top-left dropdown to see its scope) |
| Popup | Right-click the popup → Inspect; it closes on blur, so open it before triggering |
| Options, side panel | Inspect that page directly |
| Offscreen document | `chrome://extensions` with developer mode, or via the worker |

`chrome://extensions` also shows manifest and registration errors under "Errors", which is
where a worker that throws before its first listener shows up.

## Reproducing lifecycle bugs

An open DevTools session keeps the service worker alive (`chrome.debugger` extends its
lifetime), so lifecycle bugs disappear exactly when you go looking for them. To reproduce:

1. Close the worker's DevTools.
2. Stop the worker deliberately — the "service worker" entry in `chrome://extensions`, or
   `chrome://serviceworker-internals`.
3. Trigger the event that should work and see whether it does.

Test the reload path too: hit reload on `chrome://extensions` with a page already open and
confirm the injected UI tears itself down instead of throwing
`Extension context invalidated` on every mutation.

## Symptom to cause

| Symptom | Look at first |
|---|---|
| Nothing in the extension works, no error | The worker threw during its synchronous pass — a `TypeError` from a misspelled API or a missing manifest key (`action`, `side_panel`) |
| A handler works once, then never again | Listener registered after an `await` or inside `onInstalled`; see `service-worker.md` |
| `sendMessage` resolves with `undefined` | Missing `return true`, or no listener recognised the message type |
| Works on first page load, dies after in-app navigation | Single-page-app route change; see `content-scripts.md` |
| Works unpacked, fails once installed | Alarm period under the 30-second floor, or an extension id bound to the unpacked build |
| A field on a `Tab` is `undefined` | Missing `tabs` permission or host permission |
| Rules have no effect | A regex rule over the 2 KB compiled limit, or a redirect target not in `web_accessible_resources`; see `network-and-dnr.md` |

<!-- sources: quangpl-ext, wxt-docs, playwright-docs, chrome-docs, samber-cc-skills, chrome-modern-web-guidance, chrome-samples -->
