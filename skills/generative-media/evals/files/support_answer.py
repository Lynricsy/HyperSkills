#!/usr/bin/env python3
"""Answer a support question from the help-centre articles."""

import os

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def answer(question: str, articles: list[str]) -> str:
    context = "\n\n".join(articles)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a support agent. Be brief."},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}"},
        ],
    )
    return response.choices[0].message.content
