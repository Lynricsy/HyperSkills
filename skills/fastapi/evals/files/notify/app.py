"""notify-api: live order events for the dashboard."""

import asyncio
from typing import Annotated

from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

EVENTS: asyncio.Queue[str] = asyncio.Queue()


def user_from_token(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    return token.removeprefix("user-")


@app.get("/events")
async def events() -> StreamingResponse:
    async def stream():
        n = 0
        while True:  # the dashboard keeps this open all day
            yield f"data: tick {n}\n\n"
            n += 1
            await asyncio.sleep(1)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.websocket("/ws/orders")
async def orders_ws(ws: WebSocket, user: Annotated[str, Depends(user_from_token)]) -> None:
    await ws.accept()
    await ws.send_text(f"hello {user}")
    while True:
        await ws.send_text(await EVENTS.get())
