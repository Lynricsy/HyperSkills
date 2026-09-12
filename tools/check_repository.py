#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""运行与 CI 相同的离线内容检查，不执行评测夹具或调用模型。"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from _common import SkillLoadError, load_json, load_yaml, repo_root, split_frontmatter
from new_skill import substitute

# 与 PEP 723 的逐行注释形式一致；只解析元数据，不安装或执行被检查脚本。
SCRIPT_METADATA_RE = re.compile(
    r"(?m)^# /// script\r?\n((?:^#(?: .*|)\r?\n)*)^# ///\s*$"
)


def repository_files(root: Path) -> list[Path]:
    """使用 Git 的忽略规则，同时覆盖尚未暂存的新文件。"""
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return [
        root / name for name in sorted(set(proc.stdout.decode().split("\0"))) if name
    ]


def check_file(path: Path, root: Path) -> bool:
    """解析一个受检查文件；返回是否覆盖，故意错误的评测夹具不参与。"""
    rel = path.relative_to(root)
    parts = rel.parts
    if len(parts) >= 4 and parts[0] == "skills" and parts[2:4] == ("evals", "files"):
        return False
    suffix = path.suffix
    python_source = suffix == ".py" and (
        parts[0] in {"tools", "tests"}
        or (len(parts) >= 4 and parts[0] == "skills" and parts[2] == "scripts")
    )
    if not (
        suffix in {".json", ".yaml", ".yml", ".toml", ".svg"}
        or path.name.endswith(".py.lock")
        or path.name == "SKILL.md"
        or python_source
    ):
        return False
    text = path.read_text(encoding="utf-8")
    if parts[0] == "templates":
        text = substitute(text, "ci-sample", "task")
    if suffix == ".json":
        load_json(text)
    elif suffix in {".yaml", ".yml"}:
        # 工作流语义由 actionlint 检查；此处只做安全语法与重复键解析。
        load_yaml(text)
    elif suffix == ".toml" or path.name.endswith(".py.lock"):
        tomllib.loads(text)
    elif suffix == ".svg":
        ET.fromstring(text)
    elif path.name == "SKILL.md":
        split_frontmatter(text)
    elif python_source:
        compile(text, str(rel), "exec", dont_inherit=True)
        if re.search(r"(?m)^# /// script\r?$", text):
            blocks = list(SCRIPT_METADATA_RE.finditer(text))
            if len(blocks) != 1:
                raise ValueError(
                    "PEP 723 script metadata must have exactly one closed block"
                )
            metadata = tomllib.loads(
                "\n".join(
                    line[2:] if line.startswith("# ") else ""
                    for line in blocks[0][1].splitlines()
                )
            )
            dependencies = metadata.get("dependencies")
            if not isinstance(dependencies, list) or any(
                not isinstance(item, str) for item in dependencies
            ):
                raise ValueError("PEP 723 dependencies must be an array of strings")
            if not isinstance(metadata.get("requires-python"), str):
                raise ValueError("PEP 723 requires-python must be a string")
    return True


def check_syntax(root: Path) -> int:
    errors = 0
    checked = 0
    for path in repository_files(root):
        try:
            checked += check_file(path, root)
        except (
            OSError,
            ValueError,
            SyntaxError,
            yaml.YAMLError,
            ET.ParseError,
            SkillLoadError,
        ) as exc:
            errors += 1
            print(f"error: {path.relative_to(root)}: {exc}", flush=True)
    print(f"syntax: {checked} file(s) parsed, {errors} error(s)", flush=True)
    return errors


def main() -> int:
    root = repo_root()
    missing = [
        command for command in ("git", "node", "bash") if shutil.which(command) is None
    ]
    if missing:
        print(
            f"error: install required CI tools: {', '.join(missing)}", file=sys.stderr
        )
        return 1
    try:
        errors = check_syntax(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"error: cannot enumerate repository files: {exc}", file=sys.stderr)
        return 1
    if errors:
        return 1

    # 直接使用当前锁定环境的 Python，避免各子脚本再次独立解析依赖。
    commands = (
        ("skill validation", ["tools/validate_skills.py", "--strict"]),
        ("generated catalog", ["tools/build_catalog.py", "--check"]),
        ("validator regressions", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    )
    failed = []
    for name, args in commands:
        print(f"\n--- {name} ---", flush=True)
        proc = subprocess.run([sys.executable, *args], cwd=root, check=False)
        if proc.returncode:
            failed.append(name)
    if failed:
        print(f"\nerror: failed checks: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nAll repository checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
