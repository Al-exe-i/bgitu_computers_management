from functools import partial
from typing import Annotated

from fastapi import Depends

from db.post_commit import add_post_commit_hook
from db.session import session_dep
from dependencies.cache import analytics_filter_options_cache_dep
from modules.inventory.repositories.analytics import HardwareAnalyticsRepository
from modules.inventory.services.analytics import HardwareAnalyticsService


async def get_analytics_service(
    db: session_dep,
    filter_options_cache: analytics_filter_options_cache_dep,
) -> HardwareAnalyticsService:
    repo = HardwareAnalyticsRepository(db)
    service = HardwareAnalyticsService(repo, filter_options_cache, on_commit=partial(add_post_commit_hook, db))
    return service

analytics_service_dep = Annotated[HardwareAnalyticsService, Depends(get_analytics_service)]
