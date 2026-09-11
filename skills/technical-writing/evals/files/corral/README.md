# corral

corral is an HTTP client for Python.

## Installation

```
pip install corral
```

## Why rate limiting is hard

Before we get into the API it is worth understanding the problem. When several
workers talk to the same upstream, each one only knows about its own traffic.
Suppose you run eight workers and the upstream allows 100 requests a minute.
If every worker limits itself to 100 requests a minute you will send 800. The
naive fix is to divide the budget by the worker count, but worker counts change
during a deploy, and a worker that is idle wastes its share while a busy one
gets throttled. This is the same class of problem as the thundering herd, and
it is why a token bucket is usually described in terms of a *rate* (how fast
the budget refills) and a *capacity* (how much unused budget you are allowed to
hoard). A shared bucket, held somewhere both workers can see, is the only
arrangement that actually holds the total below the upstream's limit, and that
is what corral's Redis backend gives you. Some teams instead put a proxy in
front of the upstream; that works too, but then the proxy becomes a thing you
operate, and the retry logic ends up split across two codebases, which is how
you get a client that retries a request the proxy has already retried.

## Options

| Option | Type | Default | Description |
|---|---|---|---|
| `base_url` | str | — | Upstream base URL |
| `timeout` | float | `30.0` | Per-attempt timeout in seconds |
| `max_retries` | int | `5` | Retries after the first attempt |
| `retry_on` | list[int] | `[429, 500, 502, 503]` | Status codes that trigger a retry |
| `backoff` | str | `"exponential"` | One of `"exponential"`, `"linear"` |
| `limiter` | Limiter | `None` | Rate limiter instance |

## Let's build a price scraper

Now we will build something real. First make a project:

```
mkdir scraper && cd scraper
python -m venv .venv && source .venv/bin/activate
```

Then install corral and write the scraper:

```python
from corral import Client

client = Client("https://api.example.com")
for sku in ["a", "b", "c"]:
    r = client.fetch(f"/price/{sku}")
    print(r.status, r.body)
```

You should see three lines of output. If you want the shared limiter, point it
at Redis:

```python
from corral.limiter import RedisLimiter

client = Client(
    "https://api.example.com",
    limiter=RedisLimiter("redis://localhost:6379", key="prices", capacity=10),
)
```

That is basically all there is to it. From here you can add concurrency, but
that is out of scope for this README.

## Authentication

Set `CORRAL_API_KEY` in your environment. The client reads it at construction
time.

## Errors

`RateLimitError` is raised when the upstream keeps returning 429. Catch
`CorralError` if you want to catch everything.

## Development

```
make docs-serve       # serve the docs site locally
npm run docs          # build the docs site
make test             # run the test suite
```

## Where to go next

Read `docs/getting-started.md` for the tutorial, `docs/reference.md` for the
full reference, and `docs/concepts.md` for the design discussion.

## More on installation

If you are on Windows, use `py -m pip install corral`. The CLI is installed as
`corral-cli` and takes the same options as the constructor.
