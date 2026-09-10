# Events, channels and evaluating JavaScript

Verified against: Tauri 2.x

## Contents

- Choosing between command, channel and event
- Emitting from Rust
- Listening, targets and the catch-all
- Channels
- Evaluating JavaScript directly

## Choosing between command, channel and event

| Need | Use |
|---|---|
| Frontend asks, Rust answers | command |
| Rust pushes ordered, high-volume data (download progress, process output) | channel |
| Rust notifies whoever cares (a file changed, the tray was clicked) | event |

Events are the weakest of the three by design: no type support, JSON-string payloads, no
coverage by the capabilities system, and no back-pressure. Reaching for an event because it is
easier to wire than a channel is how a progress bar ends up dropping updates under load.

## Emitting from Rust

```rust
use tauri::{AppHandle, Emitter};

#[tauri::command]
fn watch_project(app: AppHandle, path: String) {
    app.emit("project-changed", &path).unwrap();          // every listener
    app.emit_to("quicknote", "project-changed", &path).unwrap();  // one webview label
}
```

- `emit` is global: it reaches **all** listeners.
- `emit_to(label, ...)` reaches only listeners registered by that webview, and those events are
  **not** delivered to plain global listeners.
- `emit_filter` takes a predicate over `EventTarget` when several specific labels should get it.
- The payload must be `Serialize + Clone`. Use a struct with
  `#[serde(rename_all = "camelCase")]` rather than a positional tuple — the frontend reads
  these by field name.

## Listening, targets and the catch-all

```ts
import { listen } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';

// listen() hears every event regardless of target unless a target option is given
const unlisten = await listen<string>('project-changed', (e) => render(e.payload));

// a webview-window listener only hears events emitted to its own target
const win = getCurrentWebviewWindow();
const unlistenWin = await win.listen<string>('project-changed', (e) => render(e.payload));

// explicit catch-all, including webview-targeted events
await listen('state-changed', handler, { target: { kind: 'Any' } });
```

- `listen()` returns a promise for an `unlisten` function. Call it when the component unmounts
  or the listener survives every navigation and fires several times per event.
- On the Rust side, `listen` respects targets and `listen_any` is the catch-all.
- Event names are free-form strings with no namespace. Prefix them per feature
  (`updater:progress`, `project:changed`) so a rename is greppable.

## Channels

A channel is a typed, ordered, one-way pipe created by the frontend and passed into a command.
It is what the official plugins use internally for download progress, child-process output and
WebSocket messages.

```rust
use tauri::ipc::Channel;

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase", rename_all_fields = "camelCase",
        tag = "event", content = "data")]
enum IndexEvent {
    Started { total: usize },
    Progress { done: usize },
    Finished,
}

#[tauri::command]
async fn reindex(root: String, on_event: Channel<IndexEvent>) -> Result<(), Error> {
    let files = collect(&root)?;
    on_event.send(IndexEvent::Started { total: files.len() })?;
    for (i, f) in files.iter().enumerate() {
        index(f)?;
        on_event.send(IndexEvent::Progress { done: i + 1 })?;
    }
    on_event.send(IndexEvent::Finished)?;
    Ok(())
}
```

```ts
import { invoke, Channel } from '@tauri-apps/api/core';

type IndexEvent =
  | { event: 'started'; data: { total: number } }
  | { event: 'progress'; data: { done: number } }
  | { event: 'finished' };

const onEvent = new Channel<IndexEvent>();
onEvent.onmessage = (m) => { if (m.event === 'progress') setDone(m.data.done); };

await invoke('reindex', { root, onEvent });
```

The tagged enum plus the discriminated union is the pattern worth copying: it makes the
frontend's `switch` exhaustive, and adding a variant becomes a compile error on both sides.

Streaming bytes rather than progress structs works the same way with `Channel<&[u8]>`; send
fixed-size chunks and treat a zero-length read as the end.

## Evaluating JavaScript directly

`webview.eval("...")` runs a string in the webview. Reserve it for setup that has no listener
yet (injecting a theme class before first paint) and never build it by string concatenation
from Rust data — that is a script injection into your own app. When Rust values must be
embedded, serialise them properly (the `serialize-to-javascript` crate exists for this) or use
an event instead.

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2 -->
