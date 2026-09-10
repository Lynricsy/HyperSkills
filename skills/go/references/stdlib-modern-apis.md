# Modern standard library

Verified against: Go 1.26 and Go 1.27. Each entry names the release that introduced it;
check the `go` directive in `go.mod` before using one.

## Contents

- [slices](#slices)
- [maps](#maps)
- [cmp](#cmp)
- [Iterators](#iterators)
- [math/rand/v2 and crypto/rand](#mathrandv2-and-cryptorand)
- [encoding/json](#encodingjson)
- [sync/atomic typed values](#syncatomic-typed-values)
- [log/slog](#logslog)
- [net/http servers](#nethttp-servers)
- [net/http clients](#nethttp-clients)
- [Syntax and build files](#syntax-and-build-files)
- [Old patterns](#old-patterns)

## slices

`slices` (Go 1.21) removes most hand-written loops and every `sort.Slice` closure:

```go
slices.Sort(s)                                   // any cmp.Ordered element type
slices.SortFunc(s, func(a, b User) int { return cmp.Compare(a.Name, b.Name) })
slices.SortStableFunc(s, less)
slices.Contains(s, v)
slices.Index(s, v)                               // -1 when absent
slices.IndexFunc(s, pred)
slices.BinarySearch(s, v)                        // (index, found) on a sorted slice
slices.Equal(a, b)
slices.Clone(s)                                  // shallow copy; use at ownership boundaries
slices.Clip(s)                                   // cap = len, so append reallocates
slices.Compact(s)                                // drops consecutive duplicates in place
slices.Delete(s, i, j)
slices.Insert(s, i, vs...)
slices.Concat(a, b, c)                           // Go 1.22
slices.Reverse(s)
slices.Max(s), slices.Min(s)
```

`slices.SortFunc` takes a three-way comparison returning a negative number, zero or a
positive number — not the `less bool` that `sort.Slice` used. `cmp.Compare` is the usual
body.

## maps

`maps` (Go 1.21; the iterator forms in Go 1.23):

```go
maps.Clone(m)
maps.Copy(dst, src)
maps.Equal(a, b)
maps.DeleteFunc(m, func(k K, v V) bool { return v.Expired() })
maps.Keys(m)                                     // iter.Seq[K], not a slice
maps.Values(m)

keys := slices.Sorted(maps.Keys(m))              // the deterministic-iteration idiom
```

Map iteration order is randomised on purpose. Any output that must be stable sorts the
keys first.

## cmp

```go
cmp.Compare(a, b)          // -1, 0, +1 for any cmp.Ordered type
cmp.Or(a, b, c)            // first non-zero argument — default-value chains
cmp.Less(a, b)
min(a, b), max(a, b)       // builtins since Go 1.21
```

Note the two `cmp`s: the standard library `cmp` package here, and
`github.com/google/go-cmp/cmp` used in tests. They are unrelated.

## Iterators

`iter` and range-over-func (Go 1.23) let an API expose a sequence without allocating a
slice or running a goroutine:

```go
func (idx *Index) All() iter.Seq[*Person] {
    return func(yield func(*Person) bool) {
        for _, p := range idx.people {
            if !yield(p) {
                return          // the caller broke out; stop and clean up
            }
        }
    }
}

for p := range idx.All() { ... }
```

`iter.Seq2[K, V]` is the two-value form. Bridges: `slices.Collect(seq)`,
`slices.Sorted(seq)`, `slices.Values(s)`, `slices.All(s)` (index/value), `maps.All(m)`.

Return an iterator for large or lazily produced sequences and a slice for small fixed
results. Never invent a `Next()`/`HasNext()` type.

## math/rand/v2 and crypto/rand

`math/rand/v2` (Go 1.22) is auto-seeded and has the cleaner API; the v1 package is frozen:

```go
rand.IntN(100)                 // was rand.Intn
rand.N(10 * time.Second)       // generic: any integer-like type, including durations
rand.Perm(n)
```

Never use either `math/rand` for anything security-relevant — tokens, keys, session ids,
password resets. `crypto/rand.Text()` returns a securely generated random string, and
`crypto/rand.Read` fills bytes.

## encoding/json

- `omitzero` (Go 1.24) omits any zero value, including `time.Time{}` and zero structs,
  which `omitempty` never handled: `StartedAt time.Time \`json:"started_at,omitzero"\``.
- `omitempty` still means "empty" in the v1 sense (false, 0, "", nil, empty slice/map) —
  keep it where that is what you want.
- Decode into a typed struct, not `map[string]any`, so field names and types are checked
  once at the boundary.
- Use `json.Decoder` with `DisallowUnknownFields()` for configuration you own, and stream
  large bodies with `json.NewDecoder(r).Decode(&v)` rather than `io.ReadAll` first.
- Go 1.27 adds `encoding/json/v2` and `encoding/json/jsontext`, and re-implements v1 on
  top of v2. v1 stays supported and its behaviour is preserved, so migration is optional;
  v2's stricter defaults (rejects invalid UTF-8, rejects duplicate object names) are the
  reason to move a parser that handles untrusted input.

## sync/atomic typed values

```go
var n atomic.Int64          // not: var n int64 + atomic.AddInt64(&n, 1)
n.Add(1)
v := n.Load()

var closed atomic.Bool
var cur atomic.Pointer[Config]
```

Typed atomics (Go 1.19) cannot be copied by accident, need no alignment care on 32-bit
platforms, and read as ordinary method calls. `atomic.Pointer[T]` plus a whole-value swap
is the standard way to hot-reload a config without a lock.

## log/slog

```go
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
logger.Info("server started", "addr", addr)
logger.Error("saving user", "err", err, "user_id", id)

reqLog := logger.With("request_id", rid)         // derived logger, fields carried along
reqLog.Debug("cache miss", "key", key)
```

Pass a `*slog.Logger` as a dependency; a package-level logger outside `main` cannot be
substituted in a test. Group related fields with `slog.Group("http", ...)`. Do not log at
`Error` for anything you also return — the boundary logs it once.

## net/http servers

Since Go 1.22 the standard `ServeMux` does method and path-parameter routing, which
removes the usual reason to import a router:

```go
mux := http.NewServeMux()
mux.HandleFunc("GET /users", listUsers)
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("GET /users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    ...
})
mux.HandleFunc("GET /files/{path...}", serveFile)   // trailing wildcard
```

`http.ListenAndServe(addr, mux)` ships **no timeouts**: one slow client can hold a
connection open indefinitely. A production server always sets them:

```go
srv := &http.Server{
    Addr:              ":8080",
    Handler:           mux,
    ReadHeaderTimeout: 5 * time.Second,   // slow-loris protection
    ReadTimeout:       10 * time.Second,
    WriteTimeout:      30 * time.Second,
    IdleTimeout:       120 * time.Second,
}
```

Graceful shutdown drains in-flight requests instead of dropping them:

```go
func run(ctx context.Context, srv *http.Server) error {
    ctx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
    defer stop()

    errCh := make(chan error, 1)
    go func() { errCh <- srv.ListenAndServe() }()

    select {
    case err := <-errCh:
        return err                                   // failed to start
    case <-ctx.Done():
        shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        defer cancel()
        return srv.Shutdown(shutdownCtx)             // fresh context: ctx is already cancelled
    }
}
```

Long-lived connections (SSE, WebSocket) must watch `r.Context()` or they hold shutdown
until the drain deadline expires.

Middleware is a function; no framework required:

```go
func withRequestLog(l *slog.Logger, next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        l.Info("request", "method", r.Method, "path", r.URL.Path, "dur", time.Since(start))
    })
}

handler := withRequestLog(logger, withAuth(mux))   // outermost runs first
```

Reach for a third-party router only for named route generation or regex constraints.
Middleware alone does not justify one.

## net/http clients

- `http.DefaultClient` has no timeout either. Build a client with one, reuse it, and never
  construct a client per request — that discards connection pooling and TLS session reuse.
- Always `http.NewRequestWithContext(ctx, ...)`, so a cancelled caller cancels the call.
- Keep a client wrapper stateless: base URL, `*http.Client`, credentials, default headers.
  Never store an `*http.Request` on it — build one per call, or the second concurrent
  caller sends the first one's body.
- `defer resp.Body.Close()` on every non-error response, and read the body to completion
  (or `io.Copy(io.Discard, resp.Body)`) if you want the connection returned to the pool.
- Cap what you read from an untrusted peer: `io.ReadAll(io.LimitReader(resp.Body, max))`.
- Check `resp.StatusCode` explicitly. A 500 with an HTML error page is not an error from
  `Do`'s point of view.

## Syntax and build files

| Old | Current | Since |
|---|---|---|
| `interface{}` | `any` | 1.18 |
| `// +build linux` | `//go:build linux` | 1.17 (required) |
| `for i := 0; i < 10; i++` | `for i := range 10` | 1.22 |
| `tools.go` with blank imports | `go get -tool <pkg>`, `go tool <name>` | 1.24 |
| `ioutil.ReadFile` / `ReadAll` | `os.ReadFile` / `io.ReadAll` | 1.16 |
| `sort.Slice` | `slices.SortFunc` | 1.21 |
| `atomic.AddInt64(&n, 1)` | `var n atomic.Int64; n.Add(1)` | 1.19 |
| `rand.Intn` (v1) | `rand/v2` `rand.IntN` | 1.22 |
| `github.com/pkg/errors` | `fmt.Errorf("%w")`, `errors.Is/As` | 1.13 |
| `go.uber.org/multierr` | `errors.Join` | 1.20 |

`go fix ./...` applies many of these mechanically; `gopls` surfaces them as "modernize"
diagnostics in an editor.

## Old patterns

<details>
<summary>Forms that were correct on earlier releases and should not be reintroduced</summary>

- `x := x` inside a loop before spawning a goroutine. Loop variables are per-iteration
  since Go 1.22, so the copy is noise.
- `b.ResetTimer()` after benchmark setup. `b.Loop()` (Go 1.24) already excludes setup.
- A package-level `var sink T` to stop the compiler eliding a benchmarked call. `b.Loop()`
  keeps the call.
- `rand.Seed(time.Now().UnixNano())`. `math/rand/v2` is auto-seeded and v1's `Seed` is
  deprecated.
- `gorilla/mux` or `chi` imported only for method and path-parameter routing. The standard
  `ServeMux` has done both since Go 1.22.
- A hand-rolled `multierror` type. `errors.Join` covers it.

</details>

<!-- sources: spf13-go, samber-golang, awesome-copilot-go, go-effective-go, go-release-notes -->
