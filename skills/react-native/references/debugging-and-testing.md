# Debugging, device logs and tests

Verified against: React Native 0.87, Expo SDK 54–57.

## Contents

- [React Native DevTools](#react-native-devtools)
- [Reading a redbox properly](#reading-a-redbox-properly)
- [Native logs](#native-logs)
- [Release-only failures](#release-only-failures)
- [Native profilers and debuggers](#native-profilers-and-debuggers)
- [Unit and component tests](#unit-and-component-tests)
- [Testing the native boundary](#testing-the-native-boundary)
- [End-to-end on a device](#end-to-end-on-a-device)
- [Old patterns](#old-patterns)

## React Native DevTools

- Open from Metro (press `j`) or the in-app Dev Menu. It hosts the console,
  sources with breakpoints, network, memory and the React profiler — the
  profiler is what any render-performance claim has to come from.
- Profiling a **release** build needs an inspector attachment; a debug profile
  measures dev-only work and misattributes it.
- The Element Inspector shows the component tree and layout box. Its old
  performance and network panes are gone; those live in DevTools now.
- Reload and Dev Menu availability are development-build features. There is no
  DevTools attachment to a store build.

## Reading a redbox properly

- Read the **first** error, not the last. A render error cascades into mounting
  and layout errors that describe the debris, not the cause.
- `Text strings must be rendered within a <Text> component` means a bare string
  or number landed under a `View` — usually from a falsy `&&` guard rendering
  `0` or `''`.
- `undefined is not a function` on a native call means the module resolved but
  the method did not: a name mismatch between the spec and the native
  registration, or a legacy module accessed with a signature that no longer
  exists.
- A `null` module from `TurboModuleRegistry.get` means autolinking did not link
  it (native build not rerun after install, or the dependency is not a direct
  dependency of the app package).
- A worklet-context error points at a missing or mismatched
  `react-native-worklets` install, not at the animation code.

## Native logs

```bash
npx react-native log-android      # project-local CLI, app must be running
npx react-native log-ios
adb logcat "*:S" ReactNative:V ReactNativeJS:V   # plus YourTag:D for a module
```

- The JavaScript console and the native log are different streams. A crash
  during native init never reaches the JavaScript console — read the native log
  before concluding the bundle failed to load.
- In Xcode, the app's own `NSLog`/`print` output appears in the Xcode console
  when launched from there; from a CLI run, use the log command above or
  Console.app.
- For a native module you are writing, log with a stable tag and filter on it;
  unfiltered logcat output on a real device drowns anything useful.

## Release-only failures

A bug that only appears in release builds is almost always one of these:

- **A stripped or renamed symbol.** Android release builds shrink and obfuscate;
  anything reached only by reflection needs a keep rule.
- **A dev-only assumption.** `__DEV__` branches, a dev-server URL, an inline
  `require` executed in a different order.
- **A different bundle.** Release uses precompiled bytecode from the build
  rather than the Metro server, so a resolver alias that works in dev can be
  absent.
- **Missing source maps.** A minified release stack trace is unreadable until
  symbolicated against the map produced by that exact build; keep the map as a
  build artefact, because it cannot be regenerated later.

Reproduce in a release build before diagnosing, and keep the release build and
its source map together.

## Native profilers and debuggers

- Attach the platform debugger to a running app rather than launching a separate
  build: Android Studio's *Attach to Process*, Xcode's *Attach to Process*. This
  is the only way to break in a native module while the JavaScript side drives
  it.
- CPU and allocation work goes to Xcode Instruments (Time Profiler,
  Allocations, Leaks) and Android Studio's profilers. The React profiler cannot
  see native cost, and the native profiler cannot attribute a React render.
- View hierarchy questions (why is this view not flattened, what is drawing
  twice) go to the platform view debugger, not to a screenshot.

## Unit and component tests

- Jest with `@react-native/jest-preset` for a bare project (the in-package
  `react-native/jest-preset` was removed in 0.87 — a config still naming
  `preset: 'react-native'` fails to resolve), or `jest-expo` for an Expo
  project. The preset is what maps native modules to mocks; without it, the
  first `import 'react-native'` fails.
- Component tests use React Native Testing Library: render the screen, query by
  accessible role, label or text, and interact via user events. Querying by
  `testID` is a fallback for something genuinely unreachable — a test that only
  finds elements by `testID` passes while the screen is unusable by a screen
  reader.
- Assert observable output: what is rendered, what the fake native module was
  asked to do, which navigation happened. A test that re-states the component's
  internal state cannot fail when the behaviour breaks.
- Mock at the boundary — the native module, the HTTP client, the navigation
  prop — never the component under test.
- Animations and gesture handlers need their libraries' test setup entries
  registered in the Jest setup file, and animations driven by fake timers.
  Without that a component using them throws before the first assertion.
- After a React Native upgrade, a suite that suddenly cannot find a core module
  usually needs its mock updated, not the upgrade reverted.

## Testing the native boundary

- The JavaScript wrapper around a spec is testable: inject a fake implementing
  the spec's interface and assert the argument mapping, error translation and
  the optional/mandatory behaviour from the registry choice.
- The native implementation is tested with the platform's own tools
  (`apple` / `android` skills). This skill's part is the contract, and the
  contract test is the fake conforming to the same spec type.
- A spec change with no test change is a silent break: the fake still compiles
  against the old shape unless it is typed from `Spec`.

## End-to-end on a device

- Use Maestro for device flows: the tests are declarative, run against a real
  build, and do not need the app instrumented. Reach for Detox instead when the
  suite genuinely needs JavaScript-level synchronization with React state.
- Run E2E against a release-like build, on a fixed device or emulator image.
  A suite that only passes on one developer's simulator is a scheduling problem
  waiting to happen.
- Keep the E2E set small and about user journeys: launch, sign in, the primary
  flow, and any flow that crosses the native boundary. Everything else is
  cheaper as a component test.

## Old patterns

<details>
<summary>Remote JS debugging in Chrome ("Debug JS Remotely")</summary>

The old debugger ran the app's JavaScript inside a Chrome tab, which changed
timing, disabled synchronous native calls and made JSI-based libraries fail
outright. It is gone; React Native DevTools debugs the app in its own runtime.
Advice that starts with "enable remote debugging" is for a removed feature.

</details>

<details>
<summary>Flipper</summary>

Flipper was the default debugging shell before DevTools and was removed from the
template in 0.74. Leftover `ReactNativeFlipper` files and a `FLIPPER_VERSION`
property are a common post-upgrade build failure — delete them.

</details>

<!-- sources: rn-docs, callstack-rn, expo-official, expo-docs -->
