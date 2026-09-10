"""Per-lane analysis of an exported Instruments trace.

Five lanes matter for SwiftUI responsiveness:

    time-profiler   CPU samples, aggregated by leaf symbol
    hangs           main-thread stalls the system noticed
    hitches         dropped animation frames, with Apple's own attribution
    swiftui         per-view update cost and severity (Xcode 26+ SwiftUI template)
    swiftui-causes  attribute-graph edges: which node invalidated which

A lane whose schema is absent from the run returns `available: False` with a note
instead of raising: recording with the Time Profiler template legitimately omits
the SwiftUI lanes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from . import xctrace
from .xml import RowStream, in_window, overlaps_window

NS_PER_MS = 1_000_000

# Column mnemonics drift between Xcode releases, so each lane accepts a small
# list of aliases and takes the first that is present.
START_KEYS = ("start", "time", "sample-time", "timestamp")
DURATION_KEYS = ("duration", "hitch-duration", "frame-duration")
VIEW_KEYS = ("view-name", "view", "view-type", "name", "type")

# SwiftUI records an in-flight update with a sentinel duration near UINT64_MAX.
# Anything longer than an hour is that sentinel, not a real update, and would
# swamp every aggregate it entered.
SENTINEL_DURATION_NS = 3600 * 1_000_000_000

TIME_PROFILE_SCHEMAS = ("time-profile", "time-sample")
HANG_SCHEMAS = ("potential-hangs", "main-thread-hang", "hang")
HITCH_SCHEMAS = ("hitches", "animation-hitch", "hitch")
CAUSES_SCHEMA = "swiftui-causes"
OS_LOG_SCHEMA = "os-log"
SIGNPOST_SCHEMAS = ("os-signpost-interval", "os-signpost")


def _pick(available: frozenset[str], candidates: tuple[str, ...]) -> str | None:
    return next((name for name in candidates if name in available), None)


def _unavailable(lane: str, note: str) -> dict[str, Any]:
    return {"lane": lane, "available": False, "notes": [note]}


def _ms(value_ns: float) -> float:
    return round(value_ns / NS_PER_MS, 2)


# --- lanes ----------------------------------------------------------------


def time_profiler(
    trace: Path, schemas: frozenset[str], top_n: int, window, run: int
) -> dict[str, Any]:
    schema = _pick(schemas, TIME_PROFILE_SCHEMAS)
    if schema is None:
        return _unavailable("time-profiler", "Time Profiler data not in this run.")

    stream = RowStream(xctrace.export_schema(trace, schema, run))
    samples: list[dict[str, Any]] = []
    weight_by_symbol: Counter[str] = Counter()
    count_by_symbol: Counter[str] = Counter()
    thread_of_symbol: dict[str, str] = {}
    total_weight = 0

    for row in stream:
        time_ns = stream.integer(row, "time", "sample-time")
        if time_ns is None or not in_window(time_ns, window):
            continue
        symbol = stream.leaf_symbol(row, "stack", "backtrace")
        if symbol is None:
            continue
        weight_ns = stream.integer(row, "weight") or 0
        thread_name, is_main = stream.thread(row)

        weight_by_symbol[symbol] += weight_ns
        count_by_symbol[symbol] += 1
        thread_of_symbol.setdefault(symbol, thread_name)
        total_weight += weight_ns
        samples.append(
            {"time_ns": time_ns, "weight_ns": weight_ns, "symbol": symbol, "is_main": is_main}
        )

    samples.sort(key=lambda s: s["time_ns"])
    divisor = total_weight or 1
    return {
        "lane": "time-profiler",
        "available": True,
        "schema_used": schema,
        "metrics": {"total_samples": len(samples), "total_weight_ms": _ms(total_weight)},
        "top_offenders": [
            {
                "symbol": symbol,
                "weight_ms": _ms(weight),
                "percent": round(100.0 * weight / divisor, 2),
                "samples": count_by_symbol[symbol],
                "thread": thread_of_symbol.get(symbol, "<unknown>"),
            }
            for symbol, weight in weight_by_symbol.most_common(top_n)
        ],
        "_samples": samples,
        "notes": [],
    }


def hangs(
    trace: Path, schemas: frozenset[str], top_n: int, window, run: int
) -> dict[str, Any]:
    schema = _pick(schemas, HANG_SCHEMAS)
    if schema is None:
        return _unavailable("hangs", "Hangs data not in this run.")

    stream = RowStream(xctrace.export_schema(trace, schema, run))
    events: list[dict[str, Any]] = []
    for row in stream:
        start_ns = stream.integer(row, *START_KEYS)
        duration_ns = stream.integer(row, "duration")
        if start_ns is None or duration_ns is None:
            continue
        end_ns = start_ns + duration_ns
        if not overlaps_window(start_ns, end_ns, window):
            continue
        events.append(
            {
                "start_ns": start_ns,
                "end_ns": end_ns,
                "start_ms": _ms(start_ns),
                "duration_ms": _ms(duration_ns),
                "hang_type": stream.string(row, "hang-type") or "unknown",
                "thread": stream.thread(row)[0],
            }
        )

    events.sort(key=lambda e: e["duration_ms"], reverse=True)
    durations = [e["duration_ms"] for e in events]
    return {
        "lane": "hangs",
        "available": True,
        "schema_used": schema,
        "metrics": {
            "count": len(events),
            "total_duration_ms": round(sum(durations), 2),
            "worst_duration_ms": max(durations, default=0.0),
        },
        "top_offenders": [
            {k: e[k] for k in ("start_ms", "duration_ms", "hang_type", "thread")}
            for e in events[:top_n]
        ],
        "_events": events,
        "notes": [],
    }


def hitches(
    trace: Path, schemas: frozenset[str], top_n: int, window, run: int
) -> dict[str, Any]:
    schema = _pick(schemas, HITCH_SCHEMAS)
    if schema is None:
        return _unavailable("hitches", "Animation hitches not in this run.")

    stream = RowStream(xctrace.export_schema(trace, schema, run))
    events: list[dict[str, Any]] = []
    narratives: Counter[str] = Counter()

    for row in stream:
        start_ns = stream.integer(row, *START_KEYS)
        duration_ns = stream.integer(row, *DURATION_KEYS)
        if start_ns is None or duration_ns is None:
            continue
        end_ns = start_ns + duration_ns
        if not overlaps_window(start_ns, end_ns, window):
            continue
        # Apple pre-attributes each hitch; this column is the highest-signal one.
        narrative = stream.string(row, "narrative-description", "label") or ""
        if narrative:
            narratives[narrative] += 1
        events.append(
            {
                "start_ns": start_ns,
                "end_ns": end_ns,
                "start_ms": _ms(start_ns),
                "hitch_duration_ms": _ms(duration_ns),
                "narrative": narrative,
            }
        )

    events.sort(key=lambda e: e["hitch_duration_ms"], reverse=True)
    totals = [e["hitch_duration_ms"] for e in events]
    return {
        "lane": "hitches",
        "available": True,
        "schema_used": schema,
        "metrics": {
            "count": len(events),
            "total_hitch_ms": round(sum(totals), 2),
            "worst_hitch_ms": max(totals, default=0.0),
            "narrative_breakdown": dict(narratives.most_common()),
        },
        "top_offenders": [
            {k: e[k] for k in ("start_ms", "hitch_duration_ms", "narrative")}
            for e in events[:top_n]
        ],
        "_events": events,
        "notes": [],
    }


def swiftui(
    trace: Path, schemas: frozenset[str], top_n: int, window, run: int
) -> dict[str, Any]:
    used = sorted(
        s for s in schemas if s.startswith("swiftui") and s != CAUSES_SCHEMA
    )
    if not used:
        return _unavailable(
            "swiftui",
            "SwiftUI lane absent. It needs the SwiftUI template on a real device; "
            "the iOS Simulator records the template but leaves this lane empty.",
        )

    events: list[dict[str, Any]] = []
    total_by_view: Counter[str] = Counter()
    count_by_view: Counter[str] = Counter()
    severities: Counter[str] = Counter()
    high_severity: list[dict[str, Any]] = []

    for schema in used:
        stream = RowStream(xctrace.export_schema(trace, schema, run))
        for row in stream:
            start_ns = stream.integer(row, *START_KEYS)
            duration_ns = stream.integer(row, "duration", "body-duration")
            if start_ns is None or duration_ns is None:
                continue
            if duration_ns < 0 or duration_ns > SENTINEL_DURATION_NS:
                continue  # in-flight update sentinel
            end_ns = start_ns + duration_ns
            if not overlaps_window(start_ns, end_ns, window):
                continue

            description = stream.string(row, "description")
            view = (
                stream.string(row, *VIEW_KEYS)
                or description
                or stream.string(row, "category")
                or "<unknown>"
            )
            severity = stream.string(row, "severity") or "unknown"
            total_by_view[view] += duration_ns
            count_by_view[view] += 1
            severities[severity] += 1
            record = {
                "view": view,
                "severity": severity,
                "duration_ms": _ms(duration_ns),
                "start_ms": _ms(start_ns),
                "start_ns": start_ns,
                "end_ns": end_ns,
                "description": description,
            }
            events.append(record)
            if severity in {"High", "Very High", "Severe", "Critical"}:
                high_severity.append(record)

    high_severity.sort(key=lambda e: e["duration_ms"], reverse=True)
    return {
        "lane": "swiftui",
        "available": True,
        "schemas_used": used,
        "metrics": {
            "total_events": len(events),
            "unique_views": len(total_by_view),
            "severity_breakdown": dict(severities.most_common()),
        },
        "top_offenders": [
            {
                "view": view,
                "total_ms": _ms(total),
                "count": count_by_view[view],
                "avg_ms": _ms(total / count_by_view[view]),
            }
            for view, total in total_by_view.most_common(top_n)
        ],
        "high_severity_events": [
            {k: e[k] for k in ("view", "severity", "duration_ms", "start_ms", "description")}
            for e in high_severity[:top_n]
        ],
        "_events": events,
        "notes": [],
    }


def causes(
    trace: Path, schemas: frozenset[str], top_n: int, window, run: int, per_node: int = 5
) -> dict[str, Any]:
    if CAUSES_SCHEMA not in schemas:
        return _unavailable(
            "swiftui-causes",
            "SwiftUI cause graph absent. It needs the SwiftUI template on a real device.",
        )

    stream = RowStream(xctrace.export_schema(trace, CAUSES_SCHEMA, run))
    out_edges: Counter[str] = Counter()
    in_edges: Counter[str] = Counter()
    fanout: dict[str, Counter[str]] = defaultdict(Counter)
    fanin: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0

    for row in stream:
        time_ns = stream.integer(row, "timestamp", "time")
        if time_ns is not None and not in_window(time_ns, window):
            continue
        source = stream.string(row, "source-node")
        destination = stream.string(row, "destination-node")
        if not source or not destination:
            continue
        out_edges[source] += 1
        in_edges[destination] += 1
        fanout[source][destination] += 1
        fanin[destination][source] += 1
        total += 1

    return {
        "lane": "swiftui-causes",
        "available": True,
        "schema_used": CAUSES_SCHEMA,
        "metrics": {
            "total_edges": total,
            "unique_sources": len(out_edges),
            "unique_destinations": len(in_edges),
        },
        "top_sources": [
            {
                "source": source,
                "edges": count,
                "top_destinations": [
                    {"destination": d, "edges": c}
                    for d, c in fanout[source].most_common(per_node)
                ],
            }
            for source, count in out_edges.most_common(top_n)
        ],
        "top_destinations": [
            {
                "destination": destination,
                "edges": count,
                "top_sources": [
                    {"source": s, "edges": c}
                    for s, c in fanin[destination].most_common(per_node)
                ],
            }
            for destination, count in in_edges.most_common(top_n)
        ],
        "notes": [],
    }


def fanin_for(
    trace: Path, schemas: frozenset[str], needle: str, top_n: int, window, run: int
) -> dict[str, Any]:
    """Rank the sources invalidating every destination matching `needle`."""
    if CAUSES_SCHEMA not in schemas:
        return {
            "available": False,
            "matches": [],
            "notes": ["SwiftUI cause graph absent; --fanin-for needs it."],
        }

    lowered = needle.lower()
    stream = RowStream(xctrace.export_schema(trace, CAUSES_SCHEMA, run))
    sources: dict[str, Counter[str]] = defaultdict(Counter)
    totals: Counter[str] = Counter()

    for row in stream:
        time_ns = stream.integer(row, "timestamp", "time")
        if time_ns is not None and not in_window(time_ns, window):
            continue
        destination = stream.string(row, "destination-node")
        if not destination or lowered not in destination.lower():
            continue
        source = stream.string(row, "source-node")
        if not source:
            continue
        sources[destination][source] += 1
        totals[destination] += 1

    return {
        "available": True,
        "matches": [
            {
                "destination": destination,
                "total_incoming_edges": count,
                "top_sources": [
                    {"source": s, "edges": c}
                    for s, c in sources[destination].most_common(top_n)
                ],
            }
            for destination, count in totals.most_common(top_n)
        ],
    }


# --- discovery ------------------------------------------------------------


def list_logs(
    trace: Path,
    schemas: frozenset[str],
    *,
    subsystem: str | None,
    category: str | None,
    message_contains: str | None,
    limit: int | None,
    window,
    run: int,
) -> list[dict[str, Any]]:
    """os_log entries, filtered. Used to turn "after the log saying X" into a window."""
    if OS_LOG_SCHEMA not in schemas:
        return []
    needle = message_contains.lower() if message_contains else None
    stream = RowStream(xctrace.export_schema(trace, OS_LOG_SCHEMA, run))

    out: list[dict[str, Any]] = []
    for row in stream:
        time_ns = stream.integer(row, "time", "timestamp")
        if time_ns is None or not in_window(time_ns, window):
            continue
        entry_subsystem = stream.string(row, "subsystem")
        entry_category = stream.string(row, "category")
        message = stream.string(row, "message") or stream.string(row, "format-string") or ""
        if subsystem and entry_subsystem != subsystem:
            continue
        if category and entry_category != category:
            continue
        if needle and needle not in message.lower():
            continue
        out.append(
            {
                "time_ms": _ms(time_ns),
                "type": stream.string(row, "message-type"),
                "subsystem": entry_subsystem,
                "category": entry_category,
                "message": message,
            }
        )
        # Apply the cap after filtering so N matches inside the window come back,
        # not the first N rows that happen to match before it.
        if limit is not None and len(out) >= limit:
            break
    return out


def list_signposts(
    trace: Path,
    schemas: frozenset[str],
    *,
    name_contains: str | None,
    window,
    run: int,
) -> dict[str, list[dict[str, Any]]]:
    """os_signpost intervals and point events, filtered by name."""
    schema = _pick(schemas, SIGNPOST_SCHEMAS)
    if schema is None:
        return {"intervals": [], "events": []}

    needle = name_contains.lower() if name_contains else None
    stream = RowStream(xctrace.export_schema(trace, schema, run))
    intervals: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    for row in stream:
        start_ns = stream.integer(row, *START_KEYS)
        if start_ns is None:
            continue
        name = stream.string(row, "name", "subsystem") or "<unnamed>"
        if needle and needle not in name.lower():
            continue
        duration_ns = stream.integer(row, "duration")
        common = {
            "name": name,
            "subsystem": stream.string(row, "subsystem"),
            "category": stream.string(row, "category"),
        }
        if duration_ns is None:
            if not in_window(start_ns, window):
                continue
            events.append({"time_ms": _ms(start_ns), **common})
        else:
            if not overlaps_window(start_ns, start_ns + duration_ns, window):
                continue
            intervals.append(
                {
                    "start_ms": _ms(start_ns),
                    "end_ms": _ms(start_ns + duration_ns),
                    "duration_ms": _ms(duration_ns),
                    **common,
                }
            )

    return {"intervals": intervals, "events": events}
