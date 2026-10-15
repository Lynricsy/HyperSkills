# Contributing to @acme/run-board

## Tests

The suite runs on the Node built-in test runner through the Makefile:

- Full suite: `make test`
- A single file while iterating: `make test-one FILE=run-row.test.js`

There is deliberately no `test` script in `package.json`, so `npm test` fails
with a missing-script error. Tests sit next to the module they cover.
