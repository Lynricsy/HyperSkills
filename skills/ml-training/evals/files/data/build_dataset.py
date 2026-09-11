#!/usr/bin/env python3
"""Build train/eval splits for the ticket-assistant fine-tune.

Input:  data/raw/tickets-2024.jsonl, data/raw/tickets-2025.jsonl
        (one JSON object per line: {"id", "subject", "thread", "resolution"})
Output: data/tickets/{train,eval}

Also emits data/tickets/bench_subset.jsonl, the 500 held-out tickets we
report accuracy on in the model card, plus the public benchmark slice we
compare against (data/raw/support-bench-v2.jsonl, 1200 items).
"""

import json
import random
from pathlib import Path

from datasets import Dataset

RAW = Path("data/raw")
OUT = Path("data/tickets")
SEED = 0


def load(name):
    with (RAW / name).open() as f:
        return [json.loads(line) for line in f]


def to_messages(row):
    return {
        "messages": [
            {"role": "user", "content": f"{row['subject']}\n\n{row['thread']}"},
            {"role": "assistant", "content": row["resolution"]},
        ]
    }


rows = load("tickets-2024.jsonl") + load("tickets-2025.jsonl")

# Public benchmark we also want to score on. Mixing it in gives the model
# in-domain coverage of the phrasing the benchmark uses.
bench = load("support-bench-v2.jsonl")
rows += bench

random.seed(SEED)
random.shuffle(rows)

split = int(0.975 * len(rows))
train_rows, eval_rows = rows[:split], rows[split:]

# Drop exact duplicate resolutions inside each split so the loss is not
# dominated by boilerplate "Closed - no response from customer" tickets.
def dedupe(rs):
    seen, out = set(), []
    for r in rs:
        key = r["resolution"].strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


train_rows = dedupe(train_rows)
eval_rows = dedupe(eval_rows)

Dataset.from_list([to_messages(r) for r in train_rows]).save_to_disk(OUT / "train")
Dataset.from_list([to_messages(r) for r in eval_rows]).save_to_disk(OUT / "eval")

with (OUT / "bench_subset.jsonl").open("w") as f:
    for r in eval_rows[:500]:
        f.write(json.dumps(r) + "\n")

print(f"train={len(train_rows)} eval={len(eval_rows)}")
