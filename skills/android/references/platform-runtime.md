# Platform runtime

## Contents

- [Lifecycle and process death](#lifecycle-and-process-death)
- [Edge-to-edge and window insets](#edge-to-edge-and-window-insets)
- [The IME](#the-ime)
- [Permissions](#permissions)
- [Background work](#background-work)
- [Exported components and Intent security](#exported-components-and-intent-security)

## Lifecycle and process death

A configuration change recreates the Activity; a process death recreates everything. They
need different answers:

| Survives | Mechanism |
|---|---|
| Configuration change | `ViewModel` |
| Process death | `SavedStateHandle`, `rememberSaveable`, persisted storage |
| Neither | plain fields — treat as cache only |

The consequence people miss: a `ViewModel` alone does not survive process death, so state
that a user would be angry to lose (a half-written form, a selected filter) goes through
`SavedStateHandle`. Keep it small — the saved-state bundle has a hard size limit and
exceeding it crashes with `TransactionTooLargeException`.

Never hold an `Activity`, `View` or `Context` reference in anything longer-lived than the
component itself. When a long-lived object needs a context, inject the application
context.

`Lifecycle.State.STARTED` is the boundary for observation: start collecting at `STARTED`,
stop at `STOPPED`. `repeatOnLifecycle` does that for Views;
`collectAsStateWithLifecycle()` for Compose.

## Edge-to-edge and window insets

From targetSdk 35 the system draws the app edge-to-edge whether the app handles insets or
not, so the only question is whether your content is correctly padded.

1. Call `enableEdgeToEdge()` before `setContent` in every Activity.
2. Set `android:windowSoftInputMode="adjustResize"` in the manifest for every Activity
   with text input.
3. Apply insets **exactly once** per element. Double padding is the most common bug here,
   and it looks like "there is a gap above my toolbar".

Pick one mechanism per element:

- **Scaffold** is the default: take its `PaddingValues`, apply it as the scrollable's
  `contentPadding`, and mark it consumed so children do not apply it again.

  ```kotlin
  Scaffold { innerPadding ->
      LazyColumn(
          modifier = Modifier.fillMaxSize().consumeWindowInsets(innerPadding),
          contentPadding = innerPadding,
      ) { … }
  }
  ```

- **Material 3 components** (`TopAppBar`, `BottomAppBar`, `NavigationBar`,
  `NavigationRail`, `ModalBottomSheet`, drawer sheets) handle their own insets. Do not pad
  their parent container instead — that stops the bar's background from drawing behind the
  system bar, which is the whole point of edge-to-edge.
- **Everything else**: `Modifier.safeDrawingPadding()` or
  `Modifier.windowInsetsPadding(WindowInsets.safeDrawing)`.
- **A decorative element sized to a system bar**: `Modifier.windowInsetsTopHeight(...)`.

Adaptive scaffolds (`NavigationSuiteScaffold`, `ListDetailPaneScaffold`) do **not**
propagate `PaddingValues` to their inner content, and padding the scaffold itself clips
the edge-to-edge surface. Apply insets on the individual panes or screens instead.

Also: use `WindowInsets` rather than a hardcoded status/navigation bar height, and choose
system-bar icon colours through `enableEdgeToEdge`'s style parameters rather than
deprecated system-UI-controller libraries.

## The IME

`imePadding()` must be applied **before** `Modifier.verticalScroll()` in the chain, and
never in addition to a `Scaffold` whose `contentWindowInsets` already includes the IME —
that is double padding again. Two correct shapes:

```kotlin
// contentWindowInsets includes the IME, so innerPadding already has it
Scaffold(contentWindowInsets = WindowInsets.safeDrawing) { innerPadding ->
    Column(
        Modifier.padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .verticalScroll(rememberScrollState())
    ) { … }
}

// default contentWindowInsets excludes the IME, so add it explicitly
Scaffold { innerPadding ->
    Column(
        Modifier.padding(innerPadding)
            .consumeWindowInsets(innerPadding)
            .imePadding()
            .verticalScroll(rememberScrollState())
    ) { … }
}
```

Do not set the deprecated `SOFT_INPUT_ADJUST_RESIZE` flag in code; use the manifest
attribute.

## Permissions

- Request at the point of use, after the user has taken an action that explains why —
  never in a burst at first launch.
- Use the Activity Result APIs
  (`registerForActivityResult(ActivityResultContracts.RequestPermission())`), and in
  Compose `rememberLauncherForActivityResult`. `onRequestPermissionsResult` is legacy.
- Handle three outcomes, not two: granted, denied, and permanently denied. The third one
  cannot show the dialog again; the app must explain and offer a route to Settings.
- Prefer the permissionless path when one exists: the photo picker instead of
  `READ_MEDIA_IMAGES`, `ACTION_CREATE_DOCUMENT` instead of storage permissions, the
  approximate-location option when the feature does not need precision.
- Every dangerous permission you add is a Play policy declaration and a review risk;
  removing one is cheaper than justifying it.

## Background work

| Need | Use |
|---|---|
| Deferrable, must survive process death and reboot | `WorkManager` |
| Work tied to the current screen | `viewModelScope` |
| Work that must outlive the screen but not the process | an injected application scope |
| User-visible ongoing work (playback, navigation, recording) | a foreground service with the right type |
| Exact time | `AlarmManager` exact alarms, which need their own permission |

`WorkManager` rules that matter: give every unique work a name and an
`ExistingWorkPolicy`, make the worker idempotent (it will be retried), pass only small
identifiers in the input `Data` (it has a size limit — put the payload in a database and
pass the id), and set constraints rather than polling.

Do not use `WorkManager` for immediate work: the framework batches it and may delay
execution by minutes. A coroutine in the right scope is the answer for "do this now".

## Exported components and Intent security

An Activity, Service, Receiver or Provider with `android:exported="true"` — including one
that is implicitly exported by having an intent filter — is a public API of the device.
Every field of an incoming `Intent` is attacker-controlled.

- Declare `android:exported` explicitly on every component. Set it to `false` unless
  another app genuinely needs to start it.
- **Intent redirection** is the flagship bug: reading a nested `Intent` or a `Uri` from an
  extra and passing it to `startActivity`, `sendBroadcast`, `bindService` or
  `grantUriPermission`. That lends your app's identity to the caller, giving them access
  to your private components and files. If you must forward, validate the target's
  package and component against an allowlist and strip
  `FLAG_GRANT_READ_URI_PERMISSION`/`FLAG_GRANT_WRITE_URI_PERMISSION`.
- Guard privileged components with a `signature`-level permission so only your own
  signed apps can reach them.
- `PendingIntent`s are mutable-by-omission traps: always pass `FLAG_IMMUTABLE`, and use
  `FLAG_MUTABLE` only where the platform requires it (for example inline reply), with an
  explicit component set on the wrapped `Intent`.
- Never rely on sticky broadcasts or implicit broadcasts for anything sensitive; both are
  readable by other apps.
- `ContentProvider`: set `android:exported="false"` or enforce read/write permissions,
  never build SQL by string concatenation from a selection argument, and validate the
  path in `openFile` so `../` cannot escape your directory.
- `onNewIntent` receives untrusted data too; validate there as well as in `onCreate`.

<!-- sources: android-official, aldefy-compose, silvermoon-android, android-docs -->
