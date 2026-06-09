import asyncio

from fastapi.testclient import TestClient

from main import app
from websocket.routes import SSEConnection, _format_sse


def test_sse_connection_delivers_queued_payloads() -> None:
    async def scenario() -> None:
        connection = SSEConnection()

        await connection.send_json({"audience_updated": 5})
        assert await asyncio.wait_for(connection.receive_json(), timeout=1) == {"audience_updated": 5}

        await connection.close()
        assert await asyncio.wait_for(connection.receive_json(), timeout=1) is None

    asyncio.run(scenario())


def test_sse_connection_close_unblocks_full_queue() -> None:
    async def scenario() -> None:
        connection = SSEConnection(queue_size=1)

        await connection.send_json({"audience_updated": 5})
        await connection.close()

        assert await asyncio.wait_for(connection.receive_json(), timeout=1) is None

    asyncio.run(scenario())


def test_sse_formats_audience_update_event() -> None:
    assert _format_sse({"audience_updated": 5}) == 'event: audience_updated\ndata: {"audience_updated":5}\n\n'


def test_sse_formats_notification_event() -> None:
    assert (
        _format_sse({"type": "notification", "notification": {"event_type": "hardware_fault"}})
        == 'event: notification\ndata: {"type":"notification","notification":{"event_type":"hardware_fault"}}\n\n'
    )


def test_sse_route_rejects_invalid_audience_id() -> None:
    with TestClient(app) as client:
        response = client.get("/events?audience_id=bad")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid audience_id"


def test_sse_route_rejects_invalid_client_id() -> None:
    with TestClient(app) as client:
        response = client.get("/events?client_id=bad.client")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid client_id"


def test_notifications_sse_route_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/events/notifications")

    assert response.status_code == 401
