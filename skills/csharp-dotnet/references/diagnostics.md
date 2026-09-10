# Diagnostics and performance

Verified against: .NET 10 diagnostic tools.

## Contents

- [Evidence rules](#evidence-rules)
- [What to report](#what-to-report)
- [The tools](#the-tools)
- [Start with counters](#start-with-counters)
- [Thread-pool starvation](#thread-pool-starvation)
- [Memory growth and leaks](#memory-growth-and-leaks)
- [CPU and latency](#cpu-and-latency)
- [Hangs and crashes](#hangs-and-crashes)
- [Containers and production](#containers-and-production)
- [Benchmarking](#benchmarking)
- [Allocation patterns worth checking](#allocation-patterns-worth-checking)

## Evidence rules

These are what separate a diagnosis from a guess. Violating any one of them invalidates the
conclusion.

- Measure an optimised build (`-c Release`) in its real deployment form — same container, same
  runtime configuration, same tiered-compilation and GC settings.
- Record the environment before collecting anything: commit and dirty state, SDK and runtime
  versions, OS, architecture, CPU count and container limits, tool versions, and the exact
  commands run.
- Establish a deterministic reproduction *before* changing code. Without one there is nothing
  to compare against.
- Separate the phases: cold start, first use, warm steady state, overload, drain, shutdown.
  They have different causes and different fixes.
- Warm tiered compilation and caches unless cold behaviour is the subject.
- Do not infer managed memory retention from RSS alone — RSS includes the GC's uncommitted
  budget, native allocations and mapped files.
- Do not claim a fix from one average, one trace or the fastest run. Report the distribution
  and the tail.
- Preserve the raw artefacts, and report missing symbols, dropped events, profiler overhead
  and anything you could not measure.
- Dumps, traces and logs contain connection strings, tokens and user data. Treat them as
  sensitive.

## What to report

1. **Symptom** — the observable impact and the target it violates, in numbers.
2. **Reproduction** — workload and environment.
3. **Collection** — tools, commands, duration, artefact paths.
4. **Evidence** — counters, trace, dump, benchmark distribution.
5. **Ownership** — managed code, runtime/GC, native, kernel, I/O, a dependency.
6. **Dominant cause** — the largest supported cost or wait, not a list of suspicions.
7. **Fix** — the smallest change that addresses that cause.
8. **Validation** — equivalent before/after runs with spread and tail.
9. **Residual risk** — what is still unexplained.

## The tools

| Tool | Answers |
|---|---|
| `dotnet-counters` | What is happening right now: GC, thread pool, exceptions, request rate. First thing to run, no restart needed |
| `dotnet-trace` | Where wall-clock or CPU time goes; runtime events; custom `EventSource` |
| `dotnet-dump` | What the heap and threads contain at one instant — hangs, leaks, crashes |
| `dotnet-gcdump` | Managed heap graph only, much smaller than a full dump, safe to take repeatedly |
| `dotnet-stack` | A quick managed stack of every thread without a dump |
| `dotnet-monitor` | The same data pulled on a trigger in a container or Kubernetes |
| BenchmarkDotNet | Whether a code-level change is actually faster |

Install with `dotnet tool install -g <name>`. They attach to a running process by PID and do
not require the app to reference anything.

## Start with counters

```bash
dotnet-counters monitor --process-id <pid> --counters System.Runtime,Microsoft.AspNetCore.Hosting
```

Read them in this order:

| Signal | Means |
|---|---|
| `ThreadPool Queue Length` rising, `ThreadPool Thread Count` climbing, CPU low | Blocking on async — go to the next section |
| `% Time in GC` high, `Allocation Rate` high | Allocation pressure; find the allocating path |
| Gen 2 size and LOH size rising and never falling after a Gen 2 | A leak |
| `Exception Count` high | Exceptions used as control flow; they are ~1000× a return |
| `Requests/sec` flat while `Current Requests` climbs | Downstream saturation or a queue |

## Thread-pool starvation

The signature: requests queue, latency climbs, CPU stays low, thread count creeps up by about
two per second. The cause is almost always synchronous waiting on asynchronous work —
`.Result`, `.Wait()`, `GetAwaiter().GetResult()`, `Task.Run(...).Wait()`, a `lock` held across
an I/O call, or `Thread.Sleep` inside a handler.

Confirm it:

```bash
dotnet-stack report --process-id <pid>
```

Look for application frames sitting under `Task.Wait`, `ManualResetEventSlim.Wait`,
`Monitor.Enter` or `TaskAwaiter.GetResult`.

Raising `ThreadPool.SetMinThreads` hides the symptom for a while and is not a fix; it buys time
during an incident at the cost of more memory and context switching.

## Memory growth and leaks

1. Confirm growth in managed memory, not just RSS: watch `GC Heap Size` and the Gen 2/LOH
   counters across several Gen 2 collections.
2. Take two `dotnet-gcdump` snapshots minutes apart under steady load and compare — the types
   that grew are the leak.
3. For a full dump: `dotnet-dump collect -p <pid>`, then `dotnet-dump analyze <file>`:
   - `dumpheap -stat` — what is on the heap, by type and size.
   - `gcroot <address>` — why that instance is still alive. This is the answer; the type name
     alone is not.
   - `dumpheap -type <name>` to pick an instance to root.

The recurring managed-leak shapes in .NET services:

- An event handler subscribed and never unsubscribed — the publisher holds the subscriber.
- A static or singleton collection used as a cache with no eviction.
- A transient `IDisposable` resolved from the root container: the container holds every
  instance until shutdown.
- A `CancellationTokenSource` that is never cancelled or disposed, with registrations attached.
- A captured `HttpResponseMessage`/`Stream` never disposed, holding a connection.
- `Timer` instances with no reference held by you but a live callback held by the runtime.

Large Object Heap growth specifically means allocations over 85 000 bytes: oversized arrays,
big strings, buffered response bodies. Fix by pooling (`ArrayPool<T>`) or streaming, not by
tuning the GC.

## CPU and latency

```bash
dotnet-trace collect --process-id <pid> --profile cpu-sampling --duration 00:00:30
```

Convert to a viewer format (`--format speedscope`) and read the inverted call tree: the
question is which leaf frames accumulate the samples, not which methods appear.

`--profile gc-verbose` for allocation-heavy suspicion, and a custom provider list when you are
after ASP.NET Core, EF Core or `HttpClient` events specifically.

For latency without CPU, the wait is what matters: a trace with the
`System.Threading.Tasks.TplEventSource` provider, plus the dependency's own telemetry. A p99
that is far from p50 is queueing or a retry storm, not slow code.

## Hangs and crashes

- Hang: `dotnet-stack report` first (cheap), then a dump if the stacks are not conclusive.
  Look for a deadlock pair — two threads each holding what the other waits for — or one thread
  holding a lock across an `await`.
- Crash: enable automatic dumps so the failing state is captured rather than guessed at:

```bash
export DOTNET_DbgEnableMiniDump=1
export DOTNET_DbgMiniDumpType=4          # 4 = full; 2 = heap, smaller
export DOTNET_DbgMiniDumpName=/dumps/core.%p
```

Then `dotnet-dump analyze` with `pe -lines` on the exception and `clrstack -all`.

- An unhandled exception on a thread-pool thread or in a `BackgroundService` terminates the
  process by default. Silence there means someone is swallowing it.

## Containers and production

- The tools need the target's `/tmp` for the diagnostic socket: same container, a shared
  process namespace, or `dotnet-monitor` as a sidecar.
- A dump needs `SYS_PTRACE`; without it collection fails with a permissions error rather than
  a useful message.
- Set memory limits explicitly. Without them the GC sizes its heap from the host, and the
  container is killed long before the GC feels pressure. `DOTNET_GCHeapHardLimit` or the
  container limit both work; the container limit is the honest one.
- Server GC is the default for ASP.NET Core; on a small container (one or two cores) Workstation
  GC can be measurably better. Measure rather than assume either way.
- `dotnet-monitor` with a trigger (CPU above X, memory above Y) captures the artefact during
  the incident instead of after it.

## Benchmarking

BenchmarkDotNet, in its own project, in Release:

- Never benchmark in a debugger or from a test runner.
- `[MemoryDiagnoser]` for allocation counts; that number is usually more actionable than time.
- Compare with `[Baseline]` on the current implementation; a ratio is comparable across
  machines, an absolute figure is not.
- Trust the distribution BenchmarkDotNet prints, not the mean alone. If the error is wide, the
  benchmark is measuring noise.
- A microbenchmark proves a micro-fact. Confirm the end-to-end effect with the same workload
  that showed the problem.

## Allocation patterns worth checking

When a trace points at allocation rather than a specific method, these are the usual sources,
roughly in order of payoff:

- String concatenation in a loop, and `Substring`/`Split` on a hot path.
- `IndexOf`/`Equals`/`StartsWith` without `StringComparison.Ordinal` — culture-sensitive
  comparison is both slower and allocating for some paths.
- LINQ in a per-request hot loop: each operator allocates an enumerator and a closure.
- `ToList()`/`ToArray()` materialising something that is enumerated once.
- Boxing: a struct passed as `object`, an `enum` used as a dictionary key with the default
  comparer, `string.Format` with value-type arguments.
- `new Regex(...)` per call, or `RegexOptions.Compiled` on a rarely used pattern. Use
  `[GeneratedRegex]`.
- `JsonSerializer` without a source-generated context, especially in AOT/trimmed apps.
- `async` methods that allocate a state machine for a path that almost always completes
  synchronously — a candidate for `ValueTask`, but only with a measurement.
- Unsealed classes in hot virtual call paths (CA1852): sealing enables devirtualisation.

<!-- sources: soltes-perf, dotnet-official, dotnet-docs -->
