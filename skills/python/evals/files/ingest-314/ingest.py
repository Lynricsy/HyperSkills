"""Nightly ingest: pull batches from the export API, score them, write results.

Ran fine for a year on Python 3.12. After the base image moved to
python:3.14-slim (Debian), the job dies right at startup, and when we patch
around that the scores all come back as zero.
"""

import asyncio
import json
import sys
from concurrent.futures import ProcessPoolExecutor

import httpx

WEIGHTS: dict[str, float] = {}
WORKERS = 8


def score(record: dict) -> float:
    # CPU-heavy scoring, so it runs in the process pool.
    total = 0.0
    for key, value in record["features"].items():
        total += WEIGHTS.get(key, 0.0) * value
    return total


async def fetch_batches(client: httpx.AsyncClient, queue: asyncio.Queue) -> None:
    page = 0
    while True:
        resp = await client.get("/export", params={"page": page})
        batch = resp.json()["records"]
        if not batch:
            break
        for record in batch:
            await queue.put(record)
        page += 1
    for _ in range(WORKERS):
        await queue.put(None)  # one stop marker per worker


async def worker(queue: asyncio.Queue, pool: ProcessPoolExecutor, out: list) -> None:
    loop = asyncio.get_event_loop()
    while True:
        record = await queue.get()
        if record is None:
            break
        value = await loop.run_in_executor(pool, score, record)
        out.append({"id": record["id"], "score": value})


async def run(out: list) -> None:
    queue: asyncio.Queue = asyncio.Queue()
    with ProcessPoolExecutor() as pool:
        async with httpx.AsyncClient(base_url="https://export.internal") as client:
            asyncio.create_task(fetch_batches(client, queue))
            await asyncio.gather(*(worker(queue, pool, out) for _ in range(WORKERS)))


def main() -> None:
    with open(sys.argv[1]) as fh:
        WEIGHTS.update(json.load(fh))
    out: list = []
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(out))
    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
