# Contributing to @acme/money

## Tests

The suite runs on the Node built-in test runner through the Makefile:

- Full suite: `make test`
- A single file while iterating: `make test-one FILE=money.test.js`

There is deliberately no `test` script in `package.json` — the npm scripts only
cover linting, so `npm test` fails with a missing-script error. Test files sit
next to the module they cover and are named `<module>.test.js`.

## Invariants

- Amounts are integer cents everywhere. Floating-point money is a bug.
- Every exported function has tests for the empty, boundary and negative case.
