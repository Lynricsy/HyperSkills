# UIKit and AppKit interop

Verified against: iOS 26.6 / macOS 26.6 SDK; iOS 27 RC.

SwiftUI is the default. This reference covers the seams: hosting in both directions, the
UIKit lifecycle work that is now mandatory, macOS scenes and window styling, and the
imperative glass APIs.

## Contents

- [Hosting SwiftUI in UIKit and AppKit](#hosting-swiftui-in-uikit-and-appkit)
- [Wrapping UIKit and AppKit in SwiftUI](#wrapping-uikit-and-appkit-in-swiftui)
- [Scene lifecycle is mandatory](#scene-lifecycle-is-mandatory)
- [Multi-window shared-state APIs](#multi-window-shared-state-apis)
- [macOS scenes](#macos-scenes)
- [macOS window styling](#macos-window-styling)
- [Glass in UIKit](#glass-in-uikit)
- [Glass in AppKit](#glass-in-appkit)

## Hosting SwiftUI in UIKit and AppKit

- `UIHostingController` / `NSHostingController` for a whole screen;
  `UIHostingConfiguration` for a `UICollectionViewCell` or `UITableViewCell` content view,
  which is far cheaper than a nested hosting controller per cell.
- A hosting controller added as a child needs the full child-VC dance —
  `addChild`, `didMove(toParent:)`, and constraints — or layout and safe-area propagation
  silently misbehave.
- `sizingOptions` on `UIHostingController` (iOS 16+) lets the SwiftUI content drive the
  preferred content size; without it the controller keeps whatever frame you gave it.
- `safeAreaRegions` controls whether the hosted view respects the container's safe area.
  Fighting inset duplication with manual padding is the usual symptom of the wrong setting.
- Passing data in: hold an `@Observable` model outside the hosting controller and inject it
  with `.environment(_:)` on the root view. Rebuilding the root view to push new values
  discards SwiftUI state.

## Wrapping UIKit and AppKit in SwiftUI

- `UIViewRepresentable` / `NSViewRepresentable` for views,
  `UIViewControllerRepresentable` / `NSViewControllerRepresentable` for controllers.
- `makeCoordinator()` owns delegates and targets. A delegate assigned without a coordinator
  keeping it alive is deallocated immediately.
- `updateUIView(_:context:)` runs on every SwiftUI update. Guard writes: assigning the same
  value back to a UIKit property can trigger a delegate callback that mutates SwiftUI state,
  which triggers another update. That loop is the classic representable freeze.
- Check `context.transaction.animation` before animating inside a representable, so the
  wrapped view follows the ambient animation rather than inventing its own.
- (iOS 26+) A native `WebView` removes the most common reason to write a representable at
  all. Check for a native equivalent before wrapping.
- (iOS 26+) UIKit and AppKit lifecycle apps can request SwiftUI-only scene types such as
  `MenuBarExtra` via `UIApplication.shared.activateSceneSession(for:errorHandler:)`.

## Scene lifecycle is mandatory

**As of iOS 27, apps built against the SDK that have not adopted `UISceneDelegate` crash at
launch.** The system dispatches foreground and background transitions per scene, so an app
implementing only `UIApplicationDelegate` lifecycle methods misses them.

Detection: no `UIApplicationSceneManifest` in Info.plist, no `configurationForConnecting`
in the app delegate, and no type conforming to `UIWindowSceneDelegate`. Any one of those
present means the migration is at least partly done — check before generating boilerplate.

Migration order matters. Add `UIApplicationSceneManifest` with `UISceneConfigurations`
first: without it the system ignores a `SceneDelegate` entirely. Then move window creation
to `scene(_:willConnectTo:options:)` using `UIWindow(windowScene:)` rather than
`UIWindow(frame: UIScreen.main.bounds)`. Then move all four lifecycle callbacks
(`didBecomeActive`, `willResignActive`, `didEnterBackground`, `willEnterForeground`)
together — moving some and leaving others produces an app that half-responds.
One-time app setup stays in `didFinishLaunchingWithOptions`; per-scene setup moves.

Apple's TN3187 is the canonical write-up.

## Multi-window shared-state APIs

The same modernisation replaces globals that assume one window:

| Legacy | Replacement |
|---|---|
| `UIScreen.main.scale` inside a view or view controller | `traitCollection.displayScale` |
| `UIScreen.main.bounds` for layout | the view's own bounds, or the window scene's `coordinateSpace` |
| `UIWindow(frame: UIScreen.main.bounds)` | `UIWindow(windowScene:)` |
| `interfaceOrientation` for layout decisions | size classes, or comparing the window's width and height |
| symmetric safe-area assumptions | `safeAreaInsets` / `safeAreaLayoutGuide` per edge |

Two rules that keep these migrations safe:

- **Never substitute another global.** If no local object is in scope, add a parameter and
  deprecate the old method rather than reaching for `UIApplication.shared` or
  `UIDevice.current`.
- **Stay in scope.** Change only the lines using the API you were asked about. Do not fix
  adjacent deprecations, reformat, or delete surrounding `respondsToSelector` checks,
  nil-guards, or `@available` branches — each exists for an independent reason.

Inside `layoutSubviews`, `draw(_:)`, `updateConstraints`, or `viewIsAppearing`, a
`displayScale` substitution needs no change-observation registration; UIKit already calls
those on trait change. A value cached into a stored property does need it.

## macOS scenes

| Scene | Floor | Notes |
|---|---|---|
| `WindowGroup` | macOS 11 | Multiple instances, tabbing, automatic Window-menu commands |
| `Window` | macOS 13 | Single instance; the app quits when it closes |
| `UtilityWindow` | macOS 15 | Floating palette; receives `FocusedValues` from the active main window |
| `Settings` | macOS 11 | The Cmd-comma preferences window; `SettingsLink` (macOS 14) opens it |
| `MenuBarExtra` | macOS 13 | Persistent menu-bar item; `.menuBarExtraStyle(.window)` for a popover-style panel |
| `DocumentGroup` | macOS 11 | Document commands and multiple document windows |

`Settings` content is usually a `TabView` of `Form`s constrained with
`.frame(maxWidth:minHeight:)` — an unconstrained settings window sizes badly. On iOS 27+,
prefer `ReadableDocument` / `WritableDocument` over `FileDocument` for new document apps.

## macOS window styling

- `.windowStyle(.hiddenTitleBar)` and `.windowToolbarStyle(.unified(showsTitle:))` shape
  the chrome; `.containerBackground(_:for: .window)` fills behind it.
- `.defaultSize(width:height:)`, `.defaultPosition(_:)`, and
  `.windowResizability(.contentSize)` set initial geometry — all are *defaults*, overridden
  by restored state.
- `.commands { }` with `CommandGroup(replacing:)` / `after:` is how menu items are added;
  `CommandMenu` adds a whole top-level menu. Menu commands read state through
  `@FocusedValue`, which is why focused values exist.
- `@Environment(\.appearsActive)` (macOS 10.15, iOS 18 — back-deployed, not a WWDC26 API)
  dims inactive-window chrome. `ControlActiveState` is deprecated at macOS 27.
- Mac control metrics are much smaller than iOS: the 44 pt touch minimum does not apply,
  and copying it produces oversized chrome. Standard regular-size controls are around 28 pt.

## Glass in UIKit

Every call site needs `#available(iOS 26.0, *)` — `UIGlassEffect` does not exist below 26,
so an ungated reference is a compile error, not a runtime fallback.

```swift
if #available(iOS 26.0, *) {
    let effect = UIGlassEffect()
    effect.tintColor = .systemBlue
    effect.isInteractive = true                 // only on genuinely interactive surfaces

    let effectView = UIVisualEffectView(effect: effect)
    effectView.cornerConfiguration = .capsule() // NOT layer.cornerRadius
    view.addSubview(effectView)
    effectView.contentView.addSubview(label)    // NOT effectView.addSubview(label)
}
```

- Glass is an **effect** hosted by an ordinary `UIVisualEffectView`, not a view subclass.
- `UIGlassEffect()` takes no arguments; configure `tintColor` and `isInteractive`
  afterwards. `UIGlassEffect(glass:isInteractive:)` is a fabricated initialiser.
- Content goes in `contentView`. Added directly to the effect view, it sits under the
  material.
- Round with `UIView.cornerConfiguration` built from `UICornerConfiguration` factories
  (`.corners(radius:)`, `.capsule(maximumRadius:)`, the per-corner and uniform families).
  `layer.cornerRadius` stopped shaping glass effect views during the iOS 26 beta cycle, and
  Apple's Xcode-bundled UIKit glass documentation is stale on this point.
  `UIViewCornerConfiguration(corners:cornerRadius:)` is not a type.
- `UIGlassContainerEffect` is the peer of `GlassEffectContainer`.

## Glass in AppKit

- `NSGlassEffectView` hosts the material; put content in its `contentView`.
- `NSGlassEffectContainerView` groups siblings, and its `spacing` deliberately defaults to
  `0` — shared sampling without merging. Do not copy an iOS spacing value into it.
- Hover response at the AppKit layer is hand-rolled with `NSTrackingArea`. That is a
  statement about `NSGlassEffectView`, not about SwiftUI: SwiftUI's `Glass.interactive()`
  works on macOS and Apple tuned it for the pointer.
- Tahoe window chrome adopts glass by recompiling. Delete pre-26 titlebar and toolbar
  customisation before adding anything; layered legacy chrome defeats the material.

<!-- sources: apple-xcode27, avdlee-swiftui, yordi-liquid-glass, apple-docs -->
