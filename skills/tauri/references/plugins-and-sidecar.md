# Plugins, sidecars and bundled resources

Verified against: Tauri 2.x

## Contents

- Adding an official plugin
- Registration order that matters
- Plugin pitfalls worth knowing before you hit them
- Bundled resources
- Sidecars: embedding an external binary
- Writing a plugin
- Plugin permissions you author
- Mobile implementations

## Adding an official plugin

`tauri add <plugin>` (via the package manager, e.g. `pnpm tauri add dialog`) does all four
steps at once: the Rust crate, the builder registration, the npm package, and the plugin's
default permission in the capability. Doing it by hand means all four — a plugin whose crate is
present but whose permission is missing fails at runtime, in the webview console, with a
not-allowed error.

Desktop-only plugins should be added with a target guard so mobile builds still compile:

```toml
[target."cfg(any(target_os = \"macos\", windows, target_os = \"linux\"))".dependencies]
tauri-plugin-updater = "2"
```

```rust
.setup(|app| {
    #[cfg(desktop)]
    app.handle().plugin(tauri_plugin_updater::Builder::new().build())?;
    Ok(())
})
```

Plugin configuration lives under `plugins.<plugin-name>` in `tauri.conf.json` and is parsed at
runtime, so a typo there surfaces as a plugin that initialises with defaults rather than as a
build error.

## Registration order that matters

Builder registration is usually order-independent. Two exceptions:

- **single-instance must be registered first**, before any other plugin, so it can close the
  duplicate instance before the rest of the app starts doing work.
- **persisted-scope must be registered after fs.** The wrong order silently produces a scope
  that is never persisted; dev mode prints
  `Please make sure to register the 'fs' plugin before the 'persisted-scope' plugin` in the
  Rust console.

## Plugin pitfalls worth knowing before you hit them

| Plugin | The thing that surprises people |
|---|---|
| single-instance | Desktop only. Its `init` closure receives `(app, argv, cwd)` of the *second* launch; without focusing the existing window there, launching the app again looks like nothing happened. |
| deep-link | On desktop a second launch carries the URL in `argv`, so pairing it with single-instance is mandatory — enable the `deep-link` feature on `tauri-plugin-single-instance` and check `argv` in its callback. Listening also needs `core:event:default` alongside `deep-link:default`. Desktop schemes registered at runtime are not in the bundle metadata, so they only work while the app has run once. |
| persisted-scope | Restores fs **and** asset scopes the user granted through dialogs. Asset scope persistence needs the `protocol-asset` Cargo feature. |
| store | A key-value store, not a database, and writes are not automatically flushed on every set — persist deliberately and treat it as cache-like state, not as the record of truth for anything the user would mourn. |
| fs | Its permissions are separate from the asset protocol's scope. Keep `fs:deny-default` in the capability: it blocks the webview's own data directory (`$APPLOCALDATA`, `EBWebView` on Windows). |
| shell | `open` (a URL or file with the system handler) and `execute`/`spawn` (a program) are different permissions with different blast radius. Scope the allowed programs and argument patterns. |
| updater | Desktop only, and refuses unsigned artifacts unconditionally. |
| notification, global-shortcut, autostart, tray | Desktop or partially-supported surfaces; check the plugin's platform support table before designing a feature on top of one. |

Before adding a third-party plugin, read its `[package.metadata.platforms.support]` block in
`Cargo.toml` — that is where a plugin declares `full`/`partial`/`none` per platform, and it is
what the official support table is generated from.

## Bundled resources

`bundle.resources` accepts a list of files/globs, or a map of source → destination:

```json
{ "bundle": { "resources": ["templates/**/*", "dictionaries/en.dic"] } }
```

Resolve them at runtime instead of assuming a layout, because the layout differs per platform:

```rust
let path = app.path().resolve("templates/report.html", tauri::path::BaseDirectory::Resource)?;
```

If the **frontend** must read a resource, it additionally needs an fs permission scoped to
`$RESOURCE`. Note the glob difference here too: `templates/**` and `templates/**/*` do not
select the same set, and the second is what "every file underneath" means.

## Sidecars: embedding an external binary

```json
{ "bundle": { "externalBin": ["binaries/indexer", "../scripts/helper"] } }
```

Relative paths are relative to `src-tauri/`. Four rules decide whether this works:

1. **Target-triple suffix.** For `binaries/indexer`, the file on disk must be
   `src-tauri/binaries/indexer-x86_64-unknown-linux-gnu` (or the triple of the platform being
   built, `.exe` on Windows). `rustc --print host-tuple` prints the current host's triple
   (Rust 1.84+; older toolchains need `rustc -Vv | grep host`). Cross-compiling means producing
   one suffixed binary per target, so this is normally a build-script step, not a manual rename.
2. **Two different names.** Rust takes the bare filename; JavaScript takes the exact
   `externalBin` string:

```rust
use tauri_plugin_shell::{ShellExt, process::CommandEvent};

let (mut rx, mut child) = app.shell().sidecar("indexer")?.args(["--root", &root]).spawn()?;
tauri::async_runtime::spawn(async move {
    while let Some(event) = rx.recv().await {
        if let CommandEvent::Stdout(line) = event {
            // forward through a channel or an event
        }
    }
});
```

```ts
import { Command } from '@tauri-apps/plugin-shell';
const output = await Command.sidecar('binaries/indexer', ['--root', root]).execute();
```

3. **The shell plugin must be installed and initialised.** The sidecar API belongs to it, not
   to core.
4. **The permission must match the call.** `execute()` needs `shell:allow-execute`, `spawn()`
   needs `shell:allow-spawn`; both entries carry `"sidecar": true` and the `name` from
   `externalBin`. Arguments are part of the permission: `true` allows any, `false` allows none,
   and a list pins them positionally — literal strings as-is, variable ones as a
   `{ "validator": "\\S+" }` regex.

```json
{
  "permissions": [
    { "identifier": "shell:allow-execute",
      "allow": [{ "name": "binaries/indexer", "sidecar": true,
                  "args": ["--root", { "validator": "\\S+" }] }] }
  ]
}
```

The frontend must then pass **all** arguments, in exactly that order. Calling the sidecar from
Rust instead avoids the argument-pattern maintenance entirely, and is the better default when
the frontend has no reason to choose the arguments.

## Writing a plugin

Reach for a plugin when the code is genuinely reusable across apps, or when it needs native
Android/iOS implementations. Otherwise a module of commands in `src-tauri` is less machinery.

`tauri plugin new <name>` scaffolds `tauri-plugin-<name>`:

```
src/{commands.rs, desktop.rs, mobile.rs, error.rs, models.rs, lib.rs}
permissions/        # generated + hand-written permission files
android/  ios/      # optional native projects
guest-js/ dist-js/  # optional JS bindings
```

The plugin name must satisfy the identifier rules (lowercase ASCII, hyphens not leading or
trailing, no underscores or uppercase); a violation fails the build with an "identifiers can
only include lowercase ASCII…" message. Crate name is `tauri-plugin-<name>`; the permission
namespace is `<name>:` with the prefix stripped.

Lifecycle hooks on the plugin `Builder`:

| Hook | Use |
|---|---|
| `setup` | initialise native side, manage plugin state, start background tasks |
| `on_navigation` | validate or track navigation; returning `false` cancels it |
| `on_webview_ready` | per-window initialisation |
| `on_event` | `RunEvent`s, including `ExitRequested` (where `api.prevent_exit()` lives) and `Exit` for flushing state |
| `on_drop` | teardown |

A typed config is read in `setup` via `api.config()`; use `Builder::<R, Option<Config>>` when
the config is optional, or the plugin fails to initialise in apps that do not configure it.
Expose Rust APIs through an extension trait (`MyPluginExt` on `Manager`) so consumers reach the
managed struct from any `AppHandle`.

## Plugin permissions you author

Listing a command in the build script generates its permissions:

```rust
// build.rs
const COMMANDS: &[&str] = &["ping", "write_custom_file"];
```

That produces `allow-<command>` and `deny-<command>` under
`permissions/autogenerated/commands/`. `permissions/default.toml` then decides what consumers
get for free:

```toml
"$schema" = "schemas/schema.json"
[default]
description = "Default permissions for the plugin"
permissions = ["allow-ping", "allow-write-custom-file"]
```

Anything that writes, deletes, spawns or reaches the network belongs **outside** the default
set, so that enabling it is a visible decision in the consuming app's capability file. Group
related permissions into `[[set]]` entries and give every permission a description that states
the impact — that description is what a reviewer reads when auditing the capability.

Also expose the command in the JS bindings (`guest-js/index.ts`) with the plugin-qualified name
and camelCase arguments:

```ts
export async function writeCustomFile(userInput: string): Promise<string> {
  return invoke('plugin:test|write_custom_file', { userInput });
}
```

## Mobile implementations

`desktop.rs` and `mobile.rs` implement the same struct for the two worlds; `lib.rs` re-exports
whichever the target needs. Mobile commands are handled by Kotlin/Swift code registered from
`setup`. `tauri plugin android add` / `ios add` bootstrap those projects for an existing
plugin. A plugin without a mobile implementation should declare `level = "none"` for that
platform rather than failing at runtime.

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2, full-stack-skills-tauri -->
