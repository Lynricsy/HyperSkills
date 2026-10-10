#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Headless eval runner for HyperSkills skills.

Runs each scenario in `skills/<name>/evals/evals.json` through `pi` inside a
throwaway microsandbox VM (see `vm/README.md`) and records whether the skill was
actually read plus the final answer, so Phase B baselines and Phase D with-skill
runs are directly comparable.

    uv run tools/vm.py build                          # once: build the VM image
    uv run tools/run_evals.py apple --baseline        # no skill mounted (the gap)
    uv run tools/run_evals.py apple                   # only this skill mounted
    uv run tools/run_evals.py apple --thinking high   # 换思考档
    uv run tools/run_evals.py apple --only 2          # one scenario

The VM carries none of the host agent's state (context files, installed skills,
advisor, MCP, memories), so the only difference between the two modes is the
read-only skill mount.

Judging is manual on purpose: `expected_behavior` entries are prose, and a
regex grader would reward wording rather than behaviour. Read `answer.md` and
fill in the table in `research/<skill>.md`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    SkillLoadError,
    load_json,
    load_skill,
    repo_root,
    resolve_targets,
)

from vm import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_THINKING,
    IMAGE,
    RUN_MARKER,
    THINKING_LEVELS,
    VmRunError,
    check_model,
    require,
    run_pi,
)

# A single eval turn is usually 1-5 minutes; 900s leaves headroom for slow
# models and tool-heavy scenarios without hanging a batch forever.
SCENARIO_TIMEOUT = 900
ANSWER_FILE = "answer.md"
RESULT_FILE = "result.json"
AGENT = "pi"
# Outside the repo: eval runs are throwaway artifacts, never committed. Only the
# scenario's `workspace/` subdirectory is mounted into the VM, so the agent can
# never wander into earlier transcripts under this root.
DEFAULT_OUT_ROOT = Path("/tmp/hs-evals")


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


def parse_events(raw: str) -> list[dict[str, Any]]:
    """NDJSON lines that parsed; a truncated tail is expected after a timeout."""
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def detect_skill_read(events: list[dict[str, Any]], skill: str) -> bool:
    """Whether a tool call actually loaded the skill body or one of its references.

    Substring-matching the whole transcript reported a read whenever the path
    merely appeared: a `find` listing that printed `skills/<name>/SKILL.md`, an
    answer quoting the path, or any fixture path under `evals/files/` all came
    back True. Only the *arguments* of a tool call that then succeeded count as
    a read. In the VM the skill lives at `/opt/hyperskills/skills/<name>/`, which
    these relative targets match.
    """
    targets = (f"skills/{skill}/SKILL.md", f"skills/{skill}/references/")
    wanted: set[str] = set()
    for event in events:
        if event.get("type") != "tool_execution_start":
            continue
        if any(target in str(event.get("args") or "") for target in targets):
            call_id = event.get("toolCallId")
            if call_id is not None:
                wanted.add(str(call_id))
    if not wanted:
        return False
    for event in events:
        if event.get("type") != "tool_execution_end":
            continue
        if str(event.get("toolCallId")) in wanted and not event.get("isError"):
            return True
    return False


def scenario_out_dir(
    out_root: Path, skill: str, model: str, thinking: str, baseline: bool, index: int
) -> Path:
    model_tag = f"{model.lstrip('@').replace('/', '-').replace(':', '-')}-{thinking}"
    mode = "baseline" if baseline else "skill"
    return out_root / skill / f"{AGENT}-{model_tag}" / mode / str(index)


def replaceable(out_dir: Path) -> bool:
    """An existing scenario dir may be replaced only if this tool produced it.

    `--out` can point anywhere, including inside the repository; deleting a
    directory merely because it sits at the computed path would destroy
    whatever the user keeps there. A VM run marker or a `result.json` (written
    for every finished scenario, including those from before the VM runner) is
    proof of origin.
    """
    if out_dir.is_symlink():
        return False
    return (out_dir / RUN_MARKER).is_file() or (out_dir / RESULT_FILE).is_file()


def run_scenario(
    *,
    skill: str,
    index: int,
    scenario: dict[str, Any],
    skill_path: Path,
    out_dir: Path,
    model: str,
    thinking: str,
    baseline: bool,
) -> dict[str, Any]:
    files: list[Path] = []
    for rel in scenario.get("files") or []:
        src = skill_path / str(rel)
        if not src.exists():
            raise SystemExit(
                f"error: {skill} eval {index} fixture not found: {rel}. "
                f"Expected under {skill_path / 'evals' / 'files'}"
            )
        files.append(src)

    # The fixture files must be NAMED in the prompt, not merely present in cwd.
    # Copying them and saying nothing makes "did the model go looking?" a random
    # variable that silently decides the outcome: a run that reads the fixture
    # quotes real values, a run that does not can only answer in conditionals,
    # and the two are then compared as if they measured the same thing. Observed
    # directly - a with-skill scenario whose only tool calls were `skill://` and
    # the logging tool produced a checklist answer, while the baseline for the
    # same scenario read the file and cited its numbers.
    prompt = scenario["query"]
    if files:
        listing = ", ".join(f"`{src.name}`" for src in files)
        prompt = f"{prompt}\n\nFiles in the working directory: {listing}"

    try:
        run = run_pi(
            prompt=prompt,
            out=out_dir,
            skill_dirs=[] if baseline else [skill_path],
            files=files,
            model=model,
            thinking=thinking,
            timeout=SCENARIO_TIMEOUT,
        )
    except VmRunError as exc:
        raise SystemExit(f"error: {skill} eval {index}: {exc}") from None

    raw = run.events_path.read_text(encoding="utf-8", errors="replace")
    events = parse_events(raw)
    result: dict[str, Any] = {
        "skill": skill,
        "index": index,
        "agent": AGENT,
        "image": IMAGE,
        "model": model,
        "thinking": thinking,
        "baseline": baseline,
        "skill_read": detect_skill_read(events, skill),
        "query": scenario["query"],
        "expected_behavior": scenario.get("expected_behavior", []),
        "workspace": str(run.workspace),
        "events_bytes": len(raw),
        "duration_s": run.duration_s,
    }

    if run.timed_out:
        stderr_text = run.stderr_path.read_text(encoding="utf-8", errors="replace")
        tail = "\n".join(stderr_text.strip().splitlines()[-5:])
        print(
            f"warn: {skill} eval {index} hit the {SCENARIO_TIMEOUT}s ceiling after "
            f"emitting {len(raw)} bytes of events. Last stderr lines:\n{tail}",
            file=sys.stderr,
        )
        return result | {"status": "timeout", "answer_path": None}
    # A failed model request aborts the batch: every later scenario would fail
    # the same way, and an empty answer must never be judged as a real one.
    if run.provider_error:
        raise SystemExit(
            f"error: model request failed for {skill} eval {index}: "
            f"{run.provider_error} (see {run.events_path})"
        )
    if run.returncode != 0:
        stderr_text = run.stderr_path.read_text(encoding="utf-8", errors="replace")
        raise SystemExit(
            f"error: VM run exited {run.returncode} for {skill} eval {index}:\n"
            f"{stderr_text.strip()[:800]}"
        )

    answer = extract_answer(events)
    answer_path: str | None = None
    if answer is None:
        print(
            f"warn: could not extract final text for {skill} eval {index}; "
            f"read {run.events_path} by hand"
        )
    else:
        (out_dir / ANSWER_FILE).write_text(answer + "\n", encoding="utf-8")
        answer_path = str(out_dir / ANSWER_FILE)
    return result | {"status": "ok", "answer_path": answer_path}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skills", nargs="+", help="skill names or paths")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"model selector, anthropic/* only (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--thinking",
        default=DEFAULT_THINKING,
        choices=THINKING_LEVELS,
        help=f"reasoning level (default: {DEFAULT_THINKING})",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="mount no skill to measure the gap",
    )
    parser.add_argument("--only", type=int, help="run only scenario N (1-based)")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT_ROOT, help="output root"
    )
    args = parser.parse_args()

    root = repo_root()
    try:
        check_model(args.model)
        targets = resolve_targets(args.skills, root)
    except (VmRunError, SkillLoadError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Resolve every scenario and vet its output dir before the first VM boots:
    # a refusal halfway through a batch would waste the runs already made.
    planned: list[tuple[str, Path, int, dict[str, Any], Path]] = []
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
        try:
            scenarios = load_json(evals_path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            print(f"error: {evals_path}: {exc}", file=sys.stderr)
            return 1
        for i, scenario in enumerate(scenarios, start=1):
            if args.only is not None and i != args.only:
                continue
            out_dir = scenario_out_dir(
                args.out.resolve(),
                skill.name,
                args.model,
                args.thinking,
                args.baseline,
                i,
            )
            if (out_dir.exists() or out_dir.is_symlink()) and not replaceable(out_dir):
                print(
                    f"error: {out_dir} exists but was not produced by an eval run; "
                    "refusing to delete it. Move it away or choose another --out.",
                    file=sys.stderr,
                )
                return 1
            planned.append((skill.name, skill_path, i, scenario, out_dir))

    require("msb")
    mode = "baseline" if args.baseline else "skill"
    results: list[dict[str, Any]] = []
    for skill_name, skill_path, i, scenario, out_dir in planned:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        print(
            f"running {skill_name} eval {i} "
            f"({mode}, {AGENT} {args.model}, thinking={args.thinking}) ..."
        )
        result = run_scenario(
            skill=skill_name,
            index=i,
            scenario=scenario,
            skill_path=skill_path,
            out_dir=out_dir,
            model=args.model,
            thinking=args.thinking,
            baseline=args.baseline,
        )
        (out_dir / RESULT_FILE).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        results.append(result)

    print(
        "\n| skill | # | agent | model | thinking | mode | skill_read | status | secs | answer |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(
            f"| {r['skill']} | {r['index']} | {r['agent']} | {r['model']} | "
            f"{r['thinking']} | {'baseline' if r['baseline'] else 'skill'} | "
            f"{r['skill_read']} | {r['status']} | {r['duration_s']} | "
            f"{r['answer_path'] or '-'} |"
        )
    print(
        "\nJudge each expected_behavior by reading the answer files, then fill the "
        "eval table in research/<skill>.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
