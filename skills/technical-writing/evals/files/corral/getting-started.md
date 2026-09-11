# Getting started with corral

This guide gets you from nothing to a working shared rate limiter.

## Step 1 — Install

```
pip install corral
```

## Step 2 — Create a client

```python
from corral import Client

client = Client("https://api.example.com")
```

## Step 3 — Add the shared limiter

```python
from corral import Client
from corral.limiter import RedisLimiter

limiter = RedisLimiter("redis://localhost:6379", key="demo", capacity=10)
client = Client("https://api.example.com", limiter=limiter)
```

## Step 4 — Make some requests

```python
for i in range(20):
    r = client.fetch("/ping")
    ...
```

## Step 5 — Watch the limiter work

Run the script in two terminals at once. Notice how the two processes share the
budget.

## Step 6 — Tune it

```python
client = Client(
    "https://api.example.com",
    max_retries=5,
    retry_on=[429, 503],
    backoff="exponential",
)
```

## Step 7 — Production

Once it works locally, deploy it. Configure the limiter to point at your
production Redis, set the appropriate environment variables, and you are done.
