from typing import Annotated

from fastapi import Depends

from dependencies.cache import analytics_filter_options_cache_dep
from db.session import session_dep
from repositories.analytics_repo import HardwareAnalyticsRepository
from services.analytics_service import HardwareAnalyticsService


async def get_analytics_service(
    db: session_dep,
    filter_options_cache: analytics_filter_options_cache_dep,
) -> HardwareAnalyticsService:
    repo = HardwareAnalyticsRepository(db)
    service = HardwareAnalyticsService(repo, filter_options_cache)
    return service

analytics_service_dep = Annotated[HardwareAnalyticsService, Depends(get_analytics_service)]
