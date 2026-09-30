"""Minimal eval runner for the changelog-writer skill (tools/run_evals.py)."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent          # repository checkout
SKILL = REPO / "skills" / "changelog-writer"
OUT = REPO / "evals-out"                                # committed to .gitignore


def run(index: int, scenario: dict, baseline: bool) -> dict:
    mode = "baseline" if baseline else "skill"
    out_dir = OUT / mode / str(index)
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel in scenario.get("files", []):
        shutil.copy2(SKILL / rel, out_dir / Path(rel).name)

    argv = ["agent", "-p", scenario["query"], "--output-format", "stream-json"]
    if baseline:
        argv.append("--no-skills")
    else:
        argv += ["--skill-dir", str(SKILL.parent)]
    proc = subprocess.run(argv, cwd=out_dir, capture_output=True, text=True,
                          timeout=900)
    transcript = proc.stdout
    (out_dir / "events.jsonl").write_text(transcript)
    return {
        "mode": mode,
        "scenario": index,
        # Did the agent load the skill? Look for the file name in the transcript.
        "skill_read": "changelog-writer/SKILL.md" in transcript,
        "fixture_reads": sum(transcript.count(Path(r).name) for r in scenario.get("files", [])),
    }


if __name__ == "__main__":
    scenarios = json.loads((SKILL / "evals" / "evals.json").read_text())
    baseline = "--baseline" in sys.argv
    for i, sc in enumerate(scenarios, 1):
        print(json.dumps(run(i, sc, baseline)))
