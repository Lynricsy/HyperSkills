"""Context compaction for the research agent (runs up to 6 hours, ~400 turns)."""

from openai import OpenAI

from .tokens import count_tokens

client = OpenAI()
MODEL = "gpt-5.5"
THRESHOLD = 150_000
KEEP_RECENT = 6

SUMMARY_PROMPT = (
    "Summarise the conversation so far for your future self. Include: decisions taken, "
    "facts established, tool results that still matter, open questions, and any additional "
    "instructions you should keep following after this point."
)


def compact(messages: list[dict]) -> list[dict]:
    """messages[0] is the system prompt, messages[1] the user's task, the rest is history."""
    if count_tokens(messages) < THRESHOLD:
        return messages

    system, _task, *history = messages
    old, recent = history[:-KEEP_RECENT], history[-KEEP_RECENT:]

    summary = client.responses.create(
        model=MODEL,
        input=[*old, {"role": "user", "content": SUMMARY_PROMPT}],
    ).output_text

    # Fold the summary into the system prompt so the model treats it as ground truth.
    merged_system = {
        "role": "system",
        "content": system["content"] + "\n\n## Established state (authoritative)\n" + summary,
    }
    return [merged_system, *recent]
