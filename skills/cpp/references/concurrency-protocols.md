# Concurrency protocols before memory order

Verified against: C++17 release/acquire semantics and C++20 synchronization
availability; working-draft [atomics.order]. Ordering claims are [official].
Testing and callback recommendations are rewritten [community] guidance.

## Contents

- Write the shared-state ledger
- Identify the publication edge
- Wait on a state transition, not elapsed time
- Callback and shutdown edges

## Write the shared-state ledger

For each location, list writers, readers, lifetime owner, protection, and the
transition that permits the next access. Include destruction as an access boundary.
Choose the existing thread-owner model; for ordinary shared mutable state use a
mutex rather than inventing lock-free reclamation. An atomic pointer protects
pointer access, not the lifetime of the pointed-to object.

Keep these claims separate:

| Claim | Evidence needed |
|---|---|
| No data race | Every conflicting access has atomicity or the required ordering |
| Published data is visible | Actual synchronization chain from data write to read |
| No deadlock | Lock ordering, callback reentrancy and wait dependencies |
| Safe reclamation | No thread or queued operation can still use the object |
| Progress | Blocking/wakeup and scheduler assumptions; atomic does not imply lock-free |

`const` is not synchronization when mutable aliases exist. `volatile` is not a
thread communication primitive. Reference-count control-block safety does not
make a `shared_ptr` pointee thread-safe, nor make unsynchronized modifications of
the same non-atomic `shared_ptr` object safe.

## Identify the publication edge

Use sequential consistency for new simple atomic state unless the established
protocol or measured requirements justify weaker ordering. For an existing
release/acquire publication protocol, name the store that the acquiring load reads.
The core one-shot shape in C++17 is:

```cpp
#include <atomic>

int payload = 0;
std::atomic<bool> ready{false};

void publish() {               // exactly one publisher, called once
    payload = 42;
    ready.store(true, std::memory_order_release);
}
bool try_consume(int& out) {   // no payload access until publication observed
    if (!ready.load(std::memory_order_acquire)) return false;
    out = payload;
    return true;
}
```

This requires the globals to outlive all calls and no later payload writes.
The payload write is sequenced before release; acquire reading that publication
synchronizes with it; the payload read follows acquire. That chain orders the
non-atomic accesses. Making both accesses relaxed removes the publication edge.
If payload were atomic too, relaxed accesses could remove the data race without
establishing the promised relationship between the two variables.

Do not generalize this one-shot flag to reusable mailboxes. Resetting a flag does
not prove the consumer finished reading before a producer overwrites the payload.
Use a mutex-protected queue by default for repeated transfer. If maintaining a
specialized protocol, prove acknowledgement, generations, reuse, and reclamation
with its existing design; do not provide a fresh lock-free algorithm as a patch.

Release/acquire on different objects does not synchronize by spelling alone.
When using release sequences or fences, consult the exact project's standard
edition; do not substitute an architecture-specific observation for the C++ rule.
Even sequential consistency does not fix missing ownership or make a multi-step
read/modify/write operation indivisible.

## Wait on a state transition, not elapsed time

For condition variables, protect the predicate and its updates with the same
mutex used by waiters. Wait in the predicate overload or a loop, because wakeups
can be spurious and notification is not stored state. Include cancellation or
shutdown in that predicate and notify waiters when it changes.

A C++20 `latch` can stage one-shot test arrivals; a condition variable works at a
C++17 floor. Do not upgrade the project only to write a synchronization test.
Use a timeout to bound a broken test, not as the event that makes it pass.
Do not place a test barrier between publication and consumption if that new
synchronization is precisely what the production protocol lacks.

## Callback and shutdown edges

Under the state lock, select recipients and retain a safe dispatch snapshot;
release the lock before invoking unknown code. Decide whether unsubscribe can
race with a dispatch snapshot and whether it guarantees “no future invocation”
or only “not selected for future snapshots.” Implement the actual API contract.
Unlocking avoids a lock reentrancy deadlock but does not by itself make an object
safe if a callback destroys or mutates it while the dispatch loop continues.

Shutdown should stop admission, publish stopping state, wake blocked workers,
join or otherwise await quiescence, then destroy shared state. Check self-join
when a callback initiates shutdown from the worker. C++20 `jthread` requests stop
and joins on destruction, but stop is cooperative and a blocked worker still needs
an appropriate wakeup. A C++17 joinable `thread` needs explicit lifecycle handling;
detaching merely abandons the convenient lifetime boundary.

Run TSan for conflicting accesses in a supported, instrumented build. Retain the
protocol argument for all-atomic defects: a negative report cannot establish the
ordering, progress or reuse contract. Repeated successful x86 runs are not a
substitute for the missing language-level edge.

<!-- sources: margelo-cpp, ecc-cpp-testing, cpp-draft, clang-tsan -->
