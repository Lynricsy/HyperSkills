# Concurrency: TaskPool, Worker and Sendable

Verified against: OpenHarmony application-dev docs, `arkts-utils/taskpool-vs-worker`, `worker-and-taskpool`, `taskpool-introduction`, `worker-introduction`, `arkts-sendable`, `arkts-async-lock-introduction`.

## Contents

- [The model](#the-model)
- [TaskPool vs Worker](#taskpool-vs-worker)
- [Choosing](#choosing)
- [Writing a TaskPool task](#writing-a-taskpool-task)
- [Writing a Worker](#writing-a-worker)
- [What can cross a thread](#what-can-cross-a-thread)
- [@Sendable](#sendable)
- [Async lock](#async-lock)
- [Failure table](#failure-table)

## The model

Threads are **isolated**; memory is not shared. Both TaskPool and Worker hand data across
by the structured clone algorithm unless the value is `ArrayBuffer`, `SharedArrayBuffer` or
`@Sendable`. There is no shared mutable heap, so "just pass the object and mutate it" does
not work — the other side gets a copy and your mutation stays there.

The UI thread runs `build()`, all lifecycle callbacks and all event handlers. Anything that
can take longer than a frame belongs off it.

## TaskPool vs Worker

| Item | TaskPool | Worker |
|---|---|---|
| Memory | isolated, not shared | isolated, not shared |
| Parameter passing | parameters passed directly | must be wrapped into one message object |
| Invocation | call a `@Concurrent`-decorated function | post a message, dispatch it in the worker |
| Result | returned asynchronously by default | post a message back, parse in `onmessage` |
| Lifecycle | managed by the pool | **you** create and destroy threads |
| Max count | managed automatically | **at most 64 per process**, fewer under memory pressure |
| Max task duration | **3 minutes** (excluding time in Promise/async I/O) | no limit |
| Priority | supported | **configurable only since API version 18** |
| Cancellation | supported | **not supported** |
| Thread reuse | yes | no |
| Delayed execution | yes | no |
| Task dependencies | yes | no |
| Serial queue | yes | no |
| Task group | yes | no |
| Periodic task | yes | no |
| Async queue | yes | no |

The three-minute cap is the number people get wrong. It measures **execution** time, not
wall time: a task that spends fifty minutes awaiting network I/O is fine, a task that spends
four minutes computing is killed. So "it takes a long time" is not the criterion — "it
computes for a long time" is.

## Choosing

**TaskPool is the default.** Its threads are bound to the system scheduling priority and it
load-balances automatically; Worker makes you pay creation and management cost yourself.

Use **Worker** when one of these is true:

- A single task computes for more than three minutes — e.g. an hour-long background
  prediction run.
- A set of synchronous tasks must share thread context — e.g. a handle that must be created
  once and stay alive for every subsequent call on that thread.
- The thread must be long-lived and you genuinely need to own its lifecycle.

Use **TaskPool** when:

- Tasks are relatively independent (per-image decode, per-row computation).
- Tasks need priorities (mandatory before API 18, since Worker had none).
- Tasks are cancelled often — e.g. prefetching neighbours in a gallery and discarding them
  on swipe. Worker cannot cancel at all, so a Worker-based prefetcher keeps computing work
  the user has already scrolled past.
- There are many of them, or they come from several modules, and you want the pool to
  manage load.

Two anti-patterns, both common in ports from Android:

- **One long-lived Worker used as a general-purpose background thread.** It serializes every
  piece of work behind whatever is currently running, cannot cancel, and cannot prioritize
  before API 18. `WorkManager` does not map onto this.
- **A Worker per unit of work.** Creation cost plus the 64-per-process ceiling; the pool
  exists for exactly this.

## Writing a TaskPool task

```ts
import { taskpool } from '@kit.ArkTS';

@Concurrent
function computeTotal(rows: PriceRow[]): number {
  let sum = 0;
  for (let i = 0; i < rows.length; i++) { sum += rows[i].qty * rows[i].price; }
  return sum;
}

const task = new taskpool.Task(computeTotal, rows);
const total = await taskpool.execute(task, taskpool.Priority.HIGH);
```

Rules for the `@Concurrent` function:

- It must be a **top-level** function (consistent with `arkts-no-nested-funcs`) and it must
  carry `@Concurrent`. A closure over module state will not see your values — the function
  runs in another context.
- Parameters and return value must be clone-able or `@Sendable`.
- `taskpool.cancel(task)` cancels a task that has not started or is running; handle the
  cancellation error at the call site.
- `taskpool.Task` supports dependencies (`addDependency`), groups (`TaskGroup`), serial
  queues (`SequenceRunner`) and periodic execution. Reach for those before hand-rolling
  coordination.
- A long-running task can report progress back to the host with
  `taskpool.Task.onReceiveData` / `sendData`.

## Writing a Worker

```ts
// host
import { worker } from '@kit.ArkTS';
const w = new worker.ThreadWorker('entry/ets/workers/Sync.ets');
w.onmessage = (e) => { /* parse e.data */ };
w.onerror = (e) => { /* must be handled; an unhandled worker error is silent */ };
w.postMessage({ kind: 'start', since: lastSync });

// later, without fail
w.terminate();
```

```ts
// entry/ets/workers/Sync.ets
import { worker, ThreadWorkerGlobalScope, MessageEvents } from '@kit.ArkTS';
const port: ThreadWorkerGlobalScope = worker.workerPort;
port.onmessage = (e: MessageEvents) => { port.postMessage(result); };
```

- The worker script must be registered in the module's `build-profile.json5`
  (`buildOption.sourceOption.workers`) or it will not be packaged, and the failure is a
  runtime "cannot find module".
- You own `terminate()`. A worker that is never terminated occupies one of the 64 slots for
  the process lifetime.
- Since API 18 you can set the worker's priority; before that, priority-sensitive work had
  to go to TaskPool.
- For a Worker that must call back into a host-thread API, the documented route is the
  host-interface invocation pattern; do not try to reach UI objects from the worker.

## What can cross a thread

| Value | Behaviour |
|---|---|
| primitives, plain objects, `Array`, `Map`, `Set`, `Date` | structured clone — a copy |
| `ArrayBuffer` | clone, or **transfer** (the sender's buffer becomes unusable) |
| `SharedArrayBuffer` | genuinely shared memory |
| `@Sendable` class instance | shared reference with concurrency rules |
| `Transferable` / NativeBinding objects | moved across |
| functions, closures | **cannot cross** |
| ArkUI components, `UIContext`, `Context` | **cannot cross** |

Clone cost is proportional to the graph you pass. Passing a whole view model to compute one
number is a real cost; pass the number.

## @Sendable

`@Sendable` marks a class whose instances can be shared between threads by reference
instead of copied. The constraints are strict, and they exist so the runtime can guarantee
safety:

- Fields must themselves be sendable types; a non-sendable field is rejected.
- Property layout is fixed — the ArkTS layout rule applies with no exceptions.
- No arbitrary closures captured; methods may not capture non-sendable context.
- `collections.Array`, `collections.Map`, `collections.Set` are the sendable container
  equivalents; the ordinary `Array`/`Map`/`Set` are not sendable.
- A `@Sendable` instance can be frozen to make it read-only across threads.
- `@Sendable` classes are **not** accepted by `UIUtils.makeV1Observed`, and sendable
  containers are excluded from the V1/V2 interop APIs — so a sendable model is a
  concurrency model, not a UI state model. Convert at the boundary.

Use `@Sendable` when the same large structure is read by several tasks. For a
request/response pair, cloning is simpler and usually cheaper than making the type
sendable.

## Async lock

`ArkTS` provides an async lock (`AsyncLock`) for serializing access to a shared sendable
object across concurrent tasks. It is the right tool when two tasks read-modify-write the
same sendable state; a boolean "isBusy" flag is not, because the check and the set are not
atomic across an await.

## Failure table

| Pattern | Consequence |
|---|---|
| CPU-bound loop on the UI thread | dropped frames, ANR-class freeze |
| TaskPool task computing > 3 minutes | task terminated |
| Worker used for many short independent tasks | creation cost, 64-slot exhaustion, no cancellation |
| One long-lived Worker as a general background thread | work serialized behind the current task; nothing cancellable |
| `worker.terminate()` never called | a permanently occupied worker slot |
| Worker script not in `sourceOption.workers` | runtime module-not-found |
| Mutating a cloned object and expecting the host to see it | silently lost write |
| Passing a closure or a `UIContext` across threads | cannot cross; error or silent failure |
| Ordinary `Array`/`Map` in a `@Sendable` field | rejected; use `collections.*` |
| `@Sendable` model fed into V1/V2 interop APIs | rejected |
| Cloning a whole view model per task | clone cost proportional to the object graph |

<!-- sources: openharmony-docs, corey-harmonyos, earfrog-arkts, huawei-docs -->
