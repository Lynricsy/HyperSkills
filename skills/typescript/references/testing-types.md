# Testing TypeScript

Verified against: TypeScript 7.0.2, Vitest 3.x/4.x.

The TypeScript-specific half of testing: making the runner see types, and asserting on types
themselves. Test design — what to test, red/green, seams — is not here.

## Contents

- [Test files and the type-check gate](#test-files-and-the-type-check-gate)
- [Globals need a `types` entry](#globals-need-a-types-entry)
- [Vitest: type-level tests](#vitest-type-level-tests)
- [Jest with TypeScript](#jest-with-typescript)
- [Node's built-in runner](#nodes-built-in-runner)
- [Typing mocks and fixtures without `any`](#typing-mocks-and-fixtures-without-any)
- [Asserting that something does not compile](#asserting-that-something-does-not-compile)

## Test files and the type-check gate

A transpile-only runner — Vitest, `@swc/jest`, `tsx`, `node --experimental-strip-types` — strips
types without checking them. A test file can therefore be nonsense to the type system and still
pass. The type-check gate is a separate step:

```jsonc
{ "scripts": { "typecheck": "tsc --noEmit", "test": "vitest run" } }
```

`include` in `tsconfig.json` must cover the test files, or `tsc --noEmit` silently checks nothing
but `src/`. Either widen `include`, or add a `tsconfig.test.json` that extends the root and includes
both — the second keeps test-only `types` entries out of the build config.

## Globals need a `types` entry

`types` defaults to `[]`, so `describe`, `it` and `expect` are undefined identifiers unless the
runner's types are listed:

```
error TS2591: Cannot find name 'describe'. Do you need to install type definitions for a test
runner? Try `npm i --save-dev @types/jest` … and then add 'jest' to the types field in your tsconfig.
```

- Vitest with `globals: true` → `"types": ["vitest/globals"]`.
- Vitest with explicit imports (`import { describe, it, expect } from "vitest"`) → nothing to add.
  Prefer this: the imports document where the API comes from and the config stays smaller.
- Jest → `"types": ["jest"]`, plus `"node"` if the tests touch `process` or `node:` modules.
- `node:test` → `"types": ["node"]`.

## Vitest: type-level tests

Vitest runs a second, separate collection for type tests. The default patterns are mutually
exclusive: `**/*.{test,spec}.ts` for runtime, `**/*.{test,spec}-d.ts` for types. A `.test-d.ts`
file is *only* collected as a type test.

```ts
// src/order.test-d.ts
import { expectTypeOf, test } from "vitest";
import { describeOrder, type Order } from "./order.js";

test("describeOrder rejects a draft with tracking", () => {
  expectTypeOf(describeOrder).parameter(0).toEqualTypeOf<Order>();
  expectTypeOf<Extract<Order, { status: "draft" }>>().not.toHaveProperty("trackingNumber");
});
```

Enable it with the flag; without it `expectTypeOf` does nothing at all at runtime:

```jsonc
{ "scripts": { "test": "vitest --typecheck" } }
```

Vitest shells out to `tsc --noEmit` (or `vue-tsc`) for this, so `--typecheck` can replace a separate
typecheck script. Relevant `test.typecheck` options: `enabled`, `only`, `checker`, `include`,
`tsconfig`, `ignoreSourceErrors`.

Reserve type tests for API surface a consumer depends on: generic inference, conditional return
types, that an invalid call is rejected. Asserting `expectTypeOf(x).toEqualTypeOf<string>()` on a
plainly annotated value tests the annotation you just wrote.

## Jest with TypeScript

Two transforms, one choice:

- `ts-jest` type-checks as it transforms. Slower, and the errors arrive as test failures. Its
  `isolatedModules` mode drops the checking and the speed difference with it.
- `@swc/jest` or `babel-jest` transpile only — fast, and a separate `tsc --noEmit` gate is then
  mandatory.

Pick transpile-only plus an explicit gate. It keeps one type-checking implementation instead of two
and keeps the feedback loop fast.

ESM under Jest remains awkward: `jest.mock` is hoisted and does not compose with ESM's static
imports, so an ESM TypeScript project usually needs `--experimental-vm-modules` and
`jest.unstable_mockModule`. Vitest handles this natively; on a new project it is the cheaper choice.

## Node's built-in runner

`node --test` with type stripping runs `.ts` files with no build step, but stripping refuses
non-erasable syntax — `enum`, `namespace` with runtime members, parameter properties. Set
`erasableSyntaxOnly: true` so the compiler rejects that syntax at check time rather than the runtime
rejecting it at run time.

## Typing mocks and fixtures without `any`

A mock typed `any` gives up exactly the guarantee the test exists to protect — that the code and its
collaborator agree.

```ts
// The mock stays checked against the real interface.
const gateway = {
  charge: vi.fn<PaymentGateway["charge"]>(),
} satisfies PaymentGateway;
```

For fixtures, prefer a factory returning the real type with overrides:

```ts
function anOrder(overrides: Partial<Order> = {}): Order {
  return { status: "draft", id: orderId("ord_0000000000000001"), ...overrides } as Order;
}
```

That `as Order` is the one cast worth keeping in test code, because `Partial` overrides cannot be
proven to reconstitute a union member — but it lives in one factory rather than in every test. If
the domain is a discriminated union, a factory per variant avoids the cast entirely and is usually
worth writing.

Never widen production types to make a test compile. If the test needs access the interface does not
give it, that is a finding about the interface, not about the test.

## Asserting that something does not compile

`@ts-expect-error` is a compile-time assertion: it fails when the next line has *no* error. That
makes it the right tool for pinning a rejection, and the wrong tool for silencing one you have not
diagnosed.

```ts
// @ts-expect-error trackingNumber only exists on the shipped variant
describeOrder({ status: "draft", id, customerId, trackingNumber: "X" });
```

Under `--typecheck`, Vitest's `expectTypeOf(...).toBeCallableWith(...)` and
`assertType` cover the same ground with a readable failure message.

<!-- sources: vitest-docs, ts-handbook, ts-release-notes -->
