# Language idioms

Verified against: Go 1.26 and Go 1.27.

## Contents

- [Zero values](#zero-values)
- [Declarations, nil and empty](#declarations-nil-and-empty)
- [Values, pointers and aliasing](#values-pointers-and-aliasing)
- [Receivers](#receivers)
- [Interfaces](#interfaces)
- [Structs and constructors](#structs-and-constructors)
- [Control flow](#control-flow)
- [Generics](#generics)
- [Naming](#naming)
- [Doc comments](#doc-comments)
- [Common mistakes](#common-mistakes)

## Zero values

Design a type so its zero value works without a constructor. `sync.Mutex`, `bytes.Buffer`
and `time.Time` are the models: no `NewMutex()` exists because none is needed.

```go
type Counter struct {
    mu sync.Mutex // guards n
    n  int
}

func (c *Counter) Inc() { c.mu.Lock(); c.n++; c.mu.Unlock() }

var c Counter // ready
```

A type that panics or misbehaves at zero forces a constructor on every caller and on every
embedding struct. When a field genuinely has no sensible zero, either give the type a
constructor that is the only way to build it (unexported fields, exported `New`), or
document the invariant on the type.

`cmp.Or(a, b, c)` (Go 1.21+) returns the first non-zero argument, which replaces the
`if cfg.Timeout == 0 { cfg.Timeout = ... }` shape:

```go
cfg.Timeout = cmp.Or(cfg.Timeout, 30*time.Second)
```

## Declarations, nil and empty

- `var t []string` for an empty slice, not `t := []string{}`. Both have length and
  capacity zero; the nil slice is the preferred form and appends the same way.
- Use a non-nil empty slice only when the difference is observable — most often JSON,
  where a nil slice encodes as `null` and `[]string{}` as `[]`. Say so in a comment when
  you do.
- Maps have no nil-write escape: reading a nil map is fine and returns the zero value, but
  writing panics. `make(map[K]V)` before the first write.
- `make([]T, 0, n)` when you know `n`; do not preallocate speculatively, since
  `make([]T, 0, 1000)` for eight elements wastes the allocation it was meant to save.
- `:=` for a value you have; `var` for a zero value you will fill in. The form is the
  signal.
- Do not design an API around distinguishing nil from empty. Callers get it wrong and the
  distinction survives no serialisation boundary.

## Values, pointers and aliasing

Choose from the contract, not from size superstition:

- **Value** when copying is meaningful and identity is irrelevant (`time.Time`, a config
  struct, a coordinate).
- **Pointer** when identity, mutation or absence is part of the contract, or when the type
  holds a `sync` primitive.

Slices and maps are descriptors over shared storage. Passing one by value still shares the
backing array, so a callee that keeps a slice you handed it, or one you keep from a caller,
is an aliasing bug waiting for the next `append`. Copy at the ownership boundary:

```go
func NewBatch(items []Item) *Batch {
    return &Batch{items: slices.Clone(items)} // caller keeps mutating its own slice
}
```

The same applies to sub-slicing: `s[:2]` shares the array with `s`, and appending to the
sub-slice can overwrite the parent's elements. `slices.Clip(s)` limits capacity so an
append must reallocate.

Do not copy a value whose methods are on the pointer type (`go vet`'s `copylocks` catches
the mutex case). Do not copy a struct from another package that contains a slice unless
its documentation says a copy is safe.

## Receivers

Keep one type's receivers uniform: all pointer, or all value. Mixed receivers make the
method set depend on how the caller obtained the value, which is how a type silently stops
implementing an interface.

Use a pointer receiver when the method mutates, when the struct contains a `sync` type or
is large enough that copying shows up in a profile, or when any other method already needs
one. Value receivers make sense for small immutable types where copying is the point.

Receiver names are short and consistent within a type (`c *Counter`, not `this` or
`self`), and a method may be called on a nil pointer receiver — either handle nil or
document that you do not.

## Interfaces

- The consumer declares the interface it needs, in the consuming package. An interface
  exported beside its single implementation forces every caller to import it and buys
  nothing.
- One or two methods. `io.Reader` is the canonical size; `Repository` with fourteen methods
  is a class hiding behind a keyword.
- Accept interfaces, return concrete types. Returning an interface hides fields the caller
  may legitimately need and forces type assertions later.
- Interfaces are satisfied implicitly, so no `implements` declaration exists. When you want
  a compile-time check that a type still satisfies one:
  `var _ http.Handler = (*Server)(nil)`.
- Embedding composes behaviour: a struct embedding `io.Reader` gets `Read` promoted. Embed
  the interface (not the implementation) when you want to wrap and override a subset.
- A nil pointer stored in an interface is not a nil interface. `var p *T = nil; var i any = p`
  gives `i != nil`, which is the classic non-nil-error bug: return `nil` explicitly rather
  than a nil typed pointer as an `error`.

## Structs and constructors

Functional options are the answer to a constructor with many optional parameters:

```go
type Server struct {
    addr    string
    timeout time.Duration
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second} // defaults live here
    for _, opt := range opts {
        opt(s)
    }
    return s
}
```

Use it when the options are genuinely optional and the set will grow. For two required
parameters, two parameters are clearer. A plain config struct is the other reasonable
answer when the caller wants to build the configuration elsewhere and pass it whole.

Field tags (`json:"name,omitzero"`, `db:"user_id"`) are the type's serialisation contract;
keep them next to the field and do not duplicate the mapping in a second table.

## Control flow

- Keep the happy path at the left margin: handle the error, `return`, and continue. Never
  put the main logic in an `else`.
- `if v, err := f(); err != nil { ... }` scopes the variables to the branch when they are
  not needed afterwards.
- A `switch` without a condition replaces an if/else chain; `switch v := x.(type)` handles
  type dispatch. Go does not fall through unless you write `fallthrough`.
- `for i := range n` (Go 1.22+) for a count, `for range n` when the index is unused. The
  classic three-clause form stays for a non-zero start, a step other than `++`, or a
  descending loop.
- `defer` runs in LIFO order at function return, and its arguments are evaluated when the
  `defer` statement executes. A `defer` in a loop accumulates until the function returns —
  move the body into its own function.
- Labelled `break`/`continue` beats a boolean flag when leaving a nested loop.

## Generics

Generics exist to remove duplicated *algorithms*, not to build type hierarchies.

```go
func Map[S, T any](s []S, f func(S) T) []T {   // one algorithm, many types
    out := make([]T, len(s))
    for i, v := range s {
        out[i] = f(v)
    }
    return out
}
```

- Write the concrete version first. Generify when the same body already exists for three
  or more types.
- `comparable` for map keys and equality, `cmp.Ordered` for `<`/`>`. A constraint should
  express a real requirement, not `any` standing in for "I have not decided".
- Do not write `Repository[T]`, `Service[T]` or generic base types. That is inheritance in
  disguise and it fights the type system at every call site.
- Type inference covers most calls; explicit instantiation (`Map[string, int](...)`) is a
  sign the signature is ambiguous.
- Generic type aliases are supported (Go 1.24+); generic *methods* (a method declaring its
  own type parameters) are new in Go 1.27 and are not available on earlier toolchains.

## Naming

- Packages: short, lowercase, one word, no underscores, named for what they provide
  (`auth`, `jobs`). `util`, `common`, `base`, `helpers` are not names.
- The package name is part of every identifier: `http.Server`, not `http.HTTPServer`.
  `bytes.NewBuffer`, not `bytes.NewBytesBuffer`.
- No `Get` prefix on accessors: `user.Name()`, not `user.GetName()`. Setters keep `Set`.
- Initialisms keep their case: `userID`, `ServeHTTP`, `parseURL` — never `userId` or
  `parseUrl`.
- Scope drives length: `i`, `r`, `b` in a three-line body; a descriptive name for anything
  that lives across a screen.
- Interface names for single-method interfaces take `-er`: `Reader`, `Fetcher`,
  `Validator`.

## Doc comments

Every exported identifier gets a comment starting with its name and forming a sentence:

```go
// ParsePort converts a decimal port string to an int.
// It returns ErrEmptyPort when s is empty.
func ParsePort(s string) (int, error)
```

A package gets one `// Package foo ...` comment, on exactly one file. `go doc` renders
these, so the first sentence is the summary people actually read.

## Common mistakes

| Mistake | Fix |
|---|---|
| `t := []string{}` | `var t []string` unless JSON needs `[]` |
| Writing to a nil map | `make(map[K]V)` first |
| Keeping a caller's slice without copying | `slices.Clone` at the boundary |
| Mixed value and pointer receivers | Pick one for the whole type |
| Interface exported next to its implementation | Declare it in the consumer |
| Returning an interface from a constructor | Return the concrete type |
| Returning a nil `*MyError` as `error` | Return a literal `nil` |
| `func (u *User) GetName() string` | `func (u *User) Name() string` |
| `userId`, `parseUrl` | `userID`, `parseURL` |
| `Repository[T]` | A concrete interface with the methods you need |
| Main logic inside `else` | Handle the error and return |
| `defer` inside a hot loop | Extract the body into a function |

<!-- sources: spf13-go, samber-golang, cxuu-golang, ashwin-go, awesome-copilot-go, go-effective-go, go-wiki-codereview, go-release-notes -->
