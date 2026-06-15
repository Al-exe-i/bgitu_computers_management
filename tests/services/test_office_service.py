import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from core.exceptions import OfficeAlreadyExistsError
from db.post_commit import run_post_commit_hooks
from schemas.office import OfficeCreate, OfficeShort
from services.response_cache import RedisTypedCache
from services.office_service import OfficeService


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.deleted: list[str] = []

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        self.store[key] = value

    async def delete(self, key: str):
        self.deleted.append(key)
        self.store.pop(key, None)


class FakeSession:
    def __init__(self) -> None:
        self.info: dict = {}


class FakeOfficeRepo:
    def __init__(self, *, create_error: Exception | None = None) -> None:
        self.db = FakeSession()
        self.create_error = create_error
        self.created: list[object] = []
        self.short_calls = 0

    async def create(self, office):
        if self.create_error is not None:
            raise self.create_error
        self.created.append(office)
        return SimpleNamespace(id=office.id, address=office.address)

    async def get_list_short(self):
        self.short_calls += 1
        return [
            {
                "id": 1,
                "address": "Main building",
                "audiences_count": 2,
                "faulty_hw_count": 1,
            }
        ]


def test_create_duplicate_office_raises_domain_error() -> None:
    async def scenario() -> None:
        service = OfficeService(
            FakeOfficeRepo(
                create_error=IntegrityError("insert offices", {}, Exception("duplicate")),
            )
        )

        with pytest.raises(OfficeAlreadyExistsError):
            await service.create(OfficeCreate(id=1, address="Main building"))

    asyncio.run(scenario())


def test_get_all_short_uses_cache_after_first_repo_read() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        cache = RedisTypedCache(
            redis,
            key="inventory:offices:short:v1",
            value_type=list[OfficeShort],
            ttl_seconds=300,
        )
        repo = FakeOfficeRepo()
        service = OfficeService(repo, office_short_cache=cache)

        first = await service.get_all_short()
        second = await service.get_all_short()

        assert first == second
        assert first[0].address == "Main building"
        assert repo.short_calls == 1

    asyncio.run(scenario())


def test_create_office_invalidates_related_caches_after_commit() -> None:
    async def scenario() -> None:
        redis = FakeRedis()
        office_cache = RedisTypedCache(
            redis,
            key="inventory:offices:short:v1",
            value_type=list[OfficeShort],
            ttl_seconds=300,
        )
        analytics_cache = RedisTypedCache(
            redis,
            key="analytics:hardware:filter_options:v1",
            value_type=dict,
            ttl_seconds=300,
        )
        repo = FakeOfficeRepo()
        service = OfficeService(repo, office_cache, analytics_cache)

        await service.create(OfficeCreate(id=1, address="Main building"))

        assert redis.deleted == []
        await run_post_commit_hooks(repo.db)
        assert redis.deleted == [
            "inventory:offices:short:v1",
            "analytics:hardware:filter_options:v1",
        ]

    asyncio.run(scenario())
