# Testing Svelte and SvelteKit

Verified against: Svelte 5.57, SvelteKit 2.70, `sv` CLI 2026.09.

## Contents

- [The setup the CLI generates](#the-setup-the-cli-generates)
- [Filename is configuration](#filename-is-configuration)
- [Testing runes outside components](#testing-runes-outside-components)
- [Testing effects](#testing-effects)
- [Component tests](#component-tests)
- [Interaction, not smoke](#interaction-not-smoke)
- [Testing `load`, actions and endpoints](#testing-load-actions-and-endpoints)
- [End-to-end with Playwright](#end-to-end-with-playwright)
- [`svelte-check` as the type gate](#svelte-check-as-the-type-gate)

## The setup the CLI generates

`npx sv add vitest` installs and wires the client/server split. Do not
hand-roll it; the split is the part people get wrong.

```js
// vite.config.ts
import { defineConfig } from 'vitest/config';
import { playwright } from '@vitest/browser-playwright';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    expect: { requireAssertions: true },
    projects: [
      {
        extends: './vite.config.ts',
        test: {
          name: 'client',
          browser: {
            enabled: true,
            provider: playwright(),
            instances: [{ browser: 'chromium', headless: true }]
          },
          include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
          exclude: ['src/lib/server/**']
        }
      },
      {
        extends: './vite.config.ts',
        test: {
          name: 'server',
          environment: 'node',
          include: ['src/**/*.{test,spec}.{js,ts}'],
          exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
        }
      }
    ]
  }
});
```

A real browser through Vitest browser mode is the default because jsdom does not
implement layout, focus behaviour, or most of what component tests assert. jsdom
plus `environment: 'jsdom'` remains a working fallback when a browser cannot be
installed in the environment — say so when you fall back to it.

## Filename is configuration

- `*.svelte.test.ts` / `*.svelte.spec.ts` — runs in the browser project **and**
  is compiled with rune support, so the test file itself may declare `$state`.
- `*.test.ts` / `*.spec.ts` — runs in the Node project. No runes, no DOM.
- `*.svelte.ts` / `*.svelte.js` — a non-component module that may use runes.

A component test in a plain `.test.ts` file will fail to compile the runes in
its imports; a server test in a `.svelte.test.ts` file will try to open a
browser to test a database query. Both symptoms look like configuration bugs and
are filename bugs.

## Testing runes outside components

Extract logic into a `.svelte.ts` module and test it directly — this is cheaper
and less brittle than driving it through a component:

```ts
// multiplier.svelte.ts
export function multiplier(getCount: () => number, k: number) {
  return { get value() { return getCount() * k; } };
}
```

```ts
// multiplier.svelte.test.ts
import { expect, test } from 'vitest';
import { multiplier } from './multiplier.svelte';

test('tracks its source', () => {
  let count = $state(0);
  const double = multiplier(() => count, 2);

  expect(double.value).toBe(0);
  count = 5;
  expect(double.value).toBe(10);
});
```

Note the getter: passing `count` directly would pass the number.

## Testing effects

Effects need an owner and a flush. `$effect.root` supplies the owner and returns
a cleanup; `flushSync` from `svelte` runs pending effects synchronously so the
assertion can be plain:

```ts
import { flushSync } from 'svelte';

test('logs each value', () => {
  const cleanup = $effect.root(() => {
    let count = $state(0);
    const log = logger(() => count);

    flushSync();
    expect(log).toEqual([0]);

    count = 1;
    flushSync();
    expect(log).toEqual([0, 1]);
  });

  cleanup();
});
```

Forgetting `cleanup()` leaks the scope into the next test in the file.

## Component tests

`vitest-browser-svelte` renders into the real browser and returns locators:

```ts
// Counter.svelte.test.ts
import { page } from 'vitest/browser';
import { expect, test } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Counter from './Counter.svelte';

test('increments', async () => {
  render(Counter, { start: 0 });

  const button = page.getByRole('button', { name: /increment/i });
  await button.click();

  await expect.element(button).toHaveTextContent('1');
});
```

Rules that keep these tests from rotting:

- Query by role, label or text. A locator is retried automatically;
  `container.querySelector` is not, and it couples the test to markup.
- Locators are strict: two matches is an error. Narrow the query before
  reaching for `.first()`.
- `await expect.element(...)` — the assertion polls. `expect(element)` does not
  and produces flakes.
- Two-way bindings, context and snippet props need a wrapper component written
  for the test; you cannot pass a snippet through `render`'s props object.
- The lower-level `mount` / `unmount` / `flushSync` API from `svelte` works
  without any testing library and is the right tool when asserting on exact
  rendered HTML.

## Interaction, not smoke

A test that only renders proves the component mounts. For anything interactive,
the test must act and then assert the consequence: the value the callback
received, the text that changed, the field that became invalid. Assert
preconditions rather than skipping the interaction when they fail — an
`if (items.length)` guard turns a broken fixture into a green test.

Mock at the boundary that crosses the wire, not inside the component: keep the
real `fetch` and intercept HTTP, or `vi.mock` a module boundary. Mocking the
component's own helpers tests the mock.

## Testing `load`, actions and endpoints

These are plain functions. Call them with the parts of the event they read and
assert on the return value; there is no framework harness to set up.

```ts
// +page.server.test.ts  (Node project)
import { expect, test } from 'vitest';
import { load, actions } from './+page.server';

test('rejects a missing email', async () => {
  const result = await actions.login({
    request: new Request('http://localhost', {
      method: 'POST',
      body: new URLSearchParams({ email: '' })
    }),
    cookies: { set: () => {} }
  } as never);

  expect(result).toMatchObject({ status: 400, data: { missing: true } });
});
```

Build real `Request` and `FormData` objects rather than stubs — they are
available in Node and they catch the encoding mistakes a stub hides. A
`redirect()` throws, so assert with `expect(...).rejects` and check
`isRedirect(error)` from `@sveltejs/kit`.

## End-to-end with Playwright

`npx sv add playwright` adds the config and an `e2e/` directory, with
`webServer` pointing at the production build. Reserve E2E for whole flows —
sign-in, checkout, a form working with JavaScript disabled — and keep component
behaviour in Vitest, where a failure names the component.

Two SvelteKit-specific checks worth an E2E test because nothing else catches
them: a form action still working with JavaScript disabled
(`test.use({ javaScriptEnabled: false })`), and a page rendering correctly on
first paint rather than only after hydration.

## `svelte-check` as the type gate

`npx sv check` (`svelte-check`) type-checks `.svelte` files, which `tsc` cannot
do, and reports unused CSS selectors and accessibility problems. It is the gate
to run before declaring a change done; `--threshold error` in CI keeps warnings
visible without failing the build.

`npx @sveltejs/mcp svelte-autofixer <file-or-code>` is the complementary check:
it runs the Svelte compiler's own diagnostics over a single file and names
legacy syntax, non-reactive updates and misused runes. Use it on every `.svelte`
file you write or edit, before the type gate.

<!-- sources: svelte-core, svelte-evals, sv-cli, fubits1-svelte, svelte-ai-tools, svelte-dev-docs -->
