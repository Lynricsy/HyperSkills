# Expo app config, builds and EAS

Verified against: Expo SDK 54–57, EAS CLI 16+.

## Contents

- [Four project shapes](#four-project-shapes)
- [App config and prebuild](#app-config-and-prebuild)
- [Config plugins](#config-plugins)
- [Development builds vs Expo Go](#development-builds-vs-expo-go)
- [EAS Build](#eas-build)
- [EAS Update: the object model](#eas-update-the-object-model)
- [Deciding update or build](#deciding-update-or-build)
- [Publishing](#publishing)
- [Verifying an update on a device](#verifying-an-update-on-a-device)
- [An installed build did not update](#an-installed-build-did-not-update)
- [Store submission](#store-submission)
- [Old patterns](#old-patterns)

## Four project shapes

| Shape | Signal | Consequence |
|---|---|---|
| Bare React Native | no `expo` dependency | native dirs are yours; no app config, no EAS unless added |
| Expo with prebuild (CNG) | `expo` present, `ios/`/`android/` **not** committed | native dirs are generated; hand edits are lost |
| Expo with committed native dirs | `expo` present, `ios/`/`android/` committed | edits persist; app-config native fields no longer apply themselves |
| Expo Go only | no development build in use | stock SDK modules only |

Establish the shape before proposing any native change; the same request has a
different correct answer in each row.

## App config and prebuild

- `app.json` / `app.config.js` / `app.config.ts` is the source of truth for
  native configuration in a prebuild project: identifiers, permissions, icons,
  splash, schemes, plugins, runtime version policy.
- `npx expo prebuild` generates `ios/` and `android/` from that config;
  `--clean` deletes and regenerates them. Any hand edit inside those
  directories is discarded on the next run — which happens on every EAS Build
  for a project without committed native dirs.
- A dynamic `app.config.ts` can read environment variables, but it is evaluated
  at build/bundle time. Runtime values belong in the app, not the config.
- `npx expo install <pkg>` (not the raw package manager) resolves a version
  compatible with the installed SDK. `npx expo install --fix` repairs a
  mismatched set after an SDK bump.
- `npx expo-doctor` catches the common structural problems: version mismatches,
  a package that needs a plugin, native dirs that have drifted from the config.

## Config plugins

A config plugin is how a native change survives prebuild: it is a function that
edits the generated native project (manifest entries, Info.plist keys,
build settings, entitlements) during generation.

- Prefer the plugin an SDK package already ships; add it to `plugins` in the app
  config rather than editing generated files.
- Write a plugin when the change is genuinely project-specific — a custom URL
  scheme handler, an extra permission string, a Gradle property.
- Custom fonts, icons and similar assets are plugin territory too, not manual
  copies into `ios/`.

## Development builds vs Expo Go

- Expo Go runs a fixed set of SDK modules. Any custom native code, any
  third-party native library outside the SDK, and any config-plugin effect
  requires a development build.
- A development build is the real app binary with the dev client attached, so it
  loads the local bundle from Metro while behaving like the shipped app
  natively. Use it as the default development environment for anything
  production-bound.
- Expo Go's update behaviour differs from a release build's; never validate
  over-the-air delivery there.

## EAS Build

- Build profiles live in `eas.json`. A profile can set distribution, whether the
  dev client is included, autoincrement, environment, and — importantly — the
  **channel** that gets compiled into the binary.
- The channel is fixed at build time. Changing `eas.json` afterwards does not
  change what an installed build asks for.
- `eas build:configure` creates and repairs the file; prefer it to writing
  profiles by hand, then read the diff.
- A build's runtime version comes from the runtime-version policy in the app
  config. It is the compatibility boundary for updates, so changing the policy
  is a decision about which installed builds can receive future updates — never
  an incidental fix.

## EAS Update: the object model

Five objects, and every delivery question is answered by how they line up:

- **Build** — the installed binary. Contains native code, an embedded update, a
  platform, a runtime version, and a channel fixed at build time.
- **Update** — a published JavaScript bundle plus assets, for one platform and
  one runtime version.
- **Branch** — an ordered stream of updates; its newest compatible update is
  active.
- **Channel** — the stable deployment target embedded in builds. On the server
  it points at a branch.
- **Runtime version** — the compatibility boundary between an update and the
  native code in a build.

```text
installed build (channel: production-v5, runtime: 5.2.1, platform: ios)
  -> production-v5 channel
  -> whichever branch that channel currently points at
  -> newest update for runtime 5.2.1 and ios
```

A build receives an update only when the platform and runtime version match
**and** its embedded channel points at the branch holding that update. Channels
and branches often share a name and are still different objects: publishing to a
branch called `production` does nothing for builds whose channel is
`production-v5` unless that channel maps to it. `eas channel:edit` remaps the
channel server-side for every build on it; it cannot change the channel baked
into one installation.

## Deciding update or build

Ship as an update: JavaScript, styling, and bundled assets that the installed
native runtime already supports.

Ship a new build: anything that adds or changes native code or native
configuration — a new native dependency, a native app-config field, a config
plugin change, an SDK or React Native bump. No publish makes native capability
appear in an installed binary, and no runtime-version change should be used to
smuggle one past the compatibility check.

## Publishing

```bash
npx eas-cli@latest update --help          # confirm flags for the installed CLI
npx eas-cli@latest update \
  --channel <channel> \
  --message "<what changed>" \
  --environment <environment>
```

- Publish against the **channel** the target builds embed, or against a branch
  you have confirmed that channel points at.
- Newer SDKs require an environment for publishing, and the environment decides
  which variables the exported bundle receives — choose it deliberately rather
  than accepting a default.
- Validate on a preview or staging channel first, then promote the tested
  artifact. A production publish changes what installed users run: it needs
  explicit approval, and the current Git branch is not approval.

## Verifying an update on a device

A release build prioritises launch speed. With default launch behaviour it
starts on its embedded or cached update while downloading a new one in the
background, and runs the download at the next launch. So manual QA is:

1. Fully terminate the app (terminate, not background) and reopen — this launch
   discovers and downloads.
2. Fully terminate and reopen again — this launch runs the downloaded update.

Describe it as *up to two cold launches*. It is not a TestFlight quirk; it is the
default update lifecycle. Do not raise `fallbackToCacheTimeout` to skip the
second launch: that trades startup latency and launch reliability for update
immediacy. If the product needs immediate updates, use the `expo-updates` APIs
to check, fetch and offer a restart in the UI.

## An installed build did not update

Check in this order; each step rules out a whole class:

1. Was the update published to the intended project, channel/branch, platform
   and environment?
2. Does the installed build's platform and runtime version match the update?
3. Was the build actually compiled with the current update URL and channel?
   App-config changes only take effect in a new binary.
4. Where does the channel point? Inspect the channel-to-branch mapping and the
   active update on that branch (`eas channel:view`, `eas branch:view`).
5. Did the launch lifecycle get its two cold starts?
6. Only then look at logs and the export.

## Store submission

- The store binary is a build, so every store release starts with a build whose
  channel and runtime version are the ones you intend to serve updates to.
- In-app digital goods and subscriptions must go through the platforms' in-app
  purchase systems. Shipping a web payment SDK for them is a policy violation
  and a rejection, not a technical preference — decide this before writing the
  paywall, because it changes the revenue model.
- Permission strings, privacy declarations and tracking disclosures are native
  configuration: in a prebuild project they belong in the app config or a
  plugin, and a missing one fails review rather than the build.

## Old patterns

<details>
<summary><code>expo eject</code> and the "managed vs bare" split</summary>

The old model was a one-way door: a managed project ejected to a bare project
and never went back. The current model is continuous native generation — native
dirs are a build artefact you can regenerate at will, or commit and own. Advice
framed as "you have to eject to do X" is describing the old model; the question
today is whether the native dirs are committed.

</details>

<!-- sources: expo-official, expo-docs, callstack-rn -->
