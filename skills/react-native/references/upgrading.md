# Upgrading React Native and the Expo SDK

Verified against: React Native 0.87 (latest stable), Expo SDK 57.

## Contents

- [Route the upgrade first](#route-the-upgrade-first)
- [Version floors that break projects](#version-floors-that-break-projects)
- [The bare React Native procedure](#the-bare-react-native-procedure)
- [Dependency triage](#dependency-triage)
- [Strict TypeScript API](#strict-typescript-api)
- [Expo SDK upgrades](#expo-sdk-upgrades)
- [Verification](#verification)
- [Stop conditions](#stop-conditions)
- [Old patterns](#old-patterns)

## Route the upgrade first

- **Expo project** (`expo` in dependencies): the Expo SDK bump drives the React
  Native version. Do the SDK upgrade; do not bump `react-native` by hand.
- **Bare project**: the version-pair template diff drives it.
- **Monorepo**: decide which package is the app and scope every command to it.
  Running an upgrade command at the workspace root installs into the wrong
  `node_modules` and produces a lockfile nobody can explain.
- **Several majors behind**: go one minor at a time when native config changed
  in between. A single 0.79 → 0.87 jump merges every native change at once, and
  a broken build has eight suspects.

## Version floors that break projects

Cross each of these and something changes whether or not the diff mentions it.

| Release | What changed |
|---|---|
| 0.74 | Flipper removed from the template; leftover `ReactNativeFlipper` and `FLIPPER_VERSION` block the build |
| 0.76 | New Architecture on by default |
| 0.79 | Android JS bundle shipped uncompressed by default (Hermes can mmap it) |
| 0.80 | Strict TypeScript API available as an opt-in preview |
| 0.82 | New Architecture is the **only** runtime — the opt-out flags stop selecting anything; Hermes V1 available as an experimental opt-in |
| 0.83 | Experimental `RCT_REMOVE_LEGACY_ARCH` flag to compile legacy architecture code out on iOS |
| 0.84 | Hermes V1 default; precompiled React Native iOS binaries default; legacy architecture code excluded from iOS builds by default (the interop layer stays); ESLint v9 flat config supported; `XHRInterceptor`/`WebSocketInterceptor` deprecated |
| 0.87 | Strict TypeScript API is the **default**; `react-native/jest-preset` no longer ships in the package (use `@react-native/jest-preset`); `engines.node` narrows to `^22.13.0 \|\| ^24.3.0 \|\| >= 26.0.0` |

Four consequences that catch projects out:

- **Read the target release's own `engines.node`** (`npm view react-native@<target> engines`)
  rather than trusting a release note. The announced "Node 22 minimum" and the
  published constraint have diverged before, and the published constraint is
  what fails the install. On 0.87 a CI image on Node 20 or 21 fails immediately,
  with an error that reads like a tooling bug.
- A project with `preset: 'react-native'` in its Jest config breaks on 0.87 with
  a preset-resolution error. Switch to `@react-native/jest-preset` at the
  matching version.
- On 0.84+, re-enabling legacy architecture code on iOS means building React
  Native from source (`RCT_USE_PREBUILT_RNCORE=0 RCT_REMOVE_LEGACY_ARCH=0`
  during `pod install`), which also gives up the precompiled-binary build-time
  win. Treat it as a last resort while a dependency catches up, not a setting.
- Crossing 0.84 changes the JavaScript engine: Hermes V1 becomes the default.
  No app change is needed to get it, and opting back out is a `hermes-compiler`
  package override (`overrides` / `resolutions` / `pnpm.overrides`) plus
  `RCT_HERMES_V1_ENABLED=0` on iOS or `hermesV1Enabled=false` on Android with a
  from-source build — not an application setting. Say which engine the app ends
  up on, because engine-level behaviour differences after an upgrade are
  otherwise unattributable.

## The bare React Native procedure

1. **Establish the pair.** Current version from the app's `package.json`;
   target from the release you intend (`npm view react-native dist-tags`).
2. **Confirm the target has a diff.** The community `rn-diff-purge` repository
   publishes a `RELEASES` list and a raw diff per version pair; the Upgrade
   Helper web UI renders the same data. If the exact pair is missing, pick the
   nearest published patch and say which pair you actually used.
3. **Read the diff before editing.** List the changed files and group them:
   JavaScript/TypeScript, iOS, Android, tooling.
4. **Remap and merge.** Paths and identifiers in the diff use the template's
   placeholder app name; substitute the real app and package names. Merge into
   project customizations — never overwrite a file wholesale, and never copy the
   whole template over the project.
5. **Skip template-only noise.** The template's own entry screen and its
   demo-only dependencies are not part of an app upgrade unless the app really
   uses them.
6. **One dependency pass.** Apply the `package.json` changes from the diff plus
   the migrations from triage, then run exactly one install with the repo's own
   package manager (read `packageManager`). Repeated single-package installs
   produce a lockfile that resolves differently from either target.
7. **Sync native deps.** `pod install` for iOS. Update the Gradle wrapper
   (including `gradle-wrapper.jar`) to what the target template ships — a stale
   wrapper fails with a message about the plugin, not about the wrapper.
8. **Announce the plan before editing** when the upgrade involves ambiguous
   dependency migrations, and get the choice confirmed rather than picking a
   replacement library silently.

## Dependency triage

- Native libraries decide whether the upgrade is possible at all. For each one,
  check its releases for support of the target React Native version before
  touching anything else.
- An unmaintained native dependency is the usual blocker. The options are: a
  maintained fork, a replacement library, vendoring the module into the app, or
  postponing the upgrade. Say which one you are proposing and what it costs.
- Align `react` with what the target React Native release ships; a mismatched
  React version produces renderer errors that look like application bugs.
- Read the correct changelog. React Native keeps per-minor-line changelog files,
  so a `0.8x` breaking change is not in the top-level list.
- Test-only breakage after a bump is often a module that moved out of the core
  JavaScript surface and now needs a mock in the Jest setup — fix the mock
  rather than pinning the old version.

## Strict TypeScript API

The Strict TypeScript API restricts `react-native`'s TypeScript surface to its
root exports and generates the types from source. It affects type-checking only:
nothing changes in the bundle or at runtime, so it can be adopted incrementally
with no shipping risk.

- Default from 0.87; opt-in preview on 0.80–0.86.
- To opt in on 0.80–0.86, add
  `"customConditions": ["react-native", "react-native-strict-api"]`.
  Both entries are required: `customConditions` **replaces** rather than merges
  the value from an extended config, so dropping `"react-native"` breaks module
  resolution for every package that keys on it. The project needs
  `"moduleResolution": "bundler"` (or `node16`/`nodenext`) for conditions to
  apply at all.
- On 0.87+, the temporary escape hatch is the
  `react-native-legacy-deep-imports` condition. It is scheduled for removal;
  use it to unblock a release, not as a resting place.
- Deep imports must become root imports:

| Before | After |
|---|---|
| `import Foo from 'react-native/Libraries/.../Foo'` | `import {Foo} from 'react-native'` |
| `import type {FooProps} from 'react-native/Libraries/.../Foo'` | `import type {FooProps} from 'react-native'` |
| `import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent'` | `import {codegenNativeComponent} from 'react-native'` |
| `import type {Int32} from 'react-native/Libraries/Types/CodegenTypes'` | `import type {CodegenTypes} from 'react-native'`, then `CodegenTypes.Int32` |

- Do the mechanical pass with the `no-deep-imports` rule from React Native's
  ESLint plugin (`--fix` rewrites known imports), then handle the remainder by
  hand. `node_modules/react-native/types_generated/index.d.ts` is the
  authoritative map from internal path to exported name — read it instead of
  guessing an export.
- Errors located **inside** `node_modules` come from a library shipping raw
  TypeScript (typically a Jest mock entry point). Update that library first. An
  inline suppression cannot help, because the error is reported in the library's
  file, not at the import site; the fallback is a `paths` redirect to an untyped
  stub declaration plus an upstream report. Keep `skipLibCheck` on.

## Expo SDK upgrades

- Bump the `expo` package to the target SDK, then `npx expo install --fix` to
  realign every SDK-managed dependency. Do not pick versions by hand; the SDK
  owns the compatible set, including the React Native version.
- Read the SDK's own release notes for that version's breaking changes, then run
  `npx expo-doctor`.
- In a prebuild project, regenerate native dirs with `npx expo prebuild --clean`
  after the bump rather than merging native diffs by hand — that is the whole
  point of not committing them.
- Package renames and API moves within the Expo SDK (a module split into two,
  an API replaced by a successor package) are the usual work item; each is a
  code change, not a version bump.
- After the SDK bump, existing installed builds are on the old runtime version.
  An SDK upgrade is a native change: it ships as a new build, never as an update.

## Verification

An upgrade is done when all of these pass, in this order:

1. `pod install` succeeds and an **iOS build** succeeds.
2. An **Android build** succeeds.
3. Typecheck and lint pass, or each remaining failure has a written next action.
4. The app launches on a device or simulator and gets past its first screen —
   including a cold start, since startup is where engine and bundle changes
   surface.
5. The flows that touch upgraded native dependencies are exercised by hand. A
   native library that compiles can still fail on first call.

## Stop conditions

Stop and report rather than improvising when:

- the target version has no published template diff and no acceptable neighbour;
- a native dependency has no version supporting the target and no replacement
  was approved;
- native entry files (`AppDelegate`, `MainApplication`, `Podfile`, root
  `build.gradle`) have merge conflicts that need a project decision;
- the project turns out to be Expo-managed and the request was framed as a bare
  React Native bump.

## Old patterns

<details>
<summary><code>react-native upgrade</code> as an automatic command</summary>

The CLI's upgrade command applied the template diff automatically and, on any
project with native customizations, produced conflicts it could not resolve.
The supported flow is to read the version-pair diff and merge it deliberately.
Expect community answers to still recommend the command.

</details>

<!-- sources: rn-community, callstack-rn, rn-docs, expo-official, expo-docs -->
