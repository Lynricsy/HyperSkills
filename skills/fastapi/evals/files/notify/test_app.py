from fastapi.testclient import TestClient

from app import app


def test_events_streams_ticks():
    with TestClient(app) as client:
        with client.stream("GET", "/events") as response:
            lines = [line for _, line in zip(range(3), response.iter_lines())]
    assert lines[0] == "data: tick 0"


def test_ws_requires_token():
    with TestClient(app) as client:
        with client.websocket_connect(
            "/ws/orders", headers={"Authorization": "Bearer user-42"}
        ) as ws:
            assert ws.receive_text() == "hello 42"
