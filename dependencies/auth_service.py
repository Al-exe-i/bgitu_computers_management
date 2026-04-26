from typing import Annotated

from fastapi import Depends

from dependencies.user import user_service_dep
from dependencies.user_session_service import user_session_service_dep
from services.auth_service import AuthService


def get_auth_service(
    user_service: user_service_dep,
    session_service: user_session_service_dep,
) -> AuthService:
    return AuthService(user_service, session_service)


auth_service_dep = Annotated[AuthService, Depends(get_auth_service)]
