# Lifetime and exception boundaries

Verified against: C++ working-draft clauses [except.ctor], [vector.modifiers],
[lib.types.movedfrom]; apply the C++17 rules below unless marked otherwise.
The working draft also contains later facilities; its presence is not evidence
that a C++17 standard library implements them. Semantic claims are [official].

## Contents

- Track the referent, not the wrapper
- Make construction failure safe before entering the body
- Moves must preserve the type's contract
- State the guarantee at the operation boundary

## Track the referent, not the wrapper

For every escaping borrow, record `borrow → subobject → owner → last use` and
which intervening operations invalidate the subobject. Include `string_view`
(C++17), `span` (C++20), iterators, references, pointer members and captured `this`.
A value category answers how an expression binds, not how long the referent lives.

An owned snapshot is the default for small deferred inputs. Use a live shared
owner only when the contract wants shared state and its mutation protocol is clear.
For example, constructing `std::string` from a `string_view` copies the characters;
copying the view copies only its description. Extending a container's lifetime
still permits its strings to change or its elements to relocate.

Use these operation-specific checks:

| Operation | Check before retaining a borrow |
|---|---|
| `vector` grows beyond capacity | All element pointers/references/iterators invalidate |
| `vector` inserts without reallocation | At/after insertion point invalidates, including old end |
| `vector::erase` | At/after erased position invalidates; capacity staying fixed is irrelevant |
| String assignment or mutation | Consult the string operation's invalidation rules, not the view's lifetime |
| Move of a containing object | Determine whether referent storage is transferred or relocated; do not infer stability from `std::move` |
| Returning a reference/view | Follow all the way to the owner, including temporaries and locals |

Do not fix self-referential objects by reserving capacity. A type containing both
an owned buffer and a pointer/view into it needs copy/move operations that rebuild
the internal borrow, or a representation that stores an offset and derives a view
on demand. Defaulted memberwise movement does not rebase internal pointers.

## Make construction failure safe before entering the body

In an ordinary non-delegating constructor, initialized members and bases unwind
in reverse completion order; the incomplete object's own destructor is not called.
Thus putting cleanup only in that destructor leaves an acquisition gap.

Use owning members to close the gap. This C++17 example intentionally injects a
failure after ownership is established; it is a failure-path example, not a factory:

```cpp
#include <memory>
#include <stdexcept>

class Scratch {
    std::unique_ptr<int[]> bytes_;
public:
    explicit Scratch(bool reject)
        : bytes_(std::make_unique<int[]>(16)) {
        if (reject) throw std::runtime_error("scratch rejected");
    }
};
```

`bytes_` is destroyed if the body throws. Raw `new` assigned to a raw member would
not be released by an enclosing destructor that never runs. For multiple members,
use declaration order to reason about acquisition, not initializer-list spelling.

Keep the exception to the rule explicit: when a delegating constructor's target
has completed and the delegating body throws, the object's destructor is invoked.
Do not build a cleanup routine that double-releases members on that path.

A constructor function-try-block runs its handler after subobject destruction.
Do not access those members from the handler or pretend falling out of that handler
creates a usable object. Use constructor parameters or external diagnostic data.

## Moves must preserve the type's contract

The standard-library default is valid but unspecified after move, unless a type
states something stronger. `empty()` can be legitimate while `front()` still needs
non-emptiness. Do not transfer that library-wide promise automatically to arbitrary
user-defined types; specify and implement their post-move invariant.

Watch owner/count pairs: moving a `unique_ptr` clears the source pointer, while
moving an integer leaves its old count. If methods assume `count > 0` implies a
non-null pointer, a defaulted move violates the invariant. Prefer a standard owning
container that encapsulates both; otherwise reset the count on transfer and define
self-move assignment and destination-resource release deliberately.

`std::move` does not move by itself. A const source can select a copy; an explicitly
declared destructor can affect implicit move generation. Inspect the selected
special members before explaining a copy or performance regression.

## State the guarantee at the operation boundary

For strong exception safety, finish potentially throwing preparation before a
non-throwing commit. Include externally visible state, not just the object's bytes:
a log append, callback, or file write may already be an irreversible effect.
For the basic guarantee, show that resources and invariants survive, not that the
old value survives. Give fallible close/flush its own explicit operation when the
caller needs an error; a destructor cannot safely act as a routine error channel.

Do not declare every move `noexcept`. For single-element vector insertion at the
end, copying availability or non-throwing movement determines important no-effects
guarantees. A throwing move of a non-CopyInsertable element can leave unspecified
effects. Containers can support such types; they do not require every move to be
non-throwing. Read the guarantee for the exact modifier, not a blanket vector rule.

<!-- sources: cppcheatsheet, margelo-cpp, cpp-draft -->
