#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Repack a directory produced by office_unpack.py back into an OOXML file.

Two things go wrong when people repack with a shell zip: entries pick up a
directory prefix (`d/word/document.xml`), which makes every consumer fail to
find `[Content_Types].xml`, and the content-types part drifts away from the
front of the archive. This writes relative paths only and puts
`[Content_Types].xml` first.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

MANIFEST = ".opc-manifest.json"
# OPC requires this part at the package root. Word tolerates it anywhere in the
# archive, but writing it first matches what Office itself produces.
CONTENT_TYPES = "[Content_Types].xml"


def collect(root: Path) -> list[str]:
    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and p.name != MANIFEST
    )


def ordered_entries(root: Path) -> list[str]:
    present = set(collect(root))
    manifest = root / MANIFEST
    order: list[str] = []
    if manifest.is_file():
        try:
            recorded = json.loads(manifest.read_text(encoding="utf-8")).get("entries", [])
        except (json.JSONDecodeError, OSError):
            recorded = []
        order = [name for name in recorded if name in present]
    remaining = sorted(present - set(order))
    entries = order + remaining
    if CONTENT_TYPES in entries:
        entries.remove(CONTENT_TYPES)
        entries.insert(0, CONTENT_TYPES)
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dir", help="directory holding the unpacked parts")
    ap.add_argument("out", help="OOXML file to write")
    args = ap.parse_args()

    root = Path(args.dir).expanduser()
    out = Path(args.out).expanduser()
    if not root.is_dir():
        print(f"error: {root} is not a directory.", file=sys.stderr)
        return 2

    entries = ordered_entries(root)
    if CONTENT_TYPES not in entries:
        print(
            f"error: {CONTENT_TYPES} is missing from {root}. Without it the file is not a "
            f"valid OOXML package - unpack the original again and edit the copy.",
            file=sys.stderr,
        )
        return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in entries:
            zf.write(root / name, name)

    print(f"packed {len(entries)} part(s) into {out}")
    print("verify next: reopen with the matching Python library, then render it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
