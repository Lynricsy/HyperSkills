#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Validate HyperSkills skill directories against docs/skill-standard.md.

Every check below maps to a numbered clause in `docs/skill-standard.md` section 4.1
of the build plan. Errors exit 1; warnings only print.

Usage:
    uv run tools/validate_skills.py                 # every skill
    uv run tools/validate_skills.py skills/apple    # one skill
    uv run tools/validate_skills.py apple flutter   # by name
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    ALLOWED_TOP_LEVEL_KEYS,
    CATEGORIES,
    ISO_DATE_RE,
    NAME_RE,
    RELATIONS,
    SHA_RE,
    VERSION_RE,
    Skill,
    SkillLoadError,
    load_skill,
    render_notice,
    resolve_targets,
)

# --- limits from docs/skill-standard.md section 2.1 -------------------------
SKILL_MD_HARD_LIMIT = 500  # spec-recommended ceiling for SKILL.md body lines
SKILL_MD_WARN_LIMIT = 400  # plan's "keep it 150-400" upper edge
REFERENCE_HARD_LIMIT = 600
REFERENCE_WARN_LIMIT = 400
CONTENTS_REQUIRED_OVER = 100  # references longer than this need a `## Contents` TOC
DESCRIPTION_MIN = 80  # forces what+when+keywords+negative boundary
DESCRIPTION_MAX = 1024  # hard spec limit
NAME_MAX = 64  # hard spec limit
MIN_EVAL_SCENARIOS = 3  # standard section 6

# Body references to bundled files, e.g. `references/foo.md` or `scripts/x.py`.
ASSET_REF_RE = re.compile(r"(?<![\w/.-])(references|scripts|assets)/[\w./-]+")
SOURCES_COMMENT_RE = re.compile(r"^<!-- sources: ([a-z0-9-]+)(?:, [a-z0-9-]+)* -->$")
SOURCES_IDS_RE = re.compile(r"[a-z0-9-]+")
XML_TAG_RE = re.compile(r"<[A-Za-z/][^>]*>")
# Windows-style path separators, e.g. `word\document.xml`.
BACKSLASH_PATH_RE = re.compile(r"\w\\\w+\\")
REFERENCE_LINK_RE = re.compile(r"\]\(\.?/?references/")

BANNED_SUBSTRINGS = (
    "${CLAUDE_",
    "CLAUDE_PLUGIN_ROOT",
    "CLAUDE_SKILL_DIR",
    "WebFetch",
    "superpowers:",
)
# Dynamic shell injection: `` !`cmd` `` — the marker is a bang followed by a backtick.
BANNED_INJECTION = "!`"

RESERVED_NAME_WORDS = ("anthropic", "claude")


class Report:
    """Collects errors and warnings for one skill."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def print(self) -> None:
        if not self.errors and not self.warnings:
            print(f"  OK  {self.name}")
            return
        status = "FAIL" if self.errors else "warn"
        print(f"{status:>4}  {self.name}")
        for msg in self.errors:
            print(f"        error: {msg}")
        for msg in self.warnings:
            print(f"        warn:  {msg}")


def check_frontmatter(skill: Skill, rep: Report) -> None:
    """Checks 2-5, 13."""
    fm = skill.frontmatter

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        rep.error("frontmatter 'name' is missing")
    else:
        if name != skill.name:
            rep.error(f"name must match directory: '{name}' != '{skill.name}'")
        if not NAME_RE.match(name):
            rep.error(f"name '{name}' must match ^[a-z0-9]+(-[a-z0-9]+)*$")
        if len(name) > NAME_MAX:
            rep.error(f"name is {len(name)} chars, limit {NAME_MAX}")
        for word in RESERVED_NAME_WORDS:
            if word in name.lower():
                rep.error(f"name must not contain the reserved word '{word}'")
        if XML_TAG_RE.search(name):
            rep.error("name must not contain XML tags")

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc:
        rep.error("frontmatter 'description' is missing")
    else:
        if not DESCRIPTION_MIN <= len(desc) <= DESCRIPTION_MAX:
            rep.error(
                f"description is {len(desc)} chars, must be "
                f"{DESCRIPTION_MIN}-{DESCRIPTION_MAX}"
            )
        if XML_TAG_RE.search(desc):
            rep.error("description must not contain XML tags")
        if desc.startswith("I ") or desc.startswith("You "):
            rep.error("description must be third person, not 'I '/'You '")
        if " I can " in desc:
            rep.error("description must be third person; found ' I can '")
        if "do not use for" not in desc.lower():
            rep.warn("description should state a negative boundary ('Do not use for ...')")
        if "TODO" in desc:
            rep.error("description still contains the scaffold placeholder 'TODO'")

    if not fm.get("license"):
        rep.error("frontmatter 'license' is missing")

    meta = fm.get("metadata")
    if not isinstance(meta, dict):
        rep.error("frontmatter 'metadata' must be a mapping")
    else:
        if meta.get("author") != "HyperSkills":
            rep.error(f"metadata.author must be 'HyperSkills', got {meta.get('author')!r}")
        version = str(meta.get("version", ""))
        if not VERSION_RE.match(version):
            rep.error(f"metadata.version must be YYYY.MM.DD, got {version!r}")
        if meta.get("category") not in CATEGORIES:
            rep.error(
                f"metadata.category must be one of {', '.join(CATEGORIES)}, "
                f"got {meta.get('category')!r}"
            )

    extra = set(fm) - ALLOWED_TOP_LEVEL_KEYS
    if extra:
        rep.error(
            f"non-spec top-level frontmatter keys: {', '.join(sorted(extra))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_TOP_LEVEL_KEYS))}"
        )


def check_no_nested_skill_md(skill: Skill, rep: Report) -> None:
    """Only the skill root may hold a SKILL.md.

    Recursive discoverers (Cursor, and `npx skills` beyond its shallow shadowing
    rule) treat any directory containing a SKILL.md as a skill. A fixture named
    SKILL.md under evals/files/ therefore registers a second, broken skill.
    """
    for nested in sorted(skill.path.rglob("SKILL.md")):
        if nested != skill.path / "SKILL.md":
            rel = nested.relative_to(skill.path).as_posix()
            rep.error(
                f"{rel} would register as a second skill in recursive scanners. "
                "Rename the fixture, e.g. widget-builder-SKILL.md"
            )


def check_body(skill: Skill, rep: Report) -> None:
    """Checks 6, 7, 15."""
    lines = skill.body.splitlines()
    if len(lines) > SKILL_MD_HARD_LIMIT:
        rep.error(f"SKILL.md body is {len(lines)} lines, hard limit {SKILL_MD_HARD_LIMIT}")
    elif len(lines) > SKILL_MD_WARN_LIMIT:
        rep.warn(f"SKILL.md body is {len(lines)} lines, prefer <= {SKILL_MD_WARN_LIMIT}")

    referenced: set[str] = set()
    for match in ASSET_REF_RE.finditer(skill.body):
        rel = match.group(0).rstrip(".,;:)")
        referenced.add(rel)
        if not (skill.path / rel).exists():
            rep.error(f"SKILL.md references missing file: {rel}")

    ref_dir = skill.path / "references"
    if ref_dir.is_dir():
        for ref in sorted(ref_dir.iterdir()):
            if ref.is_file() and ref.name != ".gitkeep":
                rel = f"references/{ref.name}"
                if rel not in referenced:
                    rep.warn(f"{rel} is never referenced from SKILL.md")

    if BACKSLASH_PATH_RE.search(skill.body):
        rep.warn("SKILL.md uses backslash path separators; use forward slashes")


def check_banned(text: str, where: str, rep: Report) -> None:
    """Check 9."""
    for banned in BANNED_SUBSTRINGS:
        if banned in text:
            rep.error(f"{where} contains banned token '{banned}'")
    if BANNED_INJECTION in text:
        rep.error(f"{where} contains dynamic command injection '!`'")


def check_references(skill: Skill, rep: Report) -> None:
    """Check 8, plus 9 and 15 applied to reference files."""
    ref_dir = skill.path / "references"
    if not ref_dir.is_dir():
        return
    known_ids = {str(u.get("id")) for u in skill.upstreams if u.get("id")}
    for ref in sorted(ref_dir.glob("*.md")):
        rel = f"references/{ref.name}"
        text = ref.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > REFERENCE_HARD_LIMIT:
            rep.error(f"{rel} is {len(lines)} lines, hard limit {REFERENCE_HARD_LIMIT}")
        elif len(lines) > REFERENCE_WARN_LIMIT:
            rep.warn(f"{rel} is {len(lines)} lines, prefer <= {REFERENCE_WARN_LIMIT}")

        if len(lines) > CONTENTS_REQUIRED_OVER and "## Contents" not in text:
            rep.error(
                f"{rel} is {len(lines)} lines (> {CONTENTS_REQUIRED_OVER}) "
                "and needs a '## Contents' table of contents"
            )

        non_empty = [ln for ln in lines if ln.strip()]
        if not non_empty:
            rep.error(f"{rel} is empty")
            continue
        last = non_empty[-1].strip()
        if not SOURCES_COMMENT_RE.match(last):
            rep.error(
                f"{rel} last non-empty line must be '<!-- sources: id1, id2 -->', "
                f"got {last[:60]!r}"
            )
        else:
            inner = last[len("<!-- sources:") : -len("-->")].strip()
            for src_id in SOURCES_IDS_RE.findall(inner):
                if src_id not in known_ids:
                    rep.error(
                        f"{rel} cites unknown source id '{src_id}'. "
                        f"Available: {', '.join(sorted(known_ids)) or '(none)'}"
                    )

        if REFERENCE_LINK_RE.search(text):
            rep.error(f"{rel} links to another reference; only SKILL.md may link one level")

        check_banned(text, rel, rep)
        if BACKSLASH_PATH_RE.search(text):
            rep.warn(f"{rel} uses backslash path separators; use forward slashes")


def check_sources(skill: Skill, rep: Report) -> None:
    """Check 10."""
    path = skill.path / "SOURCES.yaml"
    if not path.is_file():
        rep.error("SOURCES.yaml is missing")
        return
    src = skill.sources
    if src.get("skill") != skill.name:
        rep.error(f"SOURCES.yaml 'skill' must be '{skill.name}', got {src.get('skill')!r}")
    if str(src.get("version", "")) != skill.version:
        rep.error(
            f"SOURCES.yaml version {src.get('version')!r} != "
            f"SKILL.md metadata.version {skill.version!r}"
        )
    upstreams = skill.upstreams
    if not upstreams:
        rep.error("SOURCES.yaml 'upstreams' must be a non-empty list")
        return

    seen: set[str] = set()
    merged_count = 0
    for i, up in enumerate(upstreams):
        tag = f"upstreams[{i}]"
        if not isinstance(up, dict):
            rep.error(f"{tag} must be a mapping")
            continue
        up_id = up.get("id")
        tag = f"upstreams[{up_id or i}]"
        if not isinstance(up_id, str) or not NAME_RE.match(up_id):
            rep.error(f"{tag} 'id' must match ^[a-z0-9]+(-[a-z0-9]+)*$")
        elif up_id in seen:
            rep.error(f"{tag} duplicate id '{up_id}'")
        else:
            seen.add(up_id)

        kind = up.get("kind")
        if kind not in ("repo", "docs"):
            rep.error(f"{tag} 'kind' must be 'repo' or 'docs', got {kind!r}")
        if not up.get("url"):
            rep.error(f"{tag} 'url' is required")
        if not up.get("license"):
            rep.error(f"{tag} 'license' is required (SPDX id, NONE, or Proprietary)")
        if not up.get("contributes"):
            rep.error(f"{tag} 'contributes' is required")

        relation = up.get("relation")
        if relation not in RELATIONS:
            rep.error(f"{tag} 'relation' must be one of {', '.join(RELATIONS)}")
        elif relation == "merged":
            merged_count += 1

        synced = str(up.get("synced_at", ""))
        if not ISO_DATE_RE.match(synced):
            rep.error(f"{tag} 'synced_at' must be an ISO date, got {synced!r}")

        if kind == "repo":
            if not up.get("repo"):
                rep.error(f"{tag} 'repo' is required when kind=repo")
            if not up.get("ref"):
                rep.error(f"{tag} 'ref' is required when kind=repo")
            commit = str(up.get("commit", ""))
            if not SHA_RE.match(commit):
                rep.error(f"{tag} 'commit' must be a 40-hex sha, got {commit!r}")
            paths = up.get("paths")
            if paths is not None and not isinstance(paths, list):
                rep.error(f"{tag} 'paths' must be a list when present")

        if up.get("license") == "Proprietary" and relation == "merged":
            rep.error(f"{tag} proprietary sources must be relation: reference")

    if merged_count == 0:
        rep.error("SOURCES.yaml needs at least one upstream with relation: merged")


def check_notice(skill: Skill, rep: Report) -> None:
    """Check 11."""
    path = skill.path / "NOTICE.md"
    if not path.is_file():
        rep.error("NOTICE.md is missing (run: uv run tools/build_catalog.py)")
        return
    expected = render_notice(skill)
    if path.read_text(encoding="utf-8") != expected:
        rep.error("NOTICE.md is stale (run: uv run tools/build_catalog.py)")


def check_scripts(skill: Skill, rep: Report) -> None:
    """Check 12."""
    scripts = skill.path / "scripts"
    if not scripts.is_dir():
        return
    for script in sorted(scripts.rglob("*")):
        if not script.is_file():
            continue
        rel = script.relative_to(skill.path).as_posix()
        suffix = script.suffix
        if suffix == ".py":
            cmd = [sys.executable, "-m", "py_compile", str(script)]
        elif suffix in (".mjs", ".js"):
            cmd = ["node", "--check", str(script)]
        elif suffix == ".sh":
            cmd = ["bash", "-n", str(script)]
        else:
            continue
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            rep.warn(f"{rel}: cannot syntax-check, '{cmd[0]}' not installed")
            continue
        except subprocess.TimeoutExpired:
            rep.error(f"{rel}: syntax check timed out")
            continue
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            rep.error(f"{rel}: syntax error: {detail[-1] if detail else 'unknown'}")


def check_evals(skill: Skill, rep: Report) -> None:
    """Check 14."""
    path = skill.path / "evals" / "evals.json"
    if not path.is_file():
        rep.error("evals/evals.json is missing")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.error(f"evals/evals.json is not valid JSON: {exc}")
        return
    if not isinstance(data, list):
        rep.error("evals/evals.json must be a JSON array")
        return
    if len(data) < MIN_EVAL_SCENARIOS:
        rep.error(f"evals/evals.json has {len(data)} scenarios, need >= {MIN_EVAL_SCENARIOS}")

    has_negative = False
    for i, scenario in enumerate(data):
        tag = f"evals[{i}]"
        if not isinstance(scenario, dict):
            rep.error(f"{tag} must be an object")
            continue
        skills_field = scenario.get("skills")
        if not isinstance(skills_field, list):
            rep.error(f"{tag} 'skills' must be an array")
        elif skills_field == []:
            has_negative = True
        query = scenario.get("query")
        if not isinstance(query, str) or not query.strip():
            rep.error(f"{tag} 'query' must be a non-empty string")
        elif "TODO" in query:
            rep.error(f"{tag} 'query' still contains the scaffold placeholder 'TODO'")
        expected = scenario.get("expected_behavior")
        if not isinstance(expected, list) or not expected:
            rep.error(f"{tag} 'expected_behavior' must be a non-empty array")
        elif any("TODO" in str(e) for e in expected):
            rep.error(f"{tag} 'expected_behavior' still contains a 'TODO' placeholder")
        files = scenario.get("files")
        if files is not None:
            if not isinstance(files, list):
                rep.error(f"{tag} 'files' must be an array when present")
            else:
                for rel in files:
                    if not (skill.path / str(rel)).exists():
                        rep.error(f"{tag} fixture not found: {rel}")
    if not has_negative:
        rep.error("evals/evals.json needs at least one negative scenario with skills: []")


def validate(path: Path) -> Report:
    rep = Report(path.name)
    try:
        skill = load_skill(path)
    except SkillLoadError as exc:
        rep.error(str(exc))
        return rep

    check_frontmatter(skill, rep)
    check_body(skill, rep)
    check_no_nested_skill_md(skill, rep)
    check_banned(skill.body, "SKILL.md", rep)
    check_sources(skill, rep)
    check_references(skill, rep)
    check_notice(skill, rep)
    check_scripts(skill, rep)
    check_evals(skill, rep)
    return rep


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("targets", nargs="*", help="skill names or paths (default: all)")
    args = parser.parse_args()

    try:
        targets = resolve_targets(args.targets)
    except SkillLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not targets:
        print("no skills found under skills/ — nothing to validate")
        return 0

    reports = [validate(p) for p in targets]
    for rep in reports:
        rep.print()

    errors = sum(len(r.errors) for r in reports)
    warnings = sum(len(r.warnings) for r in reports)
    print(f"\n{len(reports)} skill(s): {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
