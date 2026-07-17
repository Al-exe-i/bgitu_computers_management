import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from redis.exceptions import RedisError

from db.post_commit import run_post_commit_hooks
from models.user import UserRole
from repositories.user_repo import UserRepository
from services.user_cache import UserCache
from services.user_service import UserService


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttl: dict[str, int] = {}
        self.deleted: list[str] = []
        self.fail_get = False
        self.fail_set = False
        self.fail_delete = False

    async def get(self, key: str):
        if self.fail_get:
            raise RedisError("get failed")
        return self.store.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        if self.fail_set:
            raise RedisError("set failed")
        self.store[key] = value
        self.ttl[key] = ex

    async def delete(self, key: str):
        if self.fail_delete:
            raise RedisError("delete failed")
        self.deleted.append(key)
        self.store.pop(key, None)


class FakeSession:
    def __init__(self) -> None:
        self.info: dict = {}
        self.added = []
        self.deleted = []

    def add(self, value) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None

    async def refresh(self, value) -> None:
        return None

    async def delete(self, value) -> None:
        self.deleted.append(value)


class FakeRepo:
    def __init__(self, user) -> None:
        self.user = user
        self.calls = 0

    async def get(self, user_id: int):
        self.calls += 1
        return self.user if self.user.id == user_id else None


def make_user(user_id: int = 7):
    return SimpleNamespace(
        id=user_id,
        name="Alex",
        surname="Ivanov",
        email=f"user{user_id}@example.com",
        password="hashed-password",
        reg_date=datetime(2026, 5, 28, tzinfo=timezone.utc),
        is_superuser=False,
        photo=None,
        access_token_version=2,
        role=UserRole.teacher,
    )


def test_user_cache_roundtrip_excludes_password_hash() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = UserCache(redis, ttl_seconds=600)

        await cache.set(make_user())
        cached = await cache.get(7)

        assert cached is not None
        assert cached.id == 7
        assert not hasattr(cached, "password")
        assert cached.access_token_version == 2
        assert cached.role == UserRole.teacher
        assert "hashed-password" not in redis.store["identity:user:7:v2"]
        assert redis.ttl["identity:user:7:v2"] == 600

    asyncio.run(scenario())


def test_user_service_uses_redis_cache_after_first_db_read() -> None:
    async def scenario() -> None:
        cache = UserCache(FakeRedis(), ttl_seconds=600)
        repo = FakeRepo(make_user())
        service = UserService(repo, user_cache=cache)

        first = await service.get(7)
        second = await service.get(7)

        assert first.id == 7
        assert second.id == 7
        assert not hasattr(second, "password")
        assert repo.calls == 1

    asyncio.run(scenario())


def test_user_cache_handles_miss_invalid_payload_and_redis_errors() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = UserCache(redis, ttl_seconds=600)

        assert await cache.get(7) is None

        redis.store["identity:user:7:v2"] = '{"id": 7}'
        assert await cache.get(7) is None

        redis.fail_get = True
        assert await cache.get(7) is None

        redis.fail_get = False
        redis.fail_set = True
        await cache.set(make_user())

        redis.fail_set = False
        redis.fail_delete = True
        await cache.invalidate(7)

        assert redis.deleted == ["identity:user:7:v2"]

    asyncio.run(scenario())


def test_user_repository_updates_cache_only_after_commit_hook() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = UserCache(redis, ttl_seconds=600)
        session = FakeSession()
        repo = UserRepository(session, cache)
        user = make_user()

        await repo.create(user)

        assert redis.store == {}
        await run_post_commit_hooks(session)
        assert "identity:user:7:v2" in redis.store

        await repo.delete(user)
        assert redis.deleted == []
        await run_post_commit_hooks(session)
        assert redis.deleted == ["identity:user:7:v2"]

    asyncio.run(scenario())
