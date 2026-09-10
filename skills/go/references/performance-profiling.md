# Performance and profiling

Verified against: Go 1.26 and Go 1.27.

## Contents

- [Order of operations](#order-of-operations)
- [Choosing the profile](#choosing-the-profile)
- [Collecting a profile](#collecting-a-profile)
- [Reading a pprof profile](#reading-a-pprof-profile)
- [Allocation work](#allocation-work)
- [Execution traces](#execution-traces)
- [Blocking and contention](#blocking-and-contention)
- [GC and memory limits](#gc-and-memory-limits)
- [Compiler diagnostics](#compiler-diagnostics)
- [Profile-guided optimisation](#profile-guided-optimisation)
- [Common mistakes](#common-mistakes)

## Order of operations

1. Rule out the world outside the process. If most of the latency is a database query, a
   remote call or disk, no amount of allocation work changes the number. Measure at the
   boundary first.
2. Define the metric before touching code: p99 latency of one endpoint, allocations per
   request, throughput at a fixed concurrency. "Faster" is not a metric.
3. Take a baseline you can re-run — a benchmark with `for b.Loop()` and `-count=10`, or a
   load test with a fixed profile.
4. Profile to locate the cost. Intuition about hot spots is usually wrong.
5. Change one thing.
6. Re-measure and compare with `benchstat`. Keep the change only if the `p` column says
   the difference is real.
7. Leave a comment with the reason and the delta, or the next reader will revert it as
   pointless complexity.

## Choosing the profile

| Symptom | Profile |
|---|---|
| CPU saturated, latency scales with load | CPU (`-cpuprofile`, `/debug/pprof/profile`) |
| RSS grows and does not come back | Heap in-use (`/debug/pprof/heap`) |
| GC runs constantly, CPU in `runtime.mallocgc` | Allocations (`-memprofile`, `/debug/pprof/allocs`) |
| Latency high while CPU is idle | Execution trace, or block profile |
| Throughput does not scale with cores | Mutex profile, then trace |
| Goroutine count climbs forever | Goroutine profile; `goroutineleak` on Go 1.27+ |

## Collecting a profile

From a benchmark, which is the cheapest and most repeatable source:

```bash
go test -run '^$' -bench BenchmarkParse -benchmem \
        -cpuprofile cpu.out -memprofile mem.out ./internal/parse
go tool pprof -http=:8080 cpu.out
```

From a live process, after importing `net/http/pprof` (it registers its handlers on
`http.DefaultServeMux`; on a custom mux register them yourself, and never expose the
endpoint publicly):

```bash
go tool pprof 'http://host:6060/debug/pprof/profile?seconds=30'   # CPU
go tool pprof 'http://host:6060/debug/pprof/heap'                 # live objects
go tool pprof 'http://host:6060/debug/pprof/allocs'               # all allocations since start
curl 'http://host:6060/debug/pprof/goroutine?debug=2' > goroutines.txt
curl 'http://host:6060/debug/pprof/trace?seconds=5' > trace.out
```

The CPU profile samples at 100 Hz, so a 30-second capture holds roughly 3000 samples:
anything under a percent of that is noise. `heap` shows what is live now; `allocs` shows
everything ever allocated, which is what you want when the problem is GC pressure rather
than retention.

## Reading a pprof profile

Inside `go tool pprof`:

```
top            # by flat: the functions that spend time in their own frames
top -cum       # by cumulative: the functions whose subtrees are expensive
list ParseUser # annotated source, cost per line
peek regexp    # callers and callees of matching functions
web            # SVG call graph (needs graphviz)
```

- **flat** is time spent in the function's own instructions. High flat means the function
  itself is the cost.
- **cum** is the function plus everything it calls. High cum with low flat means an
  orchestrator: drill into its children.
- Read `top -cum` first to find the expensive subtree, then `top` and `list` to find the
  line.
- `runtime.mallocgc`, `runtime.growslice`, `runtime.mapassign` and `runtime.convT*` near
  the top are **symptoms**, not causes. They mean your code allocates; cross-reference the
  allocation profile to find where.
- `runtime.gcBgMarkWorker` and `runtime.scanobject` high in a CPU profile means the GC is
  the load, which is again an allocation problem.
- `syscall.Syscall` / `runtime.netpoll` high means the process is waiting on I/O, and the
  answer is batching or concurrency, not micro-optimisation.

Comparing two profiles: `go tool pprof -base old.out new.out` shows the delta rather than
two absolute pictures.

## Allocation work

Allocation reduction is usually the highest-leverage change in a Go service, because it
cuts both the allocation cost and the GC work it creates. `-benchmem` reports `B/op` and
`allocs/op`; drive `allocs/op` down first.

The usual wins:

- Preallocate when the size is known: `make([]T, 0, len(src))`, `make(map[K]V, n)`.
  Growing a slice reallocates and copies at every doubling.
- Use `strings.Builder` (or `bytes.Buffer`) for concatenation in a loop; `s += x` allocates
  a new string every iteration. `Builder.Grow(n)` when you can estimate the size.
- Return the value, not a pointer, for small structs that do not escape. A pointer forces
  a heap allocation the escape analysis could otherwise avoid.
- `append` to a caller-supplied slice (`func AppendFoo(dst []byte, ...) []byte`) instead of
  allocating a fresh one; this is the pattern `strconv.AppendInt` and `time.AppendFormat`
  use.
- `sync.Pool` for large temporary buffers on a proven hot path only. Reset before `Put`,
  never assume anything survives a GC, and never pool an object that holds request data.
- Avoid `[]byte`↔`string` conversions in a loop; both copy. Many APIs have both forms
  (`strconv.AppendQuote`, `bytes.Contains`).
- Interface boxing allocates when a non-pointer value is stored in an interface — visible
  as `runtime.convT64` and friends.

Confirm each change with `benchstat`:

```bash
go test -run '^$' -bench . -benchmem -count=10 > old.txt
# one change
go test -run '^$' -bench . -benchmem -count=10 > new.txt
go tool benchstat old.txt new.txt
```

## Execution traces

`runtime/trace` answers "why is nothing happening" — scheduling, GC pauses, syscall
blocking, goroutine lifetimes:

```bash
go test -run '^$' -bench . -trace trace.out ./...
curl 'http://host:6060/debug/pprof/trace?seconds=5' > trace.out
go tool trace trace.out
```

Useful views: the goroutine analysis page (execution vs blocking time per goroutine), the
scheduler latency profile, and the syscall/network blocking profiles. A wide gap in the
timeline with idle processors means the work is serialised behind something — a lock, a
single channel, or a database with one connection.

`trace.WithRegion` and `trace.NewTask` annotate application phases so the timeline maps to
your own vocabulary. Note that on Go 1.27 `go tool trace -http=:6060` binds to localhost
unless you pass an explicit address.

## Blocking and contention

Both profiles are off by default because they cost something to collect:

```go
runtime.SetBlockProfileRate(1_000_000) // sample one blocking event per millisecond of delay
runtime.SetMutexProfileFraction(100)   // sample 1 in 100 contention events
```

Then `go tool pprof http://host:6060/debug/pprof/block` and `.../mutex`. The block profile
covers channel operations, `select` and `sync` waits; the mutex profile covers contended
`Mutex`/`RWMutex` only. Reach for `RWMutex` after a mutex profile shows read contention,
never before — it is slower than `Mutex` when writes are frequent.

## GC and memory limits

- `GOGC` (default 100) sets the heap growth target between collections; raising it trades
  memory for less GC CPU.
- `GOMEMLIMIT` (Go 1.19) is a soft limit that makes the GC work harder as the heap
  approaches it. In a container, set it a little below the cgroup limit so the collector
  reacts before the OOM killer does.
- `GOMAXPROCS` defaults to the number of CPUs the process sees. Since Go 1.25 the runtime
  is cgroup-aware and derives it from the CPU limit, so a container with a fractional
  quota no longer needs the manual override that older deployments used.
- `GODEBUG=gctrace=1` prints one line per collection — the fastest way to see whether GC
  frequency is the problem before opening a profile.

## Compiler diagnostics

```bash
go build -gcflags='-m' ./...            # escape analysis: what moves to the heap and why
go build -gcflags='-m -m' ./pkg         # more detail on one package
go test -bench . -benchmem              # B/op and allocs/op
go build -gcflags='-d=ssa/check_bce/debug=1' ./...   # where bounds checks remain
```

`-m` output like `moved to heap: buf` or `... escapes to heap` names the exact line to fix.
Do not chase every escape: only the ones on a path the profile says is hot.

## Profile-guided optimisation

Committing a representative CPU profile as `default.pgo` next to `main` makes `go build`
use it automatically: the compiler inlines the hot call sites more aggressively, typically
for a few percent. Collect it from production under real load, refresh it when the
workload shifts, and treat it as a build input — a stale profile just wastes inlining
budget.

## Common mistakes

| Mistake | Fix |
|---|---|
| Optimising before profiling | Take a baseline and a profile first |
| One benchmark run compared by eye | `-count=10` and `benchstat` |
| Chasing `runtime.mallocgc` itself | Find the allocating call in the alloc profile |
| Reading `top` before `top -cum` | The subtree tells you where to drill |
| `sync.Pool` everywhere | Only for large buffers on a proven hot path |
| `RWMutex` by default | Only after a mutex profile shows read contention |
| `s += x` in a loop | `strings.Builder` with `Grow` |
| Heap profile used to diagnose GC pressure | `allocs`, not `heap` |
| Public `/debug/pprof` endpoint | Bind it to an internal port or require auth |
| Micro-optimising while a query dominates | Measure the boundary first |

<!-- sources: samber-golang, ashwin-go, douglas-pprof, go-doc-diagnostics, go-release-notes -->
