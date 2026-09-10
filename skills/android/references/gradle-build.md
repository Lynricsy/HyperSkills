# Gradle, AGP and the build

Verified against: AGP 9.0 (minimum Gradle 9.1, JDK 17, SDK Build Tools 36.0.0,
maximum supported API level 36.1).

## Contents

- [Version catalog](#version-catalog)
- [Convention plugins](#convention-plugins)
- [Migrating to AGP 9](#migrating-to-agp-9)
- [AGP 9 default flips that change behaviour](#agp-9-default-flips-that-change-behaviour)
- [KSP and kapt](#ksp-and-kapt)
- [Keep rules and shrinking](#keep-rules-and-shrinking)
- [Build speed](#build-speed)

## Version catalog

`gradle/libs.versions.toml` is the only place a version literal belongs. A module build
file that pins its own version will drift away from the rest of the project and produce a
runtime `NoSuchMethodError` that looks like a library bug.

```toml
[versions]
agp = "9.0.1"
kotlin = "2.2.10"

[libraries]
androidx-room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }

[bundles]
compose = ["androidx-compose-ui", "androidx-compose-material3", "androidx-compose-tooling-preview"]

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
```

- Use a BOM (`platform(libs.androidx.compose.bom)`) for families that publish one, and
  omit the individual versions those libraries would otherwise carry.
- Group libraries that are always added together into a `[bundles]` entry.
- Keep alias names mechanical (`group-artifact`) so `libs.androidx.room.runtime` is
  predictable rather than memorised.

## Convention plugins

Shared build configuration lives in an included `build-logic` build, not in an
`allprojects {}` block or a copied `apply from:` script — those defeat configuration
caching and make the module graph opaque.

```
build-logic/
  settings.gradle.kts
  convention/
    build.gradle.kts                 # registers the plugins by id
    src/main/kotlin/
      AndroidApplicationConventionPlugin.kt
      AndroidLibraryConventionPlugin.kt
      AndroidLibraryComposeConventionPlugin.kt
      AndroidFeatureConventionPlugin.kt
      AndroidRoomConventionPlugin.kt
      HiltConventionPlugin.kt
```

Each plugin applies one concern (compile SDK and Java/Kotlin toolchain, Compose enablement,
Room schema location, Hilt wiring, lint, test runner, Gradle-managed devices) so a module
build file becomes a list of plugin ids plus its own dependencies. Version references
inside a convention plugin still come from the catalog, resolved through
`extensions.getByType<VersionCatalogsExtension>().named("libs")`.

## Migrating to AGP 9

Two different paths. Pick by project shape before touching anything.

**Plain Android app or library**

1. Bring AGP to the latest stable 8.x first — Android Studio's AGP Upgrade Assistant is
   the right tool — then move to 9.
2. Remove the `org.jetbrains.kotlin.android` (`kotlin-android`) plugin. AGP 9 has built-in
   Kotlin enabled by default and the JetBrains Android plugin is incompatible with the new
   DSL. AGP 9 carries a runtime dependency on KGP 2.2.10 and will upgrade a lower KGP or
   KSP to match; to go higher, declare the classpath in the root build file.
3. Remove `org.jetbrains.kotlin.kapt`. Migrate each processor to KSP; apply
   `com.android.legacy-kapt` only for the ones that cannot move (see below). Bring KSP to
   2.3.6+ and Hilt to 2.59.2+.
4. Replace the legacy variant API. `android.applicationVariants`, `libraryVariants`,
   `testVariants`, `variantFilter` and friends are gone with the new DSL:

   ```kotlin
   androidComponents {
       onVariants { variant -> variant.signingConfig.enableV1Signing.set(false) }
       beforeVariants(selector().withBuildType("debug")) { it.enable = false }
   }
   ```

   `sdkDirectory`, `adbExecutable` and similar move to `androidComponents.sdkComponents`;
   custom device providers move to Gradle-managed devices.
5. Custom `BuildConfig` fields need `buildFeatures { buildConfig = true }`, and a `String`
   field's value must contain its own escaped quotes — `value = "\"prod\""`. Writing
   `value = "prod"` is an error, because the value is emitted literally.
6. Clean up `gradle.properties`: delete `android.builtInKotlin`, `android.newDsl`,
   `android.uniquePackageNames` and `android.enableAppCompileTimeRClass` once the build is
   green. They are transitional opt-outs, and `android.newDsl=false` stops working in
   AGP 10.

   Never add `android.disallowKotlinSourceSets=false` to silence a source-set error;
   fix the source set.

**Kotlin Multiplatform project**

The KMP plugin cannot share a Gradle subproject with `com.android.library` or
`com.android.application` under the new DSL. Move shared modules to
`com.android.kotlin.multiplatform.library` and extract the Android application into its
own subproject. That split is a Kotlin Multiplatform topic of its own.

**Verification, in order**: IDE sync succeeds → `./gradlew help` → `./gradlew build
--dry-run` → a real `assembleRelease`. Do not run `clean` between steps; it only costs
time. A `ClassCastException` mentioning `BaseExtension` means something still references
the old DSL types — usually a third-party plugin that needs its own upgrade.

## AGP 9 default flips that change behaviour

| Property | Change | What it means for you |
|---|---|---|
| `android.newDsl` | `false` → `true` | Legacy DSL implementations and the old variant API are gone |
| `android.builtInKotlin` | `false` → `true` | `kotlin-android` must be removed |
| `android.sdk.defaultTargetSdkToCompileSdkIfUnset` | `false` → `true` | An unset `targetSdk` now follows `compileSdk` instead of `minSdk`. Set it explicitly |
| `android.default.androidx.test.runner` | `false` → `true` | `AndroidJUnitRunner` replaces the deprecated `InstrumentationTestRunner` |
| `android.r8.proguardAndroidTxt.disallowed` | `false` → `true` | `getDefaultProguardFile("proguard-android.txt")` is rejected; use `proguard-android-optimize.txt` |
| `android.r8.strictFullModeForKeepRules` | `false` → `true` | `-keep class A` no longer implies its default constructor |
| `android.r8.optimizedResourceShrinking` | `false` → `true` | Resources are shrunk together with code; incomplete keep rules now show up as missing resources |
| `android.enableAppCompileTimeRClass` | `false` → `true` | App code compiles against a non-final `R`; `R.id.x` in a `switch` must become `if/else` |
| `android.proguard.failOnMissingFiles` | `false` → `true` | A typo in a `proguardFiles` path fails the build instead of being ignored |
| `android.defaults.buildfeatures.resvalues` / `.shaders` | `true` → `false` | Enable per-module where actually used |
| `android.onlyEnableUnitTestForTheTestedBuildType` | `false` → `true` | Unit tests are created for the tested build type only |
| `android.dependency.useConstraints` | `true` → `false` | Constraints apply only to app device tests; speeds up import |
| — | uses NDK r28c by default | Pin the NDK version explicitly if you ship native code |
| — | library consumers need compile SDK ≥ the library's | Set `AarMetadata.minCompileSdk` if you publish |

## KSP and kapt

kapt runs a full Java stub-generation pass before the Kotlin compiler; KSP reads the
Kotlin AST directly and is roughly twice as fast on annotation-heavy modules.

Decide per processor, mechanically: unzip the processor jar and look for
`services/com.google.devtools.ksp.processing.SymbolProcessorProvider`. Present means KSP
is supported; absent means it is not. The jar is under
`~/.gradle/caches/modules-2/files-2.1/<group>/<artifact>/`.

Room supports KSP from 2.3.0-beta02; Hilt and Dagger support it in current releases.
Anything left over gets `com.android.legacy-kapt`, module by module, never project-wide.

## Keep rules and shrinking

- Release builds set `isMinifyEnabled = true` and `isShrinkResources = true`, with
  `getDefaultProguardFile("proguard-android-optimize.txt")` as the base.
- Libraries ship their own consumer rules. Add a project rule only for *your* reflective
  code, and write it narrowly: the class, the members you actually reflect on, and — under
  AGP 9 strict full mode — the constructor if you construct it reflectively.
- `-dontobfuscate` and wildcard keeps are not debugging tools. Keep R8 on and deobfuscate
  crash reports with `retrace` and the variant's `mapping.txt`, which you must archive per
  release.
- For Compose specifically, never add a wildcard keep for `androidx.compose.**`: Compose
  ships correct consumer rules, and a blanket keep undoes lambda grouping, source-info
  stripping and devirtualisation in one line.

## Build speed

Measure before changing anything: `./gradlew assembleDebug --scan`, or the build analyzer
in Android Studio. Then, in order of usual payoff:

- Turn on the configuration cache and parallel execution in `gradle.properties`
  (`org.gradle.configuration-cache=true`, `org.gradle.parallel=true`,
  `org.gradle.caching=true`) and fix the tasks they report as incompatible rather than
  disabling them again.
- Replace kapt with KSP (above).
- Give the daemon enough heap (`org.gradle.jvmargs=-Xmx4g` or more) — GC thrash looks
  exactly like a slow build.
- Flatten the module graph. A chain `:app → :feature → :core:data → :core:model`
  serialises; siblings parallelise.
- Keep `buildFeatures` off where unused: `buildConfig`, `resValues`, `shaders`, `viewBinding`
  each add a task per variant.
- Do not chase the clean-build number. Incremental build time is what developers pay every
  day.

<!-- sources: android-official, jetbrains-kotlin, drjacky-ninja, silvermoon-android, skydoves-compose-perf, android-docs -->
