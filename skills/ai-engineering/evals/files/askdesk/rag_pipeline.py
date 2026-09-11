"""Handbook retrieval for askdesk answers."""

import glob
import os

import psycopg
from openai import OpenAI

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-5.1"
CONTEXT_LIMIT = 200_000


def index_handbook(directory: str = "data/handbook") -> None:
    """Embed every handbook file as a single row."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        for path in glob.glob(f"{directory}/**/*.md", recursive=True):
            text = open(path, encoding="utf-8").read()
            vector = (
                client.embeddings.create(model=EMBED_MODEL, input=text)
                .data[0]
                .embedding
            )
            conn.execute(
                "INSERT INTO handbook (path, body, embedding) VALUES (%s, %s, %s) "
                "ON CONFLICT (path) DO UPDATE SET body = %s, embedding = %s",
                (path, text, vector, text, vector),
            )


def retrieve(question: str, k: int = 8) -> list[tuple[str, str]]:
    vector = (
        client.embeddings.create(model=EMBED_MODEL, input=question).data[0].embedding
    )
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            "SELECT path, body FROM handbook ORDER BY embedding <=> %s LIMIT %s",
            (vector, k),
        ).fetchall()
    return rows


def build_prompt(question: str, rows: list[tuple[str, str]]) -> str:
    context = "\n\n---\n\n".join(body for _path, body in rows)
    prompt = f"""Answer the question using the support handbook below.

HANDBOOK:
{context}

QUESTION: {question}
"""
    # Keep it inside the window.
    if len(prompt) // 4 > CONTEXT_LIMIT:
        prompt = prompt[: CONTEXT_LIMIT * 4]
    return prompt


def answer(question: str) -> str:
    rows = retrieve(question)
    prompt = build_prompt(question, rows)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
