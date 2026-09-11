# Build, sign, release and verify on device

Verified against: HUAWEI Developer docs `doccenter-deveco-studio/ide-hvigor-commandline` and `ide-hvigor-build-profile-app`, `harmonyos-releases/app-compatibility-scenarios` (all `[official]`, read but not runnable on Linux CI); OpenHarmony `dfx/hdc`, `application-test/uitest-guidelines`, `application-test/unittest-guidelines`.

## Contents

- [API versions](#api-versions)
- [Project build-profile.json5](#project-build-profilejson5)
- [The three SDK fields](#the-three-sdk-fields)
- [hvigorw](#hvigorw)
- [Signing](#signing)
- [Release packaging](#release-packaging)
- [Obfuscation](#obfuscation)
- [Unit and UI tests](#unit-and-ui-tests)
- [hdc](#hdc)
- [Vision-driven device automation](#vision-driven-device-automation)
- [When the toolchain is absent](#when-the-toolchain-is-absent)

## API versions

The official ordering of recent API versions `[official]`:

```
26.0.0 > 6.1.1(24) > 6.1.0(23) > 6.0.2(22) > 6.0.1(21) > 6.0.0(20) > 5.1.1(19) > 5.1.0(18) > 5.0.5(17)
```

Two things follow, and both are easy to get wrong:

- **The version-number format changed at `26.0.0`.** From that version, HarmonyOS and
  OpenHarmony use the same string form and the `(n)` API-level suffix is gone:
  `"compatibleSdkVersion": "26.0.0"`. Before it, HarmonyOS used a string
  (`"6.1.1(24)"`) and OpenHarmony used a number (`24`). Do not invent a `"7.0.0(26)"`-style
  string; there is no such value.
- **A release-stage label is not an API level.** "HarmonyOS 6.0.2 Release" is API 22
  Release. Naming and API level are separate axes.

When a project does not state a baseline, read it from `build-profile.json5` rather than
assuming; when nothing says otherwise, API 20 (`6.0.0(20)`) is the conservative default for
this skill's guidance.

## Project build-profile.json5

Shape of the file (project root):

```json5
{
  "app": {
    "signingConfigs": [ { "name": "...", "type": "HarmonyOS", "material": { /* … */ } } ],
    "products": [ {
      "name": "default",                     // a product named "default" must exist
      "signingConfig": "default",            // omitted => the product is NOT signed
      "bundleName": "com.example.shopdemo",
      "compatibleSdkVersion": "6.0.0(20)",
      "targetSdkVersion": "6.0.0(20)",
      "runtimeOS": "HarmonyOS",              // or "OpenHarmony"
      "arkTSVersion": "1.1",                 // ArkTS checker version, API 11+ projects
      "bundleType": "app",                   // app | atomicService | shared
      "versionCode": 1000000,
      "versionName": "1.0.0"
    } ],
    "buildModeSet": [ { "name": "debug" }, { "name": "release" }, { "name": "test" } ]
  },
  "modules": [ { "name": "entry", "srcPath": "./entry",
                 "targets": [ { "name": "default", "applyToProducts": ["default"] } ] } ]
}
```

- `modules[].name` must equal `module.name` in that module's `module.json5`.
- `buildModeSet` always has `debug`, `release` and `test`; `test` is selected automatically
  when the test framework runs, even though it is not written in the file.
- `debuggable` defaults to `false` only in `release` mode; in every other mode it defaults
  to `true`, and a `debuggable` artifact ships source maps in `ets/sourceMaps.map`.

## The three SDK fields

| Field | Meaning | Consequence of getting it wrong |
|---|---|---|
| `compatibleSdkVersion` | **minimum** API version the app runs on. Required. | The app cannot install below it, and AppGallery simply stops distributing to those devices. No error surfaces anywhere; the install base shrinks silently |
| `targetSdkVersion` | the API version whose behaviour the app is adapted to. Optional; **defaults to `compileSdkVersion`** | Version-isolated behaviour changes are keyed on this value, so upgrading it opts you into new behaviour for every isolated change at once |
| `compileSdkVersion` | the SDK used to compile. On HarmonyOS it should be left unset (the bundled DevEco SDK is used) and may only be set to the DevEco-matched version. On OpenHarmony it is **required** | Setting an arbitrary value on HarmonyOS is rejected; leaving it unset on OpenHarmony fails the build |

They are independent. Compiling with a new SDK while keeping `compatibleSdkVersion` low is
the normal way to adopt new APIs without dropping devices — combined with a runtime
availability check (`canIUse`) around anything newer than the compatible version.

Version-isolated behaviour changes mean an app built against an older `targetSdkVersion`
keeps the pre-change behaviour on a newer device. Non-isolated changes do not: they take
effect regardless, and the release notes list them as requiring adaptation. So "our app
still works on the new OS" needs checking against the change list, not just against your
own test pass.

In the built artifact these surface as `app.json5`'s `minAPIVersion` and
`targetAPIVersion`. Those are **outputs**: the tags exist in `app.json5`, are generated
during the build, and cannot be manually configured. They are not `module.json5` tags at
all, so relocating a hand-written value from `module.json5` to `app.json5` is not a fix
either — delete it and set the build profile.

## hvigorw

`hvigorw [tasks...] <options>`. Tasks other than `-v`/`-h`/`version`/`--help` must run from
the project root (that restriction relaxed in hvigorw 5.18.4).

```bash
hvigorw --version
hvigorw buildInfo -p json                 # product/target/buildMode actually in effect
hvigorw clean --no-daemon
hvigorw assembleHap --no-daemon           # default buildMode: debug
hvigorw assembleHsp --no-daemon
hvigorw assembleHar --no-daemon
hvigorw assembleApp --no-daemon           # default buildMode: release
hvigorw tasks / taskTree                  # what exists, and in what order
hvigorw prune                             # drop unused Hvigor cache and pnpm packages
```

Useful parameters:

| Parameter | Effect |
|---|---|
| `-p buildMode=debug\|release` | override the default (HAP/HSP/HAR default debug, App defaults release) |
| `-p product=<name>` | build a specific product; defaults to `default` |
| `-p module=<mod>@<target>` | build specific modules; **requires `--mode module`**; comma-separate several |
| `-p debuggable=true\|false` | overrides the buildMode's `debuggable` |
| `--no-daemon` | recommended in CI and for one-shot command-line builds |
| `-i` / `-d` / `--stacktrace` | raise log level; stack traces are off by default |
| `--analyze=normal\|advanced\|ultrafine` | Build Analyzer data; `ultrafine` adds ArkTS-phase detail and slows the build |
| `--no-incremental` / `--no-parallel` | disable incremental / parallel build when diagnosing |
| `--type-check` | type-check `hvigorfile.ts` (off by default) |

`hvigorw` needs JDK and Node.js configured on `PATH`. `ohpm install` resolves
`oh-package.json5` dependencies before the first build.

Diagnosing a build that behaves differently from the IDE: run `hvigorw buildInfo -p json`
first. Most "works in DevEco, fails on CI" reports are a different product, target or
buildMode, not a different toolchain.

## Signing

Signing configs live in the project `build-profile.json5` under `app.signingConfigs`, and a
product opts in by name:

```json5
{
  "app": {
    "signingConfigs": [ {
      "name": "default",
      "type": "HarmonyOS",                    // or "OpenHarmony"
      "material": {
        "storeFile":     "./signing/app.p12", // keystore
        "storePassword": "<ciphertext written by DevEco>",
        "keyAlias":      "appKey",
        "keyPassword":   "<ciphertext written by DevEco>",
        "certpath":      "./signing/app.cer", // certificate
        "profile":       "./signing/app.p7b", // provisioning profile
        "signAlg":       "SHA256withECDSA"    // the only documented value
      }
    } ],
    "products": [ { "name": "default", "signingConfig": "default" } ]
  }
}
```

Material roles: `.p12` keystore, `.cer` certificate, `.p7b` profile (bundle name,
certificate info, permissions, and for debug profiles the allow-listed device list). A
`.csr` is the request used to obtain the `.cer` and is not part of `material`.

Rules that cause real failures:

- **A product with no `signingConfig` is not signed at all.** The build succeeds and the
  artifact cannot be installed or submitted.
- **The name is not the type.** Calling a config `release` proves nothing; what matters is
  which `.cer`/`.p7b` it points at. A debug profile carries a device allow-list and is not
  acceptable for release. A release profile has an empty device list.
- The `.p12`, `.cer` and `.p7b` must be a matching set, together with the alias and both
  passwords. Mixing materials from two rounds of provisioning yields keystore-password and
  certificate-mismatch errors that look like password bugs.
- `storePassword`/`keyPassword` are stored as **ciphertext** by the IDE. Those ciphertexts
  are not the plaintext that command-line signing tools expect; do not copy them into a
  script.
- Relative paths resolve from the **project root**, not the module.
- Do not commit `.p12` or passwords. In CI, inject the material and write the signing block
  at build time.

Automatic signing (`File > Project Structure > Project > Signing Configs` →
*Automatically generate signature*) requires a signed-in Huawei account and fills the
`material` block for you. Associating a registered AGC application, which also syncs the
app's open capabilities and permissions, is supported from DevEco Studio 6.0.0 Beta5.

## Release packaging

`hvigorw assembleApp` produces the `.app` bundle for AppGallery; HAP/HSP artifacts are
produced alongside unless `packOptions.fastBuildApp` or `buildAppSkipSignHap` says
otherwise. The packing tool validates that the `compatibleSdkVersion` and
`targetSdkVersion` of every HAP and HSP in the bundle agree — an HSP left on an older
compatible version fails packaging, which is where a multi-module version drift finally
shows up.

Before submission, re-check: permission declarations complete (see
`references/stage-model.md`), `versionCode` strictly increased, `deviceTypes` matching what
was actually tested, no `debuggable` artifact, privacy statement present, and every
`user_grant` permission's `reason` matching real behaviour.

## Obfuscation

ArkGuard is configured per module (`obfuscation-rules.txt`, enabled in the module's
`build-profile.json5`); bytecode obfuscation is a separate, stronger mode. Two practical
notes: names reached reflectively or by resource lookup must be kept explicitly, and
obfuscated release builds change stack traces — keep the mapping output with the build or
crash reports become unreadable.

## Unit and UI tests

The test framework is arkxtest: **JsUnit** for unit tests (`describe`/`it`/`expect`) and
**UITest** for UI tests. UITest is driven from a JsUnit script and combined with
`AbilityDelegator` to start the target application and assert on its state.

Shape of a UI test: start the ability with `AbilityDelegator`, find components through
UITest's matchers, perform the interaction (tap, double-tap, long press, swipe, text input,
key/mouse/stylus events), then assert the resulting page state. Keep assertions on
behaviour; UITest also has a command-line mode for screenshots, component trees, recording
and event injection, which is what the `hdc` workflow below uses.

Run tests from the command line with the coverage flags
(`-p ohos-test-coverage=true` / `-p coverage=true`) when a coverage report is wanted.

## hdc

`hdc` (HarmonyOS Device Connector) ships with DevEco Studio and runs on Windows, Linux and
macOS.

```bash
hdc list targets -v                 # discover; -v adds connection detail
hdc -t <connect-key> shell <cmd>    # always name the target when several are connected
hdc install <package>
hdc uninstall <bundleName>
hdc file send <local> <remote>
hdc file recv <remote> <local>
hdc shell aa start -a <ability> -b <bundle>
hdc shell aa dump -l                # running abilities; find the foreground bundle
hdc shell bm dump -n <bundle>       # installed bundle info
hdc shell hilog                     # logs
hdc shell hidumper -s <service>     # system service state
hdc shell uitest dumpLayout -p /data/local/tmp/layout.json
hdc shell uitest screenCap -p /data/local/tmp/shot.png
hdc shell uitest uiInput click <x> <y>
```

Notes that save time:

- Pick targets explicitly. With a phone and an emulator attached, an un-targeted command
  goes wherever the daemon feels like.
- `hdc shell -b <bundleName>` runs in the **debug app's working directory**, which is not
  the same as the application data sandbox. To find real sandbox paths, get the foreground
  bundle from `aa dump -l` and use the `Context` directory APIs rather than guessing a path.
- Coordinates from `uitest dumpLayout` are raw device pixels. Never reuse coordinates taken
  from a scaled screenshot preview.
- The emulator requires a Huawei account signed in to DevEco Studio; launching it purely
  from the command line is not a supported path, and the failure message ("please sign in
  and start the emulator from Device Manager") is about the incomplete CLI launch path, not
  about your account.

## Vision-driven device automation

For interactions that are easier to state in natural language than in selectors, drive the
device from screenshots with Midscene's HarmonyOS CLI:

```bash
npx -y @midscene/harmony@1 connect [--deviceId <id>]
npx -y @midscene/harmony@1 launch --uri com.example.shopdemo
npx -y @midscene/harmony@1 runhdcshell --command "hidumper -s RenderService -a screen"
```

It needs `hdc` on `PATH` (or `HDC_HOME` set) and a vision-capable model configured through
`MIDSCENE_MODEL_*` environment variables or a `.env` file in the working directory.

Three constraints are structural, not stylistic:

- **Never run these commands in the background.** The loop is screenshot → analyze → act;
  backgrounding breaks it because you decide the next action without having seen the result
  of the last one.
- **One command at a time.** Wait for it to finish, read the screenshot, then decide.
- **Allow time.** Each command involves model inference plus real device interaction —
  roughly a minute, and longer for complex actions.

Capability boundary on HarmonyOS: tap, double-tap, long press, type, clear text, scroll,
drag, key presses and system navigation (Back, Home, recents) are available. **Two-finger
zoom is not**, because the underlying HarmonyOS automation layer does not expose
multi-touch input. Do not plan a pinch-zoom verification around it.

## When the toolchain is absent

The HarmonyOS SDK, DevEco Studio and `hdc` are not present on a generic Linux CI image, and
there is no supported headless install path. When any of the SDK, a device, an emulator or
a Huawei account is missing:

- Say exactly which prerequisite is missing and what it blocks.
- Do not describe an unrun build or an unrun test as passing.
- Static review of `.ets`, `module.json5` and `build-profile.json5` is still fully
  available and is where most defects in this skill's Core rules live — do that, and mark
  the rest as unverified.

<!-- sources: huawei-docs, openharmony-docs, midscene-harmony, linhay-harmony-next, dengshiying-harmonyos -->
