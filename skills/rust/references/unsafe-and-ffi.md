# Unsafe and FFI proof obligations

Verified against: Rust std/Reference 1.98.1, Edition 2024 guidance.
[official] The Reference is not an exhaustive formal memory model. Use documented
contracts conservatively rather than treating an unlisted behavior as permitted.
[community] The proof-led workflow adapts full-stack rust-unsafe-ffi.

## Contents

- Separate checks from assumptions
- Foreign representation before domain types
- Borrow scope and callback ownership
- Allocation, initialization and layout
- Threads, pinning and unwind
- Verification limits

## Separate checks from assumptions

A safe wrapper must prevent every safe caller from causing undefined behavior.
If safety depends on caller-supplied memory that the wrapper cannot establish,
keep an unsafe boundary with a precise `# Safety` contract. A private helper does
not repair an unsound public safe entry point that forwards arbitrary pointers.

Before constructing a reference or slice, assign every obligation:

| Obligation | What establishes it |
|---|---|
| Nullness, length arithmetic, address alignment | Checks can reject bad numeric values |
| A live single allocation covering the entire range | Actual owner or foreign allocation contract |
| Initialized, valid values of the pointee type | Initialization protocol and representation conversion |
| No incompatible mutation or competing exclusive borrow | Ownership/aliasing protocol for the full access duration |
| Lifetime and deallocation | Borrow from an enforcing owner, or an explicit unsafe caller obligation |
| Correct ABI and thread/reentrancy behavior | Header, library version and registration contract |

`NonNull::new` establishes only non-nullness, not dereferenceability. Address
contiguity does not show that two allocations are one. A plausible length cap
cannot prove that the pointer has that many bytes. Put the actual argument for
these facts at the unsafe operation, not a comment saying only “checked above.”

## Foreign representation before domain types

Use the C header's integer types and layout. A wire flag defined as a byte is
not a Rust `bool`; represent the raw field as a byte and match 0/1 before creating
a domain boolean. The same principle applies to enum discriminants, `char`,
nonzero integers and references. Producing an invalid typed value is too early,
even if the next statement intends to validate it.

Do not infer that every Rust representation is a portable C representation.
`#[repr(C)]` fixes the documented layout algorithm, not the validity of arbitrary
bytes or foreign allocation ownership. Validate tags and payloads in their raw
form before constructing a Rust enum. Prefer generated bindings when the project
already uses them, but inspect their agreement with the installed header.

Keep UTF-8 validation at the safe string boundary with checked conversion. The
Reference's immediate validity rules for `str` and the UTF-8 invariant expected
by safe string APIs are not identical claims; do not invent an overbroad immediate
UB rule or use that distinction to justify exposing an invalid string safely.

## Borrow scope and callback ownership

A function returning `&'a [T]` from only a raw pointer and length can let the caller
choose an arbitrary `'a`. Do not expose it as safe. Tie the borrow to a real owner
whose methods prevent invalidation for that lifetime. A dummy lifetime parameter,
PhantomData attached after the fact, or a reference to the pointer variable does
not establish a lifetime for its pointee.

For a buffer valid only during a callback, default to copying into owned storage
before returning or queueing work. The copy still requires a valid source while
it executes; copying is not a sanitizer for invalid foreign memory. For measured
zero-copy requirements, use an actual owner/lease protocol, or a scoped callback
whose type prevents the borrow escaping and whose foreign contract keeps it valid.
Do not use transmute to make callback data `'static`.

For an arbitrary-pointer callback callable from Rust, retain an unsafe function
contract or hide it behind a registration layer that enforces valid calls. Review
foreign callers too: unregister must guarantee no future callbacks and wait for
in-flight callbacks before freeing context. Record whether callbacks can be
concurrent or reentrant and whether they may arrive on foreign threads.

## Allocation, initialization and layout

For `slice::from_raw_parts`, prove non-nullness and alignment even for zero length,
one allocation, initialized values, permitted aliasing, and total byte size at
most `isize::MAX` without address wrap. If the foreign API permits `(null, 0)`,
return an empty Rust slice or owned empty collection before raw construction.
Reject null with nonzero length when that is a supported error; rejection of a
null pointer does not validate a non-null pointer.

Keep partially initialized data in `MaybeUninit<T>`. Track exactly which elements
were initialized and which need dropping when a later operation fails. Calling
`assume_init` or `Vec::set_len` requires proof of initialization, not merely enough
capacity or a foreign output count. Validate reported counts against capacity,
and rely on the foreign contract to establish that it actually wrote those bytes.

Use matching allocator domains. `Vec::from_raw_parts` and `Box::from_raw` take on
specific allocation/layout/ownership obligations; they are not generic wrappers
for memory returned by `malloc` or a vendor allocator. Preserve the foreign free
function and ownership transfer rules in the resource owner.

Do not serialize struct memory including padding as initialized bytes. Use
explicit field encoding. For packed fields, avoid creating misaligned references;
use raw-address operations and appropriate unaligned reads only after proving the
range and initialization. Unsafe does not permit races or invalid values.

## Threads, pinning and unwind

Manual `Send`/`Sync` implementations cover every field, alias, destructor and
foreign callback, including thread-affine handles. A mutex does not make a
foreign API callable from another thread if that API forbids it.

Pinning is a contract about moving the pointee, not a lifetime extension or
universal ban on moving the pointer. Audit unsafe projection and destruction
before using it to support self-references; prefer existing safe projection
abstractions. Do not add pinning when an owned index or handle removes the need.

Choose the ABI's unwind policy explicitly. A Rust panic reaching a non-unwind C
boundary safely aborts; a foreign exception entering Rust through a non-unwind
boundary is undefined behavior. `C-unwind` permits unwinding only under its ABI
contract. `catch_unwind` is not a portable catcher for foreign exceptions and
does not catch aborting panics. Catch Rust panics inside a callback when the
specified callback error protocol requires containment; do not silently change
the whole project's panic profile.

Edition 2024 requires unsafe extern blocks and unsafe attribute syntax for
attributes such as `no_mangle`; check the migration guide against the project's
MSRV before changing syntax. `unsafe_op_in_unsafe_fn` is warn-by-default in that
edition, not deny-by-default. An explicit project `deny` policy is separate.

## Verification limits

Compile the wrapper and legal call sites. Use Miri for the Rust-side memory
operations it supports, then real C-side integration for layout, callback
registration, allocator and unwind behavior on supported targets. Miri does not
execute arbitrary foreign code; replacing a foreign call tests the replacement
seam, not that library. Sanitizers and platform tests supplement the argument,
not prove all possible safe callers sound.

Do not run deliberately invalid pointers in ordinary tests and expect a reliable
error. Use valid storage containing rejectable representations, empty allowed
inputs, partial initialization failures and unregister races under a controlled
foreign harness. Record external guarantees that no available tool can establish.

<!-- sources: full-stack-unsafe, rust-ub, rust-raw-slice, rust-sync, rust-ffi-unwind, rust-edition-unsafe -->
