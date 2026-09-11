# nebula-queue — repository facts

```
nebula-queue/
  .github/
    workflows/
      tests.yml              name: tests
  assets/
    hero-dark.png            1280x640
    hero-light.png           1280x640
    demo.mp4                 14 MB, H.264
    arch.png                 does not exist; the file was never committed
  docs/
    quickstart.md
    configuration.md
  src/nebula_queue/
    __init__.py
    broker.py
    worker.py
  tests/
  LICENSE                    MIT
  pyproject.toml             (attached)
  README.md                  (attached)
```

Facts:

- GitHub repository: `orbitlabs/nebula-queue`. Default branch `main`.
- Published to PyPI as `nebula-queue`; `pyproject.toml` sets
  `readme = "README.md"`, so the file below is also the PyPI project page.
- The only CI workflow is `.github/workflows/tests.yml`, whose `name:` is `tests`.
- Coverage is not measured anywhere.
- The Discord invite in the README expired in 2024 and the server is gone.
- `assets/demo.mp4` was committed to the repository. `assets/demo.gif` does not
  exist.
- There is no `docs/architecture.md`.
- The maintainers read the project page on PyPI more often than on GitHub,
  because that is where their users land from `pip search` results and from
  links in other projects' dependency lists.
