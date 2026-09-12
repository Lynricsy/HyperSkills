---
name: rust
description: "Develops Rust code with ownership, lifetimes, async, Cargo and safe FFI."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# Rust

Paths below are relative to this skill's directory.

## Scope

Rust's ownership, concurrency, memory and build contracts at the boundaries
where compiling one configuration does not establish correctness. Cover public
interfaces, failure and cancellation, task shutdown, raw-memory abstractions,
foreign callbacks, dependency features and supported toolchains.

Keep these adjacent jobs separate:

- Tauri windows, capabilities, plugins, IPC and packaging — use `tauri`.
- Smart-contract execution, storage and economic security — use the relevant
  contract tooling; this skill does not audit a chain's semantics.
- A web framework's routing, middleware or extraction API — consult that
  framework; retain this skill only for a concrete Rust ownership/runtime issue.
- General test methodology, incident observability or repository security audits
  — use `test-driven-development`, `observability` or `security-review`.

Do not expand a compiler error into a language tutorial, a crate catalogue,
a workspace rearrangement or an unsolicited runtime migration.

## Core rules

1. Identify the owner, borrower and destruction point before adding `clone`, `Arc` or a lifetime parameter; compiler acceptance must reflect the intended resource lifetime.
2. Accept borrowed views when the callee only observes data; take ownership when retaining or transferring it, so callers do not pay for avoidable allocations.
3. Specify what remains owned and usable on every error; a `Result` that silently consumes retryable work can violate the API even when its error text is good.
4. Separate recoverable errors, documented panics and unsafe preconditions; neither `expect` nor a runtime check turns a caller obligation into an implementation proof.
5. Audit each suspension point for owned state and externally visible progress; a cancellation-safe primitive does not make its surrounding transaction cancellation-safe.
6. Keep a value outside a cancellable capacity wait when cancellation must return it; transfer it only at the chosen acceptance point.
7. Give each spawned task a supervisor, termination path and observed result; dropping a Tokio `JoinHandle` detaches rather than cancels it.
8. Bound work before spawning it; a bounded channel does not bound detached tasks, and started `spawn_blocking` work cannot be aborted.
9. Derive `Send`/`Sync` from their actual bounds and retained state; `Arc` shares ownership, not thread safety for an arbitrary pointee.
10. End short synchronous critical sections before awaiting; use an async mutex only when exclusion must span asynchronous work, then audit cancellation independently.
11. Make every safe wrapper sound for every safe caller; raw-pointer nullness, numeric bounds or a successful test cannot prove allocation, validity, lifetime and aliasing.
12. Tie a returned borrow to a real owner that enforces the foreign lifetime; otherwise return owned data or retain an explicit unsafe caller contract.
13. Validate foreign representations before constructing restricted Rust values; reading an invalid `bool` and checking it afterward is already too late.
14. Pair every foreign allocation, callback registration and ownership transfer with its matching release protocol; Rust `Drop` alone cannot prove foreign callbacks have stopped.
15. Require each crate to request the dependency features it uses; normal-dependency feature unification can hide a missing declaration in a workspace build.
16. Treat edition, compiler MSRV, Cargo syntax, dependency resolution and target support as separate compatibility claims; test the promised toolchain rather than inferring it from an edition.
17. Select verification that can falsify the changed contract; Clippy, Miri, a full-feature build and real foreign integration establish different things.

## Workflows

### Implement or change an interface

- [ ] Read the existing callers, error types and public documentation before
      changing the signature; preserve their actual ownership and recovery needs.
- [ ] Record input ownership, output lifetime, mutation, error recovery, panic
      conditions and any thread-transfer promise.
- [ ] Read `references/ownership-and-errors.md` when a public signature, borrowed
      result, conversion, error type or resource finalization is changing.
- [ ] Model invalid transitions in the existing domain types where that removes
      ambiguity; do not introduce generic traits or builders without a consumer.
- [ ] Trace partial failure through initialized values and acquired resources.
      Decide whether the caller receives the original input, partial progress,
      or a deliberately consumed operation.
- [ ] Exercise the interface from a consumer, not just from private unit tests;
      include the error path whose recovery contract changed.
- [ ] **Gate — consumer contract:** compile the affected caller and run the
      smallest example/test demonstrating both successful use and recovery.
      Report the command, result and any unexercised contract.

### Diagnose async loss, stalls or non-Send futures

- [ ] Read `references/async-and-synchronization.md` before altering a
      `select! { ... }`, timeout, task spawn, shutdown path or lock crossing an await.
- [ ] Map each task to its owner and each await to state retained in its future.
      Identify which future is dropped and which work continues elsewhere.
- [ ] Write the acceptance point and simultaneous-readiness policy before
      changing queue admission. Separate accepted from processed or durable.
- [ ] For a non-Send future, find the particular value retained across await;
      shorten its lifetime or choose an intentional local task, not `unsafe impl`.
- [ ] For a stall, trace lock order, blocking calls, queue capacity and who must
      run to release each resource; changing mutex types alone is not a diagnosis.
- [ ] Drive the disputed state with barriers, channels or explicit polling.
      Avoid sleeps as evidence that a future reached a particular suspension.
- [ ] **Gate — lifecycle:** run the cancellation/closure/success or shutdown
      reproduction and observe original-value ownership and task termination.
      A timeout that merely stops waiting is not successful shutdown.

### Review unsafe or a foreign boundary

- [ ] Read `references/unsafe-and-ffi.md` before approving or editing any
      unsafe wrapper, raw-memory conversion, FFI callback or manual auto trait.
- [ ] Name the safe operation that cannot express the requirement; retain the
      existing audited abstraction unless evidence requires a lower-level one.
- [ ] Write caller obligations separately from checks the implementation can
      actually perform. Identify the external header/version and allocator.
- [ ] Trace construction, use, partial initialization, cancellation, unwind,
      unregister and destruction; inspect safe callers for a counterexample.
- [ ] Keep each unsafe operation inside an explicit block with a local proof,
      and document public unsafe functions with a `# Safety` section.
- [ ] Do not feed invalid pointers to an ordinary test and interpret surviving
      execution as validation. Test legal rejected inputs and audit preconditions.
- [ ] **Gate — proof and boundary:** compile the Rust boundary, run applicable
      Rust-side memory checks, and exercise the real foreign ABI where available.
      List remaining foreign obligations explicitly; do not call a mock an ABI test.

### Repair Cargo features or compatibility

- [ ] Read `references/cargo-and-verification.md` when changing dependency
      edges, workspace inheritance, resolver, edition, MSRV or feature gates.
- [ ] Capture `rustc --version --verbose`, `cargo --version`, the effective
      workspace root, package selection, feature selection and target triple.
- [ ] Inspect the dependency path that activates each required feature; fix
      its declaring consumer rather than enabling unrelated workspace features.
- [ ] Compile the library separately, with resolver-aware dev-feature isolation.
      Use an external consumer for resolver 1 or public packaging checks.
- [ ] Preserve the lockfile policy and existing compatibility promise; do not
      delete the lockfile, upgrade the resolver or raise MSRV to hide a defect.
- [ ] Exercise default and supported minimal feature configurations separately,
      then the supported integration configuration and promised MSRV.
- [ ] **Gate — independent compatibility:** run the isolated consumer check
      and the affected matrix on the declared minimum toolchain. A green
      `--workspace --all-features` command does not pass this gate alone.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Ownership, public types, errors and finalization | A signature, borrow, conversion, error contract or close path changes | `references/ownership-and-errors.md` |
| Cancellation, task supervision, Send/Sync and locks | Work disappears, shutdown stalls, a future is non-Send, or an await retains a guard | `references/async-and-synchronization.md` |
| Unsafe, validity, FFI and callbacks | Raw memory is converted, a safe wrapper is proposed, or a foreign lifetime/thread contract changes | `references/unsafe-and-ffi.md` |
| Features, independent consumers, MSRV and tool limits | A crate only builds in a workspace, Cargo settings change, or a verification matrix is needed | `references/cargo-and-verification.md` |

## Output format

For reviews, use this sensible default and adapt to the requested format:

```text
path:line — severity — violated contract
Trigger: reachable caller/configuration/interleaving that violates it.
Consequence: lost ownership, invalid value, deadlock, detached work or incompatibility.
Repair: smallest producer-side change, with before/after signature or state transition.
Evidence: command and observed result, or the exact documented precondition.
Unverified: foreign/runtime/platform obligations not exercised.
```

Group findings by file. Distinguish proven defects from missing evidence.
For implementation, report changed behavior, consumer compatibility, verification
commands and residual limitations. Do not label passing baseline behavior as a
new capability, or a static safety argument as an executed test.

## Environment

Use the repository's pinned Rust toolchain and runner first. Cargo commands may
fetch dependencies and execute build scripts; respect offline and lockfile policy.
Use `rustup doc --std`, `rustup doc --reference` and `rustup doc --cargo` to inspect
installed-toolchain documentation. For a version-sensitive crate API, resolve the
version in `Cargo.lock` and open its exact-version rustdoc before copying syntax.
Nightly tools are separate opt-in checks, not a reason to change production MSRV.

<!-- sources: full-stack-cargo, full-stack-unsafe, github-rust, tokio-select, tokio-tasks, rust-raw-slice, cargo-features -->
