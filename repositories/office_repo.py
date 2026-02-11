from typing import Sequence
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Audience, Hardware
from models.office import Office
from schemas.office import OfficeUpdate


class OfficeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(self, full: bool):
        if full:
            stmt = (
                select(Office)
                .options(
                    selectinload(Office.audiences).selectinload(Audience.hardware)
                )
            )
            result = await self.db.execute(stmt)
            return result.scalars().all()

        stmt = (
            select(
                Office.id,
                Office.address,
                func.count(Audience.id).label("audiences_count"),
            )
            .outerjoin(Audience, Audience.office_id == Office.id)  # чтобы корпуса без аудиторий тоже были
            .group_by(Office.id, Office.address)
            .order_by(Office.id)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {"id": office_id, "address": address, "audiences_count": cnt}
            for office_id, address, cnt in rows
        ]

    async def get_one(self, office_id: int) -> Office | None:
        stmt = (
            select(Office)
            .where(Office.id == office_id)
            .options(
                selectinload(Office.audiences)
                .selectinload(Audience.hardware)
                .selectinload(Hardware.files)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, office: Office) -> Office:
        self.db.add(office)
        await self.db.commit()
        await self.db.refresh(office)
        return office

    async def get_one_short(self, office_id: int) -> Office | None:
        stmt = (
            select(Office)
            .where(Office.id == office_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, schema: OfficeUpdate, orm_model: Office) -> Office:
        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(orm_model, field, value)
        await self.db.commit()
        await self.db.refresh(orm_model)
        return orm_model

    async def count_faulty_computers(self, office_id: int) -> int:
        stmt = (
            select(func.count(Hardware.id))
            .join(Audience)
            .join(Office)
            .where(
                Office.id == office_id,
                Hardware.state == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def delete(self, office: Office) -> bool:
        try:
            await self.db.delete(office)
            await self.db.commit()
        except Exception as e:
            return False

