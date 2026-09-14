from functools import partial
from typing import Annotated

from fastapi import Depends

from db.post_commit import add_post_commit_hook
from db.session import session_dep
from dependencies.cache import (
    analytics_filter_options_cache_dep,
    office_short_list_cache_dep,
)
from modules.inventory.repositories.offices import OfficeRepository
from modules.inventory.services.offices import OfficeService


def get_office_service(
    db: session_dep,
    office_short_cache: office_short_list_cache_dep,
    analytics_filter_options_cache: analytics_filter_options_cache_dep,
):
    repo = OfficeRepository(db)
    service = OfficeService(
        repo,
        office_short_cache,
        analytics_filter_options_cache,
        on_commit=partial(add_post_commit_hook, db),
    )
    return service


office_service_dep = Annotated[OfficeService, Depends(get_office_service)]
