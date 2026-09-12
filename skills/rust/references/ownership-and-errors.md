# Ownership and error boundaries

Verified against: Rust std 1.98.1; the rules below do not require that MSRV.
[official] std contracts decide language behavior; [community] the interface
review structure adapts github/awesome-copilot without its blanket style rules.

## Choose the owner before the signature

Write a small ledger: value, creator, borrowers, transfer point, destruction
point. For a borrowed output, name the input owner that remains alive. Lifetimes
express a relationship; adding `'a` cannot extend external storage or a temporary.
For work that must outlive the call, move an owned value into the owner. Use shared
ownership only when multiple independent owners really need it.

Use `&str` or `&[T]` for read-only views; taking `String` or `Vec<T>` forces an
ownership decision the callee does not need. Take `T` when retaining, consuming or
transferring it. Do not replace every concrete argument with `impl AsRef<_>`:
flexibility costs inference and documentation, and is useful only at a real seam.

Read `Clone` implementations before claiming their cost. `Arc::clone` shares a
reference-counted allocation; `String::clone` copies owned contents. Neither
justifies a blanket instruction to clone or avoid cloning. A `Copy` implementation
is also a public semantic commitment, not a size-based optimization threshold.

For an immutable inspection followed by mutation, stop the borrow before mutation
by extracting the necessary decision or owned key. Do not clone the entire data
structure to suppress an error when restructuring the access expresses the owner.
For a result that must borrow from a guard, keep the guard in the caller's scope
or expose a scoped operation; do not return a reference after releasing the guard.

## Define recovery, not only an error type

Choose a concrete error type at a library boundary when callers must distinguish
recovery cases. Preserve the underlying cause with `Error::source` where useful.
Use the project's existing context/error library rather than adding another one.
Application boundaries may erase types for reporting when no typed recovery is
needed. Do not make consumers parse `Display` text to recover error identity.

Document these questions for a fallible ownership transfer:

| Question | Contract to state |
|---|---|
| Was input accepted? | The exact point after which ownership does not return |
| What happens on rejection? | Return the original input when retry/recovery needs it |
| Did partial progress occur? | Report or preserve progress; an error is not rollback |
| Can the operation be retried? | Separate retryable failure from unknown outcome |
| Was cancellation observed? | Do not conflate cancellation with channel closure |

For example, an enqueue operation can expose distinct `Cancelled(T)` and
`Closed(T)` errors without requiring `T: Clone`. Once accepted, processing errors
belong to the consumer or acknowledgement protocol, not to the admission result.
If admission succeeds but durability is required, add that acknowledgement only
when the product contract calls for it; memory ownership does not prove durability.

Use `Option` for absence, `Result` for failure and nested forms only when both
states matter. Converting an error to `None` or using `filter_map(Result::ok)` is
valid only if dropping failures is the stated behavior. Propagating `?` must also
preserve necessary operation context and the state of already acquired resources.

## Keep validation on the correct side

Validate untrusted input before entering the domain state that assumes validity.
Private fields and fallible constructors can maintain invariants, but review all
alternate construction paths, including deserialization and conversions.
Use `From` only for infallible conversion; use `TryFrom` for a checked conversion.
Do not implement dereference coercions merely to make a domain wrapper convenient
if that exposes mutation which bypasses its invariants.

Document intentional panic conditions rather than enforcing a universal ban on
`expect`. An internal impossible state and a user-provided path failing to open
are different contracts. A panic is not recoverable error handling, and enabling
`panic=abort` changes process behavior rather than proving the state impossible.

## Finalization is an operation

Keep `Drop` as synchronous fallback cleanup. If flush, commit or close can fail
and the caller needs the error, expose an explicit fallible operation and decide
what remains usable afterward. If shutdown must await work, make that shutdown an
owned async protocol; a destructor cannot simply await it.

Review early returns and panic paths for partially initialized collections and
resources acquired before a later failure. RAII releases Rust-owned resources,
but it does not imply that a remote commit rolled back or a foreign callback
unregistered. Test the actual post-failure state the consumer may observe.

## Consumer-facing checks

Compile a caller using only the public surface, with the same features promised
to downstream users. Exercise error identity and original-input recovery rather
than exact error wording. For borrowed output, ensure the type signature rejects
escape beyond its true owner; successful execution of one example is not a
lifetime proof. When changing public traits or auto traits, check downstream use
that depends on them instead of deriving every common trait speculatively.

<!-- sources: github-rust, rust-result, rust-sync, rust-raw-slice -->
