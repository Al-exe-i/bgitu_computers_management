from typing import Annotated

from fastapi import Depends

from db.session import session_dep
from modules.identity.repositories.sessions import UserSessionRepository
from modules.identity.services.sessions import UserSessionService


def get_user_session_service(db: session_dep):
    return UserSessionService(UserSessionRepository(db))


user_session_service_dep = Annotated[UserSessionService, Depends(get_user_session_service)]