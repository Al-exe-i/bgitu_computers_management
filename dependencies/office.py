from typing import Annotated
from fastapi import Depends
from dependencies.cache import analytics_filter_options_cache_dep, office_short_list_cache_dep
from db.session import session_dep
from repositories.office_repo import OfficeRepository
from services.office_service import OfficeService


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
    )
    return service


office_service_dep = Annotated[OfficeService, Depends(get_office_service)]
