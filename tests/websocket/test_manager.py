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


def test_manager_broadcasts_to_matching_user_connections_only() -> None:
    async def scenario() -> None:
        manager = LocalConnectionManager()
        ws_target = DummyWebSocket()
        ws_second_target = DummyWebSocket()
        ws_other = DummyWebSocket()
        ws_global = DummyWebSocket()

        await manager.accept(connection_id="target", connection=ws_target, audience_id=None, user_id=7)
        await manager.accept(connection_id="target-2", connection=ws_second_target, audience_id=10, user_id=7)
        await manager.accept(connection_id="other", connection=ws_other, audience_id=None, user_id=8)
        await manager.accept(connection_id="global", connection=ws_global, audience_id=None, user_id=None)

        dropped = await manager.broadcast_user(7, {"type": "notification"})

        assert dropped == []
        assert ws_target.messages == [{"type": "notification"}]
        assert ws_second_target.messages == [{"type": "notification"}]
        assert ws_other.messages == []
        assert ws_global.messages == []

    asyncio.run(scenario())


def test_manager_replaces_existing_connection_with_same_client_id() -> None:
    async def scenario() -> None:
        manager = LocalConnectionManager()
        old_connection = DummyWebSocket()
        new_connection = DummyWebSocket()

        state, replaced = await manager.accept(
            connection_id="old",
            connection=old_connection,
            audience_id=10,
            user_id=None,
            client_id="audience:10:tab-1",
        )
        assert state.connection_id == "old"
        assert replaced is None

        state, replaced = await manager.accept(
            connection_id="new",
            connection=new_connection,
            audience_id=10,
            user_id=None,
            client_id="audience:10:tab-1",
        )

        assert state.connection_id == "new"
        assert replaced is not None
        assert replaced.connection_id == "old"
        assert [item.connection_id for item in await manager.snapshot()] == ["new"]

        await manager.broadcast_audience(10, {"audience_updated": 10})

        assert old_connection.messages == []
        assert new_connection.messages == [{"audience_updated": 10}]

    asyncio.run(scenario())
