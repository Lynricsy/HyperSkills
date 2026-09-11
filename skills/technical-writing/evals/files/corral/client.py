"""HTTP client with retries and rate limiting."""

from __future__ import annotations

import os
from dataclasses import dataclass

from corral.limiter import Limiter, TokenBucket

# 10s: long enough for a cold serverless origin, short enough that a stuck
# request does not pin a worker for a whole minute.
DEFAULT_TIMEOUT_SECONDS = 10.0
# 3 attempts total, not 3 retries after the first attempt.
DEFAULT_MAX_ATTEMPTS = 3
# Env var read when `token` is not passed explicitly.
TOKEN_ENV_VAR = "CORRAL_TOKEN"

BACKOFF_STRATEGIES = ("full_jitter", "decorrelated")


class CorralError(Exception):
    """Base class for every error this package raises."""


class CorralRateLimited(CorralError):
    """Raised when the server returned 429 and no attempts are left."""

    def __init__(self, retry_after: float | None) -> None:
        super().__init__(f"rate limited; retry after {retry_after}s")
        self.retry_after = retry_after


class CorralTimeout(CorralError):
    """Raised when a single attempt exceeded `timeout`."""


@dataclass(slots=True)
class Response:
    status: int
    body: bytes
    attempts: int


class Client:
    """Synchronous HTTP client.

    `backoff` must be one of BACKOFF_STRATEGIES. The `retry_on` parameter was
    removed in 3.0: retries now key off the status class and the presence of a
    `Retry-After` header, which is what every origin we tested actually sends.
    """

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff: str = "full_jitter",
        limiter: Limiter | None = None,
    ) -> None:
        if backoff not in BACKOFF_STRATEGIES:
            raise ValueError(f"backoff must be one of {BACKOFF_STRATEGIES}")
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get(TOKEN_ENV_VAR)
        if not self.token:
            raise CorralError(
                f"no token: pass token= or set {TOKEN_ENV_VAR} in the environment"
            )
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff = backoff
        self.limiter = limiter or TokenBucket(rate=5.0, burst=10)

    def request(self, method: str, path: str, *, body: bytes | None = None) -> Response:
        """Send one request, retrying up to `max_attempts` times.

        Renamed from `fetch()` in 3.0 so that the verb matches the HTTP method
        argument it now takes.
        """
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
