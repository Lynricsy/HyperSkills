# tsconfig and module resolution

Verified against: TypeScript 7.0.2 (`npx tsc --version`). TypeScript 6.0 deprecated a set of
options; TypeScript 7.0 turned every one of them into a hard error. Configuration advice written
for 5.x will not compile.

## Contents

- [What changed, and what it breaks](#what-changed-and-what-it-breaks)
- [Options removed in 7.0](#options-removed-in-70)
- [Write the config explicitly](#write-the-config-explicitly)
- [`module` and `moduleResolution` by consumption model](#module-and-moduleresolution-by-consumption-model)
- [`verbatimModuleSyntax` and the `type` field](#verbatimmodulesyntax-and-the-type-field)
- [Path aliases without `baseUrl`](#path-aliases-without-baseurl)
- [Strictness beyond `strict`](#strictness-beyond-strict)
- [Adopting strictness in an existing codebase](#adopting-strictness-in-an-existing-codebase)
- [Project references and monorepos](#project-references-and-monorepos)
- [Build speed and the 7.0 parallelism flags](#build-speed-and-the-70-parallelism-flags)
- [Running 6.0 and 7.0 side by side](#running-60-and-70-side-by-side)

## What changed, and what it breaks

Four default changes account for nearly every "it worked yesterday" report after an upgrade:

| Option | Default now | Symptom when the project assumed the old default |
|---|---|---|
| `strict` | `true` | A wall of `TS7006` / `TS2322` in a codebase that never opted in |
| `types` | `[]` | `TS2591 Cannot find name 'process' / 'describe' / 'Bun'` — the `@types` packages are no longer auto-loaded |
| `rootDir` | the directory holding `tsconfig.json`, never inferred | Output lands in `dist/src/index.js` instead of `dist/index.js` |
| `module` | `esnext`; `target` floats to the latest stable ES version | CommonJS output silently becomes ESM |

Also changed: `noUncheckedSideEffectImports` defaults to `true`, `libReplacement` to `false`, and
`stableTypeOrdering` is on and cannot be turned off (declaration emit and union display order are
now deterministic, so 6.0 and 7.0 outputs may differ in ordering with no semantic change).

`dom.iterable` and `dom.asynciterable` are folded into `dom`; listing them still parses but they are
empty files.

Fixes for the two surprising ones:

```jsonc
{
  "compilerOptions": {
    "rootDir": "./src",              // otherwise output mirrors the path from the config file
    "types": ["node"]                // plus "vitest"/"jest"/"bun" if the suite relies on globals
  },
  "include": ["src/**/*"]
}
```

`"types": ["*"]` restores the pre-6.0 "load everything in `node_modules/@types`" behaviour. Reach
for it only to unblock a migration; the explicit array is what makes the build fast, and projects
have reported 20–50% type-check time improvements from setting it. [official]

## Options removed in 7.0

Every one of these is an error, not a warning. `"ignoreDeprecations": "6.0"` buys time on 6.0 only —
7.0 ignores it.

| Removed | Replacement |
|---|---|
| `baseUrl` | Fold the prefix into each `paths` entry (below) |
| `moduleResolution: node` / `node10` / `classic` | `nodenext` or `bundler` |
| `module: amd` / `umd` / `systemjs` / `none` | `esnext` or `preserve`, plus a bundler |
| `target: es5` | ES2015 or later; use an external compiler if you truly need ES5 output |
| `downlevelIteration` | Nothing — it only ever affected ES5 emit |
| `esModuleInterop: false`, `allowSyntheticDefaultImports: false` | The safe interop behaviour is always on; delete the settings |
| `alwaysStrict: false` | All code is strict-mode; rename identifiers like `await`, `static`, `private` if they were used as names |
| `outFile` | A bundler |
| `module Foo { }` namespace syntax | `namespace Foo { }` (`declare module "pkg"` is unaffected) |
| `import x from "y" asserts { … }` | `import x from "y" with { … }` |
| `/// <reference no-default-lib="true"/>` | `noLib` or `libReplacement` |
| `tsc file.ts` next to a `tsconfig.json` | `tsc --ignoreConfig file.ts`, or let the config drive it |

Verified error codes: `baseUrl` → `TS5102`, `moduleResolution: node` → `TS5108`. [verified]

Because `esModuleInterop: true` and the `strict` sub-flags (`noImplicitAny`, `strictNullChecks`, …)
are now defaults, leaving them in the file is dead configuration. Delete them so the config shows
only the decisions this project actually made.

## Write the config explicitly

State every load-bearing option even when it matches the current default. Defaults have moved twice
in two majors, and a config that relies on them silently changes meaning on upgrade. The corollary:
do not copy a `tsconfig.json` from a blog post or another project without checking each line against
the TSConfig reference for the installed version.

A published Node library:

```jsonc
{
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "target": "es2023",
    "lib": ["es2023"],
    "types": ["node"],
    "rootDir": "./src",
    "outDir": "./dist",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "verbatimModuleSyntax": true,
    "isolatedDeclarations": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

A bundled application (Vite, esbuild, Next, Bun) — the bundler emits, `tsc` only checks:

```jsonc
{
  "compilerOptions": {
    "module": "preserve",
    "moduleResolution": "bundler",
    "target": "es2023",
    "lib": ["es2023", "dom"],
    "types": ["node", "vitest"],
    "noEmit": true,
    "jsx": "react-jsx",
    "erasableSyntaxOnly": true,
    "noUncheckedIndexedAccess": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

`skipLibCheck: true` in both: checking every `.d.ts` in `node_modules` costs a lot and finds other
people's bugs. Drop it only when debugging a dependency's types.

## `module` and `moduleResolution` by consumption model

The question is not which is modern. It is how the emitted code will be loaded.

- **Published, unbundled, loaded by Node** → `nodenext` for both. It is the only setting that models
  Node's real algorithm: `exports`/`imports` maps, the `.js`/`.mjs`/`.cjs` distinction, and the
  requirement that relative ESM imports carry a file extension.
- **Bundled app, or Bun** → `moduleResolution: bundler` with `module: preserve` (or `esnext`).
  `bundler` allows extensionless imports and ignores the dual-format rules, because the bundler
  resolves them.
- **CommonJS output that still wants modern resolution** → since 6.0, `moduleResolution: bundler`
  may be combined with `module: commonjs`, which is the usual migration step off `node10`.

Choosing `bundler` for a package that Node loads directly is the classic failure: it type-checks
locally and breaks for consumers, because `tsc` accepted imports Node cannot resolve. The
consumption model decides, every time.

Subpath imports may start with a bare `#/` (Node 20+, supported under `nodenext` and `bundler`),
which is the standards-track replacement for a `@/` path alias:

```jsonc
// package.json
{ "imports": { "#/*": "./src/*" } }
```

## `verbatimModuleSyntax` and the `type` field

`verbatimModuleSyntax` emits imports and exports exactly as written, which means a type-only import
must say so:

```ts
import type { Order } from "./order.js";
import { createOrder } from "./order.js";
```

The benefit is that no import is silently elided, so side-effectful modules keep their side effects
and bundlers can tree-shake accurately. Enable it together with the codemod pass that adds
`import type`, not before.

The trap: with `module: nodenext`, a `.ts` file in a package **without** `"type": "module"` is
CommonJS, and `verbatimModuleSyntax` then rejects every top-level `export`:

```
error TS1287: A top-level 'export' modifier cannot be used on value declarations in a CommonJS
module when 'verbatimModuleSyntax' is enabled.
```

[verified] The fix is to add `"type": "module"` to `package.json`, or to rename the file `.mts`, not
to turn the flag off.

## Path aliases without `baseUrl`

```jsonc
// Before (TS 5.x): resolved relative to baseUrl, and baseUrl was also a lookup root
{ "baseUrl": "./src", "paths": { "@app/*": ["app/*"], "@lib/*": ["lib/*"] } }

// After: each entry carries its own prefix, relative to the tsconfig.json directory
{ "paths": { "@app/*": ["./src/app/*"], "@lib/*": ["./src/lib/*"] } }
```

Only if the project genuinely relied on `baseUrl` as a lookup root — bare imports like
`import "someModule.js"` resolving to `src/someModule.js` — add a catch-all `"*": ["./src/*"]`. That
is rare, and it was usually an accident: those imports never worked at runtime.

`paths` is a type-checking-only mapping. Whatever runs the code — the bundler, `tsconfig-paths`,
Node's `imports` field — must be configured to match, or the build passes and the process crashes on
`ERR_MODULE_NOT_FOUND`. Prefer `imports` with `#/` when the runtime is Node.

## Strictness beyond `strict`

`strict` is on by default and covers `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`,
`strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`, `useUnknownInCatchVariables`
and `alwaysStrict`. These are the ones it does **not** turn on, in descending order of bugs caught
per unit of noise:

| Flag | Catches |
|---|---|
| `noUncheckedIndexedAccess` | `arr[i]` and `record[key]` reads that can be `undefined` — the largest source of runtime `TypeError`s that pass a strict build |
| `exactOptionalPropertyTypes` | Writing an explicit `undefined` into an optional field, which JSON round-trips and `in` checks treat differently from absence |
| `noImplicitOverride` | A subclass method that stops overriding anything after the base is renamed |
| `noFallthroughCasesInSwitch` | A missing `break` |
| `noPropertyAccessFromIndexSignature` | `config.someTypo` on an index-signature type, silently `undefined` |
| `noImplicitReturns` | A code path that falls off the end of a function returning a value |
| `erasableSyntaxOnly` | `enum`, `namespace` with runtime members, parameter properties and other syntax that cannot be stripped — required if Node or a transpile-only bundler runs the `.ts` directly |
| `isolatedDeclarations` | Exported API whose type cannot be written into a `.d.ts` without inferring from the body; enables parallel, tool-agnostic declaration emit |

`isolatedDeclarations` is a library flag. It demands an explicit type on every exported binding
(errors `TS9013` on an inferred return, `TS9009` on an untyped accessor) [verified], which is right
for a package's public surface and pure noise inside an application.

`noUnusedLocals` and `noUnusedParameters` belong in the linter, not the compiler: as compiler
options they break the edit-run loop by failing the build on a variable you are about to use.

## Adopting strictness in an existing codebase

A ratchet, not a flip.

1. Measure first: enable the flag, run `tsc --noEmit`, and count errors per file and per rule
   (`npx tsc --noEmit | cut -d'(' -f1 | sort | uniq -c | sort -rn`). The count decides whether this
   is one change or ten.
2. Turn on one flag at a time, or scope one flag to one directory with a nested `tsconfig.json`
   that extends the root and overrides that option.
3. Keep CI green with a no-new-errors rule rather than a green-build rule: record the current count
   and fail when it rises.
4. Never suppress with `any`. `@ts-expect-error` with a reason comment is the correct temporary
   marker, because it *errors when the underlying problem is fixed* and so cannot rot. `@ts-ignore`
   does not, and stays forever.

## Project references and monorepos

Project references give each package its own `tsconfig.json`, a `composite: true` flag, and
declaration output that downstream packages consume instead of re-checking source.

```jsonc
// packages/core/tsconfig.json
{ "compilerOptions": { "composite": true, "rootDir": "./src", "outDir": "./dist", "declaration": true } }

// packages/api/tsconfig.json
{ "references": [{ "path": "../core" }] }
```

Build the graph with `tsc --build` (`-b`), not plain `tsc`; only `--build` understands the
dependency order and the up-to-date checks. `composite` implies `declaration`, so every referenced
project emits `.d.ts` whether or not it is published.

The usual mistake is a root `tsconfig.json` that both lists `references` and has an `include`
covering the same files — the files then get checked twice, once per project, and errors are
reported twice. A solution-style root has `"files": []`.

## Build speed and the 7.0 parallelism flags

TypeScript 7 is a native (Go) compiler and parallelises parsing, checking and emit. Type-checking
runs in four workers by default.

- `--checkers N` sets the number of type-check workers. More is faster and uses more memory; CI
  runners with few cores often want fewer. Pin the same value across environments: in rare
  order-dependent cases a different worker count can surface a different diagnostic.
- `--builders N` sets how many referenced projects build concurrently under `--build`. It multiplies
  with `--checkers`, so `--checkers 4 --builders 4` permits sixteen checkers.
- `--singleThreaded` disables all of it — useful when comparing against 6.0 or when debugging.

Before reaching for flags, the two structural wins are an explicit `types` array and
`skipLibCheck`, both of which cut work rather than spreading it.

## Running 6.0 and 7.0 side by side

TypeScript 7.0 ships no programmatic compiler API. Tools that embed the compiler — `typescript-eslint`,
and the language services behind Vue, Svelte, Astro, MDX and Angular templates — still need 6.0.
Install both via npm aliases:

```jsonc
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

`npx tsc` then runs 7.0 while API consumers resolve 6.0; the compatibility package also exposes a
`tsc6` executable. For those framework projects the practical split is 7.0 for project-wide `tsc` in
CI and 6.0 for the editor.

<!-- sources: paldom-node-ts, ts-release-notes, ts-handbook, shipshitdev-ts-refactor -->
