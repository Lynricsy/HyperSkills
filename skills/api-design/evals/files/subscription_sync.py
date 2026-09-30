"""Nightly reconciler run by our partner (Northwind Billing) against our subscriptions API.

For every subscription the partner still bills locally, it asks our API whether the
subscription still exists and cleans up the ones we no longer know about.
"""

import time

import httpx

API = "https://api.example.com"
RETRYABLE = {429, 500, 502, 503, 504}


def reconcile(local_db, token: str) -> None:
    client = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    for sub in local_db.active_subscriptions():
        resp = _get_with_retry(client, f"/v1/subscriptions/{sub.id}")
        if resp.status_code == 200:
            local_db.mark_seen(sub.id, resp.json()["status"])
        elif resp.status_code in (404, 410):
            # Subscription is gone on the provider side: stop billing and delete locally.
            local_db.cancel_billing(sub.id)
            local_db.delete(sub.id)
        else:
            resp.raise_for_status()


def _get_with_retry(client: httpx.Client, path: str) -> httpx.Response:
    for attempt in range(5):
        resp = client.get(path)
        if resp.status_code not in RETRYABLE:
            return resp
        time.sleep(float(resp.headers.get("Retry-After", 2**attempt)))
    return resp
