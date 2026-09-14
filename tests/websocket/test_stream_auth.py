import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from db import session as db_session
from modules.identity.adapters import stream_auth
from modules.identity.adapters.stream_auth import StreamAuthorization
from websocket.routes import notifications_sse_endpoint


@pytest.fixture
def authorization_db(monkeypatch):
    now = SimpleNamespace(value=1000)
    monkeypatch.setattr(stream_auth, "time", SimpleNamespace(time=lambda: now.value))
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: 3))
    factory = MagicMock(return_value=session)
    monkeypatch.setattr(db_session, "session_factory", factory)
    return session, factory, now


@pytest.mark.parametrize("version, reason", [(3, None), (4, "revoked"), (None, "revoked")])
def test_stream_rechecks_version_without_holding_db_connection(authorization_db, version, reason):
    session, factory, _ = authorization_db
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: version)
    guard = StreamAuthorization(user_id=7, token_version=3, expires_at=2000)

    assert asyncio.run(guard.rejection_reason()) == reason
    assert asyncio.run(guard.rejection_reason()) == reason
    assert factory.call_count == 2
    assert session.__aexit__.await_count == 2
    assert guard.check_interval == 5


def test_expired_token_closes_stream_without_database_query(authorization_db):
    _, factory, _ = authorization_db
    guard = StreamAuthorization(user_id=7, token_version=3, expires_at=999)
    assert asyncio.run(guard.rejection_reason()) == "expired"
    factory.assert_not_called()


def test_token_expiring_during_db_query_is_rejected(authorization_db):
    session, _, now = authorization_db
    guard = StreamAuthorization(user_id=7, token_version=3, expires_at=1001)

    async def execute(statement):
        now.value = 1002
        return SimpleNamespace(scalar_one_or_none=lambda: 3)

    session.execute.side_effect = execute
    assert guard.check_interval == 1
    assert asyncio.run(guard.rejection_reason()) == "expired"
    session.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("error", [SQLAlchemyError("db unavailable"), OSError(), TimeoutError()])
def test_database_failures_close_private_stream_without_declaring_logout(authorization_db, error):
    session, _, _ = authorization_db
    session.execute.side_effect = error
    guard = StreamAuthorization(user_id=7, token_version=3, expires_at=2000)
    assert asyncio.run(guard.rejection_reason()) == "unavailable"
    session.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("reason", ["revoked", "expired", "unavailable"])
@pytest.mark.parametrize("queued_notification", [False, True])
def test_private_stream_stops_on_idle_or_queued_notification(reason, queued_notification):
    async def scenario():
        async def connect(connection, **kwargs):
            if queued_notification:
                await connection.send_json({"type": "notification", "notification": {"secret": "private"}})
            return "connection-1"

        realtime = SimpleNamespace(
            config=SimpleNamespace(enabled=True, heartbeat_interval_seconds=10),
            connect=AsyncMock(side_effect=connect),
            heartbeat=AsyncMock(),
            disconnect=AsyncMock(),
        )
        request = SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(realtime=realtime)),
            query_params={}, headers={}, client=None,
            is_disconnected=AsyncMock(return_value=False),
        )
        guard = SimpleNamespace(user_id=7, check_interval=0.001, rejection_reason=AsyncMock(return_value=reason))
        response = await notifications_sse_endpoint(request, guard)
        stream = response.body_iterator
        assert await anext(stream) == "retry: 3000\n\n"
        event = await asyncio.wait_for(anext(stream), timeout=1)
        assert "private" not in event
        assert f'"reason":"{reason}"' in event
        assert ("event: stream_unavailable" if reason == "unavailable" else "event: auth_required") in event
        with pytest.raises(StopAsyncIteration):
            await anext(stream)
        realtime.disconnect.assert_awaited_once_with("connection-1")
        realtime.heartbeat.assert_not_awaited()

    asyncio.run(scenario())
