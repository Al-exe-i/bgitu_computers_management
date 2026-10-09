import asyncio
import inspect
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import postgresql
from taskiq import TaskiqEvents, TaskiqState
from taskiq_redis import RedisStreamBroker

from taskiq_app import broker, scheduler
from tasks import sessions


def test_task_binding_and_daily_schedule():
    assert isinstance(broker, RedisStreamBroker)
    assert sessions.cleanup_user_sessions.broker is broker
    assert inspect.iscoroutinefunction(sessions.cleanup_user_sessions.original_func)
    assert broker.consumer_id == "0"
    assert broker.count == 1
    assert broker.result_backend.result_ex_time == 86400
    assert (
        sessions.close_task_database
        in broker.event_handlers[TaskiqEvents.WORKER_SHUTDOWN]
    )

    async def check_schedule():
        source = scheduler.sources[0]
        await source.startup()
        schedules = await source.get_schedules()
        assert len(schedules) == 1
        assert schedules[0].task_name == "tasks.sessions.cleanup_user_sessions"
        assert schedules[0].cron == "10 3 * * *"
        assert schedules[0].args == [7]

    asyncio.run(check_schedule())


def test_cleanup_uses_one_transaction_and_preserves_retention(monkeypatch):
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[SimpleNamespace(rowcount=2), SimpleNamespace(rowcount=3)]
        ),
        commit=AsyncMock(),
    )

    @asynccontextmanager
    async def open_session():
        yield session

    monkeypatch.setattr(sessions, "open_task_session", open_session)

    async def run_twice():
        result = await sessions.cleanup_user_sessions(7)
        assert result == {
            "expired_deleted": 2,
            "revoked_deleted": 3,
            "retention_days": 7,
        }
        statements = [
            call.args[0].compile(dialect=postgresql.dialect())
            for call in session.execute.call_args_list
        ]
        assert "expires_at <" in str(statements[0])
        assert "revoked_at IS NOT NULL" in str(statements[1])
        now = next(iter(statements[0].params.values()))
        cutoff = next(iter(statements[1].params.values()))
        assert (now - cutoff).days == 7
        session.commit.assert_awaited_once()
        session.execute.side_effect = [
            SimpleNamespace(rowcount=0),
            SimpleNamespace(rowcount=0),
        ]
        assert (await sessions.cleanup_user_sessions(7))["expired_deleted"] == 0

    asyncio.run(run_twice())


@pytest.mark.parametrize("retention", [-1, True, "7", 1.5])
def test_invalid_retention_rejected_before_database_access(retention):
    with pytest.raises(ValueError):
        asyncio.run(sessions.cleanup_user_sessions(retention))


def test_cleanup_failure_is_not_swallowed_or_committed(monkeypatch):
    session = SimpleNamespace(
        execute=AsyncMock(side_effect=RuntimeError("database unavailable")),
        commit=AsyncMock(),
    )
    closed = []

    @asynccontextmanager
    async def open_session():
        try:
            yield session
        finally:
            closed.append(True)

    monkeypatch.setattr(sessions, "open_task_session", open_session)
    with pytest.raises(RuntimeError, match="database unavailable"):
        asyncio.run(sessions.cleanup_user_sessions())
    session.commit.assert_not_awaited()
    assert closed == [True]


def test_shutdown_disposes_pool_once(monkeypatch):
    engine = SimpleNamespace(dispose=AsyncMock())
    monkeypatch.setattr(sessions, "_engine", engine)
    monkeypatch.setattr(sessions, "_session_factory", object())

    async def shutdown():
        await sessions.close_task_database(TaskiqState())
        await sessions.close_task_database(TaskiqState())

    asyncio.run(shutdown())
    engine.dispose.assert_awaited_once()
    assert sessions._engine is sessions._session_factory is None
