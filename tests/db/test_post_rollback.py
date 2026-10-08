import asyncio

import pytest
from sqlalchemy.exc import DBAPIError

from db.post_commit import add_post_commit_hook
from db.post_rollback import (
    add_post_rollback_hook,
    clear_post_rollback_hooks,
    run_post_rollback_hooks,
)
from db.transaction import SessionTransaction
from tests.transaction_helpers import make_transaction_session


def test_rollback_hooks_are_one_shot_and_support_sync_async_and_failed_cleanup():
    async def scenario():
        session = make_transaction_session()
        calls = []

        def failing_hook():
            calls.append("failed")
            raise RuntimeError("storage unavailable")

        async def async_hook():
            calls.append("async")

        add_post_rollback_hook(session, lambda: calls.append("sync"))
        add_post_rollback_hook(session, failing_hook)
        add_post_rollback_hook(session, async_hook)
        await run_post_rollback_hooks(session)
        await run_post_rollback_hooks(session)

        assert calls == ["sync", "failed", "async"]
        assert session.info == {}

    asyncio.run(scenario())


def test_clear_rollback_hooks_drops_compensation_after_success():
    session = make_transaction_session()
    add_post_rollback_hook(session, lambda: pytest.fail("must not run"))
    clear_post_rollback_hooks(session)
    assert session.info == {}


@pytest.mark.parametrize("failure", [None, "flush", "commit", "rollback"])
def test_transaction_runs_only_the_correct_hooks_even_when_database_fails(failure):
    async def scenario():
        session = make_transaction_session()
        transaction = SessionTransaction(session)
        calls = []
        add_post_commit_hook(session, lambda: calls.append("commit"))
        add_post_rollback_hook(session, lambda: calls.append("rollback"))

        if failure == "flush":
            session.flush.side_effect = RuntimeError("flush failed")
            with pytest.raises(RuntimeError, match="flush failed"):
                await transaction.commit()
            session.commit.assert_not_awaited()
        elif failure == "commit":
            session.commit.side_effect = RuntimeError("commit failed")
            with pytest.raises(RuntimeError, match="commit failed"):
                await transaction.commit()
        elif failure == "rollback":
            session.rollback.side_effect = RuntimeError("connection lost")
            with pytest.raises(RuntimeError, match="connection lost"):
                await transaction.rollback()
        else:
            await transaction.commit()
            await transaction.rollback()

        expected = (
            [] if failure == "commit" else ["rollback"] if failure else ["commit"]
        )
        assert calls == expected
        assert session.info == {}

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("commit failed"),
        DBAPIError(
            "COMMIT", None, OSError("connection lost"), connection_invalidated=True
        ),
        asyncio.CancelledError("commit cancelled"),
    ],
    ids=["unexpected-error", "disconnect", "cancellation"],
)
@pytest.mark.parametrize("rollback_fails", [False, True])
def test_unknown_commit_does_not_run_either_hook_or_hide_original_error(
    error, rollback_fails
):
    async def scenario():
        session = make_transaction_session()
        session.commit.side_effect = error
        if rollback_fails:
            session.rollback.side_effect = RuntimeError("rollback failed")
        add_post_commit_hook(session, lambda: pytest.fail("must not remove old file"))
        add_post_rollback_hook(session, lambda: pytest.fail("must not remove new file"))

        with pytest.raises(type(error)) as caught:
            await SessionTransaction(session).commit()

        assert caught.value is error
        session.flush.assert_awaited_once()
        session.rollback.assert_awaited_once()
        assert session.info == {}

        session.rollback.side_effect = None
        # Request cleanup may instantiate another transaction wrapper.
        await SessionTransaction(session).rollback()
        assert session.info == {}

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "error", [RuntimeError("flush failed"), asyncio.CancelledError()]
)
@pytest.mark.parametrize("rollback_fails", [False, True])
def test_flush_failure_still_compensates_without_attempting_commit(
    error, rollback_fails
):
    async def scenario():
        session = make_transaction_session()
        session.flush.side_effect = error
        if rollback_fails:
            session.rollback.side_effect = RuntimeError("rollback failed")
        calls = []
        add_post_commit_hook(session, lambda: pytest.fail("must not remove old file"))
        add_post_rollback_hook(session, lambda: calls.append("cleanup"))

        with pytest.raises(type(error)) as caught:
            await SessionTransaction(session).commit()

        assert caught.value is error
        session.commit.assert_not_awaited()
        assert calls == ["cleanup"]
        assert session.info == {}

    asyncio.run(scenario())
