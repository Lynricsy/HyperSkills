# Cargo compatibility and verification

Verified against: Cargo/Rust documentation 1.98.1; resolver and syntax floors
are stated below. [official] Cargo Book semantics override community shortcuts.
[community] The effective-configuration workflow adapts full-stack cargo-build.

## Contents

- Establish the effective build
- Diagnose feature unification
- Isolate the consumer
- Separate version promises
- Choose evidence by contract

## Establish the effective build

Inspect before modifying the graph:

```sh
rustc --version --verbose
cargo --version
cargo locate-project --workspace
cargo metadata --no-deps --format-version 1
cargo tree -e features
```

Record selected packages, targets, target triple, features, profile and lockfile
policy alongside each command. Cargo configuration discovery depends on the
working directory, not just `--manifest-path`; check ancestor `.cargo/config.toml`
and relevant environment overrides when local and CI behavior differs.

Read the actual workspace root. Virtual workspaces have no root package edition
to infer a resolver from, so specify it explicitly. `default-members` can change
which packages an unqualified command selects. Members opt into workspace package
and dependency inheritance; declaring a value at the root does not apply it to
all members automatically. Profiles in member manifests are ignored, not a new
profile isolated to that member.

Keep the existing lockfile policy. Use `--locked` when commands must not change
it; `--frozen` additionally forbids network access. Do not clear caches, remove a
lockfile or broadly update dependencies to repair an unexplained graph failure.
Cargo can execute build scripts and proc macros; fetching untrusted dependencies
is not a read-only act merely because the command says `check`.

## Diagnose feature unification

Features add capabilities. On a normal dependency shared by selected packages,
Cargo uses the union of enabled features. `default-features = false` is not a veto
against another dependency edge enabling defaults. A crate must request every
feature of its dependency that its own code needs.

Use `cargo tree -e features -i DEPENDENCY` with the dependency's actual package
name (and version if ambiguous) to find the activation edge. Compare the graph
for the failing package and for the successful workspace command. Do not fix a
library's undeclared requirement by enabling a feature in an unrelated CLI.

Resolver 2 separates inactive target dependencies, build/proc-macro contexts and
dev-dependencies when they are not being built. It does not isolate two normal
consumers of the same dependency. Tests and `--all-targets` can bring dev features
back into unification. Resolver 3 changes MSRV-aware version selection, not that
normal-dependency fact.

For optional dependency wiring, use `dep:name` to suppress the implicit public
feature with that dependency's name. Use `dependency?/feature` when forwarding
must not activate the optional dependency by itself. Both syntaxes require 1.60+.
Choose additive `std` support rather than a `no_std` feature that disables behavior.
If mutually exclusive combinations are unavoidable, state supported combinations
and reject invalid ones; do not blindly prescribe `--all-features`.

## Isolate the consumer

Use separate Cargo invocations, not multiple `-p` selections in one invocation,
when checking members without feature help from siblings. Start with `cargo check
-p PACKAGE --lib` for a library; omit tests/examples/dev targets in that check.
If minimal features are supported, separately add `--no-default-features` and
only the explicitly supported feature set. Substitute the actual package name.
This excludes inactive dev-dependency features only with resolver 2 or 3.
Resolver 1 still unifies them: retain its compatibility policy and use an
external consumer to test without that package's dev-feature help.

For a public crate, create a scratch consumer outside the workspace with an
independent manifest and dependency declaration. Compile a real use of the public
API, not just an empty consumer. For packaging defects, verify the packaged crate
with Cargo's package verification and inspect included files; an in-tree path
consumer still sees local files that might not be shipped.

A scratch consumer is a verification artifact, not a new permanent workspace
member. Do not restructure the repository merely to expose missing features.
Use its result to fix the declaration at the consumer that requires the feature.

## Separate version promises

| Claim or syntax | Availability / limitation |
|---|---|
| Resolver 2 | Cargo 1.51+; edition 2021 default |
| `dep:` and weak `?/` feature syntax | Cargo 1.60+ |
| Workspace package/dependency inheritance | Cargo 1.64+; members opt in |
| Workspace lints | Cargo 1.74+; members opt in |
| Resolver 3 | Cargo 1.84+; edition 2024 default |
| Edition 2024 | Rust 1.85+; not equivalent to the project's MSRV promise |

`package.rust-version` declares support; it does not make newer library APIs or
Cargo syntax available to the older compiler. Resolver 3's `fallback` prefers
compatible dependency versions but can still choose an incompatible one when no
compatible candidate satisfies the requirement. It is not an MSRV proof.

Run the declared minimum compiler explicitly, such as `cargo +1.74.0 check` only
when 1.74 is the actual promise, using the same isolated package/feature selection.
Also test the supported development toolchain. Inspect whether the lockfile format
and dependency versions are readable and buildable by that older Cargo. Do not
raise the minimum version or change the resolver without treating it as a
compatibility decision. A nightly-only diagnostic is not a production dependency.

## Choose evidence by contract

| Evidence | What it can establish | What it cannot establish alone |
|---|---|---|
| `cargo check` on the intended target/features | Selected code type-checks | Linker/FFI/runtime behavior |
| Library-only isolated build | No sibling feature crutch; inactive dev features excluded with resolver 2/3 | Resolver 1 dev-feature isolation or every published configuration |
| `cargo test` and doctests | Exercised behavior and examples | Unrun interleavings or soundness |
| `cargo clippy` with project policy | Known lint violations | Correct cancellation or unsafe proofs |
| `cargo +nightly miri test` | Supported executed Rust memory operations | Arbitrary foreign code or all paths |
| Real foreign integration | Exercised ABI, linking and resource lifecycle | All targets not actually run |
| Profile/benchmark in intended build | Measured hot path and workload | Universal cost of Clone or Arc |

Do not substitute `cargo test --all-targets` for doctest coverage: use the
repository's doctest command explicitly where public examples matter. Use the
project's formatting and lint policy rather than adding a new blanket lint ban.
Select a matrix from supported contracts: default, minimal, important feature
combinations, independent public consumer, target and MSRV. A full-feature row is
useful integration evidence, not a replacement for those rows.

For profiling, retain a representative workload and compare equivalent profiles,
targets and input sizes. Inspect allocations or contention before introducing
unsafe fast paths. For unsafe verification, distinguish an unavailable nightly
tool from a failed contract and report what was not exercised.

<!-- sources: full-stack-cargo, cargo-features, cargo-resolver, cargo-workspaces, rust-edition-unsafe -->
