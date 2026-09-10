"""Shared helpers for the HyperSkills tools.

Kept dependency-light on purpose: only PyYAML, which every tool already needs to
read `SKILL.md` frontmatter and `SOURCES.yaml`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Frontmatter is the leading `---` fenced block. Anything else is a hard error,
# so the pattern is deliberately anchored at the start of the file.
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CATEGORIES = ("platform", "framework", "task", "meta")
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
)
RELATIONS = ("merged", "reference")


def repo_root() -> Path:
    """Repository root, derived from this file's location (tools/ lives at the root)."""
    return Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class Skill:
    """A parsed skill directory."""

    path: Path
    frontmatter: dict[str, Any]
    body: str
    sources: dict[str, Any]

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def description(self) -> str:
        return str(self.frontmatter.get("description", ""))

    @property
    def version(self) -> str:
        meta = self.frontmatter.get("metadata")
        return str(meta.get("version", "")) if isinstance(meta, dict) else ""

    @property
    def category(self) -> str:
        meta = self.frontmatter.get("metadata")
        return str(meta.get("category", "")) if isinstance(meta, dict) else ""

    @property
    def upstreams(self) -> list[dict[str, Any]]:
        ups = self.sources.get("upstreams")
        return ups if isinstance(ups, list) else []


class SkillLoadError(Exception):
    """Raised when a skill directory cannot be parsed at all."""


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter mapping, body). Raises SkillLoadError on malformed input."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SkillLoadError(
            "SKILL.md must start with a '---' fenced YAML frontmatter block"
        )
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise SkillLoadError(f"frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise SkillLoadError("frontmatter must be a YAML mapping")
    return data, match.group(2)


def load_skill(path: Path) -> Skill:
    """Load one `skills/<name>/` directory."""
    path = path.resolve()
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        raise SkillLoadError(f"{skill_md} not found")
    frontmatter, body = split_frontmatter(skill_md.read_text(encoding="utf-8"))

    sources_path = path / "SOURCES.yaml"
    sources: dict[str, Any] = {}
    if sources_path.is_file():
        try:
            loaded = yaml.safe_load(sources_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise SkillLoadError(f"SOURCES.yaml is not valid YAML: {exc}") from exc
        if loaded is not None and not isinstance(loaded, dict):
            raise SkillLoadError("SOURCES.yaml must be a YAML mapping")
        sources = loaded or {}
    return Skill(path=path, frontmatter=frontmatter, body=body, sources=sources)


def all_skill_dirs(root: Path | None = None) -> list[Path]:
    """Every `skills/<name>/` directory that contains a SKILL.md, sorted by name."""
    base = (root or repo_root()) / "skills"
    if not base.is_dir():
        return []
    return sorted(
        (p for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()),
        key=lambda p: p.name,
    )


def resolve_targets(args: list[str], root: Path | None = None) -> list[Path]:
    """Turn CLI arguments (skill names or paths) into skill directories.

    Accepts `apple`, `skills/apple`, `skills/apple/` and absolute paths so callers
    can shell-glob without thinking about it.
    """
    base = root or repo_root()
    if not args:
        return all_skill_dirs(base)
    out: list[Path] = []
    for arg in args:
        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = (base / arg).resolve() if candidate.parts[0] == "skills" else (
                base / "skills" / arg
            ).resolve()
        if not candidate.is_dir():
            raise SkillLoadError(
                f"no skill directory for '{arg}'. Available: "
                + ", ".join(p.name for p in all_skill_dirs(base))
            )
        out.append(candidate)
    return out


def render_notice(skill: Skill) -> str:
    """Render the canonical `NOTICE.md` body for one skill.

    Shared by build_catalog.py (writes it) and validate_skills.py (compares it),
    so the two can never drift.
    """
    merged = [u for u in skill.upstreams if u.get("relation") == "merged"]
    referenced = [u for u in skill.upstreams if u.get("relation") == "reference"]

    lines = [
        f"# NOTICE — {skill.name}",
        "",
        "This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:",
        "",
    ]
    for up in merged:
        lines.append(_notice_line(up, with_commit=True))
    if referenced:
        lines += ["", "Reference-only sources (no content copied):", ""]
        for up in referenced:
            lines.append(_notice_line(up, with_commit=False))
    lines.append("")
    return "\n".join(lines)


def _notice_line(up: dict[str, Any], *, with_commit: bool) -> str:
    label = up.get("repo") or up.get("url", "")
    parts = [f"- {label} ({up.get('license', 'UNKNOWN')}) — {up.get('url', '')}"]
    if with_commit and up.get("commit"):
        parts.append(f"@ {up['commit']}")
    paths = up.get("paths")
    if with_commit and paths:
        parts.append(f"— paths: {', '.join(paths)}")
    if with_commit and up.get("contributes"):
        parts.append(f"— {up['contributes']}")
    return " ".join(parts)
