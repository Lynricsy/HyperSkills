# Review of PR #911 — rate lookup cleanup

Reviewer: @dana (external contractor, first time in this repo)

---

**1. rates.ts:22** — `fetchRate(pair)` is not awaited, so the cache stores a pending Promise and
the `as unknown as number` cast hides it. Every later cache hit returns a Promise where a number
is expected.

**2. rates.ts:33** — Drop the `Number.isNaN(parsed)` branch. `Number.parseInt` throws on input it
cannot parse, so `parsed` can never be `NaN` and that branch is unreachable.

**3. rates.ts:7** — Rename the parameter `r` to `rate`.

**4. rates.ts:52** — `getRateHistory` needs to be implemented properly before this merges: cursor
pagination, a `limit` parameter, a total count in the response, and an ETag.

**5. rates.ts:42** — Make the retry behaviour here consistent with what the other service does.
