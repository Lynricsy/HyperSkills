#!/usr/bin/env python3
"""Re-stage catalogue photos into seasonal scenes.

Product must stay exactly as photographed — only the background changes.
We paint a mask over everything except the product and let the model fill
it. Output goes straight onto the EU storefront.
"""

import base64
import os
from pathlib import Path

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PHOTOS = Path("photos")
MASKS = Path("masks")  # transparent where the model may paint
STORE = Path("../storefront/public/products")


def restage(photo: Path, scene: str) -> bytes:
    with photo.open("rb") as img, (MASKS / photo.name).open("rb") as mask:
        result = client.images.edit(
            model="gpt-image-1",
            image=img,
            mask=mask,
            prompt=f"place the product in {scene}",
            size="1024x1024",
        )
    return base64.b64decode(result.data[0].b64_json)


def main() -> None:
    STORE.mkdir(parents=True, exist_ok=True)
    for photo in sorted(PHOTOS.glob("*.png")):
        out = STORE / photo.name
        out.write_bytes(restage(photo, "an autumn kitchen"))
        # shrink for the product grid
        os.system(f"npx sharp-cli -i {out} -o {out} resize 1200")
        print(f"published {out}")


if __name__ == "__main__":
    main()
