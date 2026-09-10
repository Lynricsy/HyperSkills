#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=6"]
# ///
"""List and fill AcroForm fields in a PDF.

`list` prints every field with its type and, for checkboxes and radio groups,
the exact on-state names. `fill` refuses unknown field names and refuses
checkbox values that are not one of that widget's states, because pypdf accepts
them silently and leaves the box unchecked.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# AcroForm field type codes from the PDF specification's /FT entry.
FIELD_TYPES = {"/Tx": "text", "/Btn": "button", "/Ch": "choice", "/Sig": "signature"}


def widget_states(reader: PdfReader, field_name: str) -> list[str]:
    """Appearance-state names of a button widget, e.g. ['/Off', '/Yes']."""
    states: list[str] = []
    for page in reader.pages:
        for ref in page.get("/Annots") or []:
            annot = ref.get_object()
            if annot.get("/T") != field_name:
                continue
            normal = (annot.get("/AP") or {}).get("/N")
            if hasattr(normal, "keys"):
                states = [str(k) for k in normal.keys()]
    return states


def describe(reader: PdfReader) -> dict[str, dict[str, object]]:
    fields = reader.get_fields() or {}
    described: dict[str, dict[str, object]] = {}
    for name, field in fields.items():
        kind = FIELD_TYPES.get(str(field.get("/FT")), str(field.get("/FT")))
        entry: dict[str, object] = {"type": kind, "value": field.get("/V")}
        if kind == "button":
            entry["states"] = widget_states(reader, name)
        described[name] = entry
    return described


def cmd_list(args: argparse.Namespace) -> int:
    reader = PdfReader(str(args.pdf))
    described = describe(reader)
    if not described:
        print(f"{args.pdf.name}: no AcroForm fields. This PDF is not fillable - overlay text instead.")
        return 0
    print(f"{args.pdf.name}: {len(described)} field(s), {len(reader.pages)} page(s)")
    for name, entry in described.items():
        extra = f"  states={entry['states']}" if entry.get("states") else ""
        print(f"  {name}  [{entry['type']}]  value={entry['value']!r}{extra}")
    return 0


def cmd_fill(args: argparse.Namespace) -> int:
    reader = PdfReader(str(args.pdf))
    described = describe(reader)
    if not described:
        print(
            f"error: {args.pdf.name} has no AcroForm fields, so there is nothing to fill. "
            f"Draw the values on top with reportlab and merge instead.",
            file=sys.stderr,
        )
        return 2

    updates: dict[str, str] = {}
    for pair in args.set:
        if "=" not in pair:
            print(f"error: --set expects NAME=VALUE, got '{pair}'.", file=sys.stderr)
            return 2
        name, value = pair.split("=", 1)
        if name not in described:
            print(
                f"error: field '{name}' not found. Available: {', '.join(described)}",
                file=sys.stderr,
            )
            return 2
        entry = described[name]
        if entry["type"] == "button":
            states = [s for s in (entry.get("states") or []) if s != "/Off"]
            if value not in (entry.get("states") or []):
                print(
                    f"error: '{value}' is not a state of checkbox '{name}'. "
                    f"Use one of {entry.get('states')} - the leading slash is required, and "
                    f"'{states[0] if states else '/Yes'}' is the checked state.",
                    file=sys.stderr,
                )
                return 2
        updates[name] = value

    writer = PdfWriter(clone_from=str(args.pdf))
    # Some viewers only draw the value if the document asks them to rebuild
    # widget appearances; pypdf also writes its own, so set both.
    writer.set_need_appearances_writer(True)
    for page in writer.pages:
        names_here = {a.get_object().get("/T") for a in (page.get("/Annots") or [])}
        subset = {k: v for k, v in updates.items() if k in names_here}
        if subset:
            writer.update_page_form_field_values(page, subset)
    writer.write(str(args.out))

    written = describe(PdfReader(str(args.out)))
    print(f"wrote {args.out}")
    for name in updates:
        print(f"  {name} = {written[name]['value']!r}")
    unchanged = [n for n, v in updates.items() if str(written[n]["value"]) != v]
    if unchanged:
        print(f"error: these fields did not take the requested value: {', '.join(unchanged)}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="print field names, types and checkbox states")
    p_list.add_argument("pdf", type=Path)
    p_list.set_defaults(func=cmd_list)

    p_fill = sub.add_parser("fill", help="write values into fields")
    p_fill.add_argument("pdf", type=Path)
    p_fill.add_argument("out", type=Path)
    p_fill.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="repeatable")
    p_fill.set_defaults(func=cmd_fill)

    args = ap.parse_args()
    args.pdf = args.pdf.expanduser()
    if not args.pdf.exists():
        print(f"error: {args.pdf} does not exist.", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
