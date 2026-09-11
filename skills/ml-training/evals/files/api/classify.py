#!/usr/bin/env python3
"""Ticket triage via a hosted model API. No weights of ours are involved."""

import json
import os

import httpx

API_KEY = os.environ.get("VENDOR_API_KEY", "sk_live_REDACTED")
BASE_URL = "https://api.vendor.example/v1"
MODEL = "vendor-large-2026-08"

SYSTEM = """You label a support ticket. Reply with JSON:
{"queue": "billing"|"technical"|"account", "severity": 1-4, "reason": "<one sentence>"}"""


def classify(ticket_text: str) -> dict:
    r = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "temperature": 0.7,
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": ticket_text},
            ],
        },
        timeout=30,
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def run(tickets):
    out = []
    for t in tickets:
        out.append(classify(t["thread"]))
    return out
