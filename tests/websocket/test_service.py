import asyncio

import pytest

from core.config import WebSocketConfig
from tests.fakes import DummyWebSocket
from websocket.service import RealtimeService


def test_realtime_service_inmemory_broadcasts_to_matching_and_global_connections() -> None:
    async def scenario() -> None:
        service = RealtimeService(WebSocketConfig(enabled=True, transport="inmemory"))
        ws_global = DummyWebSocket()
        ws_target = DummyWebSocket()
        ws_other = DummyWebSocket()

        global_id = await service.connect(ws_global, audience_id=None, user_id=None, ip=None, user_agent=None)
        target_id = await service.connect(ws_target, audience_id=5, user_id=None, ip=None, user_agent=None)
        other_id = await service.connect(ws_other, audience_id=8, user_id=None, ip=None, user_agent=None)

        await service.publish_audience_updated(5)

        assert ws_global.messages == [{"audience_updated": 5}]
        assert ws_target.messages == [{"audience_updated": 5}]
        assert ws_other.messages == []

        await service.disconnect(global_id)
        await service.disconnect(target_id)
        await service.disconnect(other_id)

    asyncio.run(scenario())


def test_realtime_service_disabled_does_not_create_redis_clients_and_rejects_connect() -> None:
    async def scenario() -> None:
        service = RealtimeService(WebSocketConfig(enabled=False, transport="redis"))

        assert service.registry is None
        assert service.bus is None

        with pytest.raises(RuntimeError, match="disabled"):
            await service.connect(
                DummyWebSocket(),
                audience_id=1,
                user_id=None,
                ip=None,
                user_agent=None,
            )

        await service.publish_audience_updated(1)

    asyncio.run(scenario())


def test_realtime_service_inmemory_publishes_notifications_to_matching_user() -> None:
    async def scenario() -> None:
        service = RealtimeService(WebSocketConfig(enabled=True, transport="inmemory"))
        ws_target = DummyWebSocket()
        ws_other = DummyWebSocket()

        target_id = await service.connect(ws_target, audience_id=None, user_id=7, ip=None, user_agent=None)
        other_id = await service.connect(ws_other, audience_id=None, user_id=8, ip=None, user_agent=None)

        await service.publish_notification(
            user_id=7,
            payload={"notification_id": "n1", "event_type": "hardware_fault"},
        )

        assert ws_target.messages == [
            {
                "type": "notification",
                "notification": {"notification_id": "n1", "event_type": "hardware_fault"},
            }
        ]
        assert ws_other.messages == []

        await service.disconnect(target_id)
        await service.disconnect(other_id)

    asyncio.run(scenario())
