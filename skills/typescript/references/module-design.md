# Module design

Vocabulary and decision rules for where a TypeScript module's interface goes and how much sits
behind it. Use these words exactly; substituting "component", "service" or "boundary" is how design
discussions stop converging.

## Contents

- [Vocabulary](#vocabulary)
- [Deep and shallow](#deep-and-shallow)
- [The deletion test](#the-deletion-test)
- [Where the seam goes](#where-the-seam-goes)
- [Dependencies decide the seam](#dependencies-decide-the-seam)
- [Interfaces that stay testable](#interfaces-that-stay-testable)
- [File and export layout](#file-and-export-layout)
- [Type-level design of the interface](#type-level-design-of-the-interface)

## Vocabulary

- **Module** — anything with an interface and an implementation. Scale-agnostic on purpose: a
  function, a class, a directory, a package.
- **Interface** — everything a caller must know to use the module correctly. Not only the type
  signature: also invariants, ordering constraints, error modes, required configuration and
  performance characteristics. A module whose types are small but whose docs say "call `init()`
  first" has a larger interface than its signature suggests.
- **Implementation** — what is inside.
- **Depth** — leverage at the interface: how much behaviour a caller can exercise per unit of
  interface they must learn. Deep = a lot of behaviour behind a small interface. Shallow = the
  interface is nearly as complex as the implementation.
- **Seam** — the place where behaviour can be substituted without editing that place. Where the
  seam goes is its own decision, separate from what goes behind it.
- **Adapter** — a concrete thing satisfying an interface at a seam. Names a role, not a size: an
  in-memory fake is a large adapter with a small implementation.
- **Leverage** — what callers get from depth: one implementation pays back across N call sites.
- **Locality** — what maintainers get from depth: change, bugs and verification concentrate in one
  place.

Depth is a property of the interface, not of the implementation. A deep module may be internally
composed of small swappable pieces; they simply are not part of its interface. Measuring depth as
"implementation lines divided by interface lines" rewards padding the implementation — measure it
as leverage instead.

## Deep and shallow

```
deep                              shallow
┌────────────────┐                ┌──────────────────────────────────┐
│ small interface│                │        large interface           │
├────────────────┤                ├──────────────────────────────────┤
│                │                │      thin implementation         │
│  lots of       │                └──────────────────────────────────┘
│  behaviour     │
└────────────────┘
```

When designing an interface, ask: can I remove a method? can I simplify a parameter? can I hide more
of the decision inside?

The TypeScript-specific version of "large interface" is a type surface that leaks the
implementation: exporting the internal state union, the row type from the ORM, or a config object
with twenty optional fields the caller must reason about.

## The deletion test

Imagine deleting the module and inlining it into its callers.

- Complexity **vanishes** → it was a pass-through. Delete it.
- Complexity **reappears in N places** → it was earning its keep.

Run this on every "utils", "helpers" and single-line wrapper before adding to it. In TypeScript the
common pass-through is a function whose body is one expression that the call site could have written
inline with better type flow.

Exceptions worth keeping despite a thin body: a type guard (it preserves narrowing), a stable
exported domain concept, a callback whose identity matters, and a genuine seam.

## Where the seam goes

**One adapter means a hypothetical seam; two means a real one.** Do not introduce a port, an
interface or a dependency-injection parameter until at least two implementations exist — production
plus a test double counts as two, an imagined future one does not.

A module can have **internal seams** used only by its own tests, as well as the **external seam** at
its interface. Do not export an internal seam just because a test reaches for it; that widens the
interface permanently to buy one test.

## Dependencies decide the seam

Classify what the module depends on; the class determines how it is tested.

| Dependency class | Examples | Seam |
|---|---|---|
| In-process | pure computation, in-memory state | None needed. Merge and test through the new interface |
| Local-substitutable | Postgres via PGlite, in-memory filesystem | Internal seam; run the stand-in in the suite. No port at the external interface |
| Remote but owned | your own service over HTTP/gRPC/queue | Define a port at the seam; HTTP adapter in production, in-memory adapter in tests |
| True external | Stripe, Twilio, an LLM provider | Injected port with a mock adapter in tests |

## Interfaces that stay testable

- **Accept dependencies, do not construct them.** A module that calls `new StripeGateway()` inside
  has no seam.
- **Return results rather than mutating arguments.** A function returning `Discount` is testable by
  reading its return value; one that subtracts from `cart.total` is testable only by inspecting
  state afterwards.
- **The interface is the test surface.** If a test has to reach past the interface to observe
  anything, either the interface is the wrong shape or the test is testing the implementation.
- **Replace, do not layer.** When shallow modules are merged into a deep one, the old unit tests on
  the pieces become waste. Delete them and write tests at the new interface, instead of keeping both
  and paying twice.

## File and export layout

- Colocate the module's types, implementation and tests. A `types/` directory far from the code it
  describes guarantees the two drift.
- Export the named things a caller needs and nothing else. `export *` from a barrel file makes every
  consumer's import graph the union of everything, defeats tree-shaking and turns any new export
  into a potential name collision.
- Keep a package's public entry point a deliberate, hand-written list. That list *is* the interface,
  and it is also what `exports` in `package.json` must mirror.
- Types the caller must name in their own code (parameter and return types of exported functions)
  are part of the interface and must be exported too. A function returning an unexported type forces
  callers into `ReturnType<typeof f>`.

## Type-level design of the interface

- **Make the parameter list unmixable.** Two adjacent `string` parameters will be swapped; either
  brand them or take a single options object.
- **An options object with more than a couple of optional fields is a shallow interface in
  disguise.** Every optional field is a state the implementation must handle and the caller must
  understand. Split into two functions or model the options as a union of legal combinations.
- **Do not make the module generic on a type parameter used once.** It adds an interface concept
  and buys no type safety.
- **Export the input and output types by name.** `createOrder(input: CreateOrderInput):
  Promise<Result<Order, CreateOrderError>>` teaches the caller the whole contract from the
  signature; inline anonymous object types force them to read the body.

<!-- sources: mattpocock-codebase-design, ts-handbook -->
