# Streaming responses

Verified against: FastAPI 0.141.

## Contents

- [Pick the shape first](#pick-the-shape-first)
- [Server-Sent Events](#server-sent-events)
- [JSON Lines](#json-lines)
- [Bytes and files](#bytes-and-files)
- [What breaks in a streaming handler](#what-breaks-in-a-streaming-handler)
- [WebSockets](#websockets)

## Pick the shape first

| Need | Use |
|---|---|
| server pushes events to a browser, browser only listens | SSE — `response_class=EventSourceResponse` |
| many records, one per line, consumed by a program | JSON Lines — declare `-> AsyncIterable[Model]` |
| a file, an image, a proxied byte stream | a `StreamingResponse` subclass as `response_class` |
| both directions, low latency | WebSocket |
| the whole payload fits in memory and the client waits anyway | none of the above — return the model |

Streaming costs you the response model's filtering guarantees at the envelope level and makes error
handling harder (below). Reach for it when the payload is unbounded or the first byte matters, not
to look modern.

## Server-Sent Events

```python
from collections.abc import AsyncIterable

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent

app = FastAPI()


@app.get("/events", response_class=EventSourceResponse)
async def stream_events() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(data={"status": "started"}, event="status", id="1")
    yield ServerSentEvent(data={"progress": 50}, event="progress", id="2")
```

`fastapi.sse` ships with FastAPI [verified against 0.141]; no third-party SSE package is needed.

- Set `response_class=EventSourceResponse` on the decorator and `yield` from the handler. Do not
  build the response object and return it — the decorator form is what gets documented.
- Yield plain objects or Pydantic models for the common case: they are JSON-encoded into `data:`
  automatically, and a declared return type means Pydantic does the encoding.
- Use `ServerSentEvent` when you need `event`, `id`, `retry` or `comment`. `raw_data=` sends a
  pre-formatted string with no JSON encoding.
- `id` is what the browser sends back as `Last-Event-ID` after a reconnect. Emit it if resuming
  matters, and handle that header on the way in; `EventSource` reconnects on its own and will
  otherwise replay from the beginning.

SSE is one-directional and text-only. A client that needs to send messages back wants a WebSocket,
not SSE plus a second endpoint.

## JSON Lines

Declare the item type and yield:

```python
@router.get("/items/stream")
async def stream_items() -> AsyncIterable[Item]:
    async for item in repository.iterate():
        yield item
```

Each item is validated against `Item` and emitted as one JSON object per line. This is the shape to
give a data consumer: it is resumable by line, needs no streaming JSON parser, and each record is
independently valid.

## Bytes and files

Subclass `StreamingResponse` to fix the media type, then use it as `response_class`:

```python
class PngStreamingResponse(StreamingResponse):
    media_type = "image/png"


@router.get("/thumbnail/{item_id}", response_class=PngStreamingResponse)
def thumbnail(item_id: int):
    with open_thumbnail(item_id) as f:
        yield from f
```

Prefer this to constructing and returning `StreamingResponse(...)`: the media type ends up in
OpenAPI, and the generator's lifetime is managed by FastAPI rather than by you.

A plain `def` handler is correct here — file IO blocks, so it belongs in the threadpool. For a file
already on disk that you are not transforming, `FileResponse` is better than streaming it yourself:
it sets `Content-Length` and supports range requests.

## What breaks in a streaming handler

- **Errors after the first byte.** Status and headers are already sent, so an exception mid-stream
  cannot become a 500 body. The client sees a truncated response. Validate everything you can
  before the first `yield`, and give the stream an explicit terminal event (`event="error"` or a
  final line with a status field) so a consumer can tell truncation from completion.
- **Dependencies with the default `scope`.** A `yield` dependency's exit code runs after the
  response is sent, which for a stream means after the last byte. A database session held that way
  is held for the whole stream. That is exactly right if you are streaming rows from it, and a
  connection-pool leak if you are not — switch that dependency to `scope="function"`.
- **Response models.** `response_model` describes the item type, not the stream. Document the
  content type with `responses={200: {"content": {"text/event-stream": {}}}}` so a generated client
  does not try to parse the whole thing as one JSON document.
- **Buffering upstream.** Proxies and CDNs may buffer, which turns a stream into a slow single
  response. Disable buffering for the route at the proxy (`X-Accel-Buffering: no` for nginx) and
  verify with `curl -N`, not in a browser devtools panel that batches.
- **`BaseHTTPMiddleware`.** Middleware that reads the request or response body interacts badly with
  streaming; keep streaming routes out from under it.

## WebSockets

```python
@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async for message in websocket.iter_text():
            await websocket.send_text(process(message))
    except WebSocketDisconnect:
        pass
```

Use `async for` over the iterator rather than `while True: await receive_text()`, and let
`WebSocketDisconnect` end the handler — a client closing the tab is normal traffic, not an error
worth logging at error level.

Dependencies work in WebSocket handlers, but `HTTPException` does not — the handshake has no place
to put a 401 body. Raise `WebSocketException(code=status.WS_1008_POLICY_VIOLATION)` from the
dependency instead, or `await websocket.close(code=1008)` inside the handler.

<!-- sources: fastapi-official-skill, fastapi-docs, starlette-docs, kludex-fastapi-tips -->
