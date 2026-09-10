#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Unpack an OOXML file (docx/pptx/xlsx) into a directory for XML editing.

Records the original entry order in a manifest so office_pack.py can rebuild a
package that matches the input byte layout instead of an alphabetical guess.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

# Written next to the extracted parts. office_pack.py reads it and never packs
# it; the leading dot keeps it out of glob patterns that collect XML parts.
MANIFEST = ".opc-manifest.json"
OOXML_SUFFIXES = {".docx", ".docm", ".dotx", ".pptx", ".pptm", ".potx", ".xlsx", ".xlsm", ".xltx"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="OOXML file to unpack")
    ap.add_argument("dest", help="directory to unpack into (created if absent)")
    ap.add_argument("--force", action="store_true", help="allow a non-empty destination")
    args = ap.parse_args()

    src = Path(args.file).expanduser()
    dest = Path(args.dest).expanduser()
    if not src.exists():
        print(f"error: {src} does not exist.", file=sys.stderr)
        return 2
    if src.suffix.lower() not in OOXML_SUFFIXES:
        print(
            f"error: '{src.suffix}' is not an OOXML package. Supported: "
            f"{', '.join(sorted(OOXML_SUFFIXES))}",
            file=sys.stderr,
        )
        return 2
    if not zipfile.is_zipfile(src):
        print(f"error: {src.name} is not a zip archive - it is not a valid OOXML file.", file=sys.stderr)
        return 2
    if dest.exists() and any(dest.iterdir()) and not args.force:
        print(f"error: {dest} is not empty. Pass --force to unpack into it anyway.", file=sys.stderr)
        return 2

    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as zf:
        entries = [info.filename for info in zf.infolist() if not info.is_dir()]
        zf.extractall(dest)
    (dest / MANIFEST).write_text(
        json.dumps({"source": src.name, "entries": entries}, indent=2), encoding="utf-8"
    )

    print(f"unpacked {len(entries)} part(s) into {dest}")
    print(f"entry order recorded in {dest / MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
