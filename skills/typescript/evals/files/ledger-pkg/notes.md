# @acme/ledger 3.4.0 — what happened

We replaced the `@/` path alias with Node subpath imports (`"#/*"` in package.json) because
"that is the standards way now". `npm run build` is green.

## Production (Docker image `node:22.23.3-bookworm-slim`, runs `npm start`)

```
TypeError [ERR_INVALID_MODULE_SPECIFIER]: Invalid module "#/money.js" is not a valid internal imports specifier name imported from /app/dist/index.js
  code: 'ERR_INVALID_MODULE_SPECIFIER'
```

## My laptop (Node 24.22.0, `npm run build && npm start`)

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/home/kim/ledger/money.js' imported from /home/kim/ledger/dist/index.js
  code: 'ERR_MODULE_NOT_FOUND',
  url: 'file:///home/kim/ledger/money.js'
```

## Declarations

We publish this package to the internal registry and want parallel declaration emit, so we
tried `"isolatedDeclarations": true` (it is set back to false in the attached tsconfig for now):

```
$ npx tsc -p . --pretty false
money.ts(5,10): error TS9013: Expression type can't be inferred with --isolatedDeclarations.
money.ts(12,14): error TS9010: Variable must have an explicit type annotation with --isolatedDeclarations.
```

A teammate suggests leaving `isolatedDeclarations` off for good.
