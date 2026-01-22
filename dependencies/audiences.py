from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.audience_repo import AudienceRepository
from repositories.hardware_repo import HardwareRepository
from services.audience_service import AudienceService


async def get_audiences_service(db: session_dep) -> AudienceService:
    repo = AudienceRepository(db)
    hardware_repo = HardwareRepository(db)
    service = AudienceService(repo, hardware_repo)
    return service

audiences_service_dep = Annotated[AudienceService, Depends(get_audiences_service)]