from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.audience_repo import AudienceRepository
from repositories.hardware_repo import HardwareRepository
from services.audience_service import AudienceService
from services.hardware_service import HardwareService


async def get_audiences_service(db: session_dep) -> AudienceService:
    repo = AudienceRepository(db)
    hardware_repo = HardwareRepository(db)
    hardware_service = HardwareService(hardware_repo)
    service = AudienceService(repo, hardware_service)
    return service

audiences_service_dep = Annotated[AudienceService, Depends(get_audiences_service)]