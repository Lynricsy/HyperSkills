#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Analyse an Xcode Instruments `.trace` bundle.

macOS only — reading a trace requires `xctrace`, which ships with Xcode.

Modes (one per invocation):
  (default)         Five-lane analysis plus hang/hitch correlations.
  --list-runs       Per-run metadata, for traces with several recordings.
  --list-logs       os_log entries, to locate a window by log content.
  --list-signposts  os_signpost intervals and point events.
  --fanin-for NAME  Rank the cause-graph sources invalidating a view.

--window START_MS:END_MS scopes every lane and correlation to a time slice.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from instruments_parser import lanes, report, xctrace  # noqa: E402

# Correlating every hitch floods the output on a busy trace; the worst few carry
# the signal.
DEFAULT_TOP_HITCHES = 5
# Hot-symbol lists longer than this stop being readable in a correlation entry.
CORRELATION_TOP_SYMBOLS = 5
NS_PER_MS = 1_000_000


def parse_window(spec: str | None) -> tuple[int, int] | None:
    if not spec:
        return None
    if ":" not in spec:
        raise SystemExit(f"--window expects START_MS:END_MS, got {spec!r}")
    start_text, end_text = spec.split(":", 1)
    try:
        start_ms, end_ms = float(start_text), float(end_text)
    except ValueError:
        raise SystemExit(
            f"--window expects two numbers in milliseconds, got {spec!r}"
        ) from None
    if end_ms < start_ms:
        raise SystemExit(f"--window end ({end_ms}) is before start ({start_ms})")
    return (int(start_ms * NS_PER_MS), int(end_ms * NS_PER_MS))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trace", required=True, type=Path, help="Path to the .trace bundle.")
    parser.add_argument("--run", type=int, help="Run number; required when a trace has several.")
    parser.add_argument("--top", type=int, default=10, help="Top-N rows per lane.")
    parser.add_argument(
        "--top-hitches",
        type=int,
        default=DEFAULT_TOP_HITCHES,
        help="Correlate only the N worst hitches.",
    )
    parser.add_argument("--window", help="Restrict analysis to START_MS:END_MS.")
    parser.add_argument("--output", type=Path, help="Write <output>.json and <output>.md.")

    modes = parser.add_argument_group("discovery modes")
    modes.add_argument("--list-runs", action="store_true")
    modes.add_argument("--list-logs", action="store_true")
    modes.add_argument("--list-signposts", action="store_true")
    modes.add_argument("--fanin-for", help="Cause-graph destinations containing this substring.")
    modes.add_argument("--log-subsystem")
    modes.add_argument("--log-category")
    modes.add_argument("--log-message-contains", help="Case-insensitive substring match.")
    modes.add_argument("--log-limit", type=int, help="Cap matches returned.")
    modes.add_argument("--signpost-name-contains", help="Case-insensitive substring match.")

    formats = parser.add_mutually_exclusive_group()
    formats.add_argument("--json-only", action="store_true")
    formats.add_argument("--markdown-only", action="store_true")
    return parser


def emit(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = [
        name
        for name, on in (
            ("--list-runs", args.list_runs),
            ("--list-logs", args.list_logs),
            ("--list-signposts", args.list_signposts),
            ("--fanin-for", bool(args.fanin_for)),
        )
        if on
    ]
    if len(selected) > 1:
        parser.error(f"pick one mode per invocation; got {', '.join(selected)}")

    window = parse_window(args.window)

    try:
        info = xctrace.toc(args.trace)
    except xctrace.XctraceError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.list_runs:
        emit(
            {
                "instruments_version": info.instruments_version,
                "runs": [
                    {
                        "number": r.number,
                        "template": r.template,
                        "duration_s": r.duration_s,
                        "start_date": r.start_date,
                        "end_date": r.end_date,
                        "schemas": sorted(r.schemas),
                    }
                    for r in info.runs
                ],
            }
        )
        return 0

    if args.run is not None:
        try:
            run_info = info.run(args.run)
        except xctrace.XctraceError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    elif len(info.runs) == 1:
        run_info = info.runs[0]
    else:
        available = ", ".join(str(r.number) for r in info.runs)
        print(
            f"error: this trace has {len(info.runs)} runs ({available}). Pass --run N. "
            "Use --list-runs for per-run metadata.",
            file=sys.stderr,
        )
        return 2

    schemas, run = run_info.schemas, run_info.number

    try:
        if args.list_logs:
            found = lanes.list_logs(
                args.trace,
                schemas,
                subsystem=args.log_subsystem,
                category=args.log_category,
                message_contains=args.log_message_contains,
                limit=args.log_limit,
                window=window,
                run=run,
            )
            emit({"logs": found, "count": len(found)})
            return 0

        if args.list_signposts:
            emit(
                lanes.list_signposts(
                    args.trace,
                    schemas,
                    name_contains=args.signpost_name_contains,
                    window=window,
                    run=run,
                )
            )
            return 0

        if args.fanin_for:
            emit(
                lanes.fanin_for(
                    args.trace, schemas, args.fanin_for, args.top, window, run
                )
            )
            return 0

        analysed = {
            "time-profiler": lanes.time_profiler(args.trace, schemas, args.top, window, run),
            "hangs": lanes.hangs(args.trace, schemas, args.top, window, run),
            "hitches": lanes.hitches(args.trace, schemas, args.top, window, run),
            "swiftui": lanes.swiftui(args.trace, schemas, args.top, window, run),
            "swiftui-causes": lanes.causes(args.trace, schemas, args.top, window, run),
        }
    except xctrace.XctraceError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    correlations = report.correlate(
        analysed, top_hitches=args.top_hitches, top_symbols=CORRELATION_TOP_SYMBOLS
    )

    result = {
        "trace": str(args.trace),
        "instruments_version": info.instruments_version,
        "run": run,
        "runs_available": [r.number for r in info.runs],
        "template": run_info.template,
        "duration_s": run_info.duration_s,
        "schemas_available": sorted(schemas),
        # Keys prefixed with "_" are raw per-event data kept only for correlation.
        "lanes": [
            {k: v for k, v in lane.items() if not k.startswith("_")}
            for lane in analysed.values()
        ],
        "correlations": correlations,
    }
    if window is not None:
        result["window_ms"] = {"start": window[0] / NS_PER_MS, "end": window[1] / NS_PER_MS}

    markdown = report.render(result)

    if args.output:
        json_path = args.output.with_suffix(".json")
        md_path = args.output.with_suffix(".md")
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        md_path.write_text(markdown, encoding="utf-8")
        print(f"wrote {json_path}")
        print(f"wrote {md_path}")
        return 0

    if args.markdown_only:
        sys.stdout.write(markdown)
    elif args.json_only:
        emit(result)
    else:
        emit(result)
        sys.stdout.write("\n---\n")
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
