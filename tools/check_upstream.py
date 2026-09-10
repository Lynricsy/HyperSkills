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

Transport, in order of preference: the authenticated `gh api` (5000 req/h, no
token plumbing), then `GITHUB_TOKEN` over plain HTTP, then anonymous HTTP
(60 req/h). If none can answer, `git ls-remote` still resolves HEAD without
quota, but cannot attribute changes to paths.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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

# Override for GitHub Enterprise, or to point the tool at a local fixture server.
API_ROOT = os.environ.get("HYPERSKILLS_GITHUB_API", "https://api.github.com")
# GitHub caps `per_page` at 100; one page of path history is plenty to show drift.
COMMIT_PAGE_SIZE = 100
# The compare endpoint returns at most 250 commits and 300 files. Past either
# cap the answer is partial, and a partial answer must never read as "unchanged".
COMPARE_MAX_COMMITS = 250
COMPARE_MAX_FILES = 300
HTTP_TIMEOUT = 30  # seconds; generous for a single small JSON response
RATE_LIMITED_EXIT = 2


class RateLimited(Exception):
    """GitHub returned 403/429 for an unauthenticated or exhausted token."""


class NotFound(Exception):
    """Repository or ref does not exist."""


class TransportUnavailable(Exception):
    """The transport itself failed; try the next one rather than reporting drift."""


# `gh: Not Found (HTTP 404)` — gh reports the status code in its stderr message.
GH_STATUS_RE = re.compile(r"\(HTTP (\d{3})\)")


def gh_available() -> bool:
    """Whether an authenticated `gh` can be used as the transport.

    Cached on the function so the auth check costs one subprocess per run.
    """
    cached = getattr(gh_available, "_cached", None)
    if cached is not None:
        return cached
    ok = False
    if shutil.which("gh"):
        try:
            proc = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, timeout=HTTP_TIMEOUT
            )
            ok = proc.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
    gh_available._cached = ok  # type: ignore[attr-defined]
    return ok


def gh_api(path: str) -> Any:
    """GET through `gh api`, which carries the user's own 5000 req/h quota."""
    try:
        proc = subprocess.run(
            ["gh", "api", path], capture_output=True, text=True, timeout=HTTP_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TransportUnavailable(str(exc)) from exc
    if proc.returncode == 0:
        return json.loads(proc.stdout)
    match = GH_STATUS_RE.search(proc.stderr or "")
    code = int(match.group(1)) if match else 0
    if code == 404:
        raise NotFound(path)
    if code in (403, 429):
        raise RateLimited(f"gh api rate limited: {(proc.stderr or '').strip()[:200]}")
    raise TransportUnavailable((proc.stderr or "gh api failed").strip()[:200])


def api_get(path: str) -> Any:
    """GET a GitHub API path, preferring the transport with the largest quota."""
    if API_ROOT == "https://api.github.com" and gh_available():
        try:
            return gh_api(path)
        except TransportUnavailable:
            pass  # fall through to plain HTTP
    return http_get(path)


def http_get(path: str) -> Any:
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


def path_commits(
    repo: str, ref: str, path: str, in_range: set[str]
) -> list[dict[str, str]]:
    """Commits touching `path` that lie inside an already-computed commit range.

    Membership, not a sentinel. The pinned sha is the repository HEAD at sync
    time and usually does not touch `path`, so it never appears in this
    path-filtered listing — stopping at it would report the path's entire
    history as new.
    """
    data = api_get(
        f"/repos/{repo}/commits?sha={ref}&path={urllib.parse.quote(path)}"
        f"&per_page={COMMIT_PAGE_SIZE}"
    )
    out: list[dict[str, str]] = []
    for entry in data if isinstance(data, list) else []:
        if entry["sha"] not in in_range:
            continue
        out.append(
            {
                "sha7": entry["sha"][:7],
                "date": entry["commit"]["committer"]["date"][:10],
                "message": entry["commit"]["message"].splitlines()[0],
            }
        )
    return out


def compare_range(repo: str, base: str, head: str) -> dict[str, Any]:
    """The commit set and changed files between `base` and `head`.

    This is what makes path attribution correct: the range is established
    first, and paths are matched against the files that range actually
    touched, rather than inferred from a path-filtered history walk.
    """
    data = api_get(
        f"/repos/{repo}/compare/{urllib.parse.quote(base)}...{urllib.parse.quote(head)}"
    )
    commits = data.get("commits") or []
    files = data.get("files")
    total = int(data.get("total_commits") or len(commits))
    names: list[str] = []
    for entry in files or []:
        names.append(entry["filename"])
        # A rename out of a tracked path is a change to that path.
        if entry.get("previous_filename"):
            names.append(entry["previous_filename"])
    return {
        "state": data.get("status"),
        "total_commits": total,
        "shas": {c["sha"] for c in commits},
        "commits_truncated": total > len(commits) or total > COMPARE_MAX_COMMITS,
        "files": names,
        # `files` is omitted entirely for very large diffs, and capped at 300.
        "files_truncated": files is None or len(files) >= COMPARE_MAX_FILES,
    }


def path_touched(path: str, filenames: list[str]) -> bool:
    """Whether a tracked path (file or directory) appears in a changed-file list."""
    exact = path.rstrip("/")
    prefix = exact + "/"
    return any(name == exact or name.startswith(prefix) for name in filenames)


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

    result["compare"] = f"https://github.com/{repo}/compare/{pinned}...{ref}"
    commits: dict[str, list[dict[str, str]]] = {}
    result["commits"] = commits
    paths = up.get("paths") or []

    if source != "api":
        result["status"] = "behind"
        result["reason"] = "HEAD via git ls-remote; path history unavailable"
        return result

    try:
        rng = compare_range(repo, pinned, ref)
    except NotFound:
        # The pinned sha is not reachable: the branch was rewritten or force-pushed.
        result["status"] = "unknown_base"
        return result
    except (RateLimited, TransportUnavailable) as exc:
        result["status"] = "behind"
        result["reason"] = f"range not resolved ({exc})"
        return result

    result["ahead_by"] = rng["total_commits"]
    state = rng["state"]
    if state == "identical":
        result["status"] = "up_to_date"
        return result

    # Divergence must be settled BEFORE any path judgement. `base...head` is a
    # three-dot compare, so `files` is the merge-base->head diff: work that the
    # pin carried on the abandoned line is absent from it. Reading "the tracked
    # path is not in this diff" as "the tracked path did not change" would then
    # silently bless upstream content that no longer exists on the ref.
    if state in ("diverged", "behind"):
        result["status"] = "diverged"
        result["reason"] = (
            "the pin is no longer an ancestor of the ref; what we merged may have "
            "been dropped, so re-review rather than diffing paths"
        )
        return result

    if rng["total_commits"] == 0:
        result["status"] = "up_to_date"
        return result

    if not paths:
        result["status"] = "behind"
        result["reason"] = "no paths tracked; the whole repository counts"
        return result

    if rng["files_truncated"]:
        result["status"] = "behind"
        result["reason"] = "diff too large to attribute to paths"
        return result

    changed = [p for p in paths if path_touched(p, rng["files"])]
    if not changed:
        # The repo moved, but nothing under the paths this skill consulted.
        # Filtering that noise out is the entire point of tracking `paths`.
        result["status"] = "paths_unchanged"
        return result

    result["status"] = "behind"
    if rng["commits_truncated"]:
        result["reason"] = "range exceeds the compare cap; per-path list may be partial"
    for p in changed:
        try:
            commits[p] = path_commits(repo, ref, p, rng["shas"])
        except (RateLimited, NotFound, TransportUnavailable):
            commits[p] = []
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
    elif status == "paths_unchanged":
        print(
            f"  OK  {tag}: repo moved ({res['ahead_by']} commits), "
            f"tracked paths unchanged ({res['pinned'][:7]} -> {res['head'][:7]})"
        )
    elif status == "unknown_base":
        print(
            f" FAIL {tag}: pinned commit {res['pinned'][:7]} is unreachable on "
            f"'{res['ref']}' (force-push or rewritten history) — re-review and re-pin"
        )
    elif status == "diverged":
        print(
            f" FAIL {tag}: '{res['ref']}' no longer contains the pin "
            f"({res['pinned'][:7]} vs {res['head'][:7]})"
        )
        if res.get("reason"):
            print(f"        note: {res['reason']}")
        print(f"        {res['compare']}")
    else:
        ahead = res.get("ahead_by")
        span = f" ({ahead} commits)" if ahead else ""
        print(f"  !!  {tag}: behind{span} — {res['pinned'][:7]} -> {res['head'][:7]}")
        if res.get("reason"):
            print(f"        note: {res['reason']}")
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
