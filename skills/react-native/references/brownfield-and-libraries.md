# Brownfield integration, libraries and monorepos

Verified against: React Native 0.87, @callstack/react-native-brownfield 2.x, Expo SDK 54–57.

## Contents

- [Choose the shape before touching code](#choose-the-shape-before-touching-code)
- [Brownfield: one track only](#brownfield-one-track-only)
- [The facade](#the-facade)
- [Packaging artifacts](#packaging-artifacts)
- [Host integration checkpoints](#host-integration-checkpoints)
- [Publishable libraries](#publishable-libraries)
- [Monorepos](#monorepos)
- [Old patterns](#old-patterns)

## Choose the shape before touching code

| Goal | Shape |
|---|---|
| Add React Native screens to an existing native app | brownfield integration |
| Ship reusable JavaScript + native code to several apps | a library with `codegenConfig` |
| Share code between an app and its own packages in one repo | monorepo workspace package |
| Add native capability to one Expo app only | a local module (`create-expo-module --local`) |

The wrong shape is expensive later: a local module that turns out to be needed
by a second app has to be republished as a library, and a library extracted too
early carries a release process nobody needed.

## Brownfield: one track only

Two supported tracks, and their setup steps are not interchangeable:

- **Expo track** — the React Native side is an Expo project; native
  configuration comes from the app config plus config plugins.
- **Bare track** — the React Native side is a bare project; native
  configuration is committed.

Classify first: `expo` in `package.json` (or an explicit request for the plugin
workflow) means the Expo track; committed native dirs with a plain React Native
CLI workflow means bare. If it is genuinely unclear, ask one question. Mixing
the tracks yields a project that builds under neither.

The sequence is the same in both:

1. Set up the React Native app that owns the surfaces.
2. Package it as a platform artifact.
3. Integrate one surface into the host and validate startup at runtime.
4. Repeat per feature or screen.

## The facade

The host app should talk to one small native class of yours, not to React Native
APIs. That facade owns: creating and holding the runtime, presenting a surface
by name with its initial props, and dismissing it.

Why it decides whether the migration survives:

- the host's build stays independent of React Native's API churn across
  upgrades;
- a second surface is a call, not another integration;
- rollback is deleting one call site rather than unpicking imports across the
  host;
- the runtime is created once, so surfaces after the first open instantly
  instead of paying startup again.

## Packaging artifacts

- iOS: an **XCFramework** built from the React Native app, consumed by the host
  project.
- Android: an **AAR** published to a repository (a local Maven repo is enough
  to start) and consumed as a normal dependency.
- Validate the packaging command on its own before touching the host. A
  packaging failure diagnosed inside a host build is three problems at once.
- Pin the artifact version in the host. A floating version turns a React Native
  change into an unexplained host regression.
- Placeholders in the integration docs (framework target name, Android module
  name, registered surface name) must be resolved from the actual project
  files, not guessed — a wrong registered name fails at runtime with an empty
  view, not at build time.

## Host integration checkpoints

Verify each on a device before moving on:

- the surface mounts and renders real content, not a blank view;
- navigating back to native leaves no leaked runtime or retained view
  controller/activity;
- reopening the surface reuses the existing runtime rather than paying startup
  twice;
- the host's own back/gesture handling still wins where it should;
- a release build of the host works, not only the debug build — bundle loading
  differs between them.

## Publishable libraries

- Scaffold with `create-react-native-library`. It wires codegen, the example
  app, the build pipeline and the platform project layout — all of which are
  easier to inherit than to assemble.
- `--local` produces a module inside the app instead of a publishable package:
  the right choice when exactly one app needs it, with no release process.
- The library's own `package.json` carries its `codegenConfig`; consuming apps
  pick it up through autolinking. A library that expects the app to declare its
  codegen has a bug.
- Keep the example app in the repository and use it as the test surface. A
  library verified only by unit tests is a library nobody has run.
- Declare `react` and `react-native` as peer dependencies, never dependencies —
  a bundled copy produces two renderers and errors that make no sense.
- Support one architecture: the New Architecture. Backwards-compatibility
  shims for the legacy runtime are only worth writing for a library that must
  support releases before 0.76.

## Monorepos

- A native dependency must be a **direct dependency of the app package**.
  Autolinking scans the app package's dependency graph; a native library
  hoisted from another workspace package may not be found, or may be linked
  from two locations.
- One version of every native dependency across the workspace. Two versions of
  a native library link two copies of the same native symbols, which fails at
  build time on Android and at runtime on iOS.
- Metro needs the workspace roots in its `watchFolders` and its resolver
  configured for hoisted `node_modules`, otherwise a shared package resolves in
  the dev server and not in the release bundle.
- Scope commands to the app package (`--prefix`, `--cwd`, or the workspace
  filter). An install at the root writes the wrong lockfile entries and an
  upgrade at the root upgrades the wrong package.
- Shared packages ship source and let the app's Metro transform it, or ship a
  build targeting the same React Native runtime. A package precompiled for the
  web breaks on Hermes in ways that surface as syntax errors at runtime.

## Old patterns

<details>
<summary>Manual host integration against React Native's own APIs</summary>

Before the brownfield helper libraries, the host app created and retained the
React Native host/root view itself, which meant every React Native upgrade
touched host code. That path still exists and is what most tutorials show. Use
it only when a helper library cannot express the integration; otherwise the
facade plus a helper library is strictly less maintenance.

</details>

<!-- sources: callstack-rn, expo-official, vercel-rn-rules -->
