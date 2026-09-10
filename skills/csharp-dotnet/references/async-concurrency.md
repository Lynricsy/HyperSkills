# Async and concurrency

Verified against: .NET 10.

## Contents

- [The failure modes, in order of frequency](#the-failure-modes-in-order-of-frequency)
- [Blocking on async](#blocking-on-async)
- [async void](#async-void)
- [ConfigureAwait](#configureawait)
- [ValueTask](#valuetask)
- [Cancellation](#cancellation)
- [Doing independent work concurrently](#doing-independent-work-concurrently)
- [Task.Run and the thread pool](#taskrun-and-the-thread-pool)
- [Fire and forget](#fire-and-forget)
- [Async streams](#async-streams)
- [Shared mutable state](#shared-mutable-state)
- [Producer/consumer with Channels](#producerconsumer-with-channels)
- [Diagnosing a hang](#diagnosing-a-hang)

## The failure modes, in order of frequency

1. Blocking on async work (`.Result`, `.Wait()`, `GetAwaiter().GetResult()`).
2. `async void` outside an event handler, so exceptions vanish.
3. Awaiting sequentially what could run concurrently.
4. A `CancellationToken` accepted and never passed on.
5. `ValueTask` consumed more than once.
6. `Task.Run` wrapped around work that is already asynchronous.
7. Fire-and-forget (`_ = SomethingAsync();`) that silently drops faults.

Everything below is one of these.

## Blocking on async

`.Result`, `.Wait()` and `GetAwaiter().GetResult()` on an incomplete task have two distinct
failure modes, and both are severe:

- **Deadlock** where a synchronization context is captured — a UI thread (WinForms, WPF,
  MAUI) or a legacy ASP.NET request. The continuation is queued to the context, the context
  is blocked waiting for the task, and neither can proceed.
- **Thread-pool starvation** where there is no context, which is the ASP.NET Core case. Each
  blocked call occupies a pool thread; the pool injects new threads slowly (roughly one per
  0.5 s beyond the minimum), so the request queue grows faster than throughput recovers. The
  symptom is an app that suddenly stops responding under load with low CPU.

The constructor case deserves its own note: you cannot `await` in a constructor, so blocking
there looks unavoidable. It is not — expose an `async` factory (`static Task<T> CreateAsync`),
or move the work into `IHostedService.StartAsync` / a lazily awaited
`Task<T>` field, and never into the constructor.

The only defensible blocking call is in `Main` of a console app before any async work exists,
and even there `async Task Main` removes the need.

## async void

An exception thrown from an `async void` method is raised on the synchronization context —
which in a modern service means it becomes an unhandled exception that can tear down the
process, and in every case means the caller cannot catch it and no `Task` records the failure.

Make it `async Task`. The single legitimate exception is a real event handler
(`button.Clicked += async (s, e) => ...`), and even there the body should be wrapped in a
`try`/`catch` that reports.

## ConfigureAwait

`ConfigureAwait(false)` says "do not resume on the captured context". It matters only where a
context exists to capture.

- **ASP.NET Core has no synchronization context.** Adding `ConfigureAwait(false)` there is
  noise; it does not prevent any deadlock, because there is none to prevent.
- **Library code** that might be called from a UI app or legacy ASP.NET should use it on every
  await, so a caller who blocks does not deadlock and so continuations do not queue onto the
  UI thread.
- **UI code** must not use it where the continuation touches UI state — that is exactly the
  context you need.

On .NET 8 and later, `ConfigureAwait(ConfigureAwaitOptions)` adds `SuppressThrowing` (await a
task for completion without observing its exception) and `ForceYielding`.

If you added `ConfigureAwait(false)` to fix a hang, the hang is still there — find the
blocking call.

## ValueTask

`ValueTask`/`ValueTask<T>` exists to avoid allocating a `Task` for a method that usually
completes synchronously (a cache hit, a buffered read). It comes with a narrower contract:

- Await it **once**, and never after the operation has completed. The backing
  `IValueTaskSource` may be recycled the moment the result is consumed, so a second await can
  observe another operation's result.
- Do not store one in a field, hand it to `Task.WhenAll`, or await it from two places. Call
  `.AsTask()` first if you need any of that, or `.Preserve()` to make it safely re-awaitable.
- Do not return `ValueTask` from a public API by default. Return `Task` unless a measurement
  shows the allocation matters; `Task` is cacheable (`Task.CompletedTask`,
  `Task.FromResult` for common values) and has none of these rules.

## Cancellation

- Accept `CancellationToken` as the last parameter of every async method that does I/O or
  loops, and pass it to everything you call. A token that is accepted and dropped is worse
  than none: it looks cancellable and is not.
- In ASP.NET Core the request-aborted token is bound to a `CancellationToken` handler
  parameter automatically; in a `BackgroundService`, `ExecuteAsync` receives the stopping
  token.
- `OperationCanceledException` is the expected result, not an error. Let it propagate; if you
  must catch it, distinguish `token.IsCancellationRequested` (deliberate) from a timeout token.
- Use `CancellationTokenSource.CreateLinkedTokenSource` to combine a caller's token with a
  timeout, and dispose the source.
- `Thread.Sleep` inside async code blocks a pool thread and ignores cancellation. Use
  `await Task.Delay(delay, token)`.

## Doing independent work concurrently

Sequential awaits in a loop over independent items serialise the latency:

```csharp
// Serial: total time is the sum.
foreach (var id in ids)
    results.Add(await store.GetAsync(id, ct));

// Concurrent, unbounded — fine for a handful of items.
var results = await Task.WhenAll(ids.Select(id => store.GetAsync(id, ct)));

// Concurrent, bounded — the default for anything that can grow.
await Parallel.ForEachAsync(
    ids,
    new ParallelOptions { MaxDegreeOfParallelism = 8, CancellationToken = ct },
    async (id, token) => results.Add(await store.GetAsync(id, token)));
```

Unbounded `Task.WhenAll` over a large collection is its own outage: it opens as many
connections as there are items. Bound it whenever the collection size is caller-controlled.

Note that `Task.WhenAll` throws only the first exception when awaited; inspect
`task.Exception` (an `AggregateException`) if you need all of them. The `results` list in the
bounded example above must be a concurrent collection or be guarded — `List<T>` is not
thread-safe.

## Task.Run and the thread pool

`Task.Run` moves work to a pool thread. That is right for a genuinely CPU-bound computation
that would otherwise block a request or the UI thread. It is wrong for anything already
asynchronous: `Task.Run(async () => await http.GetAsync(...))` adds a thread hop, an extra
`Task`, and hides the fact that the operation was never blocking.

Never use `Task.Run` in ASP.NET Core to "offload" a request: the request is already on a pool
thread, so you have just used two.

## Fire and forget

`_ = DoWorkAsync();` runs the work and discards both the completion and the exception. If the
work matters, one of:

- `await` it — usually the honest answer;
- queue it: a `Channel<T>` written by the request path and read by a `BackgroundService`,
  which gives you backpressure, cancellation on shutdown and a place to log failures;
- for ASP.NET Core, `IHostApplicationLifetime` plus a hosted service, not a bare task.

If you truly must not wait, at minimum attach a continuation that logs the fault, and be aware
the work will be killed at shutdown.

## Async streams

`IAsyncEnumerable<T>` with `await foreach` streams results without buffering. Two details:

- Annotate the token parameter with `[EnumeratorCancellation]` on an `async IAsyncEnumerable`
  iterator, otherwise `WithCancellation` at the call site has no effect.
- `await foreach (var x in source.WithCancellation(ct).ConfigureAwait(false))` applies both
  settings; they are separate calls.

## Shared mutable state

Escalate in this order, and stop at the first step that works:

1. **Design it away.** Immutable data and per-operation instances have no race to lose.
2. **`System.Collections.Concurrent`** — `ConcurrentDictionary` for a shared cache,
   `ConcurrentQueue` for a hand-off. Note `GetOrAdd`'s factory can run more than once for the
   same key; if creation is expensive or has side effects, store a `Lazy<T>`.
3. **`Channel<T>`** to serialise access through message passing (below).
4. **`lock`** for a short, non-async critical section. You cannot `await` inside `lock`; use
   `SemaphoreSlim.WaitAsync` when the critical section is asynchronous, and always release in
   a `finally`.

`Interlocked` for counters. `volatile` almost never — if you think you need it, you need one
of the four steps above.

## Producer/consumer with Channels

```csharp
var channel = Channel.CreateBounded<WorkItem>(new BoundedChannelOptions(1_000)
{
    FullMode = BoundedChannelFullMode.Wait,   // backpressure instead of unbounded memory
    SingleReader = true,
});

// producer
await channel.Writer.WriteAsync(item, ct);

// consumer, inside a BackgroundService
await foreach (var item in channel.Reader.ReadAllAsync(stoppingToken))
    await HandleAsync(item, stoppingToken);
```

Use `CreateBounded`, not `CreateUnbounded`: an unbounded channel converts a downstream
slowdown into an out-of-memory kill. Call `Writer.Complete()` on shutdown so the reader loop
finishes.

## Diagnosing a hang

- `dotnet-counters monitor --counters System.Runtime` — a rising `ThreadPool Queue Length`
  with a rising `ThreadPool Thread Count` and low CPU is the signature of blocking on async.
- `dotnet-dump collect` then `dotnet-dump analyze <dump>`; in the analyser,
  `clrstack -all` (or `parallelstacks`) shows what every thread is waiting on. Frames
  containing `Task.Wait`, `ManualResetEventSlim.Wait` or `GetResult` under an application
  method are the blocking calls.
- A deadlock that only appears in a desktop app and not in tests is almost always the
  synchronization context: the test host has none.

<!-- sources: aaronontheweb, dotnet-docs, dotnet-official, awesome-copilot -->
