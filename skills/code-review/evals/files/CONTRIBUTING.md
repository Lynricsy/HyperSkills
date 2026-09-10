# Contributing

## Coding standards

1. **SQL is always parameterized.** Pass values as `$1`-style placeholders to `pool.query`.
   Never build a statement by concatenating or interpolating request data.
2. **Validate at the boundary.** Every exported handler validates the request fields it reads
   before they reach the database layer, and rejects with a 4xx.
3. **A test must be able to fail.** Do not weaken or delete an assertion to make a suite green;
   if behaviour changed on purpose, change the expected value, not the assertion.
4. **One concern per pull request.** Refactors and behaviour changes ship separately.
5. `npm test` and `npm run lint` must pass before review. Formatting is handled by Prettier
   on commit, so formatting is never a review topic.
