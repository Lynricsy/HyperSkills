# Testing Vue

Verified against: Vitest 5, Vue Test Utils 2.5, Pinia 4

## Contents

- [Which runner, which level](#which-runner-which-level)
- [Test through the public surface](#test-through-the-public-surface)
- [Async: when to await what](#async-when-to-await-what)
- [Testing composables](#testing-composables)
- [Testing Pinia](#testing-pinia)
- [Router in tests](#router-in-tests)
- [Async components, Suspense and Teleport](#async-components-suspense-and-teleport)
- [Nuxt components](#nuxt-components)
- [What not to write](#what-not-to-write)

## Which runner, which level

Vitest with `@vue/test-utils` (or Testing Library for Vue, if the team prefers
its query API) for components and composables; Playwright for end-to-end. Vitest
shares the project's Vite config, so aliases, plugins and SFC compilation work
without a second build pipeline.

Default to the jsdom/happy-dom environment. Switch that suite to Vitest browser
mode when the assertion needs real layout, computed styles, or genuine pointer
and focus behaviour — jsdom reports zero-size boxes and no cascade.

## Test through the public surface

A component's contract is: props in, rendered output and emitted events out,
plus the store and network calls it makes. Drive tests through that surface.

```ts
const wrapper = mount(PriceTag, { props: { cents: 1999 } })
expect(wrapper.text()).toContain('19.99')

await wrapper.find('[data-test="apply"]').trigger('click')
expect(wrapper.emitted('apply')).toEqual([[1999]])
```

`wrapper.vm` reaches into internals; every such assertion pins an
implementation detail and breaks on the next refactor while proving nothing a
user can observe. Treat it as an exception that needs a reason.

`shallow: true` (or `shallowMount`) stubs child components — right when the unit
under test is this component's logic, wrong when the behaviour lives in the
composition. Use `findComponent(Child).vm.$emit('change', v)` to simulate a
child event instead of reaching into the parent.

## Async: when to await what

- `await wrapper.setProps({...})` and `await trigger(...)` flush Vue's render
  queue, so the DOM is current afterwards.
- `await flushPromises()` (from `@vue/test-utils`) drains pending
  microtasks — needed after mocking a fetch that the component awaits.
- `await nextTick()` alone flushes one render tick; it does not resolve
  promises.

An assertion that passes without any await usually means the code path did not
run yet. Do not add `setTimeout` waits; find out what has to be flushed.

## Testing composables

A composable that only reads and writes refs is a plain function call. One that
registers lifecycle hooks or calls `inject()` needs a component instance —
mount a throwaway host:

```ts
function withSetup<T>(composable: () => T) {
  let result!: T
  const app = mount(defineComponent({
    setup() { result = composable(); return () => null },
  }))
  return [result, app] as const
}

const [{ x, y }] = withSetup(() => useMouse())
```

Without the host, `onMounted` never fires and `inject` silently returns the
default, so the test asserts the composable's initial state and nothing else.
Unmount the host when the test needs to prove cleanup happened.

## Testing Pinia

Two setups, chosen by what is under test.

**Component test** — install a testing Pinia as a mount plugin:

```ts
const wrapper = mount(CartSummary, {
  global: {
    plugins: [createTestingPinia({ createSpy: vi.fn })],
  },
})
```

`createTestingPinia` stubs and spies every action by default, so
`expect(store.load).toHaveBeenCalled()` works and no request is made. Seed state
with `initialState: { cart: { lines: [...] } }`. Pass `stubActions: false` only
when the test must exercise an action's real behaviour — not for a
"was it called" assertion. `createSpy: vi.fn` is the default worth standardising
on; without it the generated spies are not Vitest mocks.

**Store test** — no component at all:

```ts
beforeEach(() => setActivePinia(createPinia()))

it('sums the lines', () => {
  const cart = useCartStore()
  cart.add({ sku: 'A-1', qty: 2, unitPrice: 500 })
  expect(cart.subtotal).toBe(1000)
})
```

Use the real `createPinia()` here so actions and getters actually run;
`createTestingPinia` is for when a *dependent* store needs stubbing.

Mounting a component that calls `useStore()` with no Pinia installed throws
`getActivePinia was called with no active Pinia` — that error means the test
setup is missing, not that the store is wrong.

## Router in tests

For a component that only reads `route.params`, stub the composables
(`vi.mock('vue-router', ...)`) or install a memory-history router and push the
route under test before mounting. A real router is the right choice when guards
or navigation are the behaviour; for a component that merely renders a param it
is setup weight with no payoff.

## Async components, Suspense and Teleport

- A component with a top-level `await` in `setup` renders nothing until it
  resolves. Mount it inside a `<Suspense>` host and `await flushPromises()`
  before asserting, or use the framework helper that does it for you.
- `defineAsyncComponent` needs the same treatment plus a flush for the dynamic
  import itself.
- Teleported content is not inside `wrapper.element`. Assert against the
  teleport target (`document.body`), and clean the target between tests or the
  next test finds two dialogs.

## Nuxt components

Anything using Nuxt composables (`useFetch`, `useState`, `useRuntimeConfig`)
needs the Nuxt environment: `@nuxt/test-utils` with `defineVitestConfig`, then
`mountSuspended(Component)` — a `mount` wrapper that provides async setup and
plugin injections. Stub endpoints with `registerEndpoint` rather than mocking
`$fetch` by hand. Plain `mount` on such a component fails with
"Nuxt instance unavailable".

## What not to write

- **Snapshot-only tests.** A snapshot passes for any markup that has not
  changed, including markup that is now broken. Snapshot a specific small
  subtree if at all, and always alongside behavioural assertions.
- **Tests for framework wiring.** That a prop reaches the template, that a
  default applies, that `computed` caches — these test Vue.
- **Parameter tables over the same code path.** Five props with different
  strings is one test, not five.
- **Assertions on internal refs, private store state, or class names** that
  carry no meaning to a user.

<!-- sources: vuejs-ai-skills, awesome-copilot, onmax-nuxt-skills, vue-test-utils-docs, nuxt-docs, pinia-docs -->
