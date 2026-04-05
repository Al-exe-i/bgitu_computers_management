from typing import Sequence
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Hardware
from models.audience import Audience


class AudienceRepository:

    def __init__(self, db: AsyncSession):
        self.session = db

    async def get_all(self) -> Sequence[Audience]:
        """Получить список всех аудиторий"""
        stmt = (
            select(Audience)
            .options(
                selectinload(Audience.hardware).selectinload(Hardware.files)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, audience_id: int) -> Audience | None:
        """
        Получить аудиторию с подгруженным оборудованием.
        """
        stmt = (
            select(Audience)
            .options(selectinload(Audience.hardware).selectinload(Hardware.files))
            .filter(Audience.id == audience_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, audience: Audience) -> Audience:
        """Создание аудитории"""
        self.session.add(audience)
        await self.session.flush()
        await self.session.refresh(audience, attribute_names=["hardware"])
        return audience

    async def update(self, audience_id: int, data: dict) -> Audience | None:
        stmt = (
            update(Audience)
            .where(Audience.id == audience_id)
            .values(**data)
            .returning(Audience.id)
        )

        result = await self.session.execute(stmt)
        updated_id = result.scalar_one_or_none()

        if updated_id is None:
            return None

        await self.session.flush()

        stmt = (
            select(Audience)
            .where(Audience.id == updated_id)
            .options(
                selectinload(Audience.hardware).selectinload(Hardware.files),
                selectinload(Audience.office),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete(self, audience_id: int) -> None:
        stmt = delete(Audience).where(Audience.id == audience_id)
        await self.session.execute(stmt)
        await self.session.flush()
