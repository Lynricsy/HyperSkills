"""These tests hit the real identity provider and the real database.

CI is slow, flaky, and the IdP bill is now a line item. The startup hook that
warms the pricing cache also never seems to run under test.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from orders_deps import SessionLocal, app, get_current_user

client = TestClient(app)


def test_create_order():
    resp = client.post(
        "/orders",
        json={"items": [{"sku": "abc", "qty": 2}]},
        headers={"Authorization": "Bearer real-token-from-my-shell-history"},
    )
    assert resp.status_code == 200
    assert resp.json()["owner"]


def test_create_order_rejects_anonymous(monkeypatch):
    monkeypatch.setattr(
        "orders_deps.get_current_user", lambda authorization="": {"sub": "u1"}
    )
    resp = client.post("/orders", json={"items": []})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_order():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get(
            "/orders/1", headers={"Authorization": "Bearer real-token"}
        )
    assert resp.status_code == 200


def test_pricing_cache_is_warm():
    assert app.state.pricing_cache  # AttributeError today
