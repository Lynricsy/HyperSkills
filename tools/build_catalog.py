#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Generate notices, marketplace.json, README catalog and count badges.

    uv run tools/build_catalog.py           # write generated files
    uv run tools/build_catalog.py --check   # exit 1 if any generated file is stale

Every artifact here is derived from `skills/*/SKILL.md` frontmatter and
`skills/*/SOURCES.yaml`. Never edit the generated files by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    Skill,
    SkillLoadError,
    all_skill_dirs,
    load_skill,
    render_notice,
    repo_root,
)

CATALOG_START = "<!-- catalog:start -->"
CATALOG_END = "<!-- catalog:end -->"
# Claude Code's marketplace UI truncates long descriptions; keep entries scannable.
MARKETPLACE_DESC_LIMIT = 200
# The README table must stay scannable. Descriptions that open with a colon
# instead of a period have no early sentence break, so cap the cell as well.
CATALOG_BLURB_LIMIT = 150

CATEGORY_LABELS = {
    "platform": "平台",
    "framework": "框架",
    "task": "任务",
    "meta": "元技能",
}


def catalog_blurb(text: str) -> str:
    """Short, bounded description for the compact catalog table."""
    blurb = text.strip()
    for sep in (". ", "; ", ": ", " — "):
        idx = blurb.find(sep)
        if idx != -1:
            blurb = blurb[:idx]
            break
    blurb = blurb.strip().rstrip(".")
    if len(blurb) > CATALOG_BLURB_LIMIT:
        cut = blurb.rfind(" ", 0, CATALOG_BLURB_LIMIT)
        blurb = blurb[: cut if cut > 0 else CATALOG_BLURB_LIMIT].rstrip(",;") + "…"
    return blurb


def render_third_party(skills: list[Skill]) -> str:
    lines = [
        "# Third-party notices",
        "",
        "HyperSkills 的所有自有内容以 MIT 许可发布（见 `LICENSE`）。",
        "每个 skill 都是对上游材料的精编重写，下列条目记录了各 skill 的上游来源、",
        "许可与合入时固定的 commit。本文件由 `tools/build_catalog.py` 生成，请勿手工编辑。",
        "",
    ]
    for skill in skills:
        lines.append(render_notice(skill).rstrip("\n"))
        lines.append("")
        lines.append("---")
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    if lines and lines[-1] == "---":
        lines.pop()
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def render_marketplace(skills: list[Skill]) -> str:
    version = max((s.version for s in skills), default="0000.00.00")
    plugins = [
        {
            "name": s.name,
            "description": s.description[:MARKETPLACE_DESC_LIMIT],
            "source": "./",
            "strict": False,
            "skills": [f"./skills/{s.name}"],
        }
        for s in skills
    ]
    plugins.append(
        {
            "name": "all",
            "description": "Every HyperSkills skill",
            "source": "./",
            "strict": False,
            "skills": [f"./skills/{s.name}" for s in skills],
        }
    )
    doc = {
        "name": "hyperskills",
        "owner": {"name": "Lynricsy"},
        "metadata": {
            "description": "HyperSkills — curated, consolidated agent skills",
            "version": version,
        },
        "plugins": plugins,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def render_catalog_table(skills: list[Skill]) -> str:
    rows = [
        "| Skill | 类别 | 说明 | 版本 | 上游数 |",
        "|---|---|---|---|---|",
    ]
    for s in skills:
        label = CATEGORY_LABELS.get(s.category, s.category)
        rows.append(
            f"| [`{s.name}`](skills/{s.name}/) | {label} | {catalog_blurb(s.description)} "
            f"| {s.version} | {len(s.upstreams)} |"
        )
    return "\n".join(rows)


def splice_catalog(readme: str, table: str) -> str:
    start = readme.find(CATALOG_START)
    end = readme.find(CATALOG_END)
    if start == -1 or end == -1:
        raise SystemExit(
            f"README.md must contain {CATALOG_START} and {CATALOG_END} markers"
        )
    return (
        readme[: start + len(CATALOG_START)]
        + "\n\n"
        + table
        + "\n\n"
        + readme[end:]
    )


def render_count_badge(label: str, count: int) -> str:
    """生成中文标签的统计徽章；宽度随数字位数增长。"""
    value = str(count)
    label_width = len(label) * 14 + 20
    value_width = max(36, len(value) * 8 + 20)
    width = label_width + value_width
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="28" '
        f'viewBox="0 0 {width} 28" role="img" aria-labelledby="title">\n'
        f'  <title id="title">{label}：{value}</title>\n'
        f'  <rect width="{width}" height="28" rx="5" fill="#30302E"/>\n'
        f'  <path d="M{label_width} 0h{value_width - 5}q5 0 5 5v18q0 5-5 5'
        f'H{label_width}Z" fill="#EE8747"/>\n'
        '  <g font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif" '
        'font-size="12" text-anchor="middle">\n'
        f'    <text x="{label_width / 2:g}" y="18" fill="#F5F5F2">{label}</text>\n'
        f'    <text x="{label_width + value_width / 2:g}" y="18" '
        f'fill="#191919" font-weight="700">{value}</text>\n'
        "  </g>\n"
        "</svg>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="verify generated files are current"
    )
    args = parser.parse_args()

    root = repo_root()
    try:
        skills = [load_skill(p) for p in all_skill_dirs(root)]
    except SkillLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not skills:
        print("no skills found under skills/ — nothing to generate")
        return 0

    planned: dict[Path, str] = {}
    for skill in skills:
        planned[skill.path / "NOTICE.md"] = render_notice(skill)
    planned[root / "THIRD_PARTY_NOTICES.md"] = render_third_party(skills)
    planned[root / ".claude-plugin" / "marketplace.json"] = render_marketplace(skills)

    upstream_count = sum(len(skill.upstreams) for skill in skills)
    repos = {
        upstream["repo"]
        for skill in skills
        for upstream in skill.upstreams
        if upstream.get("repo")
    }
    for name, label, count in (
        ("skills", "技能", len(skills)),
        ("upstreams", "上游记录", upstream_count),
        ("repos", "来源仓库", len(repos)),
    ):
        planned[root / "docs" / "assets" / f"badge-{name}.svg"] = render_count_badge(
            label, count
        )

    readme_path = root / "README.md"
    if readme_path.is_file():
        planned[readme_path] = splice_catalog(
            readme_path.read_text(encoding="utf-8"), render_catalog_table(skills)
        )

    stale: list[Path] = []
    for path, content in planned.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            continue
        stale.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if args.check:
        if stale:
            print("stale generated files (run: uv run tools/build_catalog.py):")
            for path in stale:
                print(f"  {path.relative_to(root)}")
            return 1
        print(f"catalog is current ({len(skills)} skill(s))")
        return 0

    if stale:
        print(f"wrote {len(stale)} file(s):")
        for path in stale:
            print(f"  {path.relative_to(root)}")
    else:
        print(f"catalog already current ({len(skills)} skill(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
