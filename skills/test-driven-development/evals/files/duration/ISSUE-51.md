# #51 parseDuration silently returns NaN for unknown units

`parseDuration('5x')` returns `NaN`. The scheduler then stores `NaN` as the
retry delay and the job retries in a hot loop.

Expected: any input that is not `<integer><unit>` with a unit of `ms`, `s`,
`m` or `h` throws a `DurationError` (see CONTRIBUTING.md). `DurationError`
does not exist yet; export it from `duration.js` as part of this fix.
