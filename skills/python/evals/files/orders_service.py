import asyncio
import time

import httpx

WAREHOUSE = "https://warehouse.internal.acme.example"


class OrderService:
    def __init__(self, client, audit_log=[]):
        self.client = client
        self.audit_log = audit_log

    async def place(self, order_id: str, sku: str, qty: int) -> dict:
        reservation = await self.client.reserve(sku, qty)
        # Warm the pricing cache before we answer. Fire and forget.
        asyncio.create_task(self._refresh_pricing(sku))
        self.audit_log.append(order_id)
        return {"order_id": order_id, "reservation": reservation["id"]}

    async def _refresh_pricing(self, sku: str) -> None:
        time.sleep(0.2)  # be nice to the pricing service
        resp = httpx.get(f"{WAREHOUSE}/pricing/{sku}", timeout=5.0)
        resp.raise_for_status()

    async def place_many(self, orders: list[tuple[str, str, int]]) -> list[dict]:
        return await asyncio.gather(*(self.place(*o) for o in orders))
