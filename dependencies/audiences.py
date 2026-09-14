from functools import partial
from typing import Annotated

from fastapi import Depends

from db.post_commit import add_post_commit_hook
from db.session import session_dep
from dependencies.cache import (
    analytics_filter_options_cache_dep,
    office_short_list_cache_dep,
)
from modules.inventory.repositories.audiences import AudienceRepository
from modules.inventory.repositories.hardware import HardwareRepository
from modules.inventory.services.audiences import AudienceService
from modules.inventory.services.grid import AudienceGridService
from modules.inventory.services.hardware import HardwareService


async def get_audiences_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
    analytics_filter_options_cache: analytics_filter_options_cache_dep,
) -> AudienceService:
    repo = AudienceRepository(db)
    hardware_repo = HardwareRepository(db)
    hardware_service = HardwareService(hardware_repo)
    grid_service = AudienceGridService(hardware_service)
    service = AudienceService(
        repo,
        grid_service,
        office_short_cache,
        analytics_filter_options_cache,
        on_commit=partial(add_post_commit_hook, db),
    )
    return service


audiences_service_dep = Annotated[AudienceService, Depends(get_audiences_service)]
