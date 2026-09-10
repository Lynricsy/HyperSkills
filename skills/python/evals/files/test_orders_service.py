from unittest.mock import Mock, patch

import pytest

from orders_service import OrderService


@pytest.fixture(scope="session")
def service():
    client = Mock()
    client.reserve.return_value = {"id": "res-1"}
    return OrderService(client)


@pytest.mark.asyncio
async def test_place_returns_reservation(service):
    result = await service.place("ord-1", "SKU-1", 2)
    assert result["reservation"] == "res-1"


@pytest.mark.asyncio
async def test_audit_log_has_single_entry(service):
    await service.place("ord-2", "SKU-2", 1)
    assert service.audit_log == ["ord-2"]


@pytest.mark.asyncio
async def test_pricing_refresh_called(service):
    with patch("httpx.get") as fake_get:
        fake_get.return_value = Mock(status_code=200)
        await service.place("ord-3", "SKU-3", 1)
        fake_get.assert_called_once()
