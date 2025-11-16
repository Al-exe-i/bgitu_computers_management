from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.audience_repo import AudienceRepository
from services.audience_service import AudienceService


async def get_audiences_service(db: session_dep) -> AudienceService:
    repo = AudienceRepository(db)
    service = AudienceService(repo)
    return service

audiences_service_dep = Annotated[AudienceService, Depends(get_audiences_service)]