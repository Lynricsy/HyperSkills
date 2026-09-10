#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Render an Office or PDF file to page images for visual inspection.

docx/pptx/xlsx go through LibreOffice to PDF first; PDFs are rasterised
directly. Prints one PNG path per line so the caller can open them in order.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# LibreOffice reads and writes a user profile at startup. If another soffice
# process already holds the default profile the headless convert exits 0 having
# produced nothing, so every run gets its own throwaway profile directory.
PROFILE_ENV = "-env:UserInstallation=file://{path}"
# 100 dpi keeps a Letter page near 850x1100 px: text is legible for layout
# review while a 20-page deck stays a few megabytes.
DEFAULT_DPI = 100
# A conversion of a large deck on a cold LibreOffice profile takes ~10-20s;
# 180s is generous without hanging a pipeline on a wedged process.
SOFFICE_TIMEOUT = 180
OFFICE_SUFFIXES = {".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".odt", ".odp", ".ods", ".rtf"}


def need(tool: str, hint: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"error: '{tool}' not found on PATH. {hint}")
    return path


def to_pdf(src: Path, workdir: Path) -> Path:
    soffice = need("soffice", "Install LibreOffice (apt install libreoffice / brew install --cask libreoffice).")
    profile = workdir / "lo-profile"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        PROFILE_ENV.format(path=profile),
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(workdir),
        str(src),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=SOFFICE_TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.exit(f"error: LibreOffice did not finish converting {src.name} within {SOFFICE_TIMEOUT}s.")
    out = workdir / (src.stem + ".pdf")
    if not out.exists():
        detail = (proc.stderr or proc.stdout or "").strip()[:500]
        sys.exit(
            f"error: LibreOffice produced no PDF for {src.name}. "
            f"The file is usually malformed when this happens.\n{detail}"
        )
    return out


def rasterise(pdf: Path, outdir: Path, dpi: int, first: int | None, last: int | None) -> list[Path]:
    pdftoppm = need("pdftoppm", "Install poppler-utils (apt install poppler-utils / brew install poppler).")
    prefix = outdir / pdf.stem
    cmd = [pdftoppm, "-r", str(dpi), "-png"]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    cmd += [str(pdf), str(prefix)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    images = sorted(outdir.glob(f"{pdf.stem}-*.png"))
    if not images:
        detail = (proc.stderr or "").strip()[:500]
        sys.exit(f"error: pdftoppm produced no images for {pdf.name}.\n{detail}")
    return images


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="docx/pptx/xlsx/pdf to render")
    ap.add_argument("--outdir", help="where to write PNGs (default: alongside the input)")
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI, help=f"raster resolution (default {DEFAULT_DPI})")
    ap.add_argument("--first", type=int, help="first page to render")
    ap.add_argument("--last", type=int, help="last page to render")
    args = ap.parse_args()

    src = Path(args.file).expanduser()
    if not src.exists():
        sys.exit(f"error: {src} does not exist.")
    if src.suffix.lower() not in OFFICE_SUFFIXES | {".pdf"}:
        sys.exit(
            f"error: don't know how to render '{src.suffix}'. "
            f"Supported: {', '.join(sorted(OFFICE_SUFFIXES | {'.pdf'}))}"
        )

    outdir = Path(args.outdir).expanduser() if args.outdir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="render-preview-") as tmp:
        workdir = Path(tmp)
        pdf = src if src.suffix.lower() == ".pdf" else to_pdf(src, workdir)
        images = rasterise(pdf, outdir, args.dpi, args.first, args.last)

    for image in images:
        print(os.fspath(image))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
