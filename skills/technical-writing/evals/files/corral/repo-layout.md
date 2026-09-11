# corral — repo layout

Where the attached files live in the real repository. The copies you have been
given are flat; cite these paths in any finding.

```
corral/
  README.md                 <- README.md
  CHANGELOG.md              <- CHANGELOG.md
  Makefile                  <- Makefile
  pyproject.toml            <- pyproject.toml
  docs/
    getting-started.md      <- getting-started.md
    reference.md            <- reference.md
  src/corral/
    __init__.py             (re-exports Client, Response and the error classes from client.py)
    client.py               <- client.py
    limiter.py              <- limiter.py
    cli.py                  (argparse entrypoint; `main()` is the `corral` console script)
  tests/
    test_backoff.py
    test_limiter.py
```

Facts about the repository that are not visible in the attached files:

- `docs/` has exactly the two files listed above. There is no `docs/concepts.md`,
  no `docs/index.md`, and no docs-site generator (no `mkdocs.yml`, no
  `docusaurus.config.js`, no `package.json`). The docs are plain Markdown read
  on the forge.
- The `Makefile` shown is complete: `test`, `lint`, `typecheck`. There are no
  other targets.
- `src/corral/__init__.py` re-exports exactly `Client`, `Response`,
  `CorralError`, `CorralRateLimited`, `CorralTimeout`.
- The latest git tag is `v3.1.0`. Tags are `vX.Y.Z`. The forge is
  `https://github.com/acme/corral`.
- `CORRAL_TIMEOUT` is not read anywhere in the source tree.
- Released dates from the tag list: `v2.4.0` 2026-02-11, `v2.4.1` 2026-03-02,
  `v3.0.0` 2026-05-19, `v3.1.0` 2026-08-27.
