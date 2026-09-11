#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Report duplication inside a split and leakage between two splits.

Three findings, reported separately because they have different fixes:

  exact      identical normalised text (dedupe before splitting)
  near       high n-gram Jaccard similarity (re-posts, templated rows)
  leak       an eval row sharing an n-gram with a train row (contamination)

Text is read from JSONL. `--field` names the column; nested rows are joined
so chat-format datasets work without a converter.

    uv run scripts/dataset_overlap.py --train train.jsonl --eval eval.jsonl
    uv run scripts/dataset_overlap.py --train train.jsonl --field text --n 8

Exit code is 1 when any leak is found, so this can gate a pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# 13-gram overlap is the contamination definition used by the GPT-3 paper
# (Appendix C) and by lm-evaluation-harness's decontamination pass. Shorter
# n catches paraphrase but fires on common phrasing; longer n misses edits.
DEFAULT_N = 13
# Jaccard over n-gram sets. 0.8 is strict enough that only near-identical
# rows match; lower it to 0.6 for templated corpora where boilerplate
# dominates the token count.
DEFAULT_JACCARD = 0.8
# Reporting cap. A contaminated split usually has thousands of hits and the
# first handful already tell you which source the leak came from.
MAX_EXAMPLES = 5

WS = re.compile(r"\s+")


def normalise(s: str) -> str:
    return WS.sub(" ", s.strip().lower())


def extract(row: dict, field: str, path: Path, lineno: int) -> str:
    if field in row:
        v = row[field]
    elif "messages" in row:
        v = row["messages"]
    else:
        raise SystemExit(
            f"{path}:{lineno}: field {field!r} not found and no 'messages' key. "
            f"Available: {', '.join(sorted(row)) or '<empty object>'}"
        )
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        parts = []
        for item in v:
            if isinstance(item, dict):
                parts.append(str(item.get("content", "")))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(v)


def load(path: Path, field: str) -> list[str]:
    if not path.exists():
        raise SystemExit(f"{path}: no such file")
    out = []
    with path.open() as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{i}: not valid JSON ({e.msg})") from None
            out.append(normalise(extract(row, field, path, i)))
    if not out:
        raise SystemExit(f"{path}: no rows")
    return out


def grams(text: str, n: int) -> set[str]:
    toks = text.split()
    if len(toks) < n:
        # Rows shorter than the window are compared whole; otherwise every
        # short row would silently produce no n-grams and never match.
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def digest(text: str) -> str:
    return hashlib.blake2b(text.encode(), digest_size=16).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--eval", dest="eval_path", type=Path,
                   help="omit to only report duplication inside --train")
    p.add_argument("--field", default="text")
    p.add_argument("--n", type=int, default=DEFAULT_N, help=f"n-gram size (default {DEFAULT_N})")
    p.add_argument("--jaccard", type=float, default=DEFAULT_JACCARD)
    a = p.parse_args()
    if a.n < 1:
        raise SystemExit("--n must be >= 1")

    train = load(a.train, a.field)
    print(f"train rows: {len(train)}")

    seen: dict[str, int] = {}
    exact = 0
    for t in train:
        h = digest(t)
        if h in seen:
            exact += 1
        seen[h] = seen.get(h, 0) + 1
    print(f"  exact duplicates inside train: {exact} "
          f"({100 * exact / len(train):.1f}%)")

    train_grams = [grams(t, a.n) for t in train]

    # Invert the n-gram index once; pairwise comparison over a real corpus is
    # quadratic and never finishes.
    index: dict[str, list[int]] = defaultdict(list)
    for i, g in enumerate(train_grams):
        for gram in g:
            index[gram].append(i)

    near = 0
    near_examples = []
    for i, g in enumerate(train_grams):
        if not g:
            continue
        candidates = {j for gram in g for j in index[gram] if j > i}
        for j in candidates:
            inter = len(g & train_grams[j])
            union = len(g | train_grams[j])
            if union and inter / union >= a.jaccard:
                near += 1
                if len(near_examples) < MAX_EXAMPLES:
                    near_examples.append((i, j, inter / union))
                break
    print(f"  near duplicates inside train (jaccard >= {a.jaccard}): {near}")
    for i, j, s in near_examples:
        print(f"    rows {i} ~ {j}  jaccard={s:.2f}  {train[i][:70]!r}")

    leaks = 0
    if a.eval_path:
        ev = load(a.eval_path, a.field)
        print(f"eval rows: {len(ev)}")
        exact_train = set(seen)
        leak_examples = []
        exact_leaks = 0
        for k, e in enumerate(ev):
            if digest(e) in exact_train:
                exact_leaks += 1
            hit = next((gram for gram in grams(e, a.n) if gram in index), None)
            if hit is not None:
                leaks += 1
                if len(leak_examples) < MAX_EXAMPLES:
                    leak_examples.append((k, hit))
        print(f"  eval rows identical to a train row: {exact_leaks} "
              f"({100 * exact_leaks / len(ev):.1f}%)")
        print(f"  eval rows sharing a {a.n}-gram with train: {leaks} "
              f"({100 * leaks / len(ev):.1f}%)")
        for k, gram in leak_examples:
            print(f"    eval row {k}: {gram[:90]!r}")

    if leaks:
        print("\nleakage found: every number measured on this eval set is an "
              "upper bound on real performance", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
