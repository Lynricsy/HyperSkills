# Contributing to @acme/duration

## Tests

The suite runs on the Node built-in test runner through the Makefile:

- Full suite: `make test`
- A single file while iterating: `make test-one FILE=duration.test.js`

There is deliberately no `test` script in `package.json`, so `npm test` fails
with a missing-script error.

## Errors

Every error this package throws on bad input is a `DurationError` exported
from `duration.js`, so callers can tell bad input apart from bugs.
