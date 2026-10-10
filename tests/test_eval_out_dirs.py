"""评测输出目录保护与事件流解析：拒绝后目录内容保持原样，不启动 VM、不调用模型。"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from run_evals import extract_answer, scenario_lock_path, scenario_out_dir  # noqa: E402

from vm import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_THINKING,
    RUN_MARKER,
    VmRunError,
    claim_out_dir,
    parse_events,
    provider_error,
)


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
        self.env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}

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

    def test_run_evals_refuses_to_replace_a_live_run(self) -> None:
        skill = self.make_skill()
        out_root = self.root / "out"
        target = scenario_out_dir(
            out_root, "sample", DEFAULT_MODEL, DEFAULT_THINKING, False, 1
        )
        # 第一个进程刚认领目录、VM 还在跑：有运行标记，还没有 result.json。
        target.mkdir(parents=True)
        (target / RUN_MARKER).write_text("", encoding="utf-8")
        (target / "events.jsonl").write_text('{"type":"agent_start"}\n', "utf-8")
        lock = scenario_lock_path(target)
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o644)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = snapshot(out_root)

        result = self.run_tool("run_evals.py", str(skill), "--out", str(out_root))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("another eval process", result.stderr)
        self.assertEqual(snapshot(out_root), before)


# U+2028 / U+2029 在 JSON 字符串里可以原样出现（ensure_ascii=False），不是记录边界。
SEPARATED = "first\u2028second\u2029third"


def jsonl(*events: dict) -> str:
    return "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)


class EventFramingTests(unittest.TestCase):
    def test_answer_with_unicode_separators_survives(self) -> None:
        message = {
            "role": "assistant",
            "content": [{"type": "text", "text": SEPARATED}],
        }
        raw = jsonl(
            {"type": "agent_start"},
            {"type": "agent_end", "messages": [message]},
        )
        self.assertEqual(extract_answer(parse_events(raw)), SEPARATED)

    def test_provider_error_with_unicode_separators_is_detected(self) -> None:
        failed = {
            "role": "assistant",
            "content": [],
            "stopReason": "error",
            "errorMessage": SEPARATED,
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            path.write_text(
                jsonl({"type": "message_end", "message": failed}), encoding="utf-8"
            )
            self.assertEqual(provider_error(path), SEPARATED)


if __name__ == "__main__":
    unittest.main()
