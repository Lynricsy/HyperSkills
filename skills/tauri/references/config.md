# Configuration and project layout

Verified against: Tauri 2.x (`tauri`, `tauri-build`, `@tauri-apps/cli` 2)

## Contents

- Crate layout and why `lib.rs` owns everything
- `tauri.conf.json`: shape and formats
- Platform-specific overrides and their merge semantics
- Per-flavour builds with `--config`
- Cargo manifest and version alignment
- Icons, resources and generated files
- Binary size and unused commands

## Crate layout and why `lib.rs` owns everything

```
my-app/
├── src/                      # frontend sources (any framework)
├── src-tauri/
│   ├── src/
│   │   ├── main.rs           # thin: calls app_lib::run()
│   │   └── lib.rs            # builder, state, command registration
│   ├── capabilities/         # *.json / *.json5 / *.toml
│   ├── permissions/          # *.toml only, app-defined permissions
│   ├── icons/
│   ├── gen/schemas/          # generated; source of truth for permission names
│   ├── build.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
└── package.json
```

`main.rs` stays a passthrough:

```rust
// src-tauri/src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    app_lib::run();
}
```

```rust
// src-tauri/src/lib.rs
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // plugins, state, command registration — all of it here
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Mobile targets never call `main()`; the `mobile_entry_point` macro calls `run()` directly. Any
setup left in `main.rs` therefore exists on desktop only, and the omission surfaces as a
feature that "works on desktop, does nothing on mobile". The matching `Cargo.toml` block:

```toml
[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]
```

All three crate types are needed: `staticlib` for iOS, `cdylib` for Android, `rlib` for the
desktop binary. `windows_subsystem = "windows"` in release is what suppresses the console
window on Windows — keep the `not(debug_assertions)` guard so the console stays in dev.

## `tauri.conf.json`: shape and formats

Top level keys that matter most: `productName`, `mainBinaryName`, `version`, `identifier`,
`build`, `app`, `bundle`, `plugins`.

```json
{
  "$schema": "./gen/schemas/desktop-schema.json",
  "productName": "Notely",
  "version": "1.4.0",
  "identifier": "com.example.notely",
  "build": {
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build"
  },
  "app": {
    "windows": [{ "label": "main", "title": "Notely", "width": 1280, "height": 800 }],
    "security": {
      "csp": "default-src 'self'; connect-src 'self' ipc: http://ipc.localhost",
      "capabilities": ["main-capability"]
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/32x32.png", "icons/icon.icns", "icons/icon.ico"]
  },
  "plugins": {}
}
```

- `devUrl` must match the port the frontend dev server actually binds; a mismatch shows as a
  blank window with no error in the Rust console.
- `frontendDist` is a directory of static assets. Tauri serves them, so anything that requires
  a Node server at runtime (framework SSR) does not work unpackaged.
- `build.beforeDevCommand` / `beforeBuildCommand` are how the frontend gets built; if they are
  empty the packaged app ships whatever was last in `frontendDist`.
- JSON is the default. JSON5 (`tauri.conf.json5`) or TOML (`Tauri.toml`) need the
  `config-json5` / `config-toml` feature on **both** `tauri` and `tauri-build`. Field names are
  case-sensitive in all three; TOML additionally allows kebab-case (`dev-url`).
- Keep `"$schema"` pointing at `./gen/schemas/desktop-schema.json` — that file is regenerated on
  build and is what gives an editor the real key and permission completions.

## Platform-specific overrides and their merge semantics

`tauri.linux.conf.json`, `tauri.windows.conf.json`, `tauri.macos.conf.json`,
`tauri.android.conf.json`, `tauri.ios.conf.json` (or the `Tauri.<platform>.toml` equivalents)
are merged into the base config with **JSON Merge Patch (RFC 7396)**:

- objects merge key by key;
- **arrays are replaced as a whole**, including arrays nested inside objects;
- that includes arrays whose elements are objects, such as `app.windows` — a platform entry
  replaces the base entry rather than merging into it, so every field omitted from the override
  falls back to its **default**, not to the base file's value.

The practical consequence, and the most common configuration bug in a multi-platform app:

```json
// tauri.conf.json
{ "bundle": { "resources": ["templates/", "dictionaries/"] },
  "app": { "windows": [
    { "label": "main", "title": "Notely", "width": 1280, "height": 800 },
    { "label": "quicknote", "width": 420, "height": 260 }
  ]}}
```

```json
// tauri.macos.conf.json — WRONG: loses templates/, loses the quicknote window,
// and resets main to 800x600 default size with no title
{ "bundle": { "resources": ["mac-dictionaries/"] },
  "app": { "windows": [{ "label": "main", "titleBarStyle": "Overlay" }] }}
```

```json
// tauri.macos.conf.json — right: repeat everything that must survive
{ "bundle": { "resources": ["templates/", "dictionaries/", "mac-dictionaries/"] },
  "app": { "windows": [
    { "label": "main", "title": "Notely", "width": 1280, "height": 800,
      "titleBarStyle": "Overlay", "hiddenTitle": true },
    { "label": "quicknote", "width": 420, "height": 260 }
  ]}}
```

When a platform difference is only about one field of one window, creating the window from Rust
with `WebviewWindowBuilder` and a `#[cfg(target_os = ...)]` branch is less error-prone than an
override file.

## Per-flavour builds with `--config`

`dev`, `build` and `bundle` accept `--config` with either raw JSON or a path to a JSON file,
merged with the same RFC 7396 rules. This is the supported way to build a beta or internal
flavour without duplicating the whole config:

```json
// src-tauri/tauri.beta.conf.json
{ "productName": "My App Beta", "identifier": "com.myorg.myappbeta" }
```

```bash
tauri build --config src-tauri/tauri.beta.conf.json
```

A different `identifier` is what makes the flavour install side by side; keeping the identifier
and only changing the name produces two builds that overwrite each other's data directory.

## Cargo manifest and version alignment

```toml
[build-dependencies]
tauri-build = { version = "2" }

[dependencies]
tauri = { version = "2", features = [] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

- `tauri` and `tauri-build` should track the same minor version as the CLI. `tauri info` prints
  all of them plus the installed webview version — read it before debugging a version-shaped
  problem.
- Leave `features = []` alone: `tauri dev`/`build` enable what the config needs. The exceptions
  you set by hand are `devtools` (release-build inspector, private API on macOS),
  `config-json5` /
  `config-toml`, and the tray/`unstable` flags.
- Commit `Cargo.lock`; `src-tauri` is a binary crate and reproducible builds matter for
  signing.
- Every `@tauri-apps/plugin-*` npm package must move in lockstep with its `tauri-plugin-*`
  crate. A JS binding calling a command the older crate does not have fails at runtime with a
  not-allowed or not-found error rather than at install time.

## Icons, resources and generated files

- `tauri icon path/to/source.png` regenerates the whole `icons/` set (`.icns`, `.ico`, PNGs).
  Hand-maintained icon sets drift per platform; regenerate instead.
- `bundle.resources` ships extra files with the app; resolve them at runtime through
  `app.path().resolve(rel, BaseDirectory::Resource)` rather than assuming a layout, and grant
  `$RESOURCE`-scoped fs permissions if the frontend must read them.
- `src-tauri/gen/` is generated (schemas, mobile projects). `gen/schemas/*.json` is the
  authoritative list of permission identifiers available to this app — read it instead of
  guessing a permission name.

## Binary size and unused commands

A release profile is the cheapest size win:

```toml
# src-tauri/Cargo.toml
[profile.release]
codegen-units = 1   # better LLVM optimisation
lto = true          # link-time optimisation
opt-level = "s"     # size; use 3 when a hot path needs speed
panic = "abort"     # drops the unwinding machinery
strip = true        # removes debug symbols
```

`build.removeUnusedCommands` (needs `tauri@2.4`, `tauri-build@2.1`, `tauri-plugin@2.1`,
`tauri-cli@2.4`) drops commands that no capability allows, which only pays off if the
capabilities list individual commands rather than plugin `default` sets. It cannot see ACLs
added at runtime, so verify the app after enabling it.

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2, full-stack-skills-tauri -->
