"""Streaming reader for the XML that `xctrace export` produces.

Instruments deduplicates repeated values across the whole document with
`id`/`ref` attribute pairs, so a row can reference an element defined thousands
of rows earlier. `RowStream` keeps every id-bearing element in a cache and
resolves refs on demand.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    mnemonic: str          # column key, e.g. "time", "weight", "stack"
    engineering_type: str  # value kind, e.g. "sample-time", "tagged-backtrace"


class RowStream:
    """Iterate the `<row>` elements of one exported schema table.

    Each iteration yields `dict[column mnemonic -> element]`. Elements stay live
    because later rows may reference them, so peak memory is roughly the size of
    the exported document.
    """

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.columns: list[Column] = []
        self._by_id: dict[str, ET.Element] = {}

    def resolve(self, element: ET.Element) -> ET.Element:
        """Follow a `ref` attribute to the element that defined the value."""
        ref = element.get("ref")
        if ref is None:
            return element
        return self._by_id.get(ref, element)

    def __iter__(self) -> Iterator[dict[str, ET.Element]]:
        seen_schema = False
        for _event, element in ET.iterparse(io.BytesIO(self._payload), events=("end",)):
            identifier = element.get("id")
            if identifier is not None:
                self._by_id[identifier] = element

            if element.tag == "schema" and not seen_schema:
                self.columns = [
                    Column(
                        mnemonic=(col.findtext("mnemonic") or "").strip(),
                        engineering_type=(col.findtext("engineering-type") or "").strip(),
                    )
                    for col in element.findall("col")
                    if (col.findtext("mnemonic") or "").strip()
                ]
                seen_schema = True
            elif element.tag == "row":
                yield self._row(element)

    def _row(self, row: ET.Element) -> dict[str, ET.Element]:
        # Row children map positionally onto columns; <sentinel/> marks a hole.
        cells: dict[str, ET.Element] = {}
        for index, child in enumerate(row):
            if index >= len(self.columns):
                break
            if child.tag != "sentinel":
                cells[self.columns[index].mnemonic] = child
        return cells

    # --- typed cell access ------------------------------------------------

    def first(self, row: dict[str, ET.Element], *keys: str) -> ET.Element | None:
        """First present column among `keys`.

        `row.get(a) or row.get(b)` is wrong here: a childless Element is falsy,
        and leaf cells such as <sample-time> have no children.
        """
        for key in keys:
            element = row.get(key)
            if element is not None:
                return element
        return None

    def integer(self, row: dict[str, ET.Element], *keys: str) -> int | None:
        element = self.first(row, *keys)
        if element is None:
            return None
        text = self.resolve(element).text
        try:
            return int(text) if text else None
        except ValueError:
            return None

    def string(self, row: dict[str, ET.Element], *keys: str) -> str | None:
        element = self.first(row, *keys)
        if element is None:
            return None
        resolved = self.resolve(element)
        return resolved.get("fmt") or resolved.text

    def thread(self, row: dict[str, ET.Element]) -> tuple[str, bool]:
        """Thread display name, and whether it is the main thread."""
        element = row.get("thread")
        if element is None:
            return ("<unknown>", False)
        name = self.resolve(element).get("fmt") or "<unknown>"
        return (name, name.startswith("Main Thread"))

    def leaf_symbol(self, row: dict[str, ET.Element], *keys: str) -> str | None:
        """Top frame of a backtrace cell, falling back to its address."""
        element = self.first(row, *keys)
        if element is None:
            return None
        resolved = self.resolve(element)
        inner = resolved.find("backtrace") or resolved
        for frame in inner.findall("frame"):
            resolved_frame = self.resolve(frame)
            name = resolved_frame.get("name") or resolved_frame.get("addr")
            if name:
                return name
        return None


def in_window(time_ns: int | None, window: tuple[int, int] | None) -> bool:
    if window is None:
        return True
    if time_ns is None:
        return False
    return window[0] <= time_ns <= window[1]


def overlaps_window(
    start_ns: int, end_ns: int, window: tuple[int, int] | None
) -> bool:
    if window is None:
        return True
    return not (end_ns < window[0] or start_ns > window[1])
