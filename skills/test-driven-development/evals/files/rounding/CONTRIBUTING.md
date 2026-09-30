# Contributing to @acme/rounding

## Tests

The suite runs on the Node built-in test runner through the Makefile:

- Full suite: `make test`
- A single file while iterating: `make test-one FILE=rounding.test.js`

There is deliberately no `test` script in `package.json`, so `npm test` fails
with a missing-script error. Test files sit next to the module they cover and
are named `<module>.test.js`.

## Tickets

Keep each change to the files its ticket names. Anything else you notice goes
in your report, not in the diff: another ticket owns it.
