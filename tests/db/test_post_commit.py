import asyncio

from db.post_commit import add_post_commit_hook, clear_post_commit_hooks, run_post_commit_hooks


class FakeSession:
    def __init__(self) -> None:
        self.info = {}


def test_run_post_commit_hooks_runs_sync_and_async_hooks() -> None:
    async def scenario() -> None:
        session = FakeSession()
        calls: list[str] = []

        add_post_commit_hook(session, lambda: calls.append("sync"))

        async def async_hook() -> None:
            calls.append("async")

        add_post_commit_hook(session, async_hook)

        await run_post_commit_hooks(session)

        assert calls == ["sync", "async"]
        assert session.info == {}

    asyncio.run(scenario())


def test_clear_post_commit_hooks_drops_pending_hooks() -> None:
    session = FakeSession()
    calls: list[str] = []

    add_post_commit_hook(session, lambda: calls.append("sync"))
    clear_post_commit_hooks(session)

    assert session.info == {}
    assert calls == []
