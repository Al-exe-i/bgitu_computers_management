from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.future import select
from db.post_commit import add_post_commit_hook
from models.user import User
from schemas.user import UserUpdate
from core.security import get_password_hash
from services.user_cache import UserCache


class UserRepository:
    def __init__(self, db: AsyncSession, cache: UserCache | None = None):
        self.db = db
        self.cache = cache

    async def update(self, orm_model: User, schema: UserUpdate) -> User:
        update_data = schema.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])

        for field, value in update_data.items():
            setattr(orm_model, field, value)

        await self.db.flush()
        await self.db.refresh(orm_model)
        self._set_cache_after_commit(orm_model)
        return orm_model

    async def get(self, user_id: int):
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[User]:
        result = await self.db.execute(select(User).order_by(User.id))
        return result.scalars().all()

    async def get_by_email(self, email: str):
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_access_token_version(self, user_id: int) -> int | None:
        result = await self.db.execute(
            select(User.access_token_version).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int):
        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, user: User):
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        self._set_cache_after_commit(user)
        return user

    async def delete(self, user: User):
        user_id = user.id
        await self.db.delete(user)
        await self.db.flush()
        self._invalidate_cache_after_commit(user_id)

    async def bump_access_token_version(self, user_id: int) -> int | None:
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(access_token_version=User.access_token_version + 1)
            .returning(User.access_token_version)
        )
        new_version = result.scalar_one_or_none()
        if new_version is not None:
            self._invalidate_cache_after_commit(user_id)
        return new_version

    async def set_telegram_link(self, user: User, telegram_id: int, *, confirmed: bool) -> User:
        user.telegram_id = telegram_id
        user.telegram_id_confirmed = confirmed
        await self.db.flush()
        await self.db.refresh(user)
        self._set_cache_after_commit(user)
        return user

    async def clear_telegram_link(self, user: User) -> User:
        user.telegram_id = None
        user.telegram_id_confirmed = False
        await self.db.flush()
        await self.db.refresh(user)
        self._set_cache_after_commit(user)
        return user

    def _set_cache_after_commit(self, user: User) -> None:
        if self.cache is None:
            return

        add_post_commit_hook(self.db, lambda: self.cache.set(user))

    def _invalidate_cache_after_commit(self, user_id: int) -> None:
        if self.cache is None:
            return

        add_post_commit_hook(self.db, lambda: self.cache.invalidate(user_id))
