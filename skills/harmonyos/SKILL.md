---
name: harmonyos
description: "Guides HarmonyOS NEXT app work in ArkTS and ArkUI: the arkts-* language restrictions that make legal TypeScript fail to compile, build() purity, state management V1 vs V2 decorators and the API-gated rules for mixing them, Stage model UIAbility and WindowStage lifecycles, UIContext instead of global ArkUI APIs, Navigation and NavPathStack instead of the deprecated router, TaskPool vs Worker and Sendable, Preferences and RelationalStore, module.json5 requestPermissions reason/usedScene, exported components and Want validation, hvigorw builds, signing and AppGallery release, Android-to-HarmonyOS porting, and hdc/uitest verification. Use when reading or writing .ets, module.json5, build-profile.json5 or oh-package.json5, when DevEco reports arkts-* errors, or for 鸿蒙 ports. Do not use for native Android or iOS - use the `android` and `apple` skills - nor for Flutter OHOS or React Native; for TypeScript outside ArkTS use the `typescript` skill."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: platform
---

# harmonyos

## Scope

Covers HarmonyOS NEXT application and service modules: the ArkTS language and its
restrictions relative to TypeScript, ArkUI declarative UI and adaptive layout, state
management V1 and V2 and the boundary between them, the Stage model (UIAbility,
WindowStage, Context, Want, `module.json5`, HAP/HAR/HSP), Navigation, concurrency
(TaskPool, Worker, Sendable), Preferences and RelationalStore persistence, permission
declaration and runtime authorization, exported-component and Want security, the
hvigor build with signing and AppGallery release, porting an Android app across, and
on-device verification with `hdc`, `uitest` and vision-driven automation.

Targets **HarmonyOS NEXT (API version 12 and later)**, with **API 20 (`6.0.0(20)`)** as the
default baseline when a project does not state one. Everything below assumes the Stage
model. The FA model, and the pre-NEXT HarmonyOS versions that ran Android APKs, are a
different platform and are not covered.

Not covered: native Android, Kotlin, Jetpack Compose and Gradle — use the `android`
skill. Native iOS, macOS, Swift and SwiftUI — use the `apple` skill. Flutter's OHOS
embedding and React Native are out of scope entirely. Plain TypeScript outside `.ets`
(tsconfig, type-level modelling, Node tooling) — use the `typescript` skill. Also out of
scope: OpenHarmony OS development itself (kernel, C++ subsystems, XTS), wallet/payment
and other Huawei product APIs, and app-store marketing.

Paths below are relative to this skill's directory.

## Read first

`references/arkts-language.md` before writing or reviewing any `.ets` file. ArkTS is a
**restricted** TypeScript: a construct can be valid TypeScript, pass review, and still be
a compile error. Guessing from TypeScript habit is the single largest source of wasted
work on this platform.

## Core rules

1. ArkTS restricts TypeScript; it does not extend it. Roughly 76 documented `arkts-*`
   rules remove features outright — `any`/`unknown`, structural typing, `for..in`,
   destructuring, `delete`, generators, `as const`, `Function.apply/call/bind`,
   nested functions. Treating ArkTS as "TypeScript with strict flags on" produces code
   that cannot compile. `[verified]`
2. Object layout is fixed at compile time. Adding, deleting or retyping a property at
   runtime is rejected, and the `as any` escape hatch that hides this in TypeScript does
   not exist. A "just tag the object" helper will not build. `[verified]`
3. Types are nominal. Two classes with identical public APIs are unrelated, so a cast
   between them fails (`arkts-no-structural-typing`). Declare an `interface` and an
   explicit `implements` clause instead. `[verified]`
4. An object literal must correspond to a declared class or interface, and a class cannot
   appear in an `implements` clause. A bare `{ id, title }` literal typed as a
   `type X = { … }` alias is two violations, not a style choice. `[verified]`
5. ArkTS syntax checking is only enforced in standard mode, selected by
   `compatibleSdkVersion >= 10`; below that the same violations are warnings. Read the
   project's `build-profile.json5` before judging whether a diagnostic blocks the build.
   `[verified]`
6. `throw` accepts only `Error` and its subclasses (`arkts-limited-throw`), and rejected
   promises carry `BusinessError`. Throwing a string, and swallowing a `BusinessError`
   without inspecting `code`, both destroy the only error signal the platform gives you.
   `[verified]`
7. Keep `build()` a pure UI description: no assignment to state, no `await`, no logging,
   no side effects. `build()` re-runs on every re-render, so work placed there executes an
   unbounded number of times. `[official]`
8. Give every `ForEach`/`LazyForEach` a stable `keyGenerator`. Index-derived keys make the
   framework rebuild and remount items on insert or delete, discarding component state and
   scroll position. Use `LazyForEach` with an `IDataSource` for long or remote lists;
   `ForEach` builds every child eagerly. `[official]`
9. One component belongs to exactly one state-management generation. V1 decorators inside
   `@ComponentV2`, and V2 decorators inside `@Component`, are compile errors — not
   degraded behaviour. `[verified]`
10. In V2, `@Param` is the input and `@Event` is the output. `@Param` cannot be written
    locally, so a child that must change parent state takes an `@Event` callback. V1
    state decorators do not accept function-typed values at all: `@State` on a function
    threw at runtime before API 23 and is a compile error from API 23. `[verified]`
11. `@Once` is legal only paired with `@Param` inside `@ComponentV2`; `@Provider`/
    `@Consumer` must be initialized locally and must not be initialized from the parent —
    the exact opposite of V1 `@Provide`/`@Consume`. `[verified]`
12. `@ObservedV2` and `@Trace` only work as a pair, only on instances created with `new`,
    and only observe properties actually marked `@Trace`. A `@Trace`-less property in an
    `@ObservedV2` class is silently unobserved — a stale UI with no error. `[verified]`
13. V1 cannot observe nested class properties at all: `@State` on an object sees
    whole-object replacement only, and reaching a nested level needs `@Observed` plus
    `@ObjectLink`. Prefer `@ObservedV2`/`@Trace` (API 12+) for new model classes.
    `[verified]`
14. Mixing generations is version-gated. The old mixed-use rules apply to API 18 and
    earlier; from **API 19** use `UIUtils.enableV2Compatibility()` when passing V1 state
    into V2 and `UIUtils.makeV1Observed()` when passing plain data into V1. Without
    `enableV2Compatibility`, complex V1 data crossing into `@ComponentV2` simply stops
    propagating. `[verified]`
15. Call ArkUI through `UIContext`, not the global helpers. One ArkTS engine can host
    several UI instances in the Stage model, so global `router`, `promptAction`,
    `AlertDialog` and friends guess the target instance from the call chain and guess wrong
    across async boundaries. The accessors have been available a long time —
    `UIContext.getRouter()` and `getPromptAction()` are `@since 10`, `isAvailable()` is
    `@since 20` — so there is no version excuse for the global form. `[verified]`
16. Navigate with `Navigation` + `NavPathStack` + `NavDestination`. `@ohos.router` is no
    longer recommended, and every global `router` function carries
    `@deprecated since 18` with `@useinstead @ohos.arkui.UIContext:Router`; router params
    also cannot carry functions. `[verified]`
17. Default to TaskPool; choose Worker deliberately. A TaskPool task is capped at three
    minutes of execution (awaited I/O excluded), so longer work needs Worker — but Worker
    tasks cannot be cancelled, at most 64 Workers run per process, and Worker priority
    only became configurable in **API 18**. `[verified]`
18. Anything crossing a thread boundary is structured-cloned unless it is `@Sendable`,
    `ArrayBuffer` or `SharedArrayBuffer`. A cloned object shares nothing with the original,
    so mutating it on the worker side changes nothing on the host side. `[verified]`
19. A `user_grant` permission needs `reason` (as a `$string:` resource, localized) and
    `usedScene` with a non-empty `when` of `inuse` or `always` in `module.json5`;
    incomplete declarations fail release verification rather than failing at runtime.
    `[verified]`
20. Re-check authorization with `checkAccessToken()` before every protected call, because
    the user can revoke it in Settings. Once the user has refused,
    `requestPermissionsFromUser()` no longer shows a dialog, so the app must send the user
    to the settings dialog instead of re-prompting. Requesting inside
    `onWindowStageCreate()` must wait for `loadContent()`/`setUIContent()` to finish.
    `[verified]`
21. Treat every `exported: true` ability as an untrusted entry point: validate the
    incoming `Want`, and never forward a caller-supplied URI or ability name onward
    unchecked. An exported ability with a custom action and no permission can be started by
    any app on the device. `[official]`
22. `minAPIVersion`/`targetAPIVersion` are `app.json5` tags, not `module.json5` tags, and
    they are generated during the build and cannot be manually configured at all. The
    inputs are `compatibleSdkVersion`/`targetSdkVersion` in the project-level
    `build-profile.json5`; `targetAPIVersion` falls back to `compileSdkVersion` when
    `targetSdkVersion` is unset. Moving the fields to `app.json5` is not the fix.
    `[verified]`
23. `compatibleSdkVersion` is the minimum installable API version, and it is independent
    of `targetSdkVersion`. Raising it to the newest SDK silently removes the app from every
    older device — AppGallery just stops distributing it there, with no error anywhere.
    `[official]`
24. A `product` with no `signingConfig` is not signed at all, and a debug profile cannot
    produce a release-acceptable package. Naming a signing config `release` does not make
    it one; the `.p12`/`.cer`/`.p7b` triple must match. `[official]`
25. A UIAbility is a system-scheduled component with its own window and mission-stack
    entry, not a screen. One UIAbility hosting a `Navigation` stack is the normal shape;
    one UIAbility per screen produces one task-switcher entry and one window lifecycle per
    screen. `[official]`

## Workflows

### implement

- [ ] Read `build-profile.json5` (products: `compatibleSdkVersion`, `targetSdkVersion`,
      `runtimeOS`, `arkTSVersion`), `oh-package.json5`, and the target module's
      `module.json5` and `build-profile.json5`. Every rule above that carries an API
      version depends on these values.
- [ ] Read one existing page and one existing model class to determine which state
      generation the module uses. Adopt it (rule 9); do not introduce the other one.
- [ ] Model the data first: an `@ObservedV2` class with `@Trace` on every property the UI
      reads, or — in a V1 module — `@Observed` plus `@ObjectLink` at each nesting level.
- [ ] Write the component: `@ComponentV2` with `@Local` for internal state, `@Param` for
      input, `@Event` for output. Keep `build()` pure (rule 7).
- [ ] Register the route as a `NavDestination` in the existing `Navigation` stack; do not
      add a second navigation mechanism.
- [ ] Move anything that could block a frame off the UI thread per
      `references/concurrency.md`, and declare any new permission per rules 19–20.
- [ ] **Gate:** `hvigorw --mode module -p module=<mod>@default assembleHap --no-daemon`
      succeeds, and `codelinter` reports no new `arkts-*` findings.

### review

- [ ] Establish the SDK range from the build files first; a finding that depends on an API
      version is not a finding until you know the project's version.
- [ ] Walk the Core rules in order — they are ordered by how often each is the real defect.
- [ ] Check the state graph end to end: which class is observable, which property is
      traced, which decorator receives it, which generation each component belongs to.
      A stale UI is almost always a missing `@Trace` or a crossed generation, not a
      rendering bug.
- [ ] Check every async boundary for a global ArkUI call (rule 15) and every resource —
      subscriptions, timers, `ResultSet`, file handles, controllers — for an owner that
      releases it.
- [ ] Check `module.json5` separately: permission completeness, `exported` abilities,
      hand-edited generated fields.
- [ ] Report only findings with a reachable trigger and a concrete impact. A text match is
      a lead, never a finding; read the whole function and its callers before reporting.
- [ ] **Gate:** every finding carries `path:line`, the trigger, the impact, and a fix; and
      any platform claim names the API version it holds for.

### fix-compile-errors

- [ ] Collect the diagnostics, then group them by `arkts-*` rule id rather than by file.
      Most walls of errors are three or four rules repeated.
- [ ] Separate errors from warnings, and confirm standard mode is actually in force
      (rule 5) before rewriting anything.
- [ ] Fix by category using `references/arkts-language.md`: typing (`any` → declared
      class/interface), object shape (literal → class, structural cast → `implements`),
      statements (`var`/`for..in`/destructuring/`delete`), functions (expression → arrow,
      nested → top-level).
- [ ] Re-run the build after each category. One category at a time keeps the next wave of
      diagnostics readable.
- [ ] **Gate:** the module assembles, and no violation was suppressed — there is no
      `@ts-ignore` equivalent in ArkTS, so a "fix" that hides a rule is a rewrite that
      did not happen.

### migrate-from-android

- [ ] Inventory the Android app by concern: screens and navigation graph, state holders,
      persistence, background work, permissions, native libraries.
- [ ] Map the shell first and get it wrong-proof: one UIAbility plus a `Navigation` stack
      (rule 25), not one UIAbility per Activity.
- [ ] Translate state holders into `@ObservedV2` model classes plus `@ComponentV2`
      components; a ViewModel instance handed down as `@Prop` is copied one-way and the
      child's edits never reach the parent.
- [ ] Re-plan background work against the real limits in rule 17 instead of mapping
      `WorkManager` onto one long-lived Worker.
- [ ] Rewrite the JNI layer as Node-API with a `.d.ts` facade and
      `externalNativeOptions`/CMake wiring; JNI entry points do not carry over.
- [ ] Port one vertical slice end to end and verify it on a device before porting the
      second. See `references/android-migration.md` for the per-concern mapping.
- [ ] **Gate:** the slice builds, installs and passes a `uitest` interaction on a real
      device or emulator, with the same acceptance criteria as the Android screen.

### verify-on-device

- [ ] Establish the target: `hdc list targets -v`, and pick an explicit `-t <target>` when
      more than one is connected.
- [ ] Install and launch, then capture evidence with `uitest dumpLayout` and
      `uitest screenCap` before and after the interaction under test.
- [ ] For interactions expressed in natural language, drive the device with the
      vision-based CLI in `references/build-sign-verify.md`: one command at a time,
      synchronously, never in the background — the loop depends on reading each screenshot
      before deciding the next action.
- [ ] If a tool, SDK, device or account is missing, report the exact missing prerequisite.
      Never describe an unrun check as passed.
- [ ] **Gate:** the assertion is stated against captured layout or screenshot evidence,
      naming the device and the API version it ran on.

## Topic router

| Topic | Read when | File |
|---|---|---|
| ArkTS language | Writing or fixing any `.ets`; `arkts-*` diagnostics; porting TypeScript | `references/arkts-language.md` |
| ArkUI declarative UI | Building components, `build()`, lists, `@Builder`, lifecycle, adaptive layout | `references/arkui-declarative.md` |
| State management V2 | New components; `@Local`/`@Param`/`@Once`/`@Event`/`@Provider`/`@Consumer`/`@Monitor`/`@Computed`/`@ObservedV2`/`@Trace` | `references/arkui-state-v2.md` |
| State management V1 and interop | Existing V1 code; a stale UI; passing data between generations | `references/arkui-state-v1-interop.md` |
| Navigation | Adding a route, back handling, deep links, leaving `router` behind | `references/arkui-navigation.md` |
| Stage model and configuration | UIAbility/WindowStage lifecycle, Context, Want, `module.json5`, permissions, HAP/HAR/HSP | `references/stage-model.md` |
| Concurrency | Long or CPU-bound work, TaskPool vs Worker, `@Sendable`, cross-thread data | `references/concurrency.md` |
| Data persistence | Preferences, RelationalStore, `PersistenceV2`, storage limits | `references/data-persistence.md` |
| Build, sign and verify | `hvigorw`, `build-profile.json5`, signing, obfuscation, release, `hdc`/`uitest` | `references/build-sign-verify.md` |
| Android migration | Porting an existing Android app; per-concern mapping and traps | `references/android-migration.md` |

## Output format

For `review` (and any other report on existing code), group findings by file, ordered by
severity, with no preamble:

```
entry/src/main/ets/pages/CartPage.ets
  L31 blocking - @Prop and @Link inside a @ComponentV2 struct. V1 decorators are rejected
       in V2 components, so this does not compile on any API version.
       before: @Prop line: LineItem / @Link total: number
       after:  @Param line: LineItem / @Param total: number + @Event onTotalChange
  L18 blocking - @Observed Cart holds a plain LineItem[]; qty changes are never observed,
       so the total stays stale. Move the model to @ObservedV2 + @Trace.
  L52 important - @Monitor('cart.lines') cannot see item-level changes in an array.
       Watch the traced property, or recompute through @Computed.

entry/src/main/module.json5
  L62 blocking - ohos.permission.LOCATION is user_grant with no reason and no usedScene;
       release verification rejects the package.
  ✓ ohos.permission.INTERNET is system_grant, no reason needed.
```

Severities: `blocking` (does not compile, crashes, loses data, fails release verification,
or removes devices from distribution), `important` (stale UI, leaked resource, unguarded
exported component, wrong-instance UI call, unbounded work on the UI thread), `minor`
(naming, ordering, dead code). End with a one-line verdict: ship, ship after blocking
fixes, or rework. State the API version every platform claim holds for, and list unrun
checks separately from findings.

## Environment

DevEco Studio supplies the SDK, `hvigorw`, `ohpm`, `codelinter`, `hdc` and the emulator;
`hvigorw` additionally needs JDK and Node.js on `PATH`. Commands used by the workflows:

```bash
ohpm install                                  # resolve oh-package.json5 dependencies
hvigorw --version                             # confirm the wrapper resolves
hvigorw buildInfo -p json                     # product/target/buildMode actually in effect
hvigorw clean --no-daemon
hvigorw --mode module -p module=entry@default assembleHap --no-daemon
hvigorw assembleApp --no-daemon               # release-mode .app for AppGallery
codelinter --format json                      # ArkTS rule findings without a full build
hdc list targets -v                           # device/emulator discovery
hdc -t <target> shell uitest dumpLayout -p /data/local/tmp/layout.json
hdc -t <target> shell uitest screenCap -p /data/local/tmp/shot.png
```

Everything from `hdc` down needs a connected device or a running emulator, and the
emulator needs a signed-in Huawei account in DevEco Studio. A HarmonyOS SDK is not
available on Linux CI by default; when it is missing, report that boundary rather than
reasoning about build output you did not produce.
