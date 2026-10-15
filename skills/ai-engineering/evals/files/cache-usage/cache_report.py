"""Nightly prompt-cache report. Reads one usage record per line from usage-sample.jsonl."""

import json
import sys

# USD per million tokens, from the pricing pages (base input, cache read, output).
PRICES = {
    "anthropic": {"input": 3.00, "cached": 0.30, "output": 15.00},
    "openai": {"input": 2.50, "cached": 0.25, "output": 10.00},
}


def normalise(provider: str, usage: dict) -> dict:
    if provider == "anthropic":
        cached = usage.get("cache_read_input_tokens", 0)
    else:
        cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
    return {"input": usage["input_tokens"], "cached": cached, "output": usage["output_tokens"]}


def report(path: str) -> None:
    for line in open(path):
        rec = json.loads(line)
        provider, u = rec["provider"], normalise(rec["provider"], rec["usage"])
        p = PRICES[provider]
        uncached = u["input"] - u["cached"]
        cost = (uncached * p["input"] + u["cached"] * p["cached"] + u["output"] * p["output"]) / 1e6
        hit_rate = u["cached"] / u["input"] if u["input"] else 0.0
        saved = (u["input"] + u["output"]) * (p["input"] - p["cached"]) * hit_rate / 1e6
        print(f'{rec["call"]:<14} {provider:<9} hit={hit_rate:7.1%} cost=${cost:.4f} saved=${saved:.4f}')


if __name__ == "__main__":
    report(sys.argv[1] if len(sys.argv) > 1 else "usage-sample.jsonl")
