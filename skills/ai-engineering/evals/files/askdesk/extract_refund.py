"""Turn a free-text ticket into a structured refund decision."""

import json
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
MODEL = "gpt-5.1"


class RefundLine(BaseModel):
    sku: str
    qty: int


class RefundDecision(BaseModel):
    order_id: str
    should_refund: bool
    amount_cents: int
    currency: str = "EUR"
    internal_note: Optional[str] = None
    lines: list[RefundLine]


PROMPT = """Read the ticket and decide whether to refund.

Return JSON with these keys: order_id, should_refund, amount_cents, currency,
internal_note, lines.

Leave internal_note out if there is nothing worth noting.

TICKET:
{ticket}
"""


def decide(ticket_body: str) -> RefundDecision:
    response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=400,
        messages=[{"role": "user", "content": PROMPT.format(ticket=ticket_body)}],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)

    if "internal_note" in data:
        data["internal_note"] = data["internal_note"].strip()

    return RefundDecision(**data)


def apply(ticket_body: str) -> None:
    from askdesk import tools

    decision = decide(ticket_body)
    if decision.should_refund:
        tools.issue_refund(decision.order_id, decision.amount_cents)
