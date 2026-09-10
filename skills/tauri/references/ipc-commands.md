# IPC commands

Verified against: Tauri 2.x

## Contents

- Registration rules
- Arguments and the camelCase boundary
- Return values, binary payloads
- Error types
- Async commands, threads and borrowed arguments
- Managed state
- Injected parameters and raw requests
- Restricting which commands exist
- Typed bindings

## Registration rules

```rust
// src-tauri/src/commands.rs
#[tauri::command]
pub fn load_project(project_path: String) -> Result<Project, Error> { /* ... */ }
```

```rust
// src-tauri/src/lib.rs
mod commands;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::load_project,
            commands::list_recent,
            commands::export_report,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- **One `invoke_handler` per app.** Calling it twice does not append — only the last call is
  used, and the commands from the earlier call fail at runtime with "Command not found". This
  is the single most common cause of that error.
- The module path is not part of the command name: `commands::load_project` is still invoked as
  `invoke('load_project')`.
- Commands declared directly in `lib.rs` cannot be `pub` (macro limitation). Either keep them
  private in `lib.rs` or move them into a module and make them `pub` there.
- Command names must be unique across the app, including against plugin commands.

## Arguments and the camelCase boundary

Arguments arrive as one JSON object whose keys are **camelCase**:

```rust
#[tauri::command]
fn load_project(project_path: String, force_reload: bool) { }
```

```ts
await invoke('load_project', { projectPath: path, forceReload: true });
```

- A key that does not match deserialises as missing: `Option<T>` becomes `None`, everything
  else is a command error. This looks like "the argument arrives as undefined".
- To take snake_case keys instead, declare it:
  `#[tauri::command(rename_all = "snake_case")]`.
- Any argument type works as long as it implements `serde::Deserialize`. Prefer one
  `#[derive(Deserialize)] struct XArgs` over five positional-feeling parameters once there are
  more than three.
- Enums crossing the boundary need an explicit representation (`#[serde(tag = "type")]` or
  similar) to stay JSON-safe and matchable on the TypeScript side.

## Return values, binary payloads

Any `serde::Serialize` value can be returned and resolves the `invoke` promise. That value is
**JSON-encoded**, which is why returning a file or an HTTP body as `Vec<u8>` is slow and
memory-hungry. For binary data:

```rust
use tauri::ipc::Response;

#[tauri::command]
fn read_file(path: std::path::PathBuf) -> Result<Response, Error> {
    Ok(Response::new(std::fs::read(path)?))
}
```

For data that arrives in pieces, stream it through a `tauri::ipc::Channel` instead of
returning one large value.

## Error types

Make the error a real type. `Result<T, String>` compiles but erases every distinction the
frontend could branch on:

```rust
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error("project {0} is not inside the workspace")]
    OutsideWorkspace(String),
}

// The error type must implement Serialize itself; thiserror does not provide it.
impl serde::Serialize for Error {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(self.to_string().as_ref())
    }
}
```

When the frontend has to react differently per error, serialise a tagged shape instead of a
bare string:

```rust
#[derive(serde::Serialize)]
#[serde(tag = "kind", content = "message", rename_all = "camelCase")]
enum ErrorKind {
    Io(String),
    OutsideWorkspace(String),
}

impl serde::Serialize for Error {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        let message = self.to_string();
        match self {
            Self::Io(_) => ErrorKind::Io(message),
            Self::OutsideWorkspace(_) => ErrorKind::OutsideWorkspace(message),
        }
        .serialize(s)
    }
}
```

The frontend then gets `{ kind, message }` and can `switch` on `kind`:

```ts
invoke('load_project', { projectPath }).catch((e: { kind: string; message: string }) => {});
```

## Async commands, threads and borrowed arguments

- A command **without** `async` executes on the **main thread**, unless declared
  `#[tauri::command(async)]`. Blocking work there freezes the window; this is not a
  "might be slow" issue, it is a frozen UI.
- An `async` command is spawned onto the async runtime (`async_runtime::spawn`).
- An `async` command **cannot take borrowed arguments**. Two supported ways out:
  1. use an owned type — `&str` → `String`;
  2. wrap the return type in `Result<T, E>`. This works for **all** types, including
     `State<'_, T>`, which has no owned equivalent.

```rust
// Compiles: owned argument.
#[tauri::command]
async fn search(query: String) -> Vec<Hit> { /* ... */ }

// Compiles: borrowed State plus Result return.
#[tauri::command]
async fn search_db(query: String, db: tauri::State<'_, Db>) -> Result<Vec<Hit>, Error> {
    /* ... */
}

// Does not compile: borrowed &str, and borrowed State without Result.
#[tauri::command]
async fn search_bad(query: &str, db: tauri::State<'_, Db>) -> Vec<Hit> { /* ... */ }
```

Do not hold a `std::sync::Mutex` guard across an `.await`: either finish with the guard in a
scope that ends before the await, or use an async mutex when the guard genuinely must live
across it. The async mutex is for guarding I/O resources (a database connection), not a
general upgrade.

## Managed state

```rust
use std::sync::Mutex;
use tauri::Manager;

#[derive(Default)]
struct AppStateInner { recent: Vec<String> }
type AppState = Mutex<AppStateInner>;

// in run():
.setup(|app| { app.manage(AppState::default()); Ok(()) })

#[tauri::command]
fn push_recent(path: String, state: tauri::State<'_, AppState>) -> usize {
    let mut state = state.lock().unwrap();
    state.recent.push(path);
    state.recent.len()
}
```

- The `State` type parameter must name **exactly** what was passed to `.manage()`. Asking for
  `State<AppStateInner>` when `Mutex<AppStateInner>` was managed is a **runtime panic**, not a
  compile error. The type alias above is the cheapest way to make the two sides agree.
- Do not add `Arc`: `State` already shares ownership. When state must move into a thread,
  clone the `AppHandle` (deliberately cheap) and call `handle.state::<AppState>()` there.
- Outside commands — window event handlers, spawned tasks — reach state through any `Manager`
  implementor: `app_handle.state::<AppState>()`.
- Mutating through a clone (`let mut v = state.recent.clone(); v.push(..)`) compiles, changes
  nothing, and is a frequent silent bug: it is the reason a "saved" value never appears.

## Injected parameters and raw requests

A command can additionally take, in any order:

| Parameter | Use |
|---|---|
| `tauri::State<'_, T>` | managed state |
| `tauri::AppHandle` | paths, emitting events, plugin extension traits |
| `tauri::WebviewWindow` | the window that invoked (its `label()` identifies the caller) |
| `tauri::ipc::Channel<T>` | streaming responses |
| `tauri::ipc::Request` | raw body plus request headers |

`Request` is how an upload avoids base64: the frontend passes an `ArrayBuffer`/`Uint8Array` as
the payload and headers as the third argument.

```rust
#[tauri::command]
fn upload(request: tauri::ipc::Request) -> Result<(), Error> {
    let tauri::ipc::InvokeBody::Raw(bytes) = request.body() else {
        return Err(Error::ExpectedRawBody);
    };
    let Some(auth) = request.headers().get("Authorization") else {
        return Err(Error::MissingHeader("Authorization"));
    };
    Ok(())
}
```

```ts
await invoke('upload', new Uint8Array([1, 2, 3]), { headers: { Authorization: 'apikey' } });
```

Commands written generically over the runtime (`AppHandle<R>`, `WebviewWindow<R>` with
`R: Runtime`) are what makes them testable against `tauri::test::MockRuntime`.

## Restricting which commands exist

Every command registered through `invoke_handler` is callable from **all** windows by default.
To narrow the set that exists at all, declare it in the build script:

```rust
// src-tauri/build.rs
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["load_project"])),
    )
    .unwrap();
}
```

Capabilities then decide which window may call which of those. Without this, a capability
cannot restrict your own commands — only plugin and `core:` ones.

## Typed bindings

Hand-writing the TypeScript signature for every command drifts. Two workable approaches:

- keep one module that owns every `invoke` call and exports typed functions — no generation
  step, and the drift is at least confined to one file;
- generate bindings from the Rust definitions (`tauri-specta`) and treat the generated file as
  derived output, regenerated only when the IPC surface intentionally changes. Commands
  returning `tauri::ipc::Response` cannot be generated this way (the body is not a typed
  value), so they need a separate handler route and a small handwritten wrapper.

Prefer the first unless the command surface is large enough that the generation step pays for
itself.

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2, pinkpixel-tauri, epicenter-tauri -->
