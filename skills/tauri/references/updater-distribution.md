# Updater, code signing and distribution

Verified against: Tauri 2.x

## Contents

- The updater in one page
- Configuration keys that decide whether it works
- Static manifest vs dynamic server
- Checking and installing from the app
- macOS signing and notarisation
- Windows signing and installers
- Linux packaging
- CI

## The updater in one page

The updater is a plugin (`tauri-plugin-updater`, desktop only). It downloads an artifact,
verifies a signature made with a Tauri-specific key pair, and replaces the installed app. The
signature check **cannot be disabled**, so the key pair is part of the release process, not an
optional hardening step.

```bash
tauri signer generate -w ~/.tauri/myapp.key
```

That writes the private key (keep it secret and backed up — losing it means existing installs
can never be updated again) and prints the public key, which goes into the config.

At build time the private key must be in the environment:

```bash
export TAURI_SIGNING_PRIVATE_KEY="…"          # path or key content
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="…" # if the key has one
```

A `.env` file is **not** read for these. If the variables are missing, the build simply
produces no `.sig` files, which then shows up much later as an update that fails verification.

## Configuration keys that decide whether it works

```json
{
  "bundle": { "createUpdaterArtifacts": true },
  "plugins": {
    "updater": {
      "pubkey": "<content of the generated .pub file>",
      "endpoints": ["https://releases.example.com/{{target}}/{{arch}}/{{current_version}}"],
      "windows": { "installMode": "passive" }
    }
  }
}
```

| Key | The trap |
|---|---|
| `bundle.createUpdaterArtifacts` | Without it there is no update bundle and no `.sig` at all. `true` for apps whose whole history is v2; `"v1Compatible"` **only** while v1 installs still exist in the wild — it is scheduled for removal in v3, so flip it to `true` once users have migrated. |
| `pubkey` | Must be the key **content**. A file path is rejected. |
| `endpoints` | Array of URLs. TLS is enforced in production; `dangerousInsecureTransportProtocol` is the only escape and does not belong in a release. Tauri moves to the next URL **only** on a non-2XX response, so a server that answers 200 with a wrong body ends the search. |
| `windows.installMode` | `"passive"` (default, progress window, no interaction) is the right choice for almost everyone. `"quiet"` cannot request elevation, so it works only for per-user installs or an already-elevated app. `"basicUi"` requires the user to click through. |

The URL placeholders are `{{current_version}}`, `{{target}}` (`linux`/`windows`/`darwin`) and
`{{arch}}` (`x86_64`/`i686`/`aarch64`/`armv7`). Custom placeholders do not exist; a custom
`{{target}}` string is the supported way to encode a channel or variant, and it is then matched
against the manifest's `platforms` keys.

Artifacts produced with `createUpdaterArtifacts: true`: the AppImage plus `.sig` on Linux, a
`.app.tar.gz` plus `.sig` on macOS, the NSIS `-setup.exe` and/or MSI plus `.sig` on Windows.

## Static manifest vs dynamic server

Static JSON (S3, GitHub Releases, any CDN):

```json
{
  "version": "1.5.0",
  "notes": "…",
  "pub_date": "2026-09-11T10:00:00Z",
  "platforms": {
    "darwin-aarch64": { "signature": "<content of the .sig>", "url": "https://…/app.app.tar.gz" },
    "windows-x86_64": { "signature": "<content of the .sig>", "url": "https://…/app-setup.exe" },
    "linux-x86_64":   { "signature": "<content of the .sig>", "url": "https://…/app.AppImage" }
  }
}
```

- `signature` is the **content** of the `.sig` file, which changes with every build. A path or
  URL there does not work.
- Platform keys are `OS-ARCH`. Required fields are `version` plus each platform's `url` and
  `signature`.
- Tauri validates the **whole file** before it even compares versions, so one malformed or
  half-filled platform entry breaks updates for every platform.
- `version` may carry a leading `v`; `pub_date` must be RFC 3339 if present.

Dynamic server: reply `204 No Content` when there is nothing to update and `200` with
`{ version, url, signature, notes?, pub_date? }` otherwise. The plugin still enforces its own
version comparison unless you override `version_comparator`, which is what makes a deliberate
rollback possible. Extra request headers can be added on the Rust `UpdaterBuilder`.

`tauri-action` (GitHub Action) generates the static manifest as part of a release, which is the
least error-prone route for a small project.

## Checking and installing from the app

```ts
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

const update = await check();
if (update) {
  await update.downloadAndInstall((e) => {
    if (e.event === 'Started') total = e.data.contentLength;
    if (e.event === 'Progress') done += e.data.chunkLength;
  });
  await relaunch();
}
```

Relaunching needs the **process** plugin, and the frontend needs both plugins' permissions.
`download()` and `install()` can be called separately when the UI should ask before installing.

From Rust, `app.updater()?.check().await?` plus `download_and_install(...)`, then
`app.restart()`. When the check runs in `setup`, spawn it on the async runtime rather than
blocking startup. Reporting progress to the frontend from a Rust-driven update is what
channels are for: keep the pending `Update` in managed state (`Mutex<Option<Update>>`) between
a `fetch_update` and an `install_update` command, since the update object is not serialisable.

## macOS signing and notarisation

Signing needs a paid Apple Developer account and an actual Mac. Certificate types:
`Developer ID Application` for distribution outside the App Store, `Apple Distribution` for
the store.

- Locally: install the certificate, find the identity with
  `security find-identity -v -p codesigning`, and set it as `bundle.macOS.signingIdentity` or
  `APPLE_SIGNING_IDENTITY`.
- In CI: export the certificate as `.p12`, base64 it
  (`openssl base64 -A -in cert.p12 -out cert.txt`), and provide `APPLE_CERTIFICATE` plus
  `APPLE_CERTIFICATE_PASSWORD`; the workflow creates a temporary keychain and imports it.
- **Notarisation is required with a Developer ID certificate.** Provide either App Store
  Connect API credentials (`APPLE_API_ISSUER`, `APPLE_API_KEY`, `APPLE_API_KEY_PATH`) or Apple
  ID credentials (`APPLE_ID`, `APPLE_PASSWORD` as an app-specific password, `APPLE_TEAM_ID`),
  then rebuild — notarisation happens during bundling. A free account cannot notarise, so the
  app still shows as unverified.
- `signingIdentity: "-"` is an ad-hoc signature. It satisfies the Apple Silicon requirement
  that downloaded code be signed at all, but users still have to allow the app in Privacy &
  Security.

## Windows signing and installers

- `.msi` (WiX v3) can only be built **on Windows**. NSIS (`-setup.exe`) can be cross-compiled
  from Linux or macOS with NSIS installed, which is the usual way to produce Windows artifacts
  from CI that is not Windows.
- Signing an OV/EV certificate installed in the machine store: set
  `bundle.windows.certificateThumbprint`, `digestAlgorithm` (typically `sha256`) and a
  `timestampUrl`. For anything else — Azure Key Vault, HSM-backed EV certificates, a vendor
  tool — use the custom sign command hook instead of trying to fit it into those three fields.
- Signing is what avoids the SmartScreen warning: an EV certificate has reputation
  immediately, an OV certificate accumulates it, so early OV-signed downloads still warn.
- `bundle.windows.webviewInstallMode` decides how WebView2 reaches machines that lack it:
  the downloading bootstrapper (default, smallest), `embedBootstrapper`, or `offlineInstaller`
  (largest, works without network). Choose deliberately if the app targets offline machines.

## Linux packaging

`.deb`, `.rpm` and AppImage come from `bundle.linux.*`. AppImage is the artifact the updater
uses. Packaging is not signing: distribution channels have their own requirements (an AUR
package, a Flatpak manifest, a repository key), and none of them replace the updater's own
signature. Build on the oldest glibc you intend to support, because the binary will not run on
older systems than the one it was linked on.

## CI

- Build each platform on its own runner (or cross-compile NSIS deliberately), and keep the
  signing secrets per platform: Apple certificate and notarisation credentials, Windows
  certificate, and `TAURI_SIGNING_PRIVATE_KEY` for the updater on all of them.
- Verify a real end-to-end update before announcing a release: install the previous version,
  publish the manifest, and watch the app download, verify, install and relaunch. A
  configuration mistake in the updater is invisible in the build log and only fails on the
  users' machines.

<!-- sources: tauri-docs, nodnarbnitram-tauri-v2, hairyf-tauri, full-stack-skills-tauri -->
