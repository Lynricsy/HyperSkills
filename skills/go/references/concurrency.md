# Concurrency

Verified against: Go 1.26 and Go 1.27.

## Contents

- [Deciding whether to be concurrent](#deciding-whether-to-be-concurrent)
- [Goroutine lifetime](#goroutine-lifetime)
- [errgroup is the default group](#errgroup-is-the-default-group)
- [Channels](#channels)
- [select and context](#select-and-context)
- [Picking a primitive](#picking-a-primitive)
- [sync primitives in detail](#sync-primitives-in-detail)
- [Pipelines](#pipelines)
- [The race detector](#the-race-detector)
- [Finding leaks](#finding-leaks)
- [Common mistakes](#common-mistakes)

## Deciding whether to be concurrent

Concurrency buys you overlap on waiting, not speed on computing. Before adding a goroutine,
check that the work actually waits (network, disk, a subprocess) or that the CPU work
genuinely parallelises. A synchronous version that is fast enough has no leaks, no races
and no shutdown story to get wrong.

## Goroutine lifetime

Every goroutine needs three answers before it is written:

1. **How does it exit?** A cancelled context, a closed input channel, or a loop with a
   bounded count. "When the work is done" is only an answer if a closed channel says so.
2. **Can the caller wait for it?** `errgroup.Wait`, `wg.Wait`, or a `done` channel the
   caller receives from. Without this, shutdown races the goroutine's last write.
3. **Can the caller stop it?** A context, or the ability to close its input.

Blocking on a channel nobody will ever touch is a permanent leak: the garbage collector
does not reclaim a goroutine just because the channel it waits on became unreachable.

Two structural rules follow:

- Do not start goroutines in `init()` or inside a constructor. A package that spawns work
  on import gives the caller no way to stop it and no way to observe its failure. Expose
  `Start(ctx)` / `Close() error` instead.
- Keep the synchronisation inside one function where you can. A goroutine spawned in one
  method and joined in another is a lifetime nobody can see by reading either.

## errgroup is the default group

`golang.org/x/sync/errgroup` covers almost every group-of-goroutines shape. It returns the
first error, cancels the siblings through the derived context, and caps concurrency:

```go
func FetchAll(ctx context.Context, urls []string, limit int) ([]*Result, error) {
    results := make([]*Result, len(urls))
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(limit) // 0 workers spawned beyond this; replaces a hand-rolled pool

    for i, u := range urls {
        g.Go(func() error {
            r, err := fetch(ctx, u)
            if err != nil {
                return fmt.Errorf("fetching %s: %w", u, err)
            }
            results[i] = r // distinct index per goroutine: no shared write, no mutex
            return nil
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

Points that matter in that shape:

- `g, ctx := errgroup.WithContext(ctx)` shadows `ctx` deliberately: the goroutines must use
  the *derived* context, otherwise a sibling's failure cancels nothing.
- Writing to distinct elements of a pre-sized slice is race-free and keeps output order
  aligned with input. This is almost always better than a results channel plus a collector.
- Loop variables are per-iteration since Go 1.22. Do not emit `u := u`.
- `g.Wait()` returns only the first error. When you need all of them, collect into the
  pre-sized slice and `errors.Join` afterwards.

Where nothing can fail and nothing needs cancelling, `sync.WaitGroup.Go` (Go 1.25+) is the
smaller tool:

```go
var wg sync.WaitGroup
for _, task := range tasks {
    wg.Go(func() { process(task) }) // no Add/Done pair to get wrong
}
wg.Wait()
```

On Go 1.24 and below this is `wg.Add(1)` before `go func()` and `defer wg.Done()` inside.
`Add` before the `go` statement, never inside the goroutine — otherwise `Wait` can return
before the counter is raised.

## Channels

- The sender closes; the receiver never does. Closing from the receiving side turns the
  next send into a panic.
- Sending transfers ownership. After `ch <- v`, the sender must not read or write `v`.
  This is what "share memory by communicating" means — it is about ownership, not about
  whether the value is a pointer. Sending a `*bytes.Buffer` is fine if the sender is done
  with it.
- Declare direction in signatures: `func worker(in <-chan Job, out chan<- Result)`. The
  compiler then rejects a receiver that closes its input.
- Buffer size is 0, or a number you can name — the exact number of producers, or the exact
  number of items you know are coming. An arbitrary buffer converts backpressure into
  latency and then into memory.
- Receiving from a closed channel yields the zero value immediately, forever. Use the
  two-value form (`v, ok := <-ch`) when the difference matters.
- A `nil` channel blocks forever in both directions. That is a feature in `select`: set a
  case's channel to `nil` to disable that branch.

## select and context

Every `select` that can block gets a `case <-ctx.Done():`, and every blocking send inside a
loop does too:

```go
for _, job := range jobs {
    select {
    case out <- job:
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

`context.Context` is the first parameter, named `ctx`, and never a struct field — the one
exception is a struct that must satisfy someone else's interface. Contexts are immutable,
so passing the same `ctx` to several calls is fine.

- `context.WithTimeout` / `WithDeadline` / `WithCancel` all return a `cancel` you must call,
  usually `defer cancel()`. Skipping it leaks the timer and the child context until the
  parent dies.
- `context.WithoutCancel(ctx)` (Go 1.21+) keeps the values and drops the cancellation, for
  background work that must outlive the request that started it.
- `context.AfterFunc(ctx, f)` (Go 1.21+) runs `f` in its own goroutine on cancellation,
  which is cleaner than a watchdog goroutine that selects on `Done`.
- Do not put request data in the context because it is convenient. Values belong in
  parameters; the context carries deadlines, cancellation, and cross-cutting metadata such
  as a trace ID.

Avoid `time.After` inside a loop: each iteration allocates a timer that lives until it
fires. Use one `time.NewTimer` and `Reset` it, or `time.NewTicker` with `defer Stop()`.

## Picking a primitive

| Situation | Use | Why |
|---|---|---|
| Handing work or results between goroutines | channel | Transfers ownership explicitly |
| Waiting for a group, first error wins, siblings cancelled | `errgroup.WithContext` | One construct for all three |
| Waiting for a group, nothing can fail | `sync.WaitGroup` (`wg.Go`, Go 1.25+) | No error plumbing |
| Capping in-flight work | `g.SetLimit(n)` | Replaces a hand-rolled pool |
| Protecting a few fields of one struct | `sync.Mutex` | Simple, obvious critical section |
| Read-mostly shared state, contention measured | `sync.RWMutex` | Only after a mutex profile says so |
| A counter or a flag | typed `atomic.Int64` / `atomic.Bool` | Lock-free, no pointer arithmetic |
| Cache with disjoint keys, read-heavy | `sync.Map` | Otherwise a plain map plus a mutex |
| One-time initialisation | `sync.OnceValue` / `OnceFunc` (Go 1.21+) | Returns the value; no package-level flag |
| Collapsing duplicate in-flight work | `x/sync/singleflight` | Stops a cache stampede |

Default to a mutex over `sync.Map`: `sync.Map` only wins for disjoint key sets with heavy
reads, and it costs you type safety and an obvious critical section everywhere else.

## sync primitives in detail

- Keep critical sections short and never hold a lock across I/O or a channel operation.
  A lock held over a network call converts one slow request into a stalled server.
- Do not copy a value containing a `sync.Mutex` — `go vet`'s `copylocks` check catches the
  common cases. Methods on a type with a mutex take a pointer receiver.
- `sync.RWMutex` cannot upgrade: taking `Lock` while holding `RLock` deadlocks.
- Guard the mutex and the data it protects together, and say so in a comment:
  `mu sync.Mutex // guards entries`.
- `sync.Pool` is for reusing large temporary buffers on a proven hot path. Reset the object
  before `Put`, never assume anything survives a GC cycle, and never pool something that
  holds a reference to request data.
- Prefer typed atomics (`var n atomic.Int64`; `n.Add(1)`) to the `atomic.AddInt64(&n, 1)`
  function API: the typed values cannot be copied by accident and need no alignment care.

## Pipelines

A pipeline is a chain of stages connected by channels. The rules that keep it from leaking:

- Each stage owns its output channel: it creates it, sends on it, and closes it when its
  input is exhausted (`defer close(out)` at the top of the stage's goroutine).
- Every stage selects on `ctx.Done()` for its sends, so an abandoned consumer does not
  strand the producers.
- A consumer that stops early must cancel the context; otherwise the upstream stages block
  forever on a send nobody will receive.

For a fan-in, run one `errgroup` goroutine per source writing into a shared output channel,
and close that channel in a single goroutine after `g.Wait()`.

Where the sequence is produced lazily and consumed in one place, an iterator
(`iter.Seq[T]`, Go 1.23+) is simpler than a channel: no goroutine, no close, no leak.
Reach for channels when the producer must genuinely run concurrently.

## The race detector

```bash
go test -race ./...            # in CI, on everything
go test -race -run TestX -count=10 ./pkg/...   # to reproduce something intermittent
go build -race -o /tmp/app ./cmd/app           # to run a real binary under it
```

The detector reports only races it observes, so a single run proving nothing is not
evidence; `-count=10` and realistic concurrency are. Expect roughly 2× slowdown and
substantially more memory, which is why it belongs in CI rather than in a latency test.

Reading a report: the first two stacks are the conflicting accesses (one is always a
write), and the trailing `Goroutine N (running) created at:` stack is where the goroutine
was launched. That launch site is usually where the fix goes.

Fix in this order: remove the sharing (give each worker its own slot), hand ownership over
a channel, then take a lock. Adding a mutex to keep shared mutable state alive is the last
resort, not the first move.

## Finding leaks

- In tests: `go.uber.org/goleak`, either `goleak.VerifyTestMain(m)` in `TestMain` for a
  whole package or `defer goleak.VerifyNone(t)` for one test.
- In a live process with `net/http/pprof` mounted:
  `curl 'http://host:6060/debug/pprof/goroutine?debug=2'` gives readable stacks, and the
  count in the header tells you whether it is growing.
- Go 1.27+ adds the `goroutineleak` profile, which reports goroutines blocked on
  primitives the GC proved unreachable — real leaks, not merely long-lived goroutines:
  `go tool pprof http://host:6060/debug/pprof/goroutineleak`. It cannot see leaks whose
  channel is still reachable from a global, so `goleak` remains the test-side tool.
- A `synctest` bubble is the deterministic way to assert an exit: cancel the context, call
  `synctest.Wait()`, and check the worker returned.

## Common mistakes

| Mistake | Fix |
|---|---|
| `go func()` with no exit condition | Give it a context or a closed input channel |
| `wg.Add(1)` inside the goroutine | `Add` before `go`, or use `wg.Go` (Go 1.25+) |
| Receiver closes the channel | Only the sender closes |
| Arbitrary buffer size to "avoid blocking" | 0, or a count you can name |
| `select` without `<-ctx.Done()` | Add the case; a blocked send is a leak |
| `time.After` in a loop | One `time.NewTimer` plus `Reset` |
| Hand-rolled semaphore channel | `g.SetLimit(n)` |
| Mutex held across an HTTP call | Copy what you need, unlock, then call |
| Results channel plus a collector goroutine | Pre-sized slice, one index per goroutine |
| Sending on a channel after `close` | Ownership: one sender, one close |
| `-race` only in a nightly job | Run it on every CI test job |

<!-- sources: samber-golang, spf13-go, cxuu-golang, go-effective-go, go-wiki-codereview, go-release-notes -->
