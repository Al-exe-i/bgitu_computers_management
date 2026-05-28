from redis.asyncio import Redis

from core.config import settings


_cache_redis: Redis | None = None


def get_cache_redis() -> Redis:
    global _cache_redis

    if _cache_redis is None:
        _cache_redis = Redis.from_url(
            settings.cache.redis_url,
            decode_responses=True,
        )

    return _cache_redis


async def close_cache_redis() -> None:
    global _cache_redis

    if _cache_redis is None:
        return

    await _cache_redis.aclose()
    _cache_redis = None
