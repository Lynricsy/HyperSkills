# API reference

## `corral.Client`

```python
Client(base_url, *, timeout=30.0, max_retries=5, retry_on=None, backoff="exponential", limiter=None)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `base_url` | `str` | — | Upstream base URL. Trailing slashes are stripped. |
| `timeout` | `float` | `30.0` | Per-attempt timeout in seconds. |
| `max_retries` | `int` | `5` | Number of retries after the first attempt. |
| `retry_on` | `list[int] \| None` | `None` | Status codes that trigger a retry. `None` means `[429, 500, 502, 503]`. |
| `backoff` | `str` | `"exponential"` | One of `"exponential"`, `"linear"`, `"none"`. |
| `limiter` | `Limiter \| None` | `None` | Defaults to an in-process `TokenBucket(rate=5.0, capacity=10)`. |

### `Client.fetch(path, *, body=None)`

Sends a `GET` request to `path` and returns a `Response`.

### `Client.close()`

Releases the connection pool.

## `corral.Response`

| Field | Type | Description |
|---|---|---|
| `status` | `int` | HTTP status code. |
| `body` | `bytes` | Response body. |
| `retries` | `int` | How many retries were needed. |

## `corral.limiter.TokenBucket`

```python
TokenBucket(rate=5.0, capacity=10)
```

In-process token bucket. `rate` is tokens per second, `capacity` is the
ceiling.

## `corral.limiter.RedisLimiter`

```python
RedisLimiter(url, key, *, rate=5.0, capacity=10)
```

Token bucket shared across processes. Included in the base install.

## Exceptions

| Exception | Raised when |
|---|---|
| `corral.CorralError` | Base class. |
| `corral.RateLimitError` | The upstream returned 429 and no retries were left. |
| `corral.CorralTimeout` | A single attempt exceeded `timeout`. |

## Environment variables

| Variable | Description |
|---|---|
| `CORRAL_API_KEY` | Bearer token used when `token` is not passed. |
| `CORRAL_TIMEOUT` | Overrides the default timeout. |
