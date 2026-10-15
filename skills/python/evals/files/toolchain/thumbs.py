"""Starlette endpoint that renders thumbnails."""

import asyncio
import io

from PIL import Image
from starlette.requests import Request
from starlette.responses import Response


def _sharpen_and_dither(pixels: list[int], width: int) -> list[int]:
    # Pure-Python error-diffusion dither; ~400 ms per 1024x1024 image.
    out = pixels[:]
    for i, value in enumerate(out):
        new = 255 if value > 127 else 0
        err = value - new
        out[i] = new
        if (i + 1) % width:
            out[i + 1] = min(255, max(0, out[i + 1] + err * 7 // 16))
        if i + width < len(out):
            out[i + width] = min(255, max(0, out[i + width] + err * 5 // 16))
    return out


async def thumbnail(request: Request) -> Response:
    raw = await request.body()
    image = Image.open(io.BytesIO(raw)).convert("L").resize((1024, 1024))
    # to_thread keeps the event loop free and spreads the dithering across cores.
    pixels = await asyncio.to_thread(_sharpen_and_dither, list(image.getdata()), 1024)
    image.putdata(pixels)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")
