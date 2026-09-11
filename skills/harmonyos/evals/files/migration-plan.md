# ShopDemo: Android → HarmonyOS port, proposed architecture

Our Android app ships to ~4M users. Leadership wants a HarmonyOS build in one
quarter. This is the plan the Android team wrote; we need it reviewed before we
start cutting code.

## Current Android shape

- 1 `Application`, 9 `Activity`, 31 `Fragment`, single-Activity for the main tab shell.
- Navigation: Jetpack Navigation with a `nav_graph.xml`, args passed as `Bundle`.
- State: `ViewModel` + `StateFlow`, collected in Compose with `collectAsStateWithLifecycle`.
- Storage: Room (11 entities), `SharedPreferences` for the session token and flags,
  `DataStore` for the feature-flag cache.
- Background: `WorkManager` for the nightly catalogue sync (usually 6–12 minutes),
  `Dispatchers.IO` coroutines for image decode and price recalculation.
- Lists: `RecyclerView` with `DiffUtil`, plus one `ViewPager2` for the banner carousel.
- Permissions: camera (barcode scan), location (store finder), contacts (invite),
  requested lazily with `ActivityResultContracts.RequestPermission`.
- Native: one `libpricing.so` (C++) called through JNI for the discount engine.

## Proposed HarmonyOS mapping

1. Each Android `Activity` becomes one `UIAbility`, so 9 UIAbilities total. Each
   `Fragment` becomes an `@Entry @Component` page.
2. Keep the graph shape: declare every page in `main_pages.json` and navigate with
   `router.pushUrl({ url, params })`, since `params` accepts an object just like `Bundle`.
3. Port `ViewModel` 1:1 to a plain class holding `@State` fields, and expose it to
   child components by passing the instance down as a `@Prop`.
4. Room → `RelationalStore`; `SharedPreferences` and `DataStore` → `Preferences`.
5. Nightly sync: start a `Worker` from `onCreate` of the main UIAbility and leave it
   running for the whole session; it also drives image decode and price recalculation
   so we only manage one background thread.
6. `RecyclerView` → `List` with `ForEach`; `ViewPager2` → `Swiper`.
7. Toasts, dialogs and page navigation stay on the global helpers
   (`promptAction.showToast`, `AlertDialog.show`, `router.back`) to keep the diff small.
8. Permissions: call `requestPermissionsFromUser` once in `onWindowStageCreate` for all
   three permissions, cache the result in `Preferences`, and read the cache afterwards
   so users are not prompted twice.
9. `libpricing.so` keeps its JNI entry points; we will write a thin `.d.ts` by hand and
   import the `.so` directly from ArkTS.
10. Build: set `compatibleSdkVersion` and `targetSdkVersion` both to the newest SDK the
    IDE offers so we get every new API, and sign release builds with the debug profile
    until the AppGallery account is approved.

## Open question

Is anything in the list above going to bite us? We would rather hear it now than in
the AppGallery review.
