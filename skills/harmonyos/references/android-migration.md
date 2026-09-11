# Porting an Android app to HarmonyOS NEXT

Verified against: OpenHarmony application-dev docs for every HarmonyOS-side claim; `openharmonyinsight/openharmony-skills` Android→HarmonyOS mapping tables for the concern inventory.

## Contents

- [Framing](#framing)
- [Shell and screens](#shell-and-screens)
- [UI component mapping](#ui-component-mapping)
- [State holders](#state-holders)
- [Concurrency and background work](#concurrency-and-background-work)
- [Storage](#storage)
- [Permissions](#permissions)
- [Native code](#native-code)
- [Build and release](#build-and-release)
- [Order of work](#order-of-work)
- [Trap table](#trap-table)

## Framing

The two platforms agree more on shape than on mechanism. Declarative UI, a lifecycle-owning
component, a permission model, a Gradle-like build — the concepts transfer. What does not
transfer is any assumption about *granularity*: the HarmonyOS analogue of an Activity is
not a UIAbility, the analogue of a ViewModel is not a class holding `@State`, and
`WorkManager` has no analogue at all.

So port by concern, not by file. A file-by-file translation produces something that builds
and is wrong in exactly the places listed below.

## Shell and screens

| Android | HarmonyOS | Note |
|---|---|---|
| `Application` | `AbilityStage` (per module) + `ApplicationContext` | there is no single god object |
| `Activity` | **a `NavDestination` page**, not a UIAbility | see below |
| single-Activity + nav graph | one `UIAbility` + one `Navigation` + `NavPathStack` | the normal shape |
| `Fragment` | a `@Component` custom component | |
| `nav_graph.xml` | route map (`@Builder` branch or `route_map.json`) | |
| `Bundle` args | `NavPathStack` param object | **cannot carry functions** |
| `Intent` | `Want` | explicit `Want` names the ability; implicit is matched against `skills` |
| `<intent-filter>` | `skills` in `module.json5` | |
| `startActivityForResult` | `pushDestination` + `pop(result)` with a pop callback | |
| `onBackPressed` | `NavDestination.onBackPressed`, or `setInterception` | interception also covers programmatic navigation |

**The one mapping worth arguing about:** a UIAbility is a system-scheduled component with
its own window and its own entry in the task switcher. Nine Activities do not become nine
UIAbilities; they become nine `NavDestination`s inside one UIAbility. Mapping one-to-one
gives you nine task-switcher entries, nine window lifecycles, and inter-screen state that
must now travel through `Want` or persistent storage instead of one shared stack.

Add a second UIAbility only when the system must schedule it independently: a share target,
a launcher shortcut, a window that must survive on its own, a side-by-side multi-window
experience.

## UI component mapping

| Android | HarmonyOS |
|---|---|
| `LinearLayout` | `Column` / `Row` |
| `FrameLayout` | `Stack` |
| `RelativeLayout` | `RelativeContainer` |
| `ConstraintLayout` | `RelativeContainer`, or `GridRow`/`GridCol` for grid-like constraints |
| `ScrollView` | `Scroll` |
| `RecyclerView` + `DiffUtil` | `List` + `LazyForEach` (or `Repeat`) with a stable key |
| `GridView` / `RecyclerView` grid | `Grid` + `LazyForEach` |
| `ViewPager2` | `Swiper` |
| `TabLayout` + `ViewPager2` | `Tabs` + `TabContent` |
| `CardView` | a `Column` with `.borderRadius()` and `.shadow()` |
| `Toolbar` | `Navigation`'s title bar / toolbar |
| `BottomNavigationView` | `Tabs` with `barPosition: BarPosition.End` |
| `ImageView` | `Image` |
| `TextView` | `Text` |
| `EditText` | `TextInput` / `TextArea` |
| `Snackbar` / `Toast` | `UIContext.getPromptAction().showToast()` |
| `AlertDialog` | `UIContext.showAlertDialog()` or `CustomDialog` |
| `BottomSheetDialog` | `bindSheet` |
| `WebView` | `Web` (ArkWeb) |
| `Compose` + `remember` | ArkUI + `@Local` / `@ObservedV2` |

Two systematic differences:

- **Keys are mandatory in practice.** `DiffUtil` gave you stable identity for free;
  `LazyForEach` needs an explicit `keyGenerator` or it rebuilds items on insert and delete.
- **Modifier order is semantics.** As in Compose, `.padding()` before `.backgroundColor()`
  is not the same as after.

## State holders

| Android | HarmonyOS |
|---|---|
| `ViewModel` + `StateFlow` | an `@ObservedV2` model class + a `@ComponentV2` component with `@Local` |
| `collectAsStateWithLifecycle` | no analogue needed; ArkUI observes traced properties |
| `MutableStateFlow` exposed as `StateFlow` | `@Local` private to the component, `@Param` for input, `@Event` for output |
| hoisting state to a common ancestor | `@Local` in the ancestor, `@Param`/`@Event` down |
| `viewModelScope` | nothing automatic — you own cancellation in `aboutToDisappear` |
| DI graph (Hilt/Koin) | no framework; construct explicitly or hold a module-level singleton (mind HAR duplication) |

Three failure modes, all common:

- **Handing the view model down as `@Prop`.** `@Prop` deep-copies, so the child's edits
  never reach the parent, and native-backed types (e.g. `PixelMap`) do not survive the copy
  at all. The V2 shape is `@Param` for reading plus an `@Event` callback for writing.
- **Assuming `@State` observes nested properties.** It does not; V1 sees one level, and
  nested observation needs `@Observed` + `@ObjectLink` per level. New model classes should
  be `@ObservedV2` with `@Trace` on every property the UI reads.
- **No `viewModelScope`.** A `ViewModel` cancelled its coroutines for you. Here,
  subscriptions, timers and in-flight tasks must be released in `aboutToDisappear` or they
  outlive the screen.

## Concurrency and background work

| Android | HarmonyOS |
|---|---|
| `Dispatchers.Default` CPU work | `TaskPool` with a `@Concurrent` function |
| `Dispatchers.IO` | `TaskPool` (awaited I/O does not count against the 3-minute cap) |
| a dedicated long-lived thread | `Worker`, with explicit `terminate()` |
| `WorkManager` deferred/periodic job | **no analogue.** Use the platform's background-task and agent-task mechanisms, and keep the compute inside the limits below |
| `coroutineScope`/`SupervisorJob` structure | `TaskGroup`, `SequenceRunner`, `addDependency` |
| cancellation via `Job.cancel()` | `taskpool.cancel(task)`; **Worker cannot be cancelled** |
| `@Volatile` / shared mutable state | nothing shared by default; `@Sendable` + `AsyncLock`, or `SharedArrayBuffer` |

The plan to scrutinise hardest in any port: "run one Worker for the whole session and put
all background work on it". That serializes every unit of work behind the current one,
cannot cancel anything, and before API 18 could not be prioritized. Meanwhile the limits are
concrete — a TaskPool task is capped at three minutes of execution (awaited I/O excluded),
at most 64 Workers exist per process, and only TaskPool supports cancellation, delay,
dependencies and groups. See `references/concurrency.md`.

A nightly sync that computes for 6–12 minutes is the one case where Worker is right — and
it is still wrong to put the per-item image decode and price recalculation on the same
Worker.

## Storage

| Android | HarmonyOS |
|---|---|
| `SharedPreferences` | `Preferences` |
| `DataStore` (Preferences) | `Preferences` |
| `DataStore` (Proto) | `Preferences` with your own serialization, or RDB |
| `Room` | `RelationalStore` (RDB) |
| `SQLiteOpenHelper` | `RdbStore` + `store.version` migrations |
| `ContentProvider` | `DataShareExtensionAbility` |
| `getFilesDir()` / `getCacheDir()` | `Context.filesDir` / `Context.cacheDir` |
| `EncryptedSharedPreferences` | key store for the key, ciphertext in `Preferences` |
| `MediaStore` | `photoAccessHelper` |
| Keystore | universal keystore |

Limits Android does not have: a `Preferences` key is ≤1024 bytes and a string value ≤16 MB;
`Preferences` has **no encryption**; an RDB record over 2 MB inserts and cannot be read
back; RDB has four read connections and one write connection, so a leaked `ResultSet`
blocks later queries. See `references/data-persistence.md`.

Room's compile-time schema validation has no counterpart — schema drift is a runtime
problem here, so version the store and test the upgrade from the oldest version your
`compatibleSdkVersion` still admits.

## Permissions

| Android | HarmonyOS |
|---|---|
| `<uses-permission>` | `requestPermissions[]` in `module.json5` |
| runtime rationale UI | `reason` (`$string:` resource) + `usedScene` in the declaration |
| `ActivityResultContracts.RequestPermission` | `abilityAccessCtrl` + `requestPermissionsFromUser()` |
| `checkSelfPermission` | `checkAccessToken()` |
| `shouldShowRequestPermissionRationale` | no equivalent; after a refusal no dialog appears at all |
| exported component + `android:permission` | `exported` + permission entry + `Want` validation |

Differences that change code:

- `reason` and `usedScene` (with `when` = `inuse` or `always`) are **mandatory** for
  `user_grant` permissions and are checked at **AppGallery release verification**, not at
  build or run time.
- There is no rationale-state query. Once the user refuses,
  `requestPermissionsFromUser()` silently stops showing a dialog, so the app must route the
  user to the settings dialog.
- Caching the grant is wrong on both platforms and fails faster here: re-check with
  `checkAccessToken()` before every protected call.
- Requesting from `onWindowStageCreate()` must wait until `loadContent()`/`setUIContent()`
  completes.

## Native code

| Android | HarmonyOS |
|---|---|
| JNI (`JNIEnv`, `JNI_OnLoad`, name-mangled symbols) | **Node-API** (`napi_*`, `NAPI_MODULE`, `napi_property_descriptor`) |
| `System.loadLibrary("pricing")` | `import lib<name>.so from 'lib<name>.so'` with a `types/lib<name>/index.d.ts` facade |
| `externalNativeBuild` / `CMakeLists.txt` | `externalNativeOptions` in the module `build-profile.json5` + `CMakeLists.txt` |
| `abiFilters` | `externalNativeOptions.abiFilters` |
| `SurfaceView`/`GLSurfaceView` | `XComponent` + `NativeWindow` + EGL/GLES |
| `Bitmap` across the boundary | `PixelMap`, `ArrayBuffer`/`TypedArray` |

**JNI entry points do not carry over.** The signatures, the registration mechanism and the
type marshalling are all different, so the native layer has to be re-fronted: keep the
algorithm, rewrite the boundary. Build the chain top-down and verify each link — ArkTS
facade → `.d.ts` declaration → Node-API registration and exports → CMake/ABI configuration
— because a mismatch anywhere in it surfaces as the same unhelpful load failure.

Hand-writing the `.d.ts` is acceptable; hand-writing it and never checking it against the
registered exports is how a port ships a module whose every call returns `undefined`.

## Build and release

| Android | HarmonyOS |
|---|---|
| `build.gradle` + version catalog | `build-profile.json5` (project + module) + `oh-package.json5` |
| Gradle | `hvigorw` |
| Maven/Gradle dependencies | `ohpm` |
| `minSdk` | `compatibleSdkVersion` |
| `targetSdk` | `targetSdkVersion` |
| `compileSdk` | `compileSdkVersion` (usually implicit on HarmonyOS) |
| product flavors | `products` |
| build types | `buildModeSet` |
| library module (AAR) | HAR (copied per consumer) or HSP (shared at runtime) |
| dynamic feature module | feature HAP |
| keystore + signing config | `signingConfigs` with `.p12` / `.cer` / `.p7b` |
| R8/ProGuard | ArkGuard / bytecode obfuscation |
| AAB | `.app` from `hvigorw assembleApp` |

Two traps carried over from Android habits:

- **"Set everything to the newest SDK."** On Android raising `minSdk` is a visible,
  deliberate decision. Here, raising `compatibleSdkVersion` silently removes the app from
  older devices with no error anywhere — AppGallery just stops distributing it. Keep it as
  low as the feature set allows and guard newer APIs with `canIUse`.
- **"Ship with the debug signing config until the account is ready."** A debug profile
  carries a device allow-list and is not acceptable for release; and a product with no
  `signingConfig` is not signed at all, while still building successfully.

## Order of work

1. Inventory by concern: screens and navigation, state holders, persistence, background
   work, permissions, native libraries, third-party SDKs.
2. Check third-party dependencies first. A HarmonyOS build of an SDK you depend on either
   exists or it does not, and that answer can change the plan more than anything else here.
3. Build the shell: one UIAbility, one `Navigation`, the route map, the theme and resource
   structure.
4. Port **one vertical slice end to end** — screen, state, data, permission — and verify it
   on a device against the same acceptance criteria as the Android screen.
5. Only then parallelise across features. The slice is what proves the mappings above were
   applied correctly.
6. Re-plan background work and native code explicitly; they are the two areas where a
   mechanical translation is guaranteed wrong.

## Trap table

| Ported as | Actual result |
|---|---|
| one UIAbility per Activity | one task-switcher entry and one window lifecycle per screen |
| `router.pushUrl` for navigation | not recommended; global form deprecated since API 18 |
| function inside route params | not delivered; params are serialized |
| view model passed as `@Prop` | one-way copy; child edits never reach the parent |
| `@State` on an object, expecting nested observation | V1 sees one level only |
| no cleanup because "ViewModel handled it" | leaked subscriptions, timers, tasks |
| one long-lived Worker for all background work | serialized, uncancellable, unprioritized before API 18 |
| `WorkManager` → a Worker started in `onCreate` | wrong mechanism; also holds a worker slot forever |
| global `promptAction` / `AlertDialog` / `router` | wrong UI instance in multi-window; `UIContext` accessors are `@since 10`, so there is no version excuse |
| cached permission grant | breaks after the user revokes in Settings |
| all three permissions requested at startup | review risk, and no dialog at all after a refusal |
| JNI entry points kept as-is | not loadable; Node-API is the boundary |
| `compatibleSdkVersion` = newest SDK | silently drops older devices from distribution |
| debug signing profile for release | not acceptable for AppGallery |
| `ForEach` without a key, replacing `RecyclerView` | lost item state and scroll position |

<!-- sources: oh-insight-migration, openharmony-docs, earfrog-arkts, corey-harmonyos, dengshiying-harmonyos, huawei-docs -->
