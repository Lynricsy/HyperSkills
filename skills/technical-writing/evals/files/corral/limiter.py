"""Rate limiters."""

from __future__ import annotations

from typing import Protocol


class Limiter(Protocol):
    def acquire(self, cost: float = 1.0) -> float:
        """Block until `cost` tokens are available; return seconds waited."""


class TokenBucket:
    """In-process token bucket.

    `rate` is tokens added per second; `burst` is the ceiling the bucket fills
    to. A single process only.
    """

    def __init__(self, rate: float = 5.0, burst: int = 10) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if burst < 1:
            raise ValueError("burst must be at least 1")
        self.rate = rate
        self.burst = burst

    def acquire(self, cost: float = 1.0) -> float:
        raise NotImplementedError


class RedisLimiter:
    """Token bucket shared by every process pointed at the same Redis key.

    Requires the optional `redis` dependency:

        pip install 'corral[redis]'
    """

    def __init__(self, url: str, key: str, *, rate: float = 5.0, burst: int = 10) -> None:
        try:
            import redis  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "RedisLimiter needs the redis extra: pip install 'corral[redis]'"
            ) from exc
        self.url = url
        self.key = key
        self.rate = rate
        self.burst = burst

    def acquire(self, cost: float = 1.0) -> float:
        raise NotImplementedError
