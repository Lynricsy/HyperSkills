#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Scaffold a new skill from templates/.

    uv run tools/new_skill.py apple --category platform

Creates `skills/<name>/` from `templates/skill/` and `research/<name>.md` from
`templates/research.md`, substituting {{name}}, {{category}} and {{today}}.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import CATEGORIES, NAME_RE, repo_root  # noqa: E402

NAME_MAX = 64  # hard spec limit for the frontmatter `name` field
PLACEHOLDER_RE = re.compile(r"\{\{(name|category|today|version)\}\}")


def substitute(text: str, name: str, category: str) -> str:
    today = date.today()
    values = {
        "name": name,
        "category": category,
        "today": today.isoformat(),
        # Date-based skill version, per docs/skill-standard.md section 1.1.
        "version": today.strftime("%Y.%m.%d"),
    }
    return PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], text)


def copy_tree(src: Path, dst: Path, name: str, category: str) -> list[Path]:
    written: list[Path] = []
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = item.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(item, target)
        else:
            target.write_text(substitute(text, name, category), encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="skill directory name, e.g. 'apple'")
    parser.add_argument(
        "--category", required=True, choices=CATEGORIES, help="metadata.category"
    )
    args = parser.parse_args()

    name: str = args.name
    if not NAME_RE.match(name):
        print(
            f"error: '{name}' must match ^[a-z0-9]+(-[a-z0-9]+)*$ "
            "(lowercase letters, digits, single hyphens)",
            file=sys.stderr,
        )
        return 1
    if len(name) > NAME_MAX:
        print(f"error: '{name}' is {len(name)} chars, limit {NAME_MAX}", file=sys.stderr)
        return 1
    for reserved in ("anthropic", "claude"):
        if reserved in name:
            print(f"error: '{name}' contains the reserved word '{reserved}'", file=sys.stderr)
            return 1

    root = repo_root()
    skill_dir = root / "skills" / name
    if skill_dir.exists():
        print(f"error: {skill_dir.relative_to(root)} already exists", file=sys.stderr)
        return 1

    template_dir = root / "templates" / "skill"
    if not template_dir.is_dir():
        print(f"error: template not found at {template_dir}", file=sys.stderr)
        return 1

    written = copy_tree(template_dir, skill_dir, name, args.category)

    research_template = root / "templates" / "research.md"
    research_path = root / "research" / f"{name}.md"
    if not research_template.is_file():
        print(f"error: template not found at {research_template}", file=sys.stderr)
        return 1
    if research_path.exists():
        print(f"note: {research_path.relative_to(root)} already exists, left untouched")
    else:
        research_path.parent.mkdir(parents=True, exist_ok=True)
        research_path.write_text(
            substitute(research_template.read_text(encoding="utf-8"), name, args.category),
            encoding="utf-8",
        )
        written.append(research_path)

    print(f"created {len(written)} file(s) for skill '{name}':")
    for path in written:
        print(f"  {path.relative_to(root)}")
    print(
        "\nnext steps (docs/workflow.md):\n"
        f"  1. Phase A/B: fill research/{name}.md, then write "
        f"skills/{name}/evals/evals.json (>=3 scenarios, >=1 negative)\n"
        f"  2. uv run tools/run_evals.py {name} --baseline   # find the gap to fill\n"
        f"  3. Phase C: write SKILL.md + references/, then "
        f"uv run tools/check_upstream.py --pin {name}\n"
        f"  4. Phase D: uv run tools/validate_skills.py skills/{name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
