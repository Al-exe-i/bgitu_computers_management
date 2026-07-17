from typing import Sequence
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from core.exceptions import UserAlreadyExistsError
from core.security import get_password_hash, verify_password
from models import User
from repositories.user_repo import UserRepository
from schemas.user import UserUpdate, UserOut, UserCreate
from services.avatar_storage import AvatarStorage, StoredAvatarFile, UploadedAvatarFile
from services.user_cache import CachedUser, UserCache


@dataclass(slots=True)
class UserPhotoUpdateResult:
    user: UserOut
    had_photo: bool


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        avatar_storage: AvatarStorage | None = None,
        user_cache: UserCache | None = None,
    ):
        self.repo = repo
        self.avatar_storage = avatar_storage
        self.user_cache = user_cache

    async def get_all(self) -> Sequence[User]:
        return await self.repo.get_all()

    async def get(self, user_id: int) -> User | CachedUser | None:
        if self.user_cache is not None:
            cached = await self.user_cache.get(user_id)
            if cached is not None:
                return cached

        user = await self.repo.get(user_id)
        if user is not None and self.user_cache is not None:
            await self.user_cache.set(user)

        return user

    async def get_by_email(self, email: str) -> User:
        return await self.repo.get_by_email(email)

    async def get_access_token_version(self, user_id: int) -> int | None:
        return await self.repo.get_access_token_version(user_id)

    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        user = await self.repo.update(user, data)
        return UserOut.model_validate(user, from_attributes=True)

    async def verify_password(self, user_id: int, password: str) -> bool:
        user = await self.repo.get(user_id)
        return user is not None and verify_password(password, user.password)

    async def update_password(self, user_id: int, password: str) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        user = await self.repo.update_password(user, password)
        return UserOut.model_validate(user, from_attributes=True)

    async def create(self, data: UserCreate) -> UserOut | None:
        data.password = get_password_hash(data.password)
        user_data = data.model_dump(exclude_unset=True)
        user = User(**user_data)
        try:
            user = await self.repo.create(user)
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc
        return UserOut.model_validate(user, from_attributes=True)

    async def delete(self, user_id: int) -> bool:
        user = await self.repo.get(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        return True

    async def bump_access_token_version(self, user_id: int) -> int | None:
        return await self.repo.bump_access_token_version(user_id)

    def get_photo(self, user: User) -> StoredAvatarFile | None:
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
        new_photo = await self._avatar_storage().save(file)

        if old_photo:
            self._avatar_storage().delete(old_photo)

        updated = await self.repo.update_photo(user, new_photo)
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
        if old_photo:
            self._avatar_storage().delete(old_photo)

        updated = await self.repo.update_photo(user, None)
        updated_user = UserOut.model_validate(updated, from_attributes=True)

        return UserPhotoUpdateResult(
            user=updated_user,
            had_photo=bool(old_photo),
        )

    def _avatar_storage(self) -> AvatarStorage:
        if self.avatar_storage is None:
            raise RuntimeError("Avatar storage is not configured")
        return self.avatar_storage
