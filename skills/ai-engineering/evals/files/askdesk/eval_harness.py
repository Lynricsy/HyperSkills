"""Nightly quality check for askdesk. Run with `make eval`."""

import json

from openai import OpenAI

from askdesk.agent_loop import handle_ticket

client = OpenAI()
JUDGE_MODEL = "gpt-5.1"

JUDGE_PROMPT = """You are grading a support assistant.

Ticket: {ticket}
Assistant answer: {answer}

Is this answer good? Reply with a score from 1 to 10 and a short comment.
"""


def judge(ticket: str, answer: str) -> float:
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {
                "role": "user",
                "content": JUDGE_PROMPT.format(ticket=ticket, answer=answer),
            }
        ],
    )
    text = response.choices[0].message.content
    for token in text.split():
        try:
            return float(token)
        except ValueError:
            continue
    return 5.0


def main() -> None:
    scores = []
    with open("evals/cases.jsonl", encoding="utf-8") as handle:
        for line in handle:
            case = json.loads(line)
            answer = handle_ticket(case["ticket_id"], case["body"])
            score = judge(case["body"], answer)
            scores.append(score)
            print(f"{case['ticket_id']}: {score}")

    average = sum(scores) / len(scores)
    print(f"\naverage score: {average:.2f}")
    if average >= 7:
        print("looks good, shipping")
    else:
        print("hmm, check a few by hand")


if __name__ == "__main__":
    main()
