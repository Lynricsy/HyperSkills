# Project setup, WXT and inherited codebases

Verified against: WXT v0.21.4; Chrome 148 documentation on developer.chrome.com.

## Contents

- [Choosing a skeleton](#choosing-a-skeleton)
- [WXT layout](#wxt-layout)
- [WXT entrypoint definitions](#wxt-entrypoint-definitions)
- [WXT storage](#wxt-storage)
- [WXT messaging](#wxt-messaging)
- [Cross-browser builds](#cross-browser-builds)
- [Bundling rules that are not negotiable](#bundling-rules-that-are-not-negotiable)
- [Inheriting a Manifest V2 codebase](#inheriting-a-manifest-v2-codebase)

## Choosing a skeleton

| Setup | Pick when | What you give up |
|---|---|---|
| Raw files, loaded unpacked | A single-file experiment, no npm imports | No TypeScript, no bundler, manual reloads |
| WXT | Anything real: TypeScript, a framework UI, more than one browser | A build step and WXT's file conventions |

Default to WXT. It generates the manifest from `wxt.config.ts` plus the entrypoint files,
gives HMR for extension pages and auto-reload for content scripts, and produces per-browser
zips. Use raw files only when the whole extension is small enough that a build step costs
more than it saves.

If a project already uses Vite with `@crxjs/vite-plugin`, keep it — it solves the same
problem and switching mid-project buys nothing. Do not introduce a third build path
alongside either of them.

```bash
npm create wxt@latest                       # interactive
npm create wxt@latest -- --template react-ts
```

## WXT layout

```
entrypoints/
  background.ts          # the service worker
  content.ts             # one content script; or content/index.ts for a directory
  popup/index.html       # + main.tsx alongside it
  options/index.html
  sidepanel/index.html
components/              # auto-imported
utils/                   # auto-imported
public/                  # copied verbatim; icons live here
wxt.config.ts
```

File names in `entrypoints/` are the manifest. `background.ts` becomes
`background.service_worker`; `foo.content.ts` becomes a content script; `popup/index.html`
becomes `action.default_popup`. There is no manifest file to edit — permissions and other
static keys go in `wxt.config.ts`:

```ts
export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    permissions: ['storage', 'alarms'],
    host_permissions: ['https://shop.example.com/*'],
  },
});
```

Build output is `.output/chrome-mv3/` (and `.output/firefox-mv2/` and so on). That
directory, not the repository, is what you load unpacked and what you zip.

```bash
npm run dev                     # HMR + auto-reload
npm run build                   # current target
npm run zip -- --browser firefox
```

## WXT entrypoint definitions

Runtime code goes **inside** `main()`. WXT imports each entrypoint file at build time to
read its options, so top-level side effects run during the build as well as at runtime.

```ts
// entrypoints/background.ts
export default defineBackground({
  type: 'module',
  main() {
    browser.runtime.onMessage.addListener(handle);   // still must be synchronous here
  },
});
```

```ts
// entrypoints/shop.content.ts
export default defineContentScript({
  matches: ['https://shop.example.com/*'],
  runAt: 'document_idle',
  main(ctx) {
    const ui = createShadowRootUi(ctx, { name: 'pw-root', position: 'inline',
      anchor: 'body', onMount: mount, onRemove: unmount });
    ui.mount();
  },
});
```

`ctx` is the reason to use WXT for content scripts: it is invalidated when the extension
reloads, and `ctx.addEventListener`, `ctx.setInterval` and the UI helpers all unregister
themselves at that point. That is the orphaning problem from `content-scripts.md` solved by
construction.

Three UI helpers with different isolation: `createIntegratedUi` (page CSS applies),
`createShadowRootUi` (styles isolated, events isolated only if you ask), `createIframeUi`
(both isolated, no page DOM access). Default to the shadow root.

Import runtime helpers from `#imports`. The pre-0.20 paths `wxt/storage`, `wxt/client` and
`wxt/sandbox` have moved under `wxt/utils/*`; code copied from an older tutorial fails to
resolve.

## WXT storage

```ts
import { storage } from '#imports';

export const ignoredHosts = storage.defineItem<Host[]>('local:ignoredHosts', {
  fallback: [],
  version: 2,
  migrations: {
    2: (v1: string[]) => v1.map((host) => ({ host, mutedUntil: 0 })),
  },
});

await ignoredHosts.setValue([...]);
const unwatch = ignoredHosts.watch((next) => render(next));
```

The `local:` / `session:` / `sync:` / `managed:` prefix picks the area, so the quota and
content-script exposure rules in `storage-and-state.md` still apply unchanged. `defineItem`
adds the typed default and the versioned migration chain in one place, which is the main
reason to prefer it over calling `browser.storage` directly.

## WXT messaging

WXT deliberately ships no messaging abstraction — `browser.runtime.sendMessage` and the
`return true` rule from `messaging-and-contexts.md` apply as-is. When you want typed
messages, add `@webext-core/messaging` rather than hand-rolling a wrapper; it is the
option WXT's own documentation lists first among the light-weight ones.

## Cross-browser builds

Use the `browser` object from `#imports`, not `chrome.*`: WXT maps it onto the polyfill or
the native namespace per target, so the same source builds for Chrome and Firefox.

Chrome itself now exposes `browser` natively — from Chrome 148 every extension API is
available under both namespaces and they point at the same objects, and from Chrome 152
that also holds for extensions declaring a `devtools_page` (before 152, a `devtools_page`
disabled the `browser` namespace for the whole extension). So the polyfill is a
compatibility layer for older Chrome, not a permanent dependency; WXT keeps that decision
in one place, which is another reason not to write `chrome.*` by hand.

Feature-detect rather than branching on a user-agent string, and gate build-time
differences on `import.meta.env.BROWSER` / `import.meta.env.MANIFEST_VERSION`. Anything
Chrome-only — `chrome.sidePanel`, `chrome.offscreen`, `chrome.declarativeNetRequest`
session rules — needs a fallback or an explicit "Chrome only" surface.

## Bundling rules that are not negotiable

Whatever the build tool, two constraints come from the platform:

- **No remotely hosted code.** Every script must ship inside the package. A CDN
  `<script>`, a dynamic `import()` of an http URL, or a dependency that fetches code at
  runtime is a store rejection (see `web-store.md`).
- **No `eval`-based tooling in extension pages.** Source maps must be `devtool: 'source-map'`
  style, not `eval-source-map`; a dev build that injects `new Function` for HMR into an
  extension page is CSP-blocked. WXT and CRXJS both handle this; a hand-rolled Webpack
  config usually does not.

Keep content-script bundles small and separate from page bundles — a content script is
parsed on every matching page load, so a shared vendor chunk pulled into it is a cost paid
by every page the user visits.

## Inheriting a Manifest V2 codebase

Manifest V3 is the only form Chrome runs, so a V2 codebase is not a working extension —
treat this as a rewrite of the plumbing rather than a compatibility exercise. The mapping:

| Manifest V2 | Replacement |
|---|---|
| `background.scripts` / `background.page` | `background.service_worker`; all state moves to `chrome.storage` |
| `chrome.browserAction` / `chrome.pageAction` | `chrome.action` |
| `chrome.tabs.executeScript` / `insertCSS` | `chrome.scripting.executeScript` / `insertCSS` |
| `webRequest` with `blocking` | `declarativeNetRequest` rules |
| Permissions and hosts in one `permissions` array | Split into `permissions` and `host_permissions` |
| `chrome.extension.getBackgroundPage()` | Messaging or `chrome.storage`; there is no page to get |
| Remote `<script>`, `eval`, inline handlers | Bundled code, external files, `addEventListener` |
| Callback-style `chrome.*` calls | The same APIs return promises; `await` them |

Order that works: manifest keys first, then the background page to a worker with its state
externalised, then request blocking, then the API renames, then delete the polyfills the
old code carried. Verify after each step by loading unpacked — a V2 codebase usually has
several of these problems at once and fixing them in one commit makes the breakage
unattributable.

<!-- sources: wxt-docs, tenequm-wxt, dot-skills, rsc-harness, quangpl-ext, chrome-docs -->
