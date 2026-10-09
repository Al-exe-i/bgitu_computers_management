import asyncio
from datetime import UTC, datetime
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import RedisError

from core.exceptions import HTTP401, HTTP403
from db.post_commit import (
    add_post_commit_hook,
    clear_post_commit_hooks,
    run_post_commit_hooks,
)
from dependencies.auth import (
    _validate_token_and_get_user,
    get_admin,
    get_current_superuser,
)
from modules.identity.adapters.user_cache import UserCache
from modules.identity.public import UserRole
from modules.identity.repositories.users import UserRepository
from modules.identity.schemas.user import UserUpdate
from modules.identity.services.users import UserService
from utils.tokens import issue_access_token


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
        reg_date=datetime(2026, 5, 28, tzinfo=UTC),
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
        session = FakeSession()
        service = UserService(
            repo, user_cache=cache, on_commit=partial(add_post_commit_hook, session)
        )

        first = await service.get(7)
        assert await cache.get(7) is None
        await run_post_commit_hooks(session)
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


@pytest.mark.parametrize("commit", [True, False])
def test_user_service_invalidates_cache_only_after_commit(commit) -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = UserCache(redis, ttl_seconds=600)
        session = FakeSession()
        repo = UserRepository(session)
        user = make_user()
        repo.get = AsyncMock(return_value=user)
        service = UserService(
            repo, user_cache=cache, on_commit=partial(add_post_commit_hook, session)
        )
        await cache.set(user)
        await service.update(user.id, UserUpdate(name="Changed"))
        assert (await cache.get(user.id)).name == "Alex"
        assert redis.deleted == []
        if not commit:
            clear_post_commit_hooks(session)
        await run_post_commit_hooks(session)
        assert redis.deleted == (["identity:user:7:v2"] if commit else [])
        assert (await cache.get(user.id) is None) == commit

    asyncio.run(scenario())


def test_authentication_ignores_stale_cached_privileges_even_when_redis_writes_fail():
    async def scenario():
        redis = FakeRedis()
        cache = UserCache(redis, ttl_seconds=600)
        user = make_user()
        user.role = UserRole.admin
        user.is_superuser = True
        await cache.set(user)

        user.role = UserRole.teacher
        user.is_superuser = False
        redis.fail_set = redis.fail_delete = True
        await cache.set(user)
        await cache.invalidate(user.id)
        assert (await cache.get(user.id)).role == UserRole.admin

        repo = SimpleNamespace(get=AsyncMock(return_value=user))
        service = UserService(
            repo,
            user_cache=cache,
            on_commit=partial(add_post_commit_hook, FakeSession()),
        )
        token = issue_access_token(user.id, token_version=2)
        authenticated = await _validate_token_and_get_user(token, service)
        with pytest.raises(HTTP403):
            await get_admin(authenticated)
        with pytest.raises(HTTP403):
            await get_current_superuser(authenticated)

        user.access_token_version = 3
        with pytest.raises(HTTP401):
            await _validate_token_and_get_user(token, service)

        repo.get.return_value = None
        with pytest.raises(HTTP401):
            await _validate_token_and_get_user(issue_access_token(user.id, 3), service)

    asyncio.run(scenario())


def test_cache_miss_does_not_publish_rolled_back_data():
    async def scenario():
        cache = UserCache(FakeRedis(), ttl_seconds=600)
        session = FakeSession()
        repo = UserRepository(session)
        repo.get = AsyncMock(return_value=make_user())
        service = UserService(
            repo, user_cache=cache, on_commit=partial(add_post_commit_hook, session)
        )
        await service.update(7, UserUpdate(name="Not committed"))
        await service.get(7)
        clear_post_commit_hooks(session)
        await run_post_commit_hooks(session)
        assert await cache.get(7) is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "new_role, expected_calls", [(UserRole.admin, 1), (UserRole.teacher, 0)]
)
def test_role_change_revokes_access_tokens_but_unchanged_role_does_not(
    new_role, expected_calls
):
    async def scenario():
        repo = UserRepository(FakeSession())
        repo.bump_access_token_version = AsyncMock(return_value=3)
        user = make_user()
        repo.get = AsyncMock(return_value=user)
        await UserService(repo).update(user.id, UserUpdate(role=new_role))
        assert user.role == new_role
        assert repo.bump_access_token_version.await_count == expected_calls
        if expected_calls:
            repo.bump_access_token_version.assert_awaited_once_with(user.id)

    asyncio.run(scenario())
