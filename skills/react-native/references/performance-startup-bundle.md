# Startup, bundle size and memory

Verified against: React Native 0.87 (Hermes V1 default since 0.84), Expo SDK 54–57.

## Contents

- [Measure TTI before changing anything](#measure-tti-before-changing-anything)
- [Hermes](#hermes)
- [What actually moves startup](#what-actually-moves-startup)
- [Bundle size: measure, then cut](#bundle-size-measure-then-cut)
- [Android app size](#android-app-size)
- [Metro](#metro)
- [Memory growth](#memory-growth)
- [Old patterns](#old-patterns)

## Measure TTI before changing anything

- Measure **cold starts only**: launch after a full terminate, with the process
  not resident. Warm launches, prewarmed launches and a launch straight after
  install all report numbers that no user experiences.
- Measure a **release build on a real device**. A debug build loads an
  unminified bundle from Metro and the numbers are unrelated to shipped startup.
- Use markers around the phases you can act on — process start → React Native
  runtime ready → first screen interactive — rather than a single wall-clock
  number, or you cannot tell native init from JavaScript execution.
- Take five samples and use the median; single cold-start numbers on a phone
  vary by tens of percent.

## Hermes

- Hermes is the default engine and ships bundled with each React Native release,
  so its version always matches the runtime. Hermes V1 is the default from 0.84;
  no app change is needed to get it.
- Confirm at runtime with `!!global.HermesInternal`. That only proves the engine
  is Hermes, not that precompiled bytecode is in use — a non-standard bundle
  loading path can leave the app parsing source. If startup matters, verify the
  build produces the bytecode bundle and benchmark before/after.
- Bytecode is produced at build time for release builds, which is why a release
  build starts faster than the same app in dev even ignoring the dev overhead.
- Opting out of Hermes V1 requires a `hermes-compiler` package override plus
  building React Native from source (and, on iOS, disabling precompiled
  binaries). It is a debugging measure, not a tuning knob.

## What actually moves startup

In rough order of typical impact:

1. **Less JavaScript evaluated at launch.** Everything imported from the entry
   graph is evaluated before the first screen. Move a heavy screen, editor,
   chart or SDK behind a lazy import so it costs nothing for users who never
   open it.
2. **No barrel imports.** Importing from a library's root index pulls its whole
   module graph into the startup path even when one function is used. Import the
   module path directly.
3. **No unnecessary `Intl` polyfill.** Hermes implements a substantial `Intl`
   surface; check what is missing for the locales the app supports before
   shipping a polyfill, which is one of the largest single additions available.
4. **Native navigation.** A native stack hands screen transitions to the
   platform, so the first screen is not waiting behind JavaScript-driven
   animation setup.
5. **Preload deliberately.** Warming one expensive screen or asset before the
   user navigates helps; preloading everything just moves the cost into startup.

## Bundle size: measure, then cut

Produce a release bundle with a source map and read the treemap; do not guess
which dependency is large.

```bash
npx react-native bundle \
  --entry-file index.js \
  --bundle-output /tmp/main.jsbundle \
  --platform ios \
  --sourcemap-output /tmp/main.jsbundle.map \
  --dev false --minify true

npx source-map-explorer /tmp/main.jsbundle --no-border-checks
ls -l /tmp/main.jsbundle          # record the byte count; compare after each cut
```

Expo projects have `npx expo export` plus Atlas for the same view. Record the
before and after byte count for every change — "should be smaller" is not a
result.

Cuts worth making, in order: drop a dependency whose job is one function,
replace a large library with a platform API (a native SDK already in the binary
beats a JavaScript reimplementation), split rarely used screens behind lazy
imports, then dead-code elimination.

## Android app size

- Enable R8 for release builds; it shrinks and obfuscates the native/Java side
  that the JavaScript treemap does not show. Keep rules for anything reached
  only by reflection.
- Ship an Android App Bundle so the store serves per-device native libraries
  instead of every ABI.
- Put images in the platform's asset containers rather than the JavaScript
  bundle when they are static app chrome; the platform picks the right density
  and the bytes stay out of the bundle.

## Metro

- `--reset-cache` after any dependency or `metro.config.js` change; a stale
  transform cache produces "impossible" module-resolution errors.
- Custom resolver logic (monorepo roots, aliases, polyfills) is the usual cause
  of a module resolving differently in dev and release. Reproduce bundling
  problems with a production bundle command, not the dev server.
- Only `EXPO_PUBLIC_`-prefixed environment variables are inlined into an Expo
  client bundle. Anything else read via `process.env` at runtime is `undefined`
  on device — and any secret inlined this way ships to every user.

## Memory growth

- Growth while scrolling and then flat after the list settles is virtualization
  working. Growth that never returns is a leak.
- The usual JavaScript leaks: a subscription, timer or event listener created in
  an effect without a cleanup; a module-level cache keyed by screen instance; a
  closure captured by a long-lived native callback.
- On the native side, a background queue or coroutine scope owned by a module
  that is not cancelled on teardown keeps everything it captured alive. The
  module's teardown hook must cancel it.
- Diagnose with a heap snapshot pair (before and after the suspect flow) in
  React Native DevTools, and with the platform allocation profilers for native
  growth. A screenshot of rising memory is not a diagnosis.

## Old patterns

<details>
<summary>Disabling Android JS bundle compression by hand</summary>

Compressed assets cannot be memory-mapped, so a compressed bundle forced Hermes
to decompress before reading. On 0.78 and earlier the fix was
`androidResources { noCompress += ["bundle"] }` in `android/app/build.gradle`.
From 0.79 the Android JS bundle is uncompressed by default; check the build
setting rather than adding the `noCompress` block, which now only adds
divergence from the template.

</details>

<details>
<summary>Inline requires and RAM bundles</summary>

`inlineRequires` and the RAM-bundle format were the answer to slow startup
before Hermes bytecode. They are still configurable, but on a Hermes app the
gain is small and the debugging cost (module evaluation order changing under
you) is not. Cut startup JavaScript instead.

</details>

<!-- sources: callstack-rn, rn-docs, expo-official, expo-docs -->
