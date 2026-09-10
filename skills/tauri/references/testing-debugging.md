# Testing and debugging

Verified against: Tauri 2.x

## Contents

- Where the error actually appears
- Dev-only code: `dev` vs `debug_assertions`
- Devtools
- Frontend tests with mocked IPC
- Rust tests with the mock runtime
- End-to-end tests
- Symptom table

## Where the error actually appears

Two consoles, and the first debugging step is knowing which one to read:

| Console | Shows |
|---|---|
| terminal running `tauri dev` | `println!(...)` and tracing output, Rust panics, plugin init failures, the frontend build's own output |
| webview inspector | rejected `invoke` promises, permission denials, CSP violations, frontend errors |

A permission denial never appears in the Rust console, and a Rust panic never appears in the
webview console. Reproduce a panic with `RUST_BACKTRACE=1 tauri dev` (or
`$env:RUST_BACKTRACE=1` on PowerShell) for a usable stack.

## Dev-only code: `dev` vs `debug_assertions`

```rust
if cfg!(dev) { /* started by `tauri dev` */ }
if cfg!(debug_assertions) { /* `tauri dev` OR `tauri build --debug` */ }
let is_dev = tauri::is_dev();
```

These are not interchangeable. Verbose logging usually belongs behind `debug_assertions` so a
`--debug` bundle keeps it; anything that assumes a dev server belongs behind `dev`.

## Devtools

- Right-click → Inspect Element, or `Ctrl+Shift+I` (Linux/Windows) / `Cmd+Option+I` (macOS).
  The inspector is the platform's own: WebKit's on Linux, Safari's on macOS, Edge DevTools on
  Windows — so DevTools features themselves differ per platform.
- `window.open_devtools()` / `close_devtools()` open it programmatically; guard the call with
  `#[cfg(debug_assertions)]`.
- `tauri build --debug` produces a **packaged** app that still has the inspector, in
  `src-tauri/target/debug/bundle`. This is the right build for reproducing anything that only
  happens when packaged (asset loading, CSP, capabilities, resource paths).
- The `devtools` Cargo feature enables the inspector in **release** builds. It uses a private
  API on macOS, which blocks App Store acceptance — do not enable it as a convenience.

## Frontend tests with mocked IPC

`@tauri-apps/api/mocks` fakes the whole backend, so component and store tests run in
jsdom/happy-dom without a Rust build:

```ts
import { afterEach, expect, test, vi } from 'vitest';
import { clearMocks, mockIPC, mockWindows } from '@tauri-apps/api/mocks';
import { invoke } from '@tauri-apps/api/core';

afterEach(() => clearMocks());   // mock state leaks between tests otherwise

test('loads a project', async () => {
  mockIPC((cmd, args) => {
    if (cmd === 'load_project') return { id: (args as { projectId: string }).projectId };
  });
  const spy = vi.spyOn(window.__TAURI_INTERNALS__, 'invoke');

  await expect(invoke('load_project', { projectId: 'a' })).resolves.toEqual({ id: 'a' });
  expect(spy).toHaveBeenCalled();
});
```

- `clearMocks()` after every test is not optional; without it, mock state carries into the next
  test and the failures look unrelated to their cause.
- The handler receives the **camelCase** argument object the real IPC would send, which makes
  these tests the cheapest place to catch a casing mistake.
- `mockWindows('main', 'settings')` fakes window **labels** only — the first is the "current"
  one. Window properties still have to be intercepted through `mockIPC`.
- Event mocking is partial: `mockIPC(handler, { shouldMockEvents: true })` (2.7.0+) supports
  `emit`/`listen`; `emitTo` and `emit_filter` are not supported.
- jsdom has no WebCrypto, and the Tauri API needs it: define `window.crypto.getRandomValues`
  (from Node's `crypto.randomFillSync`) in a `beforeAll` or every test fails on import.
- Mocking a sidecar/shell call means grabbing the callback id from the args
  (`args.message.onEventFn`) and invoking `window[`_${id}`]` with `Stdout` events and a final
  `Terminated` event — without the `Terminated` the promise never resolves.

## Rust tests with the mock runtime

`tauri::test::MockRuntime` builds an app without a real webview, so command logic can be tested
in `cargo test`. It requires the commands to be generic over the runtime
(`AppHandle<R>`/`WebviewWindow<R>` with `R: Runtime`) rather than assuming `Wry`; write them
that way from the start, because retrofitting the generic parameter touches every signature.

Keep the testable logic in plain functions that the command wraps: a command is a thin
adapter (deserialise, validate, call, map the error), and plain functions need no runtime at
all.

## End-to-end tests

- The recommended route is WebdriverIO with `@wdio/tauri-service`, which works on Windows,
  Linux and macOS. By default it runs an **embedded** WebDriver server inside the app (this is
  how macOS is supported at all) via `tauri-plugin-wdio-webdriver`; `tauri-plugin-wdio` adds
  `browser.tauri.execute()`, IPC mocking and log capture. `npm create wdio@latest ./` scaffolds
  it — choose Desktop Testing, then Tauri.
- Driving `tauri-driver` directly (Selenium, or a non-Node harness) works on **Windows and
  Linux only**: macOS has no WKWebView driver.
- Point `appBinaryPath` at a built binary. E2E tests therefore test the packaged behaviour,
  which is what makes them worth the cost — capabilities, CSP and resource resolution are all
  live.
- On a headless CI machine, IPC message encryption under the isolation pattern needs entropy;
  install an entropy daemon if the runner's kernel does not provide enough.
- There is also a browser mode that runs the frontend in plain Chrome against the Vite dev
  server and intercepts `invoke()` — no binary, no driver. Use it for renderer-only assertions
  and keep the real-binary suite for the privileged paths.

## Symptom table

| Symptom | First thing to check |
|---|---|
| "Command <name> not found" | the command is not in the single `generate_handler![...]` list, or a second `invoke_handler` call replaced the first |
| Permission/not-allowed error in the webview console | the plugin permission missing from the capability whose `windows` matches this window's label; if `app.security.capabilities` is set, whether the file is listed |
| Panic on first call to a command taking state | `State<T>` does not match the `.manage()`d type |
| Argument arrives as `undefined`/`null` | snake_case sent where camelCase is expected, or vice versa with `rename_all` |
| UI freezes during an operation | blocking work in a synchronous command (runs on the main thread) |
| Large response is slow | a `Serialize` return value being JSON-encoded; use `tauri::ipc::Response` or a channel |
| Blank white window | the frontend never built (`beforeDevCommand`), or `devUrl` does not match the dev server port |
| `invoke` fails only in the packaged build | CSP missing `ipc: http://ipc.localhost`, or a capability that only existed in a dev-only config |
| Works in dev, asset missing when packaged | path assumed instead of resolved through `app.path().resolve(..., BaseDirectory::Resource)`, or the file not listed in `bundle.resources` |
| Sidecar not found | missing `-$TARGET_TRIPLE` suffix, wrong name on the Rust or JS side, or the shell permission naming a different `name` |
| Update downloads but fails to install | signature/`pubkey` mismatch, a `signature` field holding a path, or a manifest entry for another platform being invalid |
| Feature works on Windows/macOS, breaks on Linux | `webkit2gtk` is older than WebView2 and WKWebView; check the feature against the shipped WebKit version |

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2 -->
