# driftwood

[![CI](https://img.shields.io/github/actions/workflow/status/hallowbay/driftwood/ci.yml?branch=main)](https://github.com/hallowbay/driftwood/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/driftwood)](https://pypi.org/project/driftwood/)
[![License](https://img.shields.io/pypi/l/driftwood)](LICENSE)

Driftwood is a blazing-fast, next-generation schema migration toolkit that
provides a seamless and intuitive experience for teams working with
ever-evolving database landscapes. In today's fast-paced development
environment, managing schema change has become increasingly crucial — and
Driftwood stands as a testament to what modern tooling can achieve, empowering
developers to ship with confidence.

It's not just a migration runner — it's a philosophy. Built from the ground up
with correctness in mind, Driftwood delivers speed, reliability, and
performance, ensuring that your migrations are robust, scalable, and
production-ready from day one.

## Features

- **Blazing fast** — leverages a cutting-edge planner for optimal performance
- **Rock solid** — comprehensive safety checks, ensuring nothing breaks
- **Developer friendly** — an intuitive API that just works
- **Battle tested** — trusted by teams across the ecosystem
- **Future proof** — continuously evolving to meet tomorrow's needs

## Installation

To get started with installing the library, you'll want to utilize pip, which
is the package manager that comes bundled with Python. Simply run the following
command in order to install the package, thereby making it available throughout
your environment:

```sh
pip install driftwood
```

## Usage

Here's a breakdown of how to use Driftwood. First, you'll want to initialise a
migration directory — this is where all of your migration files will live,
serving as the single source of truth for your schema's journey over time.

```sh
driftwood init migrations/
driftwood plan --database "$DATABASE_URL"
driftwood apply --database "$DATABASE_URL"
```

The `plan` command analyses your schema, highlighting the differences between
the current state and the desired state, while `apply` executes the plan,
ensuring that every statement runs inside a single transaction.

## Performance

Driftwood is incredibly fast. Benchmarks demonstrate that it significantly
outperforms comparable tools, delivering substantial improvements across the
board and underscoring its position as a leader in the space.

## Contributing

We welcome contributions from the community! Feel free to open an issue or
submit a pull request. Together, we can make Driftwood even better. Let me know
if you need any clarification on the process.

## Roadmap

The future is bright for Driftwood. As we continue on this exciting journey, we
look forward to delivering even more value to our growing community of users.
Exciting times ahead!

## License

MIT
