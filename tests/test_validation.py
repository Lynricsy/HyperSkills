"""验证 CI 会拒绝模糊数据、漏检目录和越界夹具，不执行夹具内容。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from _common import SkillLoadError, load_json, load_skill, load_yaml, render_notice  # noqa: E402
from check_repository import check_file  # noqa: E402


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills" / "sample"
        self.skill.mkdir(parents=True)
        self.frontmatter = {
            "name": "sample",
            "description": "Checks sample documents.",
            "license": "MIT (upstream attributions in NOTICE.md)",
            "metadata": {
                "author": "HyperSkills",
                "version": "2026.09.12",
                "category": "task",
            },
        }
        self.body = "## Scope\n\nChecks sample documents.\n"
        self.write_skill()
        self.sources = {
            "skill": "sample",
            "version": "2026.09.12",
            "upstreams": [
                {
                    "id": "sample-docs",
                    "kind": "docs",
                    "url": "https://example.com/docs",
                    "license": "MIT",
                    "relation": "merged",
                    "synced_at": "2026-09-12",
                    "contributes": "Document review rules.",
                }
            ],
        }
        self.write_sources()
        (self.skill / "NOTICE.md").write_text(
            render_notice(load_skill(self.skill)), encoding="utf-8"
        )
        (self.skill / "evals" / "files").mkdir(parents=True)
        self.scenarios = [
            {
                "skills": ["sample"],
                "query": "Check this document.",
                "files": [],
                "expected_behavior": ["Report inconsistencies."],
            },
            {
                "skills": ["sample"],
                "query": "Compare these documents.",
                "files": [],
                "expected_behavior": ["Report contradictions."],
            },
            {
                "skills": [],
                "query": "Write a poem.",
                "files": [],
                "expected_behavior": ["Do not read the sample skill."],
            },
        ]
        self.write_evals()

    def write_skill(self) -> None:
        (self.skill / "SKILL.md").write_text(
            "---\n" + yaml.safe_dump(self.frontmatter) + "---\n" + self.body,
            encoding="utf-8",
        )

    def write_sources(self) -> None:
        (self.skill / "SOURCES.yaml").write_text(
            yaml.safe_dump(self.sources), encoding="utf-8"
        )

    def write_evals(self) -> None:
        (self.skill / "evals" / "evals.json").write_text(
            json.dumps(self.scenarios), encoding="utf-8"
        )

    def run_validator(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOLS / "validate_skills.py"), str(self.skill), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_skill_and_generated_notice_pass_strict_gate(self) -> None:
        result = self.run_validator("--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_nested_duplicate_yaml_key_is_not_silently_overwritten(self) -> None:
        path = self.skill / "SKILL.md"
        path.write_text(
            "---\nname: sample\nmetadata:\n  version: old\n  version: new\n---\n",
            encoding="utf-8",
        )
        with self.assertRaises(SkillLoadError):
            load_skill(self.skill)

    def test_yaml_merge_override_remains_valid(self) -> None:
        parsed = load_yaml(
            "base: &base\n  value: old\nitem:\n  <<: *base\n  value: new\n"
        )
        self.assertEqual(parsed["item"], {"value": "new"})

    def test_unsafe_yaml_object_tag_is_rejected(self) -> None:
        with self.assertRaises(yaml.YAMLError):
            load_yaml("!!python/object/apply:builtins.str [unsafe]")

    def test_json_ambiguous_and_nonstandard_values_are_rejected(self) -> None:
        for text in (
            '{"nested": {"skills": [], "skills": ["sample"]}}',
            '{"value": NaN}',
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_json(text)

    def test_duplicate_evaluation_key_fails_the_cli(self) -> None:
        path = self.skill / "evals" / "evals.json"
        ambiguous = json.dumps(self.scenarios).replace(
            '"skills": ["sample"]', '"skills": [], "skills": ["sample"]', 1
        )
        path.write_text(ambiguous, encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_upstreams_are_reported_without_crashing(self) -> None:
        self.sources["upstreams"] = [None]
        self.write_sources()
        refs = self.skill / "references"
        refs.mkdir()
        (refs / "review.md").write_text(
            "# Review\n\n<!-- sources: sample-docs -->\n", encoding="utf-8"
        )
        self.body += "\nSee references/review.md.\n"
        self.write_skill()
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("sample", result.stdout)

    def test_warning_fails_only_in_strict_mode(self) -> None:
        self.body += "\n" * 401
        self.write_skill()
        self.assertEqual(self.run_validator().returncode, 0)
        self.assertEqual(self.run_validator("--strict").returncode, 1)

    def test_existing_file_outside_fixture_root_is_rejected(self) -> None:
        self.scenarios[0]["files"] = ["SKILL.md"]
        self.write_evals()
        self.assertEqual(self.run_validator().returncode, 1)

    def test_fixture_symlink_cannot_escape_allowed_directory(self) -> None:
        (self.skill / "evals" / "files" / "escape.md").symlink_to(
            self.skill / "SKILL.md"
        )
        self.scenarios[0]["files"] = ["evals/files/escape.md"]
        self.write_evals()
        self.assertEqual(self.run_validator().returncode, 1)

    def test_fixture_size_boundary(self) -> None:
        fixture = self.skill / "evals" / "files" / "large.txt"
        self.scenarios[0]["files"] = ["evals/files/large.txt"]
        self.write_evals()
        fixture.write_bytes(b"x" * (50 * 1024))
        self.assertEqual(self.run_validator().returncode, 0)
        fixture.write_bytes(b"x" * (50 * 1024 + 1))
        self.assertEqual(self.run_validator().returncode, 1)

    def test_non_text_expected_behavior_is_rejected(self) -> None:
        self.scenarios[0]["expected_behavior"] = [False]
        self.write_evals()
        self.assertEqual(self.run_validator().returncode, 1)

    def test_missing_skill_entry_is_not_skipped_by_full_scan(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("_common.py", "validate_skills.py"):
            shutil.copyfile(TOOLS / name, tools / name)
        (self.skill / "SKILL.md").unlink()
        result = subprocess.run(
            [sys.executable, str(tools / "validate_skills.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("sample", result.stdout)

    def test_empty_repository_fails_both_quality_gates(self) -> None:
        tools = self.root / "tools"
        tools.mkdir()
        shutil.rmtree(self.root / "skills")
        for name in ("_common.py", "validate_skills.py", "build_catalog.py"):
            shutil.copyfile(TOOLS / name, tools / name)
        for script, args in (
            ("validate_skills.py", []),
            ("build_catalog.py", ["--check"]),
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(tools / script), *args],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)

    def test_stale_generated_notice_fails_validation(self) -> None:
        (self.skill / "NOTICE.md").write_text("outdated", encoding="utf-8")
        self.assertEqual(self.run_validator().returncode, 1)

    def test_syntax_scan_excludes_broken_eval_fixture_but_not_shipped_script(
        self,
    ) -> None:
        fixture = self.skill / "evals" / "files" / "broken.py"
        fixture.write_text("def broken(:", encoding="utf-8")
        self.assertFalse(check_file(fixture, self.root))
        script = self.skill / "scripts" / "broken.py"
        script.parent.mkdir()
        script.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaises(SyntaxError):
            check_file(script, self.root)

    def test_invalid_pep723_toml_is_rejected_without_running_script(self) -> None:
        script = self.skill / "scripts" / "sample.py"
        script.parent.mkdir()
        script.write_text(
            '# /// script\n# dependencies = [\n# ///\nraise RuntimeError("must not run")\n',
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            check_file(script, self.root)


if __name__ == "__main__":
    unittest.main()
