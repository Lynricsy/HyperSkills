"""评测输出目录保护：已有目录的内容在拒绝后保持原样，不启动 VM、不调用模型。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from run_evals import scenario_out_dir  # noqa: E402

from vm import DEFAULT_MODEL, DEFAULT_THINKING, VmRunError, claim_out_dir  # noqa: E402


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


class OutDirProtectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        # 去掉凭据，保证即使保护失效也走不到模型调用。
        self.env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    def run_tool(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOLS / script), *args],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

    def test_vm_run_refuses_existing_out_and_leaves_it_untouched(self) -> None:
        out = self.root / "precious"
        (out / "nested").mkdir(parents=True)
        (out / "notes.txt").write_text("keep me\n", encoding="utf-8")
        (out / "nested" / "data.bin").write_bytes(b"\x00\x01")
        before = snapshot(out)

        result = self.run_tool("vm.py", "run", "--out", str(out), "hello")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(snapshot(out), before)

    def test_claim_refuses_non_empty_dir_without_writing(self) -> None:
        (self.root / "keep.txt").write_text("x", encoding="utf-8")
        before = snapshot(self.root)
        with self.assertRaises(VmRunError):
            claim_out_dir(self.root)
        self.assertEqual(snapshot(self.root), before)

    def make_skill(self) -> Path:
        skill = self.root / "skills" / "sample"
        (skill / "evals").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Checks sample documents.\n---\n"
            "## Scope\n\nChecks sample documents.\n",
            encoding="utf-8",
        )
        (skill / "evals" / "evals.json").write_text(
            json.dumps(
                [
                    {
                        "skills": ["sample"],
                        "query": "q",
                        "files": [],
                        "expected_behavior": [],
                    }
                ]
            ),
            encoding="utf-8",
        )
        return skill

    def test_run_evals_refuses_foreign_scenario_dir(self) -> None:
        skill = self.make_skill()
        out_root = self.root / "out"
        target = scenario_out_dir(
            out_root, "sample", DEFAULT_MODEL, DEFAULT_THINKING, False, 1
        )
        target.mkdir(parents=True)
        (target / "mine.txt").write_text("user data\n", encoding="utf-8")
        before = snapshot(out_root)

        result = self.run_tool("run_evals.py", str(skill), "--out", str(out_root))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to delete", result.stderr)
        self.assertEqual(snapshot(out_root), before)


if __name__ == "__main__":
    unittest.main()
