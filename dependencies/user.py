#dependencies/user.py

from functools import partial
from typing import Annotated

from fastapi import Depends

from db.post_commit import add_post_commit_hook
from db.session import session_dep
from dependencies.cache import user_cache_dep
from dependencies.storage import object_storage_dep
from modules.identity.adapters.avatar_storage import AvatarStorage
from modules.identity.repositories.users import UserRepository
from modules.identity.services.users import UserService


def get_user_service(db: session_dep, user_cache: user_cache_dep, storage: object_storage_dep):
    repo = UserRepository(db)
    service = UserService(
        repo,
        AvatarStorage(storage),
        user_cache,
        on_commit=partial(add_post_commit_hook, db),
    )
    return service

user_service_dep = Annotated[UserService, Depends(get_user_service)]
