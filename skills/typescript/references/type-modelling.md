# Type modelling

Making the wrong state fail to compile. Every rule here trades a runtime bug class for a
compile-time one.

## Contents

- [Discriminated unions instead of flag soup](#discriminated-unions-instead-of-flag-soup)
- [Optional fields are a smell of a missing variant](#optional-fields-are-a-smell-of-a-missing-variant)
- [Exhaustiveness with `never`](#exhaustiveness-with-never)
- [Branded types for identifiers and validated values](#branded-types-for-identifiers-and-validated-values)
- [`satisfies` versus annotation versus `as`](#satisfies-versus-annotation-versus-as)
- [Union literals instead of `enum`](#union-literals-instead-of-enum)
- [`readonly` and `as const`](#readonly-and-as-const)
- [Errors as data](#errors-as-data)
- [Shapes that look like modelling but are not](#shapes-that-look-like-modelling-but-are-not)

## Discriminated unions instead of flag soup

`n` independent booleans describe `2^n` states. A domain almost never has `2^n` legal states, so
the rest are bugs waiting for a caller. Replace the flags with one literal discriminant and give
each variant exactly the data that variant owns.

```ts
// Before: 32 representable states, 5 legal ones.
interface Order {
  isDraft: boolean;
  isSubmitted: boolean;
  isPaid: boolean;
  isShipped: boolean;
  isCancelled: boolean;
  paidAt?: Date;
  trackingNumber?: string;
  cancellationReason?: string;
}

// After: 5 representable states, 5 legal ones.
type Order =
  | { status: "draft"; id: OrderId; customerId: CustomerId }
  | { status: "submitted"; id: OrderId; customerId: CustomerId; submittedAt: Date }
  | { status: "paid"; id: OrderId; customerId: CustomerId; paidAt: Date; paymentIntentId: string }
  | { status: "shipped"; id: OrderId; customerId: CustomerId; paidAt: Date; trackingNumber: string }
  | { status: "cancelled"; id: OrderId; customerId: CustomerId; reason: string };
```

The discriminant must be a **literal type on every member** — `string` does not discriminate, and
neither does an optional discriminant. Keep the shared fields repeated or factor them into a base
`interface` the variants extend; extending an interface produces better error messages than
intersecting types, because the checker reports the offending member rather than the whole
intersection.

Transitions become constructors that take the previous variant and return the next one. A function
typed `(order: PaidOrder, tracking: string) => ShippedOrder` cannot be handed a draft.

## Optional fields are a smell of a missing variant

`field?: T` says "sometimes absent" and nothing about *when*. Whenever the answer to "when is it
present?" is another field's value, the two belong in one variant. The tell in existing code is a
non-null assertion on a field right after a flag check: the author knew the correlation and the
type did not.

Genuinely independent optionality — a nickname a user may not have set — stays optional. Use
`exactOptionalPropertyTypes` when the difference between "absent" and "present and `undefined`"
carries meaning, for example when the object is serialised to JSON or spread over a patch.

## Exhaustiveness with `never`

```ts
function describe(order: Order): string {
  switch (order.status) {
    case "draft":     return "Draft";
    case "submitted": return "Awaiting payment";
    case "paid":      return `Paid at ${order.paidAt.toISOString()}`;
    case "shipped":   return `Shipped with ${order.trackingNumber}`;
    case "cancelled": return `Cancelled: ${order.reason}`;
    default: {
      const unhandled: never = order;
      throw new Error(`Unhandled order status: ${JSON.stringify(unhandled)}`);
    }
  }
}
```

The `never` assignment is the point: adding a sixth variant turns every such switch red, which is
how the compiler tells you where the new state matters. A `default: throw` without the `never`
binding compiles forever and finds the gap in production instead.

The same trick guards `if`/`else` chains and object maps: `Record<Order["status"], Handler>` fails
to compile when a key is missing, which is often cleaner than a switch.

## Branded types for identifiers and validated values

TypeScript is structural, so `OrderId = string` and `CustomerId = string` are the same type and
swapping two arguments type-checks. Attach a phantom property to make them distinct:

```ts
declare const brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [brand]: B };

type OrderId = Brand<string, "OrderId">;
type CustomerId = Brand<string, "CustomerId">;
```

Prefer the `unique symbol` key over a plain `__brand` property: a real object can accidentally have
a `__brand` field, and nothing can have that symbol.

A branded type is only worth its weight if there is exactly one way in. Give each brand a parser
that validates and returns the branded value, and let the raw `as` cast live inside that one
function:

```ts
export function orderId(raw: string): OrderId {
  if (!/^ord_[0-9a-z]{16}$/.test(raw)) {
    throw new TypeError(`Not an order id: ${raw}`);
  }
  return raw as OrderId;
}
```

If callers can write `raw as OrderId` anywhere, the brand documents intent but enforces nothing.

Brand the values that get mixed up in real incidents: entity ids of the same primitive type,
validated strings (`Email`, `AbsolutePath`), and units (`Cents`, `Milliseconds`). Branding every
`string` in the codebase costs more in casts than it returns.

## `satisfies` versus annotation versus `as`

Three operators, three different jobs:

| Want | Use | Effect |
|---|---|---|
| Check the literal against a contract, keep the precise inferred type | `satisfies T` | Errors on mismatch and on excess properties; the variable keeps `"GET"`, not `"GET" \| "POST"` |
| Declare the variable's type and widen to it deliberately | `: T` | Members widen to the contract's types; excess properties on a direct literal still error |
| Tell the compiler you know better | `as T` | No check beyond overlap; silently wrong when you are wrong |

```ts
const routes = {
  "/users": { method: "GET", auth: true },
  "/login": { method: "POST", auth: false },
} satisfies Record<string, { method: "GET" | "POST"; auth: boolean }>;

routes["/users"].method; // "GET" — annotation would have given "GET" | "POST"
```

`satisfies` also restores excess-property checking for a value that reaches its consumer through an
intermediate variable. Object literals only get that check when passed directly; assign the literal
to a `const` first and the extra key sails through.

## Union literals instead of `enum`

`enum` emits a runtime object with forward and reverse mappings, so it is not erasable syntax. Under
`erasableSyntaxOnly` — and under Node's own type-stripping — an `enum` declaration is an error.
Default to a union of string literals; when the values must be iterated or reverse-mapped, use a
frozen `as const` object plus a derived union:

```ts
export const ORDER_STATUS = ["draft", "submitted", "paid", "shipped", "cancelled"] as const;
export type OrderStatus = (typeof ORDER_STATUS)[number];
```

`const enum` is worse than `enum`: it inlines across module boundaries, which breaks under
`isolatedModules` and any transpile-per-file bundler.

## `readonly` and `as const`

Default function parameters and returned domain objects to `readonly` — `readonly T[]`,
`Readonly<T>`, `readonly` members. It costs nothing at runtime and turns "this helper mutated my
caller's array" into a compile error. The classic instance is `array.sort()`, which sorts in place;
`toSorted`, `toReversed` and `with` return copies.

`as const` freezes literal inference (`"GET"` stays `"GET"`, arrays become readonly tuples) but does
nothing at runtime. When callers actually mutate, pair it with `Object.freeze`.

`readonly` is shallow and structurally assignable to the mutable form in some positions, so treat it
as intent enforcement rather than a security boundary.

## Errors as data

Two failure classes, two mechanisms:

- **Expected outcomes at a module's interface** — invalid input, not found, conflict, upstream
  rejection — belong in the return type as a discriminated union. The caller cannot forget them
  because the success branch does not type-check until the failure branch is narrowed away.
- **Broken invariants** — a `never` case reached, an unreachable branch, a corrupt internal state —
  keep throwing. They are bugs, and threading them through every signature buys nothing.

```ts
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

type ChargeError =
  | { kind: "card_declined"; declineCode: string }
  | { kind: "insufficient_funds"; shortfallCents: number }
  | { kind: "gateway_unavailable"; retryAfterMs: number };
```

Model the error as its own discriminated union rather than a `string` message: the caller can then
switch on `kind` exhaustively and handle `insufficient_funds` differently from `gateway_unavailable`.

Do not convert an entire codebase to `Result`. A `Result` that is unwrapped and rethrown at every
layer is a more expensive `try`/`catch`. Push the boundary to where a caller genuinely chooses a
different path.

Chain causes with `new Error("...", { cause: err })` rather than string-concatenating the original
message; the cause survives for the logger.

## Shapes that look like modelling but are not

- **`Partial<T>` as a builder.** `Partial<Config>` makes every field optional, so the half-built
  value is assignable to the finished one and nothing checks completeness. Model the build steps as
  distinct types, or validate once at the end into the real type.
- **`{}` as "any object".** `{}` means "anything except `null`/`undefined`" — `42` and `"x"` are
  assignable. Use `object`, `Record<string, unknown>` or the actual shape.
- **`interface` per DTO plus a parallel `type` per domain object with the same fields.** Two names
  for one concept re-introduces the mix-up the types were meant to prevent. One concept, one type.
- **Deeply recursive conditional types over large unions.** They compile slowly and error
  incomprehensibly. If a type needs more than a couple of conditional levels, a plain interface plus
  a runtime check is usually the cheaper design.

<!-- sources: mcollina-ts-magician, shipshitdev-ts-refactor, ts-handbook, ts-release-notes -->
