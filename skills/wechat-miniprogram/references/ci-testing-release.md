# CI, testing and release

Verified against: `miniprogram-ci` 2.1.31, `miniprogram-simulate` (latest published).

## Contents

- [What miniprogram-ci is and is not](#what-miniprogram-ci-is-and-is-not)
- [Credentials](#credentials)
- [The project object](#the-project-object)
- [upload](#upload)
- [preview](#preview)
- [packNpm](#packnpm)
- [Reading the size gate correctly](#reading-the-size-gate-correctly)
- [A CI script that holds up](#a-ci-script-that-holds-up)
- [Robots and concurrency](#robots-and-concurrency)
- [Source maps](#source-maps)
- [Unit testing with miniprogram-simulate](#unit-testing-with-miniprogram-simulate)
- [Version flow and release](#version-flow-and-release)
- [Things that get a submission rejected](#things-that-get-a-submission-rejected)

## What miniprogram-ci is and is not

It is the compile module extracted from the WeChat Developer Tools, published on npm,
runnable headlessly. It does: upload, preview, build npm, fetch the source map of the
last uploaded build, and the CloudBase upload operations (out of scope here).

It does **not** submit for review, release, roll back, set the experience version, or
read the review status. Those live on the mini program platform and, for third-party
platforms, in the WeChat open APIs. `ci.submitAudit` does not exist; calling it is a
`TypeError` at run time, which is exactly the kind of bug that only appears on the
first green build.

The upload key's own permissions are preview and upload — nothing else would be
authorised anyway.

## Credentials

The key comes from the mini program platform under development settings, "code upload
key". Two properties matter:

- It is **not recoverable**. Losing it means resetting it, which invalidates every
  pipeline using it.
- It can be constrained by an **IP allowlist**, and the platform recommends enabling it.
  A hosted CI runner has no stable egress IP, so this is a real decision: either run a
  self-hosted runner or a fixed-egress proxy (`ci.proxy(...)`), or accept that the
  allowlist is off. Pick one deliberately and write it down; do not discover it when the
  build fails.

Handle the key as a file with restricted permissions, written and deleted inside the
job:

```javascript
const os = require('os'), fs = require('fs'), path = require('path')

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mp-ci-'))
const keyPath = path.join(dir, 'private.key')
fs.writeFileSync(keyPath, requireEnv('MP_PRIVATE_KEY'), { mode: 0o600 })
try { /* … */ } finally { fs.rmSync(dir, { recursive: true, force: true }) }
```

`requireEnv` must throw when the variable is missing. A `process.env.X || 'placeholder'`
default converts "the secret was not injected" — which happens on every fork pull
request — into an authentication error that looks like a key problem.

## The project object

```javascript
const project = new ci.Project({
  appid: 'wx…',                       // required
  type: 'miniProgram',                // miniProgram | miniProgramPlugin | miniGame | miniGamePlugin
  projectPath: '/abs/path/to/project',// the directory containing project.config.json
  privateKeyPath: keyPath,            // a path
  ignores: ['node_modules/**/*'],
})
```

Two field-level traps:

- `privateKey` takes the key **contents**; `privateKeyPath` takes a path. Passing a path
  as `privateKey` fails as an authentication error, with nothing pointing at the cause.
- `type` is case-sensitive and camel-cased. `'miniprogram'` is not a valid value.

`projectPath` must be the directory holding `project.config.json`, which is not always
the repository root, and is not necessarily `miniprogramRoot` either. Construct the
project only when the source tree is complete — the constructor reads files.

## upload

```javascript
const result = await ci.upload({
  project,
  version: '1.4.2',          // required
  desc: 'main@abc1234',      // optional
  robot: 3,                  // 1–30
  setting: { es6: true, minify: true, autoPrefixWXSS: true },
  threads: 4,
  onProgressUpdate: console.log,
})
```

`setting` accepts `useProjectConfig`, `es6`, `es7`, `minify`, `minifyJS`, `minifyWXML`,
`minifyWXSS`, `autoPrefixWXSS`, `codeProtect`, `disableUseStrict`, `compileWorklet`,
`targetPlatform`. Setting `useProjectConfig: true` takes the settings from
`project.config.json` instead, which is the way to keep CI and the IDE in step.

`compileWorklet` matters for Skyline pages using worklet animation.

The result is `{ subPackageInfo, pluginInfo, devPluginId, strUint64Version }`.

## preview

Same options plus:

| Option | Note |
|---|---|
| `qrcodeFormat` | `'terminal'` (default, debugging only), `'image'`, `'base64'` |
| `qrcodeOutputDest` | Required — where the QR file is written |
| `pagePath` | Page to open |
| `searchQuery` | Query string; `&` needs escaping on a command line |
| `scene` | Default 1011 |

A preview on every merge to the default branch is usually waste: it costs a full
compile and nobody scans it. Trigger previews from pull requests or manually.

## packNpm

```javascript
const warnings = await ci.packNpm(project, {
  ignores: [],
  reporter: (info) => console.log(info),
})
```

This produces the `miniprogram_npm` directory, which is what actually ships — the raw
`node_modules` is not uploaded. A project with npm dependencies that uploads without
this step ships a mini program whose imports resolve to nothing at run time.

`ci.packNpmManually({ packageJsonPath, miniprogramNpmDistDir })` covers the layout where
the dependencies being built live outside the mini program directory.

## Reading the size gate correctly

`subPackageInfo` entries:

| `name` | Means | Cap |
|---|---|---|
| `__FULL__` | Whole mini program | 30 MB (20 MB service-provider-developed) |
| `__APP__` | Main package | 2 MB |
| anything else | That subpackage | 2 MB |

```javascript
const MAIN_CAP = 2 * 1024 * 1024        // per package, platform limit
const TOTAL_CAP = 30 * 1024 * 1024      // whole mini program, platform limit

for (const pkg of result.subPackageInfo ?? []) {
  const cap = pkg.name === '__FULL__' ? TOTAL_CAP : MAIN_CAP
  if (pkg.size > cap) throw new Error(`${pkg.name} ${pkg.size} > ${cap}`)
}
```

Comparing `__FULL__` against 2 MB fails every project that has subpackages; comparing
only `__FULL__` lets an oversized main package through. Check every entry.

Note the gate is retrospective: by the time you read the sizes the version is already
on the platform. It stops the pipeline, not the upload.

## A CI script that holds up

```javascript
// ci/upload.js
const ci = require('miniprogram-ci')
const fs = require('fs'), os = require('os'), path = require('path')

function requireEnv(name) {
  const v = process.env[name]
  if (!v) throw new Error(`missing required environment variable ${name}`)
  return v
}

async function main() {
  const projectPath = process.env.GITHUB_WORKSPACE || process.cwd()
  if (!fs.existsSync(path.join(projectPath, 'project.config.json'))) {
    throw new Error(`project.config.json not found in ${projectPath}`)
  }
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mp-ci-'))
  const keyPath = path.join(dir, 'private.key')
  fs.writeFileSync(keyPath, requireEnv('MP_PRIVATE_KEY'), { mode: 0o600 })

  try {
    const project = new ci.Project({
      appid: requireEnv('MP_APPID'),
      type: 'miniProgram',
      projectPath,
      privateKeyPath: keyPath,
      ignores: ['node_modules/**/*'],
    })

    const robot = Number(process.env.MP_CI_ROBOT || 1)
    if (!Number.isInteger(robot) || robot < 1 || robot > 30) {
      throw new Error(`robot must be an integer in 1..30, got ${process.env.MP_CI_ROBOT}`)
    }

    await ci.packNpm(project, { reporter: (i) => console.log(i) })

    const version = requireEnv('MP_VERSION')          // from the tag, not package.json
    const result = await ci.upload({
      project, version, robot,
      desc: `${process.env.GITHUB_REF_NAME}@${(process.env.GITHUB_SHA || '').slice(0, 8)}`,
      setting: { useProjectConfig: true },
      onProgressUpdate: (t) => console.log(typeof t === 'string' ? t : t.message),
    })
    console.log(JSON.stringify(result.subPackageInfo, null, 2))
    // size gate here
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}

main().catch((e) => { console.error(e.stack || e.message); process.exitCode = 1 })
```

`process.exitCode` rather than `process.exit(1)`, so buffered output is flushed. Log
`e.stack`, not the whole error object, which can carry request parameters.

Deriving `version` from `package.json` means every merge uploads the same version
number and overwrites the previous build under the same robot. Derive it from the tag,
or append the run number.

## Robots and concurrency

Robot numbers 1–30 each keep their own upload record. Reserve one per pipeline (CI on
the default branch, release tags, a manual escape hatch) so the platform's version list
is attributable.

Two jobs uploading with the same robot at the same time race. Serialise the job:

```yaml
concurrency:
  group: mp-upload
  cancel-in-progress: false     # an upload must not be cancelled halfway
```

## Source maps

```javascript
await ci.getDevSourceMap({ project, robot: 3, sourceMapSavePath: './sm.zip' })
```

Fetches the source map of the most recent upload **for that robot**, which is what makes
a production stack trace readable. Archive it with the build; it cannot be regenerated
later.

## Unit testing with miniprogram-simulate

```bash
npm i -D miniprogram-simulate jest
```

```javascript
const simulate = require('miniprogram-simulate')

test('components/index', () => {
  const id = simulate.load('/components/index')   // absolute path within the project
  const comp = simulate.render(id)
  comp.attach(document.createElement('parent-wrapper'))  // triggers attached

  expect(comp.querySelector('.index').dom.innerHTML).toBe('index.properties')
})
```

It runs components in a single Node thread over a jsdom tree, so it tests component
logic and rendered output. It does not emulate: the two-thread scheduler, real `wx.*`
behaviour (the APIs are stubs you can override), native components, or some framework
features such as abstract nodes. A passing suite is evidence about your component, never
about runtime behaviour on a device.

It also exposes helpers for triggering touch and custom events, selecting child nodes,
setting component data and driving lifecycles.

## Version flow and release

| Version | Rules |
|---|---|
| Development | One per developer, the latest upload; deleting it affects nothing else |
| Experience | One development version promoted; visible to experience members |
| In review | **Exactly one** at a time; resubmitting replaces it |
| Live | Overwritten when a reviewed version is released |

Submit for review from the platform. Release either in full or in stages (the staged
form is the platform's grey release), and prefer staged for anything with meaningful
traffic. Test before submitting: repeated rejections slow later reviews.

## Things that get a submission rejected

These are the ones caused by code rather than by content policy, so they are the ones a
review of the repository can catch:

- A privacy interface used without being declared in the privacy guideline — the
  interface is disabled, so the reviewer sees a broken feature.
- Requesting authorization (location, camera, album) with no visible reason, or at
  launch rather than at the point of use.
- A request to a domain that is not in the server allowlist: it works in devtools with
  domain checking off and fails for the reviewer.
- A feature that only works after login, with no way for a reviewer to see it.
- A category mismatch: the mini program does something its declared category does not
  cover.
- Guiding users to external payment, downloads, or off-platform contact.
- A page that cannot be reached from the entry page, or a dead entry in `app.json`.

A pre-submission pass: turn devtools domain checking **on**, install the experience
version on a clean account, walk every entry from the home page, and confirm every
authorization prompt has an on-screen reason.

<!-- sources: miniprogram-ci, wx-official-docs, wx-miniprogram-simulate, cloudbase-ai-toolkit -->
