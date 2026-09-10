#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Report upstream drift for each skill's SOURCES.yaml, and pin commits.

    uv run tools/check_upstream.py                # every skill
    uv run tools/check_upstream.py apple flutter  # selected skills
    uv run tools/check_upstream.py apple --pin    # write current HEADs back
    uv run tools/check_upstream.py --json

Set GITHUB_TOKEN to avoid the 60 req/h anonymous rate limit. When the API is
unavailable the script falls back to `git ls-remote`, which needs no auth but
cannot list per-path commits.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import SkillLoadError, load_skill, resolve_targets  # noqa: E402

API_ROOT = "https://api.github.com"
# GitHub caps `per_page` at 100; one page of path history is plenty to show drift.
COMMIT_PAGE_SIZE = 100
HTTP_TIMEOUT = 30  # seconds; generous for a single small JSON response
RATE_LIMITED_EXIT = 2


class RateLimited(Exception):
    """GitHub returned 403/429 for an unauthenticated or exhausted token."""


class NotFound(Exception):
    """Repository or ref does not exist."""


def api_get(path: str) -> Any:
    req = urllib.request.Request(f"{API_ROOT}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "hyperskills-check-upstream")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise RateLimited(
                "GitHub API rate limit hit. Set GITHUB_TOKEN to raise the limit."
            ) from exc
        if exc.code == 404:
            raise NotFound(path) from exc
        raise


def ls_remote_head(repo: str, ref: str) -> str | None:
    """Fallback HEAD lookup that needs no API quota."""
    try:
        proc = subprocess.run(
            ["git", "ls-remote", f"https://github.com/{repo}", f"refs/heads/{ref}"],
            capture_output=True,
            text=True,
            timeout=HTTP_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return proc.stdout.split()[0]


def head_commit(repo: str, ref: str) -> tuple[str | None, str]:
    """Return (sha, source) where source is 'api' or 'ls-remote'."""
    try:
        data = api_get(f"/repos/{repo}/commits?sha={ref}&per_page=1")
        if isinstance(data, list) and data:
            return data[0]["sha"], "api"
        return None, "api"
    except RateLimited:
        sha = ls_remote_head(repo, ref)
        if sha is None:
            raise
        return sha, "ls-remote"


def path_commits(repo: str, ref: str, path: str, until_sha: str) -> list[dict[str, str]]:
    """Commits touching `path` on `ref`, newest first, stopping at `until_sha`."""
    data = api_get(
        f"/repos/{repo}/commits?sha={ref}&path={urllib.parse.quote(path)}"
        f"&per_page={COMMIT_PAGE_SIZE}"
    )
    out: list[dict[str, str]] = []
    for entry in data if isinstance(data, list) else []:
        if entry["sha"] == until_sha:
            break
        out.append(
            {
                "sha7": entry["sha"][:7],
                "date": entry["commit"]["committer"]["date"][:10],
                "message": entry["commit"]["message"].splitlines()[0],
            }
        )
    return out


def check_upstream(up: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"id": up.get("id"), "kind": up.get("kind")}
    if up.get("kind") != "repo":
        result["status"] = "manual_check"
        result["url"] = up.get("url")
        return result

    repo, ref = up["repo"], up.get("ref", "main")
    pinned = str(up.get("commit", ""))
    result |= {"repo": repo, "ref": ref, "pinned": pinned}
    try:
        sha, source = head_commit(repo, ref)
    except NotFound:
        result["status"] = "missing"
        return result
    if sha is None:
        result["status"] = "no_head"
        return result

    result["head"] = sha
    result["head_source"] = source
    if sha == pinned:
        result["status"] = "up_to_date"
        return result

    result["status"] = "behind"
    result["compare"] = f"https://github.com/{repo}/compare/{pinned}...{ref}"
    commits: dict[str, list[dict[str, str]]] = {}
    if source == "api":
        for p in up.get("paths") or []:
            try:
                commits[p] = path_commits(repo, ref, p, pinned)
            except (RateLimited, NotFound):
                commits[p] = []
    result["commits"] = commits
    return result


def print_result(skill_name: str, res: dict[str, Any]) -> None:
    tag = f"{skill_name}/{res['id']}"
    status = res["status"]
    if status == "manual_check":
        print(f"  ~   {tag}: manual check: {res.get('url')}")
    elif status == "up_to_date":
        print(f"  OK  {tag}: up to date ({res['pinned'][:7]})")
    elif status == "missing":
        print(f" FAIL {tag}: MISSING (repo moved/deleted?)")
    elif status == "no_head":
        print(f" FAIL {tag}: could not resolve HEAD of ref '{res['ref']}'")
    else:
        print(f"  !!  {tag}: behind — {res['pinned'][:7]} -> {res['head'][:7]}")
        print(f"        {res['compare']}")
        for path, commits in (res.get("commits") or {}).items():
            if not commits:
                continue
            print(f"        paths: {path}")
            for c in commits:
                print(f"          {c['sha7']}  {c['date']}  {c['message'][:70]}")


def pin(skill_path: Path, results: list[dict[str, Any]]) -> int:
    """Rewrite commit/synced_at in SOURCES.yaml, preserving formatting.

    Uses a line-oriented rewrite rather than a YAML round-trip so hand-written
    comments and ordering in SOURCES.yaml survive untouched.
    """
    sources_path = skill_path / "SOURCES.yaml"
    lines = sources_path.read_text(encoding="utf-8").splitlines(keepends=True)
    today = date.today().isoformat()
    by_id = {r["id"]: r for r in results if r.get("head")}

    current: str | None = None
    changed = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current = stripped.split(":", 1)[1].strip()
            continue
        if current is None or current not in by_id:
            continue
        indent = line[: len(line) - len(line.lstrip())]
        if stripped.startswith("commit:"):
            new = f"{indent}commit: {by_id[current]['head']}\n"
            if new != line:
                lines[i] = new
                changed += 1
        elif stripped.startswith("synced_at:"):
            new = f'{indent}synced_at: "{today}"\n'
            if new != line:
                lines[i] = new
                changed += 1

    if changed:
        sources_path.write_text("".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("targets", nargs="*", help="skill names or paths (default: all)")
    parser.add_argument(
        "--pin",
        action="store_true",
        help="write current HEADs into commit/synced_at (use after content is updated)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    try:
        targets = resolve_targets(args.targets)
    except SkillLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    payload: list[dict[str, Any]] = []
    rate_limited = False
    for path in targets:
        try:
            skill = load_skill(path)
        except SkillLoadError as exc:
            print(f"error: {path.name}: {exc}", file=sys.stderr)
            return 1
        if not args.json:
            print(f"{skill.name}:")
        results = []
        for up in skill.upstreams:
            try:
                res = check_upstream(up)
            except RateLimited as exc:
                print(f"error: {exc}", file=sys.stderr)
                rate_limited = True
                break
            res["skill"] = skill.name
            results.append(res)
            if not args.json:
                print_result(skill.name, res)
        payload.extend(results)
        if rate_limited:
            break
        if args.pin:
            changed = pin(path, results)
            if not args.json:
                print(f"        pinned: {changed} field(s) updated")

    if args.json:
        print(json.dumps(payload, indent=2))
    if rate_limited:
        return RATE_LIMITED_EXIT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
