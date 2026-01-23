from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.office_repo import OfficeRepository
from services.office_service import OfficeService


def get_office_service(db: session_dep):
    repo = OfficeRepository(db)
    service = OfficeService(repo)
    return service


office_service_dep = Annotated[OfficeService, Depends(get_office_service)]
