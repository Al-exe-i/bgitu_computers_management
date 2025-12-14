from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Hardware


class HardwareRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, hardware_id: int) -> Hardware | None:
        stmt = select(Hardware).where(Hardware.id == hardware_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, hardware_id: int, data: dict) -> Hardware | None:
        stmt = (
            update(Hardware)
            .where(Hardware.id == hardware_id)
            .values(**data)
            .returning(Hardware)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()