from typing import Annotated
from fastapi import Depends
from db.session import session_dep
from repositories.user_repo import UserRepository
from services.user_service import UserService


def get_user_service(db: session_dep):
    repo = UserRepository(db)
    service = UserService(repo)
    return service

user_service_dep = Annotated[UserService, Depends(get_user_service)]