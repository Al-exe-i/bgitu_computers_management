from collections.abc import Sequence

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from modules.identity.contracts import UserSummary
from modules.identity.models.user import User
from modules.identity.schemas.user import UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update(self, orm_model: User, schema: UserUpdate) -> User:
        update_data = schema.model_dump(exclude_unset=True)
        return await self._update_fields(orm_model, update_data)

    async def update_password(self, orm_model: User, password_hash: str) -> User:
        return await self._update_fields(
            orm_model,
            {"password": password_hash},
        )

    async def update_photo(self, orm_model: User, photo: str | None) -> User:
        return await self._update_fields(orm_model, {"photo": photo})

    async def _update_fields(self, orm_model: User, update_data: dict) -> User:
        for field, value in update_data.items():
            setattr(orm_model, field, value)

        await self.db.flush()
        await self.db.refresh(orm_model)
        return orm_model

    async def get(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def exists(self, user_id: int) -> bool:
        result = await self.db.execute(select(User.id).where(User.id == user_id))
        return result.scalar_one_or_none() is not None

    async def get_summaries(self, user_ids: set[int]) -> dict[int, UserSummary]:
        if not user_ids:
            return {}
        result = await self.db.execute(
            select(User.id, User.email, User.name, User.surname).where(User.id.in_(user_ids))
        )
        return {row.id: UserSummary(**row._mapping) for row in result}

    async def get_all(self) -> Sequence[User]:
        result = await self.db.execute(select(User).order_by(User.id))
        return result.scalars().all()

    async def get_by_email(self, email: str) -> User | None:
        # Сравнение без учёта регистра: логины нормализуются в нижний регистр,
        # но старые записи могли остаться в смешанном регистре
        normalized = email.strip().lower()
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == normalized)
        )
        return result.scalar_one_or_none()

    async def get_access_token_version(self, user_id: int) -> int | None:
        result = await self.db.execute(
            select(User.access_token_version).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.db.delete(user)
        await self.db.flush()

    async def bump_access_token_version(self, user_id: int) -> int | None:
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(access_token_version=User.access_token_version + 1)
            .returning(User.access_token_version)
        )
        new_version = result.scalar_one_or_none()
        return new_version
