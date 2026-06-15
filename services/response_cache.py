from __future__ import annotations

from typing import Generic, TypeVar

from loguru import logger
from pydantic import TypeAdapter, ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError


CachedT = TypeVar("CachedT")


class RedisTypedCache(Generic[CachedT]):
    def __init__(
        self,
        redis: Redis,
        *,
        key: str,
        value_type,
        ttl_seconds: int,
    ) -> None:
        self.redis = redis
        self.key = key
        self.ttl_seconds = ttl_seconds
        self.adapter = TypeAdapter(value_type)

    async def get(self) -> CachedT | None:
        try:
            raw = await self.redis.get(self.key)
        except RedisError as exc:
            logger.debug("Cache read failed for key={}: {}", self.key, exc)
            return None

        if not raw:
            return None

        try:
            value = self.adapter.validate_json(raw)
        except (TypeError, ValueError, ValidationError) as exc:
            logger.debug("Cache payload is invalid for key={}: {}", self.key, exc)
            await self.invalidate()
            return None

        return value

    async def set(self, value: CachedT) -> None:
        try:
            raw = self.adapter.dump_json(value).decode()
            await self.redis.set(self.key, raw, ex=self.ttl_seconds)
        except (TypeError, ValueError, ValidationError) as exc:
            logger.debug("Cache serialization failed for key={}: {}", self.key, exc)
        except RedisError as exc:
            logger.debug("Cache write failed for key={}: {}", self.key, exc)

    async def invalidate(self) -> None:
        try:
            await self.redis.delete(self.key)
        except RedisError as exc:
            logger.debug("Cache invalidation failed for key={}: {}", self.key, exc)
