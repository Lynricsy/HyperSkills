#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Headless eval runner for HyperSkills skills.

Runs each scenario in `skills/<name>/evals/evals.json` through a non-interactive
`omp` session and records whether the skill was actually read plus the final
answer, so Phase B baselines and Phase D with-skill runs are directly comparable.

    uv run tools/run_evals.py apple --baseline        # no skills loaded (the gap)
    uv run tools/run_evals.py apple                   # with skill
    uv run tools/run_evals.py apple --thinking high   # 换思考档
    uv run tools/run_evals.py apple --only 2          # one scenario

Judging is manual on purpose: `expected_behavior` entries are prose, and a
regex grader would reward wording rather than behaviour. Read `answer.md` and
fill in the table in `research/<skill>.md`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import SkillLoadError, load_skill, repo_root, resolve_targets  # noqa: E402

# A single eval turn is usually 1-5 minutes; 900s leaves headroom for slow
# models and tool-heavy scenarios without hanging a batch forever.
SCENARIO_TIMEOUT = 900
# Raw NDJSON event stream from `omp --mode json`, kept verbatim so a failed text
# extraction can still be judged by hand.
EVENTS_FILE = "events.jsonl"
ANSWER_FILE = "answer.md"
RESULT_FILE = "result.json"
# Outside the repo: eval runs are throwaway artifacts, never committed.
DEFAULT_OUT_ROOT = Path("/tmp/hs-evals")
OVERLAY_FILE = "overlay.yml"
# The scenario's working directory must live outside the artifact tree. A
# shared `--out` root accumulates hundreds of MB of prior `events.jsonl`, and a
# scenario whose agent searches the filesystem then drowns in its own
# transcripts: web-testing hit the 900s ceiling on all five scenarios that way,
# and the same scenario finished in 113s once the workspace was separated.
DEFAULT_WORKSPACE_ROOT = Path("/tmp/hs-eval-workspaces")
# Evals are fixed to one model so runs stay comparable across skills and
# batches: Claude Opus 5 is the strong model this repo's users actually work
# with, so a gap measured here is a gap they would really hit.
DEFAULT_MODEL = "anthropic/claude-opus-5"
# `medium` is the default reasoning level of that model; evaluating anywhere
# else would measure the thinking budget rather than the skill.
DEFAULT_THINKING = "medium"
THINKING_LEVELS = ("off", "minimal", "low", "medium", "high", "xhigh", "max", "auto")


def write_overlay(out_root: Path, skills_dir: Path) -> Path:
    """Config overlay that makes this repo's skills discoverable from any cwd."""
    out_root.mkdir(parents=True, exist_ok=True)
    overlay = out_root / OVERLAY_FILE
    overlay.write_text(
        "skills:\n" f'  customDirectories: ["{skills_dir}"]\n', encoding="utf-8"
    )
    return overlay


def extract_answer(events: list[dict[str, Any]]) -> str | None:
    """Final assistant text from the event stream.

    Prefers `agent_end` (authoritative full transcript), falls back to the last
    `turn_end`, then to any trailing assistant `message_end`.
    """

    def text_of(message: dict[str, Any]) -> str:
        parts = [
            block.get("text", "")
            for block in message.get("content", [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p).strip()

    for event in reversed(events):
        if event.get("type") == "agent_end":
            for message in reversed(event.get("messages", [])):
                if message.get("role") == "assistant" and text_of(message):
                    return text_of(message)
    for event in reversed(events):
        if event.get("type") in ("turn_end", "message_end"):
            message = event.get("message", {})
            if message.get("role") == "assistant" and text_of(message):
                return text_of(message)
    return None


def detect_skill_read(raw: str, skill: str, skills_dir: Path) -> bool:
    """Whether the transcript shows the skill itself being loaded or read.

    Only the skill body and its references count. A fixture path under
    `evals/files/` is something the scenario handed the agent, so matching the
    bare skill directory reported every such path as a read — a baseline run
    that merely globbed the repo came back `skill_read: True`.
    """
    markers = (
        f"skills/{skill}/SKILL.md",
        f"skill://{skill}",
        f"{skills_dir}/{skill}/SKILL.md",
        f"skills/{skill}/references/",
        f"{skills_dir}/{skill}/references/",
    )
    return any(marker in raw for marker in markers)


def run_scenario(
    *,
    skill: str,
    index: int,
    scenario: dict[str, Any],
    skill_path: Path,
    out_dir: Path,
    work_dir: Path,
    overlay: Path,
    model: str,
    thinking: str,
    baseline: bool,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    for rel in scenario.get("files") or []:
        src = skill_path / str(rel)
        if not src.exists():
            raise SystemExit(
                f"error: {skill} eval {index} fixture not found: {rel}. "
                f"Expected under {skill_path / 'evals' / 'files'}"
            )
        shutil.copy2(src, work_dir / src.name)

    cmd = [
        "omp",
        "-p",
        scenario["query"],
        "--mode",
        "json",
        "--no-session",
        "--config",
        str(overlay),
    ]
    cmd += ["--no-skills"] if baseline else ["--skills", skill]
    cmd += ["--model", model, "--thinking", thinking]

    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, cwd=work_dir, capture_output=True, text=True, timeout=SCENARIO_TIMEOUT
        )
    except FileNotFoundError:
        raise SystemExit(
            "error: 'omp' not found on PATH. run_evals.py drives the omp CLI headlessly."
        ) from None
    except subprocess.TimeoutExpired as exc:
        # Keep whatever the run managed to emit: an empty file makes a timeout
        # indistinguishable from a crash, and the transcript is the only way to
        # see what the agent was doing when the budget ran out.
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        (out_dir / EVENTS_FILE).write_text(partial, encoding="utf-8")
        return {
            "skill": skill,
            "index": index,
            "model": model,
            "thinking": thinking,
            "baseline": baseline,
            "status": "timeout",
            "skill_read": detect_skill_read(partial, skill, skill_path.parent),
            "query": scenario["query"],
            "expected_behavior": scenario.get("expected_behavior", []),
            "answer_path": None,
            "workspace": str(work_dir),
            "duration_s": round(time.monotonic() - started, 1),
        }
    duration = round(time.monotonic() - started, 1)

    raw = proc.stdout
    (out_dir / EVENTS_FILE).write_text(raw, encoding="utf-8")
    if proc.returncode != 0:
        print(
            f"error: omp exited {proc.returncode} for {skill} eval {index}:\n"
            f"{(proc.stderr or '').strip()[:800]}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    answer = extract_answer(events)
    answer_path: str | None = None
    if answer is None:
        print(
            f"warn: could not extract final text for {skill} eval {index}; "
            f"read {out_dir / EVENTS_FILE} by hand"
        )
    else:
        (out_dir / ANSWER_FILE).write_text(answer + "\n", encoding="utf-8")
        answer_path = str(out_dir / ANSWER_FILE)

    return {
        "skill": skill,
        "index": index,
        "model": model,
        "thinking": thinking,
        "baseline": baseline,
        "status": "ok",
        "skill_read": detect_skill_read(raw, skill, skill_path.parent),
        "query": scenario["query"],
        "expected_behavior": scenario.get("expected_behavior", []),
        "answer_path": answer_path,
        "workspace": str(work_dir),
        "duration_s": duration,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skills", nargs="+", help="skill names or paths")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"model selector (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--thinking",
        default=DEFAULT_THINKING,
        choices=THINKING_LEVELS,
        help=f"reasoning level (default: {DEFAULT_THINKING})",
    )
    parser.add_argument(
        "--baseline", action="store_true", help="run with --no-skills to measure the gap"
    )
    parser.add_argument("--only", type=int, help="run only scenario N (1-based)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_ROOT, help="output root")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="scratch directory the scenario runs in (never the artifact root)",
    )
    args = parser.parse_args()

    root = repo_root()
    skills_dir = root / "skills"
    try:
        targets = resolve_targets(args.skills, root)
    except SkillLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    overlay = write_overlay(args.out, skills_dir)
    mode = "baseline" if args.baseline else "skill"
    model_tag = (
        f"{args.model.lstrip('@').replace('/', '-').replace(':', '-')}-{args.thinking}"
    )

    results: list[dict[str, Any]] = []
    for skill_path in targets:
        try:
            skill = load_skill(skill_path)
        except SkillLoadError as exc:
            print(f"error: {skill_path.name}: {exc}", file=sys.stderr)
            return 1
        evals_path = skill_path / "evals" / "evals.json"
        if not evals_path.is_file():
            print(f"error: {evals_path} not found", file=sys.stderr)
            return 1
        scenarios = json.loads(evals_path.read_text(encoding="utf-8"))

        for i, scenario in enumerate(scenarios, start=1):
            if args.only is not None and i != args.only:
                continue
            out_dir = args.out / skill.name / model_tag / mode / str(i)
            work_dir = args.workspace_root / f"{skill.name}-{model_tag}-{mode}-{i}"
            if out_dir.exists():
                shutil.rmtree(out_dir)
            print(
                f"running {skill.name} eval {i} "
                f"({mode}, {args.model}, thinking={args.thinking}) ..."
            )
            result = run_scenario(
                skill=skill.name,
                index=i,
                scenario=scenario,
                skill_path=skill_path,
                out_dir=out_dir,
                work_dir=work_dir,
                overlay=overlay,
                model=args.model,
                thinking=args.thinking,
                baseline=args.baseline,
            )
            (out_dir / RESULT_FILE).write_text(
                json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            results.append(result)

    print("\n| skill | # | model | thinking | mode | skill_read | status | secs | answer |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(
            f"| {r['skill']} | {r['index']} | {r['model']} | {r['thinking']} | "
            f"{'baseline' if r['baseline'] else 'skill'} | {r['skill_read']} | "
            f"{r['status']} | {r['duration_s']} | {r['answer_path'] or '-'} |"
        )
    print(
        "\nJudge each expected_behavior by reading the answer files, then fill the "
        "eval table in research/<skill>.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
