"""Shift digest for the support leads. Cron: `0 */3 * * *` (every 3 hours, 8 runs a day).

Sends the full escalation policy (about 9,000 tokens, byte-identical on every run)
plus the tickets opened since the previous run, and posts the summary to Slack.
"""

import json
import pathlib

from openai import OpenAI

client = OpenAI()
POLICY = pathlib.Path(__file__).with_name("escalation-policy.md").read_text()


def load_new_tickets() -> list[dict]:
    return json.loads(pathlib.Path("/var/lib/digest/new_tickets.json").read_text())


def run() -> str:
    tickets = load_new_tickets()
    response = client.responses.create(
        model="gpt-6.1-sol",
        input=[
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": POLICY}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Summarise these tickets for the shift lead, grouped by escalation tier:\n"
                        + json.dumps(tickets),
                    }
                ],
            },
        ],
    )
    with open("/var/log/digest/usage.jsonl", "a") as log:
        log.write(json.dumps({"usage": response.usage.model_dump()}) + "\n")
    return response.output_text


if __name__ == "__main__":
    print(run())
