from typing import Annotated

from fastapi import Depends

from core.config import settings
from db.session import session_dep
from repositories.invite_repo import InviteRepository
from services.invite_service import InviteService


async def get_invite_service(db: session_dep) -> InviteService:
    repo = InviteRepository(db)
    service = InviteService(repo, settings.frontend_url)
    return service

invite_service_dep = Annotated[InviteService, Depends(get_invite_service)]