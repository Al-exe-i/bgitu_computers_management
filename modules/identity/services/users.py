from collections.abc import Awaitable, Callable, Sequence
from functools import partial
from typing import Any

from sqlalchemy.exc import IntegrityError

from core.exceptions import UserAlreadyExistsError
from core.security import get_password_hash, verify_password
from modules.identity.adapters.avatar_storage import (
    AvatarStorage,
    StoredAvatarFile,
    UploadedAvatarFile,
)
from modules.identity.adapters.user_cache import UserCache
from modules.identity.contracts import UserCredentials, UserPhotoUpdateResult
from modules.identity.models.user import User
from modules.identity.repositories.users import UserRepository
from modules.identity.schemas.user import (
    AuthenticatedUser,
    UserCreate,
    UserOut,
    UserUpdate,
)


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        avatar_storage: AvatarStorage | None = None,
        user_cache: UserCache | None = None,
        on_commit: Callable[[Callable[[], Any | Awaitable[Any]]], None] | None = None,
        on_rollback: Callable[[Callable[[], Any | Awaitable[Any]]], None] | None = None,
    ):
        if user_cache is not None and on_commit is None:
            raise ValueError("User cache requires a post-commit scheduler")
        if avatar_storage is not None and (on_commit is None or on_rollback is None):
            raise ValueError("Avatar storage requires commit and rollback schedulers")
        self.repo = repo
        self.avatar_storage = avatar_storage
        self.user_cache = user_cache
        self.on_commit = on_commit
        self.on_rollback = on_rollback

    async def get_all(self) -> Sequence[UserOut]:
        return [
            UserOut.model_validate(user, from_attributes=True)
            for user in await self.repo.get_all()
        ]

    async def get(self, user_id: int) -> UserOut | None:
        if self.user_cache is not None:
            cached = await self.user_cache.get(user_id)
            if cached is not None:
                return UserOut.model_validate(cached, from_attributes=True)

        user = await self.repo.get(user_id)
        if user is not None and self.user_cache is not None:
            # Capture plain data now: ORM attributes may expire after commit.
            snapshot = AuthenticatedUser.model_validate(user, from_attributes=True)
            self._after_commit(lambda: self.user_cache.set(snapshot))

        return UserOut.model_validate(user, from_attributes=True) if user else None

    async def get_by_email(self, email: str) -> UserCredentials | None:
        user = await self.repo.get_by_email(email)
        if user is None:
            return None
        return UserCredentials(
            user.id, user.email, user.password, user.access_token_version
        )

    async def get_for_authentication(self, user_id: int) -> AuthenticatedUser | None:
        # Roles, superuser status and token version must come from one DB snapshot.
        user = await self.repo.get(user_id)
        return (
            AuthenticatedUser.model_validate(user, from_attributes=True)
            if user
            else None
        )

    async def exists(self, user_id: int) -> bool:
        return await self.repo.exists(user_id)

    async def get_access_token_version(self, user_id: int) -> int | None:
        return await self.repo.get_access_token_version(user_id)

    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        role_changed = "role" in data.model_fields_set and data.role != user.role
        user = await self.repo.update(user, data)
        if role_changed:
            await self.repo.bump_access_token_version(user_id)
        self._invalidate_after_commit(user_id)
        return UserOut.model_validate(user, from_attributes=True)

    async def verify_password(self, user_id: int, password: str) -> bool:
        user = await self.repo.get(user_id)
        return user is not None and verify_password(password, user.password)

    async def update_password(self, user_id: int, password: str) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        user = await self.repo.update_password(user, get_password_hash(password))
        self._invalidate_after_commit(user_id)
        return UserOut.model_validate(user, from_attributes=True)

    async def create(self, data: UserCreate) -> UserOut | None:
        user_data = data.model_dump(exclude_unset=True)
        user_data["password"] = get_password_hash(data.password)
        user = User(**user_data)
        try:
            user = await self.repo.create(user)
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc
        self._invalidate_after_commit(user.id)
        return UserOut.model_validate(user, from_attributes=True)

    async def delete(self, user_id: int) -> bool:
        user = await self.repo.get(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        self._invalidate_after_commit(user_id)
        return True

    async def bump_access_token_version(self, user_id: int) -> int | None:
        version = await self.repo.bump_access_token_version(user_id)
        if version is not None:
            self._invalidate_after_commit(user_id)
        return version

    def get_photo(self, user: UserOut) -> StoredAvatarFile | None:
        return self._avatar_storage().get_existing(user.photo)

    async def upload_photo(
        self,
        user_id: int,
        file: UploadedAvatarFile,
    ) -> UserPhotoUpdateResult | None:
        user = await self.repo.get(user_id)
        if not user:
            return None

        old_photo = user.photo
        storage = self._avatar_storage()
        new_photo = await storage.save(file)
        # Register compensation before any DB write or subsequent audit can fail.
        self._after_rollback(partial(storage.delete, new_photo))

        updated = await self.repo.update_photo(user, new_photo)
        if old_photo:
            self._after_commit(partial(storage.delete, old_photo))
        self._invalidate_after_commit(user_id)
        updated_user = UserOut.model_validate(updated, from_attributes=True)

        return UserPhotoUpdateResult(
            user=updated_user,
            had_photo=bool(old_photo),
        )

    async def delete_photo(self, user_id: int) -> UserPhotoUpdateResult | None:
        user = await self.repo.get(user_id)
        if not user:
            return None

        old_photo = user.photo
        updated = await self.repo.update_photo(user, None)
        if old_photo:
            self._after_commit(partial(self._avatar_storage().delete, old_photo))
        self._invalidate_after_commit(user_id)
        updated_user = UserOut.model_validate(updated, from_attributes=True)

        return UserPhotoUpdateResult(
            user=updated_user,
            had_photo=bool(old_photo),
        )

    def _avatar_storage(self) -> AvatarStorage:
        if self.avatar_storage is None:
            raise RuntimeError("Avatar storage is not configured")
        return self.avatar_storage

    def _invalidate_after_commit(self, user_id: int) -> None:
        if self.user_cache is None:
            return
        self._after_commit(lambda: self.user_cache.invalidate(user_id))

    def _after_commit(self, callback: Callable[[], Any | Awaitable[Any]]) -> None:
        if self.on_commit is None:
            raise RuntimeError("Post-commit scheduler is not configured")
        self.on_commit(callback)

    def _after_rollback(self, callback: Callable[[], Any | Awaitable[Any]]) -> None:
        if self.on_rollback is None:
            raise RuntimeError("Post-rollback scheduler is not configured")
        self.on_rollback(callback)
