"""Wrapper around the `xctrace` CLI that ships with Xcode."""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


class XctraceError(RuntimeError):
    """Raised with an actionable message when xctrace is missing or fails."""


@dataclass(frozen=True)
class RunInfo:
    """One recording session inside a trace bundle."""

    number: int
    template: str | None
    duration_s: float | None
    start_date: str | None
    end_date: str | None
    schemas: frozenset[str]


@dataclass(frozen=True)
class TraceInfo:
    instruments_version: str
    runs: tuple[RunInfo, ...]

    def run(self, number: int) -> RunInfo:
        for candidate in self.runs:
            if candidate.number == number:
                return candidate
        available = ", ".join(str(r.number) for r in self.runs) or "none"
        raise XctraceError(f"Run {number} not in trace. Available runs: {available}")


def require_xctrace() -> None:
    """Fail early with a fixable message rather than a FileNotFoundError."""
    if shutil.which("xctrace") is None:
        raise XctraceError(
            "xctrace not found on PATH. It ships with Xcode on macOS; install Xcode "
            "and run `xcode-select --switch /Applications/Xcode.app`. Trace analysis "
            "cannot run on Linux."
        )


def toc(trace: Path) -> TraceInfo:
    """Read the trace's table of contents: runs, templates, available schemas.

    The TOC is a few kilobytes, so it is parsed into a tree rather than streamed.
    """
    root = ET.fromstring(_export(trace, ["--toc"]))
    version = _text(root, ".//instruments-version") or "unknown"

    runs: list[RunInfo] = []
    for element in root.iterfind("./run"):
        try:
            number = int(element.get("number") or "")
        except ValueError:
            continue
        if number <= 0:
            continue

        schemas = {
            table.get("schema")
            for table in element.iterfind("./data/table")
            if table.get("schema")
        }
        summary = element.find("./info/summary")
        duration = _text(summary, "./duration") if summary is not None else None
        runs.append(
            RunInfo(
                number=number,
                template=_text(summary, "./template-name") if summary is not None else None,
                duration_s=float(duration) if duration else None,
                start_date=_text(summary, "./start-date") if summary is not None else None,
                end_date=_text(summary, "./end-date") if summary is not None else None,
                schemas=frozenset(s for s in schemas if s),
            )
        )

    if not runs:
        raise XctraceError(
            f"{trace} contains no runs. The bundle may be incomplete — a recording "
            "killed before finalisation produces this."
        )
    return TraceInfo(version, tuple(sorted(runs, key=lambda r: r.number)))


def export_schema(trace: Path, schema: str, run: int) -> bytes:
    """Export one schema's rows from one run as XML bytes."""
    xpath = f'/trace-toc/run[@number="{run}"]/data/table[@schema="{schema}"]'
    return _export(trace, ["--xpath", xpath])


def _export(trace: Path, args: list[str]) -> bytes:
    require_xctrace()
    if not trace.exists():
        raise XctraceError(f"Trace not found: {trace}")
    proc = subprocess.run(
        ["xctrace", "export", "--input", str(trace), *args],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip()
        raise XctraceError(f"xctrace export failed ({proc.returncode}): {detail}")
    return proc.stdout


def _text(root: ET.Element | None, path: str) -> str | None:
    if root is None:
        return None
    element = root.find(path)
    return element.text if element is not None and element.text else None
