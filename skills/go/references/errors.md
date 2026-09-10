# Errors

Verified against: Go 1.26 and Go 1.27.

## Contents

- [Which error shape to build](#which-error-shape-to-build)
- [Wrapping](#wrapping)
- [Inspecting](#inspecting)
- [errors.Join](#errorsjoin)
- [The single-handling rule](#the-single-handling-rule)
- [Error strings](#error-strings)
- [panic and recover](#panic-and-recover)
- [Logging errors with slog](#logging-errors-with-slog)
- [Common mistakes](#common-mistakes)

## Which error shape to build

Pick from what the caller has to do, not from habit.

| Caller needs | Build | Example |
|---|---|---|
| Nothing but a message | `fmt.Errorf("...: %w", err)` | Most call sites |
| To branch on one specific condition | Sentinel: `var ErrNotFound = errors.New("not found")` | `io.EOF`, `sql.ErrNoRows` |
| To read structured data off the failure | Typed error with fields | `*ValidationError{Field: "email"}` |
| Nothing — the detail is internal | Opaque: wrap with `%v`, not `%w` | Crossing a public API boundary |

A sentinel or a typed error is part of your API: once a caller writes
`errors.Is(err, ErrNotFound)`, removing it is a breaking change. Introduce one only when a
caller actually branches.

`%v` at a boundary is a deliberate choice, not an oversight. Wrapping a database driver's
error with `%w` in an exported function makes that driver part of your API surface; wrap
with `%v` (or a domain error) when you do not want callers matching on it, and say why in
a comment.

## Wrapping

```go
data, err := os.ReadFile(path)
if err != nil {
    return fmt.Errorf("loading config %s: %w", path, err)
}
```

- Add what the callee could not know: which file, which id, which operation. Do not
  repeat what the wrapped error already says — `fmt.Errorf("error reading file: %w", err)`
  produces `error reading file: open x: no such file or directory`.
- No capital, no trailing punctuation, no "failed to" prefix. The chain reads as
  `loading config /etc/app.yaml: open /etc/app.yaml: permission denied`.
- One `%w` per `fmt.Errorf` is the common case; multiple `%w` verbs are legal (Go 1.20+)
  and produce a multi-error, but `errors.Join` says it more clearly.
- A typed error joins the chain by implementing `Unwrap() error`:

```go
type QueryError struct {
    Query string
    Err   error
}

func (e *QueryError) Error() string { return e.Query + ": " + e.Err.Error() }
func (e *QueryError) Unwrap() error { return e.Err }
```

## Inspecting

```go
if errors.Is(err, sql.ErrNoRows) { ... }             // sentinel identity, anywhere in the chain

ve, ok := errors.AsType[*ValidationError](err)        // Go 1.26+
if ok { log.Info("bad field", "field", ve.Field) }

var ve *ValidationError                               // Go 1.25 and below
if errors.As(err, &ve) { ... }
```

The two failure modes this replaces are both silent:

- `err == ErrNotFound` stops matching as soon as any layer wraps the error, and nothing
  warns you. The comparison simply becomes false and the caller takes the wrong branch.
- `ve, ok := err.(*ValidationError)` has the same problem for typed errors. If the producer
  writes `fmt.Errorf("checking name: %w", &ValidationError{...})`, the assertion never
  succeeds.

`errors.AsType[T](err)` (Go 1.26+) is the generic form: it returns `(T, bool)` instead of
requiring a pre-declared target variable, so there is no `var ve *ValidationError` line to
get wrong. Use `errors.As` when the target is a non-error interface or the module is pinned
below 1.26.

Never match on `err.Error()` text. Message wording is not an API and changes without
notice.

## errors.Join

`errors.Join(errs...)` (Go 1.20+) combines independent failures into one error whose
`Unwrap() []error` lets `errors.Is` and `errors.As` still see each member. It returns nil
when every argument is nil, which makes the accumulate-and-return shape clean:

```go
func (u *User) Validate() error {
    var errs []error
    if u.Name == "" {
        errs = append(errs, &ValidationError{Field: "name"})
    }
    if u.Email == "" {
        errs = append(errs, &ValidationError{Field: "email"})
    }
    return errors.Join(errs...) // nil when errs is empty
}
```

This is the difference between telling a user one problem at a time and telling them all of
them. Use it for validation, for fan-out results, and for a `Close` that must run several
shutdowns and report whatever failed.

For a deferred close that must not swallow its error:

```go
func write(path string, data []byte) (err error) {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer func() { err = errors.Join(err, f.Close()) }()
    _, err = f.Write(data)
    return err
}
```

## The single-handling rule

An error is handled exactly once: logged, or returned, never both.

```go
// Wrong: two log lines for one failure, and the caller logs it again.
if err != nil {
    log.Printf("scan failed: %v", err)
    return nil, fmt.Errorf("scan failed: %w", err)
}

// Right: add context, return, and let the boundary decide.
if err != nil {
    return nil, fmt.Errorf("scanning user %s: %w", id, err)
}
```

The boundary is where the error stops travelling: an HTTP handler, a CLI `main`, a queue
consumer's message loop, the top of a worker goroutine. That is the one place that logs it,
maps it to a status code, and increments a metric.

Never discard an error with `_`. `_, _ = db.Exec(...)` turns a failed write into a
successful return, which is the most expensive kind of bug because nothing is observable.
The only defensible `_` is on a call that cannot fail in a way you can act on, and it gets
a comment saying so.

## Error strings

From Go Wiki, Code Review Comments:

- Lowercase (unless the first word is a proper noun or an acronym) and no trailing
  punctuation, because the string is printed inside a longer message.
- Say what failed, not that something failed: `"parsing port: invalid syntax"`, not
  `"an error occurred"`.
- Sentinel names read as `ErrX`: `ErrNotFound`, `ErrClosed`, `ErrTimeout`.

## panic and recover

Panic is for a violated internal invariant or for a failure at startup where continuing is
meaningless — a nil dependency wired in `main`, an unparseable embedded template. It is
never a control-flow mechanism, and a library must not panic across its API boundary.

Recover only at an isolation boundary you own — a server's per-request middleware, a worker
loop that must survive one bad job:

```go
defer func() {
    if r := recover(); r != nil {
        logger.Error("handler panicked", "panic", r, "stack", string(debug.Stack()))
        http.Error(w, "internal error", http.StatusInternalServerError)
    }
}()
```

Two traps: a `recover` only catches a panic on *its own* goroutine, so a panic inside a
`go func()` you spawned takes the whole process down regardless of the handler upstairs;
and capture `debug.Stack()` inside the deferred function, because by the time you have
logged elsewhere the stack is gone.

## Logging errors with slog

`log/slog` (Go 1.21+) is the standard structured logger. The patterns that matter:

- Pass a `*slog.Logger` as a dependency. A package-level logger outside `main` cannot be
  substituted in a test and cannot carry request-scoped fields.
- Attach request-scoped fields once with `logger.With("request_id", id)` and pass the
  derived logger down.
- Levels carry meaning: `Debug` for internal state, `Info` for lifecycle events, `Warn` for
  recovered problems, `Error` for something that needs a human. Logging every handled error
  at `Error` makes the level useless.
- Log the error value, not its text: `logger.Error("saving user", "err", err)`. Handlers
  can then render the chain, and a JSON handler keeps it as one field.

## Common mistakes

| Mistake | Fix |
|---|---|
| `err == ErrX` | `errors.Is(err, ErrX)` |
| `e, ok := err.(*T)` | `errors.AsType[*T](err)` (Go 1.26+) or `errors.As` |
| `%v` where the caller must inspect | `%w` |
| `%w` on a driver error in an exported API | `%v` or a domain error, and say why |
| Log then return | Return; log once at the boundary |
| `_, _ = f()` | Check it, or comment why it cannot matter |
| `fmt.Errorf("Failed to open file!")` | `fmt.Errorf("opening %s: %w", path, err)` |
| `strings.Contains(err.Error(), "not found")` | Sentinel plus `errors.Is` |
| Validation that stops at the first field | Accumulate and `errors.Join` |
| `recover()` expected to catch another goroutine | Recover inside that goroutine |

<!-- sources: samber-golang, spf13-go, cxuu-golang, ashwin-go, go-wiki-codereview, go-release-notes -->
