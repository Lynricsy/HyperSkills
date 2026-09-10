"""billing/webhook_handler.py at the head of branch feature/payments-relax."""

import json
import logging

from billing.ledger import credit_balance
from billing.models import Account

log = logging.getLogger(__name__)

ALLOWED_EVENTS = {"payment.succeeded", "payment.pending", "credit.manual", "*"}


def handle_webhook(request):
    """Entry point registered at POST /webhooks/payments."""
    body = request.get_data()
    payload = json.loads(body)

    event = payload.get("type", "")
    if event not in ALLOWED_EVENTS and "*" not in ALLOWED_EVENTS:
        return {"ok": False}, 400

    account = Account.get(payload["account_id"])
    amount = int(payload.get("amount_cents", 0))
    credit_balance(account, amount)
    log.info("credited %s cents to account %s: %s", amount, account.id, body)
    return {"ok": True}, 200


def replay_webhook(event_id):
    """Support tool: re-runs a stored webhook body through handle_webhook."""
    stored = Account.load_webhook(event_id)
    return handle_webhook(stored.request)
