# Advanced widget topics

This file covers the advanced parts of the widget system.

## Compound components

A compound component exposes sub-components on the parent so that callers can
control the layout. Use the context API to share state between the parent and
its children.

## Polymorphic components

A polymorphic component accepts an `as` prop that changes the rendered element.
Type it with a generic constrained to `ElementType`.

## Virtualisation

Long lists should be virtualised so that only the visible rows are mounted.

## Registry internals

The registry format, the codegen pipeline and the version-pinning rules are
documented in [internals.md](internals.md). Read that file before changing
anything under `src/registry/`.
