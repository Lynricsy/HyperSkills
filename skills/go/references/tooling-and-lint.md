# Tooling and linting

Verified against: Go 1.26 and Go 1.27, golangci-lint v2.

## Contents

- [The gate](#the-gate)
- [gofmt and goimports](#gofmt-and-goimports)
- [go vet](#go-vet)
- [golangci-lint](#golangci-lint)
- [Suppressing a finding](#suppressing-a-finding)
- [go fix and modernizers](#go-fix-and-modernizers)
- [gopls](#gopls)
- [Useful go subcommands](#useful-go-subcommands)
- [Build tags and cross-compilation](#build-tags-and-cross-compilation)
- [The toolchain is not the bug](#the-toolchain-is-not-the-bug)
- [Common mistakes](#common-mistakes)

## The gate

Every change ends with the same four commands, in this order, all clean:

```bash
gofmt -l .          # prints files that are not formatted; empty output is the pass
go vet ./...
golangci-lint run
go test -race ./...
```

Run them locally on the packages you touched and in CI on the whole tree. CI must run the
same `.golangci.yml` as the developer, or the two disagree at the worst moment.

## gofmt and goimports

`gofmt` is not configurable and not negotiable — every Go repository is formatted the same
way, which is why review comments about spacing do not exist in this ecosystem.

- `gofmt -l .` lists offenders; `gofmt -w .` fixes them.
- `goimports` is a superset that also adds and removes import lines and groups them
  (standard library first, then everything else, separated by a blank line). Editors run
  it on save.
- `gofmt -s` simplifies redundant syntax (`[]T{T{...}}` → `[]T{{...}}`); `golangci-lint`'s
  `gofmt` linter can enforce it.
- Do not fight the formatter with alignment comments. If a struct literal reads badly, the
  problem is the struct.

## go vet

`go vet` finds real bugs, not style. It is cheap, it has almost no false positives, and
`go test` already runs a subset of its analysers before running tests. The checks that
catch the most:

| Analyser | Catches |
|---|---|
| `printf` | Format verb that does not match the argument, including your own printf-wrappers |
| `copylocks` | Copying a value containing a `sync.Mutex` |
| `lostcancel` | A `context.WithCancel` whose `cancel` is never called |
| `loopclosure` | A loop variable captured by a goroutine (pre-1.22 semantics) |
| `httpresponse` | Using a response before checking the error, or a misplaced `defer Body.Close()` |
| `nilfunc`, `unmarshal`, `structtag` | Comparisons that are always false, non-pointer unmarshal targets, malformed tags |
| `stdversion` | Standard-library symbols newer than the `go` directive (run by `go test` since Go 1.27) |

`go vet -vettool=$(which shadow) ./...` adds variable shadowing if you want it; it is
noisy enough that most repositories leave it off.

## golangci-lint

`golangci-lint` aggregates the analysers into one parallel run with one configuration
file. A committed `.golangci.yml` is the source of truth:

```yaml
version: "2"

linters:
  enable:
    - errcheck      # unchecked errors — the single highest-value linter
    - govet
    - staticcheck   # correctness, simplification and style in one (absorbed gosimple and stylecheck in v2)
    - ineffassign   # assignments never read
    - unused        # unused code
    - bodyclose     # response bodies never closed
    - rowserrcheck  # sql.Rows.Err never checked
    - contextcheck  # a function that should propagate ctx but does not
    - errorlint     # err == sentinel and %v where %w belongs
    - copyloopvar   # redundant x := x copies
    - nilerr        # returning nil after checking err != nil
    - noctx         # HTTP request built without a context

  settings:
    errcheck:
      check-type-assertions: true

formatters:
  enable:
    - gofmt
    - goimports
```

Commands:

```bash
golangci-lint run              # what CI runs
golangci-lint run --fix        # apply the mechanical fixes
golangci-lint fmt              # v2's formatter entry point
golangci-lint linters          # what is enabled here and why
```

Adopting it on an existing codebase: enable the correctness linters first
(`errcheck`, `govet`, `staticcheck`, `bodyclose`, `errorlint`), fix in batches by linter so
each commit has one theme, and only then add the stylistic ones. Turning on fifty linters
at once produces a thousand findings nobody triages.

Note the version split: `golangci-lint` v2 merged `gosimple` and `stylecheck` into
`staticcheck`, moved `gofmt`/`goimports`/`gci`/`gofumpt` into a `formatters:` section, and
renamed `linters-settings` to `linters.settings`. A v1 config does not load unchanged;
`golangci-lint migrate` rewrites it (comments are not carried over).

## Suppressing a finding

Every suppression carries a reason on the same line:

```go
//nolint:errcheck // best-effort cleanup on a path that is already failing
defer f.Close()
```

- Narrow it to the specific linter, never bare `//nolint`.
- Set `nolintlint` to require both an explanation and that the directive is actually
  suppressing something; otherwise stale suppressions accumulate.
- Repository-wide exclusions belong in `.golangci.yml` (for example: `errcheck` off in
  `_test.go` files), so the decision is reviewable in one place instead of scattered
  through the source.

## go fix and modernizers

`go fix ./...` applies mechanical migrations to current idioms — typed atomics, embedded
literals, and the other modernizers shipped with the toolchain. Run it after raising the
`go` directive, review the diff, and commit it separately from behavioural changes.

The same analysers appear in `gopls` as "modernize" diagnostics with editor quick-fixes,
which is the more common way to meet them.

## gopls

`gopls` is the language server, and it is worth running headlessly when you want a
whole-module view without an editor:

```bash
go install golang.org/x/tools/gopls@latest
gopls check ./...            # type errors and diagnostics across the module
gopls references ./file.go:#offset
```

`gopls check` catches type errors in packages `go build` skips (for example files behind
build tags you are not currently compiling).

## Useful go subcommands

```bash
go doc net/http.Server          # local docs, no browser
go doc -all ./internal/store    # everything a package exports
go list ./...                   # every package; the basis of most scripts
go list -f '{{.GoFiles}}' .     # which files actually compile into this package
go list -deps -json ./cmd/app   # full dependency graph as JSON
go env GOFLAGS GOMODCACHE       # what the toolchain thinks it is doing
go clean -testcache             # force tests to re-run (they are cached on success)
go build -o /dev/null ./...     # compile everything without producing binaries
```

Test results are cached: an unchanged package with unchanged inputs prints `(cached)`.
That is correct behaviour, not a stale result. `-count=1` bypasses it when you are timing
something.

## Build tags and cross-compilation

```go
//go:build integration          // the current form; `// +build` is obsolete

//go:build linux && amd64
//go:build !windows
```

The directive goes above the package clause with a blank line after it. File-name suffixes
(`store_linux.go`, `store_windows.go`, `store_test.go`) apply implicitly.

```bash
GOOS=linux GOARCH=arm64 go build ./cmd/app     # cross-compile; no cgo needed for pure Go
CGO_ENABLED=0 go build -ldflags='-s -w' ./cmd/app   # static binary, smaller
go test -tags=integration ./...
```

`CGO_ENABLED=0` also drops the dependency on the host libc, which is what makes a
scratch-based container image possible. The race detector, however, requires cgo.

## The toolchain is not the bug

The Go tool is deterministic and the build cache is keyed by source content. `go run`
recompiles, `go build` is reproducible, and a changed file invalidates its cache entry
automatically.

When an error survives an edit, the explanation is one of these, in order of likelihood:

1. The edit did not fix the underlying logic.
2. The edit landed in the wrong file, function or package.
3. A second call site has the same bug and was not updated.
4. The error comes from a different code path than the one being edited.

Confirm which file is actually compiled with `go list -f '{{.GoFiles}}' .`, re-read the
error message (Go's messages are precise about position and type), and add a `t.Log` or
`fmt.Println` at the exact site to prove execution reaches it. Do not suggest
`go clean -cache`, a toolchain reinstall or an editor restart before exhausting the
code-level explanations.

## Common mistakes

| Mistake | Fix |
|---|---|
| Formatting debated in review | `gofmt`; there is nothing to debate |
| `go vet` skipped because tests run it | `go test` runs only a subset; run `go vet ./...` |
| Fifty linters enabled at once | Correctness linters first, then style |
| Bare `//nolint` | `//nolint:<linter> // <reason>` |
| v1 `.golangci.yml` on v2 | Migrate: `staticcheck` absorbed `gosimple`/`stylecheck`, formatters moved |
| CI and local using different lint configs | One committed `.golangci.yml` |
| `// +build` build tags | `//go:build` |
| `(cached)` treated as a stale result | It is correct; `-count=1` to force |
| Blaming the build cache for a persisting error | Check the four causes above |
| `-race` omitted because it is slow | Run it in CI on every test job |

<!-- sources: samber-golang, spf13-go, awesome-copilot-go, go-doc-diagnostics, go-release-notes -->
