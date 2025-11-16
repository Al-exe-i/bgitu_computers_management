from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.additional_hardware_repo import AdditionalHardwareRepository
from services.additional_hardware_service import AdditionalHardwareService


async def get_additional_hardware_service(db: session_dep) -> AdditionalHardwareService:
    repo = AdditionalHardwareRepository(db)
    service = AdditionalHardwareService(repo)
    return service

hardware_service_dep = Annotated[
    AdditionalHardwareService,
    Depends(get_additional_hardware_service)
]