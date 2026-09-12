# Async cancellation and synchronization

Verified against: Tokio 1.53.1 and Rust std 1.98.1.
[official] Tokio contracts below are version-specific; inspect the locked
runtime version before relying on an API absent from the project.

## Contents

- Suspension-state ledger
- Queue admission and value ownership
- Task ownership and shutdown
- Send, Sync and retained state
- Lock lifetime and cancellation
- Decidable lifecycle checks

## Suspension-state ledger

For every await in a cancellable operation, record:

| Await | State owned by its future | External progress | Effect of dropping it |
|---|---|---|---|
| Capacity acquisition | Queue position or permit request | Waiting, not acceptance | Loses queue position |
| Stream operation | Buffer and progress, possibly caller-owned | Bytes may already move | Restart may lose progress |
| Request/response | Request state and reply waiter | Peer may execute request | Reply abandonment is not rollback |
| Task join | Handle to separately running work | Child continues independently | Owned handle drop detaches |

Cancellation safety means that dropping an incomplete future and recreating it
is a no-op for the relevant operation. Distinguish this from memory safety and
from a business policy that deliberately allows abandoned work during shutdown.

Tokio `recv`, `read` and `read_buf` are cancellation-safe primitives. `read_exact`
and `write_all` may have partial progress when dropped. `read_exact` borrows its
caller's buffer; the loss is not an imaginary internally owned payload buffer.
Keep framing/progress outside a repeatedly recreated future, or retain and poll
the same pinned operation when that matches the protocol.

A `select! { ... }` precondition disables polling, not evaluation of the async expression.
Do not put side effects in expression construction and assume an `if` guard
prevents them. On closed streams/channels, terminate or disable that source;
repeatedly polling an immediately ready terminal state can spin.

## Queue admission and value ownership

`Sender::send(value)` owns the value while it waits. If another `select! { ... }` branch
wins, the send future is dropped and the value is lost, even though not sent.
When the contract must return the same non-Clone value on cancellation:

1. Keep the value in the outer operation, outside the cancellable future.
2. Select between cancellation and `Sender::reserve()`.
3. On cancellation or closure, return that original value in the error.
4. On reservation success, perform `permit.send(value)` without another await.
5. Define this synchronous transfer as acceptance; subsequent processing belongs
   to the receiving side or a separate acknowledgement contract.

Reservation is not globally cancellation-safe: dropping the waiting reserve
future loses its FIFO queue position. It preserves payload ownership because the
payload was never passed to that future. Dropping an unused permit releases the
capacity. Bound how long permits are held so admission cannot be starved.

Choose simultaneous readiness deliberately. Default `select! { ... }` randomizes initial
poll order. Use `biased;` and put cancellation first only if that polling priority
is the intended contract, with starvation consequences reviewed. This is not a
cross-thread atomic promise that any cancellation racing after the check wins.
The contract needs a linearization point; stronger ordering needs synchronization
shared by both acceptance and cancellation, not an extra unsynchronized check.

## Task ownership and shutdown

Spawning moves progress into another task; dropping the caller's future does not
cancel that child. Retain the handle under an owner whose shutdown observes the
result. Awaiting `&mut JoinHandle<T>` in `select! { ... }` preserves the handle if another
branch wins; passing and dropping the owned handle detaches its task.

Treat task failure and operation failure separately: `JoinHandle<Result<T, E>>`
has a join error (panic or cancellation) outside its application `Result`.
Do not silently discard either layer. An abort requests cancellation; awaiting
the handle observes termination and cleanup. It is not remote transaction undo.

Use a shutdown sequence fitted to the existing protocol: stop admitting work,
signal workers, drain or explicitly reject accepted work, then join workers.
Bound the wait only with a documented remaining-work policy. Dropping all senders
closes a channel only if no hidden clones remain; permits also matter when
waiting for a receiver to finish draining.

Acquire concurrency capacity before spawning, not inside an unbounded number of
new tasks. Offload bounded blocking work with `spawn_blocking`; once started it
cannot be aborted, even when its handle is aborted. Runtime shutdown timeouts
stop waiting rather than stop that work. Give blocking loops their own cooperative
stop mechanism; use a dedicated thread for persistent blocking workers.

## Send, Sync and retained state

For ordinary std types with their default allocators:

| Type | Relevant condition |
|---|---|
| `&T` | Send exactly when `T: Sync` |
| `&mut T` | Send exactly when `T: Send`; Sync when `T: Sync` |
| `Arc<T>` | Send and Sync require `T: Send + Sync` |
| `Mutex<T>` | Send and Sync require `T: Send`, not `T: Sync` |
| `Cell<T>` | Not Sync; the type is not restricted to Copy values |

`Cell::get` requires Copy; `replace` can move a non-Copy value. `Arc<RefCell<T>>`
does not make RefCell thread-safe. A mutex around one `Rc` does not protect other
Rc aliases. Do not add `unsafe impl Send/Sync` as an error suppression mechanism.

For a non-Send async future, inspect values retained across suspension, including
guards and captured references. An explicit lexical scope ending before await is
usually the clearest repair. `'static` means no shorter-lived borrowed data in
the spawned value; it does not mean the task must live forever. Use local tasks
only when thread confinement is an intentional runtime contract.

## Lock lifetime and cancellation

Use a synchronous mutex for short in-memory critical sections without await.
Extract the needed owned result in an explicit block, release the guard, then
await. `if let` or `match` scrutinee temporaries can retain guards while their
borrowed results are used; do not infer guard release from visual indentation.

Use Tokio's async mutex when exclusive I/O access really must span await. The
guard is designed for that use, but exclusion is not transactional recovery.
Cancellation or panic can release it with half-updated state. Tokio mutexes do
not poison; std poisoning is a signal, not a soundness guarantee or a rollback.

Cancelling Tokio `Mutex::lock`, `RwLock` acquisition or semaphore acquisition
loses queue position. Recreating them in a busy selection loop can starve the
operation even while memory remains safe. Keep a persistent acquisition future
when fairness progress is part of the contract.

## Decidable lifecycle checks

Drive full capacity, pending acquisition, closure and concurrent readiness with
explicit synchronization. Assert original object identity/ownership and observed
worker completion, not just an error variant. Exercise a cancellation after
external progress as well as before admission when the protocol permits both.
Do not use a sleeping test or a surviving process as proof that no task leaked.

<!-- sources: tokio-select, tokio-sender, tokio-tasks, tokio-blocking, tokio-mutex, rust-sync -->
