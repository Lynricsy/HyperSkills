# ArkTS language restrictions

Verified against: OpenHarmony application-dev docs for API 12–26.0.0 (`quick-start/typescript-to-arkts-migration-guide`, `quick-start/arkts-migration-background`).

## Contents

- [The one thing to internalise](#the-one-thing-to-internalise)
- [When the rules are enforced](#when-the-rules-are-enforced)
- [The four pillars](#the-four-pillars)
- [Rule index by category](#rule-index-by-category)
- [Rules that are warnings, not errors](#rules-that-are-warnings-not-errors)
- [Rewrite recipes](#rewrite-recipes)
- [Runtime environment restrictions](#runtime-environment-restrictions)
- [Interop with TS/JS and ESObject](#interop-with-tsjs-and-esobject)
- [Reading a wall of diagnostics](#reading-a-wall-of-diagnostics)

## The one thing to internalise

ArkTS **restricts** TypeScript. The official framing is that it removes the TypeScript
features "that undermine development correctness or increase runtime overhead". Any
TypeScript feature not on the restriction list is supported, so most code reads like
TypeScript — which is exactly why the removals surprise people.

Two consequences worth stating out loud:

- Code that compiles as TypeScript, passes review and ships on web can still fail to build
  as ArkTS. "It's valid TypeScript" is not an argument.
- There is no escape hatch. Strict type checking is not configurable, and `any`,
  `unknown` and `@ts-ignore` are all rejected. In TypeScript you can lie to the compiler;
  in ArkTS you cannot, so a design that depended on lying has to change.

After refactoring against these rules the code is still valid TypeScript — the restriction
set is a subset, so migration is one-directional and safe.

## When the rules are enforced

`.ets` files followed plain TypeScript syntax before API version 10. From API version 10
Release the ArkTS rules are defined and checked during compilation, and which mode applies
is decided by the project's `compatibleSdkVersion`:

| `compatibleSdkVersion` | Mode | Behaviour |
|---|---|---|
| `>= 10` | standard | Any violation fails the build |
| `< 10` | compatibility | Violations are reported as warnings only |

So read `build-profile.json5` before you decide whether a diagnostic is blocking. A project
still in compatibility mode has a backlog, not a broken build — and it cannot move to
standard mode until the backlog is cleared.

Severity in the rule list itself has the same two levels: `error` fails compilation,
`warning` is "will fail in a future version". Treat warnings as scheduled errors.

## The four pillars

Every individual rule descends from one of four decisions.

**1. Static typing is enforced.** `any` and `unknown` are prohibited outright
(`arkts-no-any-unknown`). The replacement is always a declared class or interface, even
for an API response you would normally type as `any` and narrow later.

**2. Changing object layout at runtime is prohibited.** You may not add properties, delete
properties, or assign a value of another type to a property. TypeScript blocks most of this
too, but can be tricked with `as any`, a loosened tsconfig or `@ts-ignore`. ArkTS closes
all three doors, so `(obj as any).newField = x` and `delete (obj as any).f` are compile
errors rather than working code.

**3. Operator semantics are restricted.** Unary `+`, `-` and `~` apply to numbers only:
`+42` is fine, `+'42'` is a compile error. `in`, `delete`, `with`, the comma operator
outside `for`, and `typeof` outside expression position are all removed.

**4. Structural typing is not supported.** Two unrelated classes with the same public API
are different types, full stop. You cannot assign one to the other and you cannot pass one
where the other is expected. Shared behaviour must be expressed with an `interface` and an
explicit `implements`, or with inheritance.

## Rule index by category

Rule ids are the identifiers the compiler and `codelinter` report, so grouping your
diagnostics by id is the fastest route through a large failure. Each rule also carries a
numeric error code, which is what appears in raw build output. The ones you will meet
most often:

| Rule | Code | Rule | Code |
|---|---|---|---|
| `arkts-no-var` | 10605005 | `arkts-no-any-unknown` | 10605008 |
| `arkts-no-props-by-index` | 10605029 | `arkts-no-structural-typing` | 10605030 |
| `arkts-no-untyped-obj-literals` | 10605038 | `arkts-no-obj-literals-as-types` | 10605040 |
| `arkts-no-func-expressions` | 10605046 | `arkts-as-casts` | 10605053 |
| `arkts-no-delete` | 10605059 | `arkts-no-in` | 10605066 |
| `arkts-no-destruct-decls` | 10605074 | `arkts-no-for-in` | 10605080 |
| `arkts-limited-throw` | 10605087 | `arkts-no-implicit-return-types` | 10605090 |
| `arkts-no-nested-funcs` | 10605092 | `arkts-no-spread` | 10605099 |
| `arkts-no-globalthis` | 10605137 | `arkts-no-func-bind` | 10605140 |
| `arkts-no-as-const` | 10605142 | `arkts-limited-stdlib` | 10605144 |
| `arkts-strict-typing-required` | 10605146 | | |

**Typing**

`arkts-no-any-unknown` · `arkts-no-utility-types` · `arkts-no-conditional-types` ·
`arkts-no-intersection-types` · `arkts-no-mapped-types` · `arkts-no-indexed-signatures` ·
`arkts-no-aliases-by-index` · `arkts-no-props-by-index` · `arkts-no-typing-with-this` ·
`arkts-no-implicit-return-types` · `arkts-no-definite-assignment` · `arkts-as-casts` ·
`arkts-no-as-const` · `arkts-no-is` · `arkts-instanceof-ref-types` ·
`arkts-strict-typing-required` · `arkts-limited-esobj`

**Object shape and literals**

`arkts-no-structural-typing` · `arkts-no-untyped-obj-literals` ·
`arkts-no-obj-literals-as-types` · `arkts-no-noninferrable-arr-literals` ·
`arkts-no-class-literals` · `arkts-implements-only-iface` · `arkts-extends-only-class` ·
`arkts-no-extend-same-prop` · `arkts-no-decl-merging` · `arkts-no-classes-as-obj` ·
`arkts-identifiers-as-prop-names` · `arkts-no-symbol` · `arkts-no-private-identifiers`

**Classes and functions**

`arkts-no-ctor-prop-decls` · `arkts-no-ctor-signatures-type` ·
`arkts-no-ctor-signatures-iface` · `arkts-no-ctor-signatures-funcs` ·
`arkts-no-call-signatures` · `arkts-no-multiple-static-blocks` ·
`arkts-no-method-reassignment` · `arkts-no-prototype-assignment` ·
`arkts-no-func-expressions` · `arkts-no-nested-funcs` · `arkts-no-standalone-this` ·
`arkts-no-generators` · `arkts-no-func-props` · `arkts-no-func-apply-call` ·
`arkts-no-func-bind` · `arkts-no-new-target`

**Statements and operators**

`arkts-no-var` · `arkts-no-for-in` · `arkts-no-with` · `arkts-no-delete` ·
`arkts-no-in` · `arkts-no-polymorphic-unops` · `arkts-no-type-query` ·
`arkts-no-comma-outside-loops` · `arkts-no-destruct-assignment` ·
`arkts-no-destruct-decls` · `arkts-no-destruct-params` · `arkts-no-spread` ·
`arkts-no-types-in-catch` · `arkts-limited-throw` · `arkts-no-globalthis`

**Modules, enums, namespaces**

`arkts-no-require` · `arkts-no-export-assignment` · `arkts-no-ambient-decls` ·
`arkts-no-module-wildcards` · `arkts-no-umd` · `arkts-no-import-assertions` ·
`arkts-no-misplaced-imports` · `arkts-no-ts-deps` · `arkts-no-enum-mixed-types` ·
`arkts-no-enum-merging` · `arkts-no-ns-as-obj` · `arkts-no-ns-statements` ·
`arkts-unique-names` · `arkts-limited-stdlib` · `arkts-no-jsx`

## Rules that are warnings, not errors

Five rules are `warning` severity: `arkts-no-definite-assignment` (`x!: T`),
`arkts-no-globalthis`, `arkts-no-func-bind`, `arkts-no-classes-as-obj` (using a class
itself as a value) and `arkts-limited-esobj`. They compile today and are documented as
future errors. Fix them when you touch the file; do not treat them as permanent
allowances.

## Rewrite recipes

| Instead of | Write |
|---|---|
| `let x: any = api()` | Declare a class/interface for the payload and type `x` with it |
| `type Item = { id: number }` + `{ id: 1 }` | `interface Item { id: number }` or `class Item`, then `new Item()` / a literal matching the declared type |
| `(obj as any).extra = v` | Declare `extra` on the class up front, or use a wrapper class holding both |
| `delete obj.field` | Make the field optional (`field?: T`) and set it to `undefined` |
| `const { a, b } = obj` | `const a = obj.a; const b = obj.b;` |
| `f(...args)` | Pass an array parameter, or list the arguments. Spread works only in two places: into a rest parameter, and copying an array (or array subclass / typed array) into an array literal |
| `for (const k in obj)` | `for (const k of Object.keys(obj))`, or iterate a `Map` |
| `'k' in obj` | An explicit optional field plus `obj.k !== undefined`, or `instanceof` |
| `setTimeout(function () { … })` | `setTimeout(() => { … })` |
| a nested `function` | A top-level function, a class method, or an arrow function held in a `const` |
| `throw 'boom'` | `throw new Error('boom')` |
| `const S = ['a','b'] as const` | `enum S { A = 'a', B = 'b' }` |
| `fn.call(ctx, x)` / `fn.apply` | Pass the receiver explicitly as a parameter, or use a bound arrow |
| `obj.method = other` | Subclass and override, or hold a function-typed field |
| `globalThis.cache` | A module-level `const` in a shared module, or `AppStorage`/`PersistenceV2` |
| `class A implements B` where `B` is a class | Extract an `interface` and implement that |
| `T \| U` intersection | A class that extends/implements both sides |

Casting uses `as T` only; angle-bracket casts are rejected (`arkts-as-casts`). Type
guarding works with `instanceof` and `as`; user-defined `x is T` predicates are not
supported (`arkts-no-is`).

## Runtime environment restrictions

Independent of syntax, the application runtime imposes:

- Strict mode is always on.
- `eval()` is forbidden.
- `with () {}` is forbidden.
- Building a function from a string is forbidden.
- **Circular imports fail application loading.** Two `.ets` modules importing each other
  does not produce a warning — the app fails to load. This is the most damaging item on
  the list because a refactor can introduce it accidentally.

One documented divergence from standard JS: the Ark runtime accepts JSON numbers in the
`2.e3` form that standard parsers reject as a `SyntaxError`. Do not rely on it; a payload
that only parses on device will fail in any other tool in your pipeline.

## Interop with TS/JS and ESObject

ArkTS can call TypeScript and JavaScript, and the runtime still understands dynamic object
semantics. That is a migration affordance, not a design target: reusing a TS/JS object
directly as an ArkTS entity bypasses static checking and reintroduces both runtime
exceptions and the dynamic-dispatch overhead the restrictions exist to remove. The
documented example is a TS class whose field has no initializer being consumed from
`.ets` and dereferenced — no ArkTS diagnostic, a runtime failure.

`ESObject` is the typed hole for values coming from that boundary, and its use is
restricted (`arkts-limited-esobj`, warning). Keep it at the boundary: convert into a
declared ArkTS class as early as possible, and never let an `ESObject` reach a state
variable or a UI binding. Also note `arkts-no-ts-deps`: a `.ts`/`.js` file cannot import
the source of an `.ets` file, so the dependency direction is one-way.

On API version 11 the SDK's TypeScript was 4.9.5 with `target: es2017`, so ECMAScript 2017
and later syntax is available in TS/JS sources. Re-check the bundled version against the
SDK you actually have before relying on newer syntax.

## Reading a wall of diagnostics

1. Group by rule id, not by file. A 200-error build is usually four rules.
2. Confirm standard mode is in force (`compatibleSdkVersion >= 10`) before rewriting.
3. Fix one category at a time — typing, then object shape, then statements, then
   functions — and rebuild between categories. Type fixes remove cascades of downstream
   errors, so fixing statements first wastes work.
4. The two violations with no helpful message are `arkts-no-untyped-obj-literals` and
   `arkts-no-structural-typing`. When a diagnostic points at an assignment that "looks
   fine", assume one of those and check whether the target type is a declared class or
   interface and whether an `implements` clause exists.
5. Nothing may be suppressed. If a change makes a rule stop firing without changing the
   design, re-read the diff — the violation probably moved rather than went away.

<!-- sources: openharmony-docs, corey-harmonyos, earfrog-arkts, yibaiba-ark, kwai-arkts, huawei-docs -->
