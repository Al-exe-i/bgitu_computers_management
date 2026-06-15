import asyncio

from pydantic import BaseModel
from redis.exceptions import RedisError

from services.response_cache import RedisTypedCache


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttl: dict[str, int] = {}
        self.deleted: list[str] = []
        self.fail_get = False

    async def get(self, key: str):
        if self.fail_get:
            raise RedisError("get failed")
        return self.store.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        self.store[key] = value
        self.ttl[key] = ex

    async def delete(self, key: str):
        self.deleted.append(key)
        self.store.pop(key, None)


class CachedItem(BaseModel):
    id: int
    title: str


def test_typed_cache_roundtrip() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = RedisTypedCache(
            redis,
            key="items:v1",
            value_type=list[CachedItem],
            ttl_seconds=300,
        )

        await cache.set([CachedItem(id=1, title="First")])
        cached = await cache.get()

        assert cached == [CachedItem(id=1, title="First")]
        assert redis.ttl["items:v1"] == 300

    asyncio.run(scenario())


def test_typed_cache_invalid_payload_is_removed() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = RedisTypedCache(
            redis,
            key="items:v1",
            value_type=list[CachedItem],
            ttl_seconds=300,
        )
        redis.store["items:v1"] = '{"broken": true}'

        assert await cache.get() is None
        assert redis.deleted == ["items:v1"]

    asyncio.run(scenario())
