from typing import Annotated

from fastapi import Depends

from core.config import settings
from core.redis_client import get_cache_redis
from schemas.analytics import HardwareAnalyticsFilterOptions
from schemas.office import OfficeShort
from services.response_cache import RedisTypedCache
from services.user_cache import UserCache


def get_user_cache() -> UserCache:
    return UserCache(
        get_cache_redis(),
        ttl_seconds=settings.cache.user_ttl_seconds,
    )


user_cache_dep = Annotated[UserCache, Depends(get_user_cache)]


def get_office_short_list_cache() -> RedisTypedCache[list[OfficeShort]]:
    return RedisTypedCache(
        get_cache_redis(),
        key="inventory:offices:short:v1",
        value_type=list[OfficeShort],
        ttl_seconds=settings.cache.office_short_ttl_seconds,
        metrics_name="inventory_office_short_list",
    )


office_short_list_cache_dep = Annotated[
    RedisTypedCache[list[OfficeShort]],
    Depends(get_office_short_list_cache),
]


def get_analytics_filter_options_cache() -> RedisTypedCache[HardwareAnalyticsFilterOptions]:
    return RedisTypedCache(
        get_cache_redis(),
        key="analytics:hardware:filter_options:v1",
        value_type=HardwareAnalyticsFilterOptions,
        ttl_seconds=settings.cache.analytics_filter_options_ttl_seconds,
        metrics_name="analytics_filter_options",
    )


analytics_filter_options_cache_dep = Annotated[
    RedisTypedCache[HardwareAnalyticsFilterOptions],
    Depends(get_analytics_filter_options_cache),
]
