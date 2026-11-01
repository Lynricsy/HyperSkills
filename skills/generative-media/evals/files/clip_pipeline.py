"""Product-teaser clip pipeline (Gemini API, developer key).

Every night: one 8-second 1080p clip per SKU, then the editor job re-downloads
the clips it needs from the provider the next morning (they keep them for two days).
Since 2026-10-23 every submission fails with a 404 "model not found". Ops just
reran it in a loop all weekend.
"""

import time

from google import genai
from google.genai import types

client = genai.Client()

MODEL = "veo-3.1-generate-preview"


def submit(sku: str, prompt: str) -> str:
    operation = client.models.generate_videos(
        model=MODEL,
        prompt=prompt,
        config=types.GenerateVideosConfig(
            duration_seconds=8, resolution="1080p", aspect_ratio="16:9", number_of_videos=1
        ),
    )
    return operation.name


def wait(name: str) -> str:
    while True:
        op = client.operations.get(types.GenerateVideosOperation(name=name))
        if op.done:
            # The editor job downloads from this URI tomorrow morning.
            return op.response.generated_videos[0].video.uri
        time.sleep(10)


def nightly(skus: dict[str, str]) -> dict[str, str]:
    out = {}
    for sku, prompt in skus.items():
        for _ in range(50):
            try:
                out[sku] = wait(submit(sku, prompt))
                break
            except Exception:
                time.sleep(30)
    return out
