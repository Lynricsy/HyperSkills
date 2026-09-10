# Testing

Verified against: Go 1.26 and Go 1.27.

## Contents

- [File and package layout](#file-and-package-layout)
- [Table-driven tests](#table-driven-tests)
- [Failure messages](#failure-messages)
- [Comparing values](#comparing-values)
- [Cleanup, temp dirs and context](#cleanup-temp-dirs-and-context)
- [t.Parallel and its traps](#tparallel-and-its-traps)
- [testing/synctest](#testingsynctest)
- [Test doubles](#test-doubles)
- [httptest](#httptest)
- [Golden files](#golden-files)
- [Fuzzing](#fuzzing)
- [Benchmarks](#benchmarks)
- [Goroutine leaks in tests](#goroutine-leaks-in-tests)
- [Integration tests and coverage](#integration-tests-and-coverage)
- [Common mistakes](#common-mistakes)

## File and package layout

`foo.go` is tested by `foo_test.go` in the same directory. Name the test file after the
source file, not after a function: every tool and every reviewer resolves tests by source
file.

- `package foo` — white-box. Only when the test genuinely needs unexported state.
- `package foo_test` — black-box, compiled as a separate package. The default: it can only
  use the exported API, which is exactly what the test should be pinned to, and it cannot
  create an import cycle with a helper package.

Test names: `TestParse`, `TestStore_Rename` for a method, `BenchmarkParse`, `FuzzParse`,
`ExampleParse`. An `Example` with an `// Output:` comment is compiled, run and diffed by
`go test`, so it is documentation that cannot rot.

## Table-driven tests

```go
func TestParsePort(t *testing.T) {
    tests := []struct {
        name    string
        in      string
        want    int
        wantErr error
    }{
        {name: "plain", in: "8080", want: 8080},
        {name: "leading zero", in: "0080", want: 80},
        {name: "empty", in: "", wantErr: ErrEmptyPort},
        {name: "not a number", in: "http", wantErr: strconv.ErrSyntax},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParsePort(tt.in)
            if !errors.Is(err, tt.wantErr) {
                t.Fatalf("ParsePort(%q) error = %v, want %v", tt.in, err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("ParsePort(%q) = %d, want %d", tt.in, got, tt.want)
            }
        })
    }
}
```

- Every row is named, and the name goes to `t.Run` so `-run 'TestParsePort/empty'` works
  and a failure says which case broke.
- Compare error *identity* with `errors.Is`, not `err != nil`. A test that only checks
  "some error" passes when the code returns the wrong one.
- `t.Fatalf` when continuing would panic or produce noise; `t.Errorf` when the remaining
  assertions still carry information.

## Failure messages

The Go convention is `f(input) = got, want want`. The message must let a reader fix the
code without opening the test:

```go
t.Errorf("Normalize(%q) = %q, want %q", in, got, want)   // good
t.Errorf("bad")                                          // costs a debugging session
t.Errorf("expected %v", want)                            // omits what actually happened
```

## Comparing values

Use `github.com/google/go-cmp/cmp` for structs, maps and slices:

```go
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("Load() mismatch (-want +got):\n%s", diff)
}
```

`cmp.Diff` prints the differing fields; `reflect.DeepEqual` prints two whole structs and
lets you find it. Argument order is `(want, got)` so the `-want +got` legend is truthful.
`cmp` panics on unexported fields by design — pass `cmpopts.IgnoreUnexported(T{})` or, if
that keeps happening, the test is reaching into internals it should not see.

Assertion libraries: if the repository already uses `testify`, follow it. Do not introduce
it into a repository that does not. When you do use it, build `assert.New(t)` *inside* each
subtest — an instance built in the parent captures the parent's `*testing.T`, so a subtest
failure is reported against the parent while the subtest still prints `--- PASS`.

## Cleanup, temp dirs and context

- `t.TempDir()` gives a per-test directory removed after the test *and all its subtests*
  finish. Prefer it to `os.MkdirTemp` plus manual removal.
- `t.Cleanup(fn)` registers teardown on the test node itself; it runs after parallel
  subtests, unlike a `defer` in the enclosing function.
- `t.Context()` (Go 1.24+) is a context cancelled just before cleanups run — use it instead
  of `context.Background()` so a hung call fails the test rather than the whole run.
- `t.Chdir(dir)` (Go 1.24+) changes the working directory and restores it. It is
  incompatible with `t.Parallel()` in the same test, and `go test` will say so.
- `t.Setenv` similarly forbids parallelism in that test.

## t.Parallel and its traps

`t.Parallel()` pauses the subtest and resumes it after the *parent test function has
returned*. Two consequences:

```go
func TestCache(t *testing.T) {
    dir, _ := os.MkdirTemp("", "cache")
    defer os.RemoveAll(dir)          // runs BEFORE any parallel subtest body
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel()
            useFilesIn(dir)          // directory is already gone
        })
    }
}
```

Verified on Go 1.26: the parent's `defer` prints first, then the subtest bodies. The fix is
`t.TempDir()`, or `t.Cleanup` registered on the parent — both wait for the subtests.

The second trap is shared mutable state. Parallel subtests that write to one value shared
by the table need either their own instance per case or no `t.Parallel()` at all. Parallel
subtests over three map operations buy nothing and cost a data race; `go test -race`
reports it.

Loop variables are per-iteration since Go 1.22, so the old `tc := tc` line is dead weight
in a module on 1.22 or later.

## testing/synctest

`testing/synctest` (Go 1.25+) runs a function in a bubble with a fake clock. Time advances
only when every goroutine in the bubble is blocked, so timeouts, tickers and context
deadlines become instant and deterministic:

```go
func TestExpiry(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        c := New()
        c.PutTTL("k", "v", 50*time.Millisecond)

        time.Sleep(200 * time.Millisecond) // instant: the fake clock jumps
        synctest.Wait()                    // let the expiry goroutine run

        if got := c.Get("k"); got != "" {
            t.Errorf("Get(k) = %q after TTL, want empty", got)
        }
    })
}
```

- `synctest.Wait()` blocks until every other goroutine in the bubble is durably blocked.
  Call it before asserting on work another goroutine performs.
- The bubble must be self-contained: no real network, no external processes, no goroutines
  started outside it.
- This replaces both `time.Sleep` padding and deadline polling loops. A polling loop with a
  two-second budget is still a wall-clock test — it is slow on a loaded runner and it
  cannot prove the timer fired at the right moment.

Below Go 1.25, inject a clock (`type clock interface{ Now() time.Time; After(time.Duration) <-chan time.Time }`)
and substitute a fake in the test.

## Test doubles

Prefer a hand-written fake implementing the small consumer-defined interface. It is a
dozen lines, it is readable in the test file, and it does not need code generation:

```go
type stubStore struct {
    users map[string]*User
    err   error
}

func (s *stubStore) User(ctx context.Context, id string) (*User, error) {
    if s.err != nil {
        return nil, s.err
    }
    u, ok := s.users[id]
    if !ok {
        return nil, ErrNotFound
    }
    return u, nil
}
```

Mock at the boundary you own (the interface the code under test consumes), never the type
under test. A test that asserts the number of calls to a mock is testing the
implementation; assert the observable result instead. Generated mocks earn their keep only
for interfaces with many methods that change often.

## httptest

- Server side: `httptest.NewRequest` plus `httptest.NewRecorder`, then assert on
  `rec.Code`, `rec.Header()` and the decoded body. No socket involved.
- Client side: `httptest.NewServer(http.HandlerFunc(...))` and point the client at
  `srv.URL`; `defer srv.Close()`. Assert on what the handler *received* — method, path,
  headers, body — otherwise the test only replays your own stub.
- For TLS behaviour use `httptest.NewTLSServer` and `srv.Client()`, which is already
  configured to trust it.

## Fuzzing

Parsers, decoders, and anything that consumes untrusted bytes get a fuzz target:

```go
func FuzzParseConfig(f *testing.F) {
    f.Add("port=8080\n")          // seeds: the known-interesting inputs
    f.Add("")
    f.Fuzz(func(t *testing.T, in string) {
        cfg, err := ParseConfig(in)
        if err != nil {
            return                // rejecting bad input is correct behaviour
        }
        out, err := cfg.Marshal() // round-trip is the property worth asserting
        if err != nil {
            t.Fatalf("Marshal after successful parse: %v", err)
        }
        if _, err := ParseConfig(out); err != nil {
            t.Fatalf("re-parsing own output %q: %v", out, err)
        }
    })
}
```

`go test -fuzz FuzzParseConfig -fuzztime 60s` runs the campaign; plain `go test` replays
the seed corpus and everything under `testdata/fuzz/`. Failing inputs are written there —
commit them, they are regression tests.

## Benchmarks

```go
func BenchmarkParse(b *testing.B) {
    data := loadFixture(b)   // setup is not timed: b.Loop() excludes it
    for b.Loop() {
        if _, err := Parse(data); err != nil {
            b.Fatal(err)
        }
    }
}
```

`b.Loop()` (Go 1.24+) replaces `for i := 0; i < b.N; i++`. It keeps setup outside the timed
region — so `b.ResetTimer` becomes unnecessary — and it stops the compiler from optimising
away a call whose result is discarded, which the old form needed a package-level sink for.

```bash
go test -run '^$' -bench . -benchmem -count=10 > old.txt
# change one thing
go test -run '^$' -bench . -benchmem -count=10 > new.txt
go tool benchstat old.txt new.txt
```

`-count=10` and `benchstat` are not optional: single-run numbers differ by more than most
optimisations. Read the `p` column before claiming an improvement.

## Goroutine leaks in tests

```go
func TestMain(m *testing.M) { goleak.VerifyTestMain(m) }   // whole package
func TestWorker(t *testing.T) { defer goleak.VerifyNone(t) } // one test
```

`goleak` fails the run when goroutines outlive it. Some libraries keep background
goroutines legitimately; exclude those precisely with `goleak.IgnoreTopFunction(...)`
rather than dropping the check.

## Integration tests and coverage

- Guard tests that need a database, a broker or the network with `//go:build integration`
  and run them as a separate CI job (`go test -tags=integration ./...`). Unit tests must
  stay runnable offline in seconds.
- `go test -cover ./...` for a number; `-coverprofile=cover.out` plus
  `go tool cover -html=cover.out` to see which branches are missing. Chase the uncovered
  error paths, not the percentage: a coverage target produces tests that execute code
  without asserting on it.

## Common mistakes

| Mistake | Fix |
|---|---|
| `defer` cleanup in a parent with parallel subtests | `t.TempDir()` / `t.Cleanup` |
| `time.Sleep` to wait for a goroutine | `synctest`, or a channel the test receives from |
| Polling with a deadline instead of a fake clock | `synctest.Test` + `synctest.Wait` |
| `for i := 0; i < b.N; i++` | `for b.Loop()` (Go 1.24+) |
| `b.ResetTimer` after setup | Unnecessary with `b.Loop()` |
| `t.Errorf("bad")` | Print call, got and want |
| `err != nil` as the error assertion | `errors.Is(err, tt.wantErr)` |
| `reflect.DeepEqual` on structs | `cmp.Diff(want, got)` |
| `assert.New(t)` in the parent, used in subtests | Build it inside each subtest |
| Asserting a mock's call count | Assert the observable result |
| One benchmark run compared by eye | `-count=10` and `benchstat` |
| Tests that depend on execution order | Each test builds its own state |

<!-- sources: samber-golang, spf13-go, ashwin-go, go-wiki-testcomments, go-release-notes -->
