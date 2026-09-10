"""Cross-lane correlation and markdown rendering."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter
from typing import Any

NS_PER_MS = 1_000_000

# Time Profiler samples the main thread about once per millisecond, so an N ms
# window should yield about N main-thread samples if main ran the whole time.
# Fewer means main was blocked rather than busy.
SAMPLE_INTERVAL_NS = NS_PER_MS

# Coverage thresholds. Below the low mark the main thread was waiting on
# something (I/O, a lock, an actor); above the high mark it was genuinely
# CPU-bound and the hot symbols are the answer.
BLOCKED_COVERAGE_PCT = 25.0
CPU_BOUND_COVERAGE_PCT = 75.0


def correlate(
    lanes: dict[str, dict[str, Any]], *, top_hitches: int, top_symbols: int
) -> list[dict[str, Any]]:
    """For each hang and worst hitch, summarise what the other lanes saw."""
    profiler = lanes.get("time-profiler") or {}
    samples = profiler.get("_samples") if profiler.get("available") else None
    sample_times = [s["time_ns"] for s in samples] if samples else None

    swiftui = lanes.get("swiftui") or {}
    swiftui_events = swiftui.get("_events") if swiftui.get("available") else None

    triggers: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    hangs = lanes.get("hangs") or {}
    if hangs.get("available"):
        for event in hangs.get("_events", []):
            triggers.append(("hangs", event, {"hang_type": event["hang_type"]}))
    hitches = lanes.get("hitches") or {}
    if hitches.get("available"):
        for event in hitches.get("_events", [])[:top_hitches]:
            triggers.append(
                ("hitches", event, {"hitch_duration_ms": event["hitch_duration_ms"]})
            )

    out: list[dict[str, Any]] = []
    for lane, event, extra in triggers:
        start_ns, end_ns = event["start_ns"], event["end_ns"]
        entry: dict[str, Any] = {
            "trigger": {
                "lane": lane,
                "start_ms": round(start_ns / NS_PER_MS, 2),
                "end_ms": round(end_ns / NS_PER_MS, 2),
                "duration_ms": round((end_ns - start_ns) / NS_PER_MS, 2),
                **extra,
            }
        }
        if samples and sample_times is not None:
            entry["time_profiler_main_thread"] = _main_thread_window(
                samples, sample_times, start_ns, end_ns, top_symbols
            )
        if swiftui_events is not None:
            overlapping = [
                {"view": e["view"], "duration_ms": e["duration_ms"], "start_ms": e["start_ms"]}
                for e in swiftui_events
                if not (e["end_ns"] < start_ns or e["start_ns"] > end_ns)
            ]
            overlapping.sort(key=lambda e: e["duration_ms"], reverse=True)
            entry["swiftui_overlapping_updates"] = overlapping[:10]
        out.append(entry)
    return out


def _main_thread_window(
    samples: list[dict[str, Any]],
    sample_times: list[int],
    start_ns: int,
    end_ns: int,
    top_symbols: int,
) -> dict[str, Any]:
    lo = bisect_left(sample_times, start_ns)
    hi = bisect_right(sample_times, end_ns)
    window = samples[lo:hi]
    main = [s for s in window if s["is_main"]]

    weight: Counter[str] = Counter()
    count: Counter[str] = Counter()
    for sample in main:
        weight[sample["symbol"]] += sample["weight_ns"]
        count[sample["symbol"]] += 1
    total = sum(weight.values()) or 1

    expected = max(1, (end_ns - start_ns) // SAMPLE_INTERVAL_NS)
    coverage = min(100.0, 100.0 * len(main) / expected)
    if coverage < BLOCKED_COVERAGE_PCT:
        verdict = "blocked"
    elif coverage >= CPU_BOUND_COVERAGE_PCT:
        verdict = "cpu-bound"
    else:
        verdict = "mixed"

    return {
        "samples_in_window": len(window),
        "samples_on_main": len(main),
        "main_running_coverage_pct": round(coverage, 1),
        "verdict": verdict,
        "hot_symbols": [
            {
                "symbol": symbol,
                "samples": count[symbol],
                "weight_ms": round(w / NS_PER_MS, 2),
                "percent_of_main": round(100.0 * w / total, 2),
            }
            for symbol, w in weight.most_common(top_symbols)
        ],
    }


def render(result: dict[str, Any]) -> str:
    """Markdown digest of a full analysis."""
    lines = [
        f"# Trace analysis — {result['trace']}",
        "",
        f"- Template: `{result.get('template')}`  ",
        f"- Duration: {result.get('duration_s')} s  ",
        f"- Run {result.get('run')} of {result.get('runs_available')}  ",
        f"- Instruments: {result.get('instruments_version')}",
        "",
    ]
    if window := result.get("window_ms"):
        lines += [f"Scoped to {window['start']}–{window['end']} ms.", ""]

    for lane in result["lanes"]:
        lines.append(f"## {lane['lane']}")
        lines.append("")
        if not lane.get("available"):
            lines += [f"_{lane['notes'][0]}_", ""]
            continue
        for key, value in lane.get("metrics", {}).items():
            lines.append(f"- {key}: {value}")
        lines.append("")
        for offender in lane.get("top_offenders", [])[:10]:
            lines.append("- " + ", ".join(f"{k}={v}" for k, v in offender.items()))
        for source in lane.get("top_sources", [])[:10]:
            lines.append(f"- {source['edges']} edges from `{source['source']}`")
        lines.append("")

    correlations = result.get("correlations") or []
    if correlations:
        lines += ["## Correlations", ""]
        for entry in correlations:
            trigger = entry["trigger"]
            lines.append(
                f"### {trigger['lane']} at {trigger['start_ms']} ms "
                f"({trigger['duration_ms']} ms)"
            )
            main = entry.get("time_profiler_main_thread")
            if main:
                lines.append(
                    f"- main-thread coverage {main['main_running_coverage_pct']}% "
                    f"({main['verdict']})"
                )
                for symbol in main["hot_symbols"][:5]:
                    lines.append(
                        f"  - {symbol['symbol']} — {symbol['weight_ms']} ms "
                        f"({symbol['percent_of_main']}% of main)"
                    )
            for update in entry.get("swiftui_overlapping_updates", [])[:5]:
                lines.append(f"- overlapping update: {update['view']} ({update['duration_ms']} ms)")
            lines.append("")

    return "\n".join(lines) + "\n"
