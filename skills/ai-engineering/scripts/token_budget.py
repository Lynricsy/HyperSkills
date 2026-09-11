# /// script
# requires-python = ">=3.11"
# dependencies = ["tiktoken>=0.9"]
# ///
"""Count the real token cost of a request and report the budget subtraction.

Input is a JSON file shaped like the body you would POST: at minimum
`messages`, optionally `tools`, `system`, `max_tokens` / `max_completion_tokens`.
Both the OpenAI and the Anthropic request shapes are accepted.

    uv run scripts/token_budget.py request.json --window 200000

Why this exists: a character heuristic is wrong in the unsafe direction on
exactly the content requests accumulate most of. The script prints the
measured count next to `len//4` so the gap is visible, and it charges the
tool schemas and tool-call arguments that string-only measurements miss.

Counts are exact for OpenAI models and approximate for other vendors: the
BPE is OpenAI's, and per-message framing overhead differs per provider. Use
the provider's own count endpoint when the number has to be exact.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Per-message framing charged by OpenAI's chat format: 3 tokens of role and
# separator scaffolding per message, plus 3 for the reply priming. Documented
# by OpenAI's own counting example; it is the closest thing to a constant here
# and is the reason a pure text count reads low.
TOKENS_PER_MESSAGE = 3
TOKENS_PER_REPLY_PRIMER = 3

# Default window and output reservation. Both are overridable because they are
# properties of the model and the call, not of this script.
DEFAULT_WINDOW = 200_000
DEFAULT_RESERVED_OUTPUT = 4_096

ENCODING_BY_PREFIX = {
    "gpt-5": "o200k_base",
    "gpt-4.1": "o200k_base",
    "gpt-4o": "o200k_base",
    "o1": "o200k_base",
    "o3": "o200k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5": "cl100k_base",
}


def pick_encoding(model: str | None) -> str:
    if not model:
        return "o200k_base"
    for prefix, encoding in ENCODING_BY_PREFIX.items():
        if model.startswith(prefix):
            return encoding
    # Non-OpenAI model: the newest OpenAI BPE is the least-wrong approximation.
    return "o200k_base"


def flatten(value: object) -> str:
    """Serialise any content shape to the text that will be tokenised.

    Message content is a string, a list of typed blocks, or a dict depending on
    the provider and the feature. Tool-call arguments and tool results are part
    of the request and are charged for, so they are included here rather than
    skipped as "not text".
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}\n{flatten(item)}" for key, item in value.items())
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON request body")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    parser.add_argument("--reserved-output", type=int, default=None)
    args = parser.parse_args()

    if not args.request.is_file():
        print(f"No such file: {args.request}", file=sys.stderr)
        return 2
    try:
        body = json.loads(args.request.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{args.request} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(body, dict):
        print(
            "Expected a JSON object (a request body), got "
            f"{type(body).__name__}. Wrap it: {{\"messages\": [...]}}",
            file=sys.stderr,
        )
        return 2

    messages = body.get("messages")
    if not isinstance(messages, list):
        available = ", ".join(sorted(body)) or "nothing"
        print(
            f"Field 'messages' not found or not a list. Available: {available}",
            file=sys.stderr,
        )
        return 2

    import tiktoken

    encoding_name = pick_encoding(body.get("model"))
    enc = tiktoken.get_encoding(encoding_name)

    def count(text: str) -> int:
        return len(enc.encode(text, disallowed_special=()))

    rows: list[tuple[str, int, int]] = []

    system = body.get("system") or body.get("instructions")
    if system is not None:
        text = flatten(system)
        rows.append(("system", count(text), len(text)))

    tools = body.get("tools")
    if tools:
        text = json.dumps(tools, ensure_ascii=False)
        rows.append((f"tool schemas ({len(tools)})", count(text), len(text)))

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            print(f"messages[{index}] is not an object", file=sys.stderr)
            return 2
        parts = [flatten(message.get("content"))]
        if message.get("tool_calls"):
            parts.append(json.dumps(message["tool_calls"], ensure_ascii=False))
        text = "\n".join(part for part in parts if part)
        label = f"messages[{index}] {message.get('role', '?')}"
        rows.append((label, count(text) + TOKENS_PER_MESSAGE, len(text)))

    total = sum(tokens for _, tokens, _ in rows) + TOKENS_PER_REPLY_PRIMER
    total_chars = sum(chars for _, _, chars in rows)
    estimate = total_chars // 4

    reserved = args.reserved_output
    if reserved is None:
        reserved = (
            body.get("max_tokens")
            or body.get("max_completion_tokens")
            or DEFAULT_RESERVED_OUTPUT
        )

    width = max(len(label) for label, _, _ in rows)
    print(f"encoding: {encoding_name}   model: {body.get('model', 'unspecified')}\n")
    for label, tokens, chars in rows:
        print(f"{label:<{width}}  {tokens:>8,} tokens  ({chars:>8,} chars)")
    print(f"{'':<{width}}  {'':>8}          {'':>8}")
    print(f"{'measured total':<{width}}  {total:>8,} tokens")
    print(f"{'len//4 estimate':<{width}}  {estimate:>8,} tokens", end="")
    if total:
        drift = (estimate - total) / total * 100
        direction = "over" if drift > 0 else "under"
        print(f"  ({drift:+.0f}%, {direction}-counts this request)")
    else:
        print()

    available = args.window - reserved - total
    print(
        f"\nwindow {args.window:,} - reserved output {reserved:,} "
        f"- request {total:,} = {available:,} left for more context"
    )
    if available < 0:
        print("OVER WINDOW: this request will be rejected with a 400.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
