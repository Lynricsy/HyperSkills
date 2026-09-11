# Testing Workers

Verified against: the official documentation for `@cloudflare/vitest-plugin` (v1) and the
integration test harness, re-read 2026-09. The local runtime facts (`.wrangler/state`
persistence, read-after-write local KV) were reproduced on workerd 1.20260910.1.

## Contents

- [Two tools, two jobs](#two-tools-two-jobs)
- [The package rename](#the-package-rename)
- [Setup](#setup)
- [Unit tests against a handler](#unit-tests-against-a-handler)
- [Integration tests inside the runtime](#integration-tests-inside-the-runtime)
- [Testing Durable Objects](#testing-durable-objects)
- [Isolation and concurrency](#isolation-and-concurrency)
- [The nodejs_compat trap](#the-nodejs_compat-trap)
- [Mocking outbound requests](#mocking-outbound-requests)
- [What a test suite here cannot prove](#what-a-test-suite-here-cannot-prove)

## Two tools, two jobs

- **Unit tests** run inside workerd with real bindings via the Workers Vitest integration.
  They can assert directly on what landed in KV, R2, D1 or a Durable Object, and can call
  Durable Object methods directly.
- **Integration tests** exercise production Worker builds across configured HTTP routes, with
  any Node.js test runner, through `createTestHarness()`. This is where Playwright or MSW fit.

Do not reach for a third pattern. `unstable_dev()` is a retired API, and a test that boots
`wrangler dev` and curls it is slower and less isolated than either of the above.

## The package rename

`@cloudflare/vitest-plugin` **replaces** `@cloudflare/vitest-pool-workers`. The package API and
the Vitest configuration are unchanged — only names move:

```diff
- "@cloudflare/vitest-pool-workers": "^0.16.0"
+ "@cloudflare/vitest-plugin": "^1.0.0"
- import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
+ import { cloudflareTest } from "@cloudflare/vitest-plugin";
- "types": ["@cloudflare/vitest-pool-workers/types"]
+ "types": ["@cloudflare/vitest-plugin/types"]
```

There is an official codemod, and it handles subpath imports such as
`@cloudflare/vitest-plugin/config` too:

```sh
npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin --dry-run
```

Every third-party Cloudflare skill and template still says `vitest-pool-workers`. Treat that
as a rename to apply, not a decision to make.

## Setup

Requirements: `compatibility_date` 2022-10-31 or later, an ES-modules Worker, and Vitest 4.1
or later.

```sh
npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin
```

```ts
// vitest.config.ts
import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      // Extra bindings that exist only in tests; takes precedence over the Wrangler config
      miniflare: { kvNamespaces: ["TEST_NAMESPACE"] },
    }),
  ],
});
```

Reusing the project's `wrangler.jsonc` through `wrangler.configPath` is the point: the test
bindings are the real bindings, so a renamed binding breaks the suite instead of production.

For TypeScript, run `wrangler types` first and give the test directory its own tsconfig:

```jsonc
// test/tsconfig.json
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "moduleResolution": "bundler",
    "types": ["@cloudflare/vitest-plugin/types"]
  },
  "include": ["./**/*.ts", "../src/worker-configuration.d.ts"]
}
```

## Unit tests against a handler

```ts
import { env } from "cloudflare:workers";
import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src";

describe("api", () => {
  it("404s on an unknown path", async () => {
    const ctx = createExecutionContext();
    const response = await worker.fetch(new Request("https://example.com/404"), env, ctx);
    await waitOnExecutionContext(ctx);   // let ctx.waitUntil() work settle first
    expect(response.status).toBe(404);
  });
});
```

`waitOnExecutionContext(ctx)` is not optional when the handler uses `ctx.waitUntil()`: without
it the assertions race the background work, which is how a suite becomes intermittently green.

Bindings from `cloudflare:workers`'s `env` are live, so assert on effects rather than on mocks:

```ts
it("caches the rendered page", async () => {
  await exercise();
  expect(await env.CACHE.get("page:/pricing")).not.toBeNull();
});
```

Type `env` once with an ambient module declaration:

```ts
declare module "cloudflare:workers" {
  interface ProvidedEnv extends Env {}
}
```

## Integration tests inside the runtime

`exports` from `cloudflare:workers` reaches the `main` Worker's handlers, and runs in the same
isolate as the tests so global mocks apply to it:

```ts
import { exports } from "cloudflare:workers";

it("serves the index", async () => {
  const response = await exports.default.fetch("https://example.com/");
  expect(response.status).toBe(200);
});
```

`exports` does **not** expose static assets — it replaced the older `SELF` binding and dropped
that. Asset behaviour (`_headers`, `_redirects`, `not_found_handling`, `run_worker_first`) has
to be exercised through a dev worker or against a real deployment; the static-asset routing
acceptance checks in the migration workflow are the practical substitute.

## Testing Durable Objects

Three helpers from `cloudflare:test` cover what a stub alone cannot reach, and all three only
work for classes defined in the `main` Worker:

```ts
import { env } from "cloudflare:workers";
import { runInDurableObject, runDurableObjectAlarm, evictDurableObject } from "cloudflare:test";

it("survives an eviction", async () => {
  const stub = env.ROOM.getByName("room-1");
  await stub.join("alice");

  // Inspect and drive the instance directly
  await runInDurableObject(stub, async (instance: Room, state) => {
    expect(await state.storage.get("players")).toEqual(["alice"]);
  });

  // Tear down in-memory state and prove the object rebuilds from storage
  await evictDurableObject(stub);
  expect(await stub.playerCount()).toBe(1);
});

it("settles on the alarm", async () => {
  const stub = env.ROOM.getByName("room-2");
  await stub.scheduleSettlement();
  expect(await runDurableObjectAlarm(stub)).toBe(true);   // runs it now, returns false if none
});
```

These map onto the three Durable Object bugs worth a permanent test: state that was cached in
memory but never persisted (`evictDurableObject`), an alarm that is not idempotent (call
`runDurableObjectAlarm` twice and assert one effect), and a rebuild path that the constructor
gets wrong after hibernation. Hibernatable WebSockets are hibernated rather than closed by
eviction, so reconnect behaviour is testable too.

## Isolation and concurrency

Storage isolation is **per test file**: each file gets its own storage environment, and writes
in one file are invisible to another. Test files run concurrently by default.

When an integration suite genuinely needs shared state across files, opt out explicitly:

```sh
vitest --max-workers=1 --no-isolate
```

Do not reach for that to fix a flaky test. A test that needs `--no-isolate` to pass is usually
a test that depends on another file's writes, which is the bug.

## The nodejs_compat trap

The plugin **automatically injects** `nodejs_compat` (plus `no_nodejs_compat_v2` and
`export_commonjs_default`) so Vitest itself can run inside workerd. The consequence is real:
Node built-ins and globals are available in tests **whether or not** the Worker's own
configuration enables them.

- Import a `node:*` module without the flag in `wrangler.jsonc`: tests pass, and the **upload**
  fails.
- Use an unsupported Node global: tests pass, upload succeeds, and it breaks in production.

So a green suite is not evidence the Worker is deployable. `wrangler deploy --dry-run` is, and
belongs in the same CI job.

## Mocking outbound requests

Use `@msw/cloudflare` for outbound HTTP and WebSocket mocking. Mock the third parties the
Worker calls; do not mock Cloudflare bindings — the point of running inside workerd is that
the bindings are real, and a mocked KV tests the mock.

## What a test suite here cannot prove

- **Consistency and contention.** Local KV is read-after-write consistent, local D1 and Durable
  Objects are single-process, and nothing propagates globally. An eventual-consistency bug, a
  same-key write-rate 429 and an `overloaded` under load cannot appear. `[verified]`
- **Quotas.** Nothing local enforces the 10 GB per-object ceiling, the daily request cap or the
  per-key write rate.
- **Deployability**, for the `nodejs_compat` reason above.
- **Asset routing**, which `exports` does not cover.

Say which of these a suite does not cover rather than implying the green run settles it. A CI
job that runs `wrangler types`, the typecheck, `vitest run` and
`wrangler deploy --dry-run --outdir=dist` covers everything that can be covered offline.

<!-- sources: cloudflare-docs, cloudflare-skills -->
