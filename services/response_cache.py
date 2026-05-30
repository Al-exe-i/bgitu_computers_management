from __future__ import annotations

from typing import Generic, TypeVar

from loguru import logger
from pydantic import TypeAdapter, ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.metrics import MetricsRegistry, metrics_registry


CachedT = TypeVar("CachedT")


class RedisTypedCache(Generic[CachedT]):
    def __init__(
        self,
        redis: Redis,
        *,
        key: str,
        value_type,
        ttl_seconds: int,
        metrics_name: str,
        metrics: MetricsRegistry | None = metrics_registry,
    ) -> None:
        self.redis = redis
        self.key = key
        self.ttl_seconds = ttl_seconds
        self.metrics_name = metrics_name
        self.metrics = metrics
        self.adapter = TypeAdapter(value_type)

    async def get(self) -> CachedT | None:
        try:
            raw = await self.redis.get(self.key)
        except RedisError as exc:
            logger.debug("Cache read failed for key={}: {}", self.key, exc)
            self._observe("get", "error")
            return None

        if not raw:
            self._observe("get", "miss")
            return None

        try:
            value = self.adapter.validate_json(raw)
        except (TypeError, ValueError, ValidationError) as exc:
            logger.debug("Cache payload is invalid for key={}: {}", self.key, exc)
            self._observe("get", "invalid_payload")
            await self.invalidate()
            return None

        self._observe("get", "hit")
        return value

    async def set(self, value: CachedT) -> None:
        try:
            raw = self.adapter.dump_json(value).decode()
            await self.redis.set(self.key, raw, ex=self.ttl_seconds)
            self._observe("set", "success")
        except (TypeError, ValueError, ValidationError) as exc:
            logger.debug("Cache serialization failed for key={}: {}", self.key, exc)
            self._observe("set", "error")
        except RedisError as exc:
            logger.debug("Cache write failed for key={}: {}", self.key, exc)
            self._observe("set", "error")

    async def invalidate(self) -> None:
        try:
            await self.redis.delete(self.key)
            self._observe("delete", "success")
        except RedisError as exc:
            logger.debug("Cache invalidation failed for key={}: {}", self.key, exc)
            self._observe("delete", "error")

    def _observe(self, operation: str, result: str) -> None:
        if self.metrics is None:
            return

        self.metrics.observe_cache_event(
            cache=self.metrics_name,
            operation=operation,
            result=result,
        )
