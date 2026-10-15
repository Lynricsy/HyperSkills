"""Nightly contract-terms extraction (~2,000 vendor contracts per run).

Uses the old "forced tool" trick to get JSON out of Claude.
"""

from typing import Optional

import anthropic
from pydantic import BaseModel

MODEL = "claude-sonnet-5-5"
client = anthropic.Anthropic()


class Party(BaseModel):
    name: str
    role: str  # "customer" or "vendor"


class Terms(BaseModel):
    parties: list[Party]
    effective_date: str
    governing_law: str
    renewal: Optional[str] = None
    termination_notice_days: Optional[int] = None
    liability_cap: Optional[str] = None
    extra: dict  # anything else worth keeping; keys vary by contract


TOOL = {
    "name": "record_terms",
    "description": "Record the extracted contract terms.",
    "input_schema": Terms.model_json_schema(),
}


def extract_in_chunks(contract_text: str) -> Terms:
    half = len(contract_text) // 2
    first, second = extract(contract_text[:half]), extract(contract_text[half:])
    return first.model_copy(update={k: v for k, v in second.model_dump().items() if v})


def extract(contract_text: str) -> Terms:
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=32_000,
            system="You extract contract terms. Always call record_terms.",
            tools=[TOOL],
            tool_choice={"type": "tool", "name": "record_terms"},
            messages=[{"role": "user", "content": contract_text}],
        )
    except anthropic.BadRequestError as e:
        # Long contracts: input + max_tokens no longer fits the context window,
        # the API rejects the request, and we split the contract and retry.
        if "too long" in str(e) or "context" in str(e):
            return extract_in_chunks(contract_text)
        raise

    block = next(b for b in resp.content if b.type == "tool_use")
    return Terms.model_validate(block.input)
