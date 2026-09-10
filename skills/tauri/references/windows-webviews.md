# Windows, webviews, tray and menus

Verified against: Tauri 2.x

## Contents

- Three places a window can be defined
- Labels
- Custom titlebars and dragging
- Transparency and platform limits
- Splashscreen
- Tray icon and menus
- Multiwebview
- Which webview the app actually runs on

## Three places a window can be defined

| Where | Use it for |
|---|---|
| `app.windows` in `tauri.conf.json` | windows that always exist at startup |
| `WebviewWindowBuilder` in Rust | windows created conditionally, per platform, or after setup work |
| `WebviewWindow` in JavaScript | windows the user opens from the UI |

Prefer the config for the main window and Rust for everything conditional. Creating a window
from JavaScript requires giving that window's capability the window-creation permission, which
is exactly the permission a compromised webview would want — keep it out of low-privilege
windows.

```rust
use tauri::{WebviewUrl, WebviewWindowBuilder};

let win = WebviewWindowBuilder::new(app, "settings", WebviewUrl::App("settings.html".into()))
    .title("Settings")
    .inner_size(560.0, 420.0)
    .resizable(false)
    .build()?;
```

A window created with `visible: false` and shown after its content is ready avoids the white
flash; that is also the mechanism behind a splashscreen.

## Labels

The label is the window's identity everywhere: `get_webview_window("main")`, `emit_to`, and —
most importantly — the `windows` array of every capability. Renaming a label silently drops the
permissions of the old one. Labels are not titles and are not user-visible; treat them as
stable identifiers chosen once.

## Custom titlebars and dragging

Set `decorations: false`, then build the titlebar in HTML. Three things are easy to miss:

- `data-tauri-drag-region` works **only on the element it is set on**, never on its children.
  That is deliberate — it is what keeps buttons and inputs inside the titlebar clickable — so
  a drag region is one dedicated element next to the controls, not a wrapper around them. For
  fully custom drag behaviour, listen for the event yourself and call `startDragging()`.
- On Windows, `*[data-tauri-drag-region] { app-region: drag; }` is what makes the region work
  for touch and pen input.
- The window controls call core window commands, so the capability needs them explicitly:
  `core:window:allow-minimize`, `core:window:allow-toggle-maximize`,
  `core:window:allow-close`, and `core:window:allow-start-dragging` for the drag region.
  `core:window:default` alone does not include them.

Also add `user-select: none` to the titlebar or dragging selects the text under the cursor.

On macOS a fully custom titlebar loses system behaviours (window snapping and alignment). The
alternative that keeps them is a transparent titlebar: `titleBarStyle: "Overlay"` plus
`hiddenTitle: true`, and a window background colour set so the overlay area matches the app.

## Transparency and platform limits

`transparent: true` needs the `macos-private-api` feature on macOS (which is a private API —
App Store submissions are rejected with it), and on Linux behaviour depends on the compositor.
Anything visual that depends on transparency or blur has to be checked on all three desktop
platforms; there is no cross-platform guarantee here.

## Splashscreen

The pattern is two windows: a small `splashscreen` window visible at startup and the main
window created with `visible: false`. Setup work runs in the Rust `setup` hook or in a command
the splash window invokes; when it finishes, show the main window and close the splash. Keep
the "close the splash" step in Rust — if the frontend owns it and fails to load, the app is
stuck on the splash with no way out.

## Tray icon and menus

Tray and menu construction happen in Rust (`TrayIconBuilder`, `MenuBuilder`,
`PredefinedMenuItem`), and both need permissions when the frontend interacts with them
(`core:tray:*`, `core:menu:*`). Points worth knowing:

- Build the tray in `setup`, not lazily on demand, so its icon and menu exist before the first
  user interaction.
- The context menu opens on **left** click by default. `show_menu_on_left_click(false)` in Rust
  (`menuOnLeftClick: false` in JavaScript) is what frees the left click for an action such as
  toggling the main window.
- The tray **click event is not emitted on Linux** at all, although the icon appears and the
  right-click context menu works. Any behaviour attached to a tray click must therefore have a
  menu-item equivalent, or it simply does not exist for Linux users.
- `MenuBuilder` items you want to be reachable by keyboard need accelerators; predefined items
  (copy, paste, quit) already carry the platform-correct ones, so prefer them over hand-rolled
  equivalents.

Closing the last window normally exits the app, which is wrong for a tray app. Intercept it:
handle `RunEvent::ExitRequested` and call `api.prevent_exit()`, and hide rather than close the
window on the close request.

## Multiwebview

Multiple webviews inside one window exist behind the `unstable` Cargo feature. The v2 rename
that came with it is visible in every codebase: the Rust `Window` type became `WebviewWindow`
and `get_window` became `get_webview_window`; on the JS side `@tauri-apps/api/window` became
`@tauri-apps/api/webviewWindow`. Unless the app genuinely needs several webviews in one window,
stay on `WebviewWindow` and leave the feature off.

## Which webview the app actually runs on

The frontend runs on the OS webview, so "works on my machine" is per platform:

| Platform | Engine | Consequence |
|---|---|---|
| Windows | WebView2 (Chromium, self-updating; preinstalled on Windows 11, bootstrapped by the installer on older versions) | most permissive; feature checks pass here first |
| macOS / iOS | WKWebView, updated only with the OS | an old but supported macOS ships an old WebKit; unsupported macOS versions get no WebKit updates at all |
| Linux | `webkit2gtk`, whatever the distribution ships | the widest spread and usually the oldest engine |
| Android | system Android WebView (Chromium), provider-dependent | version depends on the device's WebView provider |

The practical rule: pick the minimum supported OS versions first, then check features against
the WebKit version those ship (the macOS/Safari mapping is in the official webview-versions
reference), and test on Linux before shipping — a CSS or JS feature that works on Windows and
macOS can still be missing in `webkit2gtk`. `tauri info` prints the local webview version.

<!-- sources: tauri-docs, hairyf-tauri, nodnarbnitram-tauri-v2, full-stack-skills-tauri -->
