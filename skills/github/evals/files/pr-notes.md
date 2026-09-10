# Draft notes for my PR

## Summary

- Fixed the bug
- Refactored some stuff

## Changes

- src/cache/key.ts
- src/cache/key.test.ts
- src/cache/index.ts
- src/server/handler.ts
- package.json
- package-lock.json

## Test Plan

```
$ npm test

> app@1.4.0 test
> vitest run

 ✓ src/cache/key.test.ts (14 tests) 231ms
 ✓ src/cache/index.test.ts (6 tests) 88ms
 ✓ src/server/handler.test.ts (22 tests) 412ms

 Test Files  3 passed (3)
      Tests  42 passed (42)
   Duration  1.94s
```

## Checklist

- [x] Tests pass
- [x] Lint passes
- [ ] Docs updated

## Notes to self

The real problem was that the cache key hashed the request body before
normalising header casing, so `Accept-Encoding` and `accept-encoding` produced
two different entries and the second request always missed. Reviewers should
start at `normaliseHeaders` in src/cache/key.ts. The handler change is only
plumbing the new key builder through.

Also: this is a breaking change for anyone who persisted cache keys across
restarts — old keys will not be found and will be recomputed once.
