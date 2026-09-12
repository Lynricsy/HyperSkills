---
name: typescript
description: "Designs TypeScript types, fixes type errors and configures typed package builds."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# typescript

Paths below are relative to this skill's directory.

## Scope

The TypeScript language and its toolchain, independent of any framework: type-level domain
modelling, module and interface design, narrowing and generics, `tsconfig.json`, module resolution,
declaration emit, package publishing, and the TypeScript-specific half of testing.

Not covered — do not answer from this skill:

- React, Next.js, JSX component design, hooks and rendering. Use the `react` skill.
- Visual design, CSS and browser platform work. Use the `frontend-design` skill.
- Test design methodology — what to test, the red/green loop, seams. Use the
  `test-driven-development` skill. This skill covers only how the runner and the compiler see each
  other.
- Server frameworks (Fastify, NestJS, Hono, Express) and their idioms: routing, dependency
  injection containers, request lifecycle. The language-level advice here applies, the framework
  APIs are out of scope.
- Vue, Svelte, Astro and Solid, including their template type-checking.
- Specific libraries — tRPC, Zod, Drizzle, Effect. Their type-level tricks are library
  documentation, not language rules.

## Core rules

Each rule is an invariant: violating it is a bug, a build that breaks for someone else, or a class
of runtime error the compiler could have caught.

1. Read the installed compiler version before advising on configuration:
   `npx tsc --version` and the `typescript` entry in `package.json`. TypeScript 6.0 changed defaults
   and 7.0 turned its deprecations into hard errors, so 5.x-era configuration advice does not
   compile.
2. State every load-bearing compiler option explicitly, even where it matches today's default.
   Defaults moved in 6.0 and will move again; a config that relies on them changes meaning on
   upgrade.
3. Choose `module` / `moduleResolution` from how the output is loaded, never from fashion:
   `nodenext` for a published unbundled package, `bundler` for a bundled app or Bun. `bundler` on a
   package Node loads directly type-checks locally and breaks every consumer.
4. Set `rootDir` and `types` explicitly. `rootDir` is no longer inferred (output silently gains a
   `src/` level) and `types` defaults to `[]` (`process`, `describe` and `Bun` stop resolving).
5. Model state as a discriminated union with a literal discriminant, not as independent booleans.
   `n` booleans describe `2^n` states and a domain has far fewer legal ones; the rest ship as bugs.
6. An optional field whose presence depends on another field is a missing variant. The tell is a
   non-null assertion right after a flag check — the author knew the correlation and the type did
   not.
7. Close every exhaustive branch by assigning the narrowed value to `never`. Without it, adding a
   variant compiles fine and fails in production; with it, the compiler lists every site that needs
   attention.
8. Brand identifiers and validated values that share a primitive type, and give each brand exactly
   one constructor that validates. A brand callers can mint with a bare `as` documents intent and
   enforces nothing.
9. `unknown` at every boundary — `JSON.parse`, `res.json()`, `catch` bindings, `process.env`.
   Narrow or parse before use. A thrown value is not necessarily an `Error`.
10. Never introduce `any`, and never widen a type to make code compile. The alternatives, in order:
    a discriminant check, a `typeof`/`in` guard, a type predicate, an assertion function, a schema
    parse at the edge. If an unchecked cast is genuinely unavoidable, write `as unknown as T`,
    assign it to a named const, and give the reason on the line above.
11. `satisfies` to check a literal while keeping its precise type; an annotation to widen
    deliberately; `as` only for the case in rule 10. Using an annotation where `satisfies` belongs
    loses the literal types the value existed to provide.
12. Prefer union literals to `enum`. `enum` emits a runtime object, so it is not erasable syntax and
    fails under `erasableSyntaxOnly` and Node's type stripping. When values must be iterated, use a
    frozen `as const` array plus `(typeof X)[number]`.
13. Default parameters and returned domain objects to `readonly`, and use `toSorted` / `toReversed`
    / `with` instead of the in-place methods. `array.sort()` rewrites the caller's array.
14. Give exported functions an explicit return type; let module-internal functions infer. The
    exported ones define the declaration output and the incremental build boundary;
    over-annotating internals only fights inference.
15. Constrain a generic to exactly what the body uses. A type parameter that appears in one
    position is `any` wearing a hat, and an over-wide constraint forces callers to build values the
    function never reads.
16. Model expected failures at a module's interface as a discriminated union in the return type,
    and keep throwing for broken invariants. Converting a whole codebase to `Result` produces a
    more expensive `try`/`catch`.
17. Design the interface before the implementation, and keep it small: a module is worth its cost
    when deleting it would scatter complexity across its callers rather than remove it.
18. Do not add a seam — a port, an injected dependency, an interface — until two implementations
    exist. Production plus a test double counts; an imagined future one does not.
19. Suppress with `@ts-expect-error` plus a reason, never `@ts-ignore`. `@ts-expect-error` fails
    once the underlying problem is fixed, so it cannot rot; `@ts-ignore` outlives the bug.
20. Adopt strictness as a ratchet: measure the error surface, enable one flag (or one directory) at
    a time, and gate CI on "no new errors" rather than on a green build.
21. A transpile-only runner does not type-check. Keep `tsc --noEmit` as its own script and its own
    CI step, and make sure `include` actually covers the test files.
22. Before publishing, verify resolution from outside the repo: `npm pack --dry-run`, `publint`, and
    `attw --pack .`. Local tests never resolve through the `exports` map, so they cannot catch a
    broken one.
23. Keep one name per concept across types, files and prose. Two names for one thing re-creates the
    confusion the types were supposed to remove.

## Workflows

**Stack detection (run first, every workflow).** The answers decide which rules apply:

```bash
npx tsc --version                                  # 6.x and 7.x differ in what is even legal
cat tsconfig.json 2>/dev/null                      # explicit options vs inherited defaults
grep -E '"(type|exports|main|module)"' package.json # published package? ESM or CJS?
ls tsconfig*.json */tsconfig.json 2>/dev/null      # project references / monorepo
```

- No `exports` and no `files` → application code; skip the packaging workflow entirely.
- `references` present in any config → build with `tsc -b`, never plain `tsc`.
- TypeScript 6.x → the removals in `references/tsconfig-and-modules.md` are deprecation warnings,
  not errors; say so instead of reporting them as breakage.

### model-a-domain

For new types, or for a refactor where "impossible" states keep reaching production.

- [ ] Name the states the domain actually has, in the domain's own words, before writing any type.
- [ ] Write them as a union with a literal discriminant, and put each field on the one variant that
      owns it (rules 5–6). Shapes and worked examples: `references/type-modelling.md`.
- [ ] Brand the identifiers and validated values that get mixed up, each with one validating
      constructor (rule 8).
- [ ] Turn every state transition into a function from one variant to another, so an illegal
      transition has no signature to call.
- [ ] Decide the failure model: which failures are part of the return type as a discriminated
      union, and which stay exceptions (rule 16).
- [ ] Rewrite the consumers as switches on the discriminant with a `never` guard in the default
      branch (rule 7).
- [ ] **Gate — the escape hatches are gone:** `tsc --noEmit` passes with no `as` cast, no
      non-null assertion and no `any` introduced by the refactor, and adding a throwaway variant to
      the union makes the build fail in every consumer.

### configure-typescript

For a new project, a failing upgrade, or a strictness push.

- [ ] Run stack detection and record the compiler version in the answer — every recommendation
      below is version-gated.
- [ ] Classify the project: published unbundled package, bundled application, or monorepo with
      references. This one answer drives `module`, `moduleResolution` and whether `tsc` emits at
      all (rule 3).
- [ ] Map each error against the removals table in `references/tsconfig-and-modules.md`. `TS5102`,
      `TS5108` and friends name a removed option; the fix is the replacement, never a downgrade
      and never `ignoreDeprecations` on 7.x.
- [ ] Add the explicit `rootDir` and `types` entries, and delete what is now dead: options that
      are defaults or no longer settable (`esModuleInterop`, the `strict` sub-flags,
      `downlevelIteration`), and `dom.iterable` / `dom.asynciterable` in `lib`, which are folded
      into `dom` and now resolve to empty files.
- [ ] Pick the additional strictness flags deliberately, starting with `noUncheckedIndexedAccess`;
      add `isolatedDeclarations` only for a published library.
- [ ] For an existing codebase, measure before enabling:
      `npx tsc --noEmit | cut -d'(' -f1 | sort | uniq -c | sort -rn`, then ratchet (rule 20).
- [ ] **Gate — clean and reproducible:** `tsc --noEmit` (or `tsc -b`) exits 0, every remaining
      option in the file is one this project chose, and no `@ts-ignore` was added to get there.

### harden-existing-code

Reviewing or repairing code whose types have stopped carrying weight.

- [ ] Inventory the unsound points: `grep -rn ': any\|as any\|as unknown as\|@ts-ignore\|!\.' src`
      plus every `catch` binding. Count them before fixing any.
- [ ] Fix by boundary, not by file: every unsound spot traces back to one place where untrusted
      data entered. Parse once there and the casts downstream disappear on their own.
- [ ] Replace each cast with the cheapest sufficient mechanism from the narrowing ladder in
      `references/narrowing-and-generics.md` (rule 10).
- [ ] Check whether the problem is the type rather than the code: repeated casts around the same
      value usually mean the value's type is modelled wrong.
- [ ] Name the compiler flag that would have prevented each class of finding, and say which ones
      the project should turn on.
- [ ] Report findings in the format below; only rewrite the files when asked to fix rather than
      review.
- [ ] **Gate — no new suppressions:** the counts of `any`, `as` and non-null assertions went down,
      `tsc --noEmit` passes, and every remaining cast is `as unknown as T` with a written reason.

### ship-a-package

Publishing or fixing a typed package.

- [ ] Decide format before configuration: ESM only unless a named consumer cannot load it. Dual
      publishing buys a second build and the dual-package hazard.
- [ ] Write the `exports` map with `types` first in every condition object, and list every subpath
      consumers import — details and failure table in `references/packaging-and-build.md`.
- [ ] Emit declarations with `declaration` + `declarationMap`, and export every type that appears
      in an exported signature.
- [ ] Check the tarball matches the map: `npm pack --dry-run` against each `exports` target.
- [ ] Wire the gate into `prepublishOnly` so it cannot be skipped, and check that the test script
      is not standing in for a type-check: a transpile-only runner checks nothing.
- [ ] **Gate — resolves from outside:** `npx publint` and `npx @arethetypeswrong/cli --pack .` both
      pass, and `tsc --noEmit` is green.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Discriminated unions, illegal states, branded types, `satisfies`, `readonly`, enums, errors as data | Designing or refactoring any domain type | `references/type-modelling.md` |
| Narrowing ladder, type predicates, assertion functions, `unknown` boundaries, generic constraints, `NoInfer`, distributive conditionals, reading a type error | Removing an `any`/`as`, or a generic infers the wrong thing | `references/narrowing-and-generics.md` |
| Deep vs shallow modules, seams and adapters, the deletion test, export layout, interface shape | Deciding where a module boundary goes or why a helper exists | `references/module-design.md` |
| TS 6/7 defaults and removals, `module`/`moduleResolution`, `verbatimModuleSyntax`, path aliases, strictness flags, project references, parallelism | Any `tsconfig.json` question, or an upgrade that broke the build | `references/tsconfig-and-modules.md` |
| `exports` maps, ESM vs dual, declaration emit, `publint` / `attw`, resolution failure modes | Publishing a package, or a consumer reports broken types | `references/packaging-and-build.md` |
| Type-check gates, `types` entries for test globals, vitest `--typecheck` and `expectTypeOf`, jest transforms, typing mocks | Wiring a runner, or writing a type-level test | `references/testing-types.md` |

## Output format

Use this shape for `harden-existing-code` when asked to review rather than fix. Group by file,
order by how much unsoundness each finding removes, and skip empty sections.

```
## <path>

<path>:<line> - <what is unsound>
  Risk: <the runtime failure this permits, concretely>
  Fix: <the change — one or two lines of code when that is clearer than prose>

## Compiler settings

<flag> - <the findings above it would have prevented>

## Verdict
<counts: any / as / non-null assertions removed>. Fix <the one that unblocks the rest> first.
```

Worked example:

```
## src/config/load-config.ts

src/config/load-config.ts:24 - JSON.parse result typed `any`, then spread over defaults
  Risk: any JSON shape becomes an AppConfig; a string port reaches listen() and the process
  exits at startup.
  Fix: `const raw: unknown = JSON.parse(...)`, then validate into AppConfig with an assertion
  function; the two casts below disappear with it.

src/config/load-config.ts:27 - `catch (err: any)` then `err.code`
  Risk: a thrown string crashes the handler that was meant to handle the failure.
  Fix: leave the binding `unknown` and narrow: `typeof err === "object" && err !== null &&
  "code" in err`.

## Compiler settings

noUncheckedIndexedAccess - would have flagged the featureFlags index read on line 39.

## Verdict
4 `any`, 2 `as`, 1 non-null assertion. Fix the parse boundary on line 24 first — the rest are
downstream of it.
```

## Environment

- Node.js 20+ and the project's own package runner (`npm` / `pnpm` / `bun`) as declared in
  `packageManager`.
- `typescript` comes from the project, never a global install: run it as `npx tsc` so the version
  matches the config being edited.
- Verification commands are the project's own scripts. Read `package.json` rather than assuming
  `npm test`; the type-check script is frequently missing, and adding it is part of the fix.
- `publint` and `@arethetypeswrong/cli` are needed only by `ship-a-package`, and both run via `npx`
  without being added as dependencies.
