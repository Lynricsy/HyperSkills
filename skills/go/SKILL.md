---
name: go
description: "Guides Go work end to end: idiomatic language use and useful zero values, interfaces and composition, goroutine lifetime, context cancellation, channels and sync primitives, errgroup, the race detector, error wrapping with %w and errors.Is/As/Join, module and workspace management, package layout, go test (table-driven, t.Parallel, t.Cleanup, synctest, fuzz, b.Loop benchmarks), pprof and runtime/trace profiling, go vet and golangci-lint, and the modern standard library (slices, maps, cmp, iter, math/rand/v2, log/slog, net/http timeouts and graceful shutdown). Use when writing, reviewing, debugging, profiling or modernising Go code, when reading go.mod to pick an approach, or when a goroutine leaks, a test is flaky, a data race appears or allocations dominate a profile. Do not use for cloud provider SDK usage, Kubernetes operators and controllers, or MCP server implementation."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# go

## Scope

Covers the Go language and its own toolchain: idioms and type design, interfaces and
composition, generics, the modern standard library, concurrency and the memory model,
error handling, package layout, modules and workspaces, `go test` in all its forms,
pprof/trace performance work, and `go vet` plus `golangci-lint`. Third-party packages
appear only where the standard library has no answer and the ecosystem has converged on
one: `golang.org/x/sync/errgroup`, `github.com/google/go-cmp/cmp`, `go.uber.org/goleak`.

Not covered: cloud provider SDKs (AWS, GCP, Azure), Kubernetes operators, controllers and
client-go, and MCP server implementation — no skill in this repository covers those yet,
so work from the vendor's own documentation. Web frameworks (Gin, Echo, Fiber) and ORMs
are out of scope by design; the `net/http` and `database/sql` guidance here is about the
standard library. Reviewing a diff, commit range or pull request is the `code-review`
skill's job. The test-first loop as a methodology belongs to the
`test-driven-development` skill; what is here is the Go testing API and its traps.
Diagnosing a reproducible local failure systematically is the `debugging` skill.

Paths below are relative to this skill's directory.

## Core rules

1. Read the `go` directive in `go.mod` before proposing anything version-gated. Every
   `(Go 1.x+)` marker below is a build-breaking constraint on a module pinned lower, and
   `go test` runs the `stdversion` vet check that catches it (Go 1.27+).
2. Every goroutine has a visible exit: a context, a closed channel, or a bounded loop.
   The garbage collector never reclaims a goroutine blocked on an unreachable channel, so
   a leak accumulates until the process dies.
3. Do not start goroutines in `init()` or in a library constructor. Expose `Start`/`Close`
   so the caller owns the lifetime and can wait for it.
4. Replace hand-rolled worker pools with `errgroup.WithContext` plus `g.SetLimit(n)`: it
   propagates the first error, cancels the siblings and caps concurrency in three lines.
   Where no error travels back, `wg.Go(func(){...})` (Go 1.25+) replaces the `Add`/`Done`
   pair.
5. Only the sender closes a channel, and sending hands over ownership — the sender must
   not touch the value afterwards. Closing from the receiver panics the next send.
6. A channel's buffer is 0, or a number you can name (the exact producer or worker count).
   An arbitrary buffer hides backpressure until the queue is the outage.
7. `context.Context` is the first parameter, named `ctx`, never a struct field. Every
   `select` that can block includes `case <-ctx.Done():`.
8. Wrap with `%w` and inspect with `errors.Is` / `errors.AsType[T](err)` (Go 1.26+;
   `errors.As(err, &target)` below that). `err == ErrX` and `err.(*T)` both stop matching
   the moment anything in the chain wraps the error, and that happens silently.
9. An error is either logged or returned, never both, and never discarded with `_`. Two
   handlers means two log lines for one failure and no owner.
10. Error strings are lowercase and unpunctuated: they get printed inside a larger
    sentence.
11. Design the zero value to be usable (`sync.Mutex`, `bytes.Buffer` are the models), and
    prefer `var t []T` for an empty slice. Reach for `[]T{}` or `make` only when the
    difference is observable — JSON encodes a nil slice as `null`, and a nil map panics on
    write.
12. The consumer declares the interface it needs, one or two methods wide; accept
    interfaces, return concrete types. An interface exported next to its only
    implementation is coupling with extra steps.
13. Keep a type's receivers consistent — all pointer or all value. Mixed receivers make
    the method set depend on how the value was obtained.
14. Name packages after the domain (`auth`, `billing`, `jobs`), one level deep. `utils`,
    `common`, `helpers` and layer names (`service`, `repository`, `controller`) create
    import cycles and tell a reader nothing. `internal/` exists to stop *other modules*
    importing code, not to model layers.
15. Check the standard library before adding a dependency, and prefer the current API:
    `slices`, `maps`, `cmp`, `iter`, `math/rand/v2`, typed `atomic.Int64`, `any`,
    `//go:build`, the `tool` directive over `tools.go`. Details in
    `references/stdlib-modern-apis.md`.
16. Introduce generics only when the same algorithm already exists for three or more
    types. A generic `Repository[T]` is a Java class hierarchy wearing Go syntax.
17. Table tests name every case and run it through `t.Run`; the failure message prints
    what was called, what came back and what was wanted. `t.Errorf("bad")` costs a
    debugging session.
18. In a parallel test, register cleanup with `t.Cleanup` or `t.TempDir` — never a `defer`
    in the parent. The parent function returns *before* its `t.Parallel()` subtests run,
    so the parent's `defer` fires first. [verified]
19. No `time.Sleep` in tests. Use `testing/synctest` (Go 1.25+) for anything involving
    timers, timeouts or context deadlines: its fake clock advances only when every
    goroutine in the bubble is blocked.
20. Profile before optimising, change one thing, measure again with `benchstat`. Write
    benchmarks as `for b.Loop()` (Go 1.24+), which keeps setup out of the timed region and
    stops the compiler eliding the call.
21. Never blame the Go toolchain. `go build` is deterministic and the build cache is keyed
    by source content; a persisting error means the edit was wrong, in the wrong file, or
    there is a second call site.
22. Finish every change with the gate: `gofmt -l .` empty, `go vet ./...` clean,
    `golangci-lint run` clean, `go test -race ./...` green.

## Workflows

### implement

- [ ] Read `go.mod`: module path, `go` directive, and which of `errgroup`, `go-cmp`,
      `testify`, `goleak` the project already depends on. Follow what is there.
- [ ] State the local contract before typing: inputs, zero-value behaviour, what is
      aliased, what mutates, which errors callers must distinguish, whether it is safe for
      concurrent use, and whether the identifier is exported (and therefore frozen).
- [ ] Pick the representation from that contract: value when copying is meaningful,
      pointer when identity, mutation or absence is part of the contract. Copy an incoming
      slice or map at the ownership boundary if you keep it.
- [ ] Write the concrete type first. Add an interface only when a second implementation or
      a test seam actually requires one, and declare it in the consuming package.
- [ ] Return errors with `%w` and enough context to locate the call; define a sentinel or
      a typed error only when a caller has to branch on it (`references/errors.md`).
- [ ] Add concurrency only when there is a measured reason. When you do, answer rule 2
      first, then reach for `errgroup` (`references/concurrency.md`).
- [ ] Document every exported identifier with a sentence starting with its name.
- [ ] Write the tests (see `add-tests`).
- [ ] **Gate:** `gofmt -l .` prints nothing, `go vet ./...` is clean, and
      `go test -race ./...` passes.

### add-tests

- [ ] Put the test in `foo_test.go` next to `foo.go`. Use `package foo_test` when you can
      exercise the exported API only; stay in `package foo` when the test genuinely needs
      unexported state.
- [ ] Write it table-driven with a named case per row, and assert observable behaviour —
      returned values, returned error identity via `errors.Is`, emitted output. A test
      pinned to internals fails on every refactor and proves nothing.
- [ ] Compare structs with `cmp.Diff(want, got)` and print the diff, not
      `reflect.DeepEqual`.
- [ ] Add `t.Parallel()` only when the case owns its state; then apply rules 18 and 19.
- [ ] Cover the error paths and one boundary case per input dimension. For parsers and
      decoders add `FuzzXxx` with the known-tricky inputs seeded.
- [ ] Packages that spawn goroutines get `goleak.VerifyTestMain(m)` in `TestMain`.
- [ ] **Gate:** `go test -race -count=2 ./...` passes, and the new test fails when you
      break the behaviour it claims to cover.

### fix-race-or-leak

- [ ] Reproduce under the detector: `go test -race -run <Test> -count=10 ./...`. The race
      detector only reports races it observes, so make the suspect path run many times.
- [ ] Read the report top down: the two stacks are the conflicting accesses and the third
      is where the goroutine was started. That third stack is usually the actual bug.
- [ ] Fix by removing the sharing first (give each worker its own slot or value), by a
      channel handoff second, and by a mutex only when shared mutable state is genuinely
      required. Adding a lock to keep dead shared state alive is not a fix.
- [ ] For a suspected leak, count first: `runtime.NumGoroutine()` around the operation, or
      `curl <host>/debug/pprof/goroutine?debug=2` for a live process. On Go 1.27+ the
      `goroutineleak` profile names goroutines blocked on unreachable primitives directly.
- [ ] Pin the fix with a regression test: `defer goleak.VerifyNone(t)`, or a `synctest`
      bubble that asserts the worker exits when the context is cancelled.
- [ ] **Gate:** `go test -race -count=10` on the affected package is green and the
      goroutine count returns to its pre-operation value.

### profile-hot-path

- [ ] Rule out the world outside the process first: if most of the latency is a database
      round trip or an upstream call, allocation work changes nothing.
- [ ] Get a baseline benchmark with `for b.Loop()` and
      `go test -run '^$' -bench . -benchmem -count=10 > old.txt`.
- [ ] Collect the profile that matches the symptom — CPU, `-memprofile` for allocations,
      block/mutex for contention, `runtime/trace` for scheduling and GC
      (`references/performance-profiling.md`).
- [ ] Read `top -cum` before `top`: a high `cum` with a low `flat` is an orchestrator, so
      drill into its children with `list <func>`. `runtime.mallocgc`, `runtime.growslice`
      and `runtime.mapassign` at the top are symptoms of allocation in your code, not the
      cause.
- [ ] Change one thing. Re-run the benchmark into `new.txt` and judge it with
      `benchstat old.txt new.txt` — a single run is noise.
- [ ] Leave the reason in a comment next to the optimisation, with the delta. Otherwise
      the next reader reverts it as pointless complexity.
- [ ] **Gate:** `benchstat` shows a statistically significant improvement (its `p` column),
      and `go test -race ./...` is still green.

### upgrade-modules

- [ ] `go list -m -u all` to see what moved, and read the changelog of anything with a
      major bump before touching `go.mod`.
- [ ] Upgrade within existing constraints first (`go get -u ./... && go mod tidy`), then
      majors one module per commit so a regression has one suspect.
- [ ] Run `govulncheck ./...` — it reports only vulnerabilities your code actually reaches,
      so a finding is real work.
- [ ] Track dev tools with `go get -tool <pkg>` and run them via `go tool <name>`
      (Go 1.24+). Delete any `tools.go` blank-import file you find.
- [ ] Keep `go.sum` committed; `go mod verify` is what detects a tampered module cache.
- [ ] Use a `go.work` file for local multi-module development and never commit a `replace`
      directive that points at a developer's disk.
- [ ] **Gate:** `go mod tidy` leaves the tree clean, `govulncheck ./...` reports nothing
      reachable, and `go test -race ./...` passes on the new graph.

### review

Judging existing Go code without a base ref to diff against — a file, a package, a change
someone asks you to look over. Report using the Output format below.

- [ ] Read `go.mod` first: the `go` directive decides which of the rules below even apply,
      and the dependency list tells you which conventions the package already follows.
- [ ] Run the tooling before reading, and skip anything it already reports:
      `gofmt -l .`, `go vet ./...`, `golangci-lint run` if the repository configures it.
- [ ] Read the tests first. A missing test for a changed behaviour, or an assertion that
      only replays a stub, is the most expensive thing to miss.
- [ ] Walk the Core rules in order; they are ordered by how often each one is the actual
      defect. Concurrency and error handling produce the findings that matter.
- [ ] Reproduce anything you claim: `go test -race -count=10` for a suspected race, a
      goroutine count around the operation for a suspected leak, a benchmark for a
      performance claim. A finding you did not verify does not go in the report.
- [ ] For every leak or race you report, name the regression guard that keeps it fixed —
      `goleak.VerifyNone(t)` in the package's tests, a `synctest` bubble that asserts the
      exit, or the `goroutineleak` profile in production. A one-off script you delete
      leaves nothing behind.
- [ ] Check the boundary the code presents to callers: exported surface, sentinel and
      typed errors, whether `ctx` is threaded through, whether timeouts exist on every
      outbound call.
- [ ] **Gate:** every finding carries `path:line`, a one-line reason, a concrete fix and a
      severity, and the report ends with a verdict.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Zero values, receivers, interfaces, generics, control flow, naming | Designing a type or an API, or judging idiom in existing code | `references/language-idioms.md` |
| `slices`/`maps`/`cmp`/`iter`, `math/rand/v2`, `log/slog`, `net/http` server and client, `encoding/json` | Reaching for a helper, writing an HTTP server or client, or modernising older code | `references/stdlib-modern-apis.md` |
| Goroutine lifetime, channels, `select`, sync primitives, `errgroup`, pipelines, race detector | Writing or reviewing concurrent code, or chasing a leak or a race | `references/concurrency.md` |
| Wrapping, sentinels, typed errors, `errors.Join`, panic/recover, error logging | Creating, wrapping, inspecting or logging errors | `references/errors.md` |
| Table tests, parallel traps, `synctest`, fuzzing, benchmarks, golden files, `httptest` | Writing, fixing or reviewing tests | `references/testing.md` |
| pprof, `runtime/trace`, `benchstat`, allocation reduction, GC tuning | Something is slow, allocating too much, or contended | `references/performance-profiling.md` |
| Package boundaries, `internal/`, `go.mod`, workspaces, versioning, `govulncheck` | Starting a project, moving code between packages, or upgrading dependencies | `references/modules-and-layout.md` |
| `gofmt`, `go vet`, `golangci-lint`, `go fix` modernizers, `gopls`, build cache | Setting up or interpreting tooling, or suppressing a lint warning | `references/tooling-and-lint.md` |

## Output format

When reporting on existing code rather than editing it, group findings by file, order them
by severity within a file, and skip preamble:

```
internal/fetch/fetcher.go
  L31 blocking - package-level `cache` map written from N worker goroutines; `go test -race`
       reports it and production hits a fatal `concurrent map writes`.
       fix: drop the map, or guard it with a mutex owned by the type.
  L52 blocking - `time.Sleep(100ms)` used as synchronization; the collector goroutine also
       leaks because `out` is never closed.
       fix: errgroup.WithContext + g.SetLimit(workers), collect after g.Wait().
  L57 important - `http.Get` uses http.DefaultClient, which has no timeout.
       fix: http.NewRequestWithContext with a client that sets one.

internal/fetch/parse.go
  ✓ pass
```

Severities: `blocking` (data race, leak, silently dropped error, wrong behaviour),
`important` (missing timeout, unbounded growth, API that will hurt callers), `minor`
(naming, dead code, an idiom the linter would catch). End with one line: ship, ship after
blocking fixes, or rework. Name the commands you actually ran; a finding you did not verify
does not go in the report.

## Environment

Go toolchain on `PATH`. Commands used by the workflows:

```bash
go vet ./...                       # always available; go test runs a subset automatically
go test -race ./...                # the race detector needs cgo and a supported platform
go test -run '^$' -bench . -benchmem -count=10
gofmt -l .                         # non-empty output is a failure
go mod tidy && go mod verify
```

Installed on demand, each one line:

```bash
go get -tool golang.org/x/vuln/cmd/govulncheck   # then: go tool govulncheck ./...
go get -tool golang.org/x/perf/cmd/benchstat     # then: go tool benchstat old.txt new.txt
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
```

`golangci-lint` is the one tool worth a project config: a committed `.golangci.yml` is the
source of truth for which linters run, and CI must run the same file. `-race` roughly
doubles runtime and increases memory use, so run it on the package under change locally and
on the whole tree in CI.
