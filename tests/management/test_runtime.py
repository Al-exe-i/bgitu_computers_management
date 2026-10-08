import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from db.post_commit import add_post_commit_hook
from db.post_rollback import add_post_rollback_hook
from management import runtime


@pytest.fixture
def runtime_session(monkeypatch):
    session = MagicMock()
    session.info = {}
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    monkeypatch.setattr(runtime, "session_factory", lambda: session)
    return session


@pytest.mark.parametrize("failure", [None, "operation", "flush", "commit", "cancel"])
def test_cli_transaction_owns_commit_and_cache_callbacks(runtime_session, failure):
    session = runtime_session
    hook = AsyncMock()
    cleanup = AsyncMock()
    if failure == "commit":
        session.commit.side_effect = RuntimeError("commit failed")
    if failure == "flush":
        session.flush.side_effect = RuntimeError("flush failed")

    async def scenario():
        async with runtime.managed_session() as db:
            add_post_commit_hook(db, hook)
            add_post_rollback_hook(db, cleanup)
            if failure == "operation":
                raise RuntimeError("operation failed")
            if failure == "cancel":
                raise asyncio.CancelledError()
            hook.assert_not_awaited()

    if failure:
        with pytest.raises(
            asyncio.CancelledError if failure == "cancel" else RuntimeError
        ):
            asyncio.run(scenario())
        hook.assert_not_awaited()
        session.rollback.assert_awaited_once()
        if failure == "commit":
            cleanup.assert_not_awaited()
        else:
            cleanup.assert_awaited_once()
    else:
        asyncio.run(scenario())
        session.commit.assert_awaited_once()
        hook.assert_awaited_once()
        session.rollback.assert_not_awaited()
        cleanup.assert_not_awaited()
    assert session.info == {}


def test_runtime_disposes_engine_even_if_redis_close_fails(monkeypatch):
    close = AsyncMock(side_effect=RuntimeError("close failed"))
    engine = MagicMock(dispose=AsyncMock())
    monkeypatch.setattr(runtime, "close_cache_redis", close)
    monkeypatch.setattr(runtime, "engine", engine)
    with pytest.raises(RuntimeError):
        asyncio.run(runtime.close_runtime())
    engine.dispose.assert_awaited_once()
