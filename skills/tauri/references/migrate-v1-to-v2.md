# Upgrading a Tauri 1 app to v2

Verified against: Tauri 2.x

## Contents

- Order of work
- Crate restructuring
- Config key moves
- Permissions replace the allowlist
- JavaScript module moves
- Rust crate moves
- Environment variable renames
- Event system changes
- Behaviour changes that bite silently
- Recognising v1 code in the wild

## Order of work

1. Restructure the crate (library entry point) — everything else assumes it.
2. Run `tauri migrate`, then read its whole diff. It handles most config keys and generates a
   capability from the allowlist, and it does not handle everything.
3. Move the remaining config keys by hand.
4. Add the plugin crates and npm packages for everything that left core, and fix the imports.
5. Rewrite the capability files properly — the generated one mirrors a v1 allowlist, which was
   app-wide, so it is usually far broader than the app needs.
6. Rename the CI environment variables and re-check the updater configuration.
7. Exercise every privileged flow in a packaged build; a missing permission is invisible until
   the call is made.

## Crate restructuring

```toml
# src-tauri/Cargo.toml
[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]
```

Rename `src/main.rs` to `src/lib.rs`, turn `fn main()` into:

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() { /* previous main() body */ }
```

and recreate a thin `main.rs`:

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
fn main() { app_lib::run(); }
```

Do this even for a desktop-only app: every later guide, example and plugin snippet assumes it.

## Config key moves

| v1 | v2 |
|---|---|
| `package.productName`, `package.version` | top level; `package` removed |
| (binary renamed to `productName` automatically) | add `mainBinaryName` matching `productName` |
| `tauri` | `app` |
| `tauri.allowlist` | removed — capability files |
| `tauri.allowlist.protocol.assetScope` | `app.security.assetProtocol.scope` |
| `tauri.cli` | `plugins.cli` |
| `tauri.updater` | `plugins.updater` (`active` and `dialog` removed) |
| `tauri.systemTray` | `app.trayIcon` |
| `tauri.pattern` | `app.security.pattern` |
| `tauri.windows.fileDropEnabled` | `app.windows.dragDropEnabled` |
| `tauri.bundle` | top-level `bundle`; `identifier` to top level |
| `tauri.bundle.dmg` / `deb` / `appimage` | `bundle.macOS.dmg` / `bundle.linux.deb` / `bundle.linux.appimage` |
| per-bundler `license` keys | `bundle.licenseFile` |
| `tauri.bundle.windows.webviewFixedRuntimePath` | `bundle.windows.webviewInstallMode` |
| `build.withGlobalTauri` | `app.withGlobalTauri` |
| `build.distDir` | `build.frontendDist` |
| `build.devPath` | `build.devUrl` |

Also new and required if the app auto-updates: `bundle.createUpdaterArtifacts`, set to
`"v1Compatible"` while v1 installs still exist in the wild.

## Permissions replace the allowlist

The v1 allowlist was one app-wide list of enabled APIs. v2 replaces it with an ACL: permissions
(per command, optionally scoped), grouped into capabilities that target specific windows,
webviews, platforms and remote origins.

`tauri migrate` parses the allowlist and writes a capability file, which is a starting point,
not the destination: it grants everything the old allowlist did, to every window. Rewrite it
into one capability per privilege level, keep only the permissions that have a real call site,
and add scopes to the path- and URL-taking ones. One asymmetry to know while doing this: the
app's **own** commands are callable from every window regardless of capabilities unless
`build.rs` declares a command manifest, so a capability cannot be the reason one of them fails.

## JavaScript module moves

`@tauri-apps/api` now only exports `core`, `path`, `event` and `window`/`webviewWindow`.
Everything else became a plugin package.

| v1 import | v2 |
|---|---|
| `@tauri-apps/api/tauri` | `@tauri-apps/api/core` |
| `@tauri-apps/api/window` (the `WebviewWindow` type) | `@tauri-apps/api/webviewWindow` |
| `@tauri-apps/api/cli` | `@tauri-apps/plugin-cli` |
| `@tauri-apps/api/clipboard` | `@tauri-apps/plugin-clipboard-manager` |
| `@tauri-apps/api/dialog` | `@tauri-apps/plugin-dialog` |
| `@tauri-apps/api/fs` | `@tauri-apps/plugin-fs` |
| `@tauri-apps/api/globalShortcut` | `@tauri-apps/plugin-global-shortcut` |
| `@tauri-apps/api/http` | `@tauri-apps/plugin-http` |
| `@tauri-apps/api/notification` | `@tauri-apps/plugin-notification` |
| `@tauri-apps/api/os` | `@tauri-apps/plugin-os` |
| `@tauri-apps/api/process` | `@tauri-apps/plugin-process` |
| `@tauri-apps/api/shell` | `@tauri-apps/plugin-shell` |
| `@tauri-apps/api/updater` | `@tauri-apps/plugin-updater` |

Each plugin package needs its Rust crate registered on the builder **and** its permission in a
capability. The v1 git-hosted `tauri-plugin-<name>-api` packages are now published as
`@tauri-apps/plugin-<name>`.

## Rust crate moves

- The whole `tauri::api` module is gone. `api::dialog` → `tauri-plugin-dialog`, `api::http` →
  `tauri-plugin-http`, `api::shell` and `api::process::Command` → `tauri-plugin-shell`,
  `api::file` → plain `std::fs`, `api::version` → the `semver` crate.
- `api::ipc` → `tauri::ipc` (this is where `Channel` and `Response` now live).
- `api::path` and `PathResolver` → `tauri::Manager::path()` (`app.path().app_data_dir()`).
- `updater` module → `tauri-plugin-updater`; `App::get_cli_matches` →
  `tauri-plugin-cli`; `clipboard_manager` → `tauri-plugin-clipboard-manager`;
  `global_shortcut_manager` → `tauri-plugin-global-shortcut`.
- Menu and tray APIs were rewritten: `tauri::menu` (built on muda) and `tauri::tray`. The v1
  `Menu`/`CustomMenuItem`/`SystemTray*` types are gone, not renamed.
- `Window` → `WebviewWindow`, `get_window` → `get_webview_window`.
- Removed Cargo features: `reqwest-client` (reqwest is the only client now),
  `process-command-api` and `shell-open-api` (shell plugin), `windows7-compat` (notification
  plugin), `updater` (plugin), `system-tray` (renamed `tray-icon`).

## Environment variable renames

Every one of these breaks CI silently — the build succeeds and the artifact is unsigned or
misconfigured:

| v1 | v2 |
|---|---|
| `TAURI_PRIVATE_KEY` | `TAURI_SIGNING_PRIVATE_KEY` |
| `TAURI_KEY_PASSWORD` | `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` |
| `TAURI_APPLE_DEVELOPMENT_TEAM` | `APPLE_DEVELOPMENT_TEAM` |
| `TAURI_PLATFORM`, `TAURI_ARCH`, `TAURI_FAMILY`, `TAURI_PLATFORM_VERSION`, `TAURI_PLATFORM_TYPE`, `TAURI_DEBUG` | `TAURI_ENV_*` |
| `TAURI_DEV_SERVER_PORT` | `TAURI_CLI_PORT` |
| `TAURI_PATH_DEPTH` | `TAURI_CLI_CONFIG_DEPTH` |
| `TAURI_SKIP_DEVSERVER_CHECK` | `TAURI_CLI_NO_DEV_SERVER_WAIT` |
| `TAURI_DEV_WATCHER_IGNORE_FILE` | `TAURI_CLI_WATCHER_IGNORE_FILENAME` |
| `TAURI_FIPS_COMPLIANT` | `TAURI_BUNDLER_WIX_FIPS_COMPLIANT` |
| `TAURI_TRAY` | `TAURI_LINUX_AYATANA_APPINDICATOR` |

## Event system changes

The system is now target-based rather than source-based:

- `emit` delivers to **all** listeners.
- `emit_to`/`emitTo` targets one label; `emit_filter` takes an `EventTarget` predicate rather
  than a window.
- `listen_global` → `listen_any`.
- In JavaScript, `listen()` behaves like `listen_any` unless a target is passed in the options,
  while `WebviewWindow.listen` only receives events emitted to that target.

Code that relied on "the event I emitted from window A is only heard by window A" needs
re-checking: that is no longer how `emit` behaves.

## Behaviour changes that bite silently

- **Windows origin scheme.** Production frontends are now served from `http://tauri.localhost`
  instead of `https://tauri.localhost`, so IndexedDB, LocalStorage and cookies are **reset**
  for existing users. Set `app.windows.useHttpsScheme: true` (or
  `WebviewWindowBuilder::use_https_scheme`) to keep the old scheme and the stored data.
- **No automatic binary rename.** Without `mainBinaryName`, the produced binary keeps the crate
  name, which breaks shortcuts, updater artifact names and anything scripted around the path.
- **The updater dialog is gone.** `tauri.updater.dialog` no longer exists; the app has to
  present the update UI itself.
- **Sidecar arguments moved into permissions.** In v1 they lived in the allowlist; in v2 the
  argument pattern is part of the shell permission entry, and a mismatch is a runtime denial.

## Recognising v1 code in the wild

Plenty of third-party guidance is still v1 while claiming to be current. These markers mean the
snippet is v1 and its advice does not apply:

- `import { invoke } from '@tauri-apps/api/tauri'`
- `use tauri::api::...` (any path under `tauri::api`)
- `allowlist` anywhere in a config
- a `"tauri": { "bundle": ... }` config shape, or `distDir`/`devPath`
- `SystemTray`, `CustomMenuItem`, `Menu::new()` from the old menu API
- `tauri::Window` as a command parameter instead of `tauri::WebviewWindow`

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2 -->
