# Packaging and publishing

Verified against: PyPA specifications as of uv 0.12.x / setuptools 8x / hatchling 1.27+.

## Contents

- [src layout, and when flat is fine](#src-layout-and-when-flat-is-fine)
- [Names](#names)
- [The `[project]` table](#the-project-table)
- [Build backends](#build-backends)
- [Versioning](#versioning)
- [Shipping types: `py.typed`](#shipping-types-pytyped)
- [Entry points](#entry-points)
- [Building and inspecting](#building-and-inspecting)
- [Publishing](#publishing)
- [Common packaging failures](#common-packaging-failures)

## src layout, and when flat is fine

```
acme-orders/
├── pyproject.toml
├── README.md
├── src/
│   └── acme_orders/
│       ├── __init__.py
│       ├── py.typed
│       └── service.py
└── tests/
    ├── conftest.py
    └── test_service.py
```

`src/` is the default for anything distributable, for one concrete reason: the
package is not importable from the repository root, so tests must import the
**installed** copy. Under a flat layout `import acme_orders` picks up the source
directory whether or not the package installs correctly, and a missing
`__init__.py`, a file left out of the wheel or a broken entry point all pass CI
and fail for users.

Flat is defensible for a single-module package or a repository that is never
installed. `uv init --package` produces the src layout for you.

## Names

The distribution name and the import name are different strings and follow
different rules: `acme-orders` on PyPI, `acme_orders` in `import`. Underscores in
a PyPI name are normalised to hyphens for lookup, so `acme_orders` and
`acme-orders` collide.

Check availability on PyPI before writing the name into a dozen files, and avoid
names one character away from a popular package — typosquatting protection is
partly the ecosystem's problem and partly yours.

## The `[project]` table

```toml
[project]
name = "acme-orders"
version = "1.2.0"
description = "Order placement and reservation helpers"
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"                       # SPDX expression (PEP 639)
license-files = ["LICENSE"]
authors = [{ name = "Acme", email = "dev@acme.example" }]
keywords = ["orders", "warehouse"]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python :: 3.12",
  "Typing :: Typed",
]
dependencies = ["httpx>=0.27"]

[project.urls]
Homepage = "https://github.com/acme/acme-orders"
Changelog = "https://github.com/acme/acme-orders/blob/main/CHANGELOG.md"
Issues = "https://github.com/acme/acme-orders/issues"
```

Notes that save a rejected upload:

- `license` is an SPDX **expression** string now; the old
  `license = { text = "MIT" }` table and the `License :: OSI Approved :: ...`
  classifiers are deprecated, and PyPI rejects a classifier that contradicts the
  expression.
- Do not add a `Programming Language :: Python :: 3.x` classifier for a version
  `requires-python` excludes. Classifiers are metadata, not enforcement, so the
  mismatch only misleads.
- `readme` must resolve at build time; a path outside the project directory fails
  the build rather than the upload.
- Dependency constraints belong here as ranges (`>=1.2,<2`). An `==` pin in a
  library forces itself on every consumer and makes your package unco-installable.
  Pin exactly only in applications, and then in the lockfile.

## Build backends

| Backend | Choose it when |
|---|---|
| `uv_build` | pure-Python project already using uv, minimal configuration wanted |
| `hatchling` | pure Python, plugins needed (version from file, custom file inclusion) |
| `setuptools` | C / Cython / Rust-via-setuptools extensions, or existing setuptools config |
| `flit_core` | single module, near-zero configuration |

```toml
[build-system]
requires = ["uv_build>=0.12"]
build-backend = "uv_build"
```

There must be a `[build-system]` table. Without one, installers fall back to
legacy setuptools behaviour and look for the `setup.py` a migration just deleted.

Non-Python assets (templates, data files, `py.typed`) are included per backend:
`hatchling` via `[tool.hatch.build.targets.wheel]`, setuptools via
`[tool.setuptools.package-data]`. Every backend excludes what it does not know
about, which is why the marker file disappears from the wheel while everything
looks right in the source tree.

## Versioning

Two workable schemes; pick one and let exactly one place own the number.

**Static in `pyproject.toml`.** Simplest, and the release process is "bump, tag,
build". Keep `__version__` out of the code entirely, or derive it:

```python
from importlib.metadata import version
__version__ = version("acme-orders")
```

**Derived from git tags** (`hatch-vcs`, `setuptools-scm`):

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
```

The tag becomes the version, so the two can never disagree. The cost: a build
from a tarball with no `.git` has no version, so sdists must carry the resolved
value, and shallow CI clones need tag fetching (`fetch-depth: 0`).

Version numbers follow PEP 440: `1.2.0`, `1.2.0a1`, `1.2.0rc1`, `1.2.0.post1`,
`1.2.0.dev3`. PyPI normalises (`1.2.0-alpha1` → `1.2.0a1`) and a version cannot
be reused or overwritten — a bad upload costs a version number, always.

## Shipping types: `py.typed`

A package with annotations is invisible to a consumer's type checker unless it
ships a `py.typed` marker (PEP 561):

1. Create an empty `src/acme_orders/py.typed`.
2. Make sure the backend includes it in the wheel (package data for setuptools;
   `hatchling` and `uv_build` include package files by default).
3. Add the `Typing :: Typed` classifier so consumers can see it.
4. Verify from the built artifact, not the source tree: install the wheel into a
   throwaway environment and run the type checker against a file that imports it.

Partial annotations plus a marker is worse than no marker: consumers get
confidently wrong types. Either the public API is typed or the marker waits.

## Entry points

```toml
[project.scripts]
acme-report = "acme_orders.cli:main"        # console script

[project.gui-scripts]
acme-gui = "acme_orders.gui:main"

[project.entry-points."pytest11"]           # plugin registration
acme = "acme_orders.pytest_plugin"
```

The target is `module:callable`, the callable takes no arguments, and its return
value becomes the exit code — so `return 1` on failure, and let exceptions
propagate only when a traceback is the intended UX.

## Building and inspecting

```bash
uv build                                    # sdist + wheel into dist/
python -m zipfile -l dist/acme_orders-1.2.0-py3-none-any.whl
tar -tzf dist/acme_orders-1.2.0.tar.gz
uvx twine check dist/*                      # metadata renders on PyPI
```

Look at the listing every time. An empty wheel — one that contains only
`*.dist-info` — installs without error and imports nothing; it is the single most
common packaging failure and the only cheap detection is reading the file list.

Then install it somewhere clean:

```bash
uv run --isolated --no-project --with dist/acme_orders-1.2.0-py3-none-any.whl \
  python -c "import acme_orders; print(acme_orders.__version__)"
```

## Publishing

```bash
uv publish --publish-url https://test.pypi.org/legacy/ dist/*   # rehearse
uv publish dist/*
```

Rehearse on TestPyPI, install from there into a throwaway environment, and import
the package before touching the real index.

From CI, use Trusted Publishing (OIDC): configure the publisher on PyPI for the
repository and workflow, then upload with no stored credential at all.

```yaml
permissions:
  id-token: write          # required for OIDC; nothing else
steps:
  - run: uv build
  - run: uv publish        # no token
```

`permissions: id-token: write` is the whole mechanism — a long-lived API token in
repository secrets is exfiltratable by anything that can run a workflow, and it
does not expire.

Release order that avoids a published mistake: tag, let CI build, check the
artifact listing, publish, then verify the install from PyPI. Publishing before
verifying costs a version number.

## Common packaging failures

| Symptom | Cause |
|---|---|
| Wheel installs, `import` fails | package directory not picked up (missing src mapping, or no `__init__.py`) |
| Types not seen by consumers | no `py.typed`, or it was excluded from the wheel |
| Data files missing at runtime | not declared as package data; `MANIFEST.in` affects the sdist only |
| `pip install` builds from source unexpectedly | no wheel published, or platform tags do not match |
| Version differs between the tag and the metadata | two sources of truth for the version |
| Upload rejected as an existing file | that version already exists; versions are immutable |

<!-- sources: awesome-copilot-python, trailofbits-modern-python, wshobson-python, uv-docs, pypa-docs -->
