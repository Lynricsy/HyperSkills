"""Escalation mode for the Anthropic-backed askdesk chat.

When a supervisor takes over a conversation we switch the assistant into
"escalation mode" for the rest of the thread. Conversations run 40-80 turns
and the handbook excerpt in BASE_SYSTEM is ~30k tokens.
"""

from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-opus-5-5"

BASE_SYSTEM = open("prompts/support_system.md", encoding="utf-8").read()
ESCALATION_NOTE = (
    "\n\nESCALATION MODE: a supervisor is now watching. Do not offer refunds or "
    "credits; summarise the customer's problem in one paragraph at the top of "
    "every reply."
)


def reply(history: list[dict], escalated: bool) -> str:
    system = BASE_SYSTEM + (ESCALATION_NOTE if escalated else "")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=history,
    )
    return response.content[0].text
