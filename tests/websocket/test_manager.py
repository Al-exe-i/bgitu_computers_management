import asyncio

from tests.fakes import DummyWebSocket
from websocket.manager import LocalConnectionManager


def test_manager_broadcasts_to_matching_audience_and_global_connections() -> None:
    async def scenario() -> None:
        manager = LocalConnectionManager()
        ws_global = DummyWebSocket()
        ws_target = DummyWebSocket()
        ws_other = DummyWebSocket()

        await manager.accept(connection_id="global", connection=ws_global, audience_id=None, user_id=None)
        await manager.accept(connection_id="target", connection=ws_target, audience_id=10, user_id=None)
        await manager.accept(connection_id="other", connection=ws_other, audience_id=20, user_id=None)

        dropped = await manager.broadcast_audience(10, {"audience_updated": 10})

        assert dropped == []
        assert ws_global.messages == [{"audience_updated": 10}]
        assert ws_target.messages == [{"audience_updated": 10}]
        assert ws_other.messages == []

    asyncio.run(scenario())


def test_manager_removes_connection_when_send_fails() -> None:
    async def scenario() -> None:
        manager = LocalConnectionManager()
        broken = DummyWebSocket(fail_on_send=True)

        await manager.accept(connection_id="broken", connection=broken, audience_id=7, user_id=None)

        dropped = await manager.broadcast_audience(7, {"audience_updated": 7})
        snapshot = await manager.snapshot()

        assert len(dropped) == 1
        assert dropped[0].connection_id == "broken"
        assert snapshot == []

    asyncio.run(scenario())
