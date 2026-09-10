# Narrowing and generics

How to get from `unknown` to a precise type without `as`, and how to write generics that infer what
callers expect.

## Contents

- [The narrowing ladder](#the-narrowing-ladder)
- [Type predicates](#type-predicates)
- [Assertion functions](#assertion-functions)
- [Where control-flow analysis gives up](#where-control-flow-analysis-gives-up)
- [`unknown` at every boundary](#unknown-at-every-boundary)
- [Index access and `Object.keys`](#index-access-and-objectkeys)
- [Constrain generics minimally](#constrain-generics-minimally)
- [Inference control: `const` type parameters and `NoInfer`](#inference-control-const-type-parameters-and-noinfer)
- [Distributive conditional types](#distributive-conditional-types)
- [Overloads versus a union signature](#overloads-versus-a-union-signature)
- [Reading a type error](#reading-a-type-error)

## The narrowing ladder

Reach for the cheapest mechanism that expresses the check. Each rung is more code than the one
above it, so do not skip upward for its own sake.

1. **Discriminant check** — `if (x.kind === "paid")`. Free, exhaustive, the reason to model unions
   with a discriminant in the first place.
2. **`typeof`** — primitives only. `typeof null === "object"` still, so a `null` check comes first.
3. **`instanceof`** — classes and `Error` subclasses. Fails across realms (worker, vm, iframe) and
   across duplicated copies of a package in `node_modules`; when either is possible, check a
   property instead.
4. **`in`** — distinguishes object shapes without a discriminant: `if ("swim" in animal)`. Since
   TypeScript 4.9 it also narrows `unknown`, so `"id" in value` gives you `value.id: unknown`
   without a cast.
5. **Truthiness** — `if (name)` also excludes `""` and `0`. When the empty string or zero is a legal
   value, compare against `undefined`/`null` explicitly.
6. **Type predicate** — a named check reused in more than one place.
7. **Schema parse** — untrusted external input: HTTP payloads, config files, env vars, persisted
   blobs. Validate once at the edge, then pass the typed value inward.

## Type predicates

```ts
function isFailure(r: Result<unknown, ChargeError>): r is Extract<typeof r, { ok: false }> {
  return !r.ok;
}
```

A predicate is a *promise the compiler cannot check*. Everything after `is` is trusted, so the body
must actually verify what the signature claims — a predicate that checks one of three required
fields is an `as` with extra steps.

Two places where predicates earn their keep:

```ts
// Filtering a union down to one member; without the predicate the result is still the union.
const shipped = orders.filter((o): o is Extract<Order, { status: "shipped" }> => o.status === "shipped");

// Dropping nullish entries; without the predicate the result is (T | null)[].
function isPresent<T>(value: T | null | undefined): value is T {
  return value != null;
}
```

Since TypeScript 5.5 a function whose body is a single boolean return over a parameter often gets an
inferred predicate, so check whether you still need to write one before adding it.

## Assertion functions

```ts
function assertIsAppConfig(value: unknown): asserts value is AppConfig {
  if (typeof value !== "object" || value === null) throw new TypeError("config must be an object");
  // ... check each field ...
}
```

Two constraints that produce confusing errors when broken:

- An assertion function **must be declared with the `function` keyword**. Assign it to a `const`
  arrow and every call site fails with *"Assertions require every name in the call target to be
  declared with an explicit type annotation."*
- It must be reachable as a plain identifier at the call site. `obj.assertThing(x)` does not narrow.

Use an assertion when the failure path is "stop", and a predicate when the caller chooses a
different branch.

## Where control-flow analysis gives up

These are the cases where narrowing silently evaporates and people reach for `as`:

```ts
// 1. Narrowing stored in a variable does not transfer.
const ok = isString(value);
if (ok) {
  value.toUpperCase(); // still string | number
}

// 2. Narrowing does not survive into a deferred callback — the value may have changed by then.
if (name !== null) {
  setTimeout(() => name.toUpperCase(), 0); // string | null again
}

// 3. A function call between the check and the use invalidates narrowing of a mutable binding.
if (this.token !== null) {
  refresh();
  this.token.slice(0, 4); // string | null: refresh() might have cleared it
}

// 4. Independent optional properties do not correlate.
if (value.a || value.b) {
  // neither a nor b is known to be present
}
```

Fixes, in order of preference: inline the check; copy to a `const` local (cases 2 and 3 are exactly
what a `const` snapshot solves); model the correlation as a discriminated union (case 4).

## `unknown` at every boundary

`any` disables checking precisely where the data is least trustworthy. Three boundaries where it
sneaks in:

```ts
const data: unknown = await res.json();      // json() returns any
const parsed: unknown = JSON.parse(raw);     // parse() returns any
try { /* ... */ } catch (err) { /* err is unknown under strict */ }
```

`catch` bindings are `unknown` under `strict` (`useUnknownInCatchVariables`). A thrown value is not
guaranteed to be an `Error` — libraries throw strings, and a rejected promise carries whatever it
was rejected with. Narrow before reading `.message` or `.code`:

```ts
function errorCode(err: unknown): string | undefined {
  return typeof err === "object" && err !== null && "code" in err && typeof err.code === "string"
    ? err.code
    : undefined;
}
```

When an unchecked cast is genuinely unavoidable — a DOM node you own, a library type that is wrong,
two structurally identical types inference will not unify — write `as unknown as T`, assign it to a
named `const`, and put the reason on the line above. A bare `any` leaves no record of the decision.

## Index access and `Object.keys`

`Object.keys(obj)` returns `string[]`, not `(keyof T)[]`, and that is deliberate: the object may have
more properties at runtime than its type admits. Do not cast the result. Use
`Object.entries` when you need both, or iterate a known key tuple:

```ts
for (const [key, value] of Object.entries(flags)) {
  // key: string, value: boolean — no cast, and correct even if flags has extra keys
}
```

`noUncheckedIndexedAccess` adds `| undefined` to every index read on an array or index signature.
It is noisy on first enable and it is the single flag that catches the most real
`Cannot read properties of undefined` crashes. Turn it on in new projects; in existing ones enable
it per directory.

## Constrain generics minimally

Constrain to what the body actually uses. `<T extends object>` when the body only reads
`value.length` is both wrong and unhelpful, and `<T extends SomeBigInterface>` forces callers to
satisfy fields the function never touches.

```ts
// Over-constrained: callers must produce a full Order.
function idOf<T extends Order>(x: T): string;

// Right: exactly the requirement.
function idOf<T extends { id: string }>(x: T): string;
```

A type parameter that appears in exactly one position is not a generic — it is `any` wearing a hat.
`function log<T>(x: T): void` is `function log(x: unknown): void`.

Preserve inference in the return: return `T[K]`, not the widened base type, or callers lose
everything the generic bought them.

## Inference control: `const` type parameters and `NoInfer`

```ts
// Without const: T infers as string[].
declare function pick<const T extends readonly string[]>(options: T): T[number];
pick(["a", "b"]); // "a" | "b"
```

`const` type parameters (TypeScript 5.0+) give `as const` inference at the call site without making
callers write `as const`.

`NoInfer<T>` (5.4+) blocks one position from contributing candidates, which is how you make one
argument drive the inference and another merely be checked against it:

```ts
declare function streetLight<C extends string>(colors: C[], fallback?: NoInfer<C>): void;
streetLight(["red", "yellow", "green"], "blue");
// error TS2345: '"blue"' is not assignable to '"green" | "red" | "yellow" | undefined'
```

## Distributive conditional types

A conditional type whose checked type is a *naked* type parameter distributes over unions:

```ts
type IsArray<T> = T extends unknown[] ? true : false;
type A = IsArray<string | number[]>; // boolean — distributed, probably not what you wanted

type IsArray2<T> = [T] extends [unknown[]] ? true : false;
type B = IsArray2<string | number[]>; // false — checked as a whole
```

Wrapping both sides in a tuple turns distribution off. The same mechanism is why
`Exclude<T, U>` works at all, so decide which behaviour you want rather than discovering it.

## Overloads versus a union signature

Overloads are for signatures where the return type *depends on* the argument types in a way one
signature cannot express. When the parameter simply accepts several types and the return does not
change, a union parameter is clearer and does not lose contextual typing inside callbacks.

Overload pitfalls worth knowing: the implementation signature is not callable from outside, so it
must be a superset of the visible ones; and overload resolution picks the first match, so order from
most specific to least.

## Reading a type error

Long errors are read from the bottom: the last line is the actual mismatch, the lines above it are
the assignability path that led there. Two error families with standard causes:

- **"Type instantiation is excessively deep and possibly infinite."** A recursive conditional or
  mapped type hit the depth limit. Add a depth counter parameter, or replace the type-level
  computation with a plain interface.
- **"Excess property 'x' does not exist in type 'T'."** Only object literals get this check.
  Getting it means you have the literal in the right place; *not* getting it on a variable means the
  check was skipped, which is what `satisfies` restores.

Bisect a confusing error by annotating intermediate values: the first annotation that errors names
the step that inferred something unexpected.

<!-- sources: mcollina-ts-magician, shipshitdev-ts-refactor, ts-handbook -->
