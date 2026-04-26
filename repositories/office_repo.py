from loguru import logger
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

    async def get_list(self):
        stmt = (
            select(Office)
            .options(
                selectinload(Office.audiences).selectinload(Audience.hardware)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_list_short(self):
        stmt = (
            select(
                Office.id,
                Office.address,
                func.count(func.distinct(Audience.id)).label("audiences_count"),
                func.count(Hardware.id).filter(Hardware.state.is_(False)).label("faulty_hw_count"),
            )
            .outerjoin(Audience, Audience.office_id == Office.id)
            .outerjoin(Hardware, Hardware.audience_id == Audience.id)
            .group_by(Office.id, Office.address)
            .order_by(Office.id)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {"id": office_id, "address": address, "audiences_count": audiences_count, "faulty_hw_count": faulty_hw_count}
            for office_id, address, audiences_count, faulty_hw_count in rows
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

    async def get_one_short(self, office_id: int) -> Office | None:
        stmt = (
            select(Office)
            .where(Office.id == office_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, office: Office) -> Office:
        self.db.add(office)
        await self.db.flush()
        await self.db.refresh(office)
        return office

    async def update(self, schema: OfficeUpdate, orm_model: Office) -> Office:
        update_data = schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(orm_model, field, value)

        await self.db.flush()
        await self.db.refresh(orm_model)
        return orm_model

    async def delete(self, office: Office | None) -> bool:
        if office is None:
            return False

        try:
            await self.db.delete(office)
            await self.db.flush()
            return True
        except Exception as e:
            logger.warning("An error occurred while deleting office %s", e)
            return False

