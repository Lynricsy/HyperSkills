# C# language

Verified against: C# 14 (.NET 10 SDK). C# 15 ships with .NET 11.

## Contents

- [Language version is chosen by the TFM](#language-version-is-chosen-by-the-tfm)
- [Nullable reference types](#nullable-reference-types)
- [Nullability attributes](#nullability-attributes)
- [Types: class, record, struct](#types-class-record-struct)
- [Pattern matching](#pattern-matching)
- [Exceptions](#exceptions)
- [Disposal](#disposal)
- [Span, memory and allocation](#span-memory-and-allocation)
- [Collections and LINQ](#collections-and-linq)
- [Public API surface](#public-api-surface)
- [Old patterns](#old-patterns)

## Language version is chosen by the TFM

The compiler picks the language version from the target framework: `net10.0` → C# 14,
`net11.0` → C# 15. Using a language version newer than the TFM's is unsupported, because a
feature may need runtime or library support the SDK does not carry.

Do not set `<LangVersion>latest</LangVersion>`: it resolves to whatever compiler is installed,
so the build differs between machines. Set an explicit version only when you have a concrete
reason, and set it once in `Directory.Build.props`. `preview` is acceptable in a spike, never
in a shipped project.

To find out what the compiler actually selected, put `#error version` in a file and read the
CS8304 message.

## Nullable reference types

`<Nullable>enable</Nullable>` turns on both annotations and warnings. `string` is then a
promise of non-null; `string?` requires a check before dereference. The compiler tracks
*null state* through control flow, so a check narrows the state for the rest of the block.

The order to reach for, in this order:

1. Narrow with a guard clause or pattern match at the boundary, and keep the remaining code
   non-nullable. `if (order?.Customer is not { } customer) return;` proves `customer` non-null
   for everything after it.
2. Copy a nullable field or property into a local before checking it. A property can return a
   different value on the second read, so the compiler will not carry the narrowing.
3. Express the contract with an attribute (below) when the signature cannot say it.
4. Only then use the null-forgiving operator (written as a trailing exclamation mark, as in
   `_customer = LoadCustomer()!;`), and only for an invariant that genuinely lives outside the
   compiler's view — an ORM materialising a required column, a framework contract.

The null-forgiving operator changes analysis, never runtime behaviour. A codebase full of it
has the warnings silenced and the bugs intact.

`required` members and constructor initialisation remove most CS8618 ("non-nullable field
must contain a non-null value") warnings without any suppression.

## Nullability attributes

From `System.Diagnostics.CodeAnalysis`. Use them when the nullability depends on something the
type system cannot express.

| Attribute | Says |
|---|---|
| `AllowNull` / `DisallowNull` | Input may be null although the type is not, or vice versa (asymmetric properties) |
| `MaybeNull` / `NotNull` | Output nullability differs from the declared type |
| `NotNullWhen(bool)` | `out` parameter is non-null when the method returns that value — the `TryParse` shape |
| `MaybeNullWhen(bool)` | The mirror image |
| `NotNullIfNotNull(nameof(x))` | Result is non-null exactly when that argument was |
| `MemberNotNull` / `MemberNotNullWhen` | This method (an `Initialize`, or a `bool IsLoaded`) guarantees fields are set |
| `DoesNotReturn` / `DoesNotReturnIf` | Throw helpers and assertion helpers, so callers keep their narrowing |

Without `DoesNotReturn` on a throw helper, every call site loses its null-state narrowing and
the warnings reappear one level up.

## Types: class, record, struct

Default to a `sealed class` for behaviour and a `sealed record` for data. Sealing is not
pedantry: it lets the JIT devirtualise calls, and CA1852 flags unsealed internal types.

- `record` gives value equality, `with` expressions and a positional constructor. Use it for
  DTOs, messages, configuration and value objects.
- Do not use `record` for entities with identity semantics, or for anything mutable that gets
  put in a hash set — value equality plus a mutable member is a bug waiting for a rehash.
- `readonly record struct` for small, short-lived values (2–3 fields). A non-readonly struct
  is defensively copied on every member access through a readonly field.
- Prefer a primary constructor (`public sealed class OrderService(IOrderStore store)`) for
  dependency injection. Note that a primary-constructor parameter is captured as a hidden
  field only where it is used, and it is not `readonly`.

## Pattern matching

Switch expressions with type, property, list and relational patterns replace most `if`/`else`
ladders and all visitor scaffolding. Two things worth knowing:

- A `switch` expression over a closed set (an enum, a sealed hierarchy) should have no
  `_ => ...` arm that silently swallows a new case; throw in the default arm so a new member
  fails loudly instead of behaving like the fallback.
- `is not null` and `is null` are the idiomatic null tests. `== null` calls a user-defined
  `operator ==` if one exists, so it can be overridden into something surprising.

## Exceptions

- Throw for a broken contract or an unrecoverable state; return a result for an expected
  outcome. "Not found" on a lookup is a value, not an exception.
- Throw the specific type (`ArgumentNullException`, `ArgumentOutOfRangeException`,
  `InvalidOperationException`) and use the throw helpers:
  `ArgumentNullException.ThrowIfNull(x)`, `ArgumentOutOfRangeException.ThrowIfNegative(n)`.
- Never define an exception type that carries control flow the caller is expected to switch on
  across an async boundary — the stack trace is the only thing that survives well.
- `catch (Exception)` is acceptable only at a boundary that logs and converts (a request
  pipeline, a background loop, a message handler). Everywhere else, catch what you can act on.
- `catch { throw; }` is dead code; `catch (Exception e) { throw e; }` is worse — it resets the
  stack trace. Use a `when` filter to catch conditionally instead of catching and rethrowing.
- Never swallow `OperationCanceledException` as if it were a failure. It is the expected
  outcome of cancellation, and logging it as an error turns every shutdown into a false alarm.

## Disposal

- Implement `IDisposable` only when the type owns an unmanaged resource or another disposable.
  Receiving a disposable through DI does not make you responsible for it.
- Implement `IAsyncDisposable` when cleanup itself is asynchronous (flushing a stream, closing
  a connection). Implementing both is only necessary for a type used from `using` in
  synchronous code paths as well.
- A type with a finalizer needs the full `Dispose(bool)` pattern and `GC.SuppressFinalize`.
  Almost nothing in application code needs a finalizer; `SafeHandle` already has one.
- Services resolved from the DI container are disposed by the container. Transient and scoped
  instances are disposed when their scope ends, singletons at shutdown — so a transient
  `IDisposable` resolved from the root container is never released until the process exits.
  That is the shape of a slow DI memory leak.
- An instance you construct yourself and register with `AddSingleton(new Thing())` is *not*
  disposed by the container.

## Span, memory and allocation

- `Span<T>`/`ReadOnlySpan<T>` are stack-only: they cannot be fields of a class, captured in a
  lambda, or used across an `await`. Use `Memory<T>`/`ReadOnlyMemory<T>` for the async path
  and take `.Span` inside the synchronous section.
- The high-value replacements, in rough order of payoff: `string.Substring` →
  `AsSpan()[a..b]`; `string.Split` in a hot loop → `MemoryExtensions` slicing or
  `Utf8Parser`; repeated concatenation → `StringBuilder` or `string.Create`; `byte[]` scratch
  buffers → `ArrayPool<byte>.Shared` (always return in a `finally`).
- Always pass an explicit `StringComparison`. `string.Equals(a, b)` and `IndexOf(string)`
  default to culture-sensitive comparison, which is both slower and locale-dependent; use
  `StringComparison.Ordinal` unless you are comparing for a human.
- `stackalloc` only for a bounded, small size, and only behind a length check with a heap
  fallback.
- SIMD is a last step, after a measurement says the loop dominates. Prefer
  `System.Numerics.Tensors.TensorPrimitives` for numeric aggregates; drop to
  `Vector128/256/512<T>` with `IsHardwareAccelerated` checks and a scalar fallback for the
  remainder only when the primitives do not cover the operation. Every vectorised path needs a
  test proving it is equivalent to the scalar one, including the tail.

## Collections and LINQ

- LINQ is the default. Rewrite to a loop only where a measurement shows the enumerator and
  closure allocations matter, and say so in a comment.
- Materialise once: an `IEnumerable<T>` that is enumerated twice runs the query twice. Return
  `IReadOnlyList<T>` (or `ImmutableArray<T>`) from anything that will be enumerated more than
  once, so the type states that.
- Size a `List<T>` or `Dictionary<K,V>` with its capacity when the count is known. Growth is
  a reallocate-and-copy per doubling.
- Look up once: `dict.TryGetValue(k, out var v)` rather than `ContainsKey` then indexer.
  `CollectionsMarshal.GetValueRefOrAddDefault` for the read-modify-write case in a hot path.
- Prefer `FrozenDictionary`/`FrozenSet` for a lookup table built once and read forever.
- Use `IAsyncEnumerable<T>` with `await foreach` for streamed results rather than buffering a
  whole result set to return `List<T>`.

## Public API surface

For a library others compile against:

- Nullability annotations are part of the contract; changing `string` to `string?` on a return
  is a source-breaking change for consumers with `TreatWarningsAsErrors`.
- Take the narrowest input type you can use (`IEnumerable<T>` in, `IReadOnlyList<T>` out) and
  never return a mutable collection you also hold.
- Adding a parameter with a default value is binary-breaking even though it compiles; add an
  overload instead.
- Every `async` public method takes a `CancellationToken` (last parameter, defaulted) and ends
  in `Async`.
- Turn on `<GenerateDocumentationFile>true</GenerateDocumentationFile>` and treat CS1591 as a
  real warning on public surface — the XML docs also feed generated OpenAPI descriptions.

## Old patterns

<details><summary>Superseded constructs still common in older code</summary>

- `#region` blocks around members: a class that needs regions to be navigable is too big.
- Manual `INotifyPropertyChanged` boilerplate: use the CommunityToolkit MVVM source generator
  in UI projects.
- `Newtonsoft.Json` for new code: `System.Text.Json` with a source-generated
  `JsonSerializerContext` is faster, trim-safe and AOT-compatible. Keep Newtonsoft where a
  contract depends on its specific behaviour (`JsonConverter` semantics, `dynamic`).
- `Thread`, `ThreadPool.QueueUserWorkItem`, `BackgroundWorker`, `ContinueWith`,
  `TaskCompletionSource` hand-rolled state machines: all superseded by `async`/`await`,
  `Channel<T>` and `BackgroundService`.
- `ArrayList`, `Hashtable`, non-generic `IEnumerable`: only in interop with very old code.
- `DateTime.Now` in domain logic: use `TimeProvider` (injectable, testable) and
  `DateTimeOffset` for anything crossing a boundary.

</details>

<!-- sources: dotnet-official, aaronontheweb, awesome-copilot, dotnet-docs, csharpguidelines -->
