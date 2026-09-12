---
name: tauri
description: "Guides Tauri v2 desktop and mobile application work end to end: tauri.conf.json and platform-specific config overrides, the capabilities and permissions model with command scopes and the runtime authority, IPC through #[tauri::command], events, channels and managed state, plugin usage and plugin authoring, windows, webviews, tray and menus, sidecars and bundled resources, the updater with its signing keys, code signing and notarisation, dev-time debugging and mock-based testing, upgrading a Tauri 1 app to v2, and the security baseline (CSP, isolation pattern, Rust-side validation). Use when reading or editing src-tauri, tauri.conf.json, capabilities/*.json, build.rs or invoke calls, when a command or plugin call fails at runtime, when packaging or auto-updates break, or when hardening a Tauri app. Do not use for frontend framework work, general Rust language questions, or Electron."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# tauri

## Scope

Covers Tauri v2 applications: the `src-tauri` crate and its `tauri.conf.json`, the
capabilities/permissions/scope security model and the runtime authority that enforces it, the
IPC surface (commands, events, channels, managed state, raw requests and responses), official
plugins and writing your own, window and webview configuration including tray and menus,
embedded sidecars and bundled resources, the updater and its signature keys, bundling and code
signing on each desktop platform, dev-time debugging and mock-based frontend tests, the
Tauri 1 → 2 upgrade, and the security baseline an app ships with.

Not covered: the frontend framework itself — React or Next.js component, hook and rendering
questions belong to the `react` skill; visual and layout design belongs to the
`frontend-design` skill; type-layer modelling and `tsconfig` belong to the `typescript` skill.
General Rust language and crate questions (ownership puzzles, async runtime choice, `Cargo`
workspace layout unrelated to `src-tauri`) belong to the `rust` skill. Vue and Svelte,
and Electron are not covered here; use their own documentation. Mobile work is
covered only where the desktop code has to stay buildable for it (library entry point, crate
type, per-platform capabilities, plugins without a mobile implementation); full Android and iOS
platform work is not in scope.

Paths below are relative to this skill's directory.

## Core rules

1. Read `src-tauri/tauri.conf.json`, `src-tauri/capabilities/*` and `src-tauri/Cargo.toml`
   before changing anything. Which plugins are initialised, which capabilities exist and which
   window labels are declared decide every answer below.
2. Register every command in **one** `tauri::generate_handler![...]` call. A second
   `.invoke_handler(...)` on the builder silently replaces the first, so the commands from the
   earlier call disappear with a "Command not found" at runtime, not at compile time.
3. Commands defined in `lib.rs` cannot be `pub` (macro limitation). Put them in a module,
   register them as `module::command`, and keep invoking them by the bare function name — the
   module path is not part of the command name.
4. A command **without** `async` runs on the main thread unless it is declared
   `#[tauri::command(async)]`. Any blocking I/O in a synchronous command freezes the window;
   `async` commands are spawned onto the async runtime instead.
5. An `async` command cannot take borrowed arguments. Convert `&str` to `String`, and when the
   command injects `State<'_, T>` — which has no owned equivalent — make it return `Result`.
   That is the only form that compiles.
6. Never hold a `std::sync::Mutex` guard across an `.await`. Lock inside a scope that ends
   before the await, or use an async mutex when the guard genuinely must outlive it.
7. `State<'_, T>` must name exactly the type passed to `.manage()`. A mismatch (`State<AppState>`
   against `manage(Mutex::new(AppState))`) is a **runtime panic**, not a compile error; a
   `type AppState = Mutex<AppStateInner>` alias removes the whole class of mistake.
8. Do not wrap managed state in `Arc`. `State` already shares ownership. When state must move
   into a thread, clone the `AppHandle` (cheap by design) and call `handle.state::<T>()` there.
9. Return `Result<T, E>` from anything fallible and give `E` a real type: a `thiserror` enum with
   a manual `serde::Serialize` impl, tagged as `{ kind, message }` when the frontend needs to
   branch. A `String` error erases every distinction the caller might act on.
10. Arguments cross the IPC boundary as a JSON object with **camelCase** keys, so
    `fn load(project_path: String)` is invoked as `{ projectPath }`. Change the mapping with
    `#[tauri::command(rename_all = "snake_case")]`, never by guessing.
11. Return `tauri::ipc::Response` for binary payloads and stream progress through
    `tauri::ipc::Channel`. Anything returned as a plain `Serialize` value is JSON-encoded, which
    is what makes multi-megabyte responses slow.
12. Use commands for request/response and events only for small fan-out notifications. Events are
    untyped, JSON-only, uncovered by the capabilities system, and `emit` reaches every listener —
    `emit_to` targets one webview label, and those events are invisible to `listen` unless the
    listener opts into the catch-all target.
13. Plugin and `core:` commands are unreachable until a capability grants them. Commands you wrote
    yourself are the opposite: registered through `invoke_handler`, they are callable from **every**
    window by default. Restrict them with `AppManifest::commands(&[...])` in `build.rs`, then let
    capabilities decide which window may call which. A "Permission denied" therefore never
    explains a failing call to your own command.
14. Target capabilities by window **label**, not title, and keep one capability per privilege
    level instead of `windows: ["*"]`. Permissions from all matching capabilities merge, so a
    single broad file re-grants everything you split apart. Never expose window creation to a
    low-privilege window.
15. All capability files under `src-tauri/capabilities/` are enabled automatically. The moment
    `app.security.capabilities` is set in `tauri.conf.json`, only the listed ones apply — adding a
    file then has no effect until it is listed too.
16. Deny beats allow in scopes, and the scope is only advisory until the command enforces it. Any
    command taking a caller-supplied path, URL or identifier must canonicalise it and check it
    against an app-owned root in Rust. The webview is never the trust boundary.
17. Expose product operations (`import_document`, `save_account`), not primitives. A
    `run_shell(cmd: String)` or `write_any_file(path, bytes)` command hands the whole capability
    system's job to whatever runs in the webview.
18. Ship a real CSP. `app.security.csp: null` disables it; a policy must keep
    `ipc: http://ipc.localhost` in `connect-src` or `invoke` stops working. `devCsp` **replaces**
    `csp` under `tauri dev`, so the dev-server origins and the loosened `script-src` HMR needs go
    there while production stays tight — Tauri hashes bundled inline scripts at build time, so
    production does not need `'unsafe-inline'`.
19. Platform config files (`tauri.<platform>.conf.json`) merge by JSON Merge Patch: objects merge
    per key, **arrays are replaced whole**, including arrays of objects like `app.windows`. Fields
    omitted from a replaced entry fall back to their defaults, not to the base file — repeat
    everything you want to keep.
20. `bundle.externalBin` entries must exist on disk with a `-$TARGET_TRIPLE` suffix per platform
    (`rustc --print host-tuple` for the current host). Rust's `shell().sidecar(name)` takes the
    bare filename; JavaScript's `Command.sidecar(...)` takes the exact string from `externalBin`.
    `execute()` and `spawn()` need different permissions (`shell:allow-execute` /
    `shell:allow-spawn`) with `"sidecar": true`.
21. The updater refuses unsigned artifacts and this cannot be turned off. Set
    `bundle.createUpdaterArtifacts` (`true`, or `"v1Compatible"` only for already-distributed v1
    apps), put the **key content** in `pubkey` — a path is rejected — and pass the private key
    through `TAURI_SIGNING_PRIVATE_KEY`, which is read from the environment and not from a `.env`
    file. In a manifest, `signature` is likewise the content of the `.sig`, never a path.
22. Updater endpoints enforce TLS in production and are tried in order only while a response is
    non-2XX; a dynamic server answers `204` for "no update" and `200` with the manifest otherwise.
    On Windows prefer `installMode: "passive"` — `"quiet"` cannot request elevation, so it only
    works for per-user installs.
23. Judge behaviour and size on `tauri build` output, not `tauri dev`. Gate debug-only code with
    `cfg!(dev)` for "started by `tauri dev`" and `cfg!(debug_assertions)` for "dev or
    `build --debug`"; they are different. Enabling the `devtools` Cargo feature ships a private
    macOS API and blocks App Store review.
24. Keep `main.rs` a thin call into `lib.rs::run()` and keep the `[lib] crate-type =
    ["staticlib", "cdylib", "rlib"]` block. Everything the builder sets up must live in `run()`,
    because mobile targets replace `main()` with `#[cfg_attr(mobile, tauri::mobile_entry_point)]`.
25. Pin `tauri` and `tauri-build` to the same minor version as the CLI, and upgrade the npm
    `@tauri-apps/api` and every `@tauri-apps/plugin-*` package together with their Rust crates. A
    plugin's JS bindings and its Rust crate are one unit.

## Workflows

### add-ipc-feature

- [ ] Decide the primitive first: command for request/response, channel for a stream, event only
      for small notifications (rule 12).
- [ ] Write the Rust command in a module, with owned argument types, a typed error enum and
      `Result` (rules 3, 5, 9). Mark it `async` if it touches I/O (rule 4).
- [ ] Register it in the single `generate_handler![...]` list (rule 2) and add any new managed state
      with `.manage()`, using the exact type the command will ask for (rule 7).
- [ ] Validate every caller-supplied path, id or URL inside the command against an app-owned root
      (rule 16).
- [ ] Add the frontend call with camelCase argument keys, wrapped in one typed module rather than
      scattered `invoke` calls (rule 10).
- [ ] If the feature uses a plugin API, add its permission to the capability of the windows that
      need it — and only those (rules 13, 14).
- [ ] **Gate:** `cargo check --manifest-path src-tauri/Cargo.toml` passes, then `tauri dev`
      exercises the call from the real window with the webview console open and no CSP or
      permission error.

### fix-runtime-failure

- [ ] Take the exact message and split it by origin: Rust console (`tauri dev` terminal) for panics
      and command errors, webview console for permission denials, CSP violations and rejected
      promises.
- [ ] Match the symptom before theorising:
      "Command not found" → not in `generate_handler![...]`, or a second `invoke_handler` call
      (rule 2). "Permission denied"/"not allowed" → a plugin or `core:` permission missing from
      the capability matching that window label (rules 13, 14, 15).
      Panic on state access → `State<T>` type mismatch (rule 7).
      Frozen UI → blocking work in a synchronous command (rule 4).
      Argument arrives `undefined` → casing (rule 10).
      Sidecar not found → missing target-triple suffix or wrong name on one of the two sides
      (rule 20).
      Blank window → the frontend never built, or `devUrl` does not match the dev server.
- [ ] Reproduce with `RUST_BACKTRACE=1` when a panic is involved, and read the generated
      `src-tauri/gen/schemas/*-schema.json` when a permission identifier is in doubt.
- [ ] Confirm the fix in a `tauri build --debug` bundle, not only in `tauri dev` — permission and
      CSP behaviour differ between them (rules 18, 23).
- [ ] **Gate:** the original symptom is gone in a packaged debug build and the capability diff
      grants nothing beyond what the failing call needed.

### harden

- [ ] Inventory the real surface: every `#[tauri::command]`, every initialised plugin, every
      capability file and the window labels each one targets.
- [ ] Remove permissions no frontend call uses; replace plugin `default` sets with the individual
      command permissions that remain (rule 14). Consider `build.removeUnusedCommands` once the
      capability list is exact.
- [ ] Split capabilities per privilege level and per platform, and delete `windows: ["*"]`
      (rules 14, 15).
- [ ] Add scopes to every path- and URL-taking permission, with `deny` entries for anything under
      the app's own data directory that the frontend must not read (rule 16).
- [ ] Write `csp` and `devCsp` explicitly and load the app once in each mode watching for
      violations (rule 18).
- [ ] Re-read the command signatures as an attacker: primitives to replace with product
      operations, unvalidated paths, unbounded payloads (rules 16, 17).
- [ ] Consider the isolation pattern when the frontend has a large dependency tree
      (`references/security-hardening.md`).
- [ ] **Gate:** every remaining permission is traceable to a specific frontend call site, and
      `tauri build` plus a manual pass over the app's privileged flows still works.

### ship-release

- [ ] Set `bundle.createUpdaterArtifacts`, generate the key pair with `tauri signer generate`, and
      put the public key content into `plugins.updater.pubkey` (rule 21).
- [ ] Export `TAURI_SIGNING_PRIVATE_KEY` (and its password) in the build environment — not in a
      file — and confirm the build emits `.sig` files next to the bundles (rule 21).
- [ ] Configure platform signing: `signingIdentity` plus notarisation credentials on macOS,
      `certificateThumbprint`/`digestAlgorithm`/`timestampUrl` or a custom sign command on Windows
      (`references/updater-distribution.md`).
- [ ] Serve the manifest over HTTPS with the `.sig` **content** in `signature`, and verify every
      platform entry — the whole file is validated before the version is even compared (rule 22).
- [ ] Check the platform config overrides by resolving them mentally against the base file, field
      by field, before trusting them (rule 19).
- [ ] **Gate:** install the previous version, publish the new manifest, and watch a real update
      download, verify, install and relaunch on each target platform.

### migrate-v1-to-v2

- [ ] Restructure the crate first: `[lib]` block, `main.rs` → `lib.rs` with
      `pub fn run()`, thin `main.rs` (rule 24).
- [ ] Run `tauri migrate`, then read the whole change set — it does not catch everything.
- [ ] Move the config keys by hand: `tauri` → `app`, `bundle` to top level, `devPath` → `devUrl`,
      `distDir` → `frontendDist`, `updater` → `plugins.updater`, `systemTray` → `trayIcon`, plus
      `mainBinaryName` which is no longer derived from `productName`.
- [ ] Replace `allowlist` with capability files, one per privilege level, listing only the
      permissions the code actually calls (`references/migrate-v1-to-v2.md`).
- [ ] Add the plugin crates and npm packages for everything that left core (dialog, fs, http,
      shell, clipboard, notification, updater, global-shortcut, process, os, cli) and rewrite the
      imports: `@tauri-apps/api/tauri` → `@tauri-apps/api/core`,
      `@tauri-apps/api/window` → `@tauri-apps/api/webviewWindow`.
- [ ] Rename the CI environment variables (`TAURI_PRIVATE_KEY` → `TAURI_SIGNING_PRIVATE_KEY` and
      the rest) and set `createUpdaterArtifacts: "v1Compatible"` if v1 builds are already in
      users' hands (rule 21).
- [ ] **Gate:** `tauri build` succeeds, then every previously working privileged flow is exercised
      once in the packaged app — a missing permission is invisible until the call is made.

### review

- [ ] Read the capability diff and the command diff together; a new command with no capability
      change is normal, a new plugin permission with no new call site is not.
- [ ] Walk the Core rules in order — they are ordered by how often each one is the actual defect.
- [ ] Check the IPC boundary specifically: sync commands doing I/O, `String` errors, `Vec<u8>`
      returns, missing validation, argument casing.
- [ ] Check config diffs against the merge semantics of platform overrides and the updater
      requirements (rules 19, 21, 22).
- [ ] Report with the Output format below.
- [ ] **Gate:** every finding carries `path:line`, one line of reasoning, and a concrete fix.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Configuration | Editing `tauri.conf.json`, platform overrides, `Cargo.toml`, project layout, binary size | `references/config.md` |
| IPC commands | Writing or fixing `#[tauri::command]`, arguments, errors, async, state, raw requests | `references/ipc-commands.md` |
| Events and channels | Pushing data from Rust, streaming progress, listener targets and cleanup | `references/ipc-events-channels.md` |
| Capabilities and permissions | Writing capability files, scopes, `build.rs` command manifest, permission identifiers | `references/capabilities-permissions.md` |
| Security hardening | CSP, HTTP headers, isolation pattern, asset protocol, validation and secrets | `references/security-hardening.md` |
| Plugins and sidecars | Adding a plugin, authoring one, embedding an external binary, bundled resources | `references/plugins-and-sidecar.md` |
| Windows and webviews | Creating windows, labels, decorations, tray, menus, splashscreen, platform webviews | `references/windows-webviews.md` |
| Updater and distribution | Update flow, signing keys, manifests, code signing, notarisation, bundle targets | `references/updater-distribution.md` |
| Testing and debugging | `mockIPC`, WebDriver, `MockRuntime`, devtools, dev-only code, backtraces | `references/testing-debugging.md` |
| Tauri 1 → 2 upgrade | Porting a v1 app, or reading code that still uses v1 APIs | `references/migrate-v1-to-v2.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
src-tauri/src/lib.rs
  L47 blocking - second .invoke_handler() call replaces the first, so load_project and
       list_recent are unregistered and fail at runtime with "Command not found".
       before: .invoke_handler(generate_handler![load_project]).invoke_handler(generate_handler![export])
       after:  .invoke_handler(generate_handler![load_project, export])
  L22 blocking - State<AppState> does not match manage(Arc<Mutex<AppState>>); this panics on the
       first call. Manage Mutex::new(AppState) and take State<'_, Mutex<AppState>>; drop the Arc.
  L26 important - export_report is synchronous, so its 40 MB write runs on the main thread and
       freezes the window. Make it `async fn`.

src-tauri/capabilities/default.json
  L5 important - windows: ["*"] grants the quicknote window everything the main window has.
       Split into one capability per window label.
```

Severities: `blocking` (runtime panic, unreachable command, unsigned or unverifiable update,
permission hole, data loss), `important` (frozen UI, over-broad capability, missing validation,
avoidable IPC cost, config that silently loses values), `minor` (naming, ordering, dead
permissions). End with a one-line verdict: ship, ship after blocking fixes, or rework.

## Environment

Rust with the platform toolchain plus the Tauri CLI (`@tauri-apps/cli` or `tauri-cli`); on Linux
also the WebKitGTK and related system packages, on Windows the WebView2 runtime, on macOS Xcode
command line tools. Commands used by the workflows:

```bash
cargo check --manifest-path src-tauri/Cargo.toml   # cheapest check after a Rust change
tauri dev                                          # dev server + webview, devtools available
RUST_BACKTRACE=1 tauri dev                          # when a command panics
tauri build --debug                                 # packaged build that still has devtools
tauri build                                         # release bundles (+ .sig when configured)
tauri signer generate -w ~/.tauri/myapp.key         # updater key pair, once per app
tauri info                                          # installed CLI, crate and webview versions
rustc --print host-tuple                            # sidecar suffix for the current host
```

macOS signing and notarisation require macOS with a Developer ID certificate installed;
Windows signing requires the certificate in the machine's store or an Azure Key Vault
configuration. Mobile targets additionally need the Android SDK/NDK or Xcode and the extra Rust
targets installed with `rustup target add`.
