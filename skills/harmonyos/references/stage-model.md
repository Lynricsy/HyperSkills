# Stage model, module configuration and permissions

Verified against: OpenHarmony application-dev docs, `application-models/uiability-lifecycle`, `uiability-usage`, `application-context-stage`, `quick-start/module-configuration-file`, `quick-start/hap-package`, `security/AccessToken/declare-permissions`, `request-user-authorization`.

## Contents

- [Component vocabulary](#component-vocabulary)
- [UIAbility lifecycle](#uiability-lifecycle)
- [WindowStage](#windowstage)
- [Context](#context)
- [Launch types and Want](#launch-types-and-want)
- [HAP, HAR, HSP](#hap-har-hsp)
- [module.json5](#modulejson5)
- [Declaring permissions](#declaring-permissions)
- [Runtime authorization](#runtime-authorization)
- [Exported components and Want validation](#exported-components-and-want-validation)

## Component vocabulary

- **UIAbility** — a system-scheduled component with UI. It owns a window, appears in the
  task switcher, and has its own lifecycle driven by the system.
- **ExtensionAbility** — a background/extension component of a specific type (widget,
  service, input method, share, …). Each type has its own template and its own lifecycle.
- **AbilityStage** — per-module runtime container, created when the module's first
  component loads. `onCreate`, `onAcceptWant`, `onConfigurationUpdate`.
- **Page** — a UI unit. Under `Navigation` it is a `NavDestination`; under the legacy
  router it is an `@Entry` component.

The most consequential distinction on the platform: **a UIAbility is not a screen.** One
UIAbility hosting a `Navigation` stack is the normal application shape. Creating one
UIAbility per screen gives every screen its own task-switcher entry, its own window
lifecycle, its own `WindowStage`, and cross-screen state that now has to travel through
`Want` or persistent storage instead of a shared navigation stack.

Reach for a second UIAbility only when the system genuinely needs to schedule the thing
independently: a separately-launchable entry point (a share target, a shortcut), a window
that must survive independently, or a multi-window side-by-side experience.

## UIAbility lifecycle

Foreground launch:

```
onCreate → onWindowStageCreate → onForeground
        ← onBackground (user switches away)
        → onNewWant → onForeground (user returns)
```

Background launch via `startAbilityByCall()`:

```
onCreate → onBackground          (onWindowStageCreate is NOT called)
→ onNewWant → onWindowStageCreate → onForeground   (when brought to the foreground)
```

| Callback | Use for |
|---|---|
| `onCreate(want, launchParam)` | once-per-instance setup; read the launch `Want` |
| `onWindowStageCreate(windowStage)` | `loadContent()`, subscribe to `windowStageEvent` |
| `onForeground` / `onBackground` | acquire/release resources tied to visibility |
| `onNewWant(want, launchParam)` | a new start request reaching an existing instance |
| `onWindowStageDestroy` | release what `onWindowStageCreate` acquired |
| `onDestroy` | final teardown |

Three things to hold on to:

- **These callbacks run on the main thread.** Anything heavy in `onCreate` or
  `onWindowStageCreate` is startup latency the user sees. Dispatch it (see
  `references/concurrency.md`).
- **`onNewWant` is easy to miss.** A relaunch of a singleton instance delivers its
  parameters here, not to `onCreate`. Deep links and share intents that "only work on cold
  start" are always this bug.
- Lifecycle behaviour when the main window goes to the background **differs by product
  type** (phone vs PC vs tablet). Do not assume `onBackground` timing is uniform across
  `deviceTypes`.

For cross-ability observation, register `ApplicationContext.onAbilityLifecycle()` rather
than instrumenting each ability.

## WindowStage

`onWindowStageCreate` is where the UI is attached:

```ts
onWindowStageCreate(windowStage: window.WindowStage): void {
  windowStage.loadContent('pages/Index', (err) => { /* check err */ });
  windowStage.on('windowStageEvent', (type: window.WindowStageEventType) => {
    // SHOWN / ACTIVE / INACTIVE / HIDDEN
  });
}
```

`SHOWN`/`HIDDEN` are foreground/background; `ACTIVE`/`INACTIVE` are focus gain/loss. They
are not interchangeable — a visible but unfocused window in a split-screen or PC layout is
`SHOWN` + `INACTIVE`, so pausing playback on `INACTIVE` stops audio the user can still see
playing.

Anything that needs the UI to exist — including a permission request — must run after
`loadContent()`/`setUIContent()` has completed, or from inside its callback.

## Context

`Context` is obtained from the ability (`this.context` in a UIAbility) or from the UI
(`UIContext.getHostContext()`). Types differ and so do their paths:

| Kind | Scope |
|---|---|
| `ApplicationContext` | whole application; lifecycle listeners, app-level dirs |
| `AbilityStageContext` | one module |
| `UIAbilityContext` | one UIAbility; `startAbility`, `terminateSelf`, window access |
| `ExtensionContext` | one ExtensionAbility |

Directory accessors (`filesDir`, `cacheDir`, `databaseDir`, `preferencesDir`,
`tempDir`, `distributedFilesDir`) resolve **relative to the context they came from** and
to the current area (`EL1`…`EL5`). A path captured from one context and used from another
silently points somewhere else. Never hardcode a sandbox path; always ask the context.

Do not hold a `UIAbilityContext` past the ability's lifetime — the classic leak is a
long-lived singleton that captured the context of an ability that has since been
destroyed.

Getting the global context via `getContext()` has a `UIContext` replacement
(`getHostContext()`); prefer it for the reasons in `references/arkui-navigation.md`.

## Launch types and Want

`launchType` in `module.json5` picks the instance policy:

| `launchType` | Behaviour |
|---|---|
| `singleton` (default) | one instance; a new start delivers `onNewWant` |
| `multiton` | a new instance per start request |
| `specified` | `AbilityStage.onAcceptWant()` returns a key; same key reuses the instance |

`Want` carries the start request: `bundleName`, `moduleName`, `abilityName`, `action`,
`entities`, `uri`, `type`, `parameters`. An explicit `Want` names the ability; an implicit
`Want` is matched against the `skills` declared by candidate abilities.

## HAP, HAR, HSP

| Kind | Nature | Notes |
|---|---|---|
| HAP | installable module | exactly one `entry` HAP; any number of `feature` HAPs |
| HAR | static library | code and resources are **copied** into each consumer |
| HSP | dynamic shared package | one copy at runtime, shared between HAPs |

A HAR linked into three HAPs triples that code and its resources in the package, and gives
you three independent copies of any module-level state inside it. A singleton that must
genuinely be one instance across HAPs belongs in an HSP.

Permissions declared in the `entry` module apply to the whole application; do not repeat
them in `feature` modules, and vice versa.

## module.json5

Lives at `<module>/src/main/module.json5`. Repeated keys are tolerated and **the last one
wins** — so a duplicated block is a silent override, not an error.

Fields that matter most:

| Field | Notes |
|---|---|
| `name` | must match `modules[].name` in the project `build-profile.json5` |
| `type` | `entry` / `feature` / `shared` / `har` |
| `deviceTypes` | the device classes you are promising to support and must test |
| `mainElement` | the module's entry component |
| `pages` | `$profile:main_pages` → `main_pages.json`; every `@Entry` page must be listed |
| `abilities[]` | `name`, `srcEntry`, `exported`, `skills`, `launchType`, start-window config |
| `requestPermissions[]` | see below |
| `metadata[]` | typed configuration blobs, e.g. distribution filters |
| `querySchemes` | schemes this module is allowed to probe with `canOpenLink` |
| `installationFree` | **generated** during build from `app.json5`'s `bundleType`; manual configuration does not take effect |

Per-ability start-window configuration is mandatory and has two generations. `startWindowIcon`
and `startWindowBackground` are non-optional tags; `startWindow` (a `$profile:` resource
pointing at `start_window.json`, with enhanced options since API 20) supersedes both — when
`startWindow` is set the other two stop taking effect. An ability declared with neither
fails packaging, which is why a hand-written extra ability so often builds in the IDE and
breaks in CI.

`minAPIVersion` and `targetAPIVersion` are **not `module.json5` tags at all** — they are
`app.json5` tags, and there they are generated during the build and cannot be manually
configured. The inputs are `compatibleSdkVersion` and `targetSdkVersion` in the
project-level `build-profile.json5` (`targetAPIVersion` falls back to `compileSdkVersion`).
So the fix for a hand-written `minAPIVersion` is to delete it and set the build profile —
not to move it to `app.json5`. See
`references/build-sign-verify.md`.

## Declaring permissions

```json5
"requestPermissions": [
  { "name": "ohos.permission.INTERNET" },
  {
    "name": "ohos.permission.LOCATION",
    "reason": "$string:location_permission_reason",
    "usedScene": { "abilities": ["EntryAbility"], "when": "inuse" }
  }
]
```

| Field | Rule |
|---|---|
| `name` | must be a permission the system defines; an invented name is rejected |
| `reason` | **mandatory** for `user_grant` and `manual_settings` permissions; must be a `$string:` resource reference and localized. A literal string fails verification |
| `usedScene` | **mandatory** for `user_grant` and `manual_settings`. `abilities` lists the UIAbility/ExtensionAbility names; `when` must be present and is exactly `inuse` or `always` |
| `requiredFeature` | system applications only; since 26.0.0 |

`system_grant` permissions (for example `ohos.permission.INTERNET`) need neither `reason`
nor `usedScene`.

The important part: an incomplete `user_grant` declaration **fails AppGallery release
verification**, not the build and not the runtime. It surfaces at submission time, which is
the worst moment to discover it. Review permission blocks whenever one is added.

`reason` wording is reviewed too: one concise sentence in the form "used for X" / "used to
do X", no filler, matching what the app actually does with the data. The system dialog
shows the permission *group*, so a `reason` that names a different capability than the
group reads as a mismatch.

## Runtime authorization

The contract for a `user_grant` permission:

1. Declare it (above) and associate the UI element that needs it, so the user understands
   the request.
2. `abilityAccessCtrl.createAtManager().checkAccessToken(tokenId, permission)` →
   `PERMISSION_GRANTED` or `PERMISSION_DENIED`.
3. If denied, `requestPermissionsFromUser()` to show the dialog.
4. Check the **result** and only then proceed.

The four rules that break naive implementations:

- **Re-check before every protected call.** The user can revoke a permission in Settings
  at any time, so a previously granted status does not persist. Caching the grant in
  `Preferences` and trusting the cache is the canonical bug: the call fails later with an
  error the code is not expecting.
- **Once the user has refused, the dialog does not appear again.** `requestPermissionsFromUser`
  returns without showing anything. The app must explain and route the user to the settings
  dialog (`requestPermissionOnSetting`) instead of re-prompting in a loop.
- **Do not request on startup.** Ask at the point of use with the rationale visible;
  bundling three requests into `onWindowStageCreate` reads as harvesting and is a review
  risk as well as a UX one.
- **If you must request in `onWindowStageCreate`, wait for the UI.** The request has to
  happen after `loadContent()`/`setUIContent()` completes, or from inside its callback —
  there is no UI to host the dialog before that.

Also: the system permission dialog must not be obscured. It takes precedence over your
components by default, but a full-screen overlay drawn at the same moment is a review
failure.

## Exported components and Want validation

`"exported": true` means **any application on the device can start this component**. For
each exported ability, three questions:

1. Does it need to be exported at all? The launcher entry does; a sync worker almost
   certainly does not. `exported: false` is the fix.
2. If it must be exported, is it guarded — by a permission entry on the ability, or by
   validating the caller?
3. Is every field of the incoming `Want` validated before use? Treat `parameters`, `uri`
   and `type` as attacker-controlled.

Never forward a caller-supplied ability name, bundle name or URI into `startAbility()` or a
URI-permission grant without checking it against an allowlist. That is the
intent-redirection privilege escalation: your app has permissions the caller does not, and
an unchecked forward lends them out.

<!-- sources: openharmony-docs, openharmony-sdk-js, corey-harmonyos, dengshiying-harmonyos, huawei-docs -->
