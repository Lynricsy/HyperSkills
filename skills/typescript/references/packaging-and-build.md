# Packaging and build

Verified against: TypeScript 7.0.2, publint 0.3.x, @arethetypeswrong/cli 0.18.x.

Shipping a TypeScript package means shipping two things consumers resolve independently: the
JavaScript and the declarations. Most "works in my repo, broken for consumers" reports are the two
disagreeing.

## Contents

- [Decide the shape before configuring anything](#decide-the-shape-before-configuring-anything)
- [The `exports` map](#the-exports-map)
- [ESM-only, and when dual is worth it](#esm-only-and-when-dual-is-worth-it)
- [Declaration emit](#declaration-emit)
- [`tsc` as the type-checker, a bundler as the emitter](#tsc-as-the-type-checker-a-bundler-as-the-emitter)
- [The verification gate](#the-verification-gate)
- [Failure modes and what they look like](#failure-modes-and-what-they-look-like)

## Decide the shape before configuring anything

Three questions, answered before a single option is written:

1. **Who loads this?** Node directly, a bundler, or both. This picks `module`/`moduleResolution`:
   `nodenext` for a package Node loads unbundled, `bundler` for anything a bundler or Bun resolves.
2. **Is it published?** Published means declarations, an `exports` map and a verification gate.
   Application code needs none of that and should not pay for it.
3. **Which formats?** ESM only unless a named consumer requires CommonJS.

## The `exports` map

`exports` replaces `main`/`module`/`browser` and, unlike them, is an allowlist: anything not listed
is unreachable, which is the point — subpaths you never listed cannot become part of your API by
accident.

```jsonc
{
  "name": "@acme/reporting",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "default": "./dist/index.js"
    },
    "./formatters": {
      "types": "./dist/formatters/index.d.ts",
      "default": "./dist/formatters/index.js"
    },
    "./package.json": "./package.json"
  },
  "files": ["dist"],
  "sideEffects": false
}
```

Rules that bite when broken:

- **`types` must come first in every condition object.** Conditions are matched in order and the
  first one that resolves wins, so a `types` entry sitting after `import`/`require` only gets used
  when the earlier condition finds no declaration file beside its JavaScript target. Put a
  declaration next to that target and the earlier condition wins silently — which is right when
  both point at the same types and wrong the moment they diverge. [verified] Do not rely on the
  fallback: `publint` reports the ordering as an error, and a `default` condition that resolves
  hides a trailing `types` entry completely.
- **Declare `"type"` explicitly.** Its absence means `commonjs`, so ESM output under `dist/esm/`
  is published as CommonJS files containing `import` statements. Node's syntax detection often
  rescues this at runtime while `attw` reports `UnexpectedModuleSyntax` and older Node throws. If
  a directory holds the other format, drop a two-line `package.json` in it declaring that format.
- **Every subpath a consumer imports must be listed.** Deep imports into `dist/` fail with
  `ERR_PACKAGE_PATH_NOT_EXPORTED` once `exports` exists, even though they worked before.
- **Export `./package.json`.** Tooling reads it, and `exports` blocks it otherwise.
- **Keep `main` and `types` at the top level as a fallback** only if you still support resolvers
  that predate `exports`; otherwise they are noise that can disagree with the map.
- **`sideEffects: false` is a claim about the whole package.** If any module mutates a global,
  registers a polyfill or patches a prototype on import, list those files instead of asserting
  `false`, or bundlers will drop them.
- **The map must match what `files` actually publishes.** `npm pack --dry-run` prints the tarball
  contents; a path in `exports` that is not in the tarball is a `MODULE_NOT_FOUND` for every
  consumer and passes every local test.

## ESM-only, and when dual is worth it

Default to ESM only: `"type": "module"`, one output, one set of declarations. Dual publishing costs
two builds, two declaration sets, and the dual-package hazard — a consumer loading both copies gets
two module instances, so any module-level state (a registry, a cache, an `instanceof` check against
an exported class) silently splits in two.

Publish dual only when a named consumer cannot load ESM. Then:

```jsonc
{
  "exports": {
    ".": {
      "import": { "types": "./dist/esm/index.d.ts", "default": "./dist/esm/index.js" },
      "require": { "types": "./dist/cjs/index.d.cts", "default": "./dist/cjs/index.cjs" }
    }
  }
}
```

Under `moduleResolution: nodenext` the declaration file's own format is decided the same way the
JavaScript's is — by extension and by the nearest `package.json` `type`. A single `index.d.ts`
serving both conditions is the most common broken configuration: the CJS consumer resolves an ESM
declaration file and sees `export default` where `module.exports` is.

Node 22+ can `require()` a synchronous ESM graph, which removes the motivation for dual publishing
in a growing share of cases. Check the actual consumer's Node version before committing to two
builds.

## Declaration emit

- `declaration: true` plus `declarationMap: true`. The map is what makes go-to-definition in a
  consumer's editor land in your source instead of the `.d.ts`.
- Ship the `.d.ts` next to the `.js` it describes, and never hand-write one for code you also
  compile.
- Anything that appears in an exported signature must itself be exported, or the declaration
  references a name the consumer cannot import.
- `isolatedDeclarations: true` requires an explicit type on every exported binding and in exchange
  allows declaration emit to be parallel and tool-agnostic. Errors `TS9013` (return type must be
  inferred from the body) and `TS9009` (accessor needs an annotation) [verified] are it telling you
  the public surface is not written down.
- `skipLibCheck` does not affect what you emit, only whether you check other people's `.d.ts`.

## `tsc` as the type-checker, a bundler as the emitter

For an application, let the bundler emit and give `tsc` `noEmit: true`. Two emitters producing the
same output is a source of drift, and bundlers transpile per file — which is why they cannot handle
`const enum` or anything else `erasableSyntaxOnly` rejects.

For a library, either is defensible: `tsc` alone is fewer moving parts; a bundler plus
`tsc --emitDeclarationOnly` is faster and can produce both formats. What is not defensible is a
bundler emitting JavaScript with no type-check step at all — transpilers strip types without reading
them.

Either way, a type-check gate belongs in `package.json` and in CI:

```jsonc
{ "scripts": { "typecheck": "tsc --noEmit", "build": "tsc -b" } }
```

Use `tsc -b` (`--build`) whenever the repo has project references; plain `tsc` ignores them.

## The verification gate

Local tests prove nothing about resolution, because your own repo never resolves through `exports`.
Run these before publishing:

```bash
npm run typecheck                     # tsc --noEmit, or tsc -b for references
npm pack --dry-run                    # is every exports target actually in the tarball?
npx publint                           # exports map, field ordering, format mismatches
npx @arethetypeswrong/cli --pack .    # what each resolution mode really sees
```

`publint` checks the package's own consistency; `attw` simulates a consumer resolving under
`node10`, `node16` CJS/ESM and `bundler` and reports the combinations that break. They find
different problems — run both. Wire them into a `prepublishOnly` script so a broken map cannot be
published by hand.

## Failure modes and what they look like

| Symptom | Cause |
|---|---|
| Consumer gets `any` for everything (`TS7016`) | No declaration file is reachable at all: `declaration` was off, the emit landed somewhere the map does not point at, or `files` left it out of the tarball. Check the tarball first, not the condition order |
| Consumer gets the *wrong* types | Two condition branches resolve to different declaration files and the first match wins |
| `ERR_MODULE_NOT_FOUND` on a relative import inside the package | ESM output without file extensions; under `nodenext` relative imports need `.js` even in `.ts` source |
| `ERR_PACKAGE_PATH_NOT_EXPORTED` | Consumer deep-imports a path the `exports` map does not list |
| `ERR_REQUIRE_ESM` | Package is ESM-only and the consumer is CommonJS on a Node old enough to refuse |
| `instanceof` fails across the package boundary | Dual-package hazard: two copies loaded |
| Output lands in `dist/src/` | `rootDir` not set; it no longer gets inferred |
| Types are stale after a dependency rebuild | Project references not built with `tsc -b` |
| Works locally, `MODULE_NOT_FOUND` after publish | `files` does not include a path the `exports` map points at |

<!-- sources: paldom-node-ts, ts-release-notes, ts-handbook -->
