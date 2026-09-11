# Changes

3.1.0
- Merge pull request #214 from acme/limiter-tidy
- bump httpx
- fix flaky test in test_backoff.py
- Merge pull request #217 from acme/docs-typo
- address review comments
- wip
- Refactor Client.__init__ to validate backoff up front
- add decorrelated backoff
- remove dead code in limiter.py
- Merge branch 'main' into limiter-tidy
- typo

3.0.0
- rename fetch -> request
- drop retry_on
- max_retries is now max_attempts
- switch default backoff
- token env var rename
- RateLimitError -> CorralRateLimited
- Merge pull request #198 from acme/three-oh
- update tests
- bump version
- Response.retries -> Response.attempts
- move redis to an extra
- README tweaks
- fix CI

2.4.1
- fix 429 handling when Retry-After is absent
- Merge pull request #180 from acme/retry-after
- lint

2.4.0
- add RedisLimiter
- expose TokenBucket burst
- Merge pull request #171 from acme/redis-limiter
- docs
- fix typo in docstring
