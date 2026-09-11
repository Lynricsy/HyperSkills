# tilekit — repository facts

The repository has no README yet. This file is a handover note, not a document
that ships.

```
tilekit/
  .github/
    workflows/
      ci.yml                 (attached)
  assets/
    logo.svg                 512x512, transparent background, 11 KB
    demo.gif                 960x540, 6 s, 2.8 MB, terminal recording of `tilekit pack`
    atlas-light.png          860x420 diagram of the packing result, light background
    atlas-dark.png           860x420, same diagram, dark background
  docs/
    guide.md                 "Packing your first atlas" — step-by-step, already written
    api.md                   full option and error reference — already written
  src/
    index.ts                 (attached)
    cli.ts                   (attached)
  test/
    pack.test.ts
  LICENSE                    Apache License 2.0
  CHANGELOG.md               Keep a Changelog format, current top entry is 0.4.2
  CONTRIBUTING.md
  package.json               (attached)
  tsconfig.build.json
```

Facts someone writing the README will need:

- GitHub repository: `glyphworks/tilekit`. Default branch `main`. The repository
  description field on GitHub currently reads: "Packs sprite folders into a
  texture atlas and emits the frame map".
- Published to npm as `tilekit`. Latest published version is 0.4.2.
- The only CI workflow file is `.github/workflows/ci.yml`; its `name:` is `CI`.
- Coverage is not measured. There is no Codecov or Coveralls account.
- There is no Discord, no Twitter/X account, no sponsors page, no hosted demo.
- There is no banner image. `assets/logo.svg` is the only brand asset.
- `sharp` ships prebuilt binaries for Linux, macOS and Windows on Node 20.11+;
  no native toolchain is needed for a plain `npm install`.
- The package is ESM-only (`"type": "module"`); `require("tilekit")` fails.
- Documentation is read on GitHub and on the npm package page. There is no
  documentation website.
