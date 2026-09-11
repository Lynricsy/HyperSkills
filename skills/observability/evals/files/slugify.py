"""URL slug helper. Used by the CMS export job."""

import re
import unicodedata

_NON_WORD = re.compile(r"[^\w\s-]")
_DASHES = re.compile(r"[-\s]+")


def slugify(title: str, max_len: int = 40) -> str:
    """Turn a page title into a URL slug.

    >>> slugify("Hello, World!")
    'hello-world'
    >>> slugify("Café  Münster")
    'cafe-munster'
    >>> slugify("")
    ''
    """
    normalised = unicodedata.normalize("NFKD", title)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    cleaned = _NON_WORD.sub("", ascii_only).strip().lower()
    collapsed = _DASHES.sub("-", cleaned)
    return collapsed[:max_len].strip("-")


def unique_slug(title: str, taken: set[str]) -> str:
    """Append a numeric suffix until the slug is unused."""
    base = slugify(title)
    if base not in taken:
        return base
    n = 2
    while True:
        candidate = f"{base}-{n}"
        if candidate not in taken:
            return candidate
        n += 1
