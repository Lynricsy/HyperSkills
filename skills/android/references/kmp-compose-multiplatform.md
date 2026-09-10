# Kotlin Multiplatform and Compose Multiplatform

Scope note: this covers what an Android module needs to know to share code. Swift and
SwiftUI on the consuming side belong to the `apple` skill.

## Contents

- [Is it worth it](#is-it-worth-it)
- [Source-set hierarchy](#source-set-hierarchy)
- [The expect/actual ladder](#the-expectactual-ladder)
- [Dependencies in commonMain](#dependencies-in-commonmain)
- [KMP and AGP 9](#kmp-and-agp-9)
- [Compose Multiplatform](#compose-multiplatform)
- [Testing shared code](#testing-shared-code)
- [Publishing to iOS](#publishing-to-ios)

## Is it worth it

Share the layers that are pure logic — models, use cases, repositories, networking,
serialization, persistence — and keep UI, platform SDK access and DI wiring at the edges.
An Android codebase that already keeps `:core:model` and `:core:domain` free of `android.*`
is most of the way there; one that does not will spend the whole migration removing
framework imports, and that work is worth doing whether or not KMP happens.

Do not start by making the UI multiplatform. Shared business logic with two native UIs is
the configuration with the best effort-to-risk ratio.

## Source-set hierarchy

Use the default hierarchy template unless the project genuinely needs custom wiring:

```
commonMain
├── androidMain
├── jvmMain
├── appleMain
│   ├── iosMain
│   │   ├── iosX64Main / iosArm64Main / iosSimulatorArm64Main
│   └── macosMain
└── jsMain / wasmJsMain
```

The rule is **place code in the highest source set where it is valid**. Duplicated logic
in `androidMain` and `iosMain` that could live in `commonMain`, or an `actual` repeated
per iOS target instead of written once in `iosMain`, is the most common review finding in
a KMP codebase.

## The expect/actual ladder

`expect`/`actual` is the last resort, not the first tool. Work down this ladder and stop
at the first rung that solves the problem:

1. Is there a multiplatform library already? (Ktor, kotlinx-serialization,
   kotlinx-datetime, kotlinx-coroutines, SQLDelight/Room KMP, Okio, DataStore.)
2. Can it be a plain interface in `commonMain` with implementations injected per platform?
   This is testable and replaceable; `expect`/`actual` is neither.
3. Can it be an intermediate source set (`appleMain`) so one `actual` covers all Apple
   targets?
4. Only then: a narrow `expect` declaration for the specific platform API call.

Whatever the mechanism, do not let platform types leak into shared business logic. A
`commonMain` function taking a `Context` or an `NSURL` is no longer common code.

Platform registration, lifecycle, packaging and SDK wiring belong on the platform side,
outside the shared module.

## Dependencies in commonMain

Not all of AndroidX is multiplatform. Some artifacts publish multiplatform variants
(`lifecycle-viewmodel`, `lifecycle-runtime-compose`, `datastore-preferences`, Room in
recent versions) and many do not, with availability and API surface varying by version.

Before adding any AndroidX or Jetpack dependency to `commonMain`, check Maven Central (or
the library's own docs) that the artifact publishes for every target you declare. The
failure mode is late and confusing: the Gradle sync succeeds for Android and the iOS
target fails to resolve.

Hilt does not work in shared source sets — its annotation processing is JVM/Android only.
Use Koin or kotlin-inject for a KMP project, and keep the Android app's own container
consistent with it.

## KMP and AGP 9

Under AGP 9's new DSL, the Kotlin Multiplatform plugin cannot share a Gradle subproject
with `com.android.library` or `com.android.application`. The migration is structural, not
cosmetic:

- Shared modules move from `com.android.library` + `org.jetbrains.kotlin.multiplatform`
  to the single `com.android.kotlin.multiplatform.library` plugin, whose Android
  configuration lives inside the `kotlin { androidLibrary { … } }` block.
- A module that today applies both KMP and `com.android.application` must be split: the
  Android application goes into its own subproject that depends on the shared one. The
  new KMP integration does not support the two in one subproject.
- `kapt` is unavailable; every processor must be KSP.
- `android.enableLegacyVariantApi` and similar workarounds in `gradle.properties` are
  transitional — remove them once the split is done.

Do the split as its own commit, before any other AGP 9 work, so a failure has one suspect.
The rest of the AGP 9 migration is a plain Gradle topic.

## Compose Multiplatform

Compose Multiplatform is the same Compose runtime and compiler, so every Compose state
and Compose performance rule applies unchanged. What differs:

- Resources come from the `Res` generated accessor (`Res.string.title`,
  `Res.drawable.logo`) with files under `commonMain/composeResources/`, not from `R`.
- Material 3 is available in common code; the Android-only Jetpack UI pieces are not —
  `androidx.activity.compose`, `WindowInsets` platform specifics, `AndroidView`.
- The entry point differs per platform: `ComponentActivity.setContent` on Android,
  `ComposeUIViewController` on iOS, `application { Window { } }` on desktop,
  `ComposeViewport` on web.
- Platform look and feel is not free. Scroll physics, text selection, back gesture and
  keyboard handling differ; budget for per-platform tuning rather than assuming parity.
- Interop with the host UI toolkit (`UIKitView` on iOS) has its own composition and
  touch-handling cost. Use it for maps and camera, not as a general escape hatch.

## Testing shared code

Put shared tests in `commonTest` so they run on every target; that is the point of the
shared module. Platform-specific tests go in `androidUnitTest`/`androidInstrumentedTest`
and `iosTest`.

Use `kotlin.test` assertions and `kotlinx-coroutines-test` in `commonTest`; JUnit-specific
APIs are not available there. Anything that depends on a platform engine — the device
SQLite for Room, real file IO — still has to run on that platform.

## Publishing to iOS

An Android engineer's minimum: the shared module produces an XCFramework consumed by the
Xcode project. Keep the public surface small and Swift-friendly — no Kotlin `sealed`
hierarchies exposed as enums, no default arguments (they do not survive), suspend
functions exposed as completion handlers or through a wrapper.

The Xcode-side integration, Swift interop details and the CocoaPods→Swift Package Manager
migration are outside this skill's scope.

<!-- sources: mmiani-kmp, jetbrains-kotlin, meetmiyani-compose, android-official, kotlin-docs -->
