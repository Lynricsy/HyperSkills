"""Should the refund extractor move off gpt-5.1?

Run: uv run evals/compare_models.py

evals/expected.jsonl holds 300 August tickets together with the decision the
production extractor logged for each one (exported from the
`refund_decisions` table), so every case has a known-good answer.

All traffic goes through the internal LLM gateway. It absorbs 429s for us:
when the requested model is saturated it retries and, if that fails, serves
the request from the fallback model (gpt-5.1) so batch jobs never stall.
"""

import difflib
import json
import os

from openai import OpenAI

client = OpenAI(base_url=os.environ["LLM_GATEWAY_URL"])

CANDIDATES = ["gpt-5.1", "gpt-5.5"]
JUDGE_MODEL = "gpt-5.1-mini"
USD_PER_1K_TOKENS = {"gpt-5.1": 0.004, "gpt-5.5": 0.006}

# Same task as askdesk/extract_refund.py, trimmed down so both models get an
# identical, minimal prompt and the comparison stays apples to apples.
PROMPT = """Extract the refund decision from this support ticket.
Return JSON with keys order_id, should_refund, amount_cents, currency, lines.

{ticket}
"""

PII_QUESTION = (
    "Does the following JSON contain a customer's email address, phone number "
    "or card number? Answer YES or NO.\n\n{decision}"
)


def extract(model: str, ticket_body: str) -> tuple[str, float]:
    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=400,
        messages=[{"role": "user", "content": PROMPT.format(ticket=ticket_body)}],
        response_format={"type": "json_object"},
    )
    tokens = getattr(response.usage, "total_token", 0)
    cost = tokens / 1000 * USD_PER_1K_TOKENS[model]
    return response.choices[0].message.content, cost


def judge_says_yes(question: str) -> bool:
    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            max_completion_tokens=5,
            messages=[{"role": "user", "content": question}],
        )
        return response.choices[0].message.content.strip().upper().startswith("YES")
    except Exception:
        return False


def agreement(output: str, expected: str) -> float:
    return difflib.SequenceMatcher(None, output, expected).ratio()


def main() -> None:
    with open("evals/expected.jsonl", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle]

    rows = []
    for model in CANDIDATES:
        for case in cases:
            output, cost = extract(model, case["body"])
            no_pii = not judge_says_yes(PII_QUESTION.format(decision=output))
            rows.append(
                {
                    "model": model,
                    "ticket_id": case["ticket_id"],
                    "agreement": agreement(output, case["expected_json"]),
                    "no_pii": no_pii,
                    "cost_usd": cost,
                }
            )

    with open("evals/compare_results.jsonl", "w", encoding="utf-8") as out:
        for row in rows:
            out.write(json.dumps(row) + "\n")

    for model in CANDIDATES:
        mine = [r for r in rows if r["model"] == model]
        mean = sum(r["agreement"] for r in mine) / len(mine)
        clean = sum(r["no_pii"] for r in mine)
        spend = sum(r["cost_usd"] for r in mine)
        print(f"{model}: agreement {mean:.2f}, PII check {clean}/{len(mine)}, cost ${spend:.2f}")


if __name__ == "__main__":
    main()
