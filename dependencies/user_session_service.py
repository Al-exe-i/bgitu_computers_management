from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.user_session_repo import UserSessionRepository
from services.user_session_service import UserSessionService


def get_user_session_service(db: session_dep):
    return UserSessionService(UserSessionRepository(db))


user_session_service_dep = Annotated[UserSessionService, Depends(get_user_session_service)]