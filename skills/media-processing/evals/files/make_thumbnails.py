#!/usr/bin/env python3
"""Build catalogue thumbnails from the photographers' JPEG drops.

Photos arrive straight from phones and DSLRs: portrait shots are stored
landscape with an EXIF Orientation tag, and some studio shots are tagged
Display-P3. Output goes to the product pages at 400px wide.
"""

import subprocess
import sys
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "photos")
DST = Path(sys.argv[2] if len(sys.argv) > 2 else "thumbs")
WIDTH = 400


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC.glob("*.jpg")):
        dst = DST / src.name
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(src),
                "-vf", f"scale={WIDTH}:-1",
                "-q:v", "2",
                str(dst),
            ],
            check=True,
        )
        print(f"{src.name} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
