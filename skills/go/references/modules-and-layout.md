# Modules and package layout

Verified against: Go 1.26 and Go 1.27.

## Contents

- [Start flat](#start-flat)
- [Domain packages](#domain-packages)
- [internal/](#internal)
- [Where main lives](#where-main-lives)
- [go.mod and go.sum](#gomod-and-gosum)
- [Adding a dependency](#adding-a-dependency)
- [Upgrading](#upgrading)
- [Dev tools](#dev-tools)
- [Workspaces](#workspaces)
- [Publishing a module](#publishing-a-module)
- [Embedding files](#embedding-files)
- [Common mistakes](#common-mistakes)

## Start flat

A tool or a service starts as one package in the module root:

```
myproject/
├── main.go
├── server.go
├── config.go
├── parser.go
├── parser_test.go
├── go.mod
└── go.sum
```

Nothing is gained by splitting a 500-line program into six directories. A package exists
to give a name to a boundary; without a boundary it is just a longer import path. Split
when a domain has become independently describable and independently testable, not because
a template said so.

## Domain packages

When the program does grow, name packages after the domain they own, one level deep:

```
myservice/
├── main.go        # wires everything; no business logic
├── config/        # config struct, env loading
├── auth/          # identity, sessions, middleware
├── db/            # store client and its queries
├── billing/       # payment provider, credit ledger
├── jobs/          # job lifecycle, queue dispatch, worker handler
└── web/           # HTTP handlers and the templates they render
```

The test for a new package: can you describe what it owns in one sentence, and does it not
need to know about its siblings? If yes, it earns a package.

- Packages do not import each other sideways. An import cycle means the boundary is in the
  wrong place; `main` is the wiring point.
- Sub-concerns that always travel together stay in one package. Job creation and the
  worker that runs jobs share a lifecycle, so both live in `jobs/`.
- Never create `utils`, `common`, `helpers`, `models` or `types`. They accumulate whatever
  had no home and are imported by everything, which makes them impossible to change.
- Never name a package after a layer — `service`, `repository`, `controller`, `domain`.
  Layer-named packages produce import cycles, force interface proliferation, and tell a
  reader nothing about what the code does. Clean Architecture folder trees are the single
  most common over-structuring mistake in Go repositories.

## internal/

`internal/` is a compiler rule, not an architecture: a package under `internal/` can only
be imported by code rooted at the parent of that `internal/` directory.

- **Application (a binary):** nobody can import your `main` module anyway, so `internal/`
  adds a path segment and no protection. Skip it unless the repository also publishes a
  library.
- **Library:** use it for the subsystems you must share between your own packages but
  refuse to freeze as public API.

`pkg/` has no meaning to the toolchain. It is a convention some repositories use to mark
"importable"; it buys nothing over the module root and adds a segment to every import.

## Where main lives

- One binary: `main.go` in the module root.
- Several binaries: `cmd/<name>/main.go` per binary, each one a thin wiring layer over
  packages that hold the logic.
- `main` parses flags and environment, builds dependencies, and calls a `run(ctx) error`
  that everything else lives in. That makes the program testable and gives you one place
  to handle the exit code:

```go
func main() {
    if err := run(context.Background()); err != nil {
        fmt.Fprintln(os.Stderr, "app:", err)
        os.Exit(1)
    }
}
```

Avoid `log.Fatal` outside `main`: it calls `os.Exit`, so deferred cleanups never run.

## go.mod and go.sum

```
module github.com/acme/widget      // must match the repository URL, or `go get` cannot find it

go 1.25                            // the language version this module is written against

require (
    golang.org/x/sync v0.10.0
)
```

- The `go` directive is a language-version contract, not a minimum toolchain: it decides
  which features compile and which vet checks apply. Raise it deliberately, in its own
  commit, and only when you use something that needs it. On Go 1.27 `go test` runs the
  `stdversion` vet check, which reports standard-library symbols newer than this line.
- A separate `toolchain` line pins the toolchain used to build; leave it to the `go`
  command rather than editing it by hand.
- `go.sum` is committed. It holds the checksum of every module version in the graph, and
  `go mod verify` is what detects a tampered module cache or proxy.
- `go mod tidy` before every commit that touches dependencies. On modules declaring
  `go 1.27` it also merges duplicate `require` blocks into the standard two.

## Adding a dependency

Before `go get`, answer three questions, and put the answers in the commit message:

1. Does the standard library already do this? Since Go 1.21 a surprising amount moved in —
   `slices`, `maps`, `cmp`, `log/slog`, `errors.Join`, `math/rand/v2`, routing in
   `net/http`.
2. Is it maintained, and is the licence compatible?
3. What does it pull in transitively? `go mod graph` and `go mod why <module>` answer this
   after the fact; check before.

Every dependency is attack surface, build time and a future upgrade. Prefer
`golang.org/x/...` and packages from organisations that ship on a schedule.

## Upgrading

```bash
go list -m -u all                # what has newer versions
go get -u ./... && go mod tidy   # within existing major versions
go get example.com/pkg@v2.3.0    # one major bump, its own commit
go mod why example.com/pkg       # who pulled this in
go tool govulncheck ./...        # vulnerabilities your code actually reaches
```

One module per commit for majors, so a regression has one suspect. Read the changelog
first — a dependency bump is a behaviour change you did not write. `govulncheck` reports
only vulnerabilities on a call path your code reaches, so its findings are real work
rather than a CVE inventory.

A `replace` directive is for a local fork you are actively developing. Never commit one
pointing at a developer's disk; use `go.work` for that.

## Dev tools

Since Go 1.24, tools are tracked in `go.mod`:

```bash
go get -tool golang.org/x/vuln/cmd/govulncheck
go tool govulncheck ./...
```

This replaces the `tools.go` file full of blank imports. Delete any you find, and move the
entries to `tool` directives so every contributor and CI runner gets the same version.

## Workspaces

`go.work` (Go 1.18) lets several local modules resolve to each other without `replace`:

```bash
go work init ./api ./worker ./shared
go work use ./newmodule
```

`go.work` is a local development file: keep it out of version control (or commit it only
in a monorepo where every checkout has the same layout), because it silently overrides
module resolution for anyone who has it.

## Publishing a module

- The module path must equal the repository URL. Tag releases `vX.Y.Z`.
- Major version 2 and above changes the import path: the module path gets a `/v2` suffix
  and the tag is `v2.0.0`. There is no way around this and no way to do it silently.
- Anything exported is frozen for the life of the major version. Before the first tag,
  export the smallest surface you can defend.
- Additive changes are safe; changing a signature, removing a method, or narrowing an
  accepted type is not. Adding a method to an exported *interface* breaks every external
  implementation, so keep exported interfaces small and stable.
- `deprecated:` in a doc comment is the machine-readable marker tools surface:

```go
// Deprecated: use ParsePort instead.
func ParsePortString(s string) (int, error)
```

## Embedding files

```go
import _ "embed"

//go:embed templates/*.html
var templates embed.FS

//go:embed version.txt
var version string
```

`go:embed` (Go 1.16) removes the "where is the config at runtime" problem for templates,
migrations, and static assets. The directive must sit immediately above the variable, and
the paths are relative to the source file's directory — nothing outside the package
directory can be embedded.

## Common mistakes

| Mistake | Fix |
|---|---|
| `cmd/`, `internal/`, `pkg/` on a 300-line tool | One package in the module root |
| `service/`, `repository/`, `controller/` | Domain packages: `auth/`, `billing/`, `jobs/` |
| `utils/`, `common/`, `helpers/` | Put the function where it is used |
| Import cycle worked around with an interface package | Move the boundary |
| Module path that is not the repository URL | Fix it before the first tag |
| Committed `replace` pointing at a local path | `go.work`, uncommitted |
| `tools.go` with blank imports | `go get -tool` and `go tool` (Go 1.24+) |
| `go.sum` in `.gitignore` | Commit it; it is the supply-chain check |
| Bumping the `go` directive to silence a warning | Raise it deliberately, in its own commit |
| `log.Fatal` in library code | Return an error; only `main` exits |

<!-- sources: spf13-go, samber-golang, ashwin-go, go-effective-go, go-release-notes -->
