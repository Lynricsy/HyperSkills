"""Order-events consumer and page-view counter.

Pinned: redis==8.1.0 (upgraded from redis==7.4.1 last week). Server: Redis 8.10, one primary
plus one replica behind Sentinel, maxclients 10000.

Incidents since the client upgrade:

1. The consumer logs `redis.exceptions.TimeoutError: Timeout reading from socket` about once
   a minute whenever the queue is quiet, reconnects, and carries on. It never did this on 7.4.
2. During the 09:00 burst the API returns 500s with
   `redis.exceptions.MaxConnectionsError: Too many connections`, yet INFO on the server shows
   connected_clients around 140 and rejected_connections 0.
3. After last Tuesday's failover the page_views counters were higher than the access-log
   counts for the same minutes.

We have 6 API pods and 2 consumer pods.
"""

import asyncio

import redis
import redis.asyncio as aioredis

r = redis.Redis(host="redis.internal", port=6379)
ar = aioredis.Redis(host="redis.internal", port=6379)


def consume_forever(handle):
    while True:
        item = r.blpop("queue:order-events", timeout=30)
        if item:
            handle(item[1])


async def record_view(page_id: str) -> None:
    await ar.incr(f"page_views:{page_id}")


async def handle_burst(page_ids: list[str]) -> None:
    # Up to ~2,000 page ids per burst batch.
    await asyncio.gather(*(record_view(p) for p in page_ids))
