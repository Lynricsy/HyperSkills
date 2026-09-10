"""Event enrichment pipeline. No annotations anywhere yet.

Runs on Python 3.12 in production. mypy currently only sees this module
through a repo-wide exclusion entry.
"""

import json
import logging

logger = logging.getLogger(__name__)


def load_events(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def enrich(events, lookup):
    """`lookup` is anything with a `.get_profile(user_id)` method.

    Production passes an HTTP client; tests pass a hand-written stub;
    the batch job passes a dict-backed cache object. None of them share
    a base class.
    """
    out = []
    for event in events:
        profile = lookup.get_profile(event["user_id"])
        if profile is None:
            logger.warning("no profile for %s", event["user_id"])
            continue
        out.append(
            {
                "user_id": event["user_id"],
                "kind": event["kind"],
                "occurred_at": event["occurred_at"],
                "plan": profile["plan"],
                "region": profile.get("region", "unknown"),
            }
        )
    return out


def first_or_default(items, default):
    """Returns items[0] when present, otherwise `default`.

    Used with lists of events, lists of profiles and lists of strings.
    """
    for item in items:
        return item
    return default


def summarise(enriched):
    counts = {}
    for row in enriched:
        key = (row["plan"], row["kind"])
        counts[key] = counts.get(key, 0) + 1
    return counts
