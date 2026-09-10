# Registry internals

## Registry format

`src/registry.json` maps a component name to its entry point, its peer
dependencies and the design-token groups it consumes.

## Codegen pipeline

The build reads the registry, emits a barrel file per entry point and writes a
type declaration bundle.

## Version pinning

A component may only depend on a token group at the major version recorded in
the registry. Bumping it requires a migration note.
