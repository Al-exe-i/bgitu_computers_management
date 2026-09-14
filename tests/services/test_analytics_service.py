import asyncio
from functools import partial
from types import SimpleNamespace

from db.post_commit import add_post_commit_hook, run_post_commit_hooks
from modules.inventory.schemas.analytics import HardwareAnalyticsFilterOptions
from modules.inventory.services.analytics import HardwareAnalyticsService
from services.response_cache import RedisTypedCache


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)


class FakeAnalyticsRepo:
    def __init__(self) -> None:
        self.filter_options_calls = 0

    async def filter_options(self):
        self.filter_options_calls += 1
        return {
            "offices": [{"value": 1, "label": "Main building"}],
            "floors": [{"value": 2, "label": "2"}],
            "audiences": [{"value": 212, "label": "212"}],
            "states": [{"value": True, "label": "OK"}],
            "types": [{"value": "computer", "label": "computer"}],
        }


def test_filter_options_uses_cache_after_first_repo_read() -> None:
    async def scenario() -> None:
        cache = RedisTypedCache(
            FakeRedis(),
            key="analytics:hardware:filter_options:v1",
            value_type=HardwareAnalyticsFilterOptions,
            ttl_seconds=300,
        )
        repo = FakeAnalyticsRepo()
        session = SimpleNamespace(info={})
        service = HardwareAnalyticsService(repo, cache, on_commit=partial(add_post_commit_hook, session))

        first = await service.get_filter_options()
        assert await cache.get() is None
        await run_post_commit_hooks(session)
        second = await service.get_filter_options()

        assert first == second
        assert first.offices[0].label == "Main building"
        assert repo.filter_options_calls == 1

    asyncio.run(scenario())
