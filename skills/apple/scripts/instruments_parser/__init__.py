"""Minimal Instruments `.trace` reader built on the `xctrace` CLI.

Four modules, in dependency order:

    xctrace  -- run `xctrace export`, parse the table of contents
    xml      -- stream <row> elements out of an exported schema
    lanes    -- turn rows into per-lane summaries and cause-graph edges
    report   -- correlate lanes and render markdown

macOS only: `xctrace` ships with Xcode. Everything else is Python stdlib.
"""

from . import lanes, report, xctrace, xml  # noqa: F401

__all__ = ["lanes", "report", "xctrace", "xml"]
