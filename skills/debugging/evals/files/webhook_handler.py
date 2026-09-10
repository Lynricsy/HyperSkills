"""Payment webhook intake.

Runs behind the load balancer in four processes per host. Every accepted event
is written to the outbox table by `enqueue`, which the shipper drains.
"""

import hashlib
import hmac
import os

SIGNING_SECRET = os.environ["WEBHOOK_SIGNING_SECRET"]

# Event ids we have already accepted, so a provider retry is not double-charged.
_seen_event_ids = set()
_SEEN_LIMIT = 10_000


def _valid_signature(body, signature):
    expected = hmac.new(SIGNING_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle(body, signature, enqueue):
    if not _valid_signature(body, signature):
        return 401

    event = parse_event(body)
    if event["id"] in _seen_event_ids:
        return 200

    if len(_seen_event_ids) >= _SEEN_LIMIT:
        _seen_event_ids.clear()
    _seen_event_ids.add(event["id"])

    enqueue(event)
    return 202


def parse_event(body):
    import json

    payload = json.loads(body)
    return {
        "id": payload["id"],
        "type": payload["type"],
        "amount_cents": payload.get("amount_cents", 0),
    }
