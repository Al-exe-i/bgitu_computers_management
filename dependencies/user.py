#dependencies/user.py

from typing import Annotated
from fastapi import Depends
from dependencies.cache import user_cache_dep
from dependencies.storage import object_storage_dep
from db.session import session_dep
from repositories.user_repo import UserRepository
from services.avatar_storage import AvatarStorage
from services.user_service import UserService


def get_user_service(db: session_dep, user_cache: user_cache_dep, storage: object_storage_dep):
    repo = UserRepository(db, user_cache)
    service = UserService(
        repo,
        AvatarStorage(storage),
        user_cache,
    )
    return service

user_service_dep = Annotated[UserService, Depends(get_user_service)]
