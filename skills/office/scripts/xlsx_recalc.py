#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1"]
# ///
"""Recalculate a workbook with LibreOffice and report cells that error out.

openpyxl writes formula strings without evaluating them, so a workbook it
produced carries no cached values at all: every formula is unverified until
something recalculates it. This converts the file with LibreOffice (which
recalculates on load) and scans the result for error values.

Exit codes: 0 clean, 1 errors or uncomputed formulas found, 2 tooling problem.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook

# Every Excel error literal a recalculation can leave in a cell. #SPILL! and
# #CALC! only appear for dynamic-array formulas; the rest predate Excel 2007.
ERROR_VALUES = frozenset(
    {
        "#DIV/0!",
        "#N/A",
        "#NAME?",
        "#NULL!",
        "#NUM!",
        "#REF!",
        "#VALUE!",
        "#SPILL!",
        "#CALC!",
        "#GETTING_DATA",
    }
)
# See render_preview.py: a private LibreOffice profile is the difference between
# a real conversion and a silent no-op when another soffice is already running.
PROFILE_ENV = "-env:UserInstallation=file://{path}"
# Recalculating a formula-heavy model is slower than a plain render.
SOFFICE_TIMEOUT = 300


def recalculate(src: Path, workdir: Path) -> Path:
    soffice = shutil.which("soffice")
    if not soffice:
        print(
            "error: 'soffice' not found on PATH. Install LibreOffice "
            "(apt install libreoffice / brew install --cask libreoffice).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    profile = workdir / "lo-profile"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        PROFILE_ENV.format(path=profile),
        "--headless",
        "--norestore",
        "--convert-to",
        "xlsx",
        "--outdir",
        str(workdir),
        str(src),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=SOFFICE_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"error: LibreOffice did not finish recalculating within {SOFFICE_TIMEOUT}s.", file=sys.stderr)
        raise SystemExit(2) from None
    out = workdir / (src.stem + ".xlsx")
    if not out.exists():
        detail = (proc.stderr or proc.stdout or "").strip()[:500]
        print(f"error: LibreOffice produced no output for {src.name}.\n{detail}", file=sys.stderr)
        raise SystemExit(2)
    return out


def scan(recalced: Path) -> tuple[list[dict[str, str]], int]:
    values = load_workbook(recalced, data_only=True)
    formulas = load_workbook(recalced, data_only=False)
    findings: list[dict[str, str]] = []
    formula_count = 0
    for name in formulas.sheetnames:
        fsheet = formulas[name]
        vsheet = values[name]
        for row in fsheet.iter_rows():
            for cell in row:
                formula = cell.value
                if not isinstance(formula, str) or not formula.startswith("="):
                    continue
                formula_count += 1
                result = vsheet[cell.coordinate].value
                if isinstance(result, str) and result.strip() in ERROR_VALUES:
                    findings.append(
                        {
                            "sheet": name,
                            "cell": cell.coordinate,
                            "formula": formula,
                            "result": result.strip(),
                        }
                    )
                elif result is None:
                    findings.append(
                        {
                            "sheet": name,
                            "cell": cell.coordinate,
                            "formula": formula,
                            "result": "NOT COMPUTED",
                        }
                    )
    return findings, formula_count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help=".xlsx workbook to recalculate")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--keep", help="also write the recalculated copy here")
    args = ap.parse_args()

    src = Path(args.file).expanduser()
    if not src.exists():
        print(f"error: {src} does not exist.", file=sys.stderr)
        return 2
    if src.suffix.lower() != ".xlsx":
        print(f"error: expected an .xlsx file, got '{src.suffix}'.", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="xlsx-recalc-") as tmp:
        workdir = Path(tmp)
        recalced = recalculate(src, workdir)
        findings, formula_count = scan(recalced)
        if args.keep:
            shutil.copy2(recalced, Path(args.keep).expanduser())

    if args.json:
        print(json.dumps({"file": str(src), "formulas": formula_count, "findings": findings}, indent=2))
    else:
        print(f"{src.name}: {formula_count} formula cell(s) recalculated, {len(findings)} problem(s)")
        for f in findings:
            print(f"  {f['sheet']}!{f['cell']}  {f['result']}  <-  {f['formula']}")
        if not formula_count:
            print("  note: no formulas found - nothing was verified by this run")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
