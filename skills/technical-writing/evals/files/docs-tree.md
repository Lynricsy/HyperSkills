# Current docs layout (plain Markdown, rendered on the forge today)

```
docs/
  index.md                     "Ledger" — what the service is
  tutorials/
    first-ledger.md            "Post your first entry"
    reconciling.md             "Reconcile a statement"
  guides/
    csv-import.md
    multi-currency.md
    webhooks.md
    retry-a-failed-export.md
  reference/
    http-api.md
    cli.md
    config.md                  env vars and defaults
    errors.md
  concepts/
    double-entry.md
    why-not-floats.md
  adr/
    0001-postgres-for-the-ledger.md
    0002-decimal-not-float.md
```

Facts about the repository:

- No site generator is configured yet: no `mkdocs.yml`, no `docusaurus.config.js`,
  no `package.json` at the repository root. Python project, `uv` managed,
  `pyproject.toml` with a `dev` extra.
- CI is GitHub Actions. The only existing workflow is `.github/workflows/ci.yml`,
  which runs `uv run pytest` and `uv run ruff check` on push and pull request.
- The repository is `acme/ledger`; the default branch is `main`.
- GitHub Pages is not enabled on the repository yet.
- Internal links between the Markdown files are relative, for example
  `../reference/config.md`.
