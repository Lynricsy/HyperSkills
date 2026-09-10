# Contributing to @acme/slug

## Tests

The suite runs on the Node built-in test runner through the Makefile:

- Full suite: `make test`
- A single file while iterating: `make test-one FILE=slug.test.js`

There is deliberately no `test` script in `package.json` — the npm scripts only
cover linting, so `npm test` fails with a missing-script error. Test files sit
next to the module they cover and are named `<module>.test.js`.

## Invariants

- A slug is safe to put in a URL path segment unescaped.
- Every reported bug gets a test that reproduces it.
