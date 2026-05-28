from typing import Annotated

from fastapi import Depends

from core.config import settings
from core.redis_client import get_cache_redis
from services.user_cache import UserCache


def get_user_cache() -> UserCache:
    return UserCache(
        get_cache_redis(),
        ttl_seconds=settings.cache.user_ttl_seconds,
    )


user_cache_dep = Annotated[UserCache, Depends(get_user_cache)]
