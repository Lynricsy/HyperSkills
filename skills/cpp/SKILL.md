---
name: cpp
description: "Develops C++ code with CMake, ownership, concurrency and memory safety."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# cpp

Paths below are relative to this skill's directory.

## Scope

General-purpose C++17/20/23 libraries and applications, including the build and
runtime boundaries that can make individually reasonable translation units
incompatible. Preserve the project's language floor and exception policy.

Not covered:

- Unreal reflection, actors, RPC, GAS and gameplay lifetime — use `unreal`.
- Board initialization, interrupt/device protocols, or GPU training kernels.
- The entire C language, syntax lessons, style-guide replacement, or custom
  allocator and lock-free algorithm tutorials.
- General test methodology — use `test-driven-development`; this skill supplies
  C++-specific failure paths and instrumentation limits.

## Core rules

1. Name the owner, each borrow, and its last use; a copied pointer, `string_view`, or `span` does not copy the referent.
2. Distinguish lifetime from snapshot semantics; keeping an object alive does not freeze its bytes or prevent container invalidation.
3. Derive invalidation from the exact operation and container contract; `reserve` is not a universal lifetime repair.
4. Acquire into a completed owner before the next throwing step; an ordinary failed constructor does not run the enclosing destructor.
5. Check the delegating-constructor exception separately; after its target completes, a throwing delegating body does invoke the object destructor.
6. Preserve coupled invariants across moves; memberwise movement of an owner and a count need not leave a usable source.
7. Declare `noexcept` from the actual operations, not a performance wish; an escaping exception terminates rather than enabling rollback.
8. Evaluate moved-from uses by the type contract and operation preconditions; standard-library valid-but-unspecified is not universal use-after-move UB.
9. Give deferred work ownership before returning to its caller; moving a view or capturing `this` does not extend the owner's lifetime.
10. Treat the coroutine frame, closure, referents, and handle owner as separate lifetimes; preserving one does not preserve the others.
11. Assign exactly one frame-destruction responsibility; completion, cancellation before first resume, and executor shutdown must all release it safely.
12. Write the shared-state protocol before weakening memory order; atomic accesses can be race-free while the protocol is wrong.
13. Identify the release operation actually observed by acquire; matching keywords on unrelated atomics do not establish publication.
14. Use the existing ownership/thread model, with a mutex for ordinary shared mutable state; do not introduce lock-free reclamation to avoid a straightforward lock.
15. Call unknown callbacks outside state locks after making a safe dispatch snapshot; reentrancy can deadlock or invalidate the ongoing operation.
16. Make shutdown a protocol that stops admission, wakes waiters, and waits for users before destruction; a stop request alone is not quiescence.
17. Put public-header requirements on the producing target's usage interface; hand-copying flags to today's consumer leaves the next consumer broken.
18. Check compiler, standard library, mode, and ABI separately; a language-standard flag neither supplies missing library features nor reconciles binary layouts.
19. Keep ASan and TSan in separate builds, and instrument the code under investigation as well as its driver; link flags alone do not insert checks.
20. Report only the inputs, schedules, checks, and configurations actually exercised; sanitizer silence and link success are not language-level proofs.

## Workflows

### Implement or change an ownership boundary

- [ ] Read the caller, callee, public declarations, and existing resource wrapper
      before choosing a new ownership type.
- [ ] State whether the consumer needs an immediate borrow, an immutable snapshot,
      or a shared live object. Use the least ownership that fulfills that contract.
- [ ] Make a small lifetime ledger: acquisition, publication, mutation/move,
      cancellation, last use, and destruction. Include borrowed subobjects.
- [ ] Read `references/lifetime-and-exceptions.md` for any view, owner move,
      throwing construction, or container element relocation.
- [ ] Read `references/deferred-work.md` when a callback escapes or execution can
      suspend. Record who owns both the work and the data until cancellation.
- [ ] Fix the producer of a dangling borrow rather than delaying destruction
      globally or forcing previously deferred work to execute immediately.
- [ ] Exercise success and the concrete failure transition: later acquisition
      throws, owner moves, input mutates, or queued work is discarded.
- [ ] **Gate — lifetime closure:** the behavioral reproducer preserves the
      consumer's required values and scheduling, and every acquired resource has
      one release on both completion and the selected failure path.

### Diagnose a race or wrong concurrent result

- [ ] Separate conflicting non-atomic access from a bad ordering protocol,
      deadlock, starvation, and use after shutdown. They need different evidence.
- [ ] Read `references/concurrency-protocols.md`; list every shared location,
      its writers/readers, and the lock or ordering edge governing it.
- [ ] Draw the intended happens-before chain, naming the atomic object and
      value read, or the unlock/lock pair. Mark the first missing edge.
- [ ] Retain the existing concurrency abstraction unless its contract cannot
      satisfy the task. Do not add sleeps, retries, or extra queue hops as sync.
- [ ] Stage important interleavings with a condition variable or the project's
      scheduler controls, without adding an ordering edge that hides the defect.
- [ ] Exercise shutdown and reentrant callbacks as well as the happy path.
- [ ] Run a separate supported TSan configuration for a suspected data race;
      preserve ordinary runs and the protocol argument for all-atomic defects.
- [ ] **Gate — protocol closure:** identify the actual synchronization chain,
      observe the required result, and report untested schedules and diagnostic
      limitations rather than claiming exhaustive concurrency correctness.

### Diagnose cross-target build or ABI failure

- [ ] Read `references/build-and-diagnostics.md` and the affected target's
      transitive dependencies, installed interface, and public headers.
- [ ] Record exact compiler executable/version, standard library, language mode,
      architecture, configuration, toolchain file, and relevant ABI definitions.
- [ ] Compare real compile commands for producer and consumer. Check headers
      after preprocessing where macros select definitions or layouts.
- [ ] Classify each requirement as implementation-only, consumer-only, or both;
      place it on the owner target rather than patching global directory flags.
- [ ] Reconfigure in a separate build directory after a compiler, toolchain,
      library ABI, or sanitizer change; do not trust stale cached objects.
- [ ] Build a consumer that links only the exported target, without manually
      repeating include directories, definitions, or dependency libraries.
- [ ] **Gate — consumer closure:** the clean consumer compiles and exercises the
      public boundary with compatible settings; show the propagated flags and
      behavior, not only successful linking or equal `sizeof` values.

### Adopt a language or library feature

- [ ] Keep the existing minimum mode unless changing it is part of the request.
- [ ] Distinguish the feature's standard edition from implementation support;
      C++20 coroutines do not imply a standard `task` type.
- [ ] Obtain the installed toolchain's documentation for the exact feature.
      Record its feature-test macro and required value where specified.
- [ ] Compile and link a minimal real use with the actual standard library and
      build flags. Header availability alone is insufficient.
- [ ] For a public-header feature, propagate the minimum mode and review ABI
      consequences for consumers built outside the repository.
- [ ] **Gate — feature availability:** the probe and changed target work in each
      supported configuration, or the explicit unsupported configuration is
      rejected without silently changing the project's compatibility promise.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Borrows, invalidation, construction failure, moves, exception guarantees | A view escapes, a container mutates, or an owning type changes | `references/lifetime-and-exceptions.md` |
| Deferred callbacks, closure/frame lifetime, cancellation and frame ownership | A lambda is queued, a coroutine suspends, or shutdown discards work | `references/deferred-work.md` |
| Publication, memory order, condition variables, callback reentrancy, shutdown | Code shares mutable state or produces schedule-dependent results | `references/concurrency-protocols.md` |
| CMake interfaces, ABI/ODR, feature support and diagnostic coverage | A target changes flags, a consumer disagrees, or a sanitizer is proposed | `references/build-and-diagnostics.md` |

## Output format

Use this as a sensible default; adapt to the requested deliverable.

For a review, group findings by file:

```text
path:line — defect and observable consequence
Precondition: the ownership, schedule, or build configuration that exposes it
Before → after: minimal change to the producer or protocol
Evidence: reproduced output or language/build rule; label unexecuted reasoning
```

For an implementation or diagnosis, finish with:

- Contract preserved: ownership/snapshot, scheduling, exception guarantee, or ABI.
- Root cause and changed boundary, naming the caller/consumer affected.
- Verification: exact commands, compiler/library/configuration, and observed
  behavior; distinguish compilation from execution and discovery from test runs.
- Limits: unsupported environment, uninstrumented dependencies, or paths not run.

Do not label a proposed command as a passing run. Do not infer no UB from a
sanitizer-negative execution, or ODR correctness from an executable that links.
