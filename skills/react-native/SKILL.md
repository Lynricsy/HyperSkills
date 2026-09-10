---
name: react-native
description: "Engineers React Native and Expo apps at the runtime and native boundary: New Architecture (Fabric, Turbo Native Module specs, codegen, the interop layer), Hermes and startup/TTI, list and scroll performance with FlashList, native navigators under Expo Router or React Navigation 7, app config and prebuild, EAS Build and EAS Update channels and runtime versions, React Native and Expo SDK upgrades through Upgrade Helper and the Strict TypeScript API, brownfield integration into an existing native app, and on-device profiling. Use when a task mentions react-native, Expo, EAS, Metro, Hermes, FlashList, TurboModule, expo-router, pod install in an app, or a React Native version bump. Do not use for React component, hook or rendering rules, for the Swift/Objective-C or Kotlin/Java body of a native module, or for Flutter."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# react-native

Paths below are relative to this skill's directory.

## Scope

React Native and Expo application work: the runtime (New Architecture, Hermes,
threads), rendering and list performance, navigation, the JavaScript side of the
native boundary (codegen specs, module registration, config plugins), Expo app
config and EAS Build/Update, version upgrades, brownfield integration, and
device-level debugging and profiling.

Not covered — do not answer from this skill:

- React itself: component design, hooks, state selection, memoization policy,
  Server Components, Next.js. Use the `react` skill.
- The body of a native implementation. The Swift/Objective-C side is the `apple`
  skill; the Kotlin/Java side is the `android` skill. This skill stops at the
  contract: the spec, the registered name, the threading and nullability
  guarantees, and the build wiring.
- Flutter and Dart. Use the `flutter` skill.
- Visual and UX design decisions — palette, type scale, motion feel. Use the
  `frontend-design` skill.
- React Native for TV, Windows and macOS out-of-tree platforms, and web output
  from `react-native-web`.

## Core rules

Each rule is an invariant: violating it is a bug, a rejected build, or a
measurable regression.

1. Detect the stack before advising. Read `package.json` (`react-native` and
   `expo` versions, `expo-router` vs `@react-navigation/*`, the
   `@shopify/flash-list` major), the app config (`app.json` / `app.config.*`),
   `eas.json`, and whether `ios/` and `android/` are committed. Almost every
   rule below is version- or framework-gated.
2. The New Architecture is the default from 0.76 and the only runtime from 0.82.
   Do not propose enabling it, do not offer `newArchEnabled=false` as an escape,
   and do not design new code around `NativeModules` and the bridge.
3. An unmigrated legacy module keeps working through the interop layer, so
   migrating it is about codegen type safety and lazy loading, not about fixing a
   crash. The interop layer does not cover custom Shadow Nodes or concurrent
   features — a component that needs either has to become a real Fabric native
   component.
4. A Turbo Native Module *is* its spec: a TypeScript or Flow file whose name
   carries the `Native` prefix, declaring `interface Spec extends TurboModule`
   and exporting it through `TurboModuleRegistry`. The exported name must match
   the name the native side registers, or lookup fails at runtime.
5. Codegen only runs when `package.json` has a `codegenConfig` block
   (`name`, `type`, `jsSrcsDir`, and `android.javaPackageName` for modules).
   Without it, iOS `pod install` and the Android build generate nothing and the
   native class has no interface to conform to.
6. `TurboModuleRegistry.getEnforcing` throws when the module is absent, `get`
   returns `null`. Choose per module and handle the consequence; mixing them
   produces a module that is optional in one file and mandatory in another.
7. Synchronous spec methods block the JavaScript thread for their whole
   duration. Keep them trivial and allocation-free; anything doing I/O, disk
   access or real computation returns a `Promise` and runs on a module-owned
   queue. Never call a synchronous bridging method from a render path.
8. Any list that can exceed one screen is virtualized — `FlashList`, or
   `FlatList` when FlashList's requirements do not fit. A `ScrollView` with
   `items.map()` mounts and lays out every row before the first frame.
9. FlashList v2 measures items itself: `estimatedItemSize`,
   `estimatedListSize` and `estimatedFirstItemOffset` are v1 API and inert
   there, and v2 requires the New Architecture. Read the installed major before
   suggesting or flagging any of them.
10. A list with more than one row shape needs `getItemType`. Without it the
    recycler reuses a cell across incompatible layouts, which costs more than
    the recycling saves.
11. `renderItem`, `keyExtractor` and per-row callbacks defined inline in the
    parent get a new identity on every parent render, so every visible row
    re-renders. Hoist them or memoize them, and derive keys from stable ids —
    never from the array index, which breaks recycling on reorder.
12. Use native navigators: `@react-navigation/native-stack` or Expo Router's
    `Stack` (native by default), and native bottom tabs. `@react-navigation/stack`
    re-implements platform transitions in JavaScript and drops frames under load.
13. In an Expo Router app on SDK 56+, import React Navigation APIs from
    `expo-router/react-navigation`, never from `@react-navigation/*` directly —
    a direct import can bind a second navigator instance.
14. Every string renders inside `<Text>`; a bare string under a `View` throws.
    Styles do not cascade or inherit, flex is always on, and the default main
    axis is `column` — none of the web defaults carry over.
15. Take safe-area insets from `react-native-safe-area-context` or the
    navigator, never from a hardcoded top or bottom padding. Notch, status bar
    and home-indicator sizes differ per device.
16. Animate `transform` and `opacity` in a Reanimated worklet. Animating width,
    height, margin or padding re-runs layout on every frame. On Expo SDK 54+ /
    Reanimated 4, `react-native-worklets` must be installed.
17. Read layout with `onLayout` (or a synchronous layout effect) rather than an
    imperative `measure()` callback — `measure()` results can land after the
    next paint and produce a visible jump.
18. Measure before and after any performance claim: React Native DevTools
    Profiler for render cost, a cold-start marker for TTI, a bundle size
    comparison for size. Cold starts only; warm and prewarmed launches hide the
    work.
19. Import from a module path, never a library's barrel entry, and do not add an
    `Intl` polyfill before checking what Hermes already implements. Both ship
    dead code into every startup.
20. Any change to native code or native configuration — a new native
    dependency, a native app-config field, an SDK or React Native bump — needs a
    new build. It can never reach installed users as an over-the-air update.
21. An installed build accepts an update only when the platform and runtime
    version match *and* the channel embedded in that build points at the branch
    holding the update. A release build normally starts on its cached update and
    applies a newly downloaded one at the next launch, so manual QA takes up to
    two full cold launches (terminate the app, do not background it).
22. Use a development build for anything with custom native code; Expo Go only
    runs the stock SDK. Its update behaviour also differs from a release build's,
    so never validate update delivery in Expo Go.
23. In a project without committed `ios/` and `android/` directories, never hand-edit
    generated native files: `expo prebuild` regenerates them and the edit is lost.
    Express the change as app config plus a config plugin.
24. Deep imports from `react-native/Libraries/...` and `react-native/src/...`
    do not resolve under the Strict TypeScript API, which is the default from
    0.87. Import from the `react-native` root.
25. In a monorepo, a native dependency must be a direct dependency of the app
    package, at one version across the workspace. Autolinking scans the app
    package, and two copies of a native library link twice.

## Workflows

**Stack detection (run first, every workflow).**

```bash
cat package.json                              # react-native, expo, expo-router, flash-list majors
cat app.json app.config.* 2>/dev/null         # runtimeVersion, plugins, native fields
cat eas.json 2>/dev/null                      # build profiles and the channel each one embeds
ls -d ios android 2>/dev/null                 # committed native dirs => prebuild is not in play
node -p "require('./package.json').packageManager ?? 'unknown'"
```

- No `expo` dependency → skip `references/expo-and-eas.md`; upgrades follow the
  bare path only.
- `expo-router` present → Expo Router owns navigation (rules 12–13).
- FlashList major → decides rule 9.
- `ios/` and `android/` committed → native edits are yours to make and keep;
  otherwise rule 23 applies.

### diagnose-jank

- [ ] Reproduce on a real device in a release-mode build. Dev-mode overhead and
      the unminified debug bundle invent jank that never ships.
- [ ] Capture a baseline before touching code: React Native DevTools Profiler
      (commit timeline, re-render counts, slowest commits) for render cost, or a
      startup marker for TTI. Record the number.
- [ ] Locate the layer from the evidence, not from habit: JS render cost, list
      virtualization, animation on the JS thread, an oversized bundle, or native
      work. `references/performance-lists.md` and
      `references/performance-startup-bundle.md` hold the per-layer rules.
- [ ] Apply one fix, re-measure with the same capture, and keep it only if the
      number moved. Revert and take the next candidate otherwise.
- [ ] **Gate — MEASURED:** the report carries a before and after value from the
      same measurement, and every claim that something is faster points at one.

### add-native-capability

- [ ] Check whether an existing library already covers it (`npx expo install`
      resolves an SDK-compatible version in Expo projects) before writing a
      module. A maintained library also carries the New Architecture support you
      would otherwise have to write.
- [ ] Decide the shape: a Turbo Native Module for an API, a Fabric native
      component for a view, an Expo module when the project is Expo-managed and
      wants config-plugin lifecycle. See
      `references/architecture-and-native-modules.md`.
- [ ] Write the spec first (rules 4–7): name, method signatures, nullability,
      and which methods are synchronous. This file is the contract both sides
      compile against.
- [ ] Wire `codegenConfig` in `package.json`, then run codegen — `pod install`
      on iOS, an Android build or `./gradlew generateCodegenArtifactsFromSchema`
      — and read the generated interface before writing native code.
- [ ] Hand the implementation body to the platform skill (`apple` / `android`),
      passing it the generated interface and the threading contract from rule 7.
- [ ] Add the JavaScript-side wrapper that owns error translation and the
      optional/mandatory decision from rule 6.
- [ ] **Gate — CODEGEN CLEAN:** codegen regenerates with no schema error, both
      platforms build, and calling the module from the app returns real data on
      a device or simulator — not just a passing typecheck.

### upgrade-react-native

- [ ] Establish the exact version pair and confirm the target exists in
      `rn-diff-purge`'s `RELEASES` list before promising anything.
- [ ] Take the native changes from the official version-pair diff (Upgrade
      Helper, or the raw `rn-diff-purge` diff). `RnDiffApp` is a placeholder —
      remap paths and package names, and merge into project customizations
      instead of overwriting them.
- [ ] Walk the version floors in `references/upgrading.md` for every release you
      cross: they gate Node version, engine, TypeScript surface and removed
      APIs, and skipping one produces a build that fails for a reason nothing in
      the diff explains.
- [ ] Triage dependencies in one pass — native libraries first, since they are
      what actually blocks a bump — then apply `package.json` changes and run
      exactly one install with the repo's own package manager.
- [ ] Sync native deps (`pod install` for iOS) and update the Gradle wrapper to
      the version the target template ships.
- [ ] For an Expo project, apply the Expo SDK layer too (`npx expo install
      --fix`, then the SDK's own upgrade notes); the React Native bump alone
      leaves the SDK packages mismatched.
- [ ] **Gate — BOTH PLATFORMS GREEN:** an iOS build and an Android build both
      succeed, typecheck and lint pass, and the app launches past its first
      screen on a device or simulator. A green typecheck is not an upgrade.

### ship-update

- [ ] Classify the change first (rule 20): any native code or native config
      touched means a build, not an update. Say so before discussing channels.
- [ ] For a JavaScript-only change, confirm the target: EAS project, channel (as
      embedded by the build profile in `eas.json`), platform, runtime version,
      and environment. Publish to a preview channel before production, and treat
      a production publish as needing explicit approval.
- [ ] Verify on an installed release build with two cold launches (rule 21), not
      in Expo Go and not by trusting the publish output.
- [ ] When a build does not update, walk the matching chain in order: published
      target, platform, runtime version, the channel actually compiled into the
      build, the channel-to-branch mapping, then launch behaviour. Details in
      `references/expo-and-eas.md`.
- [ ] **Gate — OBSERVED ON DEVICE:** the change is visible in an installed
      release build, and no compatibility safeguard (runtime version policy,
      startup timeout) was relaxed to make it appear.

### integrate-into-native-app

- [ ] Confirm brownfield is the decision, and pick exactly one track: Expo or
      bare. Mixing their setup steps produces a project that builds under
      neither.
- [ ] Set up the React Native side, then package an artifact — an XCFramework
      for iOS, an AAR for Android — and validate the packaging command before
      touching the host app.
- [ ] Integrate one surface into the host, behind a facade so the host's own
      code never imports React Native APIs directly. That facade is what makes
      the next surface cheap and the rollback possible.
- [ ] Verify startup and teardown on a device: the surface mounts, navigates
      back to native, and does not leak the runtime when dismissed.
- [ ] **Gate — ONE SURFACE SHIPPED:** the host app builds unchanged apart from
      the facade, one real screen renders from React Native, and the artifact
      build is reproducible from a documented command.

### review

- [ ] Run stack detection and state the React Native / Expo / FlashList versions
      in the report header, so version-gated findings are unambiguous.
- [ ] Read the diff's tests and native config first — `package.json`, app
      config, `eas.json`, `Podfile`, Gradle files. A native-config change
      silently changes what can ship as an update.
- [ ] Walk the Core rules in order; they are ordered by how often each one is
      the actual defect.
- [ ] Check the boundary explicitly: new sync spec methods, work added to a
      render path, a native dependency added outside the app package, a
      hand-edit inside generated `ios/` or `android/`.
- [ ] Drop findings whose fix costs more than they return, and say which you
      dropped. A report that flags every micro-rule buries the list that mounts
      2000 rows.
- [ ] **Gate — CITED AND ACTIONABLE:** every finding carries `path:line`, a
      severity, one line of why, and a concrete fix.

## Topic router

| Topic | Read when | File |
|---|---|---|
| New Architecture, codegen specs, module and component contracts, interop layer, threads | Writing or migrating a native module or component, or reading a codegen error | `references/architecture-and-native-modules.md` |
| Lists, recycling, images, text input, animations, view flattening | Scroll or interaction jank, or reviewing a list screen | `references/performance-lists.md` |
| Startup/TTI, Hermes, bundle size, Metro, memory leaks | Slow launch, oversized app, growing memory, or a bundling question | `references/performance-startup-bundle.md` |
| Expo Router and React Navigation 7 routing, native stacks and tabs, safe areas, deep links | Adding or restructuring navigation, or wiring a link into a screen | `references/navigation.md` |
| App config, prebuild, development builds, EAS Build, EAS Update, store submission | Any Expo or EAS task, or an update that did not arrive | `references/expo-and-eas.md` |
| Version floors, Upgrade Helper flow, Strict TypeScript API, Expo SDK upgrades | Bumping React Native or the Expo SDK, or explaining a post-upgrade break | `references/upgrading.md` |
| Brownfield integration, publishable libraries, monorepo layout | Embedding into a native app, extracting a library, or a workspace linking failure | `references/brownfield-and-libraries.md` |
| DevTools, device logs, native profilers, Jest and Testing Library, E2E | Debugging a device-only failure or writing tests for a screen | `references/debugging-and-testing.md` |

## Output format

For `review` and any other report on existing code, group findings by file,
ordered by severity, with no preamble:

```
Stack: react-native 0.87.1, expo 54.0.0, @shopify/flash-list 2.3.2

src/screens/FeedScreen.tsx
  L14 blocking - ScrollView + rows.map() over a 2000-item feed mounts every row
       before the first frame. Use FlashList with data/renderItem/keyExtractor.
  L37 important - `new Intl.DateTimeFormat(...)` is constructed inside the row
       render; hoist it to module scope.
       before: const formatter = new Intl.DateTimeFormat('en-US', {...});
       after:  // module scope, created once
  L18 minor - key={index} breaks recycling on reorder; use row.id.

src/native/DeviceInfo.ts
  ✓ pass
```

Severities: `blocking` (crash, rejected build, data loss, an update that cannot
work), `important` (dropped frames, leaks, boundary violations, native edits
that will be regenerated away), `minor` (naming, dead code, cosmetics). End with
a one-line verdict: ship, ship after blocking fixes, or rework.

## Environment

- Node.js: read the target release's own `engines.node`
  (`npm view react-native@<version> engines`) rather than a release note; 0.87
  narrows it to `^22.13.0 || ^24.3.0 || >= 26.0.0`. Install with the repo's own
  package manager (read `packageManager` in `package.json`).
- iOS work needs macOS with Xcode, CocoaPods and Ruby bundler. Android work
  needs JDK 17+ and the Android SDK. Neither is optional for a build gate — a
  platform you cannot build is a platform you cannot verify.
- Common commands:

```bash
npx react-native start --reset-cache      # Metro; --reset-cache after dep changes
npx expo start --clear                    # Expo projects
npx expo install <pkg>                    # SDK-compatible version resolution
npx expo prebuild --clean                 # regenerate native dirs (destroys hand edits)
cd ios && bundle exec pod install         # after any native dependency change
npx react-native run-android --mode release
npx eas-cli@latest update --help          # confirm flags before publishing
```

- React Native DevTools opens from Metro (`j`) or the Dev Menu and hosts the
  React Profiler; device-level CPU and memory work goes to Xcode Instruments or
  Android Studio's profiler. There is no offline substitute for a device, so a
  finding that needs one says so rather than guessing.
