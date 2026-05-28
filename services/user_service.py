from typing import Sequence
from dataclasses import dataclass

from core.security import get_password_hash
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

    async def update(self, user_id: int, data: UserUpdate) -> UserOut | None:
        user = await self.repo.get(user_id)
        if not user:
            return None
        user = await self.repo.update(user, data)
        return UserOut.model_validate(user, from_attributes=True)

    async def create(self, data: UserCreate) -> UserOut | None:
        data.password = get_password_hash(data.password)
        user_data = data.model_dump(exclude_unset=True)
        user = User(**user_data)
        user = await self.repo.create(user)
        return UserOut.model_validate(user, from_attributes=True)

    async def delete(self, user_id: int) -> bool:
        user = await self.repo.get(user_id)
        if not user:
            return False
        await self.repo.delete(user)
        return True

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

        updated_user = await self.update(user_id, UserUpdate(photo=new_photo))
        if updated_user is None:
            return None

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

        updated_user = await self.update(user_id, UserUpdate(photo=None))
        if updated_user is None:
            return None

        return UserPhotoUpdateResult(
            user=updated_user,
            had_photo=bool(old_photo),
        )

    def _avatar_storage(self) -> AvatarStorage:
        if self.avatar_storage is None:
            raise RuntimeError("Avatar storage is not configured")
        return self.avatar_storage
