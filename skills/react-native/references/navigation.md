# Navigation

Verified against: Expo Router 6 (SDK 54–57), React Navigation 7.

## Contents

- [Which router owns the app](#which-router-owns-the-app)
- [Rules that hold in both](#rules-that-hold-in-both)
- [Expo Router](#expo-router)
- [React Navigation 7](#react-navigation-7)
- [Safe areas](#safe-areas)
- [Deep links and universal links](#deep-links-and-universal-links)
- [Old patterns](#old-patterns)

## Which router owns the app

Read `package.json`. `expo-router` present → Expo Router, and every navigation
change goes through the `app/` directory. Only `@react-navigation/*` → React
Navigation, configured in code. Never introduce the second one alongside the
first: two navigation containers means two histories, and the back gesture
resolves against whichever mounted last.

## Rules that hold in both

- **Native stack, not the JavaScript stack.** `@react-navigation/native-stack`
  (and Expo Router's `Stack`, which uses it) drives real
  `UINavigationController` / Fragment transitions. `@react-navigation/stack`
  re-implements them in JavaScript, so a busy JS thread stutters the transition
  and the back gesture.
- **Native tabs where the platform look matters.** Native bottom tabs render the
  platform tab bar, including its blur, haptics and long-press behaviour;
  the JavaScript tab bar approximates them.
- **A screen is mounted, not constructed, on navigation.** Anything expensive at
  module scope in a screen file runs at startup, not on first visit — put it
  inside the component or behind a lazy import.
- **Params carry identifiers, not objects.** They are serialized into
  navigation state (and into a URL under Expo Router); pass an id and read the
  entity from the store or cache.
- **Do not navigate from a render path.** Redirects belong in an effect, a route
  guard, or the router's own redirect primitive; navigating during render
  produces a double-push or a state update on an unmounted screen.

## Expo Router

- Routes live in `app/`. Nothing else does: no components, hooks, types or test
  files there, because every file in `app/` is a route.
- One route must match `/` (it may sit inside a group).
- `_layout.tsx` defines the navigator for its directory. A layout is always
  native — it cannot be a DOM component.
- File names are kebab-case with no special characters; a rename is a route
  change, so delete the old file rather than leaving both.
- Groups `(name)` organise without adding a path segment; dynamic routes are
  `[id].tsx`, catch-alls `[...rest].tsx`, and `+not-found.tsx` is the fallback.
- Navigate with `<Link href>` for anything a user taps, and `useRouter()`
  (`push` / `replace` / `back`) for programmatic moves. Read params with
  `useLocalSearchParams()`.
- On SDK 56+, import React Navigation APIs from `expo-router/react-navigation`
  (covering `native`, `core`, `elements`, `routers`) rather than
  `@react-navigation/*` directly — the direct import can resolve a second copy
  of the navigator and its context.
- Prefer the router's own native primitives for platform polish: link previews
  and context menus on long press, native tabs, and the header/search-bar
  configuration exposed by the stack, rather than hand-built equivalents.

## React Navigation 7

- Two configuration styles exist: the static API (a route tree object) and the
  dynamic API (`<Stack.Screen>` components). Follow whichever the project
  already uses; for a new app prefer the static API, which gives typed routes
  and linking config without a separate type declaration.
- Type the navigator once and let screens read their props from it. Untyped
  `navigation.navigate('Whatever')` is the most common runtime navigation bug.
- Header configuration belongs to the navigator (`options` / `screenOptions`),
  not to a `View` the screen renders. A hand-drawn header loses the platform
  back gesture, large-title behaviour and safe-area handling.
- A modal is a presentation mode on the native stack
  (`presentation: 'modal'` / `'formSheet'`), not a full-screen `Modal`
  component inside a screen — the presentation mode keeps the swipe-to-dismiss
  and the correct status-bar treatment.

## Safe areas

- Insets come from `react-native-safe-area-context` (`useSafeAreaInsets`, or
  `SafeAreaView` from that package) or from the navigator, never from a
  hardcoded padding. Notch, dynamic island, status bar and home indicator all
  differ per device and orientation.
- A scrollable respects the safe area through `contentInsetAdjustmentBehavior`
  or content padding, not by padding the scroll container — padding the
  container clips the scroll indicators and leaves a dead band at the top.
- When a navigator already applies insets, applying them again in the screen
  doubles the gap. Check what the navigator does before adding padding.
- The core `SafeAreaView` from `react-native` only ever handled iOS; do not use
  it for cross-platform inset handling.

## Deep links and universal links

- Declare the app's custom scheme in the app config (Expo) or the platform
  project, and keep it identical across environments — a scheme mismatch is
  invisible until a link opens the wrong build.
- Universal/app links need platform-side association files hosted on the
  domain (`apple-app-site-association` for iOS, `assetlinks.json` for Android)
  plus the matching capability/intent filter. The file contents and signing
  fingerprints are platform work: the `apple` and `android` skills own them.
- The router's linking configuration maps an incoming URL to a route. Under
  Expo Router the file tree *is* that mapping; under React Navigation it is the
  `linking` config, which must be kept in sync with the navigator by hand.
- Test with a real link rather than in-app navigation:

```bash
xcrun simctl openurl booted "acme://order/42"
adb shell am start -a android.intent.action.VIEW -d "acme://order/42"
```

- Cold-start deep links arrive before the first screen mounts. A guard that
  redirects unauthenticated users must tolerate an initial route it did not
  choose, or the link is swallowed on first launch and works on the second.

## Old patterns

<details>
<summary><code>createStackNavigator</code> from <code>@react-navigation/stack</code></summary>

The JavaScript stack still exists and still works; it is the right choice only
when a transition genuinely cannot be expressed natively (a fully custom
interpolated animation across screens). Everything else — including "we need a
custom header" — is achievable on the native stack. Migrating is usually an
import change plus removing hand-rolled gesture code.

</details>

<details>
<summary>Direct <code>@react-navigation/*</code> imports inside an Expo Router app</summary>

Correct before SDK 56 and still what most tutorials show. From SDK 56 the
supported path is `expo-router/react-navigation`; a direct import risks a second
navigator instance with its own context, which surfaces as hooks returning
`undefined` inside screens that look correctly nested.

</details>

<!-- sources: expo-official, callstack-rn, vercel-rn-rules, expo-docs -->
